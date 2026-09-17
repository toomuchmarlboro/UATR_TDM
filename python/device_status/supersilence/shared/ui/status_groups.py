"""Compact semantic groups for feature-owned read-only status rows."""
from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QSizePolicy,
    QWidget,
)

ALERT_COLOUR = "#f85149"
DIM_COLOUR = "#6b7280"

StatusRows = tuple[tuple[str, str], ...]
GroupDefinition = tuple[str, tuple[str, ...]]
AlertPredicate = Callable[[str, str], bool]


def never_alert(_caption: str, _value: str) -> bool:
    """Neutral default; each feature decides which of its values are faults."""
    return False


class StatusGroupBox(QGroupBox):
    """One semantic group of caption/value rows."""

    def __init__(
        self,
        title: str,
        parent: QWidget | None = None,
        *,
        alerting: AlertPredicate = never_alert,
    ) -> None:
        super().__init__(title, parent)
        self._alerting = alerting
        self._grid = QGridLayout(self)
        self._grid.setColumnStretch(0, 0)
        self._grid.setColumnStretch(1, 1)
        self._caption_labels: dict[str, QLabel] = {}
        self.rows: dict[str, QLabel] = {}

    def set_rows(self, described: StatusRows) -> None:
        """Reconcile this group with one complete current description."""
        wanted = {caption for caption, _value in described}
        for caption in tuple(self.rows):
            if caption in wanted:
                continue
            caption_label = self._caption_labels.pop(caption)
            value_label = self.rows.pop(caption)
            self._grid.removeWidget(caption_label)
            self._grid.removeWidget(value_label)
            caption_label.deleteLater()
            value_label.deleteLater()

        for row, (caption, value) in enumerate(described):
            label = self.rows.get(caption)
            if label is None:
                caption_label = QLabel(caption, self)
                caption_label.setWordWrap(True)
                caption_label.setMinimumWidth(0)
                caption_label.setStyleSheet(f"color: {DIM_COLOUR};")
                label = QLabel(self)
                label.setWordWrap(True)
                label.setMinimumWidth(0)
                label.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Preferred,
                )
                label.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                )
                self._grid.addWidget(caption_label, row, 0)
                self._grid.addWidget(label, row, 1)
                self._caption_labels[caption] = caption_label
                self.rows[caption] = label
            else:
                self._grid.addWidget(self._caption_labels[caption], row, 0)
                self._grid.addWidget(label, row, 1)
            label.setText(value)
            label.setStyleSheet(
                f"color: {ALERT_COLOUR}; font-weight: bold;"
                if self._alerting(caption, value)
                else ""
            )


class GroupedStatusPanel(QWidget):
    """Named status groups arranged two across, in reading order."""

    def __init__(
        self,
        definitions: Sequence[GroupDefinition],
        parent: QWidget | None = None,
        *,
        alerting: AlertPredicate = never_alert,
    ) -> None:
        super().__init__(parent)
        self._grid = QGridLayout(self)
        self._grid.setColumnStretch(0, 1)
        self._grid.setColumnStretch(1, 1)
        self._groups: dict[str, StatusGroupBox] = {}
        self._group_order: list[str] = []
        self._fixed_group_order: list[str] = []
        self._caption_groups: dict[str, str] = {}
        self.rows: dict[str, QLabel] = {}

        for index, (title, captions) in enumerate(definitions):
            if title in self._groups:
                raise ValueError(f"duplicate status group {title!r}")
            group = StatusGroupBox(title, self, alerting=alerting)
            group.setObjectName(f"status_group_{_slug(title)}")
            self._grid.addWidget(group, index // 2, index % 2)
            self._groups[title] = group
            self._group_order.append(title)
            if captions:
                self._fixed_group_order.append(title)
            for caption in captions:
                previous = self._caption_groups.get(caption)
                if previous is not None:
                    raise ValueError(
                        f"status row {caption!r} belongs to both {previous!r} "
                        f"and {title!r}"
                    )
                self._caption_groups[caption] = title
        self._grid.setRowStretch((len(definitions) + 1) // 2, 1)

    def set_rows(self, described: StatusRows) -> None:
        """Partition fixed rows into their declared semantic groups."""
        grouped: dict[str, list[tuple[str, str]]] = {
            title: [] for title in self._fixed_group_order
        }
        for caption, value in described:
            try:
                title = self._caption_groups[caption]
            except KeyError as error:
                raise KeyError(f"status row {caption!r} has no group") from error
            grouped[title].append((caption, value))
        for title, rows in grouped.items():
            self.set_group_rows(title, tuple(rows))

    def set_group_rows(self, title: str, described: StatusRows) -> None:
        group = self._groups[title]
        group.set_rows(described)
        self.rows.clear()
        for group_title in self._group_order:
            self.rows.update(self._groups[group_title].rows)

    def group(self, title: str) -> StatusGroupBox:
        return self._groups[title]

    def group_titles(self) -> tuple[str, ...]:
        return tuple(self._group_order)

    def group_for(self, caption: str) -> str:
        return self._caption_groups[caption]

    def value(self, caption: str) -> str:
        return self.rows[caption].text()


def _slug(text: str) -> str:
    return "_".join(text.lower().split())
