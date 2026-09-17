"""Non-blocking, source-routed receiver for multiple UATR-TDM units.

Four units at wire rate is 48000 datagrams a second arriving on one socket, and
every Python statement executed per datagram is spent from a budget of about
twenty microseconds. Measurement on the development host: a loop that allocated
a `bytes` object per datagram and tracked sequence numbers one packet at a time
managed roughly 33000 a second once the decode and DSP threads were competing
for the interpreter, and lost 13% to 30% of the stream. Every lost packet leaves
a gap, every gap degrades a processing window, and a degraded window produces no
observations at all — so the whole application went blind for the sake of a few
bytecodes per packet.

So this receives into a preallocated staging buffer through a list of
preallocated `memoryview` slots. Per datagram the loop does a `recvfrom_into`, a
dictionary lookup on the source address, and two list appends; it creates no
objects that the garbage collector has to take back. Sequence accounting is done
once per batch over a NumPy view rather than once per packet, with a fast path
for the ordinary case of contiguous or merely gappy sequence numbers.

Packets leave here as contiguous per-unit blobs, which is also what the decoder
wants: it can read one buffer instead of joining a list of small ones.
"""
from __future__ import annotations

import array
import os
import queue
import socket
import sys
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

try:  # Linux and the other Unixes; absent on Windows.
    import fcntl
    import termios

    FIONREAD = termios.FIONREAD
except ImportError:  # pragma: no cover - exercised only off Unix
    fcntl = None  # type: ignore[assignment]
    FIONREAD = None

from supersilence.infrastructure.acquisition.uatr_tdm import (
    FIRMWARE_SOURCE_PORT,
    PAYLOAD_SIZE,
)

#: Datagrams staged before the receive loop hands a batch over. Large enough
#: that the per-batch NumPy and locking costs are amortized to nothing, small
#: enough that a quiet unit still publishes promptly — the loop also flushes on
#: its 100 ms socket timeout, so a partial batch is never stranded.
FLUSH_PACKETS = 256

#: Room for one flush plus the datagram being received when it fills.
STAGING_SLOTS = FLUSH_PACKETS + 1

#: Windows only. How many flushed-but-not-yet-accounted batches a unit's
#: dispatch-to-worker queue holds before the oldest is dropped. Eight batches
#: is up to 2048 packets of headroom — close to `maximum_packets_per_unit`'s
#: own default — which the accounting worker only needs to eat into if it
#: falls badly behind; see `MultiUnitUdpReceiver._start_windows_dispatch`.
WINDOWS_DISPATCH_QUEUE_BATCHES = 8

#: What the socket asks the kernel for. The kernel grants at most
#: `net.core.rmem_max`, which on a stock Linux is far less, so what was actually
#: granted is reported rather than assumed — see `ReceiverStatus`.
#:
#: Sized deliberately rather than maximally. The buffer exists to absorb the tens
#: of milliseconds the receive thread can be descheduled for; 32 MiB is about
#: 1.7 seconds of one unit's audio at the per-unit default, which is ample for
#: that. Asking for more
#: has a cost that is not obvious: packet age measures time since a packet was
#: *read*, so a unit that has gone silent keeps looking alive for as long as its
#: buffered backlog lasts. At 128 MiB a disconnect took long enough to show that
#: the fault soak stopped seeing it at all.
REQUESTED_RECEIVE_BUFFER_BYTES = 32 << 20

#: Sequence numbers are 32-bit and wrap. Anything at or above this, read as a
#: forward distance, is really a backward step.
SEQUENCE_BACKWARD = 0x80000000

#: How far a sequence number may go *backwards* and still be reordering rather
#: than a restart.
#:
#: A restart is recognised by direction, not by landing on a small number. The
#: earlier rule accepted a restart only when the first sequence the host *saw*
#: was 8 or lower, which is a window of 0.67 milliseconds at 12 000 packets a
#: second — link negotiation after a power cycle always outlasts it. Every
#: packet then failed that test, was counted out of order, was discarded, and,
#: worst of all, left `last_sequence` pointing at the pre-restart stream. The
#: state was absorbing: the unit never recovered until the application itself
#: was restarted, which is exactly what operators had to do.
#:
#: Anything further back than this is a sender that began again. A genuine
#: 32-bit wrap after about four days of continuous transmission is recorded as
#: one spurious restart, which is the harmless reading.
SEQUENCE_REORDER_TOLERANCE = 8

#: Where the kernel publishes what it dropped, per socket. The last column of
#: each row is that socket's `sk_drops`, and the tenth is the inode a socket can
#: be recognised by, so a datagram the kernel threw away can be charged to one
#: unit rather than to the host.
#:
#: This is the measurement that separates the two losses a sequence gap cannot
#: tell apart: a packet the network never delivered, and a packet the kernel
#: delivered while nothing was reading. `netstat -su` answers it for the whole
#: host, which is useless when the simulator, the console and everything else on
#: the machine share the counter.
#:
#: Both families are read because a socket bound to a v4 address on a v6-capable
#: host can appear in either table. Nothing here exists off Linux, and a missing
#: file means the number is unavailable rather than zero — reporting an
#: unmeasured drop count as "no drops" is the one reading that would send an
#: operator looking in the wrong place.
PROCFS_UDP_TABLES = ("/proc/net/udp", "/proc/net/udp6")

