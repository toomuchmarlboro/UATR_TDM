"""Where the telemetry links point, and a button to bring them up.

The console configures this in `File → Preferences → Connections` and never
asks again — which is right for a deployment, where the endpoints are settled
before anyone opens a status window. It is wrong on a bench, where the whole
activity is pointing the console at a unit that has just been plugged in and
watching whether it answers.

So this is a bench control, in the one place the answer is already on screen.
Editing an address here does not touch the stored preference: the preference
window remains the place a setting is *kept*, and this is the place a link is
*tried*. Two surfaces that both wrote the same setting would be the shape of
bug that makes an operator distrust both.

**THIS WIDGET STARTS NOTHING.** It emits what the operator asked for and shows
what came back. The window it sits in owns no services, and that invariant is
what keeps a closed status window from being able to stop the console
receiving — so the actual connect is done by whoever composed the application
and handed the window its services. See `DeviceStatusWindow`'s
`telemetry_connection` argument.

Only the GDAT2 addresses are editable. The IMU and altimeter sit one digit
along on most arrays, but "most" is not a rule this can apply for the operator:
the manufacturer's own numbering has been wrong before, and deriving two
addresses from a third would put this widget in the business of guessing where
hardware is. They carry over from the existing configuration unchanged.
"""
from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

ADDRESS_WIDTH = 120
PORT_WIDTH = 64

CONNECT_STYLE = (
    "QPushButton { background-color: #1b2b1b; color: #3fb950;"
    " border: 1px solid #2d5a2d; border-radius: 3px; padding: 4px 14px;"
    " font-weight: 600; }"
)
DISCONNECT_STYLE = (
    "QPushButton { background-color: #3a1d1d; color: #f85149;"
    " border: 1px solid #f85149; border-radius: 3px; padding: 4px 14px;"
    " font-weight: 600; }"
)


class TelemetryConnectionBar(QWidget):
    """One GDAT2 address per unit, a shared port, and a connect toggle."""

    #: (addresses by unit, port). Emitted on connect only.
    #:
    #: `object`, not `dict`: Qt marshals a declared `dict` through QVariantMap,
    #: which cannot hold a Python mapping keyed by int and fails the conversion
    #: at emit time — silently, with the slot simply never running.
    connect_requested = Signal(object, int)
    disconnect_requested = Signal()

    def __init__(
        self,
        addresses: Mapping[int, str],
        port: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("telemetry_connection_bar")
        self._connected = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(6)
        layout.addWidget(QLabel("aux_vcu", self))

        self._addresses: dict[int, QLineEdit] = {}
        for unit_identifier in sorted(addresses):
            layout.addWidget(QLabel(f"T{unit_identifier}", self))
            field = QLineEdit(addresses[unit_identifier], self)
            field.setObjectName(f"telemetry_address_unit_{unit_identifier}")
            field.setFixedWidth(ADDRESS_WIDTH)
            # Enter connects. On a bench the sequence is type-an-address then
            # try it, and reaching for the mouse in between is friction for no
            # reason.
            field.returnPressed.connect(self._toggle)
            self._addresses[unit_identifier] = field
            layout.addWidget(field)

        layout.addWidget(QLabel(":", self))
        self._port = QLineEdit(str(port), self)
        self._port.setObjectName("telemetry_port")
        self._port.setFixedWidth(PORT_WIDTH)
        self._port.returnPressed.connect(self._toggle)
        layout.addWidget(self._port)

        self._button = QPushButton("connect", self)
        self._button.setObjectName("telemetry_connect")
        self._button.clicked.connect(self._toggle)
        layout.addWidget(self._button)

        self._status = QLabel("", self)
        self._status.setObjectName("telemetry_connect_status")
        layout.addWidget(self._status, 1)

        self._show_state()

    # -- what the operator asked for --------------------------------------
    def _toggle(self) -> None:
        if self._connected:
            self.disconnect_requested.emit()
            return
        try:
            port = int(self._port.text().strip())
        except ValueError:
            self.set_error("port must be a number")
            return
        if not 1 <= port <= 65_535:
            self.set_error("port must be between 1 and 65535")
            return
        addresses = {
            unit_identifier: field.text().strip()
            for unit_identifier, field in self._addresses.items()
        }
        empty = [u for u, address in addresses.items() if not address]
        if empty:
            # Refused here rather than passed on: an empty address would be
            # rejected by the configuration with a message about validation,
            # which is a worse way to learn that a box is blank.
            self.set_error("address missing for "
                           + ", ".join(f"T{u}" for u in sorted(empty)))
            return
        self.connect_requested.emit(addresses, port)

    # -- what came back ----------------------------------------------------
    def set_connected(self, connected: bool) -> None:
        """Reflect the outcome. Called by whoever actually did the connecting.

        Not set optimistically on click: this bar says what the links ARE, and
        a button that latched on its own would claim a connection that the
        service may have refused.
        """
        self._connected = connected
        self._show_state()

    def set_error(self, message: str) -> None:
        self._status.setText(message)
        self._status.setStyleSheet("color: #f85149;")

    def set_message(self, message: str) -> None:
        self._status.setText(message)
        self._status.setStyleSheet("color: #768390;")

    def addresses(self) -> dict[int, str]:
        return {u: f.text().strip() for u, f in self._addresses.items()}

    def _show_state(self) -> None:
        self._button.setText("disconnect" if self._connected else "connect")
        self._button.setStyleSheet(
            DISCONNECT_STYLE if self._connected else CONNECT_STYLE)
        # The endpoint fields are locked while up. Editing an address that is
        # already connected would show one endpoint while the socket held
        # another, which is the disagreement this bar exists to remove.
        for field in (*self._addresses.values(), self._port):
            field.setReadOnly(self._connected)
        if self._connected:
            self.set_message("connected")
        else:
            self.set_message("")
