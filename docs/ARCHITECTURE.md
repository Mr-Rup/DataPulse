# DataPulse Architecture & Technical Design

A deep-dive technical overview of DataPulse's internal design, execution pipeline, and algorithmic strategies.

---

## High-Level Execution Pipeline

DataPulse executes in a streamlined, 6-stage pipeline engineered to maximize throughput while minimizing memory footprint:

```
┌────────────────────────────────────────────────────────┐
│ 1. Zero-Copy Ingestion & Sniffing                      │
│    (Polars Lazy Engine | Delimiter / Encoding Sniffer) │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 2. Parallel Single-Pass Column Profiler                │
│    (Vectorized Expressions: Nulls, NaNs, Sentinels)    │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 3. Semantic Role Classification                        │
│    (Heuristic Rules: Numeric, Categorical, ID, etc.)   │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 4. Deep Role-Specific Statistical Profiling            │
│    (Percentiles, IQR, Frequencies, Spans, Text Lens)   │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 5. Automated Data Quality & Anomaly Engine             │
│    (Multicollinearity, Tukey Outliers, Key Discovery)  │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 6. Multi-Format Report Assembly & Delivery             │
│    (Terminal UI | Standalone HTML | Machine JSON)      │
└────────────────────────────────────────────────────────┘
```

---

## 1. Zero-Copy Ingestion & File Sniffing (`ingestion/readers.py`)

- **Polars Lazy Engine:** File scanning (`pl.scan_parquet`, `pl.scan_csv`, `pl.scan_ndjson`) avoids eagerly copying raw files into memory. Data is processed using streaming, multi-threaded operations.
- **CSV & Delimiter Sniffing:** Automatically detects field delimiters (`,`, `\t`, `;`, `|`) and line terminators (`\r\n`, `\n`, `\r`) from leading file bytes.
- **JSON Dual Ingestion:** Automatically inspects JSON structures to choose between single-object arrays (`read_json`) and line-delimited records (`scan_ndjson`).
- **In-Memory Zero-Overhead:** Ingests in-memory Polars `DataFrame` and `LazyFrame` instances directly without filesystem serialization.

---

## 2. Unified Missingness & Sentinel Accounting (`profiling/profiler.py`)

Traditional profilers miss data gaps encoded as empty strings (`""`), `NaN` floats, or custom sentinels (`"?"`, `"-999"`, `"N/A"`).

DataPulse computes missingness in a single vectorized pass:
```
Total Missing = Null Count + NaN Count + Empty String Count + Sentinel Count
```
All four components are audited and reported with precision down to individual sentinel frequencies.

---

## 3. Semantic Role Classification (`analysis/column_classifier.py`)

Physical data types (`i64`, `f64`, `str`) do not correspond 1-to-1 with analytical semantics. DataPulse classifies each column into one of 8 semantic roles:

1. **`numeric`:** Continuous or high-cardinality integers and floating-point measurements.
2. **`categorical`:** Low-to-moderate cardinality strings or integer status codes (e.g. status flags, payment methods).
3. **`boolean`:** Native boolean flags or binary string/integer representations (`0/1`, `"Y/N"`, `"True/False"`).
4. **`temporal`:** Timestamps, dates, and datetimes.
5. **`text`:** Long, freeform unstructured string data (distinguished from categoricals via token count heuristics: >= 3 avg words and >= 25 avg length).
6. **`identifier`:** High-cardinality IDs, primary keys, UUIDs, or hashes.
7. **`constant`:** Columns containing only 1 distinct non-null value (zero variance).
8. **`other`:** Binary blobs, lists, or unrecognized types.

---

## 4. Deep Statistical Profiling (`profiling/`)

Each role receives specialized profiling routines executed in parallel:

- **Numeric:** Mean, standard deviation, min, 25%, median (50%), 75%, max, interquartile range (IQR), zero counts, negative counts, skewness.
- **Categorical:** Distinct counts, cardinality ratio, mode value, and frequency tables for top N categories.
- **Temporal:** Min timestamp, max timestamp, chronological duration (days/seconds), unique timestamp counts.
- **Text:** Character length statistics (min, max, mean, median), empty string counts.
- **Boolean:** True/False counts and percentage distributions.
- **Identifier:** Uniqueness percentage, duplicate count, key viability assessment.

---

## 5. Automated Quality Rules & Anomaly Engine (`analysis/quality_rules.py`)

DataPulse runs automated audit rules on every dataset:

- **Missingness Severity:** Warns on columns with moderate (> 10%) or severe (> 50%) data loss.
- **Duplicate Rows:** Full-row duplicate count and duplicate percentage.
- **Multicollinearity:** Computes parallel Pearson and Spearman correlation matrices; flags pairs with $|r| \ge 0.90$ to catch data leakage and redundancy.
- **Primary Key Candidates:** Detects columns with 100% uniqueness and zero missing values.
- **Tukey Outliers:** Flags numeric columns with extreme outliers outside $[Q_1 - 1.5 \times \text{IQR},\, Q_3 + 1.5 \times \text{IQR}]$.
- **Domain Anomalies:** Flags negative values in non-negative columns (e.g., negative prices, fares, or ages).
- **Chronological Inversions:** Identifies instances where end timestamps precede start timestamps.

---

## 6. Multi-Format Exporters (`reporting/`)

- **Terminal (`reporting/terminal.py`):** Uses Rich tables, severity panels, and formatted metric grids for CLI users.
- **HTML (`reporting/html.py`):** Generates self-contained, single-file HTML dashboards with inline modern dark-mode CSS, client-side real-time column search filtering, and zero external network/CDN dependencies.
- **JSON (`reporting/json_exporter.py`):** Serializes clean, schema-versioned JSON structures suitable for data pipeline logging and CI/CD validation.
