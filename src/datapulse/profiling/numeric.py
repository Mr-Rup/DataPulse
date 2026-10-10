import polars as pl


def profile_numeric(series: pl.Series, total_rows: int) -> dict[str, object]:
    """Calculate descriptive statistics for a numeric column."""

    null_count = series.null_count()
    nan_count = int(series.is_nan().sum()) if series.dtype.is_float() else 0
    inf_count = int(series.is_infinite().sum()) if series.dtype.is_float() else 0

    non_null = series.drop_nulls()
    # Filter out NaNs and Infs for statistical calculations
    if non_null.dtype.is_float():
        clean_series = non_null.filter(~non_null.is_nan() & ~non_null.is_infinite())
    else:
        clean_series = non_null

    if clean_series.len() == 0:
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
            "nan_count": nan_count,
            "nan_percentage": (
                round((nan_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
            ),
            "infinite_count": inf_count,
            "infinite_percentage": (
                round((inf_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
            ),
            "effective_missing_count": null_count + nan_count,
            "skewness": None,
        }

    mean_val = clean_series.mean()
    std_val = clean_series.std()
    min_val = clean_series.min()
    max_val = clean_series.max()
    p25_val = clean_series.quantile(0.25)
    median_val = clean_series.median()
    p75_val = clean_series.quantile(0.75)
    skew_val = clean_series.skew()

    p25_round = (
        round(float(p25_val), 4) if isinstance(p25_val, (int, float)) else None
    )
    med_round = (
        round(float(median_val), 4) if isinstance(median_val, (int, float)) else None
    )
    p75_round = (
        round(float(p75_val), 4) if isinstance(p75_val, (int, float)) else None
    )
    iqr_round = (
        round(float(p75_val - p25_val), 4)
        if isinstance(p75_val, (int, float)) and isinstance(p25_val, (int, float))
        else None
    )

    zeros_count = int((clean_series == 0).sum())
    zeros_pct = (
        round((zeros_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
    )

    negatives_count = int((clean_series < 0).sum())
    negatives_pct = (
        round((negatives_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
    )

    return {
        "count": clean_series.len(),
        "mean": (
            round(float(mean_val), 4) if isinstance(mean_val, (int, float)) else None
        ),
        "std": (
            round(float(std_val), 4) if isinstance(std_val, (int, float)) else 0.0
        ),
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
        "nan_count": nan_count,
        "nan_percentage": (
            round((nan_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
        ),
        "infinite_count": inf_count,
        "infinite_percentage": (
            round((inf_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
        ),
        "effective_missing_count": null_count + nan_count,
        "skewness": (
            round(float(skew_val), 4) if isinstance(skew_val, (int, float)) else None
        ),
    }
