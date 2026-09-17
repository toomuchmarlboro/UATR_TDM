"""Guided, retained tone-capture workflow for Device Status DSP gains."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from supersilence.features.device_status.data.gain_balancing_coordinator import GainBalancingCoordinator
from supersilence.features.device_status.domain.gain_balancing import (
    DEFAULT_CAPTURE_SECONDS,
    DEFAULT_TONE_FREQUENCY_HZ,
    ToneMeasurement,
    measure_tone,
    propose_gains,
    validate_capture_request,
)
from supersilence.infrastructure.acquisition.gain import MAXIMUM_GAIN_DB, MINIMUM_GAIN_DB

WINDOW_NAME = "gain_balancing"
WINDOW_TITLE = "Gain Balancing"


class GainBalancingWindow(QMainWindow):
    """Record and review one controlled-tone WAV per physical element."""

    gains_requested = Signal(int, object)

    def __init__(self, acquisition_service, capture_root: Path, replay_loader=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = acquisition_service
        self._coordinator = GainBalancingCoordinator(acquisition_service, capture_root, sample_rate=24_000)
        self._replay_loader = replay_loader
        self._channel_index = 0
        self._measurements: dict[int, ToneMeasurement] = {}
        self._wav_paths: dict[int, Path] = {}
        self.setObjectName(WINDOW_NAME)
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(880, 680)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        form = QFormLayout()
        self.unit = QComboBox(central)
        for identifier in acquisition_service.unit_identifiers:
            self.unit.addItem(f"T{identifier}", identifier)
        self.frequency = QDoubleSpinBox(central)
        self.frequency.setRange(1.0, 11_999.0)
        self.frequency.setValue(DEFAULT_TONE_FREQUENCY_HZ)
        self.frequency.setSuffix(" Hz")
        self.duration = QDoubleSpinBox(central)
        self.duration.setRange(1.0, 120.0)
        self.duration.setValue(DEFAULT_CAPTURE_SECONDS)
        self.duration.setSuffix(" s")
        form.addRow("Unit", self.unit)
        form.addRow("Tone frequency", self.frequency)
        form.addRow("Capture duration", self.duration)
        layout.addLayout(form)

        self.instruction = QLabel("Click the hydrophone responding to the source. Its raw ADC level is shown before capture.", central)
        self.instruction.setWordWrap(True)
        layout.addWidget(self.instruction)
        self.channel_grid = QGridLayout()
        self.channel_buttons: list[QPushButton] = []
        for channel_index in range(16):
            button = QPushButton(central)
            button.clicked.connect(lambda _checked=False, index=channel_index: self._select_channel(index))
            self.channel_buttons.append(button)
            self.channel_grid.addWidget(button, channel_index // 4, channel_index % 4)
        layout.addLayout(self.channel_grid)
        actions = QHBoxLayout()
        self.capture_button = QPushButton("Record selected element", central)
        self.capture_button.clicked.connect(self._start_capture)
        self.replay_button = QPushButton("Assign replay WAV", central)
        self.replay_button.setEnabled(replay_loader is not None)
        self.replay_button.clicked.connect(self._assign_replay)
        self.apply_button = QPushButton("Apply reviewed gains", central)
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self._apply)
        actions.addWidget(self.capture_button)
        actions.addWidget(self.replay_button)
        actions.addWidget(self.apply_button)
        layout.addLayout(actions)
        self.results = QTableWidget(0, 5, central)
        self.results.setHorizontalHeaderLabels(("Element", "Tone dBFS", "Spread", "Proposed gain", "WAV"))
        layout.addWidget(self.results, 1)
        self.setCentralWidget(central)
        self.statusBar().showMessage("DSP gain only. Raw ADC preview and WAV capture never mute channels or alter hardware gain.")
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(200)
        self._refresh()

    def _select_channel(self, channel_index: int) -> None:
        self._channel_index = channel_index
        self._refresh_buttons()

    def _refresh(self) -> None:
        self._refresh_buttons()
        completed = self._coordinator.completed()
        if completed is None:
            return
        self._measurements[completed.channel_index] = measure_tone(
            completed.samples,
            channel_index=completed.channel_index,
            sample_rate=24_000,
            frequency_hz=self.frequency.value(),
        )
        self._wav_paths[completed.channel_index] = completed.wav_path
        self.capture_button.setEnabled(True)
        self.statusBar().showMessage(f"Element {completed.channel_index + 1} saved: {completed.wav_path}")
        self._refresh_results()

    def _refresh_buttons(self) -> None:
        levels = next((item for item in self._service.levels() if item.unit_identifier == self.unit.currentData()), None)
        for index, button in enumerate(self.channel_buttons):
            raw = "no signal" if levels is None or not levels.measured else f"{levels.channels[index].rms_dbfs:.1f} dBFS raw"
            button.setText(f"Hydrophone {index + 1}\n{raw}")
            button.setCheckable(True)
            button.setChecked(index == self._channel_index)

    def _start_capture(self) -> None:
        try:
            _frequency, duration = validate_capture_request(self.frequency.value(), self.duration.value())
            path = self._coordinator.start(int(self.unit.currentData()), self._channel_index, duration)
        except (RuntimeError, ValueError) as error:
            self.statusBar().showMessage(str(error))
            return
        self.capture_button.setEnabled(False)
        self.statusBar().showMessage(f"Recording hydrophone {self._channel_index + 1} to {path}")

    def _assign_replay(self) -> None:
        if self._replay_loader is None:
            return
        path_text, _selected_filter = QFileDialog.getOpenFileName(self, "Assign replay WAV", "", "WAV files (*.wav)")
        if not path_text:
            return
        path = Path(path_text)
        try:
            frequency, duration = validate_capture_request(self.frequency.value(), self.duration.value())
            samples, sample_rate = self._replay_loader(path, self._channel_index, duration)
            measurement = measure_tone(samples, channel_index=self._channel_index, sample_rate=sample_rate, frequency_hz=frequency)
        except (OSError, ValueError) as error:
            self.statusBar().showMessage(f"Cannot assign replay WAV: {error}")
            return
        self._measurements[self._channel_index] = measurement
        self._wav_paths[self._channel_index] = path
        self.statusBar().showMessage(f"Assigned {path.name} to element {self._channel_index + 1}")
        self._refresh_results()

    def _refresh_results(self) -> None:
        current = self._service.channel_gains_db(int(self.unit.currentData()))
        proposals = {
            item.channel_index: item
            for item in propose_gains(tuple(self._measurements.values()), current, minimum_gain_db=MINIMUM_GAIN_DB, maximum_gain_db=MAXIMUM_GAIN_DB)
        }
        self.results.setRowCount(len(self._measurements))
        for row, channel_index in enumerate(sorted(self._measurements)):
            item = self._measurements[channel_index]
            proposal = proposals.get(channel_index)
            values = (
                str(channel_index + 1),
                f"{item.tone_level_dbfs:.2f}",
                f"{item.level_spread_db:.2f}",
                "excluded" if proposal is None else f"{proposal.proposed_gain_db:.2f}",
                str(self._wav_paths[channel_index]),
            )
            for column, value in enumerate(values):
                self.results.setItem(row, column, QTableWidgetItem(value))
        self.apply_button.setEnabled(len(proposals) == 16)

    def _apply(self) -> None:
        unit_identifier = int(self.unit.currentData())
        current = self._service.channel_gains_db(unit_identifier)
        proposals = propose_gains(tuple(self._measurements.values()), current, minimum_gain_db=MINIMUM_GAIN_DB, maximum_gain_db=MAXIMUM_GAIN_DB)
        if len(proposals) != 16:
            self.statusBar().showMessage("Capture and validate all 16 elements before applying gains.")
            return
        gains = list(current)
        for proposal in proposals:
            gains[proposal.channel_index] = proposal.proposed_gain_db
        self.gains_requested.emit(unit_identifier, tuple(gains))
        self.statusBar().showMessage("Reviewed DSP gains applied. The retained WAVs remain unchanged.")

    def closeEvent(self, event) -> None:  # noqa: N802
        self._coordinator.cancel()
        self._timer.stop()
        super().closeEvent(event)
