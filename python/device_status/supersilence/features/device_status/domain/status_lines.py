"""What the console status bar used to cram into one line, spelled out.

The bottom bar had to say `U1 12000/s age 0.1s L0 R0 I0 D0 O0 Qp0/Qb0 Qw0 X0` to
fit, which is readable only to someone who already knows what every letter means.
Given a window to put it in, each counter gets its name and its unit back.

Formatting lives here, away from Qt, because what counts as "never", what counts
as an error, and which counters an operator is meant to read together are
decisions worth testing without a display.
"""

from __future__ import annotations

UNAVAILABLE = "—"

#: Counters that mean something is wrong when they are not zero. The window
#: draws these in the alert colour so a nonzero one is visible without reading.
ACQUISITION_ALERT_ROWS = frozenset(
    {
        "Lost packets",
        # The two halves of a lost packet. Both are faults and they are fixed in
        # different places: one is this host not reading fast enough, the other
        # is the link or the unit.
        "Dropped by this host",
        "Lost before this host",
        "Invalid packets",
        "Sequence restarts",
        "Duplicate packets",
        "Out-of-order packets",
        "Raw queue overflows",
        "Sample queue overflows",
        "Window queue overflows",
        "Callback faults",
        "Dropped input blocks",
        "Callback status",
        "Unknown-source packets",
        "Receiver error",
    }
)

TELEMETRY_ALERT_ROWS = frozenset({"Invalid messages", "Oversized frames", "Disconnects", "Dropped samples", "Error"})

PIPELINE_ALERT_ROWS = frozenset(
    {
        "Windows refused (degraded input)",
        "Dropped frames",
        "Transform error",
        "Identity error",
        "Worker error",
        "Rays behind intersection",
    }
)

PIPELINE_ALERT_VALUES: dict[str, frozenset[str]] = {
    "Array": frozenset({"collinear", "no unit positions configured"}),
}

#: What a shortfall between the requested and the granted receive buffer reads
#: as. A row that alerts on a substring rather than on a whole value, because the
#: rest of the row is a legitimate number the operator still wants to see.
RECEIVE_BUFFER_SHORTFALL = "requested"


def _age(seconds: float | None) -> str:
    """A packet age of ``None`` means nothing has ever arrived, not zero age."""
    return "never" if seconds is None else f"{seconds:.1f} s"


def _receive_buffer(size_bytes: int, requested_bytes: int = 0) -> str:
    """The kernel's granted socket buffer, and how much audio it absorbs.

    Loss on this path arrives in bursts when the receive thread is descheduled,
    so this is the number that says how long a stall the host survives. It is
    raised with `net.core.rmem_max`, which the application cannot do for itself.

    Which is why the request is named whenever it was not met. The kernel does
    not refuse an oversized `SO_RCVBUF`; it grants what `net.core.rmem_max`
    allows and says nothing. A console set to 32 MiB and running on 8 loses
    packets in bursts, and every counter that could explain it — lost packets,
    refused windows — is downstream of the one fact that would.
    """
    if size_bytes <= 0:
        return UNAVAILABLE
    # One unit's stream: 410-byte datagrams, 12000 packets a second. This buffer
    # belongs to one unit's socket, not to the fleet — dividing by the fleet rate
    # would quote a quarter of the stall it actually absorbs.
    seconds = size_bytes / (410 * 12_000)
    granted = f"{size_bytes / (1 << 20):.1f} MiB ({seconds * 1000:.0f} ms of one unit's audio)"
    if requested_bytes <= size_bytes:
        return granted
    return f"{granted} — {requested_bytes / (1 << 20):.1f} MiB requested; raise net.core.rmem_max"


#: A backlog under this is not worth qualifying a packet age with: it is less
#: than one fleet epoch, so nothing the operator reads is meaningfully stale.
TRUSTWORTHY_BACKLOG_SECONDS = 0.5


