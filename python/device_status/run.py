#!/usr/bin/env python3
"""Open HACAR_dash's Device Status window, vendored whole into this repo.

    python run.py                      # all three tabs, live services
    python run.py --db my.sqlite       # a settings database of your own
    python run.py --no-services        # the bare window, no sockets opened

WHAT OPENS
==========
The window as the console builds it, with its three tabs:

    Buoys       the AFE pages - one sub-tab per unit, each with sixteen
                channel meters, gain faders, channel enable/polarity, and
                the 48 V phantom control
    Telemetry   decoded $GDAT2 fields per unit, link statistics, compass
                and horizon
    Pipeline    built only when a target provider is supplied, which is the
                console's direction-finding stack and is not vendored here

This is a REPLICA, not a reimplementation: every widget, signal and slot is
HACAR_dash's own source, copied by vendor.py with its package paths intact. The
composition below mirrors supersilence/app/main.py - same factories, same
configuration loaders, same argument order.

WHICH TABS APPEAR
=================
The window builds a tab only when the service behind it exists. That is its own
design and it is deliberate; its comment reads "a tab of ten dashes says a field
map is broken when the truth is that telemetry is switched off". So:

    Buoys       whenever either service reports unit_identifiers
    Telemetry   whenever a telemetry service is passed
    Pipeline    only with a target_provider - always absent here

TELEMETRY IS OFF UNTIL YOU ENABLE IT. default_telemetry_configuration() ships
with enabled=False, so a first run opens sockets to nothing. Addresses and the
enable flag live in the settings database; --db keeps them per-file so a
bench setup does not overwrite a deployment one.

WHERE THESE POINT
=================
HACAR_dash's defaults, not this repo's. Its acquisition sources and this array's
192.168.3.101-104 boards are configured independently, and nothing here rewrites
one to match the other - a window that silently retargeted the addresses stored
in its own database would be the least debuggable thing in either repo. Set them
in the database, or point --db at one already holding them.

UPDATING THE COPY
=================
supersilence/ is VENDORED - do not edit it here. Edit HACAR_dash and re-run:

    python vendor.py            # refresh
    python vendor.py --check    # fail if stale
"""

import argparse
import logging
import os
import sys
from dataclasses import replace

HERE = os.path.dirname(os.path.abspath(__file__))
# The vendored tree keeps HACAR_dash's package paths, so every
# `from supersilence.… import …` inside it is left exactly as written. This is
# the one line that makes that true.
sys.path.insert(0, HERE)

from PySide6.QtWidgets import QApplication                       # noqa: E402

from supersilence.features.device_status.ui.window import (      # noqa: E402
    DeviceStatusWindow,
)
from supersilence.infrastructure.acquisition.configuration import (  # noqa: E402
    load_acquisition_configuration,
)
from supersilence.infrastructure.acquisition.factory import (    # noqa: E402
    create_acquisition_service,
)
from supersilence.infrastructure.acquisition.gain_configuration import (  # noqa: E402
    load_channel_gains_db,
)
from supersilence.infrastructure.control.phantom_power import (  # noqa: E402
    PhantomPowerKeepalive,
)
from supersilence.infrastructure.database import migrations       # noqa: E402
from supersilence.infrastructure.database.connection import open_database  # noqa: E402
from supersilence.infrastructure.settings.repository import (    # noqa: E402
    SettingsRepository,
)
from supersilence.infrastructure.telemetry.configuration import (  # noqa: E402
    default_telemetry_configuration,
    load_telemetry_configuration,
)
from supersilence.infrastructure.telemetry.service import TelemetryService  # noqa: E402
from supersilence.shared.ui.theme import apply_base_font         # noqa: E402

logger = logging.getLogger("device_status")


