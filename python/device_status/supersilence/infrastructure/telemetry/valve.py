"""The valve actuator command: ``$RMCMD``, the one thing this console sends a buoy.

Everything else under ``infrastructure/telemetry/`` reads. This writes, and what
it writes turns a motor in the water, so it lives in a module of its own rather
than folded into the GDAT2 decoder beside it.

    $RMCMD,<code>*HH<CR><LF>

Same NMEA-0183 framing and the same XOR checksum as the ``$GDAT2`` sentences it
travels beside, so :func:`gdat2_checksum` is reused rather than reimplemented.
That is not tidiness: the manufacturer's own control station carries these
sentences as string literals with the checksums baked in, and a baked-in
checksum is a copy that nothing checks. A wrong one would be dropped silently by
the firmware while the telemetry kept flowing, which looks exactly like a valve
that will not move.

CODE 5 OPENS AND CODE 1 CLOSES
==============================
Which is the opposite of the manufacturer's own labelling. Their control station
shipped with buttons reading "OPEN Valve (RMCMD_ENABLE_1)" and "CLOSE Valve
(RMCMD_DISABLE_1)"; pressing OPEN closed the valve. Established on the hardware,
and corrected in their file too.

So :class:`ValveCommand` is named for the EFFECT, never for the vendor's
mnemonic. Whatever "enable output 1" means inside that firmware, what it does to
the water is close. Callers ask for ``ValveCommand.OPEN`` and are not required
to know, or to re-derive, that this puts a 5 on the wire.

UNACKNOWLEDGED
==============
The aux_vcu sends no reply to an ``$RMCMD``. A successful send means the bytes
reached the kernel - not that the valve moved, and not that the firmware
understood the code. ``ulRaw[9]``, the digital I/O field of the telemetry
already arriving, is the only evidence of that; it is read in
``features/device_status/domain/valve.py``.
"""
from __future__ import annotations

from enum import Enum

from supersilence.infrastructure.telemetry.gdat2 import gdat2_checksum

#: The talker this console sends. Distinct from GDAT2, which it only receives.
RMCMD_TALKER = "RMCMD"


class ValveCommand(Enum):
    """What to ask the actuator to do, named for what it does.

    The values are the vendor's command codes and are deliberately not in
    numerical order - see the module docstring. Anything that "tidies" them
    into order silently reverses the valve.
    """

    #: Vendor's RMCMD_DISABLE_1.
    OPEN = 5
    #: Vendor's RMCMD_ENABLE_1.
    CLOSE = 1


def build_valve_command(command: ValveCommand) -> bytes:
    """-> the exact bytes to put on the wire, CRLF included.

    ASCII by construction: the talker and the code are both ASCII, so the
    encode cannot fail and no error path is offered for one that cannot happen.
    """
    body = f"{RMCMD_TALKER},{command.value}"
    return f"${body}*{gdat2_checksum(body):02X}\r\n".encode("ascii")
