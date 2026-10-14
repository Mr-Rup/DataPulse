<div align="center">

# 🛠️ DataPulse Developer & Contributor Guide

**The complete manual for extending DataPulse: adding automated quality rules, semantic roles, statistical profilers, CLI commands, and report exporters.**

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Polars](https://img.shields.io/badge/Polars-100%25%20Pure%20Engine-CD792C?style=flat&logo=polars&logoColor=white)](https://pola.rs/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg?style=flat)](https://github.com/astral-sh/ruff)

</div>

> Welcome to DataPulse! This guide provides end-to-end instructions for setting up the development environment, navigating the modular codebase, and extending DataPulse with new features while preserving its pure Polars performance and strict architectural standards.

---

## Architecture Principles

Before contributing code, keep DataPulse's core technical principles in mind:

- **100% Pure Polars:** Never introduce Pandas, NumPy, or eager single-threaded loop conversions into core profiling loops. Use Polars expressions, lazy plans (`LazyFrame`), and vectorized aggregations.
- **Modular File Decomposition:** Keep all files focused and clean (aiming for $\le 150\text{--}200$ lines). Decompose complex domains into dedicated sub-packages with clean `__init__.py` facades.
- **Zero Circular Dependencies:** Dependency flow strictly follows: `models` $\rightarrow$ `ingestion` $\rightarrow$ `analysis` $\rightarrow$ `profiling` $\rightarrow$ `reporting` $\rightarrow$ `api` $\rightarrow$ `cli`.
- **Strict Typing:** All function arguments, return types, and class attributes must have strict type annotations. Pyright and mypy must pass with 0 errors.

---

## Development Environment Setup

DataPulse uses [`uv`](https://github.com/astral-sh/uv) for blazing-fast dependency management and virtual environments.

### Prerequisites

- Python 3.11, 3.12, 3.13, or 3.14
- `uv` (recommended) or `pip` + `venv`
- Git

### Cloning and Installing Dependencies

```bash
# Clone the repository
git clone https://github.com/Mr-Rup/DataPulse.git
cd DataPulse

# Create virtual environment and install all development dependencies
uv sync --all-extras
```

### Running the Test Suite

```bash
# Run all tests
uv run pytest

# Run with verbose output and coverage
uv run pytest -v

# Run a specific test module
uv run pytest tests/analysis/test_quality_rules.py
```

### Code Formatting and Linting

```bash
# Lint check with Ruff
uv run ruff check .

# Auto-fix linting issues where possible
uv run ruff check --fix .

# Strict type check with Pyright
uv run pyright

# Test package build
uv build
```

---

## Codebase Map

DataPulse is structured into modular components:

```text
src/datapulse/
├── analysis/               # Semantic role classification & quality rules
│   ├── column_classifier/  # Heuristics (numeric, strings, hints, engine)
│   ├── quality_rules/      # Modular audit rules (completeness, domain, temporal)
│   └── relationships.py    # Pairwise Pearson/Spearman & key viability
├── cli/                    # Typer CLI application & command dispatchers
│   ├── commands/           # Modular subcommands (analyze, show, column, query, info)
│   └── app.py              # Root Typer application setup & routing
├── ingestion/              # Delimiter sniffing & zero-copy readers
├── models/                 # Pydantic & dataclass report schemas
├── profiling/              # Parallel single-pass statistical profilers
├── reporting/              # Multi-format report delivery engines
│   ├── html/               # Interactive dark-mode dashboard generator
│   ├── terminal/           # Rich tables, section dispatchers & query views
│   └── json_exporter.py    # Schema-versioned JSON pipeline exporter
├── api.py                  # High-level analyze() orchestrator
└── config.py               # Pydantic v2 configuration models
```

---

## Adding a Quality Rule

Quality rules detect anomalies, data leakage, domain violations, and integrity issues.

### Rule Locations

Quality rules are organized by domain in `src/datapulse/analysis/quality_rules/`:

| File | Category | Example Rules |
|---|---|---|
| `completeness.py` | Missingness & redundancy | Null thresholds, duplicate rows, constant columns |
| `constraints.py` | Value ranges & outliers | Negative values, Tukey IQR outliers |
| `temporal.py` | Time series & ordering | Chronological inversions (e.g. End < Start) |
| `constants.py` | Keyword registries | Domain keywords, chronology sequence pairs |

### Step-by-Step Implementation

#### 1. Define the Check Function

Add your audit function in the appropriate module (or create a new module in `src/datapulse/analysis/quality_rules/`). Return a list of `Finding` objects:

```python
# src/datapulse/analysis/quality_rules/constraints.py
import polars as pl
from datapulse.models.report import ColumnProfile, Finding


def check_percentage_bounds(columns: list[ColumnProfile]) -> list[Finding]:
    """Check that percentage columns do not exceed 100% or fall below 0%."""
    findings: list[Finding] = []
    percentage_keywords = ("pct", "percentage", "rate", "ratio")
    
    for col in columns:
        col_lower = col.column_name.lower()
        if any(kw in col_lower for kw in percentage_keywords):
            if col.numeric_profile and col.numeric_profile.max is not None:
                if col.numeric_profile.max > 100.0:
                    findings.append(
                        Finding(
                            severity="warning",
                            title=f"Out-of-Bounds Percentage: {col.column_name}",
                            detail=(
                                f"Column '{col.column_name}' appears to be a percentage "
                                f"but has a maximum value of {col.numeric_profile.max:.2f} (> 100)."
                            ),
                            affected_columns=[col.column_name],
                        )
                    )
    return findings
```

#### 2. Register in the Evaluator

Wire your rule into `src/datapulse/analysis/quality_rules/evaluator.py`:

```python
# In src/datapulse/analysis/quality_rules/evaluator.py
from datapulse.analysis.quality_rules.constraints import (
    check_negative_values,
    check_numeric_outliers,
    check_percentage_bounds,  # <-- Import new rule
)

def evaluate_quality_rules(...) -> list[Finding]:
    # ...
    findings.extend(check_percentage_bounds(columns))
    # ...
```

#### 3. Export in `__init__.py`

Add the function to `src/datapulse/analysis/quality_rules/__init__.py`:

```python
from datapulse.analysis.quality_rules.constraints import (
    check_negative_values,
    check_numeric_outliers,
    check_percentage_bounds,
)

__all__ = [
    # ...
    "check_percentage_bounds",
]
```

#### 4. Add Unit Tests

Create comprehensive tests in `tests/analysis/test_quality_rules.py`:

```python
def test_check_percentage_bounds():
    # Setup mock ColumnProfile and verify warning is emitted
    # ...
```

---

## Adding a Semantic Column Role

Semantic roles categorize physical Polars types (`i64`, `f64`, `str`) into analytical roles (`numeric`, `categorical`, `temporal`, `text`, `boolean`, `identifier`, `constant`, `other`).

### Step-by-Step Implementation

#### 1. Define the Role in Models

If introducing a brand new role, add it to `ColumnClassification` in `src/datapulse/analysis/column_classifier/models.py`:

```python
@dataclass
class ColumnClassification:
    column_name: str
    inferred_role: str  # e.g., "geo_coordinate", "json_blob"
    confidence: float
    physical_type: str
    reason: str
```

#### 2. Add Heuristics in the Classifier Package

Depending on the physical type of the column:

- For string/text series: edit `src/datapulse/analysis/column_classifier/string_rules.py`
- For numeric series: edit `src/datapulse/analysis/column_classifier/numeric_rules.py`
- For column name keywords: add patterns to `src/datapulse/analysis/column_classifier/hints.py`

Example keyword heuristic:

```python
# In src/datapulse/analysis/column_classifier/hints.py
GEO_NAME_HINTS: tuple[str, ...] = (
    "latitude",
    "longitude",
    "lat",
    "lon",
    "lng",
    "coord",
    "coordinates",
)
```

#### 3. Add Role-Specific Statistical Profiler

If the role requires specialized metrics, create or extend a profiler in `src/datapulse/profiling/`:

```python
# Create src/datapulse/profiling/geo.py
import polars as pl
from datapulse.models.report import GeoProfile


def profile_geo_column(series: pl.Series) -> GeoProfile:
    # Compute bounding boxes, valid coordinate percentages, etc.
    # ...
```

#### 4. Add Renderers

1. **Terminal:** Add a table renderer function in `src/datapulse/reporting/terminal/roles.py` and register it in `src/datapulse/reporting/terminal/formatter.py`.
2. **HTML:** Add a card or table row component in `src/datapulse/reporting/html/components.py`.

#### 5. Verify Invariants

Run invariant and classification tests to ensure existing role predictions are not degraded:

```bash
uv run pytest tests/analysis/test_column_classifier.py tests/test_invariants.py
```

---

## Adding a File Reader / Ingestion Format

DataPulse supports `.csv`, `.tsv`, `.parquet`, `.json`, `.jsonl`, `.ndjson`, and `.xlsx`.

### Step-by-Step Implementation

#### 1. Update Supported Extensions

In `src/datapulse/ingestion/readers.py`:

```python
SUPPORTED_EXTENSIONS: tuple[str, ...] = (
    ".csv",
    ".tsv",
    ".parquet",
    ".json",
    ".jsonl",
    ".ndjson",
    ".xlsx",
    ".feather",  # <-- Add new extension
    ".arrow",
)
```

#### 2. Implement Zero-Copy Lazy Scan

In `src/datapulse/ingestion/readers.py`, add the lazy scanning branch:

```python
elif ext in (".feather", ".arrow"):
    # Use native Polars IPC scanner for zero-copy loading
    lazy_df = pl.scan_ipc(source_path)
    file_format = "arrow_ipc"
```

#### 3. Add Unit Tests

Add test cases in `tests/ingestion/test_readers.py` verifying:
- Correct extension detection
- In-memory schema inference
- Error handling on corrupt or empty files

---

## Adding a CLI Command

DataPulse uses [Typer](https://typer.tiangolo.com/) with modular command files in `src/datapulse/cli/commands/`.

### Step-by-Step Implementation

#### 1. Create Command Module

Create a new file in `src/datapulse/cli/commands/my_command.py`:

```python
# =========================================================================
# DataPulse Sample Subcommand
# Short description of what this command accomplishes.
# =========================================================================

from pathlib import Path
import typer
from datapulse.ingestion.readers import read_source
from datapulse.reporting.terminal.console import console

# =========================================================================
# COMMAND HANDLER
# =========================================================================

def run_sample(
    file_path: Path = typer.Argument(
        ...,
        help="Path to tabular data file.",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    threshold: float = typer.Option(
        0.05,
        "--threshold",
        "-t",
        help="Custom sensitivity threshold.",
    ),
) -> None:
    """Run sample analysis on the target dataset."""
    lazy_df, source_info = read_source(file_path)
    console.print(f"[bold green]Audited file:[/] {source_info.file_path}")
```

#### 2. Register with Typer Application

Register the subcommand in `src/datapulse/cli/app.py`:

```python
from datapulse.cli.commands.my_command import run_sample

app.command(
    name="sample",
    help="Run sample analysis on a dataset.",
)(run_sample)
```

#### 3. Add CLI Test

Verify options, exits, and help texts in `tests/cli/test_app.py`:

```python
def test_sample_command(runner, realistic_csv_path):
    result = runner.invoke(app, ["sample", str(realistic_csv_path)])
    assert result.exit_code == 0
    assert "Audited file" in result.stdout
```

---

## Adding a Report Exporter

DataPulse currently delivers reports via Terminal (Rich), HTML (self-contained dark theme), and JSON.

### Step-by-Step Implementation

#### 1. Implement Exporter Module

Create `src/datapulse/reporting/markdown_exporter.py`:

```python
# =========================================================================
# DataPulse Markdown Exporter
# Generates GitHub-flavored markdown summary reports.
# =========================================================================

from pathlib import Path
from datapulse.models.report import DatasetReport

# =========================================================================
# EXPORTER LOGIC
# =========================================================================

def export_markdown(report: DatasetReport, output_path: Path | str) -> Path:
    """Generate and write a GFM Markdown report."""
    target = Path(output_path)
    lines: list[str] = [
        f"# DataPulse Report: {report.metadata.file_name}",
        f"- **Rows:** {report.overview.total_rows:,}",
        f"- **Columns:** {report.overview.total_columns}",
        f"- **Memory:** {report.overview.memory_estimate_bytes / (1024 * 1024):.2f} MB",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
```

#### 2. Wire into High-Level `analyze()` Orchestrator

In `src/datapulse/api.py`, support the new format in `export_format` and `output_path`:

```python
# In src/datapulse/api.py
if output_path:
    if target_format == "markdown":
        export_markdown(report, output_path)
```

#### 3. Wire into CLI Options

In `src/datapulse/cli/commands/analyze.py`, enable `--markdown` / `-o report.md` auto-detection.

---

## Code Style & Formatting Guidelines

All contributions must follow these conventions:

### Section Banners

Use standardized comment banners with pure descriptive titles (no numbers):

```python
# =========================================================================
# PRIMARY SECTION TITLE
# =========================================================================

# -------------------------------------------------------------------------
# Subsection Divider
# -------------------------------------------------------------------------
```

### Spacing Rules

- **1 blank line gap** immediately after a banner before a class or function definition.
- **2 blank lines gap** between top-level functions and classes.
- **0 internal blank line gaps** within the execution logic of a function or method.
- **88-character line limit** enforced by Ruff.

### Git Commits & PRs

Follow Conventional Commits:

| Prefix | Usage | Example |
|---|---|---|
| `feat:` | New features or extensions | `feat(rules): add percentage range validation rule` |
| `fix:` | Bug fixes | `fix(readers): correct UTF-8 lossy line truncation` |
| `refactor:` | Code restructuring without logic change | `refactor(terminal): decompose section view handlers` |
| `test:` | New or updated test suites | `test(classifier): add tests for float ID detection` |
| `docs:` | Documentation improvements | `docs(contributing): add developer guide for quality rules` |

---

## Pre-Push Quality Checklist

Before submitting a Pull Request, run the complete verification suite:

- [ ] All tests pass: `uv run pytest`
- [ ] No linter warnings: `uv run ruff check .`
- [ ] No typing issues: `uv run pyright`
- [ ] Package builds cleanly: `uv build`
- [ ] No circular imports introduced between packages
- [ ] No eager Pandas dependencies or conversions added
- [ ] Documentation updated to reflect new CLI flags or configuration parameters
