
# DataPulse

A local-first data profiling and analytical benchmarking toolkit
built with modern Python data technologies.

## Goals

- Profile datasets using Polars.
- Compare Pandas, Polars eager, Polars lazy, and DuckDB.
- Evaluate performance across real-world datasets.
- Produce reproducible benchmark reports.

## Technology Stack

- Python
- uv
- Polars
- DuckDB
- Apache Arrow
- Parquet
- Typer
- Rich
- pytest
- Ruff
- Pyright

## Development

Install dependencies:

```bash
uv sync
```

Run tests:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check .
```

Run type checking:

```bash
uv run pyright
```
