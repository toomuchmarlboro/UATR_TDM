"""Compact attitude, altimeter, and role-link summary."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from supersilence.features.device_status.domain.valve import valve_position
from supersilence.features.device_status.ui.valve_control import ValveControl
from supersilence.infrastructure.telemetry.tcp_client import TelemetryState
from supersilence.shared.telemetry_presentation import (
    ImuAttitudeSelector,
    TelemetryPresentation,
    select_telemetry_presentation,
)
from supersilence.shared.ui.attitude_instruments import (
    ArtificialHorizonWidget,
    CompassWidget,
)

LIVE = "#3fb950"
WARNING = "#d29922"
DIM = "#6b7280"

#: THE IMU IS NOT LISTED HERE, and that is a deliberate removal rather than an
#: oversight.
#:
#: Nothing on this page reads it. Despite its name, ImuAttitudeSelector takes
#: its attitude from `snapshot.gdat2` — the aux_vcu relays roll, pitch and yaw
#: into the sentence — so the compass and the artificial horizon are driven by
#: the GDAT2 link whether the IMU is up or not. The IMU row was therefore a
#: status line for a device that contributes nothing to what is on screen
#: beside it, and it read "reconnecting" against instruments that were visibly
#: working, which is the most misleading thing a status line can do.
#:
#: WHAT THIS COSTS: a dead IMU is now invisible on this page. It is a real
#: sensor on a real address (192.168.3.1<buoy>1) and it can be down without
#: anything here saying so. `python/imu_test.py` and `python/witmotion.py` in
#: this repo test it directly and are the place to find out.
ROLE_LINKS = (
    ("gdat2", "GDAT2", "message_age_seconds"),
    ("altimeter", "Ping1D", "reading_age_seconds"),
)


def _describe_state(snapshot: object, state: str) -> str:
    """Say what is actually wrong, not just which half of the cycle we are in.

    "reconnecting" is true but misleading for the commonest failure on this
    bench. A client that dials fine and then decodes nothing tears the
    connection down on its silence timer and waits before redialling, so it
    spends most of its time in the gap between attempts — and reports
    "reconnecting" while the socket in fact connects every single time. An
    operator reading that goes looking for a network fault.

    A link that has connected before and has never decoded a packet is not
    failing to connect. It is reaching something that is not talking, or not
    talking in the protocol this client parses — the trap this repo has hit
    once already, reading the IMU as $GDAT2.
    """
    if state != "reconnecting":
        return state
    connected_before = getattr(snapshot, "successful_connections", 0)
    if not connected_before:
        return state
    # `valid_packets` on the IMU, `valid_messages` on GDAT2. Absent on a
    # snapshot that counts neither, which then falls through unchanged.
    decoded = getattr(snapshot, "valid_packets",
                      getattr(snapshot, "valid_messages", None))
    if decoded is None:
        return state
    if decoded:
        return "dropped, redialling"
    received = getattr(snapshot, "bytes_received", 0)
    if received:
        return "connects, bytes undecodable"
    return "connects, sends nothing"


def _link_presentation(snapshot: object | None, caption: str, age_name: str) -> tuple[str, str]:
    if snapshot is None:
        return f"{caption}: unavailable", DIM
    raw_state = getattr(getattr(snapshot, "state", None), "value", getattr(snapshot, "state", "unknown"))
    state = _describe_state(snapshot, raw_state)
    address = getattr(snapshot, "sensor_address", "?")
    port = getattr(snapshot, "port", "?")
    age = getattr(snapshot, age_name, None)
    age_text = "no reading" if age is None else f"{float(age):.1f} s"
    text = f"{caption}: {state} · {address}:{port} · {age_text}"
    colour = LIVE if raw_state == "connected/fresh" else WARNING if raw_state in {"connecting", "connected/stale", "reconnecting"} else DIM
    return text, colour


class TelemetryRoleStatusBar(QFrame):
    """The three independent role states, kept visible below page content."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("telemetry_role_status_bar")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.link_labels = {role: QLabel(f"{caption}: unavailable", self) for role, caption, _age_name in ROLE_LINKS}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        for role, _caption, _age_name in ROLE_LINKS:
            label = self.link_labels[role]
            label.setWordWrap(True)
            layout.addWidget(label, 1)

    def set_snapshot(self, snapshot: object) -> None:
        for role, caption, age_name in ROLE_LINKS:
            link = getattr(snapshot, role, snapshot if role == "gdat2" else None)
            text, colour = _link_presentation(link, caption, age_name)
            self.link_labels[role].setText(text)
            self.link_labels[role].setStyleSheet(f"color: {colour};")


