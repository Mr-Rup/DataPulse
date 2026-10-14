# =========================================================================
# DataPulse CLI Analyze Command
# Comprehensive dataset analysis and profiling execution handler.
# =========================================================================

from pathlib import Path
from typing import Annotated

import rich
import typer

from datapulse.api import analyze
from datapulse.config import AnalysisConfig, load_config
from datapulse.models.report import AnalysisReport
from datapulse.reporting.terminal import display_report

# =========================================================================
# REPORT EXPORT HANDLER
# =========================================================================

def _render_and_export(
    report: AnalysisReport,
    fmt: str,
    output: Path | None,
    quiet: bool,
    full: bool,
    section: str | None,
    col_filter: list[str] | None,
    file_path: Path,
) -> None:
    """Render report to terminal or export to HTML/JSON files."""
    if fmt == "terminal":
        if not quiet:
            display_report(
                report,
                full=full,
                section=section,
                columns=col_filter,
            )
        if output:
            if output.suffix.lower() == ".html":
                report.save_html(output)
            else:
                report.save_json(output)
            if not quiet:
                rich.print(f"[green]Report saved to {output}[/green]")
    elif fmt == "html":
        out_path = output if output else Path(f"{file_path.stem}_report.html")
        report.save_html(out_path)
        if not quiet:
            rich.print(f"[green]Saved HTML report to {out_path}[/green]")
    elif fmt == "json":
        if output:
            report.save_json(output)
            if not quiet:
                rich.print(f"[green]Saved JSON report to {output}[/green]")
        else:
            typer.echo(report.to_json())


# =========================================================================
# COMMAND IMPLEMENTATION
# =========================================================================

def run_analyze(
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
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output report format: 'terminal', 'html', or 'json'.",
            case_sensitive=False,
        ),
    ] = "terminal",
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Path to save report output (.html or .json).",
        ),
    ] = None,
    html: Annotated[
        bool,
        typer.Option(
            "--html",
            help="Quick export interactive HTML dashboard.",
        ),
    ] = False,
    json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Quick export machine-readable JSON report.",
        ),
    ] = False,
    all: Annotated[
        bool,
        typer.Option(
            "--all",
            "-a",
            help="Display full comprehensive report across all sections.",
        ),
    ] = False,
    section: Annotated[
        str | None,
        typer.Option(
            "--section",
            "-s",
            help="Display only a specific report section (e.g. quality, schema).",
        ),
    ] = None,
    columns: Annotated[
        str | None,
        typer.Option(
            "--columns",
            help="Comma-separated column names to filter display.",
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
    max_categories: Annotated[
        int | None,
        typer.Option(
            "--max-categories",
            help="Max top categories to profile per column.",
        ),
    ] = None,
    correlations: Annotated[
        bool | None,
        typer.Option(
            "--correlations/--no-correlations",
            help="Enable or disable pairwise correlation calculations.",
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
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress terminal output when saving reports.",
        ),
    ] = False,
) -> None:
    """Analyze a dataset and generate an automated EDA report."""
    # Resolve output format: quick flags -> extension auto-detection -> explicit option
    fmt = format.lower()
    if html:
        fmt = "html"
    elif json:
        fmt = "json"
    elif output and fmt == "terminal":
        suffix = output.suffix.lower()
        if suffix == ".html":
            fmt = "html"
        elif suffix == ".json":
            fmt = "json"
    if fmt not in ("terminal", "html", "json"):
        raise typer.BadParameter(
            f"Invalid format '{format}'. Supported formats: terminal, html, json"
        )
    # Parse columns filter list if specified
    col_filter = (
        [c.strip() for c in columns.split(",") if c.strip()]
        if columns
        else None
    )
    # Load configuration from file or defaults
    if config:
        try:
            cfg = load_config(config)
        except Exception as exc:
            rich.print(f"[bold red]Configuration error:[/bold red] {exc}")
            raise typer.Exit(code=1) from exc
    else:
        cfg = AnalysisConfig()
    # Apply CLI flag overrides to configuration
    overrides: dict[str, object] = {}
    if max_categories is not None:
        overrides["max_categories"] = max_categories
    if correlations is not None:
        overrides["compute_correlations"] = correlations
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
    # Multi-format rendering and export
    _render_and_export(
        report=report,
        fmt=fmt,
        output=output,
        quiet=quiet,
        full=all,
        section=section,
        col_filter=col_filter,
        file_path=file_path,
    )


run_profile = run_analyze
