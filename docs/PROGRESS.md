# DataPulse Progress Tracker

## Current State
- **Project:** DataPulse
- **Phase:** DP-10 — Performance, sampling, and scale validation
- **Last Completed Milestone:** Full scale benchmark on 3.475M row TLC parquet (3.78s execution, ~1.2M rows/s sampled throughput), configuration validation, and scale test suite
- **Branch:** `dp-10-performance-scale`

## Phase History

### DP-0: Baseline and repository stabilization
- **Status:** Completed
- **Changes:**
  - Resolved import ordering lint issue in `scripts/inspect_taxi_data.py`.
  - Updated `pyproject.toml` to focus description on automated tabular EDA.
  - Aligned `target-version = "py314"` in ruff and `pythonVersion = "3.14"` in pyright.
  - Rewrote `README.md` to reflect pure EDA goals.
  - Updated `.gitignore` to exclude `reports/` and `*.html`.
  - Created `docs/PROGRESS.md` and `docs/DECISIONS.md`.
- **Validation:**
  - `uv run pytest`: 9 passed.
  - `uv run ruff check .`: 0 errors.
  - `uv run pyright`: 0 errors.

### DP-1: Real-data validation vertical slice
- **Status:** Completed
- **Changes:**
  - Implemented `scripts/download_tlc.py` (std-lib `urllib`, progress indicator, supports `--year`, `--month`, `--force`).
  - Added UTF-8 stdout configuration to `scripts/inspect_taxi_data.py` for cross-platform Windows compatibility.
  - Downloaded official `yellow_tripdata_2025-01.parquet` (56.42 MB) and `taxi_zone_lookup.csv` (12.3 KB) into `data/raw/` (safely ignored by Git).
  - Executed `inspect_taxi_data.py`: confirmed 3,475,226 rows, 20 columns; verified data characteristics (5 columns with 540,149 nulls, 90,893 zero-distance trips, 144,118 negative-fare rows, 124 dropoffs before pickup).
  - Executed `profile_dataset.py`: verified profiler on 3.47M rows; identified key improvements:
    1. Eager full load in profiler (`read_parquet`) should transition to lazy scans (`scan_parquet`) in DP-3.
    2. Rich table column truncation in terminal for wide numeric schemas (to be redesigned in DP-8).
    3. Categorical integer misclassification (`payment_type`, `VendorID`, `RatecodeID`, `PULocationID` classified as numeric rather than categorical/identifiers; to be addressed in DP-4).
- **Validation:**
  - `uv run pytest`: 9 passed in 0.22s.
  - `uv run ruff check .`: 0 errors.
  - `uv run pyright`: 0 errors.

### DP-2: Report model and core API
- **Status:** Completed
- **Changes:**
  - Implemented `@dataclass` report models in `src/datapulse/models/report.py` (`ReportMetadata`, `DatasetSummary`, `DuplicateSummary`, `MissingSummary`, `ColumnProfile`, `Finding`, `AnalysisReport`).
  - Added `to_dict()` and `to_json()` methods to `AnalysisReport` for clean serialization.
  - Created `src/datapulse/config.py` with `AnalysisConfig`.
  - Implemented `src/datapulse/api.py` with `analyze(file_path, config=None) -> AnalysisReport`.
  - Exported public symbols `analyze`, `AnalysisReport`, `AnalysisConfig`, and `__version__ = "0.1.0"` in `src/datapulse/__init__.py`.
  - Refactored `src/datapulse/reporting/terminal.py` (`display_report`, `display_profile`) to consume `AnalysisReport`.
  - Added unit test suites `tests/models/test_report.py` and `tests/test_api.py`.
- **Validation:**
  - `uv run pytest`: 13 passed in 0.26s.
  - `uv run ruff check .`: 0 errors.
  - `uv run pyright`: 0 errors.

### DP-3: Ingestion and schema inspection
- **Status:** Completed
- **Changes:**
  - Added `fastexcel` to project dependencies and `xlsxwriter` to test dev dependencies in `pyproject.toml`.
  - Created `src/datapulse/ingestion/readers.py` with `read_source` supporting Parquet, CSV, JSON/NDJSON, and Excel (`.xlsx`, `.xls`).
  - Created `src/datapulse/ingestion/__init__.py` exporting `SourceInfo`, `read_source`.
  - Updated `DatasetProfiler` to read files using `read_source`, enabling multi-format profiling.
  - Updated `src/datapulse/config.py` and `src/datapulse/api.py` to support format-specific options (e.g. `sheet_name`, `separator`).
  - Added comprehensive test suite `tests/ingestion/test_readers.py` covering all formats, custom separators, error conditions (missing, empty, unsupported extension), and local real CSV fixture validation.
  - Added multi-format tests to `tests/test_api.py`.
