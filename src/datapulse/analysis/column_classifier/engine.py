# =========================================================================
# DataPulse Column Classifier Engine
# Main classification pipeline coordinating physical types and rule modules.
# =========================================================================

import polars as pl

from datapulse.analysis.column_classifier.hints import ID_SUFFIX_HINTS
from datapulse.analysis.column_classifier.models import ColumnClassification
from datapulse.analysis.column_classifier.numeric_rules import classify_numeric_series
from datapulse.analysis.column_classifier.string_rules import classify_string_series

# =========================================================================
# CORE CLASSIFICATION ENGINE
# =========================================================================

def classify_column(
    series: pl.Series,
    total_rows: int,
    override_role: str | None = None,
) -> ColumnClassification:
    """Infer the analytical role of a Polars Series using multi-tier heuristics."""
    name = series.name
    dtype = series.dtype
    name_lower = name.lower()

    # 1. Configuration Overrides
    if override_role:
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role=override_role,
            confidence=1.0,
            reason="User-specified override in configuration",
            alternative_roles=[],
        )

    # 2. Empty datasets or columns with 100% missing values
    if total_rows == 0 or series.null_count() == total_rows:
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="other",
            confidence=0.5,
            reason="All null or empty column",
            alternative_roles=[],
        )

    non_null = series.drop_nulls()
    unique_count = non_null.n_unique()

    # 3. Zero variance columns (single distinct scalar value)
    if unique_count <= 1:
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="constant",
            confidence=1.0,
            reason="Column contains only 1 distinct value",
            alternative_roles=[],
        )

    # 4. Invariant Physical Types (Boolean & Temporal)
    if dtype == pl.Boolean:
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="boolean",
            confidence=1.0,
            reason="Physical boolean data type",
            alternative_roles=["categorical"],
        )

    if dtype.is_temporal():
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="temporal",
            confidence=1.0,
            reason="Physical temporal data type",
            alternative_roles=[],
        )

    # Precalculate cardinality ratio and identifier naming cues
    has_id_hint = any(name_lower.endswith(sfx) for sfx in ID_SUFFIX_HINTS)
    cardinality_ratio = unique_count / total_rows if total_rows > 0 else 0.0

    # 5. Numeric Types (Integers, Floats, Indicators, Codes)
    if dtype.is_numeric():
        return classify_numeric_series(
            series=series,
            dtype=dtype,
            name=name,
            name_lower=name_lower,
            non_null=non_null,
            unique_count=unique_count,
            total_rows=total_rows,
            cardinality_ratio=cardinality_ratio,
            has_id_hint=has_id_hint,
        )

    # 6. String & Categorical Types (Identifiers, Text, Codes)
    if dtype in (pl.String, pl.Categorical, pl.Enum):
        return classify_string_series(
            series=series,
            dtype=dtype,
            name=name,
            name_lower=name_lower,
            non_null=non_null,
            total_rows=total_rows,
            cardinality_ratio=cardinality_ratio,
        )

    # 7. Fallback for Unknown / Complex Dtypes
    return ColumnClassification(
        name=name,
        physical_type=str(dtype),
        inferred_role="other",
        confidence=0.5,
        reason=f"Unclassified physical type: {dtype}",
        alternative_roles=[],
    )


# =========================================================================
# BATCH DATAFRAME INFERENCE
# =========================================================================

def classify_columns(
    df: pl.DataFrame,
    column_roles: dict[str, str] | None = None,
) -> dict[str, ColumnClassification]:
    """Classify all columns in a Polars DataFrame into analytical roles."""
    total_rows = df.height
    return {
        col: classify_column(
            df[col],
            total_rows,
            override_role=column_roles.get(col) if column_roles else None,
        )
        for col in df.columns
    }
