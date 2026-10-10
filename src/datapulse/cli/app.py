from pathlib import Path
from typing import Annotated

import rich
import typer

from datapulse import __version__
from datapulse.api import analyze
from datapulse.config import AnalysisConfig, load_config
from datapulse.reporting.terminal import display_report

app = typer.Typer(
    name="datapulse",
    help="Automated tabular exploratory data analysis (EDA) toolkit.",
    add_completion=False,
)


def version_callback(value: bool) -> None:
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


@app.command(name="analyze")
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

    fmt = format.lower()
    if fmt not in ("terminal", "html", "json"):
        raise typer.BadParameter(
            f"Invalid format '{format}'. Supported formats: terminal, html, json"
        )

    # 1. Base config
    if config:
        try:
            cfg = load_config(config)
        except Exception as exc:
            rich.print(f"[bold red]Configuration error:[/bold red] {exc}")
            raise typer.Exit(code=1) from exc
    else:
        cfg = AnalysisConfig()

    # 2. Command-line overrides
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

    # 3. Execution
    try:
        report = analyze(file_path, config=cfg)
    except Exception as exc:
        rich.print(f"[bold red]Analysis error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    # 4. Reporting
    if fmt == "terminal":
        if not quiet:
            display_report(report)
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


@app.command(name="profile")
def run_profile(
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
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress terminal output when saving reports.",
        ),
    ] = False,
) -> None:
    """Alias for analyze command."""
    run_analyze(
        file_path=file_path,
        format=format,
        output=output,
        config=config,
        quiet=quiet,
    )


@app.command(name="version")
def run_version() -> None:
    """Print the DataPulse version."""
    typer.echo(f"DataPulse v{__version__}")
