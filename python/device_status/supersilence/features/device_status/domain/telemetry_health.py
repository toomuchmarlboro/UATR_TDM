"""Whether a decoded telemetry field is telling the truth.

The fault this exists to catch is not a framing fault and not a checksum fault.
It is a field map that has shifted one place: the sentence frames, the checksum
passes, and every value prints as a plausible number under the wrong heading.
That happened here — `infrastructure/telemetry/gdat2.py` carries the record of
it — and nothing in the decoder could have caught it, because there is nothing
structurally wrong with a correctly framed sentence read against the wrong map.

Three mechanisms answer it, and they are separate on purpose.

**Plausibility bounds, per field.** A value outside its bound is far more likely
to mean the map has shifted — the number is reasonable for some *other*
quantity — than that the sensor read it. Flagged per field rather than as one
banner: which fields are out is the evidence for how far the map has moved.

**Liveness, session-wide.** A value can frame, checksum, decode and print
perfectly while never being written at all. Only motion distinguishes a live
field from a dead one, and a *constant* value is not evidence of death: this
firmware quantises attitude to 0.1°, so a still unit repeats one bit pattern
indefinitely and is healthy. So a field that has never changed is reported as
unproven, with the quantisation step derived from what actually arrived, and the
operator is asked to move the unit rather than told a wrong answer. A field that
has been exactly zero for the whole session is reported separately and *is* a
fault: quantisation explains a repeated plausible value, not a field that is
exactly zero forever.

Liveness is session-wide and reset on reconnect, so a dead field cannot inherit
a previous connection's proof of life.

**Staleness, its own state.** No sentence for longer than the threshold means
every value on the page is a memory. A frozen link otherwise shows the last good
reading forever, and each field individually looks perfect.

No Qt, no database, no UI — and no import of the decoder either, because domain
code imports no infrastructure. The field order is stated here and held to the
decoder's by a test; a bound is looked up by field *name*, so nothing in this
module can silently slip one place the way the map itself once did.

The bounds come from the UATR_TDM control station's own decoder, which is the
authority on what this firmware sends.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

#: The telemetry fields, in the order the firmware sends them.
#:
#: A second statement of what ``infrastructure/telemetry/gdat2.py`` decodes, and
#: it has to be: domain code imports no infrastructure. The two are held equal by
#: a test rather than by an import, and every lookup here is by name rather than
#: by position, so a divergence shows up as a missing field and never as one
#: field reading its neighbour's bound.
TELEMETRY_FIELD_NAMES: tuple[str, ...] = (
    "leak_v",
    "voltage_v",
    "depth_m",
    "depth_temp_c",
    "roll_deg",
    "pitch_deg",
    "yaw_deg",
    "altimeter_dist_mm",
    "altimeter_conf_pct",
    "digital_io",
)

#: Physically plausible range per field, by name.
#:
#: Sanity bounds, not calibration. Taken from the control station's decoder:
#:
#: - leak sensor, V: an ADC pin on a 3.3/5 V rail
#: - voltage monitor, V: a 24 V nominal bus
#: - depth, m: slightly negative at the surface is real
#: - depth temperature, °C: seawater plus the sensor's own self-heating
#: - roll, deg: a full turn either way
#: - pitch, deg: outside ±90 is a convention error, not an attitude
#: - yaw, deg: **the one bound that is a guess.** A 0..360 convention and a
#:   0-referenced ±180 convention are both normal for an AHRS and nothing on
#:   hand rules either out, so the bound admits both rather than flagging a
#:   working device. This is the reference's own note and it carries over.
#: - altimeter distance, mm: 100 m
#: - altimeter confidence, %
#: - digital I/O: only bits 0 and 1 are defined
PLAUSIBLE_BOUNDS: dict[str, tuple[float, float]] = {
    "leak_v": (0.0, 5.0),
    "voltage_v": (0.0, 60.0),
    "depth_m": (-2.0, 500.0),
    "depth_temp_c": (-5.0, 50.0),
    "roll_deg": (-180.0, 180.0),
    "pitch_deg": (-90.0, 90.0),
    "yaw_deg": (-180.0, 360.0),
    "altimeter_dist_mm": (0.0, 100_000.0),
    "altimeter_conf_pct": (0.0, 100.0),
    "digital_io": (0.0, 3.0),
}

# The bounds are a second statement of the field set, which is the very kind of
# divergence that produced the shifted map in the first place. They are bound to
# the names here: add a field and forget its bound, and this module refuses to
# import rather than leaving that field unchecked. Raised rather than asserted,
# because assertions are stripped under -O and this is exactly the check that
# must survive a packaged build.
if set(PLAUSIBLE_BOUNDS) != set(TELEMETRY_FIELD_NAMES):
    raise RuntimeError(
        "telemetry plausibility bounds must name exactly the telemetry fields: "
        f"{sorted(set(PLAUSIBLE_BOUNDS) ^ set(TELEMETRY_FIELD_NAMES))} differ"
    )

#: How long without a sentence before every value is a memory rather than a
#: reading. The firmware broadcasts about every 20 ms, so one second is fifty
#: missed sentences — long enough not to flicker on a scheduling stall, short
#: enough that an operator does not read a dead link as a live one.
DEFAULT_STALE_AFTER_SECONDS = 1.0

#: Quantisation steps looked for, coarsest first. A firmware sending full float
#: precision matches none of them and reports no step, which is the correct
#: answer: its dither is then meaningful again.
_QUANTISATION_CANDIDATES = (1.0, 0.5, 0.25, 0.1, 0.05, 0.01)

#: Distinct values remembered per field. A 50 Hz feed left running all day must
#: not grow without limit; what matters is the step between values, and a few
#: thousand of them establish it as well as a million would.
_MAXIMUM_REMEMBERED_VALUES = 4_096

#: What a field's evidence supports.
LIVE = "live"
ZERO = "zero"
CONSTANT = "constant"
UNSEEN = "unseen"


@dataclass(frozen=True)
class FieldHealth:
    """One field's evidence: what it last read, and whether to believe it."""

    name: str
    state: str
    latest: float | int | None
    changes: int
    quantisation_step: float | None
    plausible: bool
    lowest: float
    highest: float

    def describe_liveness(self) -> str:
        """The short form an operator reads in a column.

        ``constant ?`` rather than ``constant`` — the question mark is the whole
        point: the field has not been proven either way and the operator is the
        one who can settle it by moving the unit.
        """
        if self.state == LIVE:
            return f"live {self.changes}"
        if self.state == ZERO:
            return "zero"
        if self.state == CONSTANT:
            return "constant ?"
        return "—"

    def explain(self) -> str:
        """The sentence that says what to do about this field, or an empty one.

        Implausibility is reported ahead of liveness. A field that has never
        moved *and* sits outside its bound is a map that shifted, not a unit
        that needs moving, and telling the operator to move it would send them
        to the water for a fault that is in the decoder.
        """
        if not self.plausible:
            return (
                f"Outside {self.lowest:g}..{self.highest:g}: more likely a shifted "
                "field map than a real reading."
            )
        if self.state == ZERO:
            return "Exactly zero all session: the firmware is not filling this field."
        if self.state == CONSTANT:
            if self.quantisation_step is not None:
                return (
                    f"Unchanged all session. Values arrive in steps of "
                    f"{self.quantisation_step:g}, so a still unit repeating one "
                    "value is normal — move the unit to prove it."
                )
            return "Unchanged all session — move the unit to prove it is live."
        return ""


