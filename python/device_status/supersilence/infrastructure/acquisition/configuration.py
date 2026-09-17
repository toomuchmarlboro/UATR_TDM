"""Persisted network configuration for the acquisition service."""
from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from collections.abc import Mapping

from supersilence.infrastructure.settings.repository import (
    SCOPE_SYSTEM,
    SCOPE_UNIT,
    SettingsRepository,
)

DEFAULT_BIND_ADDRESS = "0.0.0.0"
DEFAULT_PORT = 5005

#: One UDP port per board, which is what the deployed firmware images
#: transmit to and from.
#:
#: Board N has its own address *and* its own port: 192.168.1.101:5005 through
#: 192.168.1.104:5008, each board transmitting from the same port it sends to.
#: The console therefore binds four ports rather than one, and a unit's socket
#: is connected to that unit's own pair.
#:
#: Recorded per the operator, **not sighted in RTL**. The `UATR_TDM` checkout
#: available to this repository still writes 5005 as both source and
#: destination port in `udp_tx_core.vhd`, with no port generic on the entity;
#: the four images that carry per-board ports were built elsewhere. Every port
#: here is editable, so a fleet still running the older single-port images is
#: configured by setting all four fields to 5005.
#:
#: What the split buys is not throughput. It is that four sockets on four ports
#: can be read by four processes — four `udp_monitor` instances, one per board —
#: where a shared port makes them contend for one socket and one kernel buffer.
DEFAULT_PORTS = {
    1: 5005,
    2: 5006,
    3: 5007,
    4: 5008,
}

#: The old key: one port for the whole fleet. Deliberately not read, for the
#: same reason as `SUPERSEDED_RECEIVE_BUFFER_KEY` below. A stored 5005 meant
#: every unit on 5005, and silently carrying it into all four per-unit fields
#: would leave a console listening on one port for boards that now transmit to
#: four — which looks exactly like three dead units.
SUPERSEDED_PORT_KEY = "acquisition_port"
#: What the receive socket asks the kernel for, in bytes.
#:
#: This is a real trade and the operator owns it; the Acquisition settings page
#: is where they set it. Larger absorbs the scheduling stalls that cost whole
#: processing windows. But packet age measures time since a packet was *read*,
#: so a unit that has gone silent keeps looking alive for as long as its
#: buffered backlog lasts, and a large buffer delays noticing a dead unit.
#:
#: Was 128 MiB, on a measurement taken before the sender could report its own
#: pacing. Re-measured on mains power with the sender's shortfall in view, over
#: ten seconds of four-unit simulator with the receive path alone, sender in a
#: separate process and confirmed to have emitted every packet it owed:
#:
#:     8 MiB    3.51% lost, none unread
#:    16 MiB    2.33% lost, none unread
#:    32 MiB    0.00% lost, none unread
#:   128 MiB    0.00% lost, none unread
#:
#: 32 MiB is where loss reaches zero, and 128 MiB buys nothing beyond it while
#: costing four times the disconnect latency. The kernel grants double what is
#: requested, so 32 MiB asked for was 64 MiB held — about 3.4 seconds of
#: four-unit fleet audio.
#:
#: **The measurement above was taken with one socket carrying all four units.**
#: Each unit now has its own socket and its own buffer, so this is per unit and
#: the console holds four of them. 8 MiB per unit is the faithful translation of
#: that 32 MiB result: the same bytes behind each unit, the same total held, and
#: the same 3.4 seconds of backlog before a disconnect stops being visible.
#:
#: Keeping 32 MiB and calling it per-unit would have been the quiet mistake. It
#: is 13.6 seconds of one unit's audio, which is past the point where the fault
#: soak stopped seeing a disconnect at all — the exact failure that took the
#: default down from 128 MiB in the first place.
#:
#: The old 128 MiB figure was an artifact worth naming. Running the whole
#: console against the simulator, the receiver appeared to lose almost nothing
#: at 128 MiB and about 7% at 32 MiB — but the *sender* was missing 30% of its
#: own packets at 128 MiB against 6% at 32 MiB. There was simply less stream to
#: lose. `tools/live_check.py` used to terminate the sender before it printed
#: that line, so the comparison could not be made; it now waits for it.
#:
#: That particular contention is an artifact of running the simulator on the
#: same host and does not transfer to real hardware. The disconnect-latency cost
#: does transfer, and there is no measured benefit above 32 MiB, which is why
#: the default moved.
#:
#: Still needs `net.core.rmem_max` raised on the host; without it the kernel
#: silently grants a fraction of this and the loss comes back.
DEFAULT_RECEIVE_BUFFER_BYTES = 8 << 20

