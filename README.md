<div align="center">

# ⚡ DataPulse

**Blazing-fast automated exploratory data analysis (EDA) toolkit for tabular datasets, powered by Polars.**

[![CI](https://img.shields.io/badge/CI-Passing-success?style=flat&logo=github)](https://github.com/Mr-Rup/DataPulse)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Polars](https://img.shields.io/badge/Polars-Fast%20DataFrame-CD792C?style=flat&logo=polars&logoColor=white)](https://pola.rs/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat)](#license)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg?style=flat)](https://github.com/astral-sh/ruff)

</div>

> Profile millions of tabular rows in milliseconds. Generates role-specific descriptive statistics, automated data quality anomalies, multicollinearity warnings, interactive dark-mode HTML dashboards, and machine-readable JSON pipelines—with zero external CDN dependencies.

---

## 🏛️ Architecture & Processing Pipeline

```
Raw Tabular Dataset (.parquet, .csv, .json, .xlsx, DataFrame)
                            |
                            v
            Zero-Copy Ingestion & Sniffing
          (Polars Lazy Engine | Delimiter & EOL Sniffer)
                            |
                            v
          Parallel Single-Pass Column Profiler
     (Nulls | NaNs | Empty Strings | Sentinel Values)
                            |
                            v
         Semantic Role Inference & Classification
 (Numeric | Categorical | Temporal | Text | Boolean | Identifier)
                            |
                            v
       Statistical Quality & Anomaly Engine
 (Tukey IQR Outliers | Inversions | Duplicates | Collinearity)
                            |
                            v
             Unified Multi-Format Delivery
 ┌──────────────────────────┼──────────────────────────┐
 ▼                          ▼                          ▼
Terminal UI           HTML Dashboard             JSON Stream
(Rich Tables & Grids)  (Standalone Dark Theme)   (Pydantic / Dict)
```

---

## 📊 Benchmark & Performance Comparison

Engineered from the ground up on Polars and Rust multi-threading to eliminate memory duplication and single-threaded bottlenecks:

| Metric | Traditional Pandas Profilers | DataPulse (Polars Engine) |
| :--- | :--- | :--- |
| **Throughput** | ~20,000 – 50,000 rows/sec | **~1,200,000+ rows/sec** |
| **Execution Model** | Eager full in-memory copy | **Zero-copy lazy frame expressions** |
| **Missingness Audit** | Nulls only | **Unified: Nulls + NaNs + Empty Strings + Sentinels** |
| **Correlations** | Single-threaded | **Vectorized multi-threaded (Pearson & Spearman)** |
| **HTML Report** | Heavy CDN bundles (breaks offline) | **100% self-contained, inline CSS/JS (Air-gapped ready)** |
| **Multicollinearity** | Manual review required | **Automated high collinearity warnings (|r| >= 0.90)** |

---

## 🚀 Key Features

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
  - **Terminal:** Interactive Rich tables, severity badges, and metric cards.
  - **HTML:** Standalone, single-file dashboard with instant client-side column search filter and zero CDN dependencies.
  - **JSON:** Fully structured, validated JSON export for downstream data pipelines and CI/CD gates.

---

## 📦 Installation & Setup

DataPulse supports both **`uv`** (recommended for blazing speed) and standard **`pip`**:

### Standalone Global CLI
```bash
# Using uv (Isolated global CLI)
uv tool install datapulse

# Using pip
pip install datapulse
```

### Add to an Existing Project
```bash
# Using uv
uv add datapulse

# Using pip
pip install datapulse
```

### Zero-Installation Superpower (`uvx`)
Profile any dataset instantly without installing anything into your environment:
```bash
uvx datapulse data/dataset.csv --html
```

### Local Development Setup
```bash
git clone https://github.com/Mr-Rup/DataPulse.git
cd DataPulse

# Sync virtual environment with uv
uv sync

# Run test suite
uv run pytest
```

---

## 💻 Command-Line Interface (CLI)

DataPulse is built with ergonomics in mind: commands are short, intuitive, and easy to remember across CMD, PowerShell, and Bash.

### 1. Quick Terminal Inspection
```bash
# Ultra-short root command (no verb needed)
datapulse data.csv

# Explicit subcommand
datapulse analyze data.parquet
```

### 2. Generate Interactive HTML Dashboard
```bash
# Instant HTML export (auto-creates data_report.html)
datapulse data.csv --html

# Custom destination (auto-detects HTML format from file extension!)
datapulse data.csv -o reports/audit_dashboard.html
```

### 3. Machine-Readable JSON Export
```bash
# Stream JSON directly to terminal or pipe to jq
datapulse data.csv --json | jq .summary

# Save JSON directly to file (auto-detects JSON from file extension!)
datapulse data.csv -o reports/metrics.json
```

### 4. Custom Configuration & Advanced Controls
```bash
# Load validation rules and sentinels from a TOML config file
datapulse data.parquet -c audit_config.toml

# Disable heavy correlations on wide datasets
datapulse data.csv --no-correlations

# Excel workbook with specific sheet
datapulse workbook.xlsx --sheet-name "Financials" --html

# Delimited file with custom separator
datapulse server_logs.tsv --separator "\t"
```

---

## 🐍 In-Code Python SDK (`import datapulse as dp`)

Integrate DataPulse seamlessly into Python scripts, analytics workflows, or Jupyter notebooks:

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

### Pass Config File Path Directly
```python
import datapulse as dp

# Pass path to TOML or JSON config file directly
report = dp.analyze("data.csv", config="config.toml")
```

### Strongly-Typed Custom Configuration
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
|
+-- docs/                       # Comprehensive documentation
|   +-- ARCHITECTURE.md         # Pipeline design & Polars engine details
|   +-- CLI_REFERENCE.md        # Complete CLI manual & flag options
|   +-- PYTHON_API.md           # Python SDK usage & report models
|   +-- CONFIGURATION.md        # Configuration schema & sample files
|   +-- DECISIONS.md            # Architecture Decision Records (ADR log)
|
+-- src/datapulse/              # Core library source code
|   +-- analysis/               # Role classification, correlations, quality rules
|   +-- cli/                    # Typer command-line application
|   +-- ingestion/              # Delimiter sniffing & zero-copy readers
|   +-- models/                 # Report schemas & metadata dataclasses
|   +-- profiling/              # Parallel single-pass statistical profilers
|   +-- reporting/              # Terminal (Rich), HTML, and JSON exporters
|   +-- api.py                  # High-level analyze() orchestrator
|   +-- config.py               # Pydantic v2 configuration models
|
+-- tests/                      # Consolidated scenario test suite
|   +-- analysis/               # Classifier, correlation, and quality rules tests
|   +-- cli/                    # Typer CLI commands, auto-detection, and flags
|   +-- ingestion/              # Readers, format sniffing, and lazy loaders
|   +-- models/                 # Report models and serialization tests
|   +-- profiling/              # Profilers, scale, and sentinel tests
|   +-- reporting/              # HTML template and JSON export tests
|   +-- test_api.py             # Public API end-to-end integration tests
|   +-- test_edge_cases.py      # Malformed inputs, empty frames, and type errors
|   +-- test_invariants.py      # Mathematical consistency & schema invariants
|
+-- scripts/                    # Utilities and performance benchmarks
|   +-- benchmark_datapulse.py  # Throughput & scale benchmark runner
|
+-- pyproject.toml              # Build system, dependencies, and tooling configs
+-- README.md                   # Project documentation & quick start
+-- LICENSE                     # MIT License
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
