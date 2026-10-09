from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from datapulse.models.report import AnalysisReport
from datapulse.profiling.profiler import DatasetProfiler

console = Console()


def display_report(report: AnalysisReport) -> None:
    """Display an AnalysisReport in the terminal."""

    summary = report.summary
    console.print(
        Panel(
            f"[bold]File:[/bold] {summary.file_name}\n"
            f"[bold]Size:[/bold] {summary.file_size_mb} MB\n"
            f"[bold]Rows:[/bold] {summary.row_count:,}\n"
            f"[bold]Columns:[/bold] {summary.column_count}\n"
            f"[bold]Elapsed:[/bold] {report.metadata.elapsed_seconds:.4f}s",
            title="DataPulse | Dataset Overview",
        )
    )

    schema_table = Table(title="Dataset Schema")
    schema_table.add_column("Column")
    schema_table.add_column("Data Type")

    for column, dtype in summary.schema.items():
        schema_table.add_row(column, dtype)

    console.print(schema_table)

    missing_table = Table(title="Missing Values")
    missing_table.add_column("Column")
    missing_table.add_column("Null Count", justify="right")
    missing_table.add_column("Non-Missing", justify="right")
    missing_table.add_column("Missing %", justify="right")

    for item in report.missing_values:
        missing_table.add_row(
            item.column,
            f"{item.null_count:,}",
            f"{item.non_missing_count:,}",
            f"{item.missing_percentage:.2f}%",
        )

    console.print(missing_table)

    dup = report.duplicates
    duplicate_table = Table(title="Duplicate Row Analysis")
    duplicate_table.add_column("Metric")
    duplicate_table.add_column("Value", justify="right")

    duplicate_table.add_row("Total Rows", f"{dup.total_rows:,}")
    duplicate_table.add_row("Unique Rows", f"{dup.unique_rows:,}")
    duplicate_table.add_row("Duplicate Rows", f"{dup.duplicate_rows:,}")
    duplicate_table.add_row("Duplicate Percentage", f"{dup.duplicate_percentage:.2f}%")

    console.print(duplicate_table)

    quality_table = Table(title="Column Quality Summary")
    quality_table.add_column("Column")
    quality_table.add_column("Type")
    quality_table.add_column("Category")
    quality_table.add_column("Nulls", justify="right")
    quality_table.add_column("Missing %", justify="right")
    quality_table.add_column("Distinct", justify="right")

    for col in report.columns:
        quality_table.add_row(
            col.name,
            col.physical_type,
            col.inferred_role,
            f"{col.null_count:,}",
            f"{col.missing_percentage:.2f}%",
            f"{col.unique_count:,}",
        )

    console.print(quality_table)

    cat_cols = [
        col for col in report.columns
        if "cardinality_percentage" in col.statistics
    ]
    if cat_cols:
        cat_table = Table(title="Categorical Analysis")
        cat_table.add_column("Column")
        cat_table.add_column("Distinct Values", justify="right")
        cat_table.add_column("Cardinality %", justify="right")

        for col in cat_cols:
            cat_table.add_row(
                col.name,
                f"{int(col.statistics['unique_count']):,}",
                f"{float(col.statistics['cardinality_percentage']):.2f}%",
            )
        console.print(cat_table)

    temporal_cols = [
        col for col in report.columns
        if "minimum" in col.statistics and "maximum" in col.statistics
    ]
    if temporal_cols:
        temporal_table = Table(title="Date/Time Analysis")
        temporal_table.add_column("Column")
        temporal_table.add_column("Minimum")
        temporal_table.add_column("Maximum")
        temporal_table.add_column("Distinct Values", justify="right")

        for col in temporal_cols:
            temporal_table.add_row(
                col.name,
                str(col.statistics["minimum"]),
                str(col.statistics["maximum"]),
                f"{int(col.statistics['unique_count']):,}",
            )
        console.print(temporal_table)


def display_profile(target: AnalysisReport | DatasetProfiler) -> None:
    """Display profile for an AnalysisReport or DatasetProfiler in the terminal."""

    if isinstance(target, AnalysisReport):
        display_report(target)
        return

    from datapulse.api import analyze
    report = analyze(target.file_path)
    display_report(report)
