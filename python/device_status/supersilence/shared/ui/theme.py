"""The application's base text size.

Everything the operator reads is sized off one number. Qt's default point size
is whatever the desktop is configured for — typically 9 or 10 on Linux and
Windows — which is a size chosen for reading documents at a desk, not for
reading a tactical console across a compartment, and not for an operator whose
near vision is no longer what it was.

Setting it on the ``QApplication`` rather than per widget is what makes it carry:
every widget that has not been given a font of its own inherits this one, and the
custom-painted panels — DoA, BTR, LOFARGRAM, DEMON, the channel meters — all
build their label fonts from ``painter.font()``, which is the widget's, which is
this one. The two places that state a size in pixels instead are the target
detail panel and the map page; both are sized in the same proportion and are
noted where they are set, because a stylesheet pixel does not follow this.

The rest of the layout is not scaled. Qt lays out from font metrics, so panels
and windows grow with the text on their own; anything that does not is a fixed
size that was wrong before this change too.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import QApplication

#: The base size, in points, for every window in the application.
#:
#: Twelve, not the desktop default of nine or ten. Chosen as the smallest step
#: that is unambiguously larger at a normal viewing distance — a one-point rise
#: is invisible on most screens, and going past thirteen starts costing rows in
#: the contact table and the device status list, which is a real loss when the
#: question is how many contacts fit on screen at once.
BASE_POINT_SIZE = 12

#: Point size for panel titles and other deliberately larger text, kept in
#: proportion to the base rather than stated separately in each panel.
TITLE_POINT_SIZE = 15

#: Axis labels, tick values and mark annotations inside a painted panel.
#:
#: The same size as body text, not a step under it. These were drawn at 8 point,
#: a number that predated the base size and never tracked it; two points under
#: the base was the first correction and the operator asked for more. A panel
#: label is read at the same distance as everything else on the screen, so there
#: is no reason for it to be smaller — the cost is paid in panel margins, which
#: are widened to match, not in legibility.
PLOT_LABEL_POINT_SIZE = BASE_POINT_SIZE

#: For panels that draw a label per channel or per row, where the labels are the
#: densest thing on screen and a full-size label would collide with its
#: neighbour. Two points under the plot label, so it still moves when the base
#: moves.
DENSE_LABEL_POINT_SIZE = PLOT_LABEL_POINT_SIZE - 2


def apply_base_font(application: QApplication, point_size: int = BASE_POINT_SIZE) -> QFont:
    """Set the application-wide font, keeping the desktop's font family.

    Only the size changes. The family the desktop picked is the one with the
    coverage and hinting that desktop is configured for, and replacing it with a
    named family is how an application ends up rendering in a fallback font on
    the one machine that matters.
    """
    font = QFont(application.font())
    font.setPointSize(point_size)
    application.setFont(font)
    return font


#: The painted panels' colours, resolved against the desktop's own theme.
#:
#: Every custom-painted panel in this application — DoA, elevation, the
#: direction map, LOFARGRAM, BTR, DEMON, the channel meters — drew on a dark
#: ground stated as a literal in its own module. On a desktop set to light that
#: left a console of black rectangles among white windows, which is not a theme
#: so much as a set of panels that never asked.
#:
#: The two palettes are the GitHub dark and light families, which is where the
#: original literals came from; keeping the same family means the light side is
#: a real counterpart rather than an inversion. Contrast is checked on both
#: grounds rather than assumed: the dark palette's blue (#58a6ff) and green
#: (#3fb950) are chosen to sit on near-black and are washed out on white, so the
#: light palette uses their darker counterparts rather than the same values.
@dataclass(frozen=True)
class PlotPalette:
    """One theme's colours for the painted panels."""

    #: The ground a plot is drawn on.
    panel: str
    #: A panel that sits slightly above the ground — the polar plots and the
    #: channel meters use it to separate the instrument from the window.
    raised_panel: str
    #: Axis boxes, tick marks and gridlines.
    grid: str
    #: Labels and values the operator reads.
    text: str
    #: Secondary labels: axis numbers, units, annotations.
    dim: str
    #: A measured trace.
    trace: str
    #: A confirmed relation — the DEMON comb, a strong contact.
    confirm: str
    #: A rival or held reading.
    rival: str
    #: A fault, a refusal, a contact that needs attention.
    alert: str
    #: The current selection.
    selected: str
    #: Maximum contrast against the ground: peak markers, threshold lines.
    #: White on dark and near-black on light, which is why it cannot be a
    #: literal in the panels.
    accent: str


