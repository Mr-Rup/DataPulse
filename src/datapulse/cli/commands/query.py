# =========================================================================
# DataPulse CLI Query Command
# Direct tabular filtering and SQL querying engine powered by Polars SQLContext.
# =========================================================================

from pathlib import Path
from typing import Annotated

import polars as pl
import rich
import typer

from datapulse.ingestion.readers import read_source
from datapulse.reporting.terminal import display_query_results

# =========================================================================
# COMMAND IMPLEMENTATION
# =========================================================================

def run_query(
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
    target_or_sql: Annotated[
        str | None,
        typer.Argument(
            help="SQL query statement, column name, or filter expression.",
        ),
    ] = None,
    filter: Annotated[
        str | None,
        typer.Option(
            "--filter",
            help="Filter expression to apply (e.g. 'fare_amount < 0').",
        ),
    ] = None,
    equals: Annotated[
        str | None,
        typer.Option(
            "--equals",
            help="Value to match for equality on target column.",
        ),
    ] = None,
    gt: Annotated[
        float | None,
        typer.Option(
            "--gt",
            help="Greater-than threshold on target column.",
        ),
    ] = None,
    lt: Annotated[
        float | None,
        typer.Option(
            "--lt",
            help="Less-than threshold on target column.",
        ),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            "-n",
            help="Maximum number of rows to return and display.",
        ),
    ] = 50,
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
    """Execute SQL queries or column filters directly against any dataset."""
    # Read dataset lazily with zero overhead
    try:
        lazy_frame, source_info = read_source(
            file_path,
            sheet_name=sheet_name,
            separator=separator,
        )
    except Exception as exc:
        rich.print(f"[bold red]Ingestion error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    # Setup Polars SQLContext with standard self and clean table alias
    clean_stem = "".join(
        c if c.isalnum() else "_" for c in file_path.stem
    ).strip("_")
    sql_ctx = pl.SQLContext(
        frames={
            "self": lazy_frame,
            "df": lazy_frame,
            "table": lazy_frame,
            clean_stem: lazy_frame,
        }
    )
    # Determine execution SQL query string
    resolved_sql: str
    query_title: str
    if filter:
        resolved_sql = f"SELECT * FROM self WHERE {filter} LIMIT {limit}"
        query_title = f"Filter: {filter}"
    elif target_or_sql:
        normalized = target_or_sql.strip()
        lower_query = normalized.lower()
        if (
            lower_query.startswith("select ")
            or lower_query.startswith("with ")
            or lower_query.startswith("show ")
            or lower_query.startswith("describe ")
        ):
            resolved_sql = normalized
            query_title = "SQL Execution"
        elif any(op in lower_query for op in ("=", ">", "<", " in ", " like ")):
            resolved_sql = f"SELECT * FROM self WHERE {normalized} LIMIT {limit}"
            query_title = f"Expression: {normalized}"
        else:
            col_name = normalized
            if equals is not None:
                val = (
                    equals
                    if equals.replace(".", "", 1).isdigit()
                    or equals.lower() in ("true", "false")
                    else f"'{equals}'"
                )
                resolved_sql = (
                    f"SELECT * FROM self WHERE {col_name} = {val} LIMIT {limit}"
                )
                query_title = f"Filter: {col_name} == {equals}"
            elif gt is not None:
                resolved_sql = (
                    f"SELECT * FROM self WHERE {col_name} > {gt} LIMIT {limit}"
                )
                query_title = f"Filter: {col_name} > {gt}"
            elif lt is not None:
                resolved_sql = (
                    f"SELECT * FROM self WHERE {col_name} < {lt} LIMIT {limit}"
                )
                query_title = f"Filter: {col_name} < {lt}"
            else:
                resolved_sql = f"SELECT {col_name} FROM self LIMIT {limit}"
                query_title = f"Column: {col_name}"
    else:
        resolved_sql = f"SELECT * FROM self LIMIT {limit}"
        query_title = f"Preview: {source_info.file_name}"
    # Execute query and render results table
    try:
        result_df = sql_ctx.execute(resolved_sql).collect()
        display_query_results(result_df, title=query_title)
    except Exception as exc:
        rich.print(f"[bold red]Query execution error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