def _backlog(size_bytes: int, seconds: float) -> str:
    """What the kernel is still holding, and therefore how stale everything is.

    Packet age counts from the last packet *read*. While a backlog exists, a unit
    that has stopped sending still looks alive, so this is the number that says
    whether packet age can be believed.

    The seconds come measured from the receiver, at the rate it is actually
    draining. They used to be derived here from the nominal wire rate, which
    understates the delay in exactly the case that matters — a loop falling
    behind is draining slower than wire rate, so dividing by wire rate makes the
    backlog look shorter than it is.
    """
    if size_bytes <= 0:
        return "0 (current)"
    return f"{size_bytes / 1024:.0f} KiB ({seconds * 1000:.0f} ms behind)"


def _qualified_age(seconds: float | None, backlog_seconds: float) -> str:
    """Packet age, and how far it can be trusted.

    An age reads as "this unit was heard from recently". While a backlog exists
    that is not what it means: it means the unit was heard from recently *in the
    part of the stream we have reached*. A unit that stopped sending keeps
    reporting a small age for as long as its backlog lasts, which is how a
    disconnect went unnoticed for a whole soak.
    """
    age = _age(seconds)
    if seconds is None or backlog_seconds < TRUSTWORTHY_BACKLOG_SECONDS:
        return age
    return f"{age} (unreliable: {backlog_seconds:.1f} s behind)"


def _kernel_drops(health) -> str:
    """What the kernel had for this unit and threw away.

    Read per socket from the kernel's own table. `None` means the host does not
    publish it, and that is reported as unavailable rather than as zero: an
    operator told "0 dropped" stops looking here, which is the wrong thing to do
    when the number was never measured.
    """
    drops = getattr(health, "kernel_dropped_packets", None)
    if drops is None:
        return UNAVAILABLE
    return f"{drops}"


def _loss_before_this_host(health) -> str:
    """Lost packets that this host cannot be charged with.

    A sequence gap says a packet is missing, not where it went. The kernel's
    per-socket drop counter says how many of them this host was handed and did
    not read; what is left never reached the socket at all — the link, a switch,
    or the unit. Clamped at zero, because the two counters are sampled at
    different instants and a drop counted just after a snapshot would otherwise
    read as negative loss.
    """
    drops = getattr(health, "kernel_dropped_packets", None)
    if drops is None:
        return UNAVAILABLE
    return f"{max(0, health.lost_packets - drops)}"


def describe_acquisition(health) -> tuple[tuple[str, str], ...]:
    """Every acquisition counter for one unit, as caption and value."""
    if getattr(health, "source", "ethernet") == "asio":
        sample_rate = UNAVAILABLE if health.input_sample_rate <= 0 else f"{health.input_sample_rate} Hz"
        return (
            ("Source type", "ASIO"),
            ("Input device", health.device_name),
            ("Host API", health.host_api),
            ("Input sample rate", sample_rate),
            ("Callback faults", f"{health.callback_faults}"),
            ("Dropped input blocks", f"{health.dropped_input_blocks}"),
            ("Queued windows", f"{health.queued_windows}"),
            (
                "Window queue overflows",
                f"{health.window_queue_overflow_windows}",
            ),
            ("Callback status", health.last_callback_status or UNAVAILABLE),
            ("Receiver error", health.receiver_error or UNAVAILABLE),
        )
    return (
        ("Source address", health.source_address),
        ("Packet rate", f"{health.packet_rate:.0f}/s"),
        (
            "Packet age",
            _qualified_age(health.packet_age_seconds, health.receive_backlog_seconds),
        ),
        ("Received packets", f"{health.received_packets}"),
        ("Accepted packets", f"{health.accepted_packets}"),
        ("Lost packets", f"{health.lost_packets}"),
        ("Dropped by this host", _kernel_drops(health)),
        ("Lost before this host", _loss_before_this_host(health)),
        ("Sequence restarts", f"{health.sequence_restarts}"),
        ("Invalid packets", f"{health.invalid_packets}"),
        ("Duplicate packets", f"{health.duplicate_packets}"),
        ("Out-of-order packets", f"{health.out_of_order_packets}"),
        ("Queued raw packets", f"{health.queued_packets}"),
        ("Raw queue overflows", f"{health.queue_overflow_packets}"),
        ("Queued sample blocks", f"{health.queued_sample_blocks}"),
        ("Sample queue overflows", f"{health.sample_queue_overflow_blocks}"),
        ("Queued windows", f"{health.queued_windows}"),
        ("Window queue overflows", f"{health.window_queue_overflow_windows}"),
        ("Unknown-source packets", f"{health.unknown_source_packets}"),
        (
            "Receive buffer",
            _receive_buffer(
                health.receive_buffer_bytes,
                getattr(health, "requested_receive_buffer_bytes", 0),
            ),
        ),
        (
            "Receiver backlog",
            _backlog(health.receive_backlog_bytes, health.receive_backlog_seconds),
        ),
        ("Receiver error", health.receiver_error or UNAVAILABLE),
    )


