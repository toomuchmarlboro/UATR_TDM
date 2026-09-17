"""The gripper, drawn as itself and used as the control.

The actuator on the buoy is a two-jaw claw on a motor. This draws it — a mount,
a stem, a hub and two arms — and is the control for it: drag the jaws apart to
ask for open, together to ask for shut, or click to toggle.

Line art rather than a rendering. The picture has one job, which is to make the
jaw position readable at a glance from across a bench, and an outline does that
better at 90 pixels than shading does.

JAWS POINT UP. The claw hangs below its mount on the vehicle, but a control
that reads top-down puts the moving parts at the bottom of the widget where the
caption wants to be, and reads as something falling. Up is the conventional
direction for a thing you are operating.

WHY A PICTURE RATHER THAN TWO BUTTONS
=====================================
Because the thing being commanded has a *position*, and a pair of buttons can
only show what was pressed. It also removes a class of mistake that labelled
buttons are prone to here: the manufacturer's own labels for these two commands
were swapped, and an operator reading "OPEN" had no way to see that the jaws
had closed. A drawn jaw cannot be mislabelled.

THE JAWS SHOW THE READBACK, NOT THE CLICK
=========================================
`$RMCMD` is unacknowledged, so a click proves only that bytes left this host.
While you drag, the jaws follow the cursor in a dashed outline — that is the
REQUEST, drawn as a ghost precisely so it cannot be mistaken for the position.
On release the ghost disappears and the solid jaws stay exactly where the
telemetry last put them, until the buoy reports that they have moved.

So a command that goes nowhere looks like nothing happening, which is correct.
A control that animated to "open" on click would be reporting a movement it has
no evidence for.

IDLE IS NOT A POSITION
======================
`ulRaw[9]` with neither bit driven means the motor is not being driven — it
does not say where the jaws ended up. Drawn half-open and greyed rather than
guessed at. UNKNOWN (no telemetry, or telemetry too old to describe the
present) is drawn the same way but dimmer: both are "this widget does not
know", and neither is allowed to look like a measurement.
"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPointF, QRectF, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from supersilence.features.device_status.domain.valve import ValvePosition
from supersilence.infrastructure.telemetry.valve import ValveCommand

#: Jaw swing, in degrees, at each end of its travel. Not the real mechanism's
#: travel — nobody measured that — so this is a legible drawing, not a claim.
SHUT_DEGREES = 0.0
#: The arms already splay about 25 degrees at rest, so this is added to that,
#: not measured from vertical. Much past this and the claw reads as a pair of
#: outstretched arms rather than a gripper that is open.
OPEN_DEGREES = 20.0
#: Where "idle" and "unknown" sit: between the two, so neither reads as a
#: settled position.
UNSURE_DEGREES = 10.0

#: Past this fraction of the travel, a released drag means OPEN.
COMMIT_FRACTION = 0.5

HUB_RADIUS = 13.0
BORE_RADIUS = 5.0
STEM_HALF_WIDTH = 7.0
LINE_WIDTH = 3.0

#: One arm, hub outward to the tip, at rest. Mirrored for the other.
JAW_POINTS = (
    (6.0, -7.0),
    (24.0, -44.0),
    (24.0, -66.0),
    (12.0, -80.0),
)

BODY = QColor("#768390")
COLOURS = {
    ValvePosition.OPEN: QColor("#57ab5a"),
    ValvePosition.CLOSED: QColor("#539bf5"),
    ValvePosition.IDLE: QColor("#768390"),
    ValvePosition.INVALID: QColor("#e5534b"),
    ValvePosition.UNKNOWN: QColor("#444c56"),
}
GHOST = QColor("#d29922")


class ClawView(QWidget):
    """A two-jaw gripper: drawn from the readback, dragged to command."""

    #: The operator asked for this. Carries a ValveCommand and nothing else —
    #: the widget has no opinion about whether it can be delivered.
    command_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("claw_view")
        self.setMinimumSize(86, 108)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._position = ValvePosition.UNKNOWN
        self._angle = UNSURE_DEGREES
        self._enabled_for_commands = False
        self._drag_angle: float | None = None
        self._dragging = False
        self._pressed_at: QPointF | None = None

        # Animates the SOLID jaws between readback positions only. Nothing here
        # animates toward a commanded position: see the module docstring.
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(320)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._animation.valueChanged.connect(self._on_animation_step)

        self._refresh_tooltip()

    # ------------------------------------------------------------- state --
    def set_position(self, position: ValvePosition) -> None:
        if position is self._position:
            return
        self._position = position
        self._animate_to(self._angle_for(position))
        self._refresh_tooltip()
        self.update()

    def set_command_enabled(self, enabled: bool) -> None:
        self._enabled_for_commands = enabled
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if enabled
            else Qt.CursorShape.ForbiddenCursor
        )
        if not enabled:
            self._cancel_drag()
        self._refresh_tooltip()
        self.update()

    @property
    def position(self) -> ValvePosition:
        return self._position

    @staticmethod
    def _angle_for(position: ValvePosition) -> float:
        if position is ValvePosition.OPEN:
            return OPEN_DEGREES
        if position is ValvePosition.CLOSED:
            return SHUT_DEGREES
        return UNSURE_DEGREES

    def _animate_to(self, angle: float) -> None:
        self._animation.stop()
        self._animation.setStartValue(float(self._angle))
        self._animation.setEndValue(float(angle))
        self._animation.start()

    def _on_animation_step(self, value) -> None:
        self._angle = float(value)
        self.update()

    def _refresh_tooltip(self) -> None:
        if not self._enabled_for_commands:
            self.setToolTip("No telemetry link to command over.")
            return
        self.setToolTip(
            f"Jaws read {self._position.caption}, from ulRaw[9] — what the "
            "firmware reports, not what was last commanded.\n"
            "Drag the jaws apart to open, together to shut. Click to toggle."
        )

    # ------------------------------------------------------------- input --
    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton or not self._enabled_for_commands:
            event.ignore()
            return
        self._pressed_at = event.position()
        self._dragging = False
        self._drag_angle = self._angle
        self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._pressed_at is None:
            return
        if not self._dragging:
            # A few pixels of slop, so a click with a shaky hand stays a click
            # rather than becoming a one-pixel drag that commits the opposite
            # command.
            if (event.position() - self._pressed_at).manhattanLength() < 4:
                return
            self._dragging = True
        self._drag_angle = self._angle_at(event.position())
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if self._pressed_at is None or not self._enabled_for_commands:
            self._cancel_drag()
            return
        if self._dragging and self._drag_angle is not None:
            midpoint = SHUT_DEGREES + (OPEN_DEGREES - SHUT_DEGREES) * COMMIT_FRACTION
            command = (ValveCommand.OPEN if self._drag_angle >= midpoint
                       else ValveCommand.CLOSE)
        else:
            # A plain click asks for the opposite of what the buoy reports.
            # From idle or unknown it asks for open, because that is the one
            # request whose outcome is unambiguous to look at.
            command = (ValveCommand.CLOSE if self._position is ValvePosition.OPEN
                       else ValveCommand.OPEN)
        self._cancel_drag()
        self.command_requested.emit(command)

    def keyPressEvent(self, event) -> None:
        """Keyboard equivalents, so this is not a drag-only control.

        A picture that can only be operated by dragging is unusable to anyone
        who cannot drag precisely, and unscriptable in a test.
        """
        if not self._enabled_for_commands:
            super().keyPressEvent(event)
            return
        key = event.key()
        if key in (Qt.Key.Key_O, Qt.Key.Key_Right, Qt.Key.Key_Plus):
            self.command_requested.emit(ValveCommand.OPEN)
        elif key in (Qt.Key.Key_C, Qt.Key.Key_Left, Qt.Key.Key_Minus):
            self.command_requested.emit(ValveCommand.CLOSE)
        elif key in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.command_requested.emit(
                ValveCommand.CLOSE if self._position is ValvePosition.OPEN
                else ValveCommand.OPEN)
        else:
            super().keyPressEvent(event)

    def _cancel_drag(self) -> None:
        self._pressed_at = None
        self._dragging = False
        self._drag_angle = None
        self.update()

    def _angle_at(self, point: QPointF) -> float:
        """Cursor -> the swing the operator is asking for.

        Horizontal distance from the centre line, not an angle about the hub:
        the jaws separate sideways, so sideways is the direction the hand is
        already moving. Measuring an angle here would make the same gesture
        mean different things at different heights up the widget.
        """
        hub = self._hub()
        reach = max(12.0, self.width() / 2.0 - 8.0)
        fraction = min(1.0, abs(point.x() - hub.x()) / reach)
        return SHUT_DEGREES + (OPEN_DEGREES - SHUT_DEGREES) * fraction

    # ------------------------------------------------------------- paint --
    def _hub(self) -> QPointF:
        rect = self.rect()
        # Low in the widget: everything above the hub is jaw, and the jaws need
        # the room.
        return QPointF(rect.width() / 2.0, rect.height() * 0.74)

    def _scale(self) -> float:
        rect = self.rect()
        return min(rect.width() / 86.0, rect.height() / 108.0)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self._hub())
        scale = max(0.5, self._scale())
        painter.scale(scale, scale)

        colour = COLOURS[self._position]
        self._paint_mount(painter)
        for sign in (1.0, -1.0):
            self._paint_jaw(painter, sign, self._angle, colour, ghost=False)
        self._paint_hub(painter, colour)

        # The request, over the top and dashed. Drawn last so it is never
        # hidden by the solid jaws it is being compared against.
        if self._dragging and self._drag_angle is not None:
            for sign in (1.0, -1.0):
                self._paint_jaw(painter, sign, self._drag_angle, GHOST, ghost=True)

        painter.end()

    def _paint_mount(self, painter: QPainter) -> None:
        """Stem, collar and mounting block, below the hub."""
        pen = QPen(BODY, LINE_WIDTH)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRectF(-STEM_HALF_WIDTH, 2.0, STEM_HALF_WIDTH * 2.0, 18.0))
        painter.drawRoundedRect(QRectF(-13.0, 18.0, 26.0, 9.0), 3.0, 3.0)
        painter.drawRoundedRect(QRectF(-22.0, 25.0, 44.0, 14.0), 4.0, 4.0)

    def _paint_hub(self, painter: QPainter, colour: QColor) -> None:
        """The gear the arms hang off, drawn after them so it caps the joint."""
        pen = QPen(colour, LINE_WIDTH)
        painter.setPen(pen)
        painter.setBrush(self.palette().window())
        painter.drawEllipse(QPointF(0.0, 0.0), HUB_RADIUS, HUB_RADIUS)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(0.0, 0.0), BORE_RADIUS, BORE_RADIUS)

    def _paint_jaw(self, painter: QPainter, sign: float, angle: float,
                   colour: QColor, *, ghost: bool) -> None:
        painter.save()
        # MIRROR for the second arm rather than negating the angle. Mirroring
        # flips the handedness of the rotation as well as the shape, so one
        # path and one angle give a symmetric pair; negating the angle instead
        # swings both arms the same way and draws them crossed.
        painter.scale(sign, 1.0)
        painter.rotate(angle)

        pen = QPen(colour, LINE_WIDTH,
                   Qt.PenStyle.DashLine if ghost else Qt.PenStyle.SolidLine)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath(QPointF(*JAW_POINTS[0]))
        for x, y in JAW_POINTS[1:]:
            path.lineTo(x, y)
        painter.drawPath(path)
        painter.restore()