#: Below this the buffer cannot cover a scheduling stall at all.
MINIMUM_RECEIVE_BUFFER_BYTES = 1 << 20

#: The longest gap, in whole packets, that is bridged by interpolation instead
#: of being left as a hole.
#:
#: Two packets is sixteen frames, 167 microseconds at 96 kHz — far shorter than
#: one cycle of the lowest tonal this system looks for, so the bridge cannot
#: become a signal. That is the assembler's own default and it stays the default
#: here. It is a setting because the honest limit depends on the link: a hole is
#: `MISSING`, a single `MISSING` sample refuses a whole 1 s processing window,
#: and at a 0.1 s hop one refused window is ten. On a lossy link an operator may
#: reasonably choose a wider bridge over ten refusals; on a clean one they may
#: choose none at all and see every loss.
DEFAULT_MAXIMUM_INTERPOLATED_PACKETS = 2

#: Past this the bridge spans more than a millisecond, which is inside the
#: period of the lowest tonal the system looks for — the point at which the
#: interpolator's invented span is no longer defensibly brief relative to the
#: signal being measured.
MAXIMUM_INTERPOLATED_PACKETS_LIMIT = 12

#: Packets each unit's receiver stages before it starts dropping the oldest.
#:
#: 24 000 packets is 2 seconds of one unit's audio and about 9.8 MB, so 39 MB
#: across the fleet. It was 2 000 — 167 ms — and that is what a measured console
#: run showed evicting: with the simulator leaving no hole on the wire at all,
#: every refused window traced to this deque discarding oldest while the DSP
#: thread was stalled. At 24 000 the eviction counter went to zero on all four
#: units.
#:
#: It is not expected to reduce refusals on its own. That was measured too, and
#: it does not: the loss moves rather than disappears. It is worth the memory
#: anyway, because it removes one of the two sources of holes so the remaining
#: one can be attributed rather than guessed at.
#:
#: The trade is memory and staleness against tolerance of a stalled consumer.
#: Staged packets are audio the consumer has not reached yet, so a deep stage
#: means the console can be seconds behind the water and still call it current —
#: the same failure mode as an oversized receive buffer, one layer up.
DEFAULT_STAGING_PACKETS_PER_UNIT = 24_000

#: One consumer batch. Below this a single drain cannot fill itself, so the
#: staging deque would be discarding audio the consumer was about to ask for.
MINIMUM_STAGING_PACKETS_PER_UNIT = 512

#: Ten seconds of one unit's audio, about 49 MB a unit and 197 MB across the
#: fleet. Past this the staleness is worse than the hole it prevents: a window
#: analysed ten seconds late describes water the target has left.
MAXIMUM_STAGING_PACKETS_PER_UNIT = 120_000

#: The old key, which stored the same number with a different meaning: one
#: buffer for the whole fleet. Deliberately not read. A stored 32 MiB meant
#: 32 MiB in total and would now mean 32 MiB each — four times the memory and
#: four times the disconnect latency, applied silently on upgrade. An install
#: that had tuned it will fall back to the new default and can tune it again
#: against a field that now says what it means.
SUPERSEDED_RECEIVE_BUFFER_KEY = "acquisition_receive_buffer_bytes"

DEFAULT_SOURCE_ADDRESSES = {
    1: "127.0.0.2",
    2: "127.0.0.3",
    3: "127.0.0.4",
    4: "127.0.0.5",
}

DEFAULT_ASIO_TARGET_UNIT = 1

#: A fresh install's starting guess for the sixteen hydrophone rows, tuned to
#: the Soundcraft Ui24R this console is actually deployed against rather than
#: a naive identity map.
#:
#: Measured directly against the operator's own unit with Device Status open:
#: physical desk input 1 lights up on ASIO channel 11, input 2 on channel 12,
#: and so on — a flat +10 offset, so desk input N is ASIO channel N + 10 (one
#: based). This matches Harman's own multitrack-recording guide ("input
#: channels start at patch point 11") for the desk's *default* patch. An
#: earlier measurement on this same console had instead recorded a +20
#: offset; that reading did not hold up and this +10 reading, taken with
#: Device Status open against the live desk, is the one to trust.
#:
#: An identity map (channels 1-16) therefore does not fail to find sixteen
#: inputs — it succeeds, and hands back ten real, live channels that are
#: just not the desk inputs their fader position claims. That reads as "the
#: meters are on the wrong channel" with no error anywhere. Channels 11-26
#: (zero-based 10-25) are this desk's own inputs 1 through 16, in order.
#:
#: Still only a starting guess for a *different* Ui24R or a re-patched one:
#: the Ui24R's own Patch Bay (manual section 5.6, "Patching") lets an
#: operator repatch which local channel feeds which USB/DAW slot, so a desk
#: that has been repatched — or loaded a show file that was — legitimately
#: disagrees with the factory default. Nothing here can know another desk's
#: patch bay state, which is what the sixteen "Input N" fields exist to let
#: an operator correct per device.
DEFAULT_ASIO_CHANNEL_MAP = tuple(range(10, 26))


