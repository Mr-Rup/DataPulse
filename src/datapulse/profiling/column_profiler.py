import polars as pl

from datapulse.profiling.boolean import profile_boolean
from datapulse.profiling.categorical import profile_categorical
from datapulse.profiling.identifier import profile_identifier
from datapulse.profiling.numeric import profile_numeric
from datapulse.profiling.temporal import profile_temporal
from datapulse.profiling.text import profile_text


def profile_column(
    series: pl.Series,
    total_rows: int,
    role: str,
    max_categories: int = 20,
) -> dict[str, object]:
    """Calculate role-specific statistics for a single column."""

    if role == "numeric":
        return profile_numeric(series, total_rows)
    if role == "categorical":
        return profile_categorical(series, total_rows, max_categories=max_categories)
    if role == "temporal":
        return profile_temporal(series, total_rows)
    if role == "boolean":
        return profile_boolean(series, total_rows)
    if role == "text":
        return profile_text(series, total_rows)
    if role == "identifier":
        return profile_identifier(series, total_rows)
    if role == "constant":
        non_null = series.drop_nulls()
        val = str(non_null[0]) if non_null.len() > 0 else None
        return {
            "count": non_null.len(),
            "constant_value": val,
        }

    return {"count": series.drop_nulls().len()}
