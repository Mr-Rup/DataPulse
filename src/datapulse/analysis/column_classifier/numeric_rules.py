# =========================================================================
# DataPulse Numeric Role Inference Rules
# Disambiguation of continuous floats, binary indicators, discrete codes, & IDs.
# =========================================================================

import polars as pl

from datapulse.analysis.column_classifier.hints import (
    CODE_NAME_HINTS,
    METRIC_NAME_HINTS,
)
from datapulse.analysis.column_classifier.models import ColumnClassification

# =========================================================================
# NUMERIC ROLE CLASSIFIER
# =========================================================================

def classify_numeric_series(
    series: pl.Series,
    dtype: pl.DataType,
    name: str,
    name_lower: str,
    non_null: pl.Series,
    unique_count: int,
    total_rows: int,
    cardinality_ratio: float,
    has_id_hint: bool,
) -> ColumnClassification:
    """Classify physical numeric series into semantic analytical roles."""
    # Check if float column contains solely whole integers (e.g. 1001.0)
    is_integer_valued = False
    if dtype.is_float() and non_null.len() > 0:
        finite = non_null.filter(non_null.is_finite())
        if finite.len() > 0:
            frac = (finite - finite.floor()).abs().max()
            if frac == 0.0:
                is_integer_valued = True

    # Pure continuous measurement (floats with fractional parts)
    if dtype.is_float() and not is_integer_valued:
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="numeric",
            confidence=0.95,
            reason="Continuous floating-point measurement",
            alternative_roles=["continuous"],
        )

    # Binary indicator encoded as numeric {0, 1}
    if unique_count == 2:
        unique_vals = set(non_null.head(100).unique().to_list())
        if unique_vals.issubset({0, 1}):
            return ColumnClassification(
                name=name,
                physical_type=str(dtype),
                inferred_role="boolean",
                confidence=0.9,
                reason="Binary 0/1 numeric indicator",
                alternative_roles=["categorical", "numeric"],
            )

    # Numeric column with identifier naming hint (e.g. customer_id, store_code)
    if has_id_hint:
        if cardinality_ratio >= 0.8:
            return ColumnClassification(
                name=name,
                physical_type=str(dtype),
                inferred_role="identifier",
                confidence=0.9,
                reason="Identifier naming hint with high distinctness",
                alternative_roles=["numeric"],
            )
        if unique_count <= 20:
            return ColumnClassification(
                name=name,
                physical_type=str(dtype),
                inferred_role="categorical",
                confidence=0.85,
                reason="Low-cardinality discrete code/identifier",
                alternative_roles=["identifier", "numeric"],
            )
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="identifier",
            confidence=0.9,
            reason="Identifier naming hint with moderate-to-high cardinality",
            alternative_roles=["numeric"],
        )

    has_metric_hint = any(hint in name_lower for hint in METRIC_NAME_HINTS)
    has_code_hint = any(hint in name_lower for hint in CODE_NAME_HINTS)

    # Discrete numeric codes (e.g. payment_type: 1, 2, 3, 4)
    if (
        (has_code_hint or not has_metric_hint)
        and unique_count <= 20
        and cardinality_ratio <= 0.5
    ):
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="categorical",
            confidence=0.85 if has_code_hint else 0.8,
            reason="Low-cardinality discrete numeric codes",
            alternative_roles=["numeric", "discrete"],
        )

    # Monotonic or near-unique integer sequences without explicit naming hints
    if cardinality_ratio > 0.9 and total_rows > 100:
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="identifier",
            confidence=0.85,
            reason="Near-unique numeric sequence",
            alternative_roles=["numeric"],
        )

    return ColumnClassification(
        name=name,
        physical_type=str(dtype),
        inferred_role="numeric",
        confidence=0.9,
        reason="Discrete numeric measurement",
        alternative_roles=["discrete"],
    )
