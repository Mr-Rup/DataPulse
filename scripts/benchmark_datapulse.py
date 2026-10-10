import time
from pathlib import Path

from rich.console import Console
from rich.table import Table

from datapulse import analyze

console = Console()


def run_benchmark() -> None:
    tlc_path = Path("data/raw/yellow_tripdata_2025-01.parquet")
    zone_path = Path("data/raw/taxi_zone_lookup.csv")

    table = Table(title="DataPulse Performance & Scale Benchmark")
    table.add_column("Dataset", style="bold")
    table.add_column("Rows", justify="right")
    table.add_column("Cols", justify="right")
    table.add_column("Sampling", style="italic")
    table.add_column("Elapsed Time", justify="right")
    table.add_column("Throughput", justify="right")

    runs = []
    if zone_path.exists():
        runs.append((zone_path, "Taxi Zones Lookup"))

    if tlc_path.exists():
        runs.append((tlc_path, "NYC Yellow Taxi Jan 2025"))

    if not runs:
        console.print("[yellow]No raw data found in data/raw/[/yellow]")
        return

    for path, label in runs:
        start = time.perf_counter()
        rep = analyze(path)
        elapsed = time.perf_counter() - start

        rows = rep.summary.row_count
        cols = rep.summary.column_count
        throughput = f"{int(rows / elapsed):,} rows/s" if elapsed > 0 else "N/A"

        table.add_row(
            path.name,
            f"{rows:,}",
            str(cols),
            label,
            f"{elapsed:.3f}s",
            throughput,
        )

    console.print(table)


if __name__ == "__main__":
    run_benchmark()
