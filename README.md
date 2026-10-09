
# DataPulse

A local-first, automated exploratory data analysis (EDA) toolkit for tabular datasets,
built with modern Python data technologies.

## Goals

- Automated first-pass profiling of tabular datasets using Polars.
- Schema inspection, missingness analysis, and cardinality breakdown.
- Column-aware descriptive statistics and data-quality findings.
- Clean terminal summaries and standalone exportable reports.

## Technology Stack

- Python 3.14+
- uv
- Polars
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
