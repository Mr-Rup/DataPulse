# =========================================================================
# DataPulse String Role Inference Rules
# Disambiguation of freeform text, discrete categories, and string IDs.
# =========================================================================

import polars as pl

from datapulse.analysis.column_classifier.models import ColumnClassification

# =========================================================================
# STRING ROLE CLASSIFIER
# =========================================================================

def classify_string_series(
    series: pl.Series,
    dtype: pl.DataType,
    name: str,
    name_lower: str,
    non_null: pl.Series,
    total_rows: int,
    cardinality_ratio: float,
) -> ColumnClassification:
    """Classify physical string and categorical series into semantic roles."""
    has_str_id_hint = (
        any(name_lower.endswith(sfx) for sfx in ("_id", "id", "_key", "key"))
        or name_lower.endswith("uuid")
    )
    if has_str_id_hint:
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="identifier",
            confidence=0.9,
            reason="String identifier naming hint",
            alternative_roles=["categorical"],
        )

    # High cardinality strings (e.g. user tokens, session hashes)
    if cardinality_ratio > 0.9 and total_rows > 100:
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="identifier",
            confidence=0.85,
            reason="High-uniqueness string column",
            alternative_roles=["categorical"],
        )

    # Long freeform text content (e.g. comments, user reviews, descriptions)
    if dtype == pl.String and non_null.len() > 0:
        sample_str = non_null.head(100)
        avg_len = sample_str.str.len_bytes().mean()
        if isinstance(avg_len, (int, float)) and avg_len > 40:
            return ColumnClassification(
                name=name,
                physical_type=str(dtype),
                inferred_role="text",
                confidence=0.85,
                reason="Long freeform text content",
                alternative_roles=["categorical"],
            )

    return ColumnClassification(
        name=name,
        physical_type=str(dtype),
        inferred_role="categorical",
        confidence=0.9,
        reason="Discrete string categories",
        alternative_roles=[],
    )
