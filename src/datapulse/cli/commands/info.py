# =========================================================================
# DataPulse CLI Info Command
# Lightweight metadata and schema inspection without profiling overhead.
# =========================================================================

from pathlib import Path
from typing import Annotated

import polars as pl
import rich
import typer

from datapulse.ingestion.readers import read_source
from datapulse.reporting.terminal import display_file_info

# =========================================================================
# COMMAND IMPLEMENTATION
# =========================================================================

def run_info(
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
    """Inspect dataset metadata, file size, row count, and schema instantly."""
    # Ingest data lazily without profiling
    try:
        lazy_frame, source_info = read_source(
            file_path,
            sheet_name=sheet_name,
            separator=separator,
        )
    except Exception as exc:
        rich.print(f"[bold red]Ingestion error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    # Extract schema and row count
    try:
        schema = lazy_frame.collect_schema()
        row_count = lazy_frame.select(pl.len()).collect().item()
        display_file_info(
            source_name=source_info.file_name,
            file_path=str(source_info.file_path),
            file_format=source_info.file_format,
            file_size_mb=source_info.file_size_mb,
            schema=dict(schema),
            row_count=int(row_count),
        )
    except Exception as exc:
        rich.print(f"[bold red]Metadata inspection error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
