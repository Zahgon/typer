import errno
import inspect
import os
import sys
from collections.abc import Callable, MutableMapping, Sequence
from difflib import get_close_matches
from enum import Enum
from gettext import gettext as _
from typing import (
    Any,
    TextIO,
    Union,
    cast,
)

import click
import click.core
import click.formatting
import click.shell_completion
import click.types
import click.utils

from ._typing import Literal
from .utils import parse_boolean_env_var

MarkupMode = Literal["markdown", "rich", None]
MARKUP_MODE_KEY = "TYPER_RICH_MARKUP_MODE"

HAS_RICH = parse_boolean_env_var(os.getenv("TYPER_USE_RICH"), default=True)

if HAS_RICH:
    DEFAULT_MARKUP_MODE: MarkupMode = "rich"
else:
    DEFAULT_MARKUP_MODE = None


# Copy from click.parser._split_opt
def _split_opt(opt: str) -> tuple[str, str]:
    first = opt[:1]
    if first.isalnum():
        return "", opt
    if opt[1:2] == first:
        return opt[:2], opt[2:]
    return first, opt[1:]


def _typer_param_setup_autocompletion_compat(
    self: click.Parameter,
    *,
    autocompletion: Callable[
        [click.Context, list[str], str], list[tuple[str, str] | str]
    ]
    | None = None,
) -> None:
    pass


def _get_default_string(
    obj: Union["TyperArgument", "TyperOption"],
    *,
    ctx: click.Context,
    show_default_is_str: bool,
    default_value: list[Any] | tuple[Any, ...] | str | Callable[..., Any] | Any,
) -> str:
    # Extracted from click.core.Option.get_help_record() to be reused by
    # rich_utils avoiding RegEx hacks
    pass


def _extract_default_help_str(
    obj: Union["TyperArgument", "TyperOption"], *, ctx: click.Context
) -> Any | Callable[[], Any] | None:
    # Extracted from click.core.Option.get_help_record() to be reused by
    # rich_utils avoiding RegEx hacks
    # Temporarily enable resilient parsing to avoid type casting
    # failing for the default. Might be possible to extend this to
    # help formatting in general.
    pass


def _main(
    self: click.Command,
    *,
    args: Sequence[str] | None = None,
    prog_name: str | None = None,
    complete_var: str | None = None,
    standalone_mode: bool = True,
    windows_expand_args: bool = True,
    rich_markup_mode: MarkupMode = DEFAULT_MARKUP_MODE,
    **extra: Any,
) -> Any:
    # Typer override, duplicated from click.main() to handle custom rich exceptions
    # Verify that the environment is configured correctly, or reject
    # further execution to avoid a broken script.
    if args is None:
        args = sys.argv[1:]

        # Covered in Click tests
        if os.name == "nt" and windows_expand_args:  # pragma: no cover
            args = click.utils._expand_args(args)
    else:
        args = list(args)

    if prog_name is None:
        prog_name = click.utils._detect_program_name()

    # Process shell completion requests and exit early.
    self._main_shell_completion(extra, prog_name, complete_var)

    try:
        try:
            with self.make_context(prog_name, args, **extra) as ctx:
                rv = self.invoke(ctx)
                if not standalone_mode:
                    return rv
                # it's not safe to `ctx.exit(rv)` here!
                # note that `rv` may actually contain data like "1" which
                # has obvious effects
                # more subtle case: `rv=[None, None]` can come out of
                # chained commands which all returned `None` -- so it's not
                # even always obvious that `rv` indicates success/failure
                # by its truthiness/falsiness
                ctx.exit()
        except EOFError as e:
            click.echo(file=sys.stderr)
            raise click.Abort() from e
        except KeyboardInterrupt as e:
            raise click.exceptions.Exit(130) from e
        except click.ClickException as e:
            if not standalone_mode:
                raise
            # Typer override
            if HAS_RICH and rich_markup_mode is not None:
                from . import rich_utils

                rich_utils.rich_format_error(e)
            else:
                e.show()
            # Typer override end
            sys.exit(e.exit_code)
        except OSError as e:
            if e.errno == errno.EPIPE:
                sys.stdout = cast(TextIO, click.utils.PacifyFlushWrapper(sys.stdout))
                sys.stderr = cast(TextIO, click.utils.PacifyFlushWrapper(sys.stderr))
                sys.exit(1)
            else:
                raise
    except click.exceptions.Exit as e:
        if standalone_mode:
            sys.exit(e.exit_code)
        else:
            # in non-standalone mode, return the exit code
            # note that this is only reached if `self.invoke` above raises
            # an Exit explicitly -- thus bypassing the check there which
            # would return its result
            # the results of non-standalone execution may therefore be
            # somewhat ambiguous: if there are codepaths which lead to
            # `ctx.exit(1)` and to `return 1`, the caller won't be able to
            # tell the difference between the two
            return e.exit_code
    except click.Abort:
        if not standalone_mode:
            raise
        # Typer override
        if HAS_RICH and rich_markup_mode is not None:
            from . import rich_utils

            rich_utils.rich_abort_error()
        else:
            click.echo(_("Aborted!"), file=sys.stderr)
        # Typer override end
        sys.exit(1)