#: Column of the socket inode and of the drop counter in those tables.
PROCFS_INODE_COLUMN = 9
PROCFS_DROPS_COLUMN = 12

#: How often the drop tables are re-read. They are parsed in full — a host with
#: many UDP sockets is a few hundred lines — so this is kept off the flush path
#: and out of the way of a status poll that arrives faster than the counters
#: change.
DROP_COUNTER_INTERVAL_SECONDS = 0.25

#: Weight given to the newest flush when smoothing the drain rate. Low, because
#: the rate is only used to turn a backlog into a readable number of seconds and
#: a jumpy one is worse than a slightly stale one.
DRAIN_RATE_ALPHA = 0.2


@dataclass(frozen=True)
class UnitReceiverSnapshot:
    unit_identifier: int
    source_address: str
    received_packets: int
    accepted_packets: int
    lost_packets: int
    sequence_restarts: int
    duplicate_packets: int
    out_of_order_packets: int
    invalid_packets: int
    discarded_buffer_packets: int
    queued_packets: int
    last_packet_monotonic: float | None
    #: Bytes this unit's socket is still holding, and that backlog as time at
    #: the rate its own thread is draining it. Per unit rather than per fleet:
    #: with a socket each, one unit can be seconds behind while the others are
    #: current, and a single fleet-wide number would call all four unreliable
    #: or none of them.
    receive_backlog_bytes: int = 0
    receive_backlog_seconds: float = 0.0
    #: Datagrams the kernel dropped on *this unit's* socket, almost always
    #: because its receive buffer was full when one arrived. Read from the
    #: kernel rather than inferred, and per socket rather than per host, which
    #: is what makes it an attribution: a sequence gap counted in
    #: `lost_packets` is either this, or a packet that never reached the host at
    #: all, and until now nothing here could tell those apart.
    #:
    #: `None` where the kernel does not publish it — anything that is not Linux,
    #: or a socket that has been closed. Not zero: an unmeasured drop count and
    #: a measured absence of drops send an operator to different places.
    kernel_dropped_packets: int | None = None


@dataclass(frozen=True)
class ReceiverStatus:
    unknown_source_packets: int
    last_error: str
    #: What the kernel actually granted for the receive buffer. Loss on this
    #: path arrives in bursts when the receive thread is descheduled, and this
    #: number is how long a burst it can absorb: at four units and 410-byte
    #: datagrams, 8 MiB is about 1.7 seconds of one unit's audio. A host that keeps
    #: losing packets with the loop otherwise keeping up needs this raised,
    #: which is `net.core.rmem_max` and not something the application can do.
    receive_buffer_bytes: int = 0
    #: What the application asked the kernel for. Kept beside what was granted
    #: because the kernel does not refuse an oversized request, it silently
    #: honours `net.core.rmem_max` instead — so a console configured for 32 MiB
    #: can be running on 8 and lose packets in bursts with nothing on screen
    #: saying why. Zero when the receiver is not running.
    #: What the socket asked for. Now per unit: each has its own socket and its
    #: own buffer, so this is the buffer behind one unit rather than behind the
    #: fleet. Zero when the receiver is not running.
    requested_receive_buffer_bytes: int = 0


