# =========================================================================
# DataPulse CLI Column Command
# Deep-dive statistical profiling for an individual target column.
# =========================================================================

from pathlib import Path
from typing import Annotated

import rich
import typer

from datapulse.api import analyze
from datapulse.config import AnalysisConfig, load_config
from datapulse.reporting.terminal import display_column_profile

# =========================================================================
# COMMAND IMPLEMENTATION
# =========================================================================

def run_column(
    file_path: Annotated[
        Path,
        typer.Argument(
            help="Path to tabular dataset (Parquet, CSV, JSON, Excel).",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    column_name: Annotated[
        str,
        typer.Argument(
            help="Name of the column to profile.",
        ),
    ],
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration file (.json or .toml).",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    sheet_name: Annotated[
        str | None,
        typer.Option(
            "--sheet-name",
            help="Sheet name to read when profiling Excel files.",
        ),
    ] = None,
    separator: Annotated[
        str | None,
        typer.Option(
            "--separator",
            help="Delimiter character for CSV files.",
        ),
    ] = None,
) -> None:
    """Display an exhaustive statistical profile for a single column."""
    # Load configuration from file or defaults
    if config:
        try:
            cfg = load_config(config)
        except Exception as exc:
            rich.print(f"[bold red]Configuration error:[/bold red] {exc}")
            raise typer.Exit(code=1) from exc
    else:
        cfg = AnalysisConfig()
    overrides: dict[str, object] = {}
    if sheet_name is not None:
        overrides["sheet_name"] = sheet_name
    if separator is not None:
        overrides["separator"] = separator
    if overrides:
        cfg = cfg.model_copy(update=overrides)
    # Execute analysis pipeline
    try:
        report = analyze(file_path, config=cfg)
    except Exception as exc:
        rich.print(f"[bold red]Analysis error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    # Render single column profile
    try:
        display_column_profile(report, column_name)
    except ValueError as exc:
        rich.print(f"[bold red]Column error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
