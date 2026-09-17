"""48 V phantom power control, sent to one unit's board over UDP.

This is a real hardware command, not DSP: `infrastructure/acquisition/gain.py`
adjusts a software multiplier after decimation and never leaves this process.
This module sends two or three raw bytes to the unit's own board, over the
network, which the FPGA's `udp_rx_core` accepts unfiltered by destination port
and hands to `adau_sequencer` to write over I2C — the control-plane wire
contract described directly in the UATR_TDM firmware repository's
`python/ctrl.py`, read from that file rather than assumed or recalled.

The packet carries the same byte layout `ctrl.py` uses to set a channel's
hardware ADC gain, because the firmware has no separate "set flags only"
command — the 48 V enable bit rides along as an optional third byte on a
channel/gain packet. This module always addresses channel 1 at 0 dB
(`_CARRIER_GAIN_BYTE`), the documented way to change the flag without
disturbing any channel's own gain: `ctrl.py`'s own `send_flags()` helper does
exactly the same thing, with the same caveat carried here too — harmless only
because this application has no hardware ADC gain control of its own to
disturb. (The unrelated software gain in `gain.py` is a completely different
knob, applied after decimation, on this process's own copy of the samples.)

There is no acknowledgement in the firmware's control protocol, so a sent
packet is evidence it was handed to a socket, not evidence the board received
or acted on it. The answer comes back the other way instead: the board
publishes what it is actually driving in a status byte in every audio packet,
decoded by `infrastructure/acquisition/uatr_tdm.py`. `send_phantom_power` is
still one-shot, and :class:`PhantomPowerKeepalive` is what closes the loop —
it re-sends while the board disagrees, and keeps re-sending while 48 V is
meant to be on, because the firmware's phantom watchdog drops it otherwise.

The firmware watchdog is the other half of that same argument, from the
board's side. `C_PHANTOM_WATCHDOG` in `top_system.vhd` drops 48 V unless the
board has heard a flags-carrying packet within `C_PHANTOM_TIMEOUT_S`, because
an app that crashes, a pulled cable or a dead PC all otherwise leave 48 V live
on the XLRs forever with nothing on the board any the wiser. It is a build
constant and it defaults to false, so whether it is active depends on the
bitstream a given unit is running — which is exactly why the keepalive is
unconditional here. A host that sends keepalives is correct against both
builds; a host that does not is correct against only one of them, and cannot
tell which one it is talking to.

Deliberately never restored from a stored preference. The firmware's own
design is explicit about why: "Off at every reset. The FPGA gates phantom
power on the build constant C_ENABLE_48V, the staged power-up timer, AND this
flag — so it never comes up on its own after a power cycle." A console that
persisted an "on" state and resent it at the next launch would quietly defeat
that interlock's whole purpose, so nothing in this application does — the
enabled state lives only in the running UI control
(`features/device_status/ui/phantom_power_control.py`) for as long as the
operator has left it on this session.
"""
from __future__ import annotations

import socket
from collections.abc import Callable, Mapping
from threading import Event, Lock, Thread
from time import monotonic

#: The FPGA's own control port. Unrelated to the audio-stream port this
#: application separately uses 5005 for — the firmware does not filter
#: control packets by destination port at all ("any port: udp_rx_core does
#: not filter on it"). Kept at 5005 only for consistency with the reference
#: tooling, which always sends here.
DEFAULT_CONTROL_PORT = 5005

#: Bit 0 of the optional third payload byte. `ctrl.py`: "bit 0 enables 48 V
#: phantom power."
PHANTOM_POWER_FLAG_BIT = 0x01

#: ADC 0, channel 0 (packed as `(adc << 2) | sub`) — "channel 1" in the
#: board's own 1-based numbering.
_CARRIER_CHANNEL_BYTE = 0x00
#: 0 dB on the ADAU1978 gain register (its Table 25: 0x00 = +60 dB, stepping
#: -0.375 dB per count, 0xA0 = 0 dB).
_CARRIER_GAIN_BYTE = 0xA0


def build_phantom_power_packet(enabled: bool) -> bytes:
    """The 3-byte control payload that sets (or clears) the phantom-power flag.

    Pure and network-free, so the wire format can be checked without a socket.
    """
    flags = PHANTOM_POWER_FLAG_BIT if enabled else 0x00
    return bytes([_CARRIER_CHANNEL_BYTE, _CARRIER_GAIN_BYTE, flags])