def describe_telemetry(health) -> tuple[tuple[str, str], ...]:
    """Every telemetry counter for one unit, as caption and value."""
    sample = health.latest_sample
    if sample is None:
        latest = UNAVAILABLE
    else:
        latest = ", ".join(sample.raw_fields) or "not retained"
    return (
        ("Endpoint", f"{health.sensor_address}:{health.port}"),
        ("State", health.state.value),
        ("Valid-message age", _age(health.message_age_seconds)),
        ("Bytes received", f"{health.bytes_received}"),
        ("Valid messages", f"{health.valid_messages}"),
        ("Invalid messages", f"{health.invalid_messages}"),
        ("Oversized frames", f"{health.oversized_frames}"),
        ("Connection attempts", f"{health.connection_attempts}"),
        ("Successful connections", f"{health.successful_connections}"),
        ("Disconnects", f"{health.disconnects}"),
        ("Latest raw fields", latest),
        ("Error", health.last_error or UNAVAILABLE),
    )


#: Rows where a nonzero value is normal rather than a fault. Skipped windows are
#: the provider staying current, and refused solutions are it refusing to place a
#: contact it cannot place — both are the design working.
PIPELINE_NEUTRAL_ROWS = frozenset(
    {
        "Windows skipped",
        "Solutions refused",
        "Refusals",
        "Meaning",
        # A rate and a mean are a measurement of this host, not a fault count.
        # What they mean depends on the epoch window beside them, which is why
        # they are read rather than alerted on.
        "Epoch cadence",
    }
)


def describe_pipeline(health) -> tuple[tuple[str, str], ...]:
    """The target provider's stage counts, in the order the data flows.

    Read top to bottom, this says where targets are being lost. Windows without
    observations means the water is quiet or the input is damaged; observations
    without epoch contributors means they arrive too late to be combined;
    contributors without associations means the units are not hearing the same
    frequency; associations without solutions means the geometry is refusing.
    """
    if health is None:
        return (("State", "no target provider"),)
    return (
        ("Running", "yes" if health.running else "no"),
        ("Orientation", "available" if health.orientation_available else "unavailable"),
        ("Windows analysed", f"{health.processed_windows}"),
        ("Windows skipped", f"{health.skipped_windows}"),
        ("Windows refused (degraded input)", f"{health.refused_windows}"),
        ("Observations published", f"{health.observations_published}"),
        (
            "Epochs with contributors",
            f"{health.epochs_with_contributors} of {health.processed_epochs}",
        ),
        # Named rather than left inside the exclusion histogram. An epoch with
        # one buoy in it cannot associate anything — association is two units by
        # definition — so all of its observations are counted an unmatched
        # frequency, which reads as buoys disagreeing about a line when in fact
        # only one of them was in the room.
        ("Epochs with one unit", f"{health.single_contributor_epochs}"),
        (
            "Epoch cadence",
            f"{health.epochs_per_second:.2f}/s, {health.mean_contributors_per_epoch:.1f} units each",
        ),
        # What the epoch is being cut on, and — when it waits for the fleet —
        # what that wait costs. A cadence below the window rate reads as a fault
        # under a free-running clock and as the design working under a barrier,
        # so the reader is told which of the two they are looking at.
        ("Epoch synchronization", _describe_synchronization(health)),
        ("Associations formed", f"{health.associations_formed}"),
        ("Solutions refused", f"{health.solutions_rejected}"),
        ("Queued frames", f"{health.queued_frames}"),
        ("Dropped frames", f"{health.dropped_frames}"),
        ("Transform error", health.last_transform_error or UNAVAILABLE),
        ("Identity error", health.last_identity_error or UNAVAILABLE),
        ("Worker error", health.worker_error or UNAVAILABLE),
    )


