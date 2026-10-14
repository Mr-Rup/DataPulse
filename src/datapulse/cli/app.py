# =========================================================================
# DataPulse Command-Line Interface (CLI)
# Interactive Typer app for profiling, querying, and inspecting datasets.
# =========================================================================

from typing import Annotated

import typer
from typer.core import TyperGroup

from datapulse import __version__
from datapulse.cli.commands import (
    run_analyze,
    run_column,
    run_info,
    run_profile,
    run_query,
    run_show,
)

# =========================================================================
# APPLICATION SETUP & GLOBAL CALLBACKS
# =========================================================================

class DefaultTyperGroup(TyperGroup):
    """Command group defaulting to 'analyze' when file is passed directly."""

    def resolve_command(self, ctx, args):
        if not args:
            return super().resolve_command(ctx, args)
        cmd_name = args[0]
        if cmd_name not in self.commands and not cmd_name.startswith("-"):
            cmd = self.get_command(ctx, "analyze")
            return "analyze", cmd, args
        return super().resolve_command(ctx, args)


app = typer.Typer(
    cls=DefaultTyperGroup,
    name="datapulse",
    help="Automated tabular exploratory data analysis (EDA) toolkit.",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print the package version and terminate execution."""
    if value:
        typer.echo(f"DataPulse v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            help="Show DataPulse version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """DataPulse: Automated exploratory data analysis."""


# =========================================================================
# COMMAND REGISTRATION
# =========================================================================

app.command(name="analyze")(run_analyze)
app.command(name="profile", help="Alias for analyze command.")(run_profile)
app.command(name="show")(run_show)
app.command(name="column")(run_column)
app.command(name="query")(run_query)
app.command(name="info")(run_info)


@app.command(name="version")
def run_version() -> None:
    """Print the DataPulse version."""
    typer.echo(f"DataPulse v{__version__}")
