"""Sixteen channel gain faders for one unit.

A live console control, not a settings form: each fader applies the moment it
is moved, there is no Save or Cancel, and the panel never re-reads its own
values off a timer — that would fight the operator mid-drag. It only ever moves
in two directions: out, when the window pushes a freshly loaded, freshly
reset, or freshly balanced set of values in; and out to the window's
apply-and-persist method, on every edit.

Drawn as vertical faders, sixteen side by side, rather than a grid of number
boxes: this is a mixing-console control, and an operator who has used one
reaches for the shape immediately. Each fader shows its own current value as a
number above it — read there, not estimated from where the handle sits — and
the numeric range is quantized to the same 0.5 dB step a fader detent would
give, not free-typed decimals. No tick marks down the side of the track: on
one fader a tick rule is a helpful ruler, but on sixteen side by side it is
sixteen ladders of dashes competing with the sixteen numbers that already say
the same thing more precisely. The value label is muted at 0 dB and lit only
once a channel has actually been touched, so a glance at the row shows which
channels were adjusted rather than shouting sixteen numbers at once.

Each fader also carries the channel's **in-array** checkbox, and it lives here
rather than on the meter strip for one reason: this is the panel of controls,
and the meters above are the reading. Switching a channel out removes it from
the direction estimators — see `infrastructure/acquisition/channel_enable.py`
for what that means and why it is not a mute — so the fader below it is
disabled at the same time: gain on a channel no estimator reads is a control
that does nothing.

Below that sits the channel's **inversion** checkbox, labelled ``INV`` and lit
amber when set. It says the channel arrives multiplied by minus one,
which is what a cable with pin 2 and pin 3 swapped delivers, and it exists
because three of unit 1's channels were measured to be exactly that — see
`infrastructure/acquisition/channel_polarity.py`. It is a fault being recorded
rather than a preference being expressed, which is why it is coloured like a
warning and not like an adjustment, and why it gets its own row instead of
crowding the number: sixteen more controls beside the checkbox would widen the
strip, and width is what this panel is short of.

Deliberately separate from `ChannelMeterStrip` above it. The meters are metered
before decimation, so this panel's gain is invisible on them by design — see the
module docstring in `infrastructure/acquisition/gain.py`. The current gain is
read as the number above each fader, not as a moving bar.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from supersilence.features.device_status.domain.linked_gain import (
    GainRange,
    linked_gains_db,
)
from supersilence.infrastructure.acquisition.gain import (
    CHANNEL_COUNT,
    DEFAULT_GAIN_DB,
    MAXIMUM_GAIN_DB,
    MINIMUM_GAIN_DB,
)
from supersilence.shared.ui.theme import DENSE_LABEL_POINT_SIZE

#: What the acquisition path allows, handed to the link arithmetic rather than
#: reached for by it: the range belongs to acquisition, and the domain module
#: that moves the faders together is not allowed to know acquisition exists.
GAIN_RANGE = GainRange(CHANNEL_COUNT, MINIMUM_GAIN_DB, MAXIMUM_GAIN_DB)

GAIN_STEP_DB = 0.5

#: How tall the fader track is. Short enough that sixteen of them plus their
#: meters fit one unit's tab without a second scroll region, tall enough that a
#: 0.5 dB step is a distinguishable handle position rather than a pixel.
#:
#: Was 130, then 126 when the in-array checkbox replaced the plain
#: channel-number label, and 106 now that the polarity row sits below it. The
#: Device Status window is composed to exactly 720 px and the track is what pays
#: for anything added to the fader, because the alternative is a window that
#: grows every time a control is added. 0.5 dB is still most of a pixel per step.
FADER_HEIGHT = 106

#: Value-label colour when a fader sits at 0 dB — dim, so an untouched channel
#: does not compete for attention with one the operator actually adjusted.
NEUTRAL_LABEL_COLOUR = "#6b7280"
#: Value-label colour once a channel has been moved off 0 dB.
ADJUSTED_LABEL_COLOUR = "#58a6ff"

#: An inverted channel is a fault being compensated for, not a preference, so it
#: is coloured like a warning rather than like an adjustment.
INVERTED_LABEL_COLOUR = "#e0a458"

#: A hard horizontal contract is necessary because this control repeats sixteen
#: times. It is nearly twice the old glyph button's width while still letting
#: the complete panel fit the supported 700 px Device Status window.
POLARITY_CHECKBOX_WIDTH = 31


def _to_tick(value_db: float) -> int:
    return round(value_db / GAIN_STEP_DB)


def _to_db(tick: int) -> float:
    return tick * GAIN_STEP_DB


class ChannelFader(QWidget):
    """One channel's vertical gain slider, with its value shown above it."""

    valueChanged = Signal(float)
    enabledChanged = Signal(bool)
    #: Carries "as delivered", not "inverted" — see `_on_polarity_toggled`.
    polarityChanged = Signal(bool)

    def __init__(self, unit_identifier: int, channel_index: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._channel_index = channel_index
        self._value_db = DEFAULT_GAIN_DB

        self.value_label = QLabel(self._format(DEFAULT_GAIN_DB), self)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_font = self.value_label.font()
        value_font.setPointSize(DENSE_LABEL_POINT_SIZE)
        self.value_label.setFont(value_font)
        self._style_value_label()

        self.slider = QSlider(Qt.Orientation.Vertical, self)
        self.slider.setObjectName(f"channel_gain_slider_{unit_identifier}_{channel_index}")
        self.slider.setMinimumHeight(FADER_HEIGHT)
        self.slider.setFixedWidth(28)
        self.slider.setRange(_to_tick(MINIMUM_GAIN_DB), _to_tick(MAXIMUM_GAIN_DB))
        self.slider.setSingleStep(1)
        self.slider.setPageStep(4)
        # A vertical QSlider already puts its minimum at the bottom and its
        # maximum at the top — a real fader's own orientation — so nothing here
        # needs `invertedAppearance`.
        self.slider.setValue(_to_tick(DEFAULT_GAIN_DB))
        # No ticks: see the module docstring. Sixteen ladders of dashes read as
        # clutter next to sixteen numbers that already say the same thing.
        self.slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.slider.valueChanged.connect(self._on_slider_changed)

        # The channel number *is* the checkbox. Two controls stacked would
        # have cost the fader strip an extra row, and the Device Status window
        # is already composed to exactly 720 px; more to the point, a number
        # and a box that always mean the same channel are one control drawn
        # twice.
        self.enabled_box = QCheckBox(str(channel_index + 1), self)
        self.enabled_box.setObjectName(f"channel_enabled_{unit_identifier}_{channel_index}")
        # Tight indicator-to-number spacing: sixteen faders side by side set
        # the panel's minimum width, and Qt's default 6 px gap on each of them
        # is 96 px of the window.
        self.enabled_box.setStyleSheet(f"QCheckBox {{ color: {NEUTRAL_LABEL_COLOUR}; spacing: 2px; }}")
        self.enabled_box.setChecked(True)
        self.enabled_box.setToolTip(
            f"Channel {channel_index + 1} in unit {unit_identifier}'s array. "
            "Clear it for a channel whose hydrophone, cable or preamplifier has "
            "failed: it is removed from the direction estimators entirely, not "
            "muted. Its meter, its recording and the monitor speaker keep it, so "
            "a channel that comes back can still be seen and heard."
        )
        self.enabled_box.setAccessibleName(f"Unit {unit_identifier} channel {channel_index + 1} in array")
        self.enabled_box.toggled.connect(self._on_enabled_toggled)
        enabled_row = QWidget(self)
        enabled_layout = QHBoxLayout(enabled_row)
        enabled_layout.setContentsMargins(0, 0, 0, 0)
        enabled_layout.addStretch(1)
        enabled_layout.addWidget(self.enabled_box)
        enabled_layout.addStretch(1)
        enabled_row.setToolTip(self.enabled_box.toolTip())

        # Its own row rather than beside the number, because the fader strip is
        # what sets this panel's minimum width — the module docstring records
        # that repeating "dB" sixteen times cost a 900 px window — and sixteen
        # more controls side by side would widen it again. One short row costs
        # height, which this panel has more of to spend.
        self.polarity_checkbox = QCheckBox("INV", self)
        self.polarity_checkbox.setFixedWidth(POLARITY_CHECKBOX_WIDTH)
        self.polarity_checkbox.setObjectName(f"channel_polarity_{unit_identifier}_{channel_index}")
        self.polarity_checkbox.setToolTip(
            "Checked = INVERTED. Unchecked = normal/as delivered. "
            f"Channel {channel_index + 1} of unit {unit_identifier} arrives "
            "inverted — its samples are multiplied by minus one, which is what a "
            "cable with pin 2 and pin 3 swapped produces. Set it only for a "
            "channel measured to be wired that way: it corrects the direction "
            "estimators, and setting it on a correctly wired channel breaks that "
            "channel exactly as thoroughly. The recording is unaffected; it is "
            "written before this is applied."
        )
        self.polarity_checkbox.setAccessibleName(f"Unit {unit_identifier} channel {channel_index + 1} arrives inverted")
        self.polarity_checkbox.setAccessibleDescription("Checked means this channel arrives inverted; unchecked means normal.")
        self.polarity_checkbox.toggled.connect(self._on_polarity_toggled)
        self._style_polarity_checkbox()
        polarity_row = QWidget(self)
        polarity_layout = QHBoxLayout(polarity_row)
        polarity_layout.setContentsMargins(0, 0, 0, 0)
        polarity_layout.addStretch(1)
        polarity_layout.addWidget(self.polarity_checkbox)
        polarity_layout.addStretch(1)
        polarity_row.setToolTip(self.polarity_checkbox.toolTip())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 4, 3, 4)
        layout.setSpacing(4)
        layout.addWidget(self.value_label)
        layout.addWidget(self.slider, 1, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(enabled_row)
        layout.addWidget(polarity_row)

    def _on_slider_changed(self, tick: int) -> None:
        self._value_db = _to_db(tick)
        self.value_label.setText(self._format(self._value_db))
        self._style_value_label()
        self.valueChanged.emit(self._value_db)

    def _on_enabled_toggled(self, enabled: bool) -> None:
        self.slider.setEnabled(enabled)
        self.enabledChanged.emit(bool(enabled))

    def _on_polarity_toggled(self, inverted: bool) -> None:
        self._style_polarity_checkbox()
        # Emitted as "as delivered", which is what the store and the settings
        # hold. The checkbox reads the other way round because what an operator
        # ticks is the fault, not its absence.
        self.polarityChanged.emit(not bool(inverted))

    def _style_polarity_checkbox(self) -> None:
        inverted = self.polarity_checkbox.isChecked()
        colour = INVERTED_LABEL_COLOUR if inverted else NEUTRAL_LABEL_COLOUR
        weight = "700" if inverted else "400"
        background = "#3a2b16" if inverted else "transparent"
        self.polarity_checkbox.setStyleSheet(
            "QCheckBox { "
            f"color: {colour}; font-size: 7pt; font-weight: {weight}; spacing: 0; "
            f"background-color: {background}; border: none; "
            "border-radius: 2px; padding: 0; "
            "} "
            "QCheckBox::indicator:unchecked { "
            f"border: 1px solid {NEUTRAL_LABEL_COLOUR}; background-color: #ffffff; "
            "}"
        )

    def isChannelAsDelivered(self) -> bool:  # noqa: N802 - mirrors Qt's own naming
        return not self.polarity_checkbox.isChecked()

    def setChannelAsDelivered(self, as_delivered: bool) -> None:  # noqa: N802 - Qt naming
        """Push a polarity into the checkbox without emitting `polarityChanged`."""
        self.polarity_checkbox.blockSignals(True)
        self.polarity_checkbox.setChecked(not bool(as_delivered))
        self.polarity_checkbox.blockSignals(False)
        self._style_polarity_checkbox()

    def isChannelEnabled(self) -> bool:  # noqa: N802 - mirrors Qt's own naming
        return self.enabled_box.isChecked()

    def setChannelEnabled(self, enabled: bool) -> None:  # noqa: N802 - Qt naming
        """Push a selection into the checkbox without emitting `enabledChanged`."""
        self.enabled_box.blockSignals(True)
        self.enabled_box.setChecked(bool(enabled))
        self.enabled_box.blockSignals(False)
        self.slider.setEnabled(bool(enabled))

    def _style_value_label(self) -> None:
        adjusted = self._value_db != DEFAULT_GAIN_DB
        colour = ADJUSTED_LABEL_COLOUR if adjusted else NEUTRAL_LABEL_COLOUR
        weight = "600" if adjusted else "400"
        self.value_label.setStyleSheet(f"color: {colour}; font-weight: {weight};")

    def value(self) -> float:
        return self._value_db

    def setValue(self, value_db: float) -> None:  # noqa: N802 - mirrors Qt's own setValue
        self.slider.setValue(_to_tick(value_db))

    def minimum(self) -> float:
        return MINIMUM_GAIN_DB

    def maximum(self) -> float:
        return MAXIMUM_GAIN_DB

    @staticmethod
    def _format(value_db: float) -> str:
        # The group heading owns the shared unit. Repeating "dB" sixteen times
        # made the fader strip impose a 900 px window minimum.
        return f"{value_db:+.1f}"


def ask_twice(parent: QWidget | None, title: str, first_question: str, second_question: str) -> bool:
    """Two separate dialogs, both of which must be accepted.

    Not a nagging habit: wiping a balance is the one action on this panel that
    destroys measurement work and cannot be undone from here, and a single
    dialog in the path of a mis-aimed click is dismissed by the same reflex
    that made the click. The second dialog asks a differently worded question
    with the consequence spelled out, so answering it is a second decision
    rather than a second click in the same place. Default button on both is No.
    """
    for question in (first_question, second_question):
        answer = QMessageBox.warning(
            parent,
            title,
            question,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return False
    return True


class ChannelGainPanel(QWidget):
    """One unit's sixteen channel gain faders, in decibels."""

    #: Emitted on every edit the operator makes — a drag, a reset, or an
    #: applied balance. Not emitted by `set_gains_db`, which is how a freshly
    #: loaded set of values reaches the faders without looping back through
    #: the window as sixteen redundant writes.
    gain_changed = Signal(int, int, float)
    #: The owner (the window) holds the current channel levels this panel
    #: deliberately does not; see the module docstring. Requesting rather than
    #: computing keeps that separation.
    balance_requested = Signal()
    #: Emitted when the operator switches a channel into or out of the array.
    #: Not emitted by `set_channels_enabled`, for the same reason
    #: `gain_changed` is not emitted by `set_gains_db`.
    enabled_changed = Signal(int, int, bool)
    #: Emitted when the operator marks a channel as arriving inverted, or stops
    #: doing so. Carries "as delivered". Not emitted by `set_channel_polarity`.
    polarity_changed = Signal(int, int, bool)
    #: Asked for by the two file buttons. The panel holds no path, opens no
    #: dialog and touches no disk: the window owns the file system and the
    #: acquisition service, exactly as it owns the levels the balance is
    #: computed from. Both carry the unit identifier so one handler serves
    #: every page.
    export_requested = Signal(int)
    import_requested = Signal(int)

    def __init__(self, unit_identifier: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(f"channel_gain_panel_{unit_identifier}")
        self.unit_identifier = unit_identifier
        #: How the two destructive buttons ask. Replaceable so a test can
        #: answer without a modal dialog, and so a caller that already has the
        #: operator's decision can supply it.
        self.confirm_action: Callable[[str, str, str], bool] = lambda title, first, second: ask_twice(self, title, first, second)

        group = QGroupBox("Channel gain (dB)", self)
        group.setToolTip(
            "Software correction after acquisition, from -60 to +60 dB. It does not change ADC gain; large positive values amplify noise as well as signal."
        )
        strip = QHBoxLayout()
        strip.setSpacing(2)
        self._boxes: list[ChannelFader] = []
        for channel_index in range(CHANNEL_COUNT):
            fader = ChannelFader(unit_identifier, channel_index, group)
            fader.setObjectName(f"channel_gain_{unit_identifier}_{channel_index}")
            fader.valueChanged.connect(self._make_handler(channel_index))
            fader.enabledChanged.connect(self._make_enabled_handler(channel_index))
            fader.polarityChanged.connect(self._make_polarity_handler(channel_index))
            strip.addWidget(fader)
            self._boxes.append(fader)
        self._known_gains_db = list(self.gains_db())
        self._applying_bulk_gains = False
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(10, 14, 10, 10)
        group_layout.setSpacing(10)
        group_layout.addLayout(strip)

        self.balance_button = QPushButton("Balance channels", group)
        self.balance_button.setObjectName(f"balance_channel_gain_{unit_identifier}")
        self.balance_button.setToolTip(
            "Calibration: balances eligible ON channels against their median "
            "raw level right now. OFF, silent and clipping channels are "
            "excluded from the calculation and left unchanged."
        )
        self.balance_button.clicked.connect(self._confirm_then_balance)
        self.reset_button = QPushButton("Reset all to 0 dB", group)
        self.reset_button.setObjectName(f"reset_channel_gain_{unit_identifier}")
        self.reset_button.setToolTip("Returns every channel to 0 dB, discarding the current balance. Asks twice; there is no undo.")
        self.reset_button.clicked.connect(self._confirm_then_reset)
        self.export_button = QPushButton("Export gains\u2026", group)
        self.export_button.setObjectName(f"export_channel_gain_{unit_identifier}")
        self.export_button.setToolTip("Write this buoy's sixteen gains to a file, so a balance can be kept, copied to another console, or brought back later.")
        self.export_button.clicked.connect(lambda: self.export_requested.emit(self.unit_identifier))
        self.import_button = QPushButton("Import gains\u2026", group)
        self.import_button.setObjectName(f"import_channel_gain_{unit_identifier}")
        self.import_button.setToolTip("Load sixteen gains from a previously exported file, replacing what this buoy is using now.")
        self.import_button.clicked.connect(lambda: self.import_requested.emit(self.unit_identifier))
        self.link_gains_checkbox = QCheckBox("Link gains", group)
        self.link_gains_checkbox.setObjectName(f"link_channel_gains_{unit_identifier}")
        self.link_gains_checkbox.setToolTip(
            "Move all sixteen gains on this buoy by the same amount when any "
            "one fader is moved. Existing differences are preserved. The "
            "largest or smallest channel limits the shared movement at the "
            "gain range boundary. Balance and Reset all remain separate bulk "
            "actions."
        )
        self.link_gains_checkbox.setAccessibleName(f"Link all channel gains for unit {unit_identifier}")
        self.link_gains_checkbox.setAccessibleDescription(
            "When checked, moving one channel gain moves all sixteen channels on this unit by the same decibel amount."
        )
        actions = QWidget(group)
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)
        actions_layout.addWidget(self.link_gains_checkbox)
        actions_layout.addStretch(1)
        actions_layout.addWidget(self.export_button)
        actions_layout.addWidget(self.import_button)
        actions_layout.addWidget(self.balance_button)
        actions_layout.addWidget(self.reset_button)
        group_layout.addWidget(actions)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(group)

    def _make_handler(self, channel_index: int):
        def handler(value: float) -> None:
            requested = float(value)
            if self._applying_bulk_gains or not self.link_gains_checkbox.isChecked():
                self._known_gains_db[channel_index] = requested
                self.gain_changed.emit(self.unit_identifier, channel_index, requested)
                return

            previous = tuple(self._known_gains_db)
            linked = linked_gains_db(previous, channel_index, requested, GAIN_RANGE)
            changed = [index for index, (before, after) in enumerate(zip(previous, linked)) if before != after]
            for fader, linked_value in zip(self._boxes, linked):
                signals_were_blocked = fader.blockSignals(True)
                fader.setValue(linked_value)
                fader.blockSignals(signals_were_blocked)
            self._known_gains_db[:] = linked
            for changed_index in changed:
                self.gain_changed.emit(
                    self.unit_identifier,
                    changed_index,
                    linked[changed_index],
                )

        return handler

    def _make_enabled_handler(self, channel_index: int):
        def handler(enabled: bool) -> None:
            self.enabled_changed.emit(self.unit_identifier, channel_index, bool(enabled))

        return handler

    def _make_polarity_handler(self, channel_index: int):
        def handler(as_delivered: bool) -> None:
            self.polarity_changed.emit(self.unit_identifier, channel_index, bool(as_delivered))

        return handler

    def channels_enabled(self) -> tuple[bool, ...]:
        return tuple(fader.isChannelEnabled() for fader in self._boxes)

    def channel_polarity(self) -> tuple[bool, ...]:
        """One flag per channel: whether it arrives the way it was delivered."""
        return tuple(fader.isChannelAsDelivered() for fader in self._boxes)

    def set_channel_polarity(self, polarity: tuple[bool, ...]) -> None:
        """Push a polarity into the checkboxes without emitting anything."""
        for fader, value in zip(self._boxes, polarity):
            fader.setChannelAsDelivered(value)

    def set_channels_enabled(self, enabled: tuple[bool, ...]) -> None:
        """Push a selection into the checkboxes without emitting anything."""
        for fader, value in zip(self._boxes, enabled):
            fader.setChannelEnabled(value)

    def gains_db(self) -> tuple[float, ...]:
        return tuple(fader.value() for fader in self._boxes)

    def set_gains_db(self, gains_db: tuple[float, ...]) -> None:
        """Push values into the faders without emitting `gain_changed`."""
        for fader, value in zip(self._boxes, gains_db):
            fader.blockSignals(True)
            fader.setValue(value)
            fader.blockSignals(False)
        self._known_gains_db[:] = self.gains_db()

    def apply_gains_db(self, gains_db: tuple[float, ...]) -> None:
        """Push computed values into the faders, applying each like a manual edit.

        Unlike `set_gains_db`, signals are not blocked: every channel whose
        value actually changes emits `gain_changed` exactly as a drag would, so
        the window's existing write-through-and-persist path handles a
        computed balance with no separate code path to keep in sync.
        """
        self._applying_bulk_gains = True
        try:
            for fader, value in zip(self._boxes, gains_db):
                fader.setValue(value)
        finally:
            self._applying_bulk_gains = False

    def _confirm_then_reset(self) -> None:
        """Ask twice, then flatten every gain on this unit to 0 dB."""
        adjusted = sum(1 for value in self.gains_db() if value != DEFAULT_GAIN_DB)
        if adjusted == 0:
            # Nothing to destroy: every channel is already at 0 dB, so there is
            # no calibration for the dialogs to protect.
            self.reset()
            return
        if not self.confirm_action(
            f"Reset unit {self.unit_identifier} channel gains",
            f"Reset all {CHANNEL_COUNT} channel gains on unit {self.unit_identifier} to 0 dB?\n\n{adjusted} channel(s) are currently adjusted.",
            "This discards the current balance for this unit and cannot be undone. Export the gains first if you want them back. Reset now?",
        ):
            return
        self.reset()

    def _confirm_then_balance(self) -> None:
        """Ask twice, then ask the window to compute and apply a balance."""
        if not self.confirm_action(
            f"Balance unit {self.unit_identifier} channels",
            f"Balance eligible ON channels on unit {self.unit_identifier} against their median raw level right now?\n\n"
            "OFF, silent and clipping channels are excluded and left unchanged.",
            "This overwrites the gains this unit is using and cannot be undone. Export the gains first if you want them back. Balance now?",
        ):
            return
        self.balance_requested.emit()

    def confirm_import(self, source_name: str) -> bool:
        """Ask twice before a file replaces this unit's gains.

        An import destroys exactly what a reset does, so it is protected the
        same way. The window asks rather than doing it here because only the
        window knows which file the operator chose.
        """
        return self.confirm_action(
            f"Import unit {self.unit_identifier} channel gains",
            f"Replace unit {self.unit_identifier}'s {CHANNEL_COUNT} channel gains with the ones in {source_name}?",
            "This discards the gains this unit is using now and cannot be undone. Export them first if you want them back. Import now?",
        )

    def reset(self) -> None:
        """Set every channel to 0 dB, applying each one like any other edit.

        Gain only. A channel switched out of the array stays out: which
        hydrophones are dead is a statement about the hardware, and it is not
        something a gain reset has any business changing.
        """
        self.apply_gains_db((DEFAULT_GAIN_DB,) * CHANNEL_COUNT)