class _UnitState:
    """One unit's staged packets and everything counted about its stream."""

    def __init__(self, unit_identifier: int, source_address: str, maximum_packets: int):
        self.unit_identifier = unit_identifier
        self.source_address = source_address
        self.maximum_packets = maximum_packets
        #: Contiguous blobs, each holding whole packets end to end. Bounded by
        #: total packets rather than by blob count, because a consumer that
        #: stalls must lose a bounded amount of audio, not a bounded number of
        #: arbitrarily sized batches.
        self.blobs: deque[tuple[bytes, int]] = deque()
        self.queued_packets = 0
        self.last_sequence: int | None = None
        self.received_packets = 0
        self.accepted_packets = 0
        self.lost_packets = 0
        self.sequence_restarts = 0
        self.duplicate_packets = 0
        self.out_of_order_packets = 0
        self.invalid_packets = 0
        self.discarded_buffer_packets = 0
        #: Refreshed from the kernel's own table by the receiver, not counted
        #: here. `None` until it has been read once, and on any host that does
        #: not publish it.
        self.kernel_dropped_packets: int | None = None
        self.last_packet_monotonic: float | None = None
        self.receive_backlog_bytes = 0
        self.receive_backlog_seconds = 0.0
        #: Drain rate, in bytes a second, smoothed across flushes. Smoothed
        #: because one flush is a few milliseconds and its instantaneous rate
        #: swings with scheduling; the backlog delay derived from it would
        #: otherwise flicker between values an operator cannot read.
        self._drain_bytes_per_second = 0.0
        self._last_flush_monotonic: float | None = None

    def observe_backlog(self, backlog: int, flushed_bytes: int, now: float) -> None:
        """Record what the kernel still holds for this unit, and how stale it is.

        The kernel is holding `backlog` bytes this thread has not reached yet,
        and it is draining at roughly `_drain_bytes_per_second`, so the oldest
        thing still waiting arrived about that many seconds ago — and so did the
        packets in this flush, near enough to matter. That is what makes packet
        age honest: age counts from the last packet *read*, so with a backlog a
        unit that has stopped sending keeps looking alive until it drains.

        The alternative was a kernel receive timestamp per datagram, which is
        the exact answer rather than a derived one. Measured on this host,
        ``recvmsg_into`` with ``SO_TIMESTAMPNS`` costs 8.42 microseconds a
        datagram against ``recvfrom_into``'s 5.23 — 61% more in the hot loop.
        This costs one ``ioctl`` per few hundred datagrams and answers the same
        question well enough to act on.

        Caller holds the lock.
        """
        previous = self._last_flush_monotonic
        self._last_flush_monotonic = now
        if previous is not None and now > previous:
            immediate = flushed_bytes / (now - previous)
            if self._drain_bytes_per_second <= 0.0:
                self._drain_bytes_per_second = immediate
            else:
                self._drain_bytes_per_second = (
                    DRAIN_RATE_ALPHA * immediate
                    + (1.0 - DRAIN_RATE_ALPHA) * self._drain_bytes_per_second
                )
        self.receive_backlog_bytes = backlog
        self.receive_backlog_seconds = (
            0.0
            if self._drain_bytes_per_second <= 0.0
            else backlog / self._drain_bytes_per_second
        )

    def stage(self, wire: np.ndarray, now: float) -> None:
        """Account for one batch of this unit's datagrams and queue them.

        ``wire`` is a ``(packets, PAYLOAD_SIZE)`` view in arrival order.
        """
        count = int(wire.shape[0])
        if not count:
            return
        self.received_packets += count
        self.last_packet_monotonic = now
        sequences = (
            (wire[:, 4].astype(np.uint64) << np.uint64(24))
            | (wire[:, 5].astype(np.uint64) << np.uint64(16))
            | (wire[:, 6].astype(np.uint64) << np.uint64(8))
            | wire[:, 7].astype(np.uint64)
        )
        accepted = self._account(sequences, wire)
        if accepted is None:
            return
        self._queue(accepted, count)

    def _account(self, sequences: np.ndarray, wire: np.ndarray) -> np.ndarray | None:
        """Update the stream counters, returning the packets to keep.

        The fast path covers every batch that only moves forward — contiguous,
        or with gaps where the network dropped something. That is what a healthy
        or merely lossy link looks like, and it costs one NumPy pass. Duplicates,
        reordering, and restarts fall back to the exact per-packet rules, which
        is affordable precisely because they are the rare cases.
        """
        previous = self.last_sequence
        first = int(sequences[0])
        forward = None if previous is None else (first - previous) & 0xFFFFFFFF
        steps = np.diff(sequences.astype(np.int64)) & 0xFFFFFFFF
        ordinary = bool(np.all((steps >= 1) & (steps < SEQUENCE_BACKWARD)))
        if ordinary and (
            previous is None or (1 <= forward < SEQUENCE_BACKWARD)
        ):
            if forward is not None:
                self.lost_packets += forward - 1
            self.lost_packets += int(np.sum(steps - 1))
            self.last_sequence = int(sequences[-1])
            self.accepted_packets += int(sequences.shape[0])
            return wire
        return self._account_packet_by_packet(sequences, wire)

    def _account_packet_by_packet(
        self, sequences: np.ndarray, wire: np.ndarray
    ) -> np.ndarray | None:
        keep = np.ones(sequences.shape[0], dtype=bool)
        for index in range(int(sequences.shape[0])):
            sequence = int(sequences[index])
            previous = self.last_sequence
            if previous is None:
                self.last_sequence = sequence
                self.accepted_packets += 1
                continue
            forward = (sequence - previous) & 0xFFFFFFFF
            if forward == 0:
                self.duplicate_packets += 1
                keep[index] = False
                continue
            if forward == 1:
                self.last_sequence = sequence
            elif forward < SEQUENCE_BACKWARD:
                self.lost_packets += forward - 1
                self.last_sequence = sequence
            elif (previous - sequence) & 0xFFFFFFFF <= SEQUENCE_REORDER_TOLERANCE:
                # A few places back: the network delivered out of order. Drop the
                # late copy and keep expecting what we were already expecting.
                self.out_of_order_packets += 1
                keep[index] = False
                continue
            else:
                # Far back: the sender began again. Adopt its numbering, keep the
                # packet, and let the sample assembler mark the discontinuity —
                # refusing it here is what used to strand the unit permanently.
                self.sequence_restarts += 1
                self.last_sequence = sequence
            self.accepted_packets += 1
        if not np.any(keep):
            return None
        return wire if np.all(keep) else wire[keep]

    def _queue(self, accepted: np.ndarray, arrived: int) -> None:
        del arrived
        count = int(accepted.shape[0])
        blob = accepted.tobytes()
        self.blobs.append((blob, count))
        self.queued_packets += count
        # Oldest first, packet by packet rather than blob by blob: with the
        # consumer behind, recent audio is what can still become a target, and
        # discarding a whole batch to shed one packet would throw away audio the
        # buffer had room for.
        while self.queued_packets > self.maximum_packets and self.blobs:
            excess = self.queued_packets - self.maximum_packets
            oldest, oldest_count = self.blobs[0]
            if oldest_count <= excess:
                self.blobs.popleft()
                self.queued_packets -= oldest_count
                self.discarded_buffer_packets += oldest_count
                continue
            self.blobs[0] = (
                oldest[excess * PAYLOAD_SIZE :],
                oldest_count - excess,
            )
            self.queued_packets -= excess
            self.discarded_buffer_packets += excess

    def take(self, maximum_packets: int) -> tuple[bytes, int]:
        """Hand over up to ``maximum_packets`` staged packets, contiguously."""
        if not self.blobs:
            return b"", 0
        if maximum_packets <= 0:
            maximum_packets = self.queued_packets
        pieces: list[bytes] = []
        taken = 0
        while self.blobs and taken < maximum_packets:
            blob, count = self.blobs[0]
            if taken + count <= maximum_packets:
                self.blobs.popleft()
                pieces.append(blob)
                taken += count
                continue
            wanted = maximum_packets - taken
            pieces.append(blob[: wanted * PAYLOAD_SIZE])
            self.blobs[0] = (blob[wanted * PAYLOAD_SIZE :], count - wanted)
            taken += wanted
        self.queued_packets -= taken
        if len(pieces) == 1:
            return pieces[0], taken
        return b"".join(pieces), taken

    def snapshot(self) -> UnitReceiverSnapshot:
        return UnitReceiverSnapshot(
            self.unit_identifier,
            self.source_address,
            self.received_packets,
            self.accepted_packets,
            self.lost_packets,
            self.sequence_restarts,
            self.duplicate_packets,
            self.out_of_order_packets,
            self.invalid_packets,
            self.discarded_buffer_packets,
            self.queued_packets,
            self.last_packet_monotonic,
            self.receive_backlog_bytes,
            self.receive_backlog_seconds,
            self.kernel_dropped_packets,
        )

