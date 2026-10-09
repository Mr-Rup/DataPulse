# DataPulse Progress Tracker

## Current State
- **Project:** DataPulse
- **Phase:** DP-1 — Real-data validation vertical slice
- **Last Completed Milestone:** Downloaded TLC Parquet & CSV, executed profiling runs, and validated observed findings
- **Branch:** `dp-1-real-data-validation`

## Phase History

### DP-0: Baseline and repository stabilization
- **Status:** Completed
- **Changes:**
  - Resolved import ordering lint issue in `scripts/inspect_taxi_data.py`.
  - Updated `pyproject.toml` to focus description on automated tabular EDA.
  - Aligned `target-version = "py314"` in ruff and `pythonVersion = "3.14"` in pyright.
  - Rewrote `README.md` to reflect pure EDA goals (deferring engine benchmarks to DataBench).
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

## Next Exact Action
- Review and merge `dp-1-real-data-validation` into `main`, then start **DP-2: Report model and `analyze()` API**.

## Do Not Do Yet
- Do not hard-code taxi-specific business rules into generic profiler logic.
- Do not build custom exception hierarchies.
- Do not start DataBench implementation before DataPulse V1 is stabilized.
- Do not commit raw datasets into git.