class TelemetryInstrumentPanel(QWidget):
    """One unit's selected compass, attitude, and altimeter readings."""

    def __init__(
        self,
        unit_identifier: int,
        parent: QWidget | None = None,
        *,
        compass_offset_degrees: float = 0.0,
        on_compass_offset_saved: Callable[[int, float], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.unit_identifier = unit_identifier
        self._attitude_selector = ImuAttitudeSelector()
        self._on_compass_offset_saved = on_compass_offset_saved
        self.compass = CompassWidget(self)
        self.horizon = ArtificialHorizonWidget(self)
        self.altimeter_distance = QLabel("—", self)
        self.altimeter_quality = QLabel("No fresh Ping1D reading", self)
        self.altimeter_quality.setWordWrap(True)

        self.compass_box = QGroupBox("Compass", self)
        compass_layout = QVBoxLayout(self.compass_box)
        compass_layout.addWidget(self.compass, 1)
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(QLabel("Compass offset", self.compass_box))
        self.compass_offset = QDoubleSpinBox(self.compass_box)
        self.compass_offset.setObjectName(f"telemetry_compass_offset_{unit_identifier}")
        self.compass_offset.setRange(-180.0, 180.0)
        self.compass_offset.setDecimals(1)
        self.compass_offset.setSingleStep(0.5)
        self.compass_offset.setSuffix("°")
        self.compass_offset.setWrapping(True)
        self.compass_offset.setValue(compass_offset_degrees)
        self.compass_offset.setToolTip(
            "Subtracted from the yaw this unit reports. It corrects the sensor, "
            "not the picture: the dial, the decoded yaw field, and every bearing "
            "steered from this unit all move with it. Positive means the compass "
            "reads high."
        )
        offset_layout.addWidget(self.compass_offset)
        compass_layout.addLayout(offset_layout)
        self.save_compass_offset_button = QPushButton("Save compass offset", self.compass_box)
        self.save_compass_offset_button.setObjectName(f"telemetry_save_compass_offset_{unit_identifier}")
        self.save_compass_offset_button.clicked.connect(self._save_compass_offset)
        compass_layout.addWidget(self.save_compass_offset_button)

        self.horizon_box = QGroupBox("Artificial horizon", self)
        horizon_layout = QVBoxLayout(self.horizon_box)
        horizon_layout.addWidget(self.horizon, 1)

        self.altimeter_box = QGroupBox("Altimeter", self)
        altimeter_layout = QVBoxLayout(self.altimeter_box)
        distance_font = QFont(self.altimeter_distance.font())
        distance_font.setPointSize(distance_font.pointSize() + 8)
        distance_font.setBold(True)
        self.altimeter_distance.setFont(distance_font)
        self.altimeter_distance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.altimeter_quality.setAlignment(Qt.AlignmentFlag.AlignCenter)
        altimeter_layout.addStretch(1)
        altimeter_layout.addWidget(self.altimeter_distance)
        altimeter_layout.addWidget(self.altimeter_quality)
        altimeter_layout.addStretch(1)

        # The valve sits with the instruments because it answers the same kind
        # of question they do — what is this unit's hardware doing right now —
        # and is fed from the same telemetry snapshot. It is the only one of
        # the four that also COMMANDS, which is why its own widget keeps the
        # request and the readback visibly apart. See `valve_control.py`.
        self.valve_box = QGroupBox("Valve", self)
        valve_layout = QVBoxLayout(self.valve_box)
        self.valve = ValveControl(unit_identifier, self.valve_box)
        valve_layout.addWidget(self.valve, 1)

        self.instrument_layout = QHBoxLayout()
        self.instrument_layout.addWidget(self.compass_box, 1)
        self.instrument_layout.addWidget(self.horizon_box, 1)
        self.instrument_layout.addWidget(self.altimeter_box, 1)
        self.instrument_layout.addWidget(self.valve_box, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.instrument_layout)

    def set_snapshot(self, snapshot: object) -> None:
        presentation = select_telemetry_presentation(
            snapshot,
            attitude_selector=self._attitude_selector,
            compass_offset_degrees=self.compass_offset.value(),
        )
        self._set_presentation(presentation)
        self._set_valve(snapshot)

    def _set_valve(self, snapshot: object) -> None:
        """Drive the valve box from the GDAT2 half of this unit's snapshot.

        Reads the raw sample rather than going through TelemetryPresentation:
        that type is about attitude and altimeter, and widening it to carry a
        digital I/O word would make every consumer of it handle a field only
        this box wants.

        FRESHNESS DECIDES WHETHER THERE IS A POSITION AT ALL. A link that is
        connected but silent leaves its last reading on screen looking
        healthy, and that reading is where the jaws WERE. Stale reports
        UNKNOWN; the command buttons stay live, because a link that has gone
        briefly quiet is exactly when an operator may most want the valve.
        """
        gdat2 = getattr(snapshot, "gdat2", snapshot)
        state = getattr(gdat2, "state", None)
        fresh = state is TelemetryState.CONNECTED_FRESH
        connected = state in (
            TelemetryState.CONNECTED_FRESH,
            TelemetryState.CONNECTED_STALE,
        )
        sample = getattr(gdat2, "latest_sample", None)
        digital_io = getattr(sample, "digital_io", None) if fresh else None
        self.valve.set_position(valve_position(digital_io))
        self.valve.set_available(connected)

    def set_compass_offset_degrees(self, offset_degrees: float) -> None:
        self.compass_offset.setValue(offset_degrees)

    def _save_compass_offset(self) -> None:
        if self._on_compass_offset_saved is not None:
            self._on_compass_offset_saved(self.unit_identifier, self.compass_offset.value())

    def _set_presentation(self, presentation: TelemetryPresentation) -> None:
        attitude = presentation.attitude
        if attitude is None:
            self.compass.set_heading(None)
            self.horizon.set_attitude(None, None)
        else:
            self.compass.set_heading(attitude.heading_degrees)
            self.horizon.set_attitude(attitude.roll_degrees, attitude.pitch_degrees)

        altimeter = presentation.altimeter
        if altimeter is None:
            self.altimeter_distance.setText("—")
            self.altimeter_quality.setText("No fresh Ping1D reading")
        else:
            self.altimeter_distance.setText("—" if altimeter.quality == "no echo" else f"{altimeter.distance_metres:.2f} m")
            self.altimeter_quality.setText(f"{altimeter.confidence_percent}% confidence · {altimeter.quality}")