def _backlog_bytes(receiver: socket.socket) -> int:
    """What the kernel is still holding on one socket, asked once per flush.

    Cheap enough at one call per few hundred datagrams, and it is the only way
    to tell "this unit stopped sending" from "we have not caught up".

    Returns zero where `FIONREAD` cannot be asked for — every platform without
    `fcntl`, which is Windows. The backlog then reads as permanently drained,
    which is the harmless direction: it turns the "we are behind" warning off
    rather than raising a false one, and the lost- and dropped-packet counters
    still report an overrun.
    """
    if fcntl is None:
        return 0
    try:
        waiting = array.array("i", [0])
        fcntl.ioctl(receiver.fileno(), FIONREAD, waiting, True)
        return int(waiting[0])
    except (OSError, ValueError):
        # ValueError is a closed socket: `stop` closes every socket and each
        # thread then runs one last flush, so asking a descriptor of -1 for its
        # backlog is the ordinary way a receiver shuts down, not a fault.
        return 0


def read_socket_drop_counters() -> dict[int, int]:
    """Every UDP socket's drop count on this host, keyed by inode.

    Returns an empty mapping where the tables do not exist, which is every
    platform that is not Linux. The caller turns that into "unavailable" rather
    than into zero.
    """
    counters: dict[int, int] = {}
    for path in PROCFS_UDP_TABLES:
        try:
            with open(path, "r", encoding="ascii", errors="replace") as table:
                next(table, None)  # the header row
                for line in table:
                    columns = line.split()
                    if len(columns) <= PROCFS_DROPS_COLUMN:
                        continue
                    try:
                        inode = int(columns[PROCFS_INODE_COLUMN])
                        drops = int(columns[PROCFS_DROPS_COLUMN])
                    except ValueError:
                        continue
                    counters[inode] = drops
        except OSError:
            continue
    return counters


