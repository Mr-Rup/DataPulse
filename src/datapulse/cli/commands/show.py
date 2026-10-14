# =========================================================================
# DataPulse CLI Show Command
# Target a specific analytical section or subset of columns.
# =========================================================================

from pathlib import Path
from typing import Annotated

import rich
import typer

from datapulse.api import analyze
from datapulse.config import AnalysisConfig, load_config
from datapulse.reporting.terminal import display_report

# =========================================================================
# COMMAND IMPLEMENTATION
# =========================================================================

def run_show(
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
    section: Annotated[
        str,
        typer.Argument(
            help=(
                "Section to display: overview, schema, missing, duplicates, "
                "quality, numeric, categorical, temporal, boolean, text, "
                "identifiers, findings, correlations, keys."
            ),
        ),
    ] = "overview",
    columns: Annotated[
        str | None,
        typer.Option(
            "--columns",
            help="Comma-separated column names to filter section display.",
        ),
    ] = None,
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
    """Show a specific analytical section or filtered column view of a dataset."""
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
    # Parse columns filter list if specified
    col_filter = (
        [c.strip() for c in columns.split(",") if c.strip()]
        if columns
        else None
    )
    # Execute analysis pipeline
    try:
        report = analyze(file_path, config=cfg)
    except Exception as exc:
        rich.print(f"[bold red]Analysis error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    # Render selected section
    try:
        display_report(report, section=section, columns=col_filter)
    except ValueError as exc:
        rich.print(f"[bold red]Section error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