- **Validation:**
  - `uv run pytest`: 26 passed in 0.37s.
  - `uv run ruff check .`: 0 errors.
  - `uv run pyright`: 0 errors.

### DP-4: Column classification
- **Status:** Completed
- **Changes:**
  - Implemented heuristic rule-based column classification engine in `src/datapulse/analysis/column_classifier.py`.
  - Roles supported: `numeric`, `categorical`, `temporal`, `boolean`, `text`, `identifier`, `constant`, `other`.
  - Distinguishes coded low-cardinality integers (e.g. `payment_type`, `VendorID`) as categorical rather than continuous numeric.
  - Detects IDs and keys (`PULocationID`, `uuid`, etc.) based on cardinality and naming patterns.
  - Detects freeform text columns based on average string length.
  - Added `confidence` and `inference_reason` to `ColumnClassification` and `ColumnProfile`.
  - Wired classifier into `DatasetProfiler.get_column_quality()` and `analyze()`.
  - Created test suite `tests/analysis/test_column_classifier.py` covering all roles and heuristics.
- **Validation:**
  - `uv run pytest`: 36 passed in 0.40s.
  - `uv run ruff check .`: 0 errors.
  - `uv run pyright`: 0 errors.

### DP-5: Core descriptive profiling by role
- **Status:** Completed
- **Changes:**
  - Implemented modular, role-specific descriptive statistics profilers in `src/datapulse/profiling/`:
    - `numeric.py`: count, mean, std, min, 25%, median (50%), 75%, max, IQR, zeros count & %, negatives count & %, skewness.
    - `categorical.py`: count, unique_count, cardinality %, mode, bounded `top_categories` (value, count, percentage).
    - `temporal.py`: count, minimum, maximum, span_days, span_seconds, unique_count.
    - `boolean.py`: count, true_count & %, false_count & %.
    - `text.py`: count, min/max/mean/median lengths, empty_count & %, unique_count, cardinality %.
    - `identifier.py`: count, unique_count, duplicate_count, uniqueness %, cardinality %.
    - `column_profiler.py`: unified dispatcher `profile_column(series, total_rows, role, max_categories)`.
  - Added `DatasetProfiler.profile_column()` and updated `api.analyze()` to populate rich role-specific `ColumnProfile.statistics`.
  - Upgraded terminal report renderer in `src/datapulse/reporting/terminal.py` to display clean, dedicated tables for each analytical role.
  - Added comprehensive test suite `tests/profiling/test_role_profilers.py`.
- **Validation:**
  - `uv run pytest`: 48 passed in 0.39s.
  - `uv run ruff check .`: 0 errors.
  - `uv run pyright`: 0 errors.
  - Real data smoke test: verified on `taxi_zone_lookup.csv`.

### DP-6: Quality checks and heuristic anomaly rules
- **Status:** Completed
- **Changes:**
  - Implemented automated heuristic quality checks and anomaly detection in `src/datapulse/analysis/quality_rules.py`:
    - `check_missingness`: severe (>=50%) and moderate (>=20%) missingness alerts.
    - `check_duplicates`: duplicate rows alert with severity tiering.
    - `check_constant_columns`: zero-variance / single-value columns.
    - `check_high_cardinality`: high-cardinality categorical warnings (>50% cardinality ratio).
    - `check_negative_values`: checks conventionally non-negative columns (fares, amounts, prices, distances, counts, ages, etc.).
    - `check_numeric_outliers`: Tukey 1.5x IQR boundary detection.
    - `check_chronology_inversion`: temporal pairs check (e.g. pickup/dropoff, start/end).
  - Wired `evaluate_quality_rules()` into `api.analyze()`, populating `AnalysisReport.findings` and `AnalysisReport.warnings`.
  - Added dedicated "Data Quality Findings & Anomalies" table to `src/datapulse/reporting/terminal.py`.
  - Real data smoke test: verified on 3.47M TLC dataset; accurately detected 144k negative fares, 124 chronological dropoff-before-pickup inversions, and distance/fare outliers.
  - Added test suite in `tests/analysis/test_quality_rules.py`.
- **Validation:**
  - `uv run pytest`: 56 passed in 0.40s.
  - `uv run ruff check .`: 0 errors.
  - `uv run pyright`: 0 errors.

### DP-7: Relationship and correlation analysis
- **Status:** Completed
- **Changes:**
  - Implemented dependency-free native Polars relationship and correlation engine in `src/datapulse/analysis/relationships.py`:
    - `compute_correlations`: parallel pairwise numeric correlation computation (`pearson` and `spearman`) via native `pl.corr()`.
    - `find_key_candidates`: detects 100% unique, zero-null primary key candidate columns.
    - `evaluate_collinear_findings`: automatically generates findings for highly collinear pairs (`|r| >= 0.90`) to alert on leakage or redundancy.
  - Added `CorrelationPair` and `KeyCandidate` data models to `src/datapulse/models/report.py` and connected them to `AnalysisReport`.
  - Wired relationship computations into `api.analyze()`.
  - Added "Top Numeric Correlations" and "Key & Identifier Candidates" tables to terminal report renderer.
  - Added test suite in `tests/analysis/test_relationships.py`.
