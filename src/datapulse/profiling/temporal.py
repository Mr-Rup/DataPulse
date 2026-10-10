# =========================================================================
# DataPulse Temporal Column Profiler
# Chronological boundaries (min/max), range duration (span in days/seconds).
# =========================================================================

from datetime import date, datetime

import polars as pl

# =========================================================================
# TEMPORAL PROFILER IMPLEMENTATION
# =========================================================================

def profile_temporal(series: pl.Series, total_rows: int) -> dict[str, object]:
    """Calculate descriptive statistics for a date or datetime column."""
    non_null = series.drop_nulls()
    if non_null.len() == 0:
        return {
            "count": 0,
            "minimum": None,
            "maximum": None,
            "span_days": None,
            "span_seconds": None,
            "unique_count": 0,
        }

    min_val = non_null.min()
    max_val = non_null.max()
    unique_count = non_null.n_unique()

    span_days = None
    span_seconds = None

    if isinstance(min_val, datetime) and isinstance(max_val, datetime):
        diff = max_val - min_val
        span_seconds = float(diff.total_seconds())
        span_days = round(diff.total_seconds() / 86400.0, 2)
    elif (
        isinstance(min_val, date)
        and not isinstance(min_val, datetime)
        and isinstance(max_val, date)
        and not isinstance(max_val, datetime)
    ):
        diff = max_val - min_val
        span_seconds = float(diff.total_seconds())
        span_days = round(diff.total_seconds() / 86400.0, 2)

    return {
        "count": non_null.len(),
        "minimum": str(min_val) if min_val is not None else None,
        "maximum": str(max_val) if max_val is not None else None,
        "span_days": span_days,
        "span_seconds": span_seconds,
        "unique_count": unique_count,
    }