class TyperArgument(click.core.Argument):
    def __init__(
        self,
        *,
        # Parameter
        param_decls: list[str],
        type: Any | None = None,
        required: bool | None = None,
        default: Any | None = None,
        callback: Callable[..., Any] | None = None,
        nargs: int | None = None,
        metavar: str | None = None,
        expose_value: bool = True,
        is_eager: bool = False,
        envvar: str | list[str] | None = None,
        # Note that shell_complete is not fully supported and will be removed in future versions
        # TODO: Remove shell_complete in a future version (after 0.16.0)
        shell_complete: Callable[
            [click.Context, click.Parameter, str],
            list["click.shell_completion.CompletionItem"] | list[str],
        ]
        | None = None,
        autocompletion: Callable[..., Any] | None = None,
        # TyperArgument
        show_default: bool | str = True,
        show_choices: bool = True,
        show_envvar: bool = True,
        help: str | None = None,
        hidden: bool = False,
        # Rich settings
        rich_help_panel: str | None = None,
    ):
        self.help = help
        self.show_default = show_default
        self.show_choices = show_choices
        self.show_envvar = show_envvar
        self.hidden = hidden
        self.rich_help_panel = rich_help_panel

        super().__init__(
            param_decls=param_decls,
            type=type,
            required=required,
            default=default,
            callback=callback,
            nargs=nargs,
            metavar=metavar,
            expose_value=expose_value,
            is_eager=is_eager,
            envvar=envvar,
            shell_complete=shell_complete,
        )
        _typer_param_setup_autocompletion_compat(self, autocompletion=autocompletion)

    def _get_default_string(
        self,
        *,
        ctx: click.Context,
        show_default_is_str: bool,
        default_value: list[Any] | tuple[Any, ...] | str | Callable[..., Any] | Any,
    ) -> str:
        pass

    def _extract_default_help_str(
        self, *, ctx: click.Context
    ) -> Any | Callable[[], Any] | None:
        pass

    def get_help_record(self, ctx: click.Context) -> tuple[str, str] | None:
        # Modified version of click.core.Option.get_help_record()
        # to support Arguments
        pass

    def make_metavar(self, ctx: click.Context) -> str:
        # Modified version of click.core.Argument.make_metavar()
        # to include Argument name
        pass

    def value_is_missing(self, value: Any) -> bool:
        pass


class TyperOption(click.core.Option):
    def __init__(
        self,
        *,
        # Parameter
        param_decls: list[str],
        type: click.types.ParamType | Any | None = None,
        required: bool | None = None,
        default: Any | None = None,
        callback: Callable[..., Any] | None = None,
        nargs: int | None = None,
        metavar: str | None = None,
        expose_value: bool = True,
        is_eager: bool = False,
        envvar: str | list[str] | None = None,
        # Note that shell_complete is not fully supported and will be removed in future versions
        # TODO: Remove shell_complete in a future version (after 0.16.0)
        shell_complete: Callable[
            [click.Context, click.Parameter, str],
            list["click.shell_completion.CompletionItem"] | list[str],
        ]
        | None = None,
        autocompletion: Callable[..., Any] | None = None,
        # Option
        show_default: bool | str = False,
        prompt: bool | str = False,
        confirmation_prompt: bool | str = False,
        prompt_required: bool = True,
        hide_input: bool = False,
        is_flag: bool | None = None,
        multiple: bool = False,
        count: bool = False,
        allow_from_autoenv: bool = True,
        help: str | None = None,
        hidden: bool = False,
        show_choices: bool = True,
        show_envvar: bool = False,
        # Rich settings
        rich_help_panel: str | None = None,
    ):
        super().__init__(
            param_decls=param_decls,
            type=type,
            required=required,
            default=default,
            callback=callback,
            nargs=nargs,
            metavar=metavar,
            expose_value=expose_value,
            is_eager=is_eager,
            envvar=envvar,
            show_default=show_default,
            prompt=prompt,
            confirmation_prompt=confirmation_prompt,
            hide_input=hide_input,
            is_flag=is_flag,
            multiple=multiple,
            count=count,
            allow_from_autoenv=allow_from_autoenv,
            help=help,
            hidden=hidden,
            show_choices=show_choices,
            show_envvar=show_envvar,
            prompt_required=prompt_required,
            shell_complete=shell_complete,
        )
        _typer_param_setup_autocompletion_compat(self, autocompletion=autocompletion)
        self.rich_help_panel = rich_help_panel

    def _get_default_string(
        self,
        *,
        ctx: click.Context,
        show_default_is_str: bool,
        default_value: list[Any] | tuple[Any, ...] | str | Callable[..., Any] | Any,
    ) -> str:
        pass

    def _extract_default_help_str(
        self, *, ctx: click.Context
    ) -> Any | Callable[[], Any] | None:
        pass

    def make_metavar(self, ctx: click.Context) -> str:
        pass

    def get_help_record(self, ctx: click.Context) -> tuple[str, str] | None:
        # Duplicate all of Click's logic only to modify a single line, to allow boolean
        # flags with only names for False values as it's currently supported by Typer
        # Ref: https://typer.tiangolo.com/tutorial/parameter-types/bool/#only-names-for-false
        pass

    def value_is_missing(self, value: Any) -> bool:
        pass


