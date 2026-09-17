"""Live raw-waveform tools presented together in one operator window."""

from __future__ import annotations

import time

import numpy as np
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from supersilence.features.device_status.data.raw_waveform_monitor import DEFAULT_RETAINED_FRAMES, DISPLAY_WINDOW_SECONDS
from supersilence.features.device_status.domain.raw_waveforms import (
    DEFAULT_BANDPASS_HIGH_HZ,
    DEFAULT_BANDPASS_LOW_HZ,
    ELEMENT_COUNT,
    CorrelationMatrixAccumulator,
    MatrixAnalysisMode,
    apply_polarity_signs,
    bandpass_waveforms,
    min_max_normalize,
    selected_waveforms,
    signed_correlation,
    validate_matrix_analysis_mode,
    waveform_correlation_matrix,
)
from supersilence.features.device_status.ui.correlation_matrix import CorrelationMatrixPlot
from supersilence.features.device_status.ui.waveform_plot import WaveformPlot
from supersilence.infrastructure.acquisition.uatr_tdm import SAMPLE_RATE

WINDOW_NAME = "raw_waveform_tools"
WINDOW_TITLE = "Raw Waveforms"
REFRESH_MILLISECONDS = 2_000
INITIAL_WINDOW_WIDTH = 1_200
INITIAL_WINDOW_HEIGHT = 760
NORMALIZATION_STATUS = "display: each element uses per-window min–max -1 to 1 · sum data is not renormalized; visible scale -1 to 1"
REFRESH_STATUS = "waveforms update every 2 s"
WINDOW_STATUS = f"shows latest {DISPLAY_WINDOW_SECONDS:.2f} s · {DEFAULT_RETAINED_FRAMES:,} samples at 24 kHz"


def correlation_text(correlation: float | None) -> str:
    """Format a signed zero-lag correlation without implying a phase estimator."""
    if correlation is None:
        return "Correlation r: N/A"
    magnitude = abs(correlation)
    strength = "strong" if magnitude >= 0.7 else "weak" if magnitude < 0.3 else "moderate"
    direction = "positive" if correlation > 0.0 else "negative" if correlation < 0.0 else "zero"
    return f"Correlation r: {correlation:+.3f} · {strength} {direction}"


