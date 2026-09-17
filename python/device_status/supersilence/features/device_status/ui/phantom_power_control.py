"""48 V phantom power: one board-wide toggle that follows the board.

Deliberately not part of `ChannelGainPanel` — gain is per channel and pure
software; phantom power is one flag for the whole board and a real command
sent to hardware (see `infrastructure/control/phantom_power.py`). Different
enough in kind and in consequence that it gets its own small widget rather
than becoming a seventeenth control squeezed onto the gain strip.

Starts unchecked on every construction and stays that way until either the
operator enables it or the board reports 48 V already live. Nothing here reads
a stored preference back and resends it. See the module docstring in
`infrastructure/control/phantom_power.py` for why: the firmware never brings
48 V up on its own after a power cycle, and restoring a stored "on" from
software would defeat that by design.

**This control follows the board, not the click.** The firmware publishes what
it is actually driving in a status byte in every audio packet
(`infrastructure/acquisition/uatr_tdm.py`), so the truth lives in the FPGA and
this exists to show it. A click is a request; the board's own readback is what
confirms it. If the FPGA refuses — the build forbids 48 V, the staged power-up
has not reached 1000 ms, or the phantom watchdog has tripped — the button
snaps back and names the gate holding it off, rather than showing an ON that
never happened.

One honesty limit remains, and the tooltip says so: `EN_48V` is an FPGA output
with no sense line back. "ON" here means the FPGA is asserting the enable, not
that voltage reached the hydrophones — a dead converter, a blown fuse or an
open enable trace all still read as on.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton, QWidget

from supersilence.infrastructure.acquisition.uatr_tdm import PhantomPowerReadback

OFF_STYLE = (
    "QPushButton { background-color: #191d24; color: #d29922;"
    " border: 1px solid #3a2f1d; border-radius: 3px; padding: 4px 12px;"
    " font-weight: 600; }"
)
ON_STYLE = (
    "QPushButton { background-color: #3a1d1d; color: #f85149;"
    " border: 1px solid #f85149; border-radius: 3px; padding: 4px 12px;"
    " font-weight: 700; }"
)
#: Asked for, not yet confirmed by the board. Distinct from both settled
#: states because "we have told the board" and "the board is doing it" are
#: different facts and the operator is entitled to see which one they have.
PENDING_STYLE = (
    "QPushButton { background-color: #2a2410; color: #d29922;"
    " border: 1px dashed #d29922; border-radius: 3px; padding: 4px 12px;"
    " font-weight: 700; }"
)

#: How many disagreeing readbacks to sit through before the board wins.
#:
#: Not a timeout dressed up as a count. A command takes a moment to reach the
#: board and another for the next packet to carry the answer back, so the
#: first readback after a click is very often still describing the state from
#: before it. Snapping back on that one reading would make every successful
#: enable flicker. After a few, the disagreement is real: the FPGA has had the
#: command and is refusing it, and continuing to show the operator's request
#: would be showing them a lie.
CONFIRMATION_GRACE_READBACKS = 3

_UNKNOWN = "board: unknown — nothing heard from this unit yet"


class PhantomPowerControl(QPushButton):
    """A checkable button that is the whole control surface for 48 V phantom power."""

    #: Emitted with the newly requested state on every click. The owner sends
    #: the actual command and decides what to do if it fails; this widget only
    #: asks, and then shows what the board came back with.
    toggled_by_operator = Signal(bool)

    def __init__(self, unit_identifier: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(f"phantom_power_{unit_identifier}")
        self.setCheckable(True)
        self.setChecked(False)
        self._readback: PhantomPowerReadback | None = None
        self._requested: bool | None = None
        self._disagreements = 0
        self._refresh()
        self.clicked.connect(self._on_clicked)

    def set_readback(self, readback: PhantomPowerReadback | None) -> None:
        """Show what this unit's board says it is doing with 48 V.

        `None` means there is no answer to show — nothing heard from the unit,
        or a bitstream older than the readback. The control then falls back to
        displaying the request, which is the best available guess and exactly
        what it did before any readback existed.
        """
        self._readback = readback
        if readback is not None:
            if self._requested is None or readback.driven == self._requested:
                self._requested = None
                self._disagreements = 0
            else:
                self._disagreements += 1
                if self._disagreements > CONFIRMATION_GRACE_READBACKS:
                    # The board has had long enough. It wins.
                    self._requested = None
                    self._disagreements = 0
        self._show(self._displayed_state())
        self._refresh()

    def board_state(self) -> str:
        """One line naming what the board reports, and which gate is holding it.

        Mirrors the firmware's own diagnosing table: only one row can be true
        at a time, and whichever gate is closed is the cause.
        """
        readback = self._readback
        if readback is None:
            return _UNKNOWN
        if readback.driven:
            return "board: ON — the FPGA is asserting EN_48V"
        if not readback.permitted:
            return "board: off — this build forbids 48 V (C_ENABLE_48V false)"
        if not readback.staged:
            return "board: off — staged power-up has not reached 1000 ms yet"
        if not readback.requested:
            return (
                "board: off — not requested. An FPGA reset clears the request, "
                "so this is also what a rebooted board shows"
            )
        return (
            "board: off — the phantom WATCHDOG has tripped. The board heard no "
            "flags-carrying packet in time and dropped 48 V itself"
        )

    def awaiting_confirmation(self) -> bool:
        """True while a click has been made and the board has not agreed yet."""
        return self._requested is not None

    def _on_clicked(self) -> None:
        # setCheckable already flipped isChecked() by the time clicked fires.
        self._requested = self.isChecked()
        self._disagreements = 0
        self._refresh()
        self.toggled_by_operator.emit(self._requested)

    def _displayed_state(self) -> bool:
        if self._requested is not None:
            return self._requested
        if self._readback is not None:
            return self._readback.driven
        return self.isChecked()

    def _show(self, on: bool) -> None:
        """Set the checkbox without emitting a command.

        Following the board must never send a packet, or the console would
        command whatever it happened to observe and two consoles watching the
        same board would argue with each other forever.
        """
        if self.isChecked() == on:
            return
        blocked = self.blockSignals(True)
        try:
            self.setChecked(on)
        finally:
            self.blockSignals(blocked)

    def _refresh(self) -> None:
        on = self._displayed_state()
        pending = self._requested is not None
        self.setStyleSheet(PENDING_STYLE if pending else ON_STYLE if on else OFF_STYLE)
        if pending:
            self.setText(
                "48V PHANTOM: ON (asking)" if on else "48V Phantom: off (asking)"
            )
        else:
            self.setText("48V PHANTOM: ON" if on else "48V Phantom Power")
        self.setToolTip(
            f"{self.board_state()}\n\n"
            "This follows the board, not the button: the FPGA reports what it "
            "is driving in every audio packet, and a click is a request that "
            "waits for that readback to agree.\n\n"
            "Asserted, not measured. EN_48V is an FPGA output with no sense "
            "line back, so a dead supply or an open enable trace still reads "
            "as on. Off at every console start regardless of what it was set "
            "to before — the firmware never brings 48 V up on its own after a "
            "power cycle, and this control does not fight that."
        )
