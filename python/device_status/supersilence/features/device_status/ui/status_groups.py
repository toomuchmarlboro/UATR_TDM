"""Device Status compatibility wrapper for the shared status-row layout."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget

from supersilence.features.device_status.domain.status_lines import is_alerting
from supersilence.shared.ui.status_groups import (
    GroupDefinition,
    GroupedStatusPanel as SharedGroupedStatusPanel,
    StatusGroupBox as SharedStatusGroupBox,
)


class StatusGroupBox(SharedStatusGroupBox):
    """A shared status group using Device Status alert semantics."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(title, parent, alerting=is_alerting)


class GroupedStatusPanel(SharedGroupedStatusPanel):
    """The shared layout using Device Status alert semantics."""

    def __init__(
        self,
        definitions: tuple[GroupDefinition, ...],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(definitions, parent, alerting=is_alerting)
