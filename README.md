<div align="center">

# ⚡ DataPulse

**Blazing-fast automated exploratory data analysis (EDA) toolkit for tabular datasets, powered solely by Polars.**

[![CI](https://img.shields.io/badge/CI-Passing-success?style=flat&logo=github)](https://github.com/Mr-Rup/DataPulse)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Polars](https://img.shields.io/badge/Polars-100%25%20Pure%20Engine-CD792C?style=flat&logo=polars&logoColor=white)](https://pola.rs/)
[![Zero Pandas](https://img.shields.io/badge/Pandas%20Overhead-0%25-green?style=flat)](#pure-polars-architecture)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat)](#license)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg?style=flat)](https://github.com/astral-sh/ruff)

</div>

> Profile millions of tabular rows in milliseconds. Generates role-specific descriptive statistics, automated data quality anomalies, multicollinearity warnings, interactive dark-mode HTML dashboards, and machine-readable JSON pipelines—with zero external CDN dependencies and zero Pandas overhead.

---

## 🚀 Pure Polars Architecture (0% Pandas Overhead)

DataPulse is built **solely on Polars** and Rust-native multi-threading:
- **Zero Pandas Dependency:** 100% free of legacy Pandas bottlenecks, eager single-threaded loops, and memory copies.
- **Zero-Copy Streaming:** Queries, scans, and profiles run directly on Polars `LazyFrame` expression graphs without full memory duplication.
- **Unified Missingness Audit:** Simultaneously audits nulls, IEEE 754 float `NaN`s, empty strings (`""`), and domain sentinel tokens (`"?"`, `"-999"`, `"N/A"`).
- **Embedded In-Terminal SQL:** Direct dataset filtering and SQL querying powered by native Polars `SQLContext`.

---

## 🏛️ Pipeline Architecture

```
Raw Tabular Dataset (.parquet, .csv, .json, .xlsx, Polars DataFrame)
                            │
                            ▼
            Zero-Copy Ingestion & Sniffing
          (Polars Lazy Engine | Delimiter & EOL Sniffer)
                            │
                            ▼
           Parallel Single-Pass Column Profiler
      (Nulls | NaNs | Empty Strings | Sentinel Values)
                            │
                            ▼
          Semantic Role Inference & Classification
  (Numeric | Categorical | Temporal | Text | Boolean | Identifier)
                            │
                            ▼
        Statistical Quality & Anomaly Engine
  (Tukey IQR Outliers | Inversions | Duplicates | Collinearity)
                            │
                            ▼
              Unified Multi-Format Delivery
  ┌─────────────────────────┼─────────────────────────┐
  ▼                         ▼                         ▼
Terminal UI           HTML Dashboard            JSON Stream
(Rich Tables & Grids)  (Standalone Dark Theme)   (Pydantic / Dict)
```

---

## ⚡ Key Features

- **Multi-Format Ingestion:** Zero-overhead streaming ingestion for Apache Parquet (`.parquet`), CSV/TSV (`.csv`, `.tsv`), JSON/NDJSON (`.json`, `.ndjson`, `.jsonl`), Excel (`.xlsx`, `.xls`), and in-memory Polars `DataFrame` / `LazyFrame` objects.
- **Smart Delimiter Sniffing:** Automatically detects field delimiters (`,`, `\t`, `;`, `|`) and line terminators (`\r\n`, `\n`, `\r`) from leading byte samples.
- **Semantic Role Classification:** Disambiguates physical data types into 8 analytical roles (`numeric`, `categorical`, `temporal`, `boolean`, `text`, `identifier`, `constant`, and `other`).
- **Deep Statistical Metrics:**
  - *Numeric:* Mean, std dev, min, 25%, median (50%), 75%, max, IQR, zero counts, negative counts, skewness.
  - *Categorical:* Distinct counts, cardinality ratio, mode value, top N frequency distribution.
  - *Temporal:* Earliest/latest timestamps, duration span (days/seconds), unique timestamps.
  - *Text:* Min, max, mean, and median character lengths, empty string counts.
  - *Boolean:* True/False counts and percentage distributions.
  - *Identifier:* Uniqueness ratio, duplicate count, primary key viability.
- **Automated Data Quality & Anomaly Rules:**
  - Full-row duplicate row detection.
  - Missingness severity tiers (moderate > 10%, critical > 50%).
  - Tukey 1.5x IQR outlier boundary identification.
  - Domain violations (negative fares, prices, or ages in non-negative columns).
  - Chronological inversions (end timestamps occurring before start timestamps).
- **Multicollinearity & Key Discovery:**
  - Parallel pairwise correlation calculation (Pearson and Spearman).
  - Severe collinearity warnings ($|r| \ge 0.90$) to catch data leakage and redundancy.
  - Automated primary key discovery (100% uniqueness, zero missing values).
- **Multi-Format Output:**
  - **Terminal:** Interactive Rich tables, severity badges, and metric cards. Default view presents 5–6 essential features; full reports accessible via `--all`.
  - **HTML:** Standalone, single-file dashboard with instant client-side column search filter and zero CDN dependencies.
  - **JSON:** Fully structured, validated JSON export for downstream data pipelines and CI/CD gates.

---

## 📦 Installation & Setup

DataPulse is optimized for [**`uv`**](https://github.com/astral-sh/uv)—the ultra-fast Python package installer and resolver.

### 1. Install `uv` (Recommended)
If you do not have `uv` installed, get it in seconds:

- **Windows (PowerShell):**
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **macOS / Linux:**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
> For additional installation options, visit the [official uv GitHub repository](https://github.com/astral-sh/uv).

### 2. Install DataPulse

#### Add to an Existing Project
```bash
# Using uv (Recommended)
uv add git+https://github.com/Mr-Rup/DataPulse.git

# Using standard pip
pip install git+https://github.com/Mr-Rup/DataPulse.git
```

#### Install as a Standalone Global CLI
```bash
# Using uv tool
uv tool install git+https://github.com/Mr-Rup/DataPulse.git

# Using pip
pip install git+https://github.com/Mr-Rup/DataPulse.git
```

#### Zero-Installation Instant Run (`uvx`)
Profile any dataset directly without installing anything into your global or local environment:
```bash
uvx --from git+https://github.com/Mr-Rup/DataPulse.git datapulse data/dataset.csv --html
```

#### Local Development Setup
```bash
git clone https://github.com/Mr-Rup/DataPulse.git
cd DataPulse

# Sync virtual environment with uv
uv sync

# Run test suite
uv run pytest
```

---

## 💻 Core CLI Commands

DataPulse adheres to a uniform command syntax:
```bash
datapulse <command> <file> [target/column/section] [options]
```

Here are the 5 core commands for day-to-day data engineering and analysis:

### 1. Automated Profile & Analysis (`analyze`)
```bash
# Clean default terminal overview (5-6 core features)
datapulse data.csv

# Comprehensive full report across all sections
datapulse data.csv --all

# Export interactive HTML dashboard
datapulse data.csv --html -o reports/audit.html
```

### 2. Section Deep-Dive (`show`)
```bash
# Inspect specific analytical section (quality, numeric, missing, schema, etc.)
datapulse show data.csv quality

# Filter section display to specific columns
datapulse show data.csv numeric --columns amount,tax,total
```

### 3. Single Column Profile (`column`)
```bash
# Exhaustive statistical breakdown for an individual column
datapulse column data.csv fare_amount
```

### 4. Interactive SQL & In-Terminal Querying (`query`)
```bash
# Execute direct SQL via Polars SQLContext
datapulse query data.csv "SELECT * FROM self WHERE fare_amount < 0"

# Filter by column threshold
datapulse query data.csv age --gt 30 --limit 20
```

### 5. Instant File Metadata & Schema (`info`)
```bash
# Lightweight inspection of row count, size, and Polars types without full profiling
datapulse info data.parquet
```

> 📖 **Full Command Reference:**  
> For complete syntax, all available options, filtering parameters, and examples, see the [CLI Reference Manual (docs/CLI_REFERENCE.md)](docs/CLI_REFERENCE.md).

---

## 🐍 In-Code Python SDK (`import datapulse as dp`)

Integrate DataPulse directly into your Python pipelines and Jupyter notebooks:

### The One-Liner
```python
import datapulse as dp

# Profile file and save dashboard in a single line
dp.analyze("sales.csv").save_html("sales_report.html")
```

### In-Memory Polars DataFrame (Zero Disk Reload)
```python
import polars as pl
import datapulse as dp

# Profile an existing in-memory DataFrame directly
df = pl.read_parquet("transactions.parquet")
report = dp.analyze(df)

print(f"Total Rows: {report.summary.row_count}")
print(f"Columns: {report.summary.column_count}")
```

### Strongly-Typed Configuration
```python
import datapulse as dp

# Configure analysis rules programmatically
config = dp.AnalysisConfig(
    max_categories=15,
    compute_correlations=True,
    min_correlation=0.65,
    correlation_method="pearson",
    missing_sentinels=["?", "N/A", "MISSING", "-999"],
    allowed_negative_columns=["temperature_celsius"],
    non_negative_columns=["unit_price", "quantity"],
)

report = dp.analyze("inventory.parquet", config=config)
report.save_html("inventory_audit.html")
```

### Inspect Metrics & Programmatic Export
```python
import datapulse as dp

report = dp.analyze("customers.csv")

# 1. Access high-level summary & missingness
summary = report.summary
missing_gaps = report.missing_values

# 2. Iterate through column profiles
for col in report.columns:
    print(f"{col.name} ({col.inferred_role}): {col.unique_count} distinct values")

# 3. Access automated data quality findings
for finding in report.findings:
    print(f"[{finding.severity.upper()}] {finding.title}: {finding.description}")

# 4. Export to Python dictionary or JSON string
data_dict = report.to_dict()
json_str = report.to_json(indent=2)
```

---

## ⚙️ Configuration Reference (`datapulse_config.toml`)

DataPulse configurations use Pydantic v2 with strict typo and extra-key detection:

```toml
# Statistical & Categorical Profiling
max_categories = 20
compute_correlations = true
correlation_method = "pearson"
min_correlation = 0.50
max_correlation_columns = 30

# Unified Missingness Sentinels
missing_sentinels = ["?", "NA", "N/A", "MISSING", "-999", "null", "None"]

# Explicit Column Role Overrides
[column_roles]
user_id = "identifier"
status_code = "categorical"
is_active = "boolean"

# Quality Rules & Domain Constraints
allowed_negative_columns = ["net_balance", "temperature"]
non_negative_columns = ["price", "quantity", "distance", "fare_amount"]

# Privacy Settings
include_full_path = false
```

---

## 📂 Project Structure

```
DataPulse/
│
├── docs/                       # Comprehensive documentation
│   ├── ARCHITECTURE.md         # Polars engine design & pipeline internals
│   ├── CLI_REFERENCE.md        # Complete CLI manual & flag options
│   ├── PYTHON_API.md           # Python SDK usage & report models
│   ├── CONFIGURATION.md        # Configuration schema & sample files
│   └── DECISIONS.md            # Architecture Decision Records (ADR log)
│
├── src/datapulse/              # Core library source code
│   ├── analysis/               # Role classification, correlations, quality rules
│   ├── cli/                    # Typer command-line application & commands
│   │   ├── commands/           # Modular subcommands (analyze, show, column, query, info)
│   │   └── app.py              # Application setup & default routing
│   ├── ingestion/              # Delimiter sniffing & zero-copy readers
│   ├── models/                 # Report schemas & metadata dataclasses
│   ├── profiling/              # Parallel single-pass statistical profilers
│   ├── reporting/              # Terminal (Rich), HTML, and JSON exporters
│   ├── api.py                  # High-level analyze() orchestrator
│   └── config.py               # Pydantic v2 configuration models
│
├── tests/                      # Consolidated scenario test suite
│   ├── analysis/               # Classifier, correlation, and quality rules tests
│   ├── cli/                    # Typer CLI commands, subcommands, and flags
│   ├── ingestion/              # Readers, format sniffing, and lazy loaders
│   ├── models/                 # Report models and serialization tests
│   ├── profiling/              # Profilers, scale, and sentinel tests
│   ├── reporting/              # HTML template and JSON export tests
│   ├── test_api.py             # Public API end-to-end integration tests
│   ├── test_edge_cases.py      # Malformed inputs, empty frames, and type errors
│   └── test_invariants.py      # Mathematical consistency & schema invariants
│
├── pyproject.toml              # Build system, dependencies, and tooling configs
├── README.md                   # Project documentation & quick start
└── LICENSE                     # MIT License
```

---

## 📚 In-Depth Documentation

For detailed technical specifications and API references:

- [Architecture & Internal Engine](docs/ARCHITECTURE.md)
- [Command-Line Interface (CLI) Manual](docs/CLI_REFERENCE.md)
- [Python API & SDK Reference](docs/PYTHON_API.md)
- [Configuration Schema & Reference](docs/CONFIGURATION.md)
- [Architecture Decision Records (ADRs)](docs/DECISIONS.md)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