def _value_is_missing(param: click.Parameter, value: Any) -> bool:
    pass


def _typer_format_options(
    self: click.core.Command, *, ctx: click.Context, formatter: click.HelpFormatter
) -> None:
    pass


def _typer_main_shell_completion(
    self: click.core.Command,
    *,
    ctx_args: MutableMapping[str, Any],
    prog_name: str,
    complete_var: str | None = None,
) -> None:
    if complete_var is None:
        complete_var = f"_{prog_name}_COMPLETE".replace("-", "_").upper()

    instruction = os.environ.get(complete_var)

    if not instruction:
        return

    from .completion import shell_complete

    rv = shell_complete(self, ctx_args, prog_name, complete_var, instruction)
    sys.exit(rv)


class TyperCommand(click.core.Command):
    def __init__(
        self,
        name: str | None,
        *,
        context_settings: dict[str, Any] | None = None,
        callback: Callable[..., Any] | None = None,
        params: list[click.Parameter] | None = None,
        help: str | None = None,
        epilog: str | None = None,
        short_help: str | None = None,
        options_metavar: str | None = "[OPTIONS]",
        add_help_option: bool = True,
        no_args_is_help: bool = False,
        hidden: bool = False,
        deprecated: bool = False,
        # Rich settings
        rich_markup_mode: MarkupMode = DEFAULT_MARKUP_MODE,
        rich_help_panel: str | None = None,
    ) -> None:
        super().__init__(
            name=name,
            context_settings=context_settings,
            callback=callback,
            params=params,
            help=help,
            epilog=epilog,
            short_help=short_help,
            options_metavar=options_metavar,
            add_help_option=add_help_option,
            no_args_is_help=no_args_is_help,
            hidden=hidden,
            deprecated=deprecated,
        )
        self.rich_markup_mode: MarkupMode = rich_markup_mode
        self.rich_help_panel = rich_help_panel

    def format_options(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        pass

    def _main_shell_completion(
        self,
        ctx_args: MutableMapping[str, Any],
        prog_name: str,
        complete_var: str | None = None,
    ) -> None:
        _typer_main_shell_completion(
            self, ctx_args=ctx_args, prog_name=prog_name, complete_var=complete_var
        )

    def main(
        self,
        args: Sequence[str] | None = None,
        prog_name: str | None = None,
        complete_var: str | None = None,
        standalone_mode: bool = True,
        windows_expand_args: bool = True,
        **extra: Any,
    ) -> Any:
        return _main(
            self,
            args=args,
            prog_name=prog_name,
            complete_var=complete_var,
            standalone_mode=standalone_mode,
            windows_expand_args=windows_expand_args,
            rich_markup_mode=self.rich_markup_mode,
            **extra,
        )

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        pass


class TyperGroup(click.core.Group):
    def __init__(
        self,
        *,
        name: str | None = None,
        commands: dict[str, click.Command] | Sequence[click.Command] | None = None,
        # Rich settings
        rich_markup_mode: MarkupMode = DEFAULT_MARKUP_MODE,
        rich_help_panel: str | None = None,
        suggest_commands: bool = True,
        **attrs: Any,
    ) -> None:
        super().__init__(name=name, commands=commands, **attrs)
        self.rich_markup_mode: MarkupMode = rich_markup_mode
        self.rich_help_panel = rich_help_panel
        self.suggest_commands = suggest_commands

    def format_options(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        pass

    def _main_shell_completion(
        self,
        ctx_args: MutableMapping[str, Any],
        prog_name: str,
        complete_var: str | None = None,
    ) -> None:
        _typer_main_shell_completion(
            self, ctx_args=ctx_args, prog_name=prog_name, complete_var=complete_var
        )

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        pass

    def main(
        self,
        args: Sequence[str] | None = None,
        prog_name: str | None = None,
        complete_var: str | None = None,
        standalone_mode: bool = True,
        windows_expand_args: bool = True,
        **extra: Any,
    ) -> Any:
        return _main(
            self,
            args=args,
            prog_name=prog_name,
            complete_var=complete_var,
            standalone_mode=standalone_mode,
            windows_expand_args=windows_expand_args,
            rich_markup_mode=self.rich_markup_mode,
            **extra,
        )

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        pass

    def list_commands(self, ctx: click.Context) -> list[str]:
        """Returns a list of subcommand names.
        Note that in Click's Group class, these are sorted.
        In Typer, we wish to maintain the original order of creation (cf Issue #933)"""
        pass