def uniform_ports(port: int) -> dict[int, int]:
    """Every unit on one port.

    Not what the deployed fleet does — see `DEFAULT_PORTS` — but a real
    configuration: a fleet still running single-port firmware images is exactly
    this, and so is a loopback simulator that has not been told otherwise.
    """
    return {unit_identifier: int(port) for unit_identifier in DEFAULT_SOURCE_ADDRESSES}


class AcquisitionMode(str, Enum):
    """The one live acoustic transport selected for a console run."""

    ETHERNET = "ethernet"
    ASIO = "asio"


@dataclass(frozen=True)
class AcquisitionConfiguration:
    bind_address: str
    #: One port per unit. See `DEFAULT_PORTS`.
    ports: Mapping[int, int]
    source_addresses: Mapping[int, str]
    receive_buffer_bytes: int = DEFAULT_RECEIVE_BUFFER_BYTES
    #: Whole packets of gap the sample assembler bridges rather than marking as
    #: a hole. See `DEFAULT_MAXIMUM_INTERPOLATED_PACKETS`.
    maximum_interpolated_packets: int = DEFAULT_MAXIMUM_INTERPOLATED_PACKETS
    #: Packets one unit's receiver stages before discarding its oldest. See
    #: `DEFAULT_STAGING_PACKETS_PER_UNIT`.
    staging_packets_per_unit: int = DEFAULT_STAGING_PACKETS_PER_UNIT
    #: Which buoys this console expects to hear from. A fleet is often deployed
    #: short — three units in the water, or two while a board is being repaired
    #: — and a unit the console still expects is not free: it is counted MISSING
    #: in every fleet epoch, it holds a bound port, and it shows on the buoy menu
    #: and the device status as a unit that has gone quiet. Disabling it says the
    #: absence is intended. The address and port stay stored, so re-enabling a
    #: unit does not mean entering its endpoint again.
    enabled_units: tuple[int, ...] = tuple(sorted(DEFAULT_SOURCE_ADDRESSES))
    mode: AcquisitionMode = AcquisitionMode.ETHERNET
    asio_device_name: str = ""
    asio_host_api: str = ""
    asio_target_unit: int = DEFAULT_ASIO_TARGET_UNIT
    asio_channel_map: tuple[int, ...] = DEFAULT_ASIO_CHANNEL_MAP

    def __post_init__(self) -> None:
        try:
            mode = AcquisitionMode(self.mode)
        except ValueError as error:
            raise ValueError("acquisition mode must be ethernet or asio") from error
        object.__setattr__(self, "mode", mode)
        _validate_address(self.bind_address, "bind address")
        if (
            isinstance(self.receive_buffer_bytes, bool)
            or not isinstance(self.receive_buffer_bytes, int)
            or self.receive_buffer_bytes < MINIMUM_RECEIVE_BUFFER_BYTES
        ):
            raise ValueError(
                "acquisition receive buffer must be at least "
                f"{MINIMUM_RECEIVE_BUFFER_BYTES} bytes"
            )
        if (
            isinstance(self.maximum_interpolated_packets, bool)
            or not isinstance(self.maximum_interpolated_packets, int)
            or not 0
            <= self.maximum_interpolated_packets
            <= MAXIMUM_INTERPOLATED_PACKETS_LIMIT
        ):
            raise ValueError(
                "acquisition maximum interpolated packets must be between 0 and "
                f"{MAXIMUM_INTERPOLATED_PACKETS_LIMIT}"
            )
        if (
            isinstance(self.staging_packets_per_unit, bool)
            or not isinstance(self.staging_packets_per_unit, int)
            or not MINIMUM_STAGING_PACKETS_PER_UNIT
            <= self.staging_packets_per_unit
            <= MAXIMUM_STAGING_PACKETS_PER_UNIT
        ):
            raise ValueError(
                "acquisition staging packets per unit must be between "
                f"{MINIMUM_STAGING_PACKETS_PER_UNIT} and "
                f"{MAXIMUM_STAGING_PACKETS_PER_UNIT}"
            )
        if set(self.ports) != set(DEFAULT_SOURCE_ADDRESSES):
            raise ValueError("acquisition ports must cover units 1 through 4")
        ports = {}
        for unit_identifier, port in self.ports.items():
            if isinstance(port, bool) or not isinstance(port, int):
                raise ValueError(
                    f"acquisition port for unit {unit_identifier} must be an integer"
                )
            if not 1 <= port <= 65_535:
                raise ValueError("acquisition port must be between 1 and 65535")
            ports[int(unit_identifier)] = int(port)
        object.__setattr__(self, "ports", MappingProxyType(ports))
        if set(self.source_addresses) != set(DEFAULT_SOURCE_ADDRESSES):
            raise ValueError("acquisition configuration must contain units 1 through 4")
        addresses = {
            unit_identifier: str(address)
            for unit_identifier, address in self.source_addresses.items()
        }
        for unit_identifier, address in addresses.items():
            _validate_address(address, f"source address for unit {unit_identifier}")
        # Address *and* port together. Two boards may legitimately share an
        # address on separate ports, or a port on separate addresses; what no
        # two boards may share is the pair, because that pair is what the
        # kernel matches a connected socket on and what tells one unit's
        # datagrams from another's.
        endpoints = [
            (address, ports[unit_identifier])
            for unit_identifier, address in addresses.items()
        ]
        if len(set(endpoints)) != len(endpoints):
            raise ValueError(
                "each acquisition unit needs its own source address and port pair"
            )
        object.__setattr__(self, "source_addresses", MappingProxyType(addresses))

        enabled_units = tuple(
            sorted({int(unit_identifier) for unit_identifier in self.enabled_units})
        )
        if not enabled_units:
            raise ValueError("at least one acquisition unit must stay enabled")
        if any(
            unit_identifier not in DEFAULT_SOURCE_ADDRESSES
            for unit_identifier in enabled_units
        ):
            raise ValueError("enabled acquisition units must be between 1 and 4")
        object.__setattr__(self, "enabled_units", enabled_units)

        if (
            isinstance(self.asio_target_unit, bool)
            or self.asio_target_unit not in DEFAULT_SOURCE_ADDRESSES
        ):
            raise ValueError("ASIO target unit must be between 1 and 4")
        device_name = str(self.asio_device_name).strip()
        host_api = str(self.asio_host_api).strip()
        if mode is AcquisitionMode.ASIO and not device_name:
            raise ValueError("ASIO mode requires an input device")
        if mode is AcquisitionMode.ASIO and not host_api:
            raise ValueError("ASIO mode requires an ASIO host API")
        channel_map = tuple(self.asio_channel_map)
        if (
            len(channel_map) != 16
            or any(
                isinstance(index, bool) or not isinstance(index, int)
                for index in channel_map
            )
            or any(index < 0 for index in channel_map)
            or len(set(channel_map)) != len(channel_map)
        ):
            raise ValueError(
                "ASIO channel map must contain sixteen unique nonnegative input indices"
            )
        object.__setattr__(self, "asio_device_name", device_name)
        object.__setattr__(self, "asio_host_api", host_api)
        object.__setattr__(self, "asio_channel_map", channel_map)

    @property
    def active_unit_identifiers(self) -> tuple[int, ...]:
        """The fleet that the selected acoustic source can actually provide.

        A disabled unit is absent from this, which is what makes the rest of the
        console stop expecting it: the receiver binds no port for it, no
        observation pipeline is built for it, the fleet epoch does not count it
        MISSING, and it keeps no row on the buoy menu or the device status.
        """
        if self.mode is AcquisitionMode.ASIO:
            return (self.asio_target_unit,)
        return tuple(
            unit_identifier
            for unit_identifier in sorted(self.source_addresses)
            if unit_identifier in self.enabled_units
        )

    def save(self, settings: SettingsRepository) -> None:
        settings.set(SCOPE_SYSTEM, "acquisition_bind_address", self.bind_address)
        settings.set(
            SCOPE_SYSTEM,
            "acquisition_receive_buffer_bytes_per_unit",
            self.receive_buffer_bytes,
        )
        settings.set(
            SCOPE_SYSTEM,
            "acquisition_maximum_interpolated_packets",
            self.maximum_interpolated_packets,
        )
        settings.set(
            SCOPE_SYSTEM,
            "acquisition_staging_packets_per_unit",
            self.staging_packets_per_unit,
        )
        settings.set(SCOPE_SYSTEM, "acquisition_mode", self.mode.value)
        settings.set(SCOPE_SYSTEM, "acquisition_asio_device_name", self.asio_device_name)
        settings.set(SCOPE_SYSTEM, "acquisition_asio_host_api", self.asio_host_api)
        settings.set(SCOPE_SYSTEM, "acquisition_asio_target_unit", self.asio_target_unit)
        settings.set(
            SCOPE_SYSTEM,
            "acquisition_asio_channel_map",
            list(self.asio_channel_map),
        )
        for unit_identifier, address in self.source_addresses.items():
            settings.set(
                SCOPE_UNIT,
                "acquisition_source_address",
                address,
                unit_id=unit_identifier,
            )
            settings.set(
                SCOPE_UNIT,
                "acquisition_unit_enabled",
                unit_identifier in self.enabled_units,
                unit_id=unit_identifier,
            )
            settings.set(
                SCOPE_UNIT,
                "acquisition_unit_port",
                self.ports[unit_identifier],
                unit_id=unit_identifier,
            )


