# DataPulse

An automated exploratory data analysis (EDA) toolkit for tabular datasets, powered by Polars.

DataPulse inspects tabular data, infers analytical column roles, generates role-specific descriptive statistics, identifies data-quality anomalies, evaluates pairwise correlations, and produces standalone HTML, JSON, or terminal reports in milliseconds.

---

## Key Features

- **Blistering Performance:** Built directly on Polars lazy execution and Rust multi-threading. Profiles millions of rows in seconds (~1,000,000+ rows/second).
- **Multi-Format Ingestion:** Native, zero-overhead ingestion for:
  - Apache Parquet (`.parquet`)
  - Delimited text / CSV (`.csv`, `.tsv`, `.txt`) with custom delimiters
  - JSON & Newline-delimited JSON (`.json`, `.ndjson`, `.jsonl`)
  - Excel workbooks (`.xlsx`, `.xls`) with sheet selection
- **Heuristic Role Classification:** Classifies physical types into semantic analytical roles:
  - `numeric`, `categorical`, `temporal`, `boolean`, `text`, `identifier`, `constant`, and `other`.
  - Disambiguates low-cardinality coded integers (e.g., status flags, payment codes) from continuous variables.
  - Distinguishes freeform string text from categorical labels based on token length.
- **Deep Role-Specific Profiling:**
  - *Numeric:* mean, standard deviation, min, 25%, median (50%), 75%, max, IQR, zero counts, negative counts, skewness.
  - *Categorical:* distinct count, cardinality percentage, mode, bounded top category frequencies.
  - *Temporal:* minimum/maximum dates, temporal span (days, seconds), unique timestamps.
  - *Text:* minimum, maximum, mean, and median character lengths, empty counts.
  - *Boolean:* true/false counts and percentage distributions.
  - *Identifier:* uniqueness percentage, duplicate count, key candidate viability.
- **Automated Data Quality & Anomaly Rules:**
  - Severe and moderate missingness alerts.
  - Full-row duplicate detection.
  - Zero-variance / constant column warnings.
  - High-cardinality categorical warnings.
  - Domain anomaly detection (unexpected negative fares, prices, or counts).
  - Tukey 1.5x IQR statistical outlier boundary detection.
  - Chronological inversion checks (e.g., end timestamps occurring before start timestamps).
- **Relationships & Key Candidate Analysis:**
  - Parallel pairwise correlation calculation (Pearson and Spearman).
  - High collinearity warnings (|r| >= 0.90) to detect data leakage or redundancy.
  - Automated primary key candidate discovery (100% unique, zero nulls).
- **Multi-Format Reporting:**
  - **Terminal:** Rich interactive tables with styled panels, severity badges, and metric grids.
  - **HTML:** Standalone, self-contained single-file reports featuring a sleek modern dark theme, real-time client-side column search filter, and zero external CDN dependencies.
  - **JSON:** Fully structured, schema-validated JSON export for downstream data pipelines.

---

## Installation

Ensure you have Python 3.14+ and `uv` installed:

```bash
# Clone the repository
git clone https://github.com/Mr-Rup/DataPulse.git
cd DataPulse

# Sync dependencies
uv sync
```

---

## Command-Line Interface (CLI)

DataPulse includes a complete Typer-based command-line tool.

### Basic Analysis

```bash
# Terminal summary report
uv run datapulse analyze data/dataset.parquet

# Generate self-contained HTML report
uv run datapulse analyze data/dataset.csv --format html -o reports/dataset.html

# Stream structured JSON to stdout
uv run datapulse analyze data/dataset.json --format json
```

### Sampling Large Datasets

For massive datasets, profile with instant head or random sampling:

```bash
# Fast first 100,000 rows
uv run datapulse analyze data/large_file.parquet --sample 100000

# Random 50,000 rows with deterministic seed
uv run datapulse analyze data/large_file.parquet --sample 50000 --sample-method random
```

### CLI Options

| Flag | Short | Description | Default |
|---|---|---|---|
| `--format` | `-f` | Output report format: `terminal`, `html`, or `json` | `terminal` |
| `--output` | `-o` | Output file destination path | `None` |
| `--sample` | `-s` | Limit analysis to N rows | `None` (full) |
| `--sample-method` | | Sampling mode: `head` or `random` | `head` |
| `--config` | `-c` | Path to configuration file (`.json` or `.toml`) | `None` |
| `--max-categories` | | Maximum category frequencies to track | `20` |
| `--correlations / --no-correlations` | | Toggle pairwise correlation computation | `True` |
| `--sheet-name` | | Excel worksheet name | `None` |
| `--separator` | | Delimiter character for CSV files | `None` |
| `--quiet` | `-q` | Suppress terminal printout when exporting | `False` |

---

## Python API Usage

DataPulse can be imported and executed programmatically within any Python script or notebook.

```python
from pathlib import Path
from datapulse import analyze, AnalysisConfig

# 1. Quick analysis with defaults
report = analyze("data/sales.parquet")

print(f"Total Rows: {report.summary.row_count:,}")
print(f"Total Columns: {report.summary.column_count}")
print(f"Findings: {len(report.findings)}")

# 2. Export reports
report.save_html("reports/sales_report.html")
report.save_json("reports/sales_report.json")

# 3. Custom configuration
config = AnalysisConfig(
    sample_size=250_000,
    sample_method="head",
    max_categories=10,
    compute_correlations=True,
    correlation_method="pearson",
    min_correlation=0.60,
)

custom_report = analyze("data/transactions.csv", config=config)
```

### Loading Configuration Files

Configuration can be specified in `.toml` or `.json` files:

```toml
# datapulse.toml
[datapulse]
max_categories = 15
sample_size = 100000
compute_correlations = true
min_correlation = 0.50
```

```python
from datapulse import analyze, load_config

config = load_config("datapulse.toml")
report = analyze("data/transactions.csv", config=config)
```

---

## Performance & Scale

Benchmarked on official NYC Taxi & Limousine Commission (TLC) Parquet datasets on commodity hardware:

| Dataset | Rows | Columns | Mode | Elapsed Time | Throughput |
|---|---|---|---|---|---|
| `taxi_zone_lookup.csv` | 265 | 4 | Full dataset | 0.007s | ~38,000 rows/s |
| `yellow_tripdata.parquet` | 10,000 | 20 | Sampled 10k | 0.031s | ~321,000 rows/s |
| `yellow_tripdata.parquet` | 100,000 | 20 | Sampled 100k | 0.084s | ~1,195,000 rows/s |
| `yellow_tripdata.parquet` | 1,000,000 | 20 | Sampled 1M | 0.956s | ~1,045,000 rows/s |
| `yellow_tripdata.parquet` | 3,475,226 | 20 | Full 3.475M | 3.778s | ~920,000 rows/s |

---

## Development & Testing

```bash
# Run complete test suite (85 tests)
uv run pytest

# Check linting and formatting rules
uv run ruff check .

# Type checking
uv run pyright
```

---

## License

MIT License.
