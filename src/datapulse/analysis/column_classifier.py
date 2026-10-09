from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True)
class ColumnClassification:
    """Analytical classification of a dataset column."""

    name: str
    physical_type: str
    inferred_role: str
    confidence: float
    reason: str


def classify_column(series: pl.Series, total_rows: int) -> ColumnClassification:
    """Infer the analytical role of a Polars Series."""

    name = series.name
    dtype = series.dtype
    name_lower = name.lower()

    if total_rows == 0 or series.null_count() == total_rows:
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="other",
            confidence=0.5,
            reason="All null or empty column",
        )

    non_null = series.drop_nulls()
    unique_count = non_null.n_unique()

    if unique_count <= 1:
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="constant",
            confidence=1.0,
            reason="Column contains only 1 distinct value",
        )

    if dtype == pl.Boolean:
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="boolean",
            confidence=1.0,
            reason="Physical boolean data type",
        )

    if dtype.is_temporal():
        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="temporal",
            confidence=1.0,
            reason="Physical temporal data type",
        )

    if dtype.is_numeric():
        if dtype.is_float():
            return ColumnClassification(
                name=name,
                physical_type=str(dtype),
                inferred_role="numeric",
                confidence=0.95,
                reason="Continuous floating-point measurement",
            )

        # Integer types
        if unique_count == 2:
            unique_vals = set(non_null.head(100).unique().to_list())
            if unique_vals.issubset({0, 1}):
                return ColumnClassification(
                    name=name,
                    physical_type=str(dtype),
                    inferred_role="boolean",
                    confidence=0.9,
                    reason="Binary 0/1 integer indicator",
                )

        has_id_hint = (
            name_lower.endswith("_id")
            or name_lower.endswith("id")
            or name_lower == "id"
            or name_lower.endswith("_key")
            or name_lower.endswith("key")
            or name_lower.endswith("code")
        )

        if has_id_hint:
            if unique_count <= 20:
                return ColumnClassification(
                    name=name,
                    physical_type=str(dtype),
                    inferred_role="categorical",
                    confidence=0.85,
                    reason="Low-cardinality integer with code/identifier naming hint",
                )
            return ColumnClassification(
                name=name,
                physical_type=str(dtype),
                inferred_role="identifier",
                confidence=0.9,
                reason="Identifier naming hint with moderate-to-high cardinality",
            )

        cardinality_ratio = unique_count / total_rows if total_rows > 0 else 0.0

        if unique_count <= 20 and (cardinality_ratio < 0.05 or total_rows < 100):
            return ColumnClassification(
                name=name,
                physical_type=str(dtype),
                inferred_role="categorical",
                confidence=0.8,
                reason="Low-cardinality discrete integer values",
            )

        if cardinality_ratio > 0.9 and total_rows > 100:
            return ColumnClassification(
                name=name,
                physical_type=str(dtype),
                inferred_role="identifier",
                confidence=0.85,
                reason="Near-unique integer sequence",
            )

        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="numeric",
            confidence=0.9,
            reason="Integer numeric measurement",
        )

    if dtype in (pl.String, pl.Categorical, pl.Enum):
        has_id_hint = (
            name_lower.endswith("_id")
            or name_lower == "id"
            or name_lower.endswith("uuid")
            or name_lower.endswith("_key")
        )
        if has_id_hint:
            return ColumnClassification(
                name=name,
                physical_type=str(dtype),
                inferred_role="identifier",
                confidence=0.9,
                reason="String identifier naming hint",
            )

        cardinality_ratio = unique_count / total_rows if total_rows > 0 else 0.0
        if cardinality_ratio > 0.9 and total_rows > 100:
            return ColumnClassification(
                name=name,
                physical_type=str(dtype),
                inferred_role="identifier",
                confidence=0.85,
                reason="High-uniqueness string column",
            )

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
                )

        return ColumnClassification(
            name=name,
            physical_type=str(dtype),
            inferred_role="categorical",
            confidence=0.9,
            reason="Discrete string categories",
        )

    return ColumnClassification(
        name=name,
        physical_type=str(dtype),
        inferred_role="other",
        confidence=0.5,
        reason=f"Unclassified physical type: {dtype}",
    )


def classify_columns(df: pl.DataFrame) -> dict[str, ColumnClassification]:
    """Classify all columns in a Polars DataFrame into analytical roles."""

    total_rows = df.height
    return {col: classify_column(df[col], total_rows) for col in df.columns}
