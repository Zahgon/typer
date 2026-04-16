# Extracted and modified from https://github.com/ewels/rich-click

import inspect
import io
from collections import defaultdict
from collections.abc import Iterable
from gettext import gettext as _
from os import getenv
from typing import Any, Literal

import click
from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, RenderableType, group
from rich.emoji import Emoji
from rich.highlighter import RegexHighlighter
from rich.markdown import Markdown
from rich.markup import escape
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.traceback import Traceback
from typer.models import DeveloperExceptionConfig

# Default styles
STYLE_OPTION = "bold cyan"
STYLE_SWITCH = "bold green"
STYLE_NEGATIVE_OPTION = "bold magenta"
STYLE_NEGATIVE_SWITCH = "bold red"
STYLE_METAVAR = "bold yellow"
STYLE_METAVAR_SEPARATOR = "dim"
STYLE_USAGE = "yellow"
STYLE_USAGE_COMMAND = "bold"
STYLE_DEPRECATED = "red"
STYLE_DEPRECATED_COMMAND = "dim"
STYLE_HELPTEXT_FIRST_LINE = ""
STYLE_HELPTEXT = "dim"
STYLE_OPTION_HELP = ""
STYLE_OPTION_DEFAULT = "dim"
STYLE_OPTION_ENVVAR = "dim yellow"
STYLE_REQUIRED_SHORT = "red"
STYLE_REQUIRED_LONG = "dim red"
STYLE_OPTIONS_PANEL_BORDER = "dim"
ALIGN_OPTIONS_PANEL: Literal["left", "center", "right"] = "left"
STYLE_OPTIONS_TABLE_SHOW_LINES = False
STYLE_OPTIONS_TABLE_LEADING = 0
STYLE_OPTIONS_TABLE_PAD_EDGE = False
STYLE_OPTIONS_TABLE_PADDING = (0, 1)
STYLE_OPTIONS_TABLE_BOX = ""
STYLE_OPTIONS_TABLE_ROW_STYLES = None
STYLE_OPTIONS_TABLE_BORDER_STYLE = None
STYLE_COMMANDS_PANEL_BORDER = "dim"
ALIGN_COMMANDS_PANEL: Literal["left", "center", "right"] = "left"
STYLE_COMMANDS_TABLE_SHOW_LINES = False
STYLE_COMMANDS_TABLE_LEADING = 0
STYLE_COMMANDS_TABLE_PAD_EDGE = False
STYLE_COMMANDS_TABLE_PADDING = (0, 1)
STYLE_COMMANDS_TABLE_BOX = ""
STYLE_COMMANDS_TABLE_ROW_STYLES = None
STYLE_COMMANDS_TABLE_BORDER_STYLE = None
STYLE_COMMANDS_TABLE_FIRST_COLUMN = "bold cyan"
STYLE_ERRORS_PANEL_BORDER = "red"
ALIGN_ERRORS_PANEL: Literal["left", "center", "right"] = "left"
STYLE_ERRORS_SUGGESTION = "dim"
STYLE_ABORTED = "red"
_TERMINAL_WIDTH = getenv("TERMINAL_WIDTH")
MAX_WIDTH = int(_TERMINAL_WIDTH) if _TERMINAL_WIDTH else None
COLOR_SYSTEM: Literal["auto", "standard", "256", "truecolor", "windows"] | None = (
    "auto"  # Set to None to disable colors
)
_TYPER_FORCE_DISABLE_TERMINAL = getenv("_TYPER_FORCE_DISABLE_TERMINAL")
FORCE_TERMINAL = (
    True
    if getenv("GITHUB_ACTIONS") or getenv("FORCE_COLOR") or getenv("PY_COLORS")
    else None
)
if _TYPER_FORCE_DISABLE_TERMINAL:
    FORCE_TERMINAL = False

# Fixed strings
DEPRECATED_STRING = _("(deprecated) ")
DEFAULT_STRING = _("[default: {}]")
ENVVAR_STRING = _("[env var: {}]")
REQUIRED_SHORT_STRING = "*"
REQUIRED_LONG_STRING = _("[required]")
RANGE_STRING = " [{}]"
ARGUMENTS_PANEL_TITLE = _("Arguments")
OPTIONS_PANEL_TITLE = _("Options")
COMMANDS_PANEL_TITLE = _("Commands")
ERRORS_PANEL_TITLE = _("Error")
ABORTED_TEXT = _("Aborted.")
RICH_HELP = _("Try [blue]'{command_path} {help_option}'[/] for help.")

MARKUP_MODE_MARKDOWN = "markdown"
MARKUP_MODE_RICH = "rich"
_RICH_HELP_PANEL_NAME = "rich_help_panel"
ANSI_PREFIX = "\033["

MarkupModeStrict = Literal["markdown", "rich"]


# Rich regex highlighter
class OptionHighlighter(RegexHighlighter):
    """Highlights our special options."""

    highlights = [
        r"(^|\W)(?P<switch>\-\w+)(?![a-zA-Z0-9])",
        r"(^|\W)(?P<option>\-\-[\w\-]+)(?![a-zA-Z0-9])",
        r"(?P<metavar>\<[^\>]+\>)",
        r"(?P<usage>Usage: )",
    ]


class NegativeOptionHighlighter(RegexHighlighter):
    highlights = [
        r"(^|\W)(?P<negative_switch>\-\w+)(?![a-zA-Z0-9])",
        r"(^|\W)(?P<negative_option>\-\-[\w\-]+)(?![a-zA-Z0-9])",
    ]


