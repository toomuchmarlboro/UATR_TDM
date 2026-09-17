"""Link and transport statistics for one telemetry unit."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from supersilence.features.device_status.domain.status_lines import describe_telemetry
from supersilence.features.device_status.ui.status_groups import (
    GroupedStatusPanel,
)

TELEMETRY_GROUPS = (
    ("Link", ("Endpoint", "State", "Valid-message age", "Error")),
    (
        "Traffic",
        ("Bytes received", "Valid messages", "Invalid messages", "Oversized frames"),
    ),
    (
        "Connections",
        ("Connection attempts", "Successful connections", "Disconnects"),
    ),
    ("Latest message", ("Latest raw fields",)),
)


class TelemetryStatisticsPanel(GroupedStatusPanel):
    """Every connection counter reported for one telemetry unit."""

    def __init__(
        self,
        unit_identifier: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(TELEMETRY_GROUPS, parent)
        self.unit_identifier = unit_identifier
        self.setObjectName(f"telemetry_statistics_unit_{unit_identifier}")

    def set_health(self, health) -> None:
        """Render one service snapshot without deciding what it means."""
        self.set_rows(describe_telemetry(health))