def load_acquisition_configuration(
    settings: SettingsRepository,
) -> AcquisitionConfiguration:
    """Load settings and materialize missing values with safe loopback defaults."""
    bind_address = settings.get(
        SCOPE_SYSTEM, "acquisition_bind_address", DEFAULT_BIND_ADDRESS
    )
    ports = {
        unit_identifier: settings.get(
            SCOPE_UNIT,
            "acquisition_unit_port",
            default_port,
            unit_id=unit_identifier,
        )
        for unit_identifier, default_port in DEFAULT_PORTS.items()
    }
    source_addresses = {
        unit_identifier: settings.get(
            SCOPE_UNIT,
            "acquisition_source_address",
            default_address,
            unit_id=unit_identifier,
        )
        for unit_identifier, default_address in DEFAULT_SOURCE_ADDRESSES.items()
    }
    enabled_units = tuple(
        unit_identifier
        for unit_identifier in sorted(DEFAULT_SOURCE_ADDRESSES)
        if bool(
            settings.get(
                SCOPE_UNIT,
                "acquisition_unit_enabled",
                True,
                unit_id=unit_identifier,
            )
        )
    )
    # A stored fleet with every unit switched off would leave the console with
    # nothing to listen to and no way back except editing the database, so the
    # unusable state is read as the default rather than raised at startup.
    if not enabled_units:
        enabled_units = tuple(sorted(DEFAULT_SOURCE_ADDRESSES))
    receive_buffer_bytes = settings.get(
        SCOPE_SYSTEM,
        "acquisition_receive_buffer_bytes_per_unit",
        DEFAULT_RECEIVE_BUFFER_BYTES,
    )
    maximum_interpolated_packets = settings.get(
        SCOPE_SYSTEM,
        "acquisition_maximum_interpolated_packets",
        DEFAULT_MAXIMUM_INTERPOLATED_PACKETS,
    )
    staging_packets_per_unit = settings.get(
        SCOPE_SYSTEM,
        "acquisition_staging_packets_per_unit",
        DEFAULT_STAGING_PACKETS_PER_UNIT,
    )
    mode = settings.get(SCOPE_SYSTEM, "acquisition_mode", AcquisitionMode.ETHERNET.value)
    asio_device_name = settings.get(SCOPE_SYSTEM, "acquisition_asio_device_name", "")
    asio_host_api = settings.get(SCOPE_SYSTEM, "acquisition_asio_host_api", "")
    asio_target_unit = settings.get(
        SCOPE_SYSTEM, "acquisition_asio_target_unit", DEFAULT_ASIO_TARGET_UNIT
    )
    asio_channel_map = settings.get(
        SCOPE_SYSTEM,
        "acquisition_asio_channel_map",
        list(DEFAULT_ASIO_CHANNEL_MAP),
    )
    configuration = AcquisitionConfiguration(
        str(bind_address),
        {
            unit_identifier: int(value)
            for unit_identifier, value in ports.items()
        },
        source_addresses,
        int(receive_buffer_bytes),
        int(maximum_interpolated_packets),
        int(staging_packets_per_unit),
        enabled_units,
        AcquisitionMode(str(mode)),
        str(asio_device_name),
        str(asio_host_api),
        int(asio_target_unit),
        tuple(asio_channel_map),
    )
    configuration.save(settings)
    return configuration


def _validate_address(address: str, label: str) -> None:
    try:
        ipaddress.IPv4Address(address)
    except ValueError as error:
        raise ValueError(f"{label} must be an IP address") from error
