"""The valve: two buttons that ask, and one line that says what happened.

Sibling of `phantom_power_control.py`, and for the same reason it exists at all
— this and 48 V are the only two controls on this window that reach past a
service and into hardware. Kept as its own widget rather than a third pair of
buttons on the gain strip, because gain is per channel and pure software while
this turns a motor in the water.

**THE BUTTONS ARE A REQUEST; THE READBACK IS THE ANSWER.** `$RMCMD` is
unacknowledged — the aux_vcu replies to nothing — so a click can only ever
prove that bytes left this host. What the actuator did comes back in `ulRaw[9]`
of the telemetry that was already arriving, and it comes back on its own
schedule. The two are shown as separate lines and are allowed to disagree.

That separation is the whole design, and it is why this does not follow the
pattern of a checkbox that latches on click. A latched control would report the
valve as open because somebody asked for open, which is precisely the claim
nobody can make here. When the two lines disagree, the readback is the one
telling the truth.

**A STALE LINK READS UNKNOWN, NOT "LAST KNOWN GOOD".** A socket can stay open
while the far end stops talking, and the last position sits there looking
healthy — that is where the valve *was*. The caller decides how old is too old
and passes `ValvePosition.UNKNOWN`; this widget never ages a reading itself,
because it does not own the clock that would make that judgement.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from supersilence.features.device_status.domain.valve import ValvePosition
from supersilence.features.device_status.ui.claw import ClawView
from supersilence.infrastructure.telemetry.valve import ValveCommand

#: One colour per position. Idle is deliberately the same muted grey as an
#: unknown reading is given no colour at all: idle is a real, uninteresting
#: resting state, and painting it green or red would imply the valve had
#: settled somewhere it has not.
POSITION_COLOURS = {
    ValvePosition.OPEN: "#3fb950",
    ValvePosition.CLOSED: "#539bf5",
    ValvePosition.IDLE: "#768390",
    ValvePosition.INVALID: "#f85149",
    ValvePosition.UNKNOWN: "#545d68",
}

#: Green for open, red for shut, the way the manufacturer's own host colours
#: them. Worth matching: anyone who has used that host has the association
#: already, and disagreeing with it on a control that moves hardware would be a
#: gratuitous place to be original.
OPEN_STYLE = (
    "QPushButton { background-color: #1b2b1b; color: #57ab5a;"
    " border: 1px solid #2d5a2d; border-radius: 3px; padding: 5px 10px;"
    " font-weight: 700; }"
    "QPushButton:hover:enabled { background-color: #244024; }"
    "QPushButton:disabled { color: #444c56; border-color: #2d333b;"
    " background-color: #21262d; }"
)
CLOSE_STYLE = (
    "QPushButton { background-color: #3a1d1d; color: #e5534b;"
    " border: 1px solid #5a2d2d; border-radius: 3px; padding: 5px 10px;"
    " font-weight: 700; }"
    "QPushButton:hover:enabled { background-color: #4d2424; }"
    "QPushButton:disabled { color: #444c56; border-color: #2d333b;"
    " background-color: #21262d; }"
)


class ValveControl(QWidget):
    """One unit's valve: OPEN, CLOSE, and what the buoy says about it."""

    #: Emitted with the ValveCommand the operator asked for. Carries no unit
    #: identifier: the window connects one of these per page and already knows
    #: which unit it built.
    command_requested = Signal(object)

    def __init__(self, unit_identifier: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.unit_identifier = unit_identifier
        self.setObjectName(f"valve_control_unit_{unit_identifier}")

        self._position = ValvePosition.UNKNOWN

        # The gripper itself, drawn and dragged. It is the control, not an
        # illustration beside one: see `claw.py` for why the thing being
        # commanded is worth drawing rather than labelling.
        self._claw = ClawView(self)
        self._claw.setObjectName(f"valve_claw_unit_{unit_identifier}")
        self._claw.command_requested.connect(self._request)

        # TWO EXPLICIT BUTTONS, as on the manufacturer's host. The claw is
        # still draggable, but a drag and a click-to-toggle both decide WHICH
        # command to send from context — how far you dragged, or what the
        # readback currently says — and an actuator is the wrong place to make
        # an operator infer that. These say which one they send, and send only
        # that one. The claw stays as the position display and the fast path.
        self._open = QPushButton("OPEN", self)
        self._open.setObjectName(f"valve_open_unit_{unit_identifier}")
        self._open.setStyleSheet(OPEN_STYLE)
        self._open.setToolTip(
            "Sends $RMCMD,5 — the vendor's RMCMD_DISABLE_1, which opens.")
        self._open.clicked.connect(lambda: self._request(ValveCommand.OPEN))

        self._close = QPushButton("CLOSE", self)
        self._close.setObjectName(f"valve_close_unit_{unit_identifier}")
        self._close.setStyleSheet(CLOSE_STYLE)
        self._close.setToolTip(
            "Sends $RMCMD,1 — the vendor's RMCMD_ENABLE_1, which closes.")
        self._close.clicked.connect(lambda: self._request(ValveCommand.CLOSE))

        self._readback = QLabel(self)
        self._readback.setObjectName(f"valve_readback_unit_{unit_identifier}")

        #: What left this host, kept separate from what came back. Empty until
        #: something has been sent, so an untouched page makes no claim at all.
        self._sent = QLabel("", self)
        self._sent.setObjectName(f"valve_sent_unit_{unit_identifier}")
        self._sent.setStyleSheet("color: #768390;")

        # Readback UNDER the jaws, not beside them. Beside is where the box is
        # narrowest, and "reads INVALID" is exactly the caption that must not
        # be the one that gets elided. Stacked also matches the compass and
        # horizon boxes it sits next to: instrument on top, words below.
        self._readback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._readback.setWordWrap(True)
        self._sent.setWordWrap(True)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(6)
        buttons.addWidget(self._open, 1)
        buttons.addWidget(self._close, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._claw, 1)
        layout.addLayout(buttons)
        layout.addWidget(self._readback)
        layout.addWidget(self._sent)

        self.set_available(False)
        self.set_position(ValvePosition.UNKNOWN)
        # SHUT BY DEFAULT. Nothing has been commanded yet, and of the two
        # states that is the one that is safe to be wrong about: a claw drawn
        # shut that is actually open is a surprise, a claw drawn open that is
        # actually shut is a dropped payload.
        self._set_commanded(ValveCommand.CLOSE)

    # -- what the operator can do -----------------------------------------
    def set_available(self, available: bool) -> None:
        """Let the valve be commanded, or grey it out with no link to do it over.

        Disabled rather than hidden: a control that vanishes reads as a
        capability this unit does not have, when the truth is that its
        telemetry link is down and the capability is one reconnect away.
        """
        self._claw.set_command_enabled(available)
        self._open.setEnabled(available)
        self._close.setEnabled(available)

    def _request(self, command: ValveCommand) -> None:
        self.command_requested.emit(command)

    # -- what a test, or a keyboard, drives -------------------------------
    def request_open(self) -> None:
        self._request(ValveCommand.OPEN)

    def request_close(self) -> None:
        self._request(ValveCommand.CLOSE)

    @property
    def claw(self) -> ClawView:
        return self._claw

    # -- what has been commanded ------------------------------------------
    def _set_commanded(self, command: ValveCommand) -> None:
        """Draw the jaws where the last button press asked them to be.

        THE PICTURE FOLLOWS THE BUTTON, NOT THE TELEMETRY. That is a decision,
        and it is worth being explicit about what it costs: `$RMCMD` is
        unacknowledged, so these jaws show what was ASKED FOR, and a command
        the firmware ignored still moves them.

        It is the right trade here anyway, because the alternative is worse in
        practice. The readback is a single field on a firmware that already
        reports several others as hard zero, and when it does not move, a
        readback-driven claw sits at IDLE forever and shows nothing at all.

        The telemetry reading is still on the line below, and still says what
        the firmware reports. When the two disagree, that disagreement is
        visible — which is the whole reason it stays on screen instead of
        being replaced by this.
        """
        self._commanded = command
        self._claw.set_position(
            ValvePosition.OPEN if command is ValveCommand.OPEN
            else ValvePosition.CLOSED)

    @property
    def commanded(self) -> ValveCommand:
        return self._commanded

    # -- what the buoy says -----------------------------------------------
    def set_position(self, position: ValvePosition) -> None:
        """The telemetry reading. Updates the caption; does NOT move the jaws."""
        self._position = position
        colour = POSITION_COLOURS[position]
        weight = 700 if position.is_fault else 600
        self._readback.setText(f"claw reads {position.caption}")
        self._readback.setStyleSheet(f"color: {colour}; font-weight: {weight};")
        self._readback.setToolTip(
            "ulRaw[9] of this unit's telemetry — what the firmware reports the "
            "claw is doing. The jaws above show what was last commanded, so "
            "these two can disagree; when they do, this line is the one with "
            "evidence behind it."
        )

    @property
    def position(self) -> ValvePosition:
        return self._position

    def set_outcome(self, command: ValveCommand, error: str) -> None:
        """Report what became of a command that was just sent.

        Names the ACTION as well as the code. The two codes are not in the
        order anyone expects — 5 opens, 1 closes — so a line showing only the
        sentence invites a reader who remembers the vendor's mnemonics to
        conclude the opposite of what happened.
        """
        if error:
            # The jaws stay where they were. A command that never left the host
            # commanded nothing, and moving the picture for it would be the one
            # version of "follows the last press" that is simply false.
            self._sent.setText(f"{command.name} failed: {error}")
            self._sent.setStyleSheet("color: #f85149;")
            return
        self._set_commanded(command)
        self._sent.setText(f"sent {command.name}")
        self._sent.setStyleSheet("color: #768390;")
