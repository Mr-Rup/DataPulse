# DataPulse Python API & SDK Reference

Complete programmatic reference for integrating DataPulse into Python scripts, analytics pipelines, and Jupyter notebooks.

---

## The Core Import Idiom

```python
import datapulse as dp
```

Similar to `import polars as pl` and `import pandas as pd`, `dp` provides a concise, recognizable 2-letter namespace.

---

## High-Level Function: `dp.analyze()`

```python
dp.analyze(
    file_path: str | Path | pl.DataFrame | pl.LazyFrame,
    config: dp.AnalysisConfig | str | Path | None = None,
) -> dp.AnalysisReport
```

Executes the complete profiling pipeline: ingestion, missingness auditing, semantic role classification, statistical profiling, correlation evaluation, and quality rule auditing.

### Parameters

- **`file_path`** (`str | Path | pl.DataFrame | pl.LazyFrame`):  
  Path to a supported tabular file on disk, or an in-memory Polars `DataFrame` / `LazyFrame`.
- **`config`** (`dp.AnalysisConfig | str | Path | None`, optional):  
  Configuration controlling profiling behavior. Can be:
  - An instance of `dp.AnalysisConfig`.
  - A `str` or `Path` pointing to a `.toml` or `.json` configuration file.
  - `None` (uses defaults).

### Returns

- **`AnalysisReport`**: A populated report model containing summaries, column profiles, findings, warnings, and correlations.

---

## Common Code Patterns

### 1. One-Liner HTML Generation
```python
import datapulse as dp

# Profile file and save interactive HTML dashboard in a single line
dp.analyze("sales_data.csv").save_html("sales_report.html")
```

### 2. In-Memory Polars DataFrame Analysis
```python
import polars as pl
import datapulse as dp

# Create or load DataFrame in memory
df = pl.DataFrame({
    "user_id": [101, 102, 103, 104],
    "amount": [120.50, 45.00, 300.00, 89.90],
    "status": ["active", "pending", "active", "cancelled"],
})

# Profile directly from memory without reloading disk files
report = dp.analyze(df)
print(f"Rows: {report.summary.row_count}, Columns: {report.summary.column_count}")
```

### 3. Load Configuration from File
```python
import datapulse as dp

# Pass path to TOML or JSON config file directly
report = dp.analyze("transactions.parquet", config="config/audit_rules.toml")
```

### 4. Custom Strongly-Typed Configuration
```python
import datapulse as dp

# Configure analysis rules programmatically
config = dp.AnalysisConfig(
    max_categories=15,
    compute_correlations=True,
    min_correlation=0.70,
    correlation_method="spearman",
    missing_sentinels=["N/A", "MISSING", "-999", "NULL"],
    allowed_negative_columns=["temperature_celsius"],
)

report = dp.analyze("sensor_readings.csv", config=config)
report.save_html("sensor_audit.html")
```

### 5. Accessing Structured Metrics Programmatically
```python
import datapulse as dp

report = dp.analyze("data/customers.parquet")

# 1. Access high-level summary
print(report.summary.row_count)
print(report.summary.column_count)
print(report.summary.schema)

# 2. Inspect missingness breakdown
for m in report.missing_values:
    if m.total_missing_count > 0:
        print(f"{m.column}: {m.total_missing_count} missing ({m.missing_percentage:.1f}%)")

# 3. Inspect column profiles
for col in report.columns:
    print(f"Column: {col.name} | Role: {col.inferred_role} | Confidence: {col.confidence:.2f}")
    if col.inferred_role == "numeric":
        print(f"  Mean: {col.statistics.mean}, Min: {col.statistics.min}, Max: {col.statistics.max}")

# 4. Inspect data quality findings and warnings
for finding in report.findings:
    print(f"[{finding.severity.upper()}] {finding.title}: {finding.description}")

# 5. Export to dict or JSON
data_dict = report.to_dict()
json_string = report.to_json(indent=2)
```

---

## Report Export & Interactive Methods

| Method | Return Type | Description |
| :--- | :--- | :--- |
| `report.to_dict()` | `dict[str, Any]` | Converts the report into a pure Python dictionary. |
| `report.to_json(indent=2)` | `str` | Serializes the report into a formatted JSON string. |
| `report.to_html()` | `str` | Returns the self-contained HTML dashboard as an in-memory string. |
| `report._repr_html_()` | `str` | Automatic interactive HTML dashboard rendering in Jupyter Notebooks. |
| `report.save_html(path)` | `Path` | Writes self-contained standalone HTML report to disk. |
| `report.save_json(path, indent=2)` | `Path` | Writes formatted JSON report to disk. |

---

## Standalone Exporters

DataPulse also exports top-level renderer functions:

```python
from datapulse import export_html, export_json

html_path = export_html(report, "reports/audit.html")
json_path = export_json(report, "reports/audit.json", indent=2)
```

---

## Domain Exceptions

DataPulse provides a strongly-typed exception hierarchy so client applications can handle specific failure modes cleanly:

```python
import datapulse as dp

try:
    report = dp.analyze("corrupt_or_unsupported.xyz")
except dp.UnsupportedFormatError as err:
    print(f"Format not supported: {err}")
except dp.IngestionError as err:
    print(f"Failed to ingest dataset: {err}")
except dp.ConfigurationError as err:
    print(f"Invalid analysis configuration: {err}")
except dp.DataPulseError as err:
    print(f"DataPulse error: {err}")
```
