# DataPulse Configuration Guide

DataPulse is powered by a strongly-typed, schema-validated configuration model built on Pydantic v2.

Configurations can be passed programmatically in Python (`dp.AnalysisConfig`), loaded from a `.toml` or `.json` file via CLI (`-c config.toml`), or passed directly to `dp.analyze(config="config.toml")`.

---

## Configuration Schema & Options

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `max_categories` | `int` | `20` | Maximum top category frequencies to track per column (>= 1). |
| `min_correlation` | `float` | `0.50` | Minimum absolute correlation threshold for reporting (|r| >= threshold, 0.0 to 1.0). |
| `compute_correlations` | `bool` | `True` | Whether to calculate pairwise correlations between numeric columns. |
| `correlation_method` | `str` | `"pearson"` | Correlation method: `"pearson"` or `"spearman"`. |
| `max_correlation_columns` | `int` | `30` | Maximum numeric columns to include in pairwise correlation matrix (prevents O(N^2) stalls on wide datasets). |
| `missing_sentinels` | `list[str]` | `["?"]` | String tokens treated as missing values in addition to nulls, NaNs, and empty strings. |
| `column_roles` | `dict[str, str]` | `{}` | Explicit role overrides for specific column names (e.g., `{"user_id": "identifier"}`). |
| `allowed_negative_columns` | `list[str]` | `[]` | Columns permitted to have negative values without triggering anomaly warnings (e.g., `["temperature", "profit_loss"]`). |
| `non_negative_columns` | `list[str]` | `[]` | Columns strictly flagged as critical domain errors if negative values occur (e.g., `["age", "fare_amount", "trip_distance"]`). |
| `sheet_name` | `str \| None` | `None` | Sheet name to read when profiling Excel workbooks (`.xlsx`, `.xls`). |
| `separator` | `str \| None` | `None` | Custom delimiter character for CSV/TSV text files. |
| `include_full_path` | `bool` | `False` | Whether to include the full resolved filesystem path in report metadata (defaults to `False` for privacy). |

---

## Sample TOML Configuration (`datapulse_config.toml`)

```toml
# =========================================================================
# DataPulse Production Audit Configuration
# =========================================================================

# Statistical Profiling
max_categories = 15
compute_correlations = true
correlation_method = "pearson"
min_correlation = 0.65
max_correlation_columns = 25

# Missingness & Sentinels
missing_sentinels = [
    "?",
    "NA",
    "N/A",
    "MISSING",
    "-999",
    "null",
    "None"
]

# Explicit Column Role Overrides
[column_roles]
account_id = "identifier"
status_code = "categorical"
is_verified = "boolean"

# Quality Rules & Domain Constraints
allowed_negative_columns = [
    "net_change",
    "temperature_celsius"
]

non_negative_columns = [
    "age",
    "price",
    "quantity",
    "total_amount"
]

# Privacy
include_full_path = false
```

---

## Sample JSON Configuration (`datapulse_config.json`)

```json
{
  "max_categories": 15,
  "compute_correlations": true,
  "correlation_method": "pearson",
  "min_correlation": 0.65,
  "max_correlation_columns": 25,
  "missing_sentinels": ["?", "NA", "N/A", "MISSING", "-999"],
  "column_roles": {
    "account_id": "identifier",
    "status_code": "categorical"
  },
  "allowed_negative_columns": ["net_change"],
  "non_negative_columns": ["price", "quantity"],
  "include_full_path": false
}
```

---

## Loading and Validating in Python

```python
import datapulse as dp

# Load and validate configuration
config = dp.load_config("datapulse_config.toml")

# Inspect validated settings
print(f"Max categories: {config.max_categories}")
print(f"Correlation threshold: {config.min_correlation}")
```

> **Typo & Extra Key Protection:**  
> DataPulse strictly validates all configurations (`extra="forbid"`). Any misspelling in option names (e.g. `max_catgories`) immediately raises a descriptive `pydantic.ValidationError` rather than silently failing.