#: Drawn on a desktop set to dark, and the palette every panel used to hardcode.
DARK_PLOT_PALETTE = PlotPalette(
    panel="#12151a",
    raised_panel="#1c1f26",
    grid="#2c313a",
    text="#c8ccd4",
    dim="#6b7280",
    trace="#58a6ff",
    confirm="#3fb950",
    rival="#d29922",
    alert="#f85149",
    selected="#ffd44a",
    accent="#f0f3f7",
)

#: Drawn on a desktop set to light.
#:
#: `dim` is darker than the dark palette's, not the same value: #6b7280 has
#: enough contrast against near-black and not enough against white, and axis
#: numbers are exactly the text that stops being readable first.
LIGHT_PLOT_PALETTE = PlotPalette(
    panel="#ffffff",
    raised_panel="#f5f6f8",
    grid="#d0d7de",
    text="#1c1f26",
    dim="#57606a",
    trace="#0969da",
    confirm="#1a7f37",
    rival="#9a6700",
    alert="#cf222e",
    selected="#bf8700",
    accent="#24292f",
)

#: Lightness above which the desktop's window colour counts as a light theme.
#:
#: The midpoint of Qt's 0–255 lightness. Read from the window role rather than
#: from a style hint so it works on the Qt versions this application is built
#: against and on a desktop whose theme the platform does not report.
LIGHT_THEME_LIGHTNESS = 128


def is_light_theme(application: QApplication | None = None) -> bool:
    """Whether the desktop is running a light theme.

    Defaults to dark when there is no application yet, because that is what the
    console is used in and because a panel constructed before the application
    exists is a test, not an operator.
    """
    instance = application or QApplication.instance()
    if instance is None:
        return False
    window = instance.palette().color(QPalette.ColorRole.Window)
    return window.lightness() >= LIGHT_THEME_LIGHTNESS


@dataclass(frozen=True)
class SelectionColours:
    """The ground and text of a picked row, for one theme."""

    ground: str
    text: str


#: A picked row on a dark desktop: white ground, near-black text.
DARK_SELECTION = SelectionColours(ground="#f0f3f7", text="#12151a")
#: A picked row on a light desktop: dark grey ground, white text.
LIGHT_SELECTION = SelectionColours(ground="#3a3f47", text="#ffffff")


def selection_colours(application: QApplication | None = None) -> SelectionColours:
    """How a picked row is drawn against the theme in force.

    Inverted against the desktop rather than tinted with it, at the operator's
    request. A selection is answering one question — *which row am I looking
    at* — and the fastest answer the eye has is a block of the opposite value;
    a highlight in the same family as the table it sits in has to be searched
    for among the rows it is meant to stand out from.

    The text is inverted with the ground, together, because that is the pair
    that can go wrong: a themed ground with unthemed text is how a selected row
    ends up white on white and disappears entirely at the moment it is clicked.
    """
    return LIGHT_SELECTION if is_light_theme(application) else DARK_SELECTION


def plot_palette(application: QApplication | None = None) -> PlotPalette:
    """The painted panels' colours for the theme in force right now.

    Called at paint time rather than captured at import, for two reasons: a
    module constant is fixed when the module is first imported, which is before
    the ``QApplication`` exists, and the desktop's theme can change while the
    console is running.
    """
    return LIGHT_PLOT_PALETTE if is_light_theme(application) else DARK_PLOT_PALETTE