class WaveformProcessingControls(QWidget):
    """Reusable opt-in band-pass and gain choices for derived waveform views."""

    changed = Signal()

    def __init__(self, gain_label: str, object_prefix: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.bandpass_enabled = QCheckBox("Apply band-pass", self)
        self.bandpass_enabled.setObjectName(f"{object_prefix}_bandpass_enabled")
        self.low_hz = self._frequency_control(f"{object_prefix}_bandpass_low_hz", DEFAULT_BANDPASS_LOW_HZ)
        self.high_hz = self._frequency_control(f"{object_prefix}_bandpass_high_hz", DEFAULT_BANDPASS_HIGH_HZ)
        self.low_hz.setMaximum(self.high_hz.value() - 1.0)
        self.high_hz.setMinimum(self.low_hz.value() + 1.0)
        self.include_gain = QCheckBox(gain_label, self)
        self.include_gain.setObjectName(f"{object_prefix}_include_gain")
        self.include_inversion = QCheckBox("Apply Device Status inversion", self)
        self.include_inversion.setObjectName(f"{object_prefix}_include_inversion")
        layout.addRow(self.include_inversion)
        layout.addRow(self.bandpass_enabled)
        layout.addRow("Low frequency", self.low_hz)
        layout.addRow("High frequency", self.high_hz)
        layout.addRow(self.include_gain)
        self.bandpass_enabled.toggled.connect(self.changed)
        self.include_inversion.toggled.connect(self.changed)
        self.include_gain.toggled.connect(self.changed)
        self.low_hz.valueChanged.connect(self._edges_changed)
        self.high_hz.valueChanged.connect(self._edges_changed)

    def _frequency_control(self, name: str, value: float) -> QDoubleSpinBox:
        control = QDoubleSpinBox(self)
        control.setObjectName(name)
        control.setDecimals(0)
        control.setRange(1.0, SAMPLE_RATE / 2.0 - 1.0)
        control.setSuffix(" Hz")
        control.setValue(value)
        return control

    def _edges_changed(self) -> None:
        self.low_hz.setMaximum(self.high_hz.value() - 1.0)
        self.high_hz.setMinimum(self.low_hz.value() + 1.0)
        self.changed.emit()

    def process(self, samples: np.ndarray, polarity_signs=None) -> np.ndarray:
        processed = np.asarray(samples)
        if self.include_inversion.isChecked():
            processed = apply_polarity_signs(processed, polarity_signs or (1,) * ELEMENT_COUNT)
        if self.bandpass_enabled.isChecked():
            processed = bandpass_waveforms(processed, self.low_hz.value(), self.high_hz.value(), sample_rate=SAMPLE_RATE)
        return processed

    def set_polarity_already_applied(self, applied: bool) -> None:
        if applied:
            self.include_inversion.setChecked(False)
            self.include_inversion.setText("Recorded inversion already applied")
            self.include_inversion.setEnabled(False)
        else:
            self.include_inversion.setText("Apply Device Status inversion")
            self.include_inversion.setEnabled(True)


class AllWaveformsTab(QWidget):
    """Sixteen physical-element waveforms in a compact four-by-four grid."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("all_raw_waveforms_tab")
        layout = QGridLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        self.plots = tuple(WaveformPlot(f"Element {identifier}", self) for identifier in range(1, ELEMENT_COUNT + 1))
        for index, plot in enumerate(self.plots):
            layout.addWidget(plot, index // 4, index % 4)

    def set_samples(self, samples: np.ndarray) -> None:
        values = np.asarray(samples)
        if values.ndim != 2 or values.shape[1] != ELEMENT_COUNT:
            raise ValueError(f"raw samples must have shape (frames, {ELEMENT_COUNT})")
        for index, plot in enumerate(self.plots):
            plot.set_waveform(min_max_normalize(values[:, index]), y_limit=1.0)


class ElementSumTab(QWidget):
    """Two independently normalized elements and their sample-wise sum."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("element_sum_tab")
        layout = QVBoxLayout(self)
        selectors = QWidget(self)
        selector_layout = QFormLayout(selectors)
        selector_layout.setContentsMargins(0, 0, 0, 0)
        self.first_element = self._selector("first_sum_element")
        self.second_element = self._selector("second_sum_element")
        self.second_element.setCurrentIndex(1)
        selector_layout.addRow("First element", self.first_element)
        selector_layout.addRow("Second element", self.second_element)
        layout.addWidget(selectors)
        self.processing = WaveformProcessingControls("Include Device Status gain in sum", "element_sum", self)
        self.processing.setObjectName("element_sum_processing")
        layout.addWidget(self.processing)
        self.correlation = QLabel("Correlation r: N/A", self)
        self.correlation.setObjectName("element_sum_correlation")
        layout.addWidget(self.correlation)
        self.first_plot = WaveformPlot("Element 1", self)
        self.second_plot = WaveformPlot("Element 2", self)
        self.sum_plot = WaveformPlot("Element 1 + Element 2", self)
        for plot in (self.first_plot, self.second_plot, self.sum_plot):
            layout.addWidget(plot, 1)
        self._samples = np.empty((0, ELEMENT_COUNT), dtype=np.float32)
        self._gain_multipliers = np.ones(ELEMENT_COUNT, dtype=np.float64)
        self._enabled_elements = (True,) * ELEMENT_COUNT
        self._polarity_signs = (1.0,) * ELEMENT_COUNT
        self._changing_selection = False
        self.first_element.currentIndexChanged.connect(lambda: self._selection_changed(self.first_element))
        self.second_element.currentIndexChanged.connect(lambda: self._selection_changed(self.second_element))
        self.processing.changed.connect(self._refresh_plots)

    @staticmethod
    def _selector(name: str) -> QComboBox:
        selector = QComboBox()
        selector.setObjectName(name)
        for identifier in range(1, ELEMENT_COUNT + 1):
            selector.addItem(f"Element {identifier}", identifier - 1)
        return selector

    def selected_elements(self) -> tuple[int, int]:
        return int(self.first_element.currentData()), int(self.second_element.currentData())

    def set_samples(self, samples: np.ndarray) -> None:
        values = np.asarray(samples)
        if values.ndim != 2 or values.shape[1] != ELEMENT_COUNT:
            raise ValueError(f"raw samples must have shape (frames, {ELEMENT_COUNT})")
        self._samples = values
        self._refresh_plots()

    def set_gain_multipliers(self, multipliers, *, refresh: bool = True) -> None:
        values = np.asarray(multipliers, dtype=np.float64)
        if values.shape != (ELEMENT_COUNT,) or not np.isfinite(values).all() or np.any(values <= 0.0):
            raise ValueError(f"element gain multipliers must contain {ELEMENT_COUNT} finite positive values")
        self._gain_multipliers = values.copy()
        if refresh:
            self._refresh_plots()

    def set_enabled_elements(self, enabled, *, refresh: bool = True) -> None:
        active = tuple(enabled)
        if len(active) != ELEMENT_COUNT or any(not isinstance(value, (bool, np.bool_)) for value in active):
            raise ValueError(f"enabled elements must contain {ELEMENT_COUNT} boolean values")
        self._enabled_elements = tuple(bool(value) for value in active)
        for selector in (self.first_element, self.second_element):
            model = selector.model()
            for index, is_enabled in enumerate(self._enabled_elements):
                model.item(index).setEnabled(is_enabled)
        self._reconcile_enabled_selection()
        if refresh:
            self._refresh_plots()

    def set_polarity_signs(self, signs, *, refresh: bool = True) -> None:
        values = tuple(float(value) for value in signs)
        if len(values) != ELEMENT_COUNT or any(value not in (-1.0, 1.0) for value in values):
            raise ValueError(f"polarity signs must contain {ELEMENT_COUNT} values of +1 or -1")
        self._polarity_signs = values
        if refresh:
            self._refresh_plots()

    def _reconcile_enabled_selection(self) -> None:
        available = [index for index, enabled in enumerate(self._enabled_elements) if enabled]
        if len(available) < 2:
            return
        first, second = self.selected_elements()
        selected = []
        for candidate in (first, second, *available):
            if candidate in available and candidate not in selected:
                selected.append(candidate)
            if len(selected) == 2:
                break
        self._changing_selection = True
        self.first_element.setCurrentIndex(selected[0])
        self.second_element.setCurrentIndex(selected[1])
        self._changing_selection = False

    def _selection_changed(self, changed: QComboBox) -> None:
        if self._changing_selection:
            return
        first, second = self.selected_elements()
        if first == second:
            self._changing_selection = True
            other = self.second_element if changed is self.first_element else self.first_element
            other.setCurrentIndex((first + 1) % ELEMENT_COUNT)
            self._changing_selection = False
        self._refresh_plots()

    def _refresh_plots(self) -> None:
        if sum(self._enabled_elements) < 2:
            unavailable = np.zeros(self._samples.shape[0], dtype=np.float64)
            self.correlation.setText("Correlation r: N/A · two ON elements required")
            self.first_plot.caption = "Element unavailable"
            self.second_plot.caption = "Element unavailable"
            self.sum_plot.caption = "Sum unavailable · two ON elements required"
            for plot in (self.first_plot, self.second_plot, self.sum_plot):
                plot.set_waveform(unavailable, y_limit=1.0)
            return
        first_index, second_index = self.selected_elements()
        processed = self.processing.process(self._samples, self._polarity_signs)
        gains = None
        if self.processing.include_gain.isChecked():
            gains = (self._gain_multipliers[first_index], self._gain_multipliers[second_index])
        first, second, summed = selected_waveforms(
            processed,
            first_index,
            second_index,
            sum_gain_multipliers=gains,
            enabled=self._enabled_elements,
        )
        self.correlation.setText(correlation_text(signed_correlation(processed[:, first_index], processed[:, second_index])))
        first_identifier = first_index + 1
        second_identifier = second_index + 1
        self.first_plot.caption = f"Element {first_identifier}"
        self.second_plot.caption = f"Element {second_identifier}"
        self.sum_plot.caption = f"Element {first_identifier} + Element {second_identifier}"
        self.first_plot.set_waveform(first, y_limit=1.0)
        self.second_plot.set_waveform(second, y_limit=1.0)
        self.sum_plot.set_waveform(summed, y_limit=1.0)


class CorrelationMatrixTab(QWidget):
    """All pairwise signed correlations for one shared waveform window."""

    capture_active_changed = Signal(bool)

    def __init__(self, parent: QWidget | None = None, *, clock=time.monotonic) -> None:
        super().__init__(parent)
        self.setObjectName("correlation_matrix_tab")
        layout = QVBoxLayout(self)
        mode_controls = QWidget(self)
        mode_layout = QFormLayout(mode_controls)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        self.analysis_mode = QComboBox(mode_controls)
        self.analysis_mode.setObjectName("correlation_analysis_mode")
        self.analysis_mode.setAccessibleName("Correlation matrix analysis mode")
        self.analysis_mode.addItem("Live (0.05 s window · updates every 2 s)", MatrixAnalysisMode.LIVE.value)
        self.analysis_mode.addItem("Timed average", MatrixAnalysisMode.TIMED_MEAN.value)
        mode_layout.addRow("Analysis mode", self.analysis_mode)
        layout.addWidget(mode_controls)
        self.processing = WaveformProcessingControls("Include Device Status gain", "correlation_matrix", self)
        layout.addWidget(self.processing)
        explanation = QLabel(
            "Pearson r is scale-invariant: positive Device Status gain is included when selected but normally does not change matrix values.",
            self,
        )
        explanation.setWordWrap(True)
        explanation.setObjectName("correlation_matrix_explanation")
        layout.addWidget(explanation)
        self.capture_controls = QWidget(self)
        self.capture_controls.setObjectName("correlation_capture_controls")
        capture_layout = QHBoxLayout(self.capture_controls)
        capture_layout.setContentsMargins(0, 0, 0, 0)
        self.capture_duration = QComboBox(self.capture_controls)
        self.capture_duration.setObjectName("correlation_capture_duration")
        self.capture_duration.setAccessibleName("Timed average duration")
        self.capture_duration.addItem("15 seconds", 15.0)
        self.capture_duration.addItem("30 seconds", 30.0)
        self.start_capture = QPushButton("Start mean capture", self.capture_controls)
        self.start_capture.setObjectName("correlation_start_capture")
        self.return_to_live = QPushButton("Return to live", self.capture_controls)
        self.return_to_live.setObjectName("correlation_return_live")
        self.return_to_live.setEnabled(False)
        capture_layout.addWidget(self.capture_duration)
        capture_layout.addWidget(self.start_capture)
        capture_layout.addWidget(self.return_to_live)
        self.capture_status = QLabel("Live matrix", self.capture_controls)
        self.capture_status.setObjectName("correlation_capture_status")
        capture_layout.addWidget(self.capture_status, 1)
        layout.addWidget(self.capture_controls)
        self.capture_controls.setVisible(False)
        self.plot = CorrelationMatrixPlot(self)
        layout.addWidget(self.plot, 1)
        self._samples = np.empty((0, ELEMENT_COUNT), dtype=np.float32)
        self._gain_multipliers = np.ones(ELEMENT_COUNT, dtype=np.float64)
        self._enabled_elements = (True,) * ELEMENT_COUNT
        self._polarity_signs = (1.0,) * ELEMENT_COUNT
        self._clock = clock
        self._capture_state = "live"
        self._capture_deadline = 0.0
        self._capture_duration_seconds = 0.0
        self._accumulator: CorrelationMatrixAccumulator | None = None
        self._latest_live_matrix = waveform_correlation_matrix(self._samples)
        self._capture_timer = QTimer(self)
        self._capture_timer.setInterval(100)
        self._capture_timer.timeout.connect(self._update_capture_clock)
        self.processing.changed.connect(self._refresh_matrix)
        self.analysis_mode.currentIndexChanged.connect(self._analysis_mode_changed)
        self.start_capture.clicked.connect(self._start_mean_capture)
        self.return_to_live.clicked.connect(self._return_to_live)

    @property
    def capture_state(self) -> str:
        return self._capture_state

    def analysis_mode_value(self) -> MatrixAnalysisMode:
        return validate_matrix_analysis_mode(self.analysis_mode.currentData())

    def set_samples(self, samples: np.ndarray) -> None:
        values = np.asarray(samples)
        if values.ndim != 2 or values.shape[1] != ELEMENT_COUNT:
            raise ValueError(f"raw samples must have shape (frames, {ELEMENT_COUNT})")
        self._samples = values
        self._refresh_matrix()

    def set_gain_multipliers(self, multipliers, *, refresh: bool = True) -> None:
        values = np.asarray(multipliers, dtype=np.float64)
        if values.shape != (ELEMENT_COUNT,) or not np.isfinite(values).all() or np.any(values <= 0.0):
            raise ValueError(f"element gain multipliers must contain {ELEMENT_COUNT} finite positive values")
        if self._capture_state == "capturing" and not np.array_equal(values, self._gain_multipliers):
            self._cancel_capture_for_status_change()
        self._gain_multipliers = values.copy()
        if refresh:
            self._refresh_matrix()

    def set_enabled_elements(self, enabled, *, refresh: bool = True) -> None:
        active = tuple(enabled)
        if len(active) != ELEMENT_COUNT or any(not isinstance(value, (bool, np.bool_)) for value in active):
            raise ValueError(f"enabled elements must contain {ELEMENT_COUNT} boolean values")
        checked = tuple(bool(value) for value in active)
        if self._capture_state == "capturing" and checked != self._enabled_elements:
            self._cancel_capture_for_status_change()
        self._enabled_elements = checked
        if refresh:
            self._refresh_matrix()

    def set_polarity_signs(self, signs, *, refresh: bool = True) -> None:
        values = tuple(float(value) for value in signs)
        if len(values) != ELEMENT_COUNT or any(value not in (-1.0, 1.0) for value in values):
            raise ValueError(f"polarity signs must contain {ELEMENT_COUNT} values of +1 or -1")
        if self._capture_state == "capturing" and values != self._polarity_signs:
            self._cancel_capture_for_status_change()
        self._polarity_signs = values
        if refresh:
            self._refresh_matrix()

    def _refresh_matrix(self) -> None:
        processed = self.processing.process(self._samples, self._polarity_signs)
        if self.processing.include_gain.isChecked():
            processed = processed * self._gain_multipliers[None, :]
        matrix = waveform_correlation_matrix(processed, enabled=self._enabled_elements)
        self._latest_live_matrix = matrix
        if self._capture_state == "capturing":
            self._accumulator.append(matrix)
            self._update_capture_clock()
        elif self._capture_state == "live":
            self._show_latest_live_matrix()

    def _show_latest_live_matrix(self) -> None:
        self.plot.set_matrix(self._latest_live_matrix, enabled=self._enabled_elements)

    def _start_mean_capture(self) -> None:
        if self._capture_state != "live" or self.analysis_mode_value() is not MatrixAnalysisMode.TIMED_MEAN:
            return
        self._capture_duration_seconds = float(self.capture_duration.currentData())
        self._capture_deadline = self._clock() + self._capture_duration_seconds
        self._accumulator = CorrelationMatrixAccumulator()
        self._accumulator.append(self._latest_live_matrix)
        self._capture_state = "capturing"
        self._set_capture_controls_locked(True)
        self.capture_active_changed.emit(True)
        self._capture_timer.start()
        self._update_capture_clock()

    def _analysis_mode_changed(self) -> None:
        timed = self.analysis_mode_value() is MatrixAnalysisMode.TIMED_MEAN
        self.capture_controls.setVisible(timed)
        if not timed and self._capture_state != "live":
            self._return_to_live()
            return
        if self._capture_state == "live":
            self.capture_status.setText("Timed average ready" if timed else "Live matrix")
        self._show_latest_live_matrix()

    def _update_capture_clock(self) -> None:
        if self._capture_state != "capturing":
            return
        remaining = max(0.0, self._capture_deadline - self._clock())
        if remaining <= 0.0:
            self._freeze_mean_capture()
            return
        self.capture_status.setText(f"Capturing mean · {remaining:.1f} s remaining · {self._accumulator.windows} windows")

    def _freeze_mean_capture(self) -> None:
        self._capture_timer.stop()
        self._capture_state = "frozen"
        mean = self._accumulator.mean()
        self.plot.set_matrix(mean, enabled=self._enabled_elements)
        self.capture_status.setText(f"Frozen mean · {self._capture_duration_seconds:.0f} s · {self._accumulator.windows} windows")
        self.return_to_live.setEnabled(True)

    def _return_to_live(self) -> None:
        self._capture_timer.stop()
        was_active = self._capture_state != "live"
        self._capture_state = "live"
        self._accumulator = None
        self._set_capture_controls_locked(False)
        self.analysis_mode.blockSignals(True)
        self.analysis_mode.setCurrentIndex(0)
        self.analysis_mode.blockSignals(False)
        self.capture_controls.setVisible(False)
        self.plot.set_matrix(self._latest_live_matrix, enabled=self._enabled_elements)
        self.capture_status.setText("Live matrix")
        if was_active:
            self.capture_active_changed.emit(False)

    def _cancel_capture_for_status_change(self) -> None:
        self._return_to_live()
        self.capture_status.setText("Live matrix · capture cancelled because Device Status changed")

    def _set_capture_controls_locked(self, locked: bool) -> None:
        self.processing.setEnabled(not locked)
        self.capture_duration.setEnabled(not locked)
        self.start_capture.setEnabled(not locked)
        self.return_to_live.setEnabled(locked)

    def reset_for_source_change(self) -> None:
        """Prevent a timed result from being presented as belonging to a new source."""
        if self._capture_state != "live" or self.analysis_mode_value() is not MatrixAnalysisMode.LIVE:
            self._return_to_live()
        self.capture_status.setText("Live matrix · source changed")


class RawWaveformToolsWindow(QMainWindow):
    """One current-source device selector above all waveform tool tabs."""

    def __init__(
        self,
        monitor,
        unit_identifiers=None,
        *,
        gain_source=None,
        enabled_source=None,
        polarity_source=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._dynamic_identifiers = unit_identifiers is None
        identifiers = tuple(getattr(monitor, "unit_identifiers", ()) if unit_identifiers is None else unit_identifiers)
        if not identifiers:
            raise ValueError("raw waveform tools require at least one source unit")
        self._monitor = monitor
        self._gain_source = gain_source or (lambda _unit_identifier: (1.0,) * ELEMENT_COUNT)
        self._enabled_source = enabled_source or (lambda _unit_identifier: (True,) * ELEMENT_COUNT)
        self._polarity_source = polarity_source or (lambda _unit_identifier: (1.0,) * ELEMENT_COUNT)
        self.setObjectName(WINDOW_NAME)
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(INITIAL_WINDOW_WIDTH, INITIAL_WINDOW_HEIGHT)

        body = QWidget(self)
        layout = QVBoxLayout(body)
        controls = QWidget(body)
        controls_layout = QFormLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        self.unit_selector = QComboBox(controls)
        self.unit_selector.setObjectName("raw_waveform_unit")
        for identifier in identifiers:
            self.unit_selector.addItem(f"HACAR {identifier}", identifier)
        controls_layout.addRow("Device", self.unit_selector)
        layout.addWidget(controls)
        self._source_status = getattr(
            monitor,
            "source_description",
            "Live native device samples · x-axis: sample index · no gain, polarity correction, filtering or estimator processing",
        )
        self._polarity_already_applied = bool(getattr(monitor, "polarity_already_applied", False))
        self.status = QLabel(self._status_text(), body)
        self.status.setObjectName("raw_waveform_status")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.tabs = QTabWidget(body)
        self.tabs.setObjectName("raw_waveform_tabs")
        self.all_waveforms = AllWaveformsTab(self.tabs)
        self.element_sum = ElementSumTab(self.tabs)
        self.correlation_matrix = CorrelationMatrixTab(self.tabs)
        self.correlation_matrix.capture_active_changed.connect(self.unit_selector.setDisabled)
        self.tabs.addTab(self.all_waveforms, "16 Waveforms")
        self.tabs.addTab(self.element_sum, "Element Sum")
        self.tabs.addTab(self.correlation_matrix, "16×16 Correlation")
        layout.addWidget(self.tabs, 1)
        self.scroll = QScrollArea(self)
        self.scroll.setObjectName("raw_waveform_scroll")
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setWidget(body)
        self.setCentralWidget(self.scroll)

        self._timer = QTimer(self)
        self._timer.setInterval(REFRESH_MILLISECONDS)
        self._timer.timeout.connect(self.refresh)
        self.unit_selector.currentIndexChanged.connect(self.refresh)

    def selected_unit(self) -> int:
        return int(self.unit_selector.currentData())

    def refresh(self) -> None:
        self._synchronise_source()
        unit_identifier = self.selected_unit()
        gain_multipliers = self._gain_source(unit_identifier)
        enabled_elements = self._enabled_source(unit_identifier)
        polarity_signs = self._polarity_source(unit_identifier)
        self.element_sum.set_gain_multipliers(gain_multipliers, refresh=False)
        self.element_sum.set_enabled_elements(enabled_elements, refresh=False)
        self.element_sum.set_polarity_signs(polarity_signs, refresh=False)
        self.correlation_matrix.set_gain_multipliers(gain_multipliers, refresh=False)
        self.correlation_matrix.set_enabled_elements(enabled_elements, refresh=False)
        self.correlation_matrix.set_polarity_signs(polarity_signs, refresh=False)
        snapshot = self._monitor.snapshot(unit_identifier)
        displayed = snapshot.samples[-DEFAULT_RETAINED_FRAMES:]
        self.all_waveforms.set_samples(displayed)
        self.element_sum.set_samples(displayed)
        self.correlation_matrix.set_samples(displayed)

    def _synchronise_source(self) -> None:
        current_identifiers = tuple(self.unit_selector.itemData(index) for index in range(self.unit_selector.count()))
        identifiers = tuple(getattr(self._monitor, "unit_identifiers", current_identifiers)) if self._dynamic_identifiers else current_identifiers
        source_description = getattr(self._monitor, "source_description", self._source_status)
        polarity_already_applied = bool(getattr(self._monitor, "polarity_already_applied", False))
        source_changed = (
            identifiers != current_identifiers or source_description != self._source_status or polarity_already_applied != self._polarity_already_applied
        )
        if identifiers != current_identifiers:
            selected = self.unit_selector.currentData()
            self.unit_selector.blockSignals(True)
            self.unit_selector.clear()
            for identifier in identifiers:
                self.unit_selector.addItem(f"HACAR {identifier}", identifier)
            if selected in identifiers:
                self.unit_selector.setCurrentIndex(identifiers.index(selected))
            self.unit_selector.blockSignals(False)
        if source_changed:
            self.correlation_matrix.reset_for_source_change()
        self._source_status = source_description
        self._polarity_already_applied = polarity_already_applied
        self.element_sum.processing.set_polarity_already_applied(polarity_already_applied)
        self.correlation_matrix.processing.set_polarity_already_applied(polarity_already_applied)
        self.status.setText(self._status_text())

    def _status_text(self) -> str:
        return f"{self._source_status} · {WINDOW_STATUS} · {REFRESH_STATUS} · {NORMALIZATION_STATUS}"

    def showEvent(self, event) -> None:  # noqa: N802 - Qt naming
        self._monitor.start()
        self._timer.start()
        self.refresh()
        super().showEvent(event)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt naming
        self._timer.stop()
        self._monitor.stop()
        super().closeEvent(event)


__all__ = [
    "AllWaveformsTab",
    "CorrelationMatrixTab",
    "ElementSumTab",
    "INITIAL_WINDOW_HEIGHT",
    "INITIAL_WINDOW_WIDTH",
    "RawWaveformToolsWindow",
    "WINDOW_NAME",
    "WINDOW_TITLE",
]
