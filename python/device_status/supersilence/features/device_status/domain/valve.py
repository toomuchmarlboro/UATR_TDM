"""Where the valve is, read from telemetry that is already arriving.

The command half of this actuator is
``infrastructure/telemetry/valve.py``; this is the half that says whether it
worked. They are separate on purpose: ``$RMCMD`` is unacknowledged, so what was
SENT and what the hardware REPORTS are two different facts, and a design that
lets one stand in for the other will happily show a valve as open because
somebody clicked open.

``ulRaw[9]`` carries two defined bits and the firmware drives them as a pair, so
there are more readings than the two an operator expects:

    bit 0 alone   OPEN
    bit 1 alone   CLOSED
    neither       IDLE      - a real resting state, not missing data
    both          INVALID   - a motor cannot open and close at once

IDLE AND INVALID BOTH MATTER. Collapsing idle into "closed" would report a
valve that is merely unpowered as one that is sealed; collapsing invalid into
anything at all discards the only evidence that the actuator or its wiring is
faulty.

BIT 1 IS OPEN AND BIT 0 IS CLOSED, which is the opposite of the manufacturer's
documented field map. Confirmed on the hardware: with the jaws visibly open
this read CLOSED, and with them shut it read OPEN.

That is the SECOND swap found in this one actuator's documentation. Their
command codes are reversed too - what they call ENABLE_1 closes. The two errors
are independent: finding one was not grounds to assume the other, and fixing
one did not fix the other. Both are now set from what the hardware does rather
than from what the paperwork says, and neither should be "tidied" back to match
the datasheet.
"""
from __future__ import annotations

from enum import Enum

#: ``ulRaw[9]``. The only two bits the firmware defines; the telemetry health
#: bounds for this field are (0.0, 3.0) for exactly that reason.
#:
#: Named for the EFFECT, like the command codes, and like them set from the
#: hardware rather than from the manufacturer's map, which has them the other
#: way round.
OPEN_BIT = 0x02
CLOSE_BIT = 0x01


class ValvePosition(Enum):
    """What the buoy says its actuator is doing."""

    #: No telemetry, or telemetry too old to describe the present.
    UNKNOWN = "unknown"
    OPEN = "open"
    CLOSED = "closed"
    #: Neither bit driven. A resting actuator, not an absent reading.
    IDLE = "idle"
    #: Both bits driven, which is not a position but a fault.
    INVALID = "invalid"

    @property
    def caption(self) -> str:
        """How it reads on screen. Upper case, because this is a state."""
        return self.value.upper()

    @property
    def is_fault(self) -> bool:
        return self is ValvePosition.INVALID

    @property
    def is_known(self) -> bool:
        return self not in (ValvePosition.UNKNOWN, ValvePosition.INVALID)


def valve_position(digital_io: int | None) -> ValvePosition:
    """Decode ``ulRaw[9]`` into a position.

    ``None`` - no sample yet, or a caller that has decided the newest one is too
    old to describe the present - is UNKNOWN rather than IDLE. A link that has
    gone quiet leaves its last reading looking perfectly healthy, and that last
    reading is where the valve was, not where it is.
    """
    if digital_io is None:
        return ValvePosition.UNKNOWN
    try:
        bits = int(digital_io)
    except (TypeError, ValueError):
        return ValvePosition.UNKNOWN
    opening = bool(bits & OPEN_BIT)
    closing = bool(bits & CLOSE_BIT)
    if opening and closing:
        return ValvePosition.INVALID
    if opening:
        return ValvePosition.OPEN
    if closing:
        return ValvePosition.CLOSED
    return ValvePosition.IDLE
