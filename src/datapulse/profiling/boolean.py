import polars as pl


def profile_boolean(series: pl.Series, total_rows: int) -> dict[str, object]:
    """Calculate descriptive statistics for a boolean column."""

    non_null = series.drop_nulls()
    if non_null.len() == 0:
        return {
            "count": 0,
            "true_count": 0,
            "true_percentage": 0.0,
            "false_count": 0,
            "false_percentage": 0.0,
        }

    try:
        bool_s = non_null.cast(pl.Boolean, strict=False)
        true_count = int((bool_s == True).sum())  # noqa: E712
    except Exception:
        true_count = int((non_null == 1).sum())

    false_count = non_null.len() - true_count
    true_pct = round((true_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
    false_pct = round((false_count / total_rows) * 100, 2) if total_rows > 0 else 0.0

    return {
        "count": non_null.len(),
        "true_count": true_count,
        "true_percentage": true_pct,
        "false_count": false_count,
        "false_percentage": false_pct,
    }
