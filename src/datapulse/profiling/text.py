import polars as pl


def profile_text(series: pl.Series, total_rows: int) -> dict[str, object]:
    """Calculate descriptive statistics for a text column."""

    non_null = series.drop_nulls()
    if non_null.len() == 0:
        return {
            "count": 0,
            "min_length": 0,
            "max_length": 0,
            "mean_length": 0.0,
            "median_length": 0.0,
            "empty_count": 0,
            "empty_percentage": 0.0,
            "unique_count": 0,
            "cardinality_percentage": 0.0,
        }

    lengths = non_null.str.len_chars()
    min_len = lengths.min()
    max_len = lengths.max()
    mean_len = lengths.mean()
    median_len = lengths.median()

    empty_count = int((non_null == "").sum())
    empty_pct = round((empty_count / total_rows) * 100, 2) if total_rows > 0 else 0.0

    unique_count = non_null.n_unique()
    cardinality_pct = (
        round((unique_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
    )

    return {
        "count": non_null.len(),
        "min_length": int(min_len) if isinstance(min_len, (int, float)) else 0,
        "max_length": int(max_len) if isinstance(max_len, (int, float)) else 0,
        "mean_length": (
            round(float(mean_len), 2) if isinstance(mean_len, (int, float)) else 0.0
        ),
        "median_length": (
            round(float(median_len), 2) if isinstance(median_len, (int, float)) else 0.0
        ),
        "empty_count": empty_count,
        "empty_percentage": empty_pct,
        "unique_count": unique_count,
        "cardinality_percentage": cardinality_pct,
    }