@dataclass(frozen=True)
class TelemetryHealth:
    """Every field of one unit, and whether the link is still saying anything."""

    fields: tuple[FieldHealth, ...]
    sentences: int
    seconds_since_sentence: float | None
    is_stale: bool

    def implausible(self) -> tuple[FieldHealth, ...]:
        """The fields whose value is outside its bound, in field-map order."""
        return tuple(entry for entry in self.fields if not entry.plausible)

    def field(self, name: str) -> FieldHealth:
        for entry in self.fields:
            if entry.name == name:
                return entry
        raise KeyError(f"no telemetry field named {name!r}")


@dataclass
class _FieldEvidence:
    """What has been seen of one field since the connection was made."""

    changes: int = 0
    latest: float | int | None = None
    seen: bool = False
    all_zero: bool = True
    values: set[float] = field(default_factory=set)
    _previous_raw: object = None

    def observe(self, raw: object, value: float | int) -> None:
        if self.seen and raw != self._previous_raw:
            self.changes += 1
        self._previous_raw = raw
        self.seen = True
        self.latest = value
        if value != 0:
            self.all_zero = False
        if len(self.values) < _MAXIMUM_REMEMBERED_VALUES:
            self.values.add(round(float(value), 6))

    def state(self) -> str:
        if not self.seen:
            return UNSEEN
        if self.changes > 0:
            return LIVE
        # Zero is reported ahead of constant because an all-zero field is also
        # constant, and "the firmware never filled this" is the more actionable
        # reading of the same evidence.
        if self.all_zero:
            return ZERO
        return CONSTANT

    def quantisation_step(self) -> float | None:
        """The apparent step between values, or None if it cannot be established.

        Derived from what arrived rather than assumed. A field that has only ever
        shown one value establishes nothing, which is why a constant field is
        reported as unproven rather than as quantised.
        """
        values = sorted(self.values)
        if len(values) < 2:
            return None
        for step in _QUANTISATION_CANDIDATES:
            if all(abs(value / step - round(value / step)) < 1e-4 for value in values):
                return step
        return None


