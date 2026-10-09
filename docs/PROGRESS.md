# DataPulse Progress Tracker

## Current State
- **Project:** DataPulse
- **Phase:** DP-0 — Baseline and repository stabilization
- **Last Completed Milestone:** Initial baseline test/lint check and configuration update
- **Branch:** `dp-0-baseline`

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

## Next Exact Action
- Create branch `dp-1-real-data-validation` and implement `scripts/download_tlc.py` to fetch TLC data and the lookup CSV.

## Do Not Do Yet
- Do not build custom exception hierarchies.
- Do not start DataBench implementation before DataPulse V1 is stabilized.
- Do not commit raw datasets into git.
