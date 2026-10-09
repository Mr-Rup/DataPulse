# DataPulse Progress Tracker

## Current State
- **Project:** DataPulse
- **Phase:** DP-5 — Core descriptive profiling by role
- **Last Completed Milestone:** Modular role-specific profilers implemented and wired into AnalysisReport
- **Branch:** `dp-5-descriptive-profiling`

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

## Next Exact Action
- Start **DP-6: Quality checks and heuristic anomaly rules**.

## Do Not Do Yet
- Do not hard-code taxi-specific business rules into generic profiler logic.
- Do not build custom exception hierarchies.
- Do not commit raw datasets into git.

