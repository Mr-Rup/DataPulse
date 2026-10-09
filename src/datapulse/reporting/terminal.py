from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from datapulse.profiling.profiler import DatasetProfiler

# start console
console = Console()

def display_profile(profiler: DatasetProfiler) -> None:
    """Display the dataset profile in the terminal."""

    # display the profile overview
    overview = profiler.get_overview()  
    console.print(
        Panel(
            f"[bold]File:[/bold] {overview['file_name']}\n"
            f"[bold]Size:[/bold] {overview['file_size_mb']} MB\n"
            f"[bold]Rows:[/bold] {overview['row_count']:,}\n"
            f"[bold]Columns:[/bold] {overview['column_count']}",
            title="DataPulse | Dataset Overview",
        )
    )

    # create schema table and display
    schema_table = Table(title="Dataset Schema")

    schema_table.add_column("Column")
    schema_table.add_column("Data Type")

    for column, dtype in overview["schema"].items():
        schema_table.add_row(column, dtype)

    console.print(schema_table)

    # create missing values table and display
    missing_table = Table(title="Missing Values")

    missing_table.add_column("Column")
    missing_table.add_column("Null Count", justify="right")
    missing_table.add_column("Non-Missing", justify="right")
    missing_table.add_column("Missing %", justify="right")

    missing_values = profiler.get_missing_values()

    for row in missing_values.iter_rows(named=True):
        missing_table.add_row(
            row["column"],
            f"{row['null_count']:,}",
            f"{row['non_missing_count']:,}",
            f"{row['missing_percentage']:.2f}%",
        )

    console.print(missing_table)

    # create numeric statistics table and display
    statistics = profiler.get_numeric_statistics()

    if statistics.width > 0:
        statistics_table = Table(title="Numeric Statistics")

        statistics_table.add_column("Statistic")

        for column in statistics.columns:
            statistics_table.add_column(column)

        for row in statistics.iter_rows():
            statistic_name = str(row[0])

            values = [
                str(value) if value is not None else "NULL"
                for value in row[1:]
            ]

            statistics_table.add_row(statistic_name, *values)

        console.print(statistics_table)

    # create numeric statistics table and display
    duplicate_summary = profiler.get_duplicate_summary()

    duplicate_table = Table(title="Duplicate Row Analysis")
    duplicate_table.add_column("Metric")
    duplicate_table.add_column("Value", justify="right")

    duplicate_table.add_row(
        "Total Rows",
        f"{duplicate_summary['total_rows']:,}",
    )
    duplicate_table.add_row(
        "Unique Rows",
        f"{duplicate_summary['unique_rows']:,}",
    )
    duplicate_table.add_row(
        "Duplicate Rows",
        f"{duplicate_summary['duplicate_rows']:,}",
    )
    duplicate_table.add_row(
        "Duplicate Percentage",
        f"{duplicate_summary['duplicate_percentage']:.2f}%",
    )

    console.print(duplicate_table)

    # create categorical statistics table and display
    categorical_statistics = profiler.get_categorical_statistics()

    if categorical_statistics.height > 0:
        categorical_table = Table(title="Categorical Analysis")

        categorical_table.add_column("Column")
        categorical_table.add_column("Distinct Values", justify="right")
        categorical_table.add_column(
            "Cardinality %", justify="right"
        )

        for row in categorical_statistics.iter_rows(named=True):
            categorical_table.add_row(
                row["column"],
                f"{row['unique_count']:,}",
                f"{row['cardinality_percentage']:.2f}%",
            )

        console.print(categorical_table)

    
    quality = profiler.get_column_quality()

    quality_table = Table(title="Column Quality Summary")
    quality_table.add_column("Column")
    quality_table.add_column("Type")
    quality_table.add_column("Category")
    quality_table.add_column("Nulls", justify="right")
    quality_table.add_column("Missing %", justify="right")
    quality_table.add_column("Distinct", justify="right")

    for row in quality.iter_rows(named=True):
        quality_table.add_row(
            row["column"],
            row["data_type"],
            row["category"],
            f"{row['null_count']:,}",
            f"{row['missing_percentage']:.2f}%",
            f"{row['unique_count']:,}",
        )

    console.print(quality_table)

    temporal = profiler.get_temporal_statistics()

    if temporal.height > 0:
        temporal_table = Table(title="Date/Time Analysis")
        temporal_table.add_column("Column")
        temporal_table.add_column("Minimum")
        temporal_table.add_column("Maximum")
        temporal_table.add_column("Distinct Values", justify="right")

        for row in temporal.iter_rows(named=True):
            temporal_table.add_row(
                row["column"],
                row["minimum"],
                row["maximum"],
                f"{row['unique_count']:,}",
            )

        console.print(temporal_table)

