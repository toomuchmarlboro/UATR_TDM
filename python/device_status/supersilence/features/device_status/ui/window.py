"""What each unit is hearing, and what its link is doing.

One buoy page per unit carries its sixteen channel meters, gain controls, and
acquisition counters. Telemetry has its own per-unit pages beside it, where link
statistics and decoded fields answer the separate question "what is T3 saying?".

The window owns no services. It is handed the acquisition and telemetry services
and reads them on a timer; it never starts or stops either, so a closed status
window cannot affect whether the console is receiving.

The in-array checkboxes on that same panel take the same route, with one
difference: the service can refuse. Too few live channels and there is no
array left to estimate from, so the refusal is shown on the status bar and the
checkbox is put back — the panel never shows a selection the pipeline did not
take.

Two deliberate exceptions. The channel gain panel on each unit page writes
through to the acquisition service and, when a settings repository is given,
persists the change — safe by the same measure as everything else here, since
the gain lives in the service and in SQLite, not in the window, so closing the
window loses nothing and a console that never opens it runs exactly as it
would have before gain control existed. The 48 V phantom power control on
each page is a real command sent to that unit's own board over the network
(`infrastructure/control/phantom_power.py`) — the one place this window
reaches past acquisition and telemetry into hardware it does not otherwise
touch. It is never persisted and never restored on a later launch; see that
module's docstring for why. What it *displays*, though, comes back through
acquisition like everything else here: the board reports what it is driving in
every audio packet, so the control follows the board and a click that the FPGA
refuses snaps back, with the control's tooltip naming the gate that refused it.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from time import monotonic

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from supersilence.features.device_status.data.live_audio_monitor import (
    LiveAudioMonitor,
)
from supersilence.features.device_status.domain.gain_profile import (
    parse_gain_profile,
    select_unit_gains,
    serialize_gain_profile,
)
from supersilence.features.device_status.domain.meter_scale import summarize
from supersilence.features.device_status.domain.status_lines import (
    console_summary,
    describe_acquisition,
    describe_array_footprint,
    describe_geometry_refusals,
    describe_histogram,
    describe_pipeline,
    describe_unit_participation,
)
from supersilence.features.device_status.ui.channel_gain_panel import (
    GAIN_RANGE,
    ChannelGainPanel,
)
from supersilence.features.device_status.ui.channel_meters import ChannelMeterStrip
from supersilence.features.device_status.ui.phantom_power_control import (
    PhantomPowerControl,
)
from supersilence.features.device_status.ui.status_groups import GroupedStatusPanel
from supersilence.features.device_status.ui.telemetry_connection import (
    TelemetryConnectionBar,
)
from supersilence.features.device_status.ui.telemetry_fields import TelemetryFieldsPage
from supersilence.infrastructure.acquisition.channel_enable_configuration import (
    save_channels_enabled,
)
from supersilence.infrastructure.acquisition.channel_polarity_configuration import (
    save_channel_polarity,
)
from supersilence.infrastructure.acquisition.gain import balance_gains_db
from supersilence.infrastructure.acquisition.gain_configuration import (
    save_channel_gains_db,
)
from supersilence.infrastructure.telemetry.configuration import (
    load_compass_offsets,
    save_compass_offset,
)

WINDOW_NAME = "device_status"
WINDOW_TITLE = "Device Status"

#: Meters are watched, not read: they have to move at something like the rate
#: the eye expects or a transient is invisible. The counters beside them are
#: cheap enough to refresh at the same rate.
DEFAULT_REFRESH_INTERVAL_MS = 200

ACQUISITION_GROUPS = (
    (
        "Source",
        (
            "Source type",
            "Input device",
            "Host API",
            "Input sample rate",
            "Source address",
            "Packet rate",
            "Packet age",
            "Callback status",
            "Receiver error",
        ),
    ),
    (
        "Packet accounting",
        (
            "Received packets",
            "Accepted packets",
            "Lost packets",
            "Dropped by this host",
            "Lost before this host",
            "Sequence restarts",
            "Invalid packets",
            "Duplicate packets",
            "Out-of-order packets",
            "Unknown-source packets",
            "Callback faults",
        ),
    ),
    (
        "Queues",
        (
            "Queued raw packets",
            "Raw queue overflows",
            "Queued sample blocks",
            "Sample queue overflows",
            "Queued windows",
            "Window queue overflows",
            "Dropped input blocks",
        ),
    ),
    ("Socket buffering", ("Receive buffer", "Receiver backlog")),
)

PIPELINE_GROUPS = (
    ("Provider", ("Running", "Orientation", "Queued frames", "Dropped frames")),
    (
        "Processing",
        (
            "Windows analysed",
            "Windows skipped",
            "Windows refused (degraded input)",
            "Observations published",
        ),
    ),
    (
        "Fusion",
        (
            "Epochs with contributors",
            "Epochs with one unit",
            "Epoch cadence",
            "Epoch synchronization",
            "Associations formed",
            "Solutions refused",
        ),
    ),
    ("Errors", ("Transform error", "Identity error", "Worker error")),
    ("Array footprint", ()),
    ("Fleet roll call", ()),
    ("Fleet exclusions", ()),
    ("Triangulation refusals", ()),
    ("Refused geometry", ()),
)


class UnitStatusPage(QWidget):
    """One buoy: channel meters, gain controls, and acquisition statistics."""

    def __init__(self, unit_identifier: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.unit_identifier = unit_identifier
        self.setObjectName(f"device_status_unit_{unit_identifier}")

        self.meters = ChannelMeterStrip(unit_identifier, self)
        self.gain_panel = ChannelGainPanel(unit_identifier, self)
        self.phantom_power = PhantomPowerControl(unit_identifier, self)
        self.summary = QLabel("no samples yet", self)
        self.summary.setObjectName(f"device_status_summary_{unit_identifier}")

        self.acquisition_statistics = GroupedStatusPanel(ACQUISITION_GROUPS, self)
        self.acquisition_statistics.setObjectName(f"acquisition_statistics_unit_{unit_identifier}")
        self._acquisition_rows = self.acquisition_statistics.rows

        self.acquisition_scroll = QScrollArea(self)
        self.acquisition_scroll.setWidgetResizable(True)
        self.acquisition_scroll.setWidget(self.acquisition_statistics)

        # Summary and the phantom power control share a row at the very top —
        # phantom power is a real, board-wide hazard state, and keeping it out
        # of the scrolling counters area means it is never scrolled out of
        # sight while it might be on.
        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(self.summary, 1)
        header_layout.addWidget(self.phantom_power)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.addWidget(header)
        layout.addWidget(self.meters, 3)
        layout.addWidget(self.gain_panel)
        layout.addWidget(self.acquisition_scroll, 2)

    def set_levels(self, levels) -> None:
        self.meters.set_levels(levels)
        self.summary.setText(f"Unit {self.unit_identifier}: {summarize(levels)}")

    def set_acquisition(self, health) -> None:
        self.acquisition_statistics.set_rows(describe_acquisition(health))
        # 48 V comes back on the same health object as the packet counters
        # because it arrives on the same packets. See
        # `infrastructure/acquisition/uatr_tdm.py`. An ASIO sound card has no
        # such field and no board behind it to have one, so it reports the
        # same "unknown" a network unit that has not been heard from does —
        # which is exactly right, and why this reads the attribute rather than
        # inventing a phantom field on a source that has no phantom power.
        self.phantom_power.set_readback(getattr(health, "phantom_power", None))

    def acquisition_value(self, caption: str) -> str:
        return self.acquisition_statistics.value(caption)


class PipelinePage(QWidget):
    """Compatibility view for callers outside the composed application.

    The application no longer injects a target provider into Device Status;
    operators use the dedicated Triangulation window. Keeping this class avoids
    breaking concurrent callers while that ownership transition settles.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("device_status_pipeline")
        self.groups = GroupedStatusPanel(PIPELINE_GROUPS, self)
        self.groups.setObjectName("device_status_pipeline_groups")
        self._stage_rows: dict[str, QLabel] = {}
        self._participation_rows = self.groups.group("Fleet roll call").rows
        self._exclusion_rows = self.groups.group("Fleet exclusions").rows
        self._refusal_rows = self.groups.group("Triangulation refusals").rows
        self._geometry_rows = self.groups.group("Refused geometry").rows
        self._footprint_rows = self.groups.group("Array footprint").rows
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.groups)
        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll)

    def set_array_footprint(self, footprint) -> None:
        self.groups.set_group_rows("Array footprint", describe_array_footprint(footprint))

    def set_health(self, health) -> None:
        self.groups.set_rows(describe_pipeline(health))
        self._stage_rows.clear()
        for title in ("Provider", "Processing", "Fusion", "Errors"):
            self._stage_rows.update(self.groups.group(title).rows)
        self.groups.set_group_rows(
            "Fleet roll call",
            describe_unit_participation(() if health is None else health.unit_participation),
        )
        self.groups.set_group_rows(
            "Fleet exclusions",
            describe_histogram(() if health is None else health.exclusions),
        )
        self.groups.set_group_rows(
            "Triangulation refusals",
            describe_histogram(() if health is None else health.triangulation_failures),
        )
        self.groups.set_group_rows(
            "Refused geometry",
            describe_geometry_refusals(None if health is None else health.geometry_refusals),
        )

    def stage_value(self, caption: str) -> str:
        return self._stage_rows[caption].text()

    def participation_value(self, caption: str) -> str:
        return self._participation_rows[caption].text()

    def exclusion_value(self, caption: str) -> str:
        return self._exclusion_rows[caption].text()

    def refusal_value(self, caption: str) -> str:
        return self._refusal_rows[caption].text()

    def geometry_value(self, caption: str) -> str:
        return self._geometry_rows[caption].text()

    def footprint_value(self, caption: str) -> str:
        return self._footprint_rows[caption].text()


