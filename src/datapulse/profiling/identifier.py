import polars as pl


def profile_identifier(series: pl.Series, total_rows: int) -> dict[str, object]:
    """Calculate descriptive statistics for an identifier column."""

    non_null = series.drop_nulls()
    if non_null.len() == 0:
        return {
            "count": 0,
            "unique_count": 0,
            "duplicate_count": 0,
            "uniqueness_percentage": 0.0,
            "cardinality_percentage": 0.0,
        }

    unique_count = non_null.n_unique()
    duplicate_count = non_null.len() - unique_count
    uniqueness_pct = (
        round((unique_count / non_null.len()) * 100, 2) if non_null.len() > 0 else 0.0
    )
    cardinality_pct = (
        round((unique_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
    )

    return {
        "count": non_null.len(),
        "unique_count": unique_count,
        "duplicate_count": duplicate_count,
        "uniqueness_percentage": uniqueness_pct,
        "cardinality_percentage": cardinality_pct,
    }
