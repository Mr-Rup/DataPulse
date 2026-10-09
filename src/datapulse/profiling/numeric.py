import polars as pl


def profile_numeric(series: pl.Series, total_rows: int) -> dict[str, object]:
    """Calculate descriptive statistics for a numeric column."""

    non_null = series.drop_nulls()
    if non_null.len() == 0:
        return {
            "count": 0,
            "mean": None,
            "std": None,
            "min": None,
            "p25": None,
            "25%": None,
            "median": None,
            "50%": None,
            "p75": None,
            "75%": None,
            "max": None,
            "iqr": None,
            "zeros_count": 0,
            "zeros_percentage": 0.0,
            "negatives_count": 0,
            "negatives_percentage": 0.0,
            "skewness": None,
        }

    mean_val = non_null.mean()
    std_val = non_null.std()
    min_val = non_null.min()
    max_val = non_null.max()
    p25_val = non_null.quantile(0.25)
    median_val = non_null.median()
    p75_val = non_null.quantile(0.75)
    skew_val = non_null.skew()

    p25_round = round(float(p25_val), 4) if isinstance(p25_val, (int, float)) else None
    med_round = (
        round(float(median_val), 4) if isinstance(median_val, (int, float)) else None
    )
    p75_round = round(float(p75_val), 4) if isinstance(p75_val, (int, float)) else None
    iqr_round = (
        round(float(p75_val - p25_val), 4)
        if isinstance(p75_val, (int, float)) and isinstance(p25_val, (int, float))
        else None
    )

    zeros_count = int((non_null == 0).sum())
    zeros_pct = round((zeros_count / total_rows) * 100, 2) if total_rows > 0 else 0.0

    negatives_count = int((non_null < 0).sum())
    negatives_pct = (
        round((negatives_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
    )

    return {
        "count": non_null.len(),
        "mean": (
            round(float(mean_val), 4) if isinstance(mean_val, (int, float)) else None
        ),
        "std": (round(float(std_val), 4) if isinstance(std_val, (int, float)) else 0.0),
        "min": (
            round(float(min_val), 4) if isinstance(min_val, (int, float)) else None
        ),
        "p25": p25_round,
        "25%": p25_round,
        "median": med_round,
        "50%": med_round,
        "p75": p75_round,
        "75%": p75_round,
        "max": (
            round(float(max_val), 4) if isinstance(max_val, (int, float)) else None
        ),
        "iqr": iqr_round,
        "zeros_count": zeros_count,
        "zeros_percentage": zeros_pct,
        "negatives_count": negatives_count,
        "negatives_percentage": negatives_pct,
        "skewness": (
            round(float(skew_val), 4) if isinstance(skew_val, (int, float)) else None
        ),
    }