# Highlighter to make [ | ] and <> dim
class MetavarHighlighter(RegexHighlighter):
    highlights = [
        r"^(?P<metavar_sep>(\[|<))",
        r"(?P<metavar_sep>\|)",
        r"(?P<metavar_sep>(\]|>))(\.\.\.)?$",
    ]


highlighter = OptionHighlighter()
negative_highlighter = NegativeOptionHighlighter()
metavar_highlighter = MetavarHighlighter()


def _has_ansi_character(text: str) -> bool:
    pass


def _get_rich_console(stderr: bool = False) -> Console:
    return Console(
        theme=Theme(
            {
                "option": STYLE_OPTION,
                "switch": STYLE_SWITCH,
                "negative_option": STYLE_NEGATIVE_OPTION,
                "negative_switch": STYLE_NEGATIVE_SWITCH,
                "metavar": STYLE_METAVAR,
                "metavar_sep": STYLE_METAVAR_SEPARATOR,
                "usage": STYLE_USAGE,
            },
        ),
        highlighter=highlighter,
        color_system=COLOR_SYSTEM,
        force_terminal=FORCE_TERMINAL,
        width=MAX_WIDTH,
        stderr=stderr,
    )


def _make_rich_text(
    *, text: str, style: str = "", markup_mode: MarkupModeStrict
) -> Markdown | Text:
    """Take a string, remove indentations, and return styled text.

    If `markup_mode` is `"rich"`, the text is parsed for Rich markup strings.
    If `markup_mode` is `"markdown"`, parse as Markdown.
    """
    pass


@group()
def _get_help_text(
    *,
    obj: click.Command | click.Group,
    markup_mode: MarkupModeStrict,
) -> Iterable[Markdown | Text]:
    """Build primary help text for a click command or group.

    Returns the prose help text for a command or group, rendered either as a
    Rich Text object or as Markdown.
    If the command is marked as deprecated, the deprecated string will be prepended.
    """
    pass


def _get_parameter_help(
    *,
    param: click.Option | click.Argument | click.Parameter,
    ctx: click.Context,
    markup_mode: MarkupModeStrict,
) -> Columns:
    """Build primary help text for a click option or argument.

    Returns the prose help text for an option or argument, rendered either
    as a Rich Text object or as Markdown.
    Additional elements are appended to show the default and required status if
    applicable.
    """
    pass


def _make_command_help(
    *,
    help_text: str,
    markup_mode: MarkupModeStrict,
) -> Text | Markdown:
    """Build cli help text for a click group command.

    That is, when calling help on groups with multiple subcommands
    (not the main help text when calling the subcommand help).

    Returns the first paragraph of help text for a command, rendered either as a
    Rich Text object or as Markdown.
    Ignores single newlines as paragraph markers, looks for double only.
    """
    pass


def _print_options_panel(
    *,
    name: str,
    params: list[click.Option] | list[click.Argument],
    ctx: click.Context,
    markup_mode: MarkupModeStrict,
    console: Console,
) -> None:
    pass


def _print_commands_panel(
    *,
    name: str,
    commands: list[click.Command],
    markup_mode: MarkupModeStrict,
    console: Console,
    cmd_len: int,
) -> None:
    pass


def rich_format_help(
    *,
    obj: click.Command | click.Group,
    ctx: click.Context,
    markup_mode: MarkupModeStrict,
) -> None:
    """Print nicely formatted help text using rich.

    Based on original code from rich-cli, by @willmcgugan.
    https://github.com/Textualize/rich-cli/blob/8a2767c7a340715fc6fbf4930ace717b9b2fc5e5/src/rich_cli/__main__.py#L162-L236

    Replacement for the click function format_help().
    Takes a command or group and builds the help text output.
    """
    pass


def rich_format_error(self: click.ClickException) -> None:
    """Print richly formatted click errors.

    Called by custom exception handler to print richly formatted click errors.
    Mimics original click.ClickException.echo() function but with rich formatting.
    """
    # Don't do anything when it's a NoArgsIsHelpError (without importing it, cf. #1278)
    if self.__class__.__name__ == "NoArgsIsHelpError":
        return

    console = _get_rich_console(stderr=True)
    ctx: click.Context | None = getattr(self, "ctx", None)
    if ctx is not None:
        console.print(ctx.get_usage())

    if ctx is not None and ctx.command.get_help_option(ctx) is not None:
        console.print(
            RICH_HELP.format(
                command_path=ctx.command_path, help_option=ctx.help_option_names[0]
            ),
            style=STYLE_ERRORS_SUGGESTION,
        )

    console.print(
        Panel(
            highlighter(self.format_message()),
            border_style=STYLE_ERRORS_PANEL_BORDER,
            title=ERRORS_PANEL_TITLE,
            title_align=ALIGN_ERRORS_PANEL,
        )
    )


def rich_abort_error() -> None:
    """Print richly formatted abort error."""
    console = _get_rich_console(stderr=True)
    console.print(ABORTED_TEXT, style=STYLE_ABORTED)


def escape_before_html_export(input_text: str) -> str:
    """Ensure that the input string can be used for HTML export."""
    pass


def rich_to_html(input_text: str) -> str:
    """Print the HTML version of a rich-formatted input string.

    This function does not provide a full HTML page, but can be used to insert
    HTML-formatted text spans into a markdown file.
    """
    pass


def rich_render_text(text: str) -> str:
    """Remove rich tags and render a pure text representation"""
    console = _get_rich_console()
    return "".join(segment.text for segment in console.render(text)).rstrip("\n")


def get_traceback(
    exc: BaseException,
    exception_config: DeveloperExceptionConfig,
    internal_dir_names: list[str],
) -> Traceback:
    pass
