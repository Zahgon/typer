from enum import Enum
from typing import TypeVar

import click

ParamTypeValue = TypeVar("ParamTypeValue")


class TyperChoice(click.Choice[ParamTypeValue]):
    def normalize_choice(
        self, choice: ParamTypeValue, ctx: click.Context | None
    ) -> str:
        # Click 8.2.0 added a new method `normalize_choice` to the `Choice` class
        # to support enums, but it uses the enum names, while Typer has always used the
        # enum values.
        # This class overrides that method to maintain the previous behavior.
        # In Click:
        # normed_value = choice.name if isinstance(choice, Enum) else str(choice)
        pass