def describe_array_footprint(footprint) -> tuple[tuple[str, str], ...]:
    """The shape the moored units make, and what it means for solving.

    Sits above the refusal numbers because it is the first thing to read. A
    collinear fleet produces weak horizontal geometry no matter how good the
    bearings are, and an operator who does not know that will go looking for a
    fault in the software — which is exactly what happened.
    """
    if footprint is None:
        return (("Array", "no unit positions configured"),)
    return (
        ("Array", "collinear" if footprint.is_collinear else "two-dimensional"),
        ("Baseline", f"{footprint.baseline_metres:.0f} m"),
        (
            "Perpendicular spread",
            f"{footprint.perpendicular_extent_metres:.0f} m ({footprint.aspect_ratio * 100:.1f}%)",
        ),
        ("Meaning", footprint.describe()),
    )


def describe_geometry_refusals(summary) -> tuple[tuple[str, str], ...]:
    """The measured geometry behind the horizontal-geometry refusals.

    Read as a verdict, not as counters. Rays behind intersection is the row
    that decides it: weak geometry still puts the target in front of the rays
    that heard it, so any nonzero count there is a bearing or orientation
    fault and not a limit of where the units are moored.

    Failing that, a crossing angle that stays small with a residual that stays
    small is the deployment's own geometry refusing honestly; a wide crossing
    angle, a residual on the scale of the fleet baseline, or a range far
    outside the operating area is not geometry at all.
    """
    if summary is None or not summary.refusals:
        return (("Refusals", "0"),)
    return (
        ("Refusals", f"{summary.refusals}"),
        ("Rays behind intersection", f"{summary.behind_ray_refusals}"),
        (
            "Crossing angle",
            f"{summary.crossing_angle_minimum_degrees:.1f}–{summary.crossing_angle_maximum_degrees:.1f}°",
        ),
        (
            "HDOP",
            f"{summary.hdop_minimum:.2f}–{summary.hdop_maximum:.2f} (limit {summary.hdop_limit:.2f})",
        ),
        (
            "GDOP peak",
            UNAVAILABLE if summary.gdop_maximum is None else f"{summary.gdop_maximum:.2f}",
        ),
        (
            "Residual",
            f"{summary.residual_minimum_metres:.0f}–{summary.residual_maximum_metres:.0f} m",
        ),
        ("Range peak", f"{summary.range_maximum_metres:.0f} m"),
    )


def _describe_synchronization(health) -> str:
    if health.synchronization_mode != "barrier":
        return "free running on the epoch window"
    parts = [f"waiting for the fleet, {health.held_cycles_per_epoch:.1f} cycle(s) held per epoch"]
    if health.barrier_deadline_closes:
        parts.append(f"{health.barrier_deadline_closes} published on the deadline")
    if health.epoch_discards:
        parts.append(f"{health.epoch_discards} dropped at a timeline break")
    return ", ".join(parts)


