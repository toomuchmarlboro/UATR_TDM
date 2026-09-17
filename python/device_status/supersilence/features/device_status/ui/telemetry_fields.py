"""Every telemetry field of every unit, and whether to believe it.

The counters already on each unit's tab answer whether the link is up: bytes,
valid messages, disconnects. They cannot answer the question this page exists
for — whether the numbers arriving over that healthy link mean what their
headings say. A shifted field map produces perfectly framed, perfectly
checksummed, perfectly plausible-looking nonsense, and every counter beside it
stays green.

So this page shows the decoded value, what the value's own bound says about it,
and whether the field has ever been seen to move. The judgements are all in
``domain/telemetry_health.py``; this module draws them and does not decide
anything, which is what keeps the rules testable without a screen.

One subtab per unit rather than four tables side by side. Ten fields with a
value, a liveness column and a sentence of explanation is already a wide table,
and the question an operator arrives with is about one unit — "what is T3
saying" — not about the fleet.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QGroupBox,
    QHeaderView,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from supersilence.features.device_status.domain.telemetry_health import (
    CONSTANT,
    LIVE,
    TELEMETRY_FIELD_NAMES,
    ZERO,
    TelemetryHealth,
    UnitTelemetryHealth,
)
from supersilence.features.device_status.ui.attitude_instruments import (
    TelemetryInstrumentPanel,
    TelemetryRoleStatusBar,
)
from supersilence.features.device_status.ui.telemetry_statistics import (
    TelemetryStatisticsPanel,
)
from supersilence.shared.telemetry_presentation import normalise_signed_yaw
from supersilence.shared.ui.theme import DENSE_LABEL_POINT_SIZE

#: What each field is called on screen, and the unit it is read in. Keyed by
#: field name rather than positioned in a list, because a parallel list is
#: exactly how a display goes one place out of step with the map it is showing —
#: which is the fault this page exists to catch.
FIELD_LABELS: dict[str, tuple[str, str]] = {
    "leak_v": ("Leak sensor", "V"),
    "voltage_v": ("Bus voltage", "V"),
    "depth_m": ("Depth", "m"),
    "depth_temp_c": ("Depth sensor temperature", "°C"),
    "roll_deg": ("Roll", "°"),
    "pitch_deg": ("Pitch", "°"),
    "yaw_deg": ("Yaw", "°"),
    "altimeter_dist_mm": ("Altimeter distance", "mm"),
    "altimeter_conf_pct": ("Altimeter confidence", "%"),
    "digital_io": ("Digital I/O", ""),
}

if set(FIELD_LABELS) != set(TELEMETRY_FIELD_NAMES):
    raise RuntimeError(f"telemetry field labels must name exactly the telemetry fields: {sorted(set(FIELD_LABELS) ^ set(TELEMETRY_FIELD_NAMES))} differ")

HEADERS = ("Field", "Value", "Liveness", "Note")

#: THE AUX_VCU DOES NOT FILL THESE TWO. The altimeter is a separate device on a
#: separate link, and the manufacturer's own reference parser skips ulRaw[7:9]
#: for that reason, so they arrive as hard zero in every sentence forever.
#:
#: Reporting that as "the firmware is not filling this field" is true and
#: useless: it reads as a fault on a unit that is working exactly as designed,
#: and it sits two rows away from an Altimeter box showing a real range. So
#: these rows show the Ping1D's own reading instead, ATTRIBUTED — the value
#: comes from the altimeter link and the Note says so, rather than being
#: presented as something this sentence carried.
ALTIMETER_FIELDS: dict[str, str] = {
    "altimeter_dist_mm": "distance_millimetres",
    "altimeter_conf_pct": "confidence_percent",
}

#: The same palette the rest of the device-status window uses, so a fault reads
#: the same way here as it does on the counters beside it.
ALERT_COLOUR = "#f85149"
WARNING_COLOUR = "#d29922"
DIM_COLOUR = "#6b7280"
LIVE_COLOUR = "#3fb950"


def _format_value(value: float | int | None, unit: str) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        text = f"{value:.3f}".rstrip("0").rstrip(".")
    else:
        text = f"{value}"
    return f"{text} {unit}".strip()


def _format_field_value(
    name: str,
    value: float | int | None,
    unit: str,
    compass_offset_degrees: float,
) -> str:
    """Present the decoder yaw exactly as the corrected compass uses it."""
    if name == "yaw_deg" and value is not None:
        value = normalise_signed_yaw(float(value) - compass_offset_degrees)
    return _format_value(value, unit)


class UnitTelemetryFieldsPanel(QWidget):
    """One unit: its ten fields, their liveness, and the link's own staleness."""

    def __init__(
        self,
        unit_identifier: int,
        parent: QWidget | None = None,
        *,
        compass_offset_degrees: float = 0.0,
    ) -> None:
        super().__init__(parent)
        self.unit_identifier = unit_identifier
        self._compass_offset_degrees = float(compass_offset_degrees)
        self.setObjectName(f"telemetry_fields_unit_{unit_identifier}")

        self.link = QLabel("No sentence received.", self)
        self.link.setObjectName(f"telemetry_fields_link_{unit_identifier}")
        self.link.setWordWrap(True)

        box = QGroupBox("Decoded fields", self)
        box_layout = QVBoxLayout(box)
        self.table = QTableWidget(len(TELEMETRY_FIELD_NAMES), len(HEADERS), box)
        self.table.setObjectName(f"telemetry_fields_table_{unit_identifier}")
        self.table.setHorizontalHeaderLabels(HEADERS)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        note_font = self.table.font()
        note_font.setPointSize(DENSE_LABEL_POINT_SIZE)
        for row, name in enumerate(TELEMETRY_FIELD_NAMES):
            caption, _unit = FIELD_LABELS[name]
            for column in range(len(HEADERS)):
                item = QTableWidgetItem("")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if column == len(HEADERS) - 1:
                    item.setFont(note_font)
                self.table.setItem(row, column, item)
            self.table.item(row, 0).setText(caption)
        self._fit_table_to_contents()
        box_layout.addWidget(self.table)

        layout = QVBoxLayout(self)
        layout.addWidget(self.link)
        layout.addWidget(box)

    def set_health(self, health: TelemetryHealth, altimeter: object | None = None) -> None:
        """Draw one snapshot. Nothing is decided here.

        `altimeter` is that unit's Ping1D snapshot, used only to fill the two
        rows this sentence leaves at zero. Optional, so a caller with no
        altimeter link — or a test — gets the unmodified table.
        """
        self.link.setText(self._describe_link(health))
        self.link.setStyleSheet(f"color: {WARNING_COLOUR};" if health.is_stale else "")
        for row, name in enumerate(TELEMETRY_FIELD_NAMES):
            entry = health.field(name)
            _caption, unit = FIELD_LABELS[name]
            value_item = self.table.item(row, 1)
            liveness_item = self.table.item(row, 2)

            if name in ALTIMETER_FIELDS:
                value, liveness, note, colour = self._altimeter_row(name, altimeter, unit)
                value_item.setText(value)
                liveness_item.setText(liveness)
                self.table.item(row, 3).setText(note)
                value_item.setData(Qt.ItemDataRole.ForegroundRole, None)
                liveness_item.setForeground(QColor(colour))
                # Deliberately NOT dimmed with the rest of a stale GDAT2 link:
                # this row is not from that link, and a live sonar reading is
                # not a memory just because the aux_vcu went quiet.
                continue

            value_item.setText(
                _format_field_value(
                    name,
                    entry.latest,
                    unit,
                    self._compass_offset_degrees,
                )
            )
            liveness_item.setText(entry.describe_liveness())
            self.table.item(row, 3).setText(entry.explain())

            # A stale link dims everything: every value on the page is a memory,
            # and a field that is out of bounds in a memory is not news about
            # what the unit is doing now.
            if health.is_stale:
                value_item.setForeground(QColor(DIM_COLOUR))
                liveness_item.setForeground(QColor(DIM_COLOUR))
                continue
            if entry.plausible:
                # Cleared rather than set to a colour of our own: a value that is
                # simply correct should read in whatever the palette says text
                # reads in, on any theme.
                value_item.setData(Qt.ItemDataRole.ForegroundRole, None)
            else:
                value_item.setForeground(QColor(ALERT_COLOUR))
            liveness_item.setForeground(QColor(_liveness_colour(entry.state)))
        self._fit_table_to_contents()

    @staticmethod
    def _altimeter_row(name: str, altimeter: object | None, unit: str) -> tuple[str, str, str, str]:
        """-> (value, liveness, note, liveness colour) for one altimeter row.

        Says where the number came from in every case, including the cases
        where there is no number. "—" with no explanation next to a populated
        Altimeter box is the thing that sent someone looking at this table in
        the first place.
        """
        source = "Not in $GDAT2 — the altimeter is its own device."
        if altimeter is None:
            return "—", "no link", f"{source} No altimeter link on this unit.", DIM_COLOUR
        distance = getattr(altimeter, "distance", None)
        state = getattr(getattr(altimeter, "state", None), "value", "unknown")
        address = getattr(altimeter, "sensor_address", "?")
        if distance is None:
            return "—", state, f"{source} Nothing decoded yet from {address}.", WARNING_COLOUR
        value = getattr(distance, ALTIMETER_FIELDS[name], None)
        if value is None:
            return "—", state, f"{source} Field missing from {address}.", WARNING_COLOUR
        age = getattr(altimeter, "reading_age_seconds", None)
        # A Ping1D answers on request, so it legitimately goes quiet between
        # polls; 3 s is the same tolerance the overview gives it.
        fresh = age is not None and age <= 3.0
        age_text = "no reading" if age is None else f"{float(age):.1f} s ago"
        return (
            _format_value(value, unit),
            age_text,
            f"{source} From the Ping1D at {address}.",
            LIVE_COLOUR if fresh else WARNING_COLOUR,
        )

    def set_compass_offset_degrees(self, value: float) -> None:
        """Keep decoded-yaw presentation aligned after an offset edit."""
        self._compass_offset_degrees = float(value)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        self._fit_table_to_contents()

    def _fit_table_to_contents(self) -> None:
        self.table.resizeRowsToContents()
        rows_height = sum(self.table.rowHeight(row) for row in range(self.table.rowCount()))
        frame_height = self.table.frameWidth() * 2
        self.table.setFixedHeight(self.table.horizontalHeader().height() + rows_height + frame_height)

    def value(self, name: str) -> str:
        """What one field's value column reads, by field name."""
        return self.table.item(TELEMETRY_FIELD_NAMES.index(name), 1).text()

    def liveness(self, name: str) -> str:
        return self.table.item(TELEMETRY_FIELD_NAMES.index(name), 2).text()

    def note(self, name: str) -> str:
        return self.table.item(TELEMETRY_FIELD_NAMES.index(name), 3).text()

    @staticmethod
    def _describe_link(health: TelemetryHealth) -> str:
        if health.seconds_since_sentence is None:
            return "No sentence received. Nothing below has been read from this unit."
        if health.is_stale:
            return f"Stale: no sentence for {health.seconds_since_sentence:.1f} s. Every value below is the last one that arrived, not a reading."
        return f"{health.sentences} sentences, last {health.seconds_since_sentence:.1f} s ago."


