# =========================================================================
# DataPulse Categorical Column Profiler
# Frequency distribution, distinct counts, cardinality ratios, and modes.
# =========================================================================

import polars as pl

# =========================================================================
# CATEGORICAL PROFILER IMPLEMENTATION
# =========================================================================

def profile_categorical(
    series: pl.Series,
    total_rows: int,
    max_categories: int = 10,
    sentinels: list[str] | None = None,
) -> dict[str, object]:
    """Calculate descriptive statistics and top categories for a categorical column."""
    non_null = series.drop_nulls()
    if non_null.len() == 0:
        return {
            "count": 0,
            "unique_count": 0,
            "cardinality_percentage": 0.0,
            "mode": None,
            "top_categories": [],
            "empty_count": 0,
            "sentinel_count": 0,
            "effective_missing_count": series.null_count(),
        }

    unique_count = non_null.n_unique()
    cardinality_pct = (
        round((unique_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
    )

    empty_count = 0
    sentinel_count = 0
    if non_null.dtype == pl.String:
        empty_count = int((non_null == "").sum())
        if sentinels:
            sentinel_count = int(non_null.is_in(sentinels).sum())

    effective_missing = series.null_count() + empty_count + sentinel_count
    vc_df = non_null.value_counts(sort=True).head(max_categories)
    top_categories = []

    for row in vc_df.to_dicts():
        raw_val = row[series.name]
        val_str = str(raw_val) if raw_val is not None else "null"
        cnt = int(row["count"])
        pct = round((cnt / total_rows) * 100, 2) if total_rows > 0 else 0.0
        top_categories.append(
            {
                "value": val_str,
                "count": cnt,
                "percentage": pct,
            }
        )

    mode_val = top_categories[0]["value"] if top_categories else None

    return {
        "count": non_null.len(),
        "unique_count": unique_count,
        "cardinality_percentage": cardinality_pct,
        "mode": mode_val,
        "top_categories": top_categories,
        "empty_count": empty_count,
        "sentinel_count": sentinel_count,
        "effective_missing_count": effective_missing,
    }