#: Swappable for a test double, and for anything other than a plain UDP
#: socket a future caller might need. The real sender opens one throwaway
#: socket per call — this is an occasional operator action, not a hot path,
#: so a pooled or persistent socket is not worth the complexity.
PacketSender = Callable[[bytes, str, int], None]


def _send_udp(packet: bytes, address: str, port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(packet, (address, port))
    finally:
        sock.close()


def send_phantom_power(
    enabled: bool,
    address: str,
    port: int = DEFAULT_CONTROL_PORT,
    *,
    sender: PacketSender = _send_udp,
) -> None:
    """Command one unit's board to enable or disable 48 V phantom power.

    `address` is the unit's own IP — the same one this application already
    persists as that unit's audio source address
    (`AcquisitionConfiguration.source_addresses`), since the board that
    streams audio is the same board that receives this command. There is no
    separate "control address" setting: nothing establishes that a real
    deployment would ever need one to differ from the audio source address,
    and inventing a second address to configure would be a setting with
    nothing to justify it.
    """
    sender(build_phantom_power_packet(enabled), address, port)


#: How often to re-send the flag while phantom power is meant to be on.
#:
#: The firmware's `C_PHANTOM_WATCHDOG` drops 48 V unless it has heard a
#: flags-carrying packet within `C_PHANTOM_TIMEOUT_S` (120 s), and its own
#: `docs/PHANTOM_POWER.md` states the host contract as a 3-byte packet every
#: ~20 s, tolerating five consecutive losses. This is that number. It is not a
#: guess with margin added: the margin is what the five-loss tolerance is.
#:
#: Every packet this module sends carries a flags byte, so every one of them
#: feeds the watchdog. A two-byte gain command would not — the FPGA kicks the
#: timer on `udp_flags_wr`, not on `udp_req`, deliberately, so that a stray
#: gain command cannot re-arm 48 V minutes after the app that asked for it
#: died.
KEEPALIVE_INTERVAL_SECONDS = 20.0

#: How soon to try again when the board is not yet reporting what was asked
#: for. Covers the ordinary lost datagram and the console that started while
#: the unit was unreachable — the firmware documentation is explicit that
#: "sent" and "off" are different facts and that the host should read the
#: state back and retry until it agrees.
RETRY_INTERVAL_SECONDS = 2.0

#: How many times to retry before falling back to the keepalive cadence.
#:
#: Retrying forever would be wrong: a board whose build has `C_ENABLE_48V`
#: false, or whose staged power-up has not reached 1000 ms, can never report
#: on, and hammering it every two seconds for the rest of the session buys
#: nothing. The readback names which gate is holding it, and the console shows
#: that instead.
MAXIMUM_RETRIES = 5

#: Answers "is this unit's board driving 48 V", or `None` where there is no
#: answer — nothing heard from it yet, or a bitstream older than the readback.
#: A callable rather than a service reference so this module keeps knowing
#: nothing about acquisition; the composition root wires the two together.
PhantomPowerReadbackSource = Callable[[int], bool | None]


class PhantomPowerKeepalive:
    """Holds the requested 48 V state for each unit and keeps saying it.

    Two jobs, both of which exist because a single fire-and-forget datagram is
    not enough:

    **Feeding the watchdog.** On a bitstream built with `C_PHANTOM_WATCHDOG`,
    48 V drops on its own unless the board keeps hearing from the host. Without
    this, an operator who enables phantom power and then leaves the console
    alone watches it die mid-capture, roughly two minutes in, with the button
    still lit. The gate does not latch, so a keepalive arriving after a trip
    brings 48 V back on the spot.

    **Making a command stick.** The control protocol has no acknowledgement,
    so a lost datagram is invisible at the sending end. This compares what was
    asked for against what the board reports and re-sends while they disagree,
    which is what turns "the console sent an off" into "the board is off".

    Deliberately not a persistence layer. Nothing here is stored or restored:
    the requested state starts empty on every construction, exactly as
    :mod:`phantom_power`'s module docstring requires, and a unit nobody has
    touched this session is never sent anything at all.
    """

    def __init__(
        self,
        addresses: Mapping[int, str],
        *,
        readback_source: PhantomPowerReadbackSource | None = None,
        port: int = DEFAULT_CONTROL_PORT,
        sender: PacketSender = _send_udp,
        interval_seconds: float = KEEPALIVE_INTERVAL_SECONDS,
        retry_seconds: float = RETRY_INTERVAL_SECONDS,
        maximum_retries: int = MAXIMUM_RETRIES,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if interval_seconds <= 0.0 or retry_seconds <= 0.0:
            raise ValueError("keepalive intervals must be positive")
        if maximum_retries < 0:
            raise ValueError("maximum_retries cannot be negative")
        self._addresses = dict(addresses)
        self._readback_source = readback_source
        self._port = port
        self._sender = sender
        self._interval = interval_seconds
        self._retry = retry_seconds
        self._maximum_retries = maximum_retries
        self._clock = clock
        self._lock = Lock()
        self._requested: dict[int, bool] = {}
        self._last_sent: dict[int, float] = {}
        self._retries: dict[int, int] = {}
        self._failures: dict[int, str] = {}
        self._stop = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        """Begin re-sending. Safe to call twice; the second call does nothing."""
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = Thread(
            target=self._run, name="phantom-power-keepalive", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop re-sending. Does NOT command 48 V off.

        Turning phantom power off is a decision, and one the operator or the
        shutdown path makes explicitly by requesting it — never a side effect
        of a thread ending. On a board with the watchdog enabled, silence is
        already the fail-safe.
        """
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)

    def request(self, unit_identifier: int, enabled: bool) -> None:
        """Record what the operator asked for, and say it to the board now."""
        with self._lock:
            self._requested[unit_identifier] = enabled
            self._retries[unit_identifier] = 0
        self._send(unit_identifier, enabled)

    def requested(self, unit_identifier: int) -> bool | None:
        """What was last asked for, or `None` if this unit was never touched."""
        with self._lock:
            return self._requested.get(unit_identifier)

    def last_error(self, unit_identifier: int) -> str:
        """The most recent send failure for this unit, or an empty string.

        A socket error here means the command never left the host, which is a
        different fault from a board that received it and refused — and the
        operator needs to be able to tell them apart.
        """
        with self._lock:
            return self._failures.get(unit_identifier, "")

    def _run(self) -> None:
        while not self._stop.wait(self._retry):
            self._tick()

    def _tick(self) -> None:
        for unit_identifier, enabled in self._pending():
            self._send(unit_identifier, enabled)

    def _pending(self) -> tuple[tuple[int, bool], ...]:
        """Which units are due a packet this tick.

        The snapshot is taken under the lock and every decision made outside
        it, because deciding needs `_readback_source` — a callable owned by
        somebody else, which may take locks of its own. Calling it while
        holding this one is how two independently correct components deadlock.
        """
        now = self._clock()
        with self._lock:
            state = tuple(
                (
                    unit_identifier,
                    enabled,
                    now - self._last_sent.get(unit_identifier, now),
                    self._retries.get(unit_identifier, 0),
                )
                for unit_identifier, enabled in self._requested.items()
            )

        due: list[tuple[int, bool]] = []
        for unit_identifier, enabled, elapsed, retries in state:
            confirmed = self._readback(unit_identifier) == enabled
            if confirmed:
                # The board agrees. Clear the retry budget so a later
                # disagreement — a watchdog trip, a board that rebooted and
                # cleared its flag — is retried properly instead of inheriting
                # an exhausted count from minutes ago.
                with self._lock:
                    self._retries[unit_identifier] = 0
            # The steady keepalive: only "on" needs holding up. Silence can
            # only ever cause 48 V to drop, which is where "off" wants to be.
            if enabled and elapsed >= self._interval:
                due.append((unit_identifier, enabled))
                continue
            # Retrying while the board has not confirmed. An unknown readback
            # counts as disagreement: a unit that has said nothing has not
            # said yes.
            if not confirmed and retries < self._maximum_retries:
                due.append((unit_identifier, enabled))
        return tuple(due)

    def _readback(self, unit_identifier: int) -> bool | None:
        if self._readback_source is None:
            return None
        try:
            return self._readback_source(unit_identifier)
        except Exception:  # a broken source must not stop the keepalive
            return None

    def _send(self, unit_identifier: int, enabled: bool) -> None:
        address = self._addresses.get(unit_identifier)
        if address is None:
            return
        packet = build_phantom_power_packet(enabled)
        try:
            self._sender(packet, address, self._port)
        except OSError as error:
            with self._lock:
                self._failures[unit_identifier] = str(error)
                self._last_sent[unit_identifier] = self._clock()
                self._retries[unit_identifier] = (
                    self._retries.get(unit_identifier, 0) + 1
                )
            return
        with self._lock:
            self._failures.pop(unit_identifier, None)
            self._last_sent[unit_identifier] = self._clock()
            self._retries[unit_identifier] = self._retries.get(unit_identifier, 0) + 1