class MultiUnitUdpReceiver:
    """Receive every unit on its own socket, on that unit's own UDP port.

    Each board has its own address *and* its own port — 192.168.1.101:5005
    through 192.168.1.104:5008 — and transmits from the same port it sends to.
    None of that is ours to choose; what is ours is how many sockets listen.

    One socket for the fleet was the obvious reading of the older single-port
    firmware, and it cost more than it looked. Four units sharing one kernel
    receive buffer means a consumer that stalls on one unit overflows the buffer
    for all four — measured at 43% to 56% packet loss on the three healthy units
    while one had an overloaded consumer, against zero loss for those three on
    separate sockets with a quarter of the buffer each. Triangulation needs two
    units in an epoch, so a fleet-wide loss is not a degraded fix, it is no fix.

    Separate ports make that separation the kernel's own rather than something
    this class arranges on top of a shared port. Each unit gets a socket bound
    to its port and `connect`ed to its address and port, so the kernel delivers
    each unit's datagrams to its own socket, its own buffer, and its own thread.
    Source routing is not a Python dictionary lookup per datagram; it already
    happened on the way in.

    A wildcard socket is bound **per distinct port** to catch everything that
    matches no unit, which is what `unknown_source_packets` counts. It also
    catches a board still running an image that transmits from the old shared
    5005 to a console listening on 5008 — a mis-flash that would otherwise look
    exactly like a dead unit, and which nothing physical on the board tells you
    about.
    """

    def __init__(
        self,
        bind_address: str,
        ports: dict[int, int],
        units_by_source_address: dict[str, int],
        *,
        maximum_packets_per_unit: int = 2_000,
        receive_buffer_bytes: int = REQUESTED_RECEIVE_BUFFER_BYTES,
        source_ports: dict[int, int] | None = None,
        drop_counter_source: Callable[[], dict[int, int]] = read_socket_drop_counters,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not units_by_source_address:
            raise ValueError("at least one unit source address is required")
        if len(set(units_by_source_address.values())) != len(units_by_source_address):
            raise ValueError("unit identifiers must be unique")
        if maximum_packets_per_unit <= 0:
            raise ValueError("maximum packets per unit must be positive")
        identifiers = set(units_by_source_address.values())
        if not identifiers <= set(ports):
            raise ValueError("every unit needs a port")
        # A board transmits from the port it transmits to. `source_ports`
        # exists for a board that does not.
        self._explicit_source_ports = {
            int(identifier): int(port)
            for identifier, port in (source_ports or {}).items()
        }
        for source_port in self._explicit_source_ports.values():
            if not 1 <= source_port <= 65_535:
                raise ValueError("unit source port must be between 1 and 65535")
        self._bind_address = bind_address
        self._requested_receive_buffer_bytes = receive_buffer_bytes
        self._requested_ports = {
            identifier: int(ports[identifier]) for identifier in identifiers
        }
        self._states = {
            address: _UnitState(identifier, address, maximum_packets_per_unit)
            for address, identifier in units_by_source_address.items()
        }
        self._states_by_identifier = {
            state.unit_identifier: state for state in self._states.values()
        }
        self._lock = threading.Lock()
        self._stop = threading.Event()
        #: One per unit. Empty until started, and emptied again by `stop`.
        self._sockets: dict[int, socket.socket] = {}
        #: One per distinct bound port, keyed by that port. These are the
        #: sockets that see datagrams belonging to no unit.
        self._wildcards: dict[int, socket.socket] = {}
        self._threads: list[threading.Thread] = []
        #: The port each unit is actually bound to. Only differs from the
        #: requested one when the caller asked for zero, which tests do.
        self._bound_ports: dict[int, int] = {}
        self.unknown_source_packets = 0
        self.last_error = ""
        self.receive_buffer_bytes = 0
        self._drop_counter_source = drop_counter_source
        self._clock = clock
        #: Unit identifier by socket inode, filled in at `start`. The inode is
        #: how a socket is found in the kernel's table; it is read once, because
        #: it cannot change while the socket is open.
        self._unit_by_inode: dict[int, int] = {}
        self._drops_read_at: float | None = None
        #: Windows only. Populated by `_start_windows_dispatch`, emptied by
        #: `stop`; see that method for why Windows needs them at all.
        self._windows_queues: dict[int, queue.Queue] = {}
        self._windows_lookup: dict[tuple[str, int], int] = {}

    @property
    def ports(self) -> dict[int, int]:
        """The port each unit is bound to, or was asked to bind."""
        return {
            identifier: self._bound_ports.get(identifier, requested)
            for identifier, requested in self._requested_ports.items()
        }

    def port_for(self, unit_identifier: int) -> int:
        return self.ports[unit_identifier]

    @property
    def running(self) -> bool:
        # Every thread is required. On Linux these are one receive path per
        # unit plus the wildcard observers; on Windows they include every port
        # dispatcher and accounting worker. `any` let one surviving wildcard
        # hide a dead unit thread forever, so the service never rebuilt the
        # failed sockets and that unit recovered only with an app restart.
        return bool(self._threads) and all(
            thread.is_alive() for thread in self._threads
        )

    def start(self) -> None:
        if self.running:
            return
        if self._sockets or self._threads:
            self.stop()
        try:
            # Units are grouped by the port they asked for, because a wildcard
            # is bound once per port and not once per unit. Two units on one
            # port is a legitimate configuration — the boards then differ by
            # address, as they did before per-board ports existed.
            for requested_port, states in self._states_by_requested_port().items():
                # The wildcard binds first because it is the socket that decides
                # the port when the caller asked for zero. Binding order does
                # not affect delivery: the kernel scores by how specific a
                # socket's address pair is, not by when it was bound.
                wildcard = self._open_socket(requested_port)
                bound_port = int(wildcard.getsockname()[1])
                self._wildcards[bound_port] = wildcard
                for state in states:
                    self._bound_ports[state.unit_identifier] = bound_port
                # Windows has nothing to attach a per-unit connected socket to;
                # see `_start_windows_dispatch`. It gets the wildcards alone.
                if sys.platform != "win32":
                    for state in states:
                        self._sockets[state.unit_identifier] = self._open_socket(
                            requested_port,
                            (
                                state.source_address,
                                self._source_port_for(state.unit_identifier, bound_port),
                            ),
                            bound_port=bound_port,
                        )
        except BaseException:
            self._close_sockets()
            raise
        # Every unit's socket asks for the same buffer, so any of them reports
        # what the kernel granted.
        self.receive_buffer_bytes = int(
            next(iter(self._wildcards.values())).getsockopt(
                socket.SOL_SOCKET, socket.SO_RCVBUF
            )
        )
        self._unit_by_inode = {}
        self._drops_read_at = None
        for unit_identifier, unit_socket in self._sockets.items():
            try:
                self._unit_by_inode[os.fstat(unit_socket.fileno()).st_ino] = (
                    unit_identifier
                )
            except OSError:
                continue
        self._stop.clear()
        self.last_error = ""
        if sys.platform == "win32":
            self._start_windows_dispatch()
            return
        for unit_identifier, unit_socket in self._sockets.items():
            state = self._states_by_identifier[unit_identifier]
            thread = threading.Thread(
                target=(
                    lambda state=state, unit_socket=unit_socket: self._receive_unit(
                        state, unit_socket
                    )
                ),
                daemon=True,
                name=f"uatr-tdm-receiver-{unit_identifier}",
            )
            self._threads.append(thread)
            thread.start()
        for bound_port, wildcard in self._wildcards.items():
            thread = threading.Thread(
                target=(
                    lambda wildcard=wildcard: self._receive_unknown(wildcard)
                ),
                daemon=True,
                name=f"uatr-tdm-receiver-unknown-{bound_port}",
            )
            self._threads.append(thread)
            thread.start()

    def _states_by_requested_port(self) -> dict[int, list["_UnitState"]]:
        grouped: dict[int, list[_UnitState]] = {}
        for state in self._states.values():
            grouped.setdefault(
                self._requested_ports[state.unit_identifier], []
            ).append(state)
        return grouped

    def _source_port_for(self, unit_identifier: int, bound_port: int) -> int:
        """The port this unit transmits *from*.

        A board transmits from the port it transmits to, so the destination
        port is the default. An explicit `source_ports` entry wins, which is
        what describes a board whose two ports differ.

        Port zero — an ephemeral bind, which is what tests ask for — cannot
        mean "whatever the kernel gave us", because a board cannot know that
        number. It falls back to the firmware's own constant instead, so a
        receiver on an ephemeral port still expects a real unit's source port.
        """
        explicit = self._explicit_source_ports.get(unit_identifier)
        if explicit is not None:
            return explicit
        requested = self._requested_ports[unit_identifier]
        return requested if requested else FIRMWARE_SOURCE_PORT

    def _open_socket(
        self,
        requested_port: int,
        connect_to: tuple[str, int] | None = None,
        *,
        bound_port: int | None = None,
    ) -> socket.socket:
        """One socket on one unit's port, optionally connected to its pair."""
        receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Without this the second bind of the same port is refused. It does
            # not load-balance these sockets against each other: a connected
            # socket outscores the wildcard, so each unit's datagrams have
            # exactly one place to go.
            #
            # `SO_REUSEPORT` is POSIX and the name is simply absent from the
            # `socket` module on Windows. Nothing is lost by skipping it there:
            # Windows gives `SO_REUSEADDR` the wider meaning this line is here
            # for, so the second bind of the same port already succeeds. The
            # option is set where it exists rather than dropped everywhere,
            # because on Linux `SO_REUSEADDR` alone does not permit it.
            if hasattr(socket, "SO_REUSEPORT"):
                receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            try:
                receiver.setsockopt(
                    socket.SOL_SOCKET,
                    socket.SO_RCVBUF,
                    self._requested_receive_buffer_bytes,
                )
            except OSError:
                pass
            receiver.settimeout(0.1)
            receiver.bind((self._bind_address, bound_port or requested_port))
            if connect_to is not None:
                receiver.connect(connect_to)
        except BaseException:
            receiver.close()
            raise
        return receiver

    def _close_sockets(self) -> None:
        for receiver in self._sockets.values():
            receiver.close()
        self._sockets.clear()
        for receiver in self._wildcards.values():
            receiver.close()
        self._wildcards.clear()

    def stop(self) -> None:
        self._stop.set()
        self._close_sockets()
        threads, self._threads = self._threads, []
        for thread in threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        self._bound_ports = {}
        # The inodes are gone with the sockets, and the kernel reuses them. A
        # stale one would charge another process's drops to a unit.
        self._unit_by_inode = {}
        self._drops_read_at = None
        self._windows_queues = {}
        self._windows_lookup = {}

    def drain_blob(
        self, unit_identifier: int, maximum_packets: int = 0
    ) -> tuple[bytes, int]:
        """Staged packets for one unit as one contiguous buffer and a count.

        This is the path the real-time consumer uses: the decoder reads the
        buffer directly, so no packet ever becomes an individual Python object
        between the socket and NumPy.
        """
        state = self._states_by_identifier[unit_identifier]
        with self._lock:
            return state.take(maximum_packets)

    def drain(self, unit_identifier: int, maximum_packets: int = 0) -> tuple[bytes, ...]:
        """The same packets, split into individual payloads.

        Kept for callers that want packets one at a time — tests, and anything
        inspecting a single datagram. It costs one object per packet, which is
        exactly what the consumer path avoids.
        """
        blob, count = self.drain_blob(unit_identifier, maximum_packets)
        return tuple(
            blob[index * PAYLOAD_SIZE : (index + 1) * PAYLOAD_SIZE]
            for index in range(count)
        )

    def _refresh_kernel_drops(self) -> None:
        """Charge the kernel's drop counters to the units that own the sockets.

        Called from the status path rather than from the receive loop: at four
        units and wire rate the loop has about twenty microseconds a datagram,
        and reading a procfs table in it would cost more than the packets it is
        trying to account for.
        """
        if not self._unit_by_inode:
            return
        now = self._clock()
        if (
            self._drops_read_at is not None
            and now - self._drops_read_at < DROP_COUNTER_INTERVAL_SECONDS
        ):
            return
        counters = self._drop_counter_source()
        self._drops_read_at = now
        if not counters:
            return
        with self._lock:
            for inode, unit_identifier in self._unit_by_inode.items():
                drops = counters.get(inode)
                if drops is None:
                    continue
                self._states_by_identifier[unit_identifier].kernel_dropped_packets = (
                    drops
                )

    def snapshots(self) -> tuple[UnitReceiverSnapshot, ...]:
        self._refresh_kernel_drops()
        with self._lock:
            return tuple(
                state.snapshot()
                for state in sorted(
                    self._states.values(), key=lambda item: item.unit_identifier
                )
            )

    def status(self) -> ReceiverStatus:
        with self._lock:
            return ReceiverStatus(
                self.unknown_source_packets,
                self.last_error,
                self.receive_buffer_bytes,
                self._requested_receive_buffer_bytes if self._sockets else 0,
            )

    def _receive_unit(self, state: "_UnitState", receiver: socket.socket) -> None:
        """One unit's hot loop. Everything it needs is allocated before it starts.

        No source address is read and no routing is done: this socket is
        connected to one unit, so every datagram that reaches it is that unit's.
        """
        staging = bytearray(STAGING_SLOTS * PAYLOAD_SIZE)
        view = memoryview(staging)
        # One memoryview per slot, made once: slicing a memoryview inside the
        # loop would allocate an object per datagram, which is the cost this
        # whole design exists to avoid.
        slots = [
            view[index * PAYLOAD_SIZE : (index + 1) * PAYLOAD_SIZE]
            for index in range(STAGING_SLOTS)
        ]
        index = 0
        stop_is_set = self._stop.is_set
        try:
            while not stop_is_set():
                try:
                    received = receiver.recv_into(slots[index], PAYLOAD_SIZE)
                except socket.timeout:
                    index = self._flush(state, receiver, staging, index)
                    continue
                except OSError as error:
                    if not stop_is_set():
                        with self._lock:
                            self.last_error = str(error)
                    break
                if received != PAYLOAD_SIZE:
                    # A short datagram cannot be a packet, and a long one was
                    # truncated into the slot; either way it is not decodable.
                    with self._lock:
                        state.invalid_packets += 1
                    continue
                index += 1
                if index >= FLUSH_PACKETS:
                    index = self._flush(state, receiver, staging, index)
        finally:
            self._flush(state, receiver, staging, index)

    def _receive_unknown(self, receiver: socket.socket) -> None:
        """Everything addressed to one bound port that belongs to no unit.

        Counted rather than ignored. A datagram here is a misconfigured source
        address, another application on the port, or a board transmitting from
        a port this console does not expect — a board still carrying a
        single-port image, most likely, which nothing physical on it announces.
        All three are worth seeing, and the last would otherwise be
        indistinguishable from a unit that is switched off.
        """
        scratch = memoryview(bytearray(2 * PAYLOAD_SIZE))
        stop_is_set = self._stop.is_set
        while not stop_is_set():
            try:
                receiver.recv_into(scratch)
            except socket.timeout:
                continue
            except OSError as error:
                if not stop_is_set():
                    with self._lock:
                        self.last_error = str(error)
                break
            with self._lock:
                self.unknown_source_packets += 1

    def _start_windows_dispatch(self) -> None:
        """Windows has nothing for the per-unit sockets above to attach to.

        Isolated outside pytest, on a real Windows host: bind a wildcard socket
        and a second socket to the same port, `connect()` the second to a
        specific peer, `SO_REUSEADDR` on both — every datagram from that peer
        still lands on the wildcard. Windows does not score a connected
        socket's four-tuple above a wildcard bind the way Linux does, so
        `_open_socket`'s per-unit sockets above would exist but never receive
        anything; `start` does not create them here.

        So Windows gets one socket, one thread reading it, and a `dict` lookup
        on the source address to route each datagram — conceptually the
        single-socket design this module's own top docstring describes and
        measured against on Linux, where a stalled consumer starved every unit
        sharing its one kernel buffer. That risk is not something Windows can
        avoid by having several sockets, because it cannot get several kernel
        buffers here in the first place — there is only the one socket. What
        *can* still be kept off the wire-reading path is the accounting: the
        dispatch loop below only copies a datagram into its unit's staging slot
        and, once a batch fills, hands it to that unit's own worker thread
        without waiting for the accounting to finish. A unit whose sequence
        accounting falls behind backs up its own bounded queue, not the socket
        the other units are being read from.

        One consequence worth naming: `received_packets` is only counted once
        a batch is accounted for, in the worker. On Linux it is counted by the
        kernel's own delivery to a unit's socket, so it stays accurate even
        under backpressure; here, a unit whose worker falls far enough behind
        to overflow its queue (see `WINDOWS_DISPATCH_QUEUE_BATCHES`) undercounts
        by however many packets were dropped before they were ever staged.
        """
        self._windows_queues = {
            state.unit_identifier: queue.Queue(maxsize=WINDOWS_DISPATCH_QUEUE_BATCHES)
            for state in self._states.values()
        }
        self._windows_lookup = {
            (
                state.source_address,
                self._source_port_for(
                    state.unit_identifier,
                    self._bound_ports[state.unit_identifier],
                ),
            ): state.unit_identifier
            for state in self._states.values()
        }
        for state in self._states.values():
            worker = threading.Thread(
                target=self._windows_unit_worker,
                args=(state,),
                daemon=True,
                name=f"uatr-tdm-worker-{state.unit_identifier}",
            )
            self._threads.append(worker)
            worker.start()
        # One dispatcher per bound port. Windows delivers everything on a port
        # to that port's wildcard socket, so there is one hot loop per port
        # rather than one for the fleet — which is the one place the per-board
        # ports buy Windows something the shared port could not.
        for bound_port, wildcard in self._wildcards.items():
            dispatcher = threading.Thread(
                target=self._windows_dispatch,
                args=(wildcard,),
                daemon=True,
                name=f"uatr-tdm-receiver-dispatch-{bound_port}",
            )
            self._threads.append(dispatcher)
            dispatcher.start()

    def _windows_dispatch(self, receiver: socket.socket) -> None:
        """The Windows hot loop: read, look up, copy into the unit's slot.

        No accounting happens here — see `_start_windows_dispatch`. A full
        batch is handed to the unit's worker by `_windows_flush` and this loop
        goes straight back to `recvfrom_into`.
        """
        staging = {
            identifier: bytearray(STAGING_SLOTS * PAYLOAD_SIZE)
            for identifier in self._states_by_identifier
        }
        indices = {identifier: 0 for identifier in self._states_by_identifier}
        scratch = bytearray(PAYLOAD_SIZE)
        stop_is_set = self._stop.is_set
        lookup = self._windows_lookup
        try:
            while not stop_is_set():
                try:
                    received, address = receiver.recvfrom_into(scratch)
                except socket.timeout:
                    for identifier in indices:
                        indices[identifier] = self._windows_flush(
                            identifier, staging[identifier], indices[identifier]
                        )
                    continue
                except OSError as error:
                    if not stop_is_set():
                        with self._lock:
                            self.last_error = str(error)
                    break
                unit_identifier = lookup.get(address)
                if unit_identifier is None:
                    with self._lock:
                        self.unknown_source_packets += 1
                    continue
                if received != PAYLOAD_SIZE:
                    with self._lock:
                        self._states_by_identifier[unit_identifier].invalid_packets += 1
                    continue
                index = indices[unit_identifier]
                buffer = staging[unit_identifier]
                buffer[index * PAYLOAD_SIZE : (index + 1) * PAYLOAD_SIZE] = scratch[
                    :received
                ]
                index += 1
                if index >= FLUSH_PACKETS:
                    index = self._windows_flush(unit_identifier, buffer, index)
                indices[unit_identifier] = index
        finally:
            for identifier in indices:
                self._windows_flush(identifier, staging[identifier], indices[identifier])

    def _windows_flush(
        self, unit_identifier: int, staging: bytearray, index: int
    ) -> int:
        """Hand one unit's staged batch to its worker queue. Returns the new index."""
        if not index:
            return 0
        blob = bytes(staging[: index * PAYLOAD_SIZE])
        item = (blob, index, time.monotonic())
        pending = self._windows_queues[unit_identifier]
        while True:
            try:
                pending.put_nowait(item)
                return 0
            except queue.Full:
                try:
                    _, dropped_count, _ = pending.get_nowait()
                except queue.Empty:
                    continue
                with self._lock:
                    self._states_by_identifier[
                        unit_identifier
                    ].discarded_buffer_packets += dropped_count

    def _windows_unit_worker(self, state: "_UnitState") -> None:
        """One unit's accounting, off the thread that is reading the wire."""
        pending = self._windows_queues[state.unit_identifier]
        stop_is_set = self._stop.is_set
        while True:
            try:
                blob, count, arrived_at = pending.get(timeout=0.1)
            except queue.Empty:
                if stop_is_set():
                    return
                continue
            wire = np.frombuffer(
                blob, dtype=np.uint8, count=count * PAYLOAD_SIZE
            ).reshape(count, PAYLOAD_SIZE)
            with self._lock:
                state.stage(wire, arrived_at)

    def _flush(
        self,
        state: "_UnitState",
        receiver: socket.socket,
        staging: bytearray,
        index: int,
    ) -> int:
        """Hand one unit's staged batch to its state. Returns the new index."""
        if not index:
            return 0
        wire = np.frombuffer(
            staging, dtype=np.uint8, count=index * PAYLOAD_SIZE
        ).reshape(index, PAYLOAD_SIZE)
        now = time.monotonic()
        backlog = _backlog_bytes(receiver)
        with self._lock:
            state.observe_backlog(backlog, index * PAYLOAD_SIZE, now)
            state.stage(wire, now)
        return 0
