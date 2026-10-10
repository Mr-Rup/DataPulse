# =========================================================================
# DataPulse Column Classifier
# Heuristic inference engine mapping physical Polars data types into
# high-level analytical roles (numeric, categorical, temporal, etc.).
# =========================================================================

from dataclasses import dataclass, field

import polars as pl

# =========================================================================
# DATA STRUCTURES
# =========================================================================

@dataclass(frozen=True)
class ColumnClassification:
    """Analytical classification of a dataset column."""

    name: str
    physical_type: str
    inferred_role: str
    confidence: float
    reason: str
    alternative_roles: list[str] = field(default_factory=list)


# =========================================================================
# HEURISTIC CONSTANTS & PATTERNS
# =========================================================================

# Naming suffixes and tokens commonly indicating primary/foreign keys or codes
ID_SUFFIX_HINTS: tuple[str, ...] = (
    "_id",
    "id",
    "_key",
    "key",
    "code",
)

# Semantic substrings in column names indicating continuous metric measurements
METRIC_NAME_HINTS: tuple[str, ...] = (
    "fare",
    "amount",
    "price",
    "cost",
    "total",
    "fee",
    "tip",
    "units",
    "revenue",
    "count",
    "qty",
    "quantity",
    "val",
    "score",
    "temp",
    "speed",
    "distance",
    "rate",
    "pct",
    "percent",
)

# Semantic substrings in column names indicating discrete status or classification
CODE_NAME_HINTS: tuple[str, ...] = (
    "type",
    "status",
    "mode",
    "class",
    "group",
    "category",
)


# =========================================================================
# CORE COLUMN CLASSIFICATION ENGINE
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

    # -------------------------------------------------------------------------
    # Configuration Overrides & Degenerate Cases
    # -------------------------------------------------------------------------
    if override_role:
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role=override_role,
            confidence=1.0,
            reason="User-specified override in configuration",
            alternative_roles=[],
        )

    # Empty datasets or columns with 100% missing values
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

    # Zero variance columns (single distinct scalar value)
    if unique_count <= 1:
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="constant",
            confidence=1.0,
            reason="Column contains only 1 distinct value",
            alternative_roles=[],
        )

    # -------------------------------------------------------------------------
    # Invariant Physical Types (Boolean & Temporal)
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # Numeric Types (Integers, Floats, Indicators, Codes)
    # -------------------------------------------------------------------------
    if dtype.is_numeric():
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

    # -------------------------------------------------------------------------
    # String & Categorical Types (Identifiers, Text, Codes)
    # -------------------------------------------------------------------------
    if dtype in (pl.String, pl.Categorical, pl.Enum):
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

    # -------------------------------------------------------------------------
    # Fallback for Unknown / Complex Dtypes
    # -------------------------------------------------------------------------
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