class TelemetryConnection:
    """Owns starting and stopping telemetry, so the window does not have to.

    The window is handed this and calls it; it never touches the service
    itself. That keeps the invariant in the window's own docstring true - it
    owns no services and cannot, by being closed, stop the console receiving.

    Reconfiguring in place rather than building a second service is what makes
    a reconnect visible to everything already holding the first one. See
    TelemetryService.reconfigure.
    """

    def __init__(self, service, configuration):
        self._service = service
        self._configuration = configuration
        self._connected = False

    def start_if_enabled(self):
        """Bring the links up only if the stored configuration says to.

        A bench run that has never been configured opens with the links down
        and the addresses on screen waiting to be tried, rather than dialling
        four loopback addresses nobody asked for.
        """
        if not self._configuration.enabled:
            return False
        self._service.start()
        self._connected = True
        return True

    # -- what the bar shows on construction -------------------------------
    def addresses(self):
        return dict(self._configuration.sensor_addresses)

    def port(self):
        return self._configuration.port

    def connected(self):
        return self._connected

    # -- what the buttons do ----------------------------------------------
    def connect(self, addresses, port):
        """-> "" once the links are starting, else why they are not.

        A started link is not a connected one - the clients dial in their own
        threads and may be reconnecting for a while - so this reports that the
        attempt is under way. Whether a buoy actually answered shows up in the
        per-unit state on the page below, which is the honest place for it.
        """
        try:
            configuration = replace(
                self._configuration,
                enabled=True,
                sensor_addresses=dict(addresses),
                port=int(port),
            )
        except ValueError as error:
            # TelemetryConfiguration validates in __post_init__ - unroutable
            # address, port out of range, or an address colliding with one of
            # the IMU/altimeter roles. Its message already names which.
            return str(error)
        self._service.reconfigure(configuration)
        self._configuration = configuration
        self._service.start()
        self._connected = True
        logger.info("telemetry connecting to %s:%d",
                    ", ".join(sorted(configuration.sensor_addresses.values())),
                    configuration.port)
        return ""

    def disconnect(self):
        self._service.stop()
        self._connected = False
        return ""


def build_services(settings):
    """-> (acquisition_service, telemetry_service, set_phantom_power).

    Mirrors the composition in supersilence/app/main.py. Kept in one function
    so the window is constructed the same way whether it is run from here or
    lifted into something larger later.
    """
    acquisition_configuration = load_acquisition_configuration(settings)
    initial_gains_db = {
        unit: load_channel_gains_db(settings, unit)
        for unit in acquisition_configuration.source_addresses
    }
    acquisition_service = create_acquisition_service(
        acquisition_configuration, initial_gains_db=initial_gains_db)

    try:
        telemetry_configuration = load_telemetry_configuration(settings)
    except ValueError as error:
        # Same handling as the console: a stored configuration that no longer
        # validates must not stop the window opening, because the window is
        # where you would go to look at why.
        logger.error("stored telemetry configuration is invalid; telemetry "
                     "remains disabled: %s", error)
        telemetry_configuration = default_telemetry_configuration()
    telemetry_service = TelemetryService(telemetry_configuration)

    # The 48 V path. A keepalive rather than a single datagram because the
    # firmware drops phantom power on its own if it stops hearing a
    # flags-carrying packet - see the module's docstring, and ctrl.phantom_reason
    # in this repo, which names that watchdog as a distinct cause.
    keepalive = PhantomPowerKeepalive(acquisition_configuration.source_addresses)

    def set_phantom_power(unit_identifier, enabled):
        if unit_identifier not in acquisition_configuration.source_addresses:
            logger.warning("no configured address for unit %s; phantom power "
                           "command dropped", unit_identifier)
            return
        keepalive.request(unit_identifier, enabled)

    connection = TelemetryConnection(telemetry_service, telemetry_configuration)
    connection.start_if_enabled()

    return acquisition_service, telemetry_service, set_phantom_power, connection


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", metavar="PATH", default=None,
                    help="settings database (default: HACAR_dash's own)")
    ap.add_argument("--no-services", action="store_true",
                    help="open the bare window without starting acquisition "
                         "or telemetry - opens no sockets")
    ap.add_argument("--refresh-ms", type=int, default=200,
                    help="how often the window re-reads its services")
    a = ap.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    app = QApplication(sys.argv)
    apply_base_font(app)

    settings = acquisition = telemetry = phantom = link = None
    if not a.no_services:
        database = open_database(a.db)
        # open_database only opens; the schema is a separate step, exactly as
        # in main.py. A fresh --db file has no settings table at all until
        # this runs.
        version = migrations.apply_migrations(database)
        logger.info("settings database at schema version %d", version)
        settings = SettingsRepository(database)
        acquisition, telemetry, phantom, link = build_services(settings)

    window = DeviceStatusWindow(
        acquisition,
        telemetry,
        settings=settings,
        phantom_power_control=phantom,
        telemetry_connection=link,
        refresh_interval_ms=a.refresh_ms,
    )
    window.show()
    try:
        return app.exec()
    finally:
        # Both services own threads and sockets. Leaving them running past the
        # window turns a closed GUI into a process that is still receiving.
        for service in (acquisition, telemetry):
            stop = getattr(service, "stop", None) or getattr(service, "close", None)
            if stop is not None:
                try:
                    stop()
                except Exception:               # noqa: BLE001 - shutdown path
                    logger.exception("failed to stop %r", service)


if __name__ == "__main__":
    sys.exit(main())