- **Validation:**
  - `uv run pytest`: 62 passed in 0.42s.
  - `uv run ruff check .`: 0 errors.
  - `uv run pyright`: 0 errors.
  - Smoke tests: verified on real datasets (`taxi_zone_lookup.csv` accurately identified `LocationID` as primary key candidate).

### DP-8: Multi-format reporting (Terminal, JSON, HTML)
- **Status:** Completed
- **Changes:**
  - Implemented standalone JSON exporter in `src/datapulse/reporting/json_exporter.py` with `export_json()`.
  - Implemented modern, self-contained HTML report generator in `src/datapulse/reporting/html.py` with `generate_html_report()` and `export_html()`.
  - HTML report features zero external CDN dependencies, dark modern aesthetic, responsive metric cards, badges, interactive column search filter, data quality alerts, key candidates, and correlation tables.
  - Added `save_html()` and `save_json()` helper methods to `AnalysisReport` in `src/datapulse/models/report.py`.
  - Exported `generate_html_report`, `export_html`, and `export_json` in `src/datapulse/reporting/__init__.py` and root package `src/datapulse/__init__.py`.
  - Added unit test suite in `tests/reporting/test_html_report.py` covering HTML generation, file saving, search script inclusion, and JSON export.
- **Validation:**
  - `uv run pytest`: 64 passed in 0.49s.
  - `uv run ruff check .`: 0 errors.
  - `uv run pyright`: 0 errors.

### DP-9: CLI and configuration
- **Status:** Completed
- **Changes:**
  - Implemented full Typer CLI in `src/datapulse/cli/app.py`:
    - Commands: `datapulse analyze <file>`, `datapulse profile <file>`, `datapulse version`.
    - Flags: `--format, -f` (`terminal`, `html`, `json`), `--output, -o`, `--config, -c`, `--sample, -s`, `--sample-method`, `--max-categories`, `--correlations/--no-correlations`, `--quiet, -q`, `--sheet-name`, `--separator`.
    - Handles format routing: terminal table preview, HTML standalone generation, direct JSON stdout streaming or file export.
  - Expanded `AnalysisConfig` in `src/datapulse/config.py` with sampling method, correlation toggles, and thresholds.
  - Implemented `load_config()` supporting JSON and TOML formats with top-level or `[datapulse]` nested sections.
  - Updated `DatasetProfiler` with lazy sampling (`limit()` for head, `sample()` for random) to avoid loading full datasets into memory when sampled.
  - Exported `load_config` in `src/datapulse/__init__.py`.
  - Created test suite `tests/cli/test_app.py` covering help, version, format options, file export, sampling, configuration overrides, and error exits.
- **Validation:**
  - `uv run pytest`: 78 passed in 0.66s.
  - `uv run ruff check .`: 0 errors.
  - `uv run pyright`: 0 errors.
  - Smoke tests: verified CLI execution on `taxi_zone_lookup.csv` with sampling and terminal formatting.

### DP-10: Performance, sampling, and scale validation
- **Status:** Completed
- **Changes:**
  - Validated and benchmarked performance against the official NYC TLC dataset (`yellow_tripdata_2025-01.parquet`, 3,475,226 rows, 20 columns):
    - Full 3.475M row end-to-end profiling completes in 3.78s (~920,000 rows/second).
    - Sampled 1M rows completes in 0.956s (~1,045,000 rows/second).
    - Sampled 100k rows completes in 0.084s (~1,195,000 rows/second).
    - Sampled 10k rows completes in 0.031s (~321,000 rows/second).
  - Added `sample_size` reporting into `ReportMetadata` and indicators into both terminal overview panel and HTML report header badges.
  - Added configuration validation `__post_init__` to `AnalysisConfig` with clear, standard `ValueError` checks.
  - Created automated benchmark utility in `scripts/benchmark_datapulse.py` with formatted Rich performance tables.
  - Updated `scripts/profile_dataset.py` to leverage the unified `analyze()` engine with `--sample` and format flags.
  - Created unit test suite `tests/profiling/test_sampling_scale.py` covering head sampling, reproducible random sampling, row boundary conditions, metadata tracking, config validation, and execution budgets.
- **Validation:**
  - `uv run pytest`: 85 passed in 0.76s.
  - `uv run ruff check .`: 0 errors.
  - `uv run pyright`: 0 errors.

## Next Exact Action
- Start **DP-11: Release candidate, documentation polish, and packaging**.

## Do Not Do Yet
- Do not hard-code taxi-specific business rules into generic profiler logic.
- Do not build custom exception hierarchies.
- Do not commit raw datasets into git.