class UnitTelemetryHealth:
    """Session-wide evidence for one unit's telemetry, fed one sample at a time.

    One instance per unit, reset when that unit's link is remade. Reset is not
    optional bookkeeping: without it a reconnected unit inherits the previous
    connection's proof of life, and a field that died in between reads as live.
    """

    def __init__(
        self,
        *,
        stale_after_seconds: float = DEFAULT_STALE_AFTER_SECONDS,
    ) -> None:
        if stale_after_seconds <= 0.0:
            raise ValueError("stale threshold must be positive")
        self._stale_after_seconds = stale_after_seconds
        self._evidence: dict[str, _FieldEvidence] = {}
        self._sentences = 0
        self._last_received_at: float | None = None
        self.reset()

    def reset(self) -> None:
        """Forget everything. Called when the link is remade, not on a gap."""
        self._evidence = {name: _FieldEvidence() for name in TELEMETRY_FIELD_NAMES}
        self._sentences = 0
        self._last_received_at = None

    def observe(
        self,
        values: Sequence[float | int],
        received_at: float,
        raw_fields: Sequence[str] = (),
    ) -> None:
        """Record one decoded sentence.

        ``raw_fields`` are the sentence's undecoded words, and they are what a
        change is measured on where they are available: two different bit
        patterns that decode to the same rounded value are still a field that
        moved. A sample carrying none — one built in a test, or by a source that
        does not keep them — falls back to the decoded value, which can only
        under-count changes, never invent one.
        """
        if len(values) != len(TELEMETRY_FIELD_NAMES):
            raise ValueError(
                f"expected {len(TELEMETRY_FIELD_NAMES)} telemetry values, "
                f"got {len(values)}"
            )
        for index, name in enumerate(TELEMETRY_FIELD_NAMES):
            value = values[index]
            raw = raw_fields[index] if index < len(raw_fields) else value
            self._evidence[name].observe(raw, value)
        self._sentences += 1
        self._last_received_at = received_at

    def snapshot(self, now: float) -> TelemetryHealth:
        """What the operator should be shown, as of ``now``."""
        entries: list[FieldHealth] = []
        for name in TELEMETRY_FIELD_NAMES:
            evidence = self._evidence[name]
            lowest, highest = PLAUSIBLE_BOUNDS[name]
            latest = evidence.latest
            entries.append(
                FieldHealth(
                    name=name,
                    state=evidence.state(),
                    latest=latest,
                    changes=evidence.changes,
                    quantisation_step=evidence.quantisation_step(),
                    # A field nothing has been seen for is not implausible; it is
                    # unseen, and reporting it as out of bounds would be one
                    # fault printed as two.
                    plausible=latest is None or lowest <= latest <= highest,
                    lowest=lowest,
                    highest=highest,
                )
            )
        since = (
            None
            if self._last_received_at is None
            else max(0.0, now - self._last_received_at)
        )
        return TelemetryHealth(
            fields=tuple(entries),
            sentences=self._sentences,
            seconds_since_sentence=since,
            is_stale=since is None or since > self._stale_after_seconds,
        )