class UnitTelemetryPage(QWidget):
    """One unit's link statistics and decoded telemetry fields."""

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
        self.setObjectName(f"device_status_telemetry_unit_{unit_identifier}")
        self.content = QWidget(self)
        self.content.setObjectName(f"device_status_telemetry_content_{unit_identifier}")
        self.statistics = TelemetryStatisticsPanel(unit_identifier, self.content)
        self.instruments = TelemetryInstrumentPanel(
            unit_identifier,
            self.content,
            compass_offset_degrees=compass_offset_degrees,
            on_compass_offset_saved=self._save_compass_offset,
        )
        self.fields = UnitTelemetryFieldsPanel(
            unit_identifier,
            self.content,
            compass_offset_degrees=compass_offset_degrees,
        )
        self._on_compass_offset_saved = on_compass_offset_saved
        self.status_bar = TelemetryRoleStatusBar(self)

        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.addWidget(self.statistics)
        self.content_layout.addWidget(self.instruments)
        self.content_layout.addWidget(self.fields)

        self.scroll = QScrollArea(self)
        self.scroll.setObjectName(f"device_status_telemetry_scroll_{unit_identifier}")
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll, 1)
        layout.addWidget(self.status_bar)

    def _save_compass_offset(self, unit_identifier: int, offset_degrees: float) -> None:
        """Apply one correction to both the compass and decoder-yaw field."""
        self.fields.set_compass_offset_degrees(offset_degrees)
        if self._on_compass_offset_saved is not None:
            self._on_compass_offset_saved(unit_identifier, offset_degrees)


