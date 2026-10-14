# =========================================================================
# DataPulse Terminal Query & File Info Views
# Renderers for tabular query results and lightweight file metadata.
# =========================================================================

from typing import Any

import polars as pl
from rich.panel import Panel
from rich.table import Table

from datapulse.reporting.terminal.console import console

# =========================================================================
# QUERY RESULTS & FILE INFO RENDERERS
# =========================================================================

def display_query_results(df: pl.DataFrame, title: str = "Query Results") -> None:
    """Render matching Polars DataFrame query results in a clean Rich table."""
    table = Table(title=f"{title} ({df.height:,} rows, {df.width} cols)")
    for col in df.columns:
        table.add_column(col, style="cyan")
    # Truncate row display if large to avoid terminal freeze
    display_rows = df.head(50)
    for row in display_rows.iter_rows():
        table.add_row(
            *[str(val) if val is not None else "[dim]null[/dim]" for val in row]
        )
    console.print(table)
    if df.height > 50:
        console.print(
            f"[dim]... showing first 50 rows of {df.height:,} total rows.[/dim]"
        )


def display_file_info(
    source_name: str,
    file_path: str,
    file_format: str,
    file_size_mb: float,
    schema: dict[str, Any],
    row_count: int | None = None,
) -> None:
    """Display instant file metadata and schema without full profiling overhead."""
    row_str = f"{row_count:,}" if row_count is not None else "Lazy (Not collected)"
    console.print(
        Panel(
            f"[bold]Source:[/bold] {source_name}\n"
            f"[bold]Path:[/bold] {file_path}\n"
            f"[bold]Format:[/bold] [cyan]{file_format.upper()}[/cyan]\n"
            f"[bold]Size:[/bold] {file_size_mb:.2f} MB\n"
            f"[bold]Rows:[/bold] {row_str}\n"
            f"[bold]Columns:[/bold] {len(schema)}",
            title="DataPulse | File Information",
        )
    )
    schema_table = Table(title="Schema Definition")
    schema_table.add_column("Column Name", style="bold")
    schema_table.add_column("Polars Data Type", style="cyan")
    for col_name, dtype in schema.items():
        schema_table.add_row(col_name, str(dtype))
    console.print(schema_table)