def describe_unit_participation(entries) -> tuple[tuple[str, str], ...]:
    """One row per buoy: how it fared at the fleet epoch.

    The exclusion histogram above says the console is losing data at the epoch
    and never which unit it is losing. `missing 51` on a four-unit console is
    three different faults sharing one number — a board that is switched off, a
    board whose analysis runs behind the water, and a fleet that is simply short
    a unit — and per buoy the three look nothing alike.
    """
    if not entries:
        return (("Fleet", "no epoch has closed yet"),)
    rows = []
    for unit in entries:
        detail = [f"{unit.contributed} in"]
        for count, label in (
            (unit.missing, "missing"),
            (unit.not_streaming, "not streaming"),
            (unit.stale, "stale"),
            (unit.publication_skew, "skewed"),
            (unit.other, "other"),
        ):
            if count:
                detail.append(f"{count} {label}")
        rows.append((f"Unit {unit.unit_identifier}", ", ".join(detail)))
    return tuple(rows)


def describe_histogram(entries) -> tuple[tuple[str, str], ...]:
    """One row per reason, worst first, or a single row saying there were none."""
    if not entries:
        return (("None", "0"),)
    return tuple((reason.replace("_", " ").capitalize(), f"{count}") for reason, count in entries)


def is_alerting(caption: str, value: str) -> bool:
    """Whether this row should be drawn as a problem rather than a number."""
    if caption in PIPELINE_NEUTRAL_ROWS:
        return False
    if caption == "Receive buffer":
        # A granted buffer is a number, not a fault. A granted buffer smaller
        # than the one asked for is the fault, and it is the one that explains
        # the burst losses below it.
        return RECEIVE_BUFFER_SHORTFALL in value
    if caption in PIPELINE_ALERT_VALUES:
        return value in PIPELINE_ALERT_VALUES[caption]
    if caption.startswith("Unit ") and value.startswith("0 in"):
        # A buoy that has contributed to no epoch *and* been left out of at
        # least one is the fault this row exists to name. A console in its first
        # seconds has contributed to nothing either, and drawing that as a fault
        # would make the row red every startup — so the comma matters: it is
        # there only once the epoch has actually left this unit out.
        return "," in value
    if caption in ACQUISITION_ALERT_ROWS or caption in TELEMETRY_ALERT_ROWS or caption in PIPELINE_ALERT_ROWS:
        return value not in ("0", UNAVAILABLE)
    return False


def console_summary(acquisition_health, telemetry_health) -> str:
    """One line for the console status bar, now that the detail has a window.

    Says how many units are delivering and whether anything is wrong. It does not
    say *what* is wrong: that is what the device status window is for, and a
    status bar that tries to say it ends up back where it started.
    """
    parts = []
    if acquisition_health is not None:
        total = len(acquisition_health)
        asio = bool(acquisition_health) and all(getattr(health, "source", "ethernet") == "asio" for health in acquisition_health)
        if asio:
            receiving = sum(1 for health in acquisition_health if health.input_sample_rate > 0 and not health.receiver_error)
            faults = sum(
                1
                for health in acquisition_health
                if health.receiver_error
                or health.callback_faults
                or health.dropped_input_blocks
                or health.window_queue_overflow_windows
                or health.last_callback_status
            )
            source_name = "ASIO"
        else:
            receiving = sum(1 for health in acquisition_health if health.packet_age_seconds is not None and not health.receiver_error)
            faults = sum(
                1 for health in acquisition_health if health.receiver_error or health.lost_packets or health.invalid_packets or health.queue_overflow_packets
            )
            source_name = "Acquisition"
        acquisition = f"{source_name} {receiving}/{total}"
        if faults:
            acquisition += f" · {faults} with faults"
        parts.append(acquisition)
    if telemetry_health is not None:
        total = len(telemetry_health)
        connected = sum(1 for health in telemetry_health if health.message_age_seconds is not None and not health.last_error)
        parts.append(f"Telemetry {connected}/{total}")
    if not parts:
        return "No acquisition or telemetry service"
    return "  ·  ".join(parts)