def _liveness_colour(state: str) -> str:
    """Green proves life, red is a fault, amber is unproven, grey is nothing yet."""
    if state == LIVE:
        return LIVE_COLOUR
    if state == ZERO:
        return ALERT_COLOUR
    if state == CONSTANT:
        return WARNING_COLOUR
    return DIM_COLOUR


class TelemetryFieldsPage(QWidget):
    """The Telemetry tab: one subtab per unit, and the evidence behind each.

    Owns one ``UnitTelemetryHealth`` per unit and feeds it from the telemetry
    client snapshots the window already polls. Nothing else has to change on the
    refresh path, and no sample is consumed — the snapshot's latest sample is
    read, not drained, so the orientation transform still sees every sentence.
    """

    def __init__(
        self,
        unit_identifiers: tuple[int, ...],
        parent: QWidget | None = None,
        *,
        compass_offsets: Mapping[int, float] | None = None,
        on_compass_offset_saved: Callable[[int, float], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("device_status_telemetry_fields")
        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("telemetry_fields_units")
        self.unit_pages: dict[int, UnitTelemetryPage] = {}
        self.panels: dict[int, UnitTelemetryFieldsPanel] = {}
        self._health: dict[int, UnitTelemetryHealth] = {}
        self._seen_messages: dict[int, int] = {}
        self._seen_connections: dict[int, int] = {}
        for unit_identifier in unit_identifiers:
            page = UnitTelemetryPage(
                unit_identifier,
                self,
                compass_offset_degrees=(compass_offsets or {}).get(unit_identifier, 0.0),
                on_compass_offset_saved=on_compass_offset_saved,
            )
            self.unit_pages[unit_identifier] = page
            self.panels[unit_identifier] = page.fields
            self._health[unit_identifier] = UnitTelemetryHealth()
            self._seen_messages[unit_identifier] = 0
            self._seen_connections[unit_identifier] = 0
            self.tabs.addTab(page, f"T{unit_identifier}")
        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)

    def observe(self, snapshot, now: float) -> None:
        """Take one telemetry client snapshot and redraw that unit's panel.

        Two counters decide what happens rather than the sample itself. A rise
        in successful connections means the link was remade, and the unit's
        evidence is reset — otherwise a reconnected unit inherits the previous
        connection's proof of life and a field that died in between reads as
        live. A rise in valid messages means there is something new to record;
        without that check the same retained sample would be fed on every
        refresh and a field that never moved would still look constant, which is
        true but earned for the wrong reason.
        """
        unit_identifier = snapshot.unit_identifier
        health = self._health.get(unit_identifier)
        if health is None:
            return
        gdat2 = getattr(snapshot, "gdat2", snapshot)
        page = self.unit_pages[unit_identifier]
        page.instruments.set_snapshot(snapshot)
        page.status_bar.set_snapshot(snapshot)
        page.statistics.set_health(gdat2)
        connections = getattr(gdat2, "successful_connections", 0)
        if connections > self._seen_connections[unit_identifier]:
            health.reset()
            self._seen_connections[unit_identifier] = connections
            self._seen_messages[unit_identifier] = 0
        messages = getattr(gdat2, "valid_messages", 0)
        sample = gdat2.latest_sample
        if sample is not None and messages > self._seen_messages[unit_identifier]:
            health.observe(sample.values(), now, sample.raw_fields)
            self._seen_messages[unit_identifier] = messages
        # The altimeter rows come off the Ping1D link, not this sentence.
        self.panels[unit_identifier].set_health(
            health.snapshot(now), getattr(snapshot, "altimeter", None))

    def panel(self, unit_identifier: int) -> UnitTelemetryFieldsPanel:
        return self.panels[unit_identifier]

    def statistics_panel(self, unit_identifier: int) -> TelemetryStatisticsPanel:
        return self.unit_pages[unit_identifier].statistics

    def instrument_panel(self, unit_identifier: int) -> TelemetryInstrumentPanel:
        return self.unit_pages[unit_identifier].instruments

    def titles(self) -> tuple[str, ...]:
        return tuple(self.tabs.tabText(index) for index in range(self.tabs.count()))