class DeviceStatusWindow(QMainWindow):
    """Per-unit hardware status: channel levels, acquisition, and telemetry."""

    #: Emitted after a compass offset is persisted, so the application can tell
    #: the running orientation source without this window knowing what one is.
    #: The offset is a correction to the sensor's yaw, so it has to reach every
    #: consumer of that yaw — the instruments here and the bearings on the map.
    compass_offset_saved = Signal(int, float)

    def __init__(
        self,
        acquisition_service=None,
        telemetry_service=None,
        parent: QWidget | None = None,
        *,
        target_provider=None,
        array_footprint=None,
        refresh_interval_ms: int = DEFAULT_REFRESH_INTERVAL_MS,
        settings=None,
        phantom_power_control: Callable[[int, bool], None] | None = None,
        telemetry_connection=None,
        audio_monitor_factory=LiveAudioMonitor,
    ) -> None:
        super().__init__(parent)
        self._acquisition_service = acquisition_service
        self._telemetry_service = telemetry_service
        self._target_provider = target_provider
        # Persists operator calibration changes only; services keep ownership of
        # their live state.
        self._settings = settings
        self._compass_offsets = load_compass_offsets(settings) if settings is not None else {}
        # Sends the real command; this window only relays what the operator
        # clicked. `None` (no acquisition-configured address to send it to,
        # or a caller — chiefly tests — that never supplied one) leaves the
        # button present but inert rather than hiding it, matching how a gain
        # edit with no settings still applies live instead of being refused.
        self._phantom_power_control = phantom_power_control
        #: Optional bench control over where telemetry points and whether it is
        #: up. An object with addresses(), port(), connected(), connect(…) and
        #: disconnect() — duck-typed like everything else this window is handed,
        #: and supplied by whoever composed the application, because starting
        #: and stopping services is theirs to do and not this window's.
        #: `None` leaves the Telemetry tab exactly as it was.
        self._telemetry_connection = telemetry_connection
        #: How a gain file is chosen. Replaceable so a test can name a path
        #: without a modal file dialog. Each returns the chosen path, or an
        #: empty string when the operator cancelled.
        self.choose_export_path: Callable[[str, str], str] = self._ask_for_export_path
        self.choose_import_path: Callable[[str], str] = self._ask_for_import_path
        self._supports_hardware_control = bool(acquisition_service is None or getattr(acquisition_service, "supports_hardware_control", True))
        self.setWindowTitle(WINDOW_TITLE)
        self.setObjectName(WINDOW_NAME)
        self.resize(1080, 720)

        self.audio_monitor = audio_monitor_factory(acquisition_service, self) if acquisition_service is not None else None
        if self.audio_monitor is not None:
            self.audio_monitor.selection_changed.connect(self._sync_heard_channel_buttons)
            self.audio_monitor.failed.connect(self._show_hearing_failure)
            self.statusBar().setObjectName("device_status_status")

        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("device_status_sections")
        self.buoys = QWidget(self)
        self.buoys.setObjectName("device_status_buoys")
        self.buoy_tabs = QTabWidget(self.buoys)
        self.buoy_tabs.setObjectName("device_status_buoy_units")
        buoy_layout = QVBoxLayout(self.buoys)
        buoy_layout.addWidget(self.buoy_tabs)
        self.pages: dict[int, UnitStatusPage] = {}
        for unit_identifier in self._unit_identifiers():
            page = UnitStatusPage(unit_identifier, self.buoy_tabs)
            self.pages[unit_identifier] = page
            self.buoy_tabs.addTab(page, f"T{unit_identifier}")
            has_live_acquisition = self._acquisition_service is not None and unit_identifier in self._acquisition_service.unit_identifiers
            page.meters.set_hearing_available(has_live_acquisition)
            if has_live_acquisition and self.audio_monitor is not None:
                page.meters.hear_requested.connect(self._toggle_hearing)
            if has_live_acquisition:
                initial_gains_db = self._acquisition_service.channel_gains_db(unit_identifier)
                page.gain_panel.set_gains_db(initial_gains_db)
                # The meter's marker line, not the bar: see `channel_meters.py`.
                page.meters.set_gains_db(initial_gains_db)
                page.gain_panel.gain_changed.connect(self._apply_gain_change)
                page.gain_panel.balance_requested.connect(lambda identifier=unit_identifier: self._balance_channels(identifier))
                initial_enabled = self._acquisition_service.channels_enabled(unit_identifier)
                page.gain_panel.set_channels_enabled(initial_enabled)
                page.meters.set_channels_enabled(initial_enabled)
                page.gain_panel.enabled_changed.connect(self._apply_channel_enabled)
                page.gain_panel.set_channel_polarity(self._acquisition_service.channel_polarity(unit_identifier))
                page.gain_panel.polarity_changed.connect(self._apply_channel_polarity)
            # Not behind `has_live_acquisition`: a file of gains can be written
            # and read for a unit that is not currently streaming, and the
            # faders are the authority on what would be applied when it is.
            page.gain_panel.export_requested.connect(self._export_channel_gains)
            page.gain_panel.import_requested.connect(self._import_channel_gains)
            if self._phantom_power_control is not None:
                page.phantom_power.toggled_by_operator.connect(lambda enabled, identifier=unit_identifier: self._phantom_power_control(identifier, enabled))
            page.phantom_power.setEnabled(self._supports_hardware_control)
        if self.pages:
            self.tabs.addTab(self.buoys, "Buoys")
        # The decoded telemetry fields, one subtab per unit. Only built when
        # there is a telemetry service: a tab of ten dashes says a field map is
        # broken when the truth is that telemetry is switched off.
        self.telemetry_fields = (
            TelemetryFieldsPage(
                self._unit_identifiers(),
                self,
                compass_offsets=self._compass_offsets,
                on_compass_offset_saved=self._save_compass_offset,
            )
            if telemetry_service is not None
            else None
        )
        # The bench connection bar, above the fields it decides the content of.
        # Present only when a caller supplied something that can actually do the
        # connecting: this window owns no services and does not start one, so
        # without a controller there is nothing a button here could do. See
        # `telemetry_connection.py`.
        self.telemetry_connection = None
        if self.telemetry_fields is not None:
            # The valve lives in its own box on the Telemetry tab, beside the
            # compass and the artificial horizon, because it answers the same
            # kind of question they do and is fed from the same snapshot. It is
            # the only one of them that also commands, so the window has to
            # carry the click out to the service — see _send_valve_command.
            for unit_identifier in self._unit_identifiers():
                panel = self.telemetry_fields.instrument_panel(unit_identifier)
                panel.valve.command_requested.connect(
                    lambda command, identifier=unit_identifier:
                    self._send_valve_command(identifier, command))
            telemetry_tab: QWidget = self.telemetry_fields
            if self._telemetry_connection is not None:
                self.telemetry_connection = TelemetryConnectionBar(
                    self._telemetry_connection.addresses(),
                    self._telemetry_connection.port(),
                    self,
                )
                self.telemetry_connection.connect_requested.connect(self._connect_telemetry)
                self.telemetry_connection.disconnect_requested.connect(self._disconnect_telemetry)
                self.telemetry_connection.set_connected(self._telemetry_connection.connected())
                telemetry_tab = QWidget(self)
                telemetry_layout = QVBoxLayout(telemetry_tab)
                telemetry_layout.setContentsMargins(8, 8, 8, 8)
                telemetry_layout.addWidget(self.telemetry_connection)
                telemetry_layout.addWidget(self.telemetry_fields, 1)
            self.tabs.addTab(telemetry_tab, "Telemetry")
        self.pipeline = PipelinePage(self) if target_provider is not None else None
        if self.pipeline is not None:
            self.pipeline.set_array_footprint(array_footprint)
            self.tabs.addTab(self.pipeline, "Pipeline")
        self.setCentralWidget(self.tabs)

        if not self.pages:
            # Nothing to show, and an empty tab strip would read as four healthy
            # units with no channels rather than as no service at all.
            empty = QLabel("No acquisition or telemetry service is running.", self)
            empty.setObjectName("device_status_empty")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font = QFont(empty.font())
            font.setPointSize(font.pointSize() + 2)
            empty.setFont(font)
            self.setCentralWidget(empty)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(refresh_interval_ms)
        self.refresh()

    def _unit_identifiers(self) -> tuple[int, ...]:
        identifiers: set[int] = set()
        for service in (self._acquisition_service, self._telemetry_service):
            if service is not None:
                identifiers.update(service.unit_identifiers)
        return tuple(sorted(identifiers))

    def refresh(self) -> None:
        """Re-read both services. Missing services simply contribute nothing."""
        if self._acquisition_service is not None:
            for levels in self._acquisition_service.levels():
                page = self.pages.get(levels.unit_identifier)
                if page is not None:
                    page.set_levels(levels)
            for health in self._acquisition_service.health():
                page = self.pages.get(health.unit_identifier)
                if page is not None:
                    page.set_acquisition(health)
        if self._telemetry_service is not None:
            now = monotonic()
            health_provider = getattr(
                self._telemetry_service,
                "unit_health",
                self._telemetry_service.health,
            )
            for health in health_provider():
                if self.telemetry_fields is not None:
                    self.telemetry_fields.observe(health, now)
        if self.pipeline is not None and self._target_provider is not None:
            self.pipeline.set_health(self._target_provider.health())

    def _connect_telemetry(self, addresses: dict, port: int) -> None:
        """Bring the telemetry links up on the addresses in the bar.

        The controller does the work and returns why not; this only carries the
        answer back to the bar. A refused connect leaves the button showing
        "connect" rather than latching, because the links did not come up.
        """
        try:
            error = self._telemetry_connection.connect(dict(addresses), int(port))
        except Exception as failure:  # noqa: BLE001 - a click must not kill the window
            error = str(failure) or failure.__class__.__name__
        self.telemetry_connection.set_connected(not error)
        if error:
            self.telemetry_connection.set_error(error)

    def _disconnect_telemetry(self) -> None:
        try:
            error = self._telemetry_connection.disconnect()
        except Exception as failure:  # noqa: BLE001
            error = str(failure) or failure.__class__.__name__
        # Shown as down either way. A disconnect that raised still stopped the
        # clients it reached, and presenting that as "still connected" would be
        # the more misleading of the two available lies.
        self.telemetry_connection.set_connected(False)
        if error:
            self.telemetry_connection.set_error(error)

    def _send_valve_command(self, unit_identifier: int, command) -> None:
        """Relay one valve request to the telemetry link and report what happened.

        RELAY, NOT COMMAND. This window owns no services, and that holds here
        too: the send goes to the telemetry service, which owns the socket, and
        this only carries the click there and the answer back. The alternative —
        opening a socket from the UI — would put a second connection on a link
        whose server takes one client.

        Never raises. The caller is a button, and a telemetry service that
        cannot send (an older one, or a test double) must leave the rest of the
        window working rather than take the click path down with it.
        """
        send = getattr(self._telemetry_service, "send_valve_command", None)
        if send is None:
            error = "this telemetry service cannot send commands"
        else:
            try:
                error = send(unit_identifier, command)
            except Exception as failure:  # noqa: BLE001 - a click must not kill the window
                error = str(failure) or failure.__class__.__name__
        if self.telemetry_fields is not None:
            self.telemetry_fields.instrument_panel(unit_identifier).valve.set_outcome(
                command, error)
        if error:
            # On the status bar as well as the page: a refusal that only ever
            # appeared in the small print beside the button is a refusal an
            # operator walks away from believing the valve moved.
            self.statusBar().showMessage(
                f"Unit {unit_identifier} valve {command.name}: {error}", 8000
            )

    def _save_compass_offset(self, unit_identifier: int, offset_degrees: float) -> None:
        """Persist one unit's direct-IMU heading correction and announce it.

        The signal carries the stored value rather than the typed one, and is
        emitted only after the write succeeds: a refused edit must not move the
        bearings on the map.
        """
        if self._settings is None:
            self._compass_offsets = {**self._compass_offsets, unit_identifier: offset_degrees}
            self.compass_offset_saved.emit(unit_identifier, float(offset_degrees))
            return
        self._compass_offsets = save_compass_offset(self._settings, unit_identifier, offset_degrees)
        self.compass_offset_saved.emit(unit_identifier, float(self._compass_offsets[unit_identifier]))

    def _apply_gain_change(self, unit_identifier: int, channel_index: int, gain_db: float) -> None:
        """Write through to the live pipeline, then persist if there is somewhere to.

        The service update always happens; a missing `settings` only means the
        change does not survive a restart, which is a defensible degraded mode
        for a window used without one (tests, mainly) rather than a reason to
        refuse the live edit.
        """
        self._acquisition_service.set_channel_gain_db(unit_identifier, channel_index, gain_db)
        current_gains_db = self._acquisition_service.channel_gains_db(unit_identifier)
        page = self.pages.get(unit_identifier)
        if page is not None:
            # The meter's marker line, not the bar: see `channel_meters.py`.
            page.meters.set_gains_db(current_gains_db)
        if self._settings is not None:
            save_channel_gains_db(self._settings, unit_identifier, current_gains_db)

    def _apply_channel_enabled(self, unit_identifier: int, channel_index: int, enabled: bool) -> None:
        """Switch a channel into or out of the array, then persist it.

        The service is the authority on whether the change is allowed — it
        refuses to leave a unit with too few elements to estimate a direction
        from. A refusal is reported on the status bar and the checkbox is put
        back where it was, rather than left showing a selection the pipeline
        never took.
        """
        page = self.pages.get(unit_identifier)
        try:
            current = self._acquisition_service.set_channel_enabled(unit_identifier, channel_index, bool(enabled))
        except ValueError as error:
            if page is not None:
                page.gain_panel.set_channels_enabled(self._acquisition_service.channels_enabled(unit_identifier))
            self.statusBar().showMessage(f"Unit {unit_identifier} channel {channel_index + 1}: {error}")
            return
        if page is not None:
            page.meters.set_channels_enabled(current)
            page.gain_panel.set_channels_enabled(current)
        if self._settings is not None:
            save_channels_enabled(self._settings, unit_identifier, current)

    def reload_channel_settings(self) -> None:
        """Re-read gain and polarity from the service into every fader.

        For a change made somewhere other than these controls — loading a
        recording's settings, chiefly. The faders are pushed at construction and
        never polled, deliberately (see `channel_gain_panel.py`), so a window
        already open would otherwise go on showing settings the pipeline has
        stopped using.
        """
        if self._acquisition_service is None:
            return
        for unit_identifier, page in self.pages.items():
            if unit_identifier not in self._acquisition_service.unit_identifiers:
                continue
            gains_db = self._acquisition_service.channel_gains_db(unit_identifier)
            page.gain_panel.set_gains_db(gains_db)
            page.meters.set_gains_db(gains_db)
            page.gain_panel.set_channel_polarity(self._acquisition_service.channel_polarity(unit_identifier))

    def _apply_channel_polarity(self, unit_identifier: int, channel_index: int, as_delivered: bool) -> None:
        """Record that one channel arrives inverted, and persist it.

        Unlike switching a channel out of the array there is nothing for the
        service to refuse: any combination of sixteen signs is a state the
        hardware can actually be in, including all of them. The status bar still
        says what happened, because a control that silently changes what every
        bearing means should not be silent.
        """
        current = self._acquisition_service.set_channel_polarity(unit_identifier, channel_index, bool(as_delivered))
        if self._settings is not None:
            save_channel_polarity(self._settings, unit_identifier, current)
        inverted = sum(1 for value in current if not value)
        state = "as delivered" if as_delivered else "inverted"
        self.statusBar().showMessage(f"Unit {unit_identifier} channel {channel_index + 1} marked {state} ({inverted} of {len(current)} inverted)")

    #: What the two file dialogs filter on, and the suffix an exported file
    #: gets when the operator types a bare name.
    GAIN_PROFILE_FILTER = "Channel gain profile (*.json);;All files (*)"
    GAIN_PROFILE_SUFFIX = ".json"

    def _ask_for_export_path(self, title: str, suggested_name: str) -> str:
        path, _ = QFileDialog.getSaveFileName(self, title, suggested_name, self.GAIN_PROFILE_FILTER)
        return path

    def _ask_for_import_path(self, title: str) -> str:
        path, _ = QFileDialog.getOpenFileName(self, title, "", self.GAIN_PROFILE_FILTER)
        return path

    def _channel_gains_db(self, unit_identifier: int) -> tuple[float, ...] | None:
        """This unit's gains from the service, falling back to what the faders show.

        The service is the authority whenever there is one. A window built
        without acquisition still has sixteen real values on screen, and
        exporting those is more useful than refusing.
        """
        page = self.pages.get(unit_identifier)
        if page is None:
            return None
        if self._acquisition_service is not None and unit_identifier in self._acquisition_service.unit_identifiers:
            return tuple(self._acquisition_service.channel_gains_db(unit_identifier))
        return tuple(page.gain_panel.gains_db())

    def _export_channel_gains(self, unit_identifier: int) -> None:
        """Write one unit's sixteen gains to a file the operator names.

        A failure — a cancelled dialog, a read-only folder, a value the format
        will not carry — is reported on the status bar and changes nothing.
        Nothing about the running pipeline is touched either way: this reads.
        """
        gains_db = self._channel_gains_db(unit_identifier)
        if gains_db is None:
            return
        path = self.choose_export_path(f"Export unit {unit_identifier} channel gains", f"unit-{unit_identifier}-channel-gains{self.GAIN_PROFILE_SUFFIX}")
        if not path:
            return
        destination = Path(path)
        if not destination.suffix:
            destination = destination.with_suffix(self.GAIN_PROFILE_SUFFIX)
        try:
            document = serialize_gain_profile({unit_identifier: gains_db}, GAIN_RANGE)
            destination.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        except (OSError, ValueError) as error:
            self.statusBar().showMessage(f"Unit {unit_identifier} gains not exported: {error}")
            return
        self.statusBar().showMessage(f"Unit {unit_identifier} gains exported to {destination}")

    def _import_channel_gains(self, unit_identifier: int) -> None:
        """Replace one unit's gains with a previously exported file's.

        The file is read and understood *before* the operator is asked to
        confirm, so a wrong file is refused with a reason instead of being
        confirmed twice and then failing. Once confirmed, the values reach the
        pipeline through the panel's ordinary edit path, so the live service
        update and the SQLite write are the same ones a drag performs — there
        is no second way for gain to be applied.
        """
        page = self.pages.get(unit_identifier)
        if page is None:
            return
        path = self.choose_import_path(f"Import unit {unit_identifier} channel gains")
        if not path:
            return
        source = Path(path)
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except OSError as error:
            self.statusBar().showMessage(f"Unit {unit_identifier} gains not imported: {error}")
            return
        except ValueError:
            self.statusBar().showMessage(f"Unit {unit_identifier} gains not imported: {source.name} is not a readable JSON file")
            return
        try:
            gains_db = select_unit_gains(parse_gain_profile(payload, GAIN_RANGE), unit_identifier)
        except ValueError as error:
            self.statusBar().showMessage(f"Unit {unit_identifier} gains not imported: {error}")
            return
        if not page.gain_panel.confirm_import(source.name):
            self.statusBar().showMessage(f"Unit {unit_identifier} gains left unchanged")
            return
        page.gain_panel.apply_gains_db(gains_db)
        self.statusBar().showMessage(f"Unit {unit_identifier} gains imported from {source}")

    def _balance_channels(self, unit_identifier: int) -> None:
        """Calibrate: set every live channel's gain to match the others now.

        Reads the raw levels the meter already has — see `channel_meters.py`
        and `gain.py`'s own module docstring for why gain is computed from the
        raw, pre-decimation signal rather than anything already gained. Nothing
        happens without a measurement to calibrate against, and each resulting
        change reaches `_apply_gain_change` through `ChannelGainPanel.
        apply_gains_db`'s normal signal path — this method computes the target
        gains and nothing else.
        """
        page = self.pages.get(unit_identifier)
        if page is None:
            return
        levels = page.meters.levels()
        if levels is None or not levels.measured or not levels.channels:
            return
        current_gains_db = self._acquisition_service.channel_gains_db(unit_identifier)
        enabled = self._acquisition_service.channels_enabled(unit_identifier)
        # A channel switched out of the array is excluded from the calibration
        # for the same reason a silent or clipping one is: it has no level
        # worth matching, and including it would drag every other channel's
        # target toward a number that means nothing. Its own gain is carried
        # through untouched.
        balanced = balance_gains_db(
            tuple(channel.rms_dbfs for channel in levels.channels),
            tuple(channel.silent or channel.clipping or not in_array for channel, in_array in zip(levels.channels, enabled)),
            current_gains_db,
        )
        page.gain_panel.apply_gains_db(balanced)

    def _toggle_hearing(self, unit_identifier: int, channel_index: int) -> None:
        if self.audio_monitor is None:
            return
        selected = self.audio_monitor.toggle(unit_identifier, channel_index)
        if selected:
            self.statusBar().clearMessage()
        # Start failure leaves the selection unchanged and therefore emits no
        # selection signal. Always reconcile after the attempt so a checkable
        # button cannot remain visually active without an audio route.
        self._sync_heard_channel_buttons(self.audio_monitor.selection)

    def _sync_heard_channel_buttons(self, selection) -> None:
        for unit_identifier, page in self.pages.items():
            channel_index = selection.channel_index if selection is not None and selection.unit_identifier == unit_identifier else None
            page.meters.set_heard_channel(channel_index)

    def _show_hearing_failure(self, message: str) -> None:
        self.statusBar().showMessage(f"Hearing unavailable: {message}")

    def summary(self) -> str:
        """The one-line form the console status bar shows."""
        return console_summary(
            None if self._acquisition_service is None else self._acquisition_service.health(),
            None if self._telemetry_service is None else self._telemetry_service.health(),
        )

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt naming
        """Stop polling and hearing; a hidden status window must cost nothing."""
        self._timer.stop()
        if self.audio_monitor is not None:
            self.audio_monitor.stop()
            self._sync_heard_channel_buttons(None)
            self.statusBar().clearMessage()
        super().closeEvent(event)

    def showEvent(self, event) -> None:  # noqa: N802 - Qt naming
        super().showEvent(event)
        if not self._timer.isActive():
            self._timer.start(DEFAULT_REFRESH_INTERVAL_MS)
        self.refresh()
