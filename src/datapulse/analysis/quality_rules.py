# =========================================================================
# DataPulse Quality Rules Engine
# Automated heuristics for identifying anomalies, severe missingness,
# duplicates, range violations, outliers, and chronological inversions.
# =========================================================================

import polars as pl

from datapulse.models.report import (
    ColumnProfile,
    DuplicateSummary,
    Finding,
)

# =========================================================================
# DOMAIN HEURISTICS & STATIC RULE DEFINITIONS
# =========================================================================

# Substrings commonly associated with quantities that cannot physically be negative
NON_NEGATIVE_KEYWORDS: tuple[str, ...] = (
    "fare",
    "amount",
    "distance",
    "price",
    "cost",
    "count",
    "passenger",
    "trip",
    "duration",
    "age",
    "qty",
    "quantity",
    "length",
    "width",
    "height",
    "weight",
    "volume",
    "speed",
    "fee",
    "tip",
    "toll",
)

# Standard predefined pairs of start-and-end event timestamps
CHRONOLOGY_PAIRS: tuple[tuple[str, str], ...] = (
    ("tpep_pickup_datetime", "tpep_dropoff_datetime"),
    ("pickup_datetime", "dropoff_datetime"),
    ("started_at", "ended_at"),
    ("start_time", "end_time"),
    ("start_date", "end_date"),
    ("created_at", "updated_at"),
    ("valid_from", "valid_to"),
    ("departure_time", "arrival_time"),
)

# Dynamic suffix pairings used to automatically discover paired temporal columns
DYNAMIC_TEMPORAL_SUFFIX_PAIRS: tuple[tuple[str, str], ...] = (
    ("_start", "_end"),
    ("_begin", "_finish"),
    ("_pickup", "_dropoff"),
    ("_opened", "_closed"),
    ("_created", "_updated"),
    ("_dispatched", "_received"),
    ("_departure", "_arrival"),
    ("_in", "_out"),
)


# =========================================================================
# COMPLETENESS & STRUCTURAL QUALITY RULES
# =========================================================================

def check_missingness(columns: list[ColumnProfile]) -> list[Finding]:
    """Check for columns with severe (>=50%) or moderate (>=20%) missing values."""
    findings: list[Finding] = []
    for col in columns:
        if col.missing_percentage >= 50.0:
            findings.append(
                Finding(
                    rule_id="high_missingness",
                    severity="critical",
                    title="Severe missingness",
                    description=(
                        f"Column '{col.name}' has {col.missing_percentage:.1f}% "
                        f"missing values ({col.total_missing_count:,} missing)."
                    ),
                    affected_columns=[col.name],
                    affected_rows=col.total_missing_count,
                    affected_percentage=col.missing_percentage,
                )
            )
        elif col.missing_percentage >= 20.0:
            findings.append(
                Finding(
                    rule_id="high_missingness",
                    severity="warning",
                    title="Moderate missingness",
                    description=(
                        f"Column '{col.name}' has {col.missing_percentage:.1f}% "
                        f"missing values ({col.total_missing_count:,} missing)."
                    ),
                    affected_columns=[col.name],
                    affected_rows=col.total_missing_count,
                    affected_percentage=col.missing_percentage,
                )
            )
    return findings


def check_duplicates(duplicates: DuplicateSummary) -> list[Finding]:
    """Check for duplicate rows across the dataset."""
    findings: list[Finding] = []
    if duplicates.duplicate_rows > 0:
        severity = "critical" if duplicates.duplicate_percentage >= 10.0 else "warning"
        findings.append(
            Finding(
                rule_id="duplicate_rows",
                severity=severity,
                title="Duplicate rows detected",
                description=(
                    f"Found {duplicates.duplicate_rows:,} duplicate rows "
                    f"({duplicates.duplicate_percentage:.2f}% of total)."
                ),
                affected_columns=[],
                affected_rows=duplicates.duplicate_rows,
                affected_percentage=duplicates.duplicate_percentage,
            )
        )
    return findings


def check_constant_columns(columns: list[ColumnProfile]) -> list[Finding]:
    """Check for columns with zero variance (single distinct value)."""
    findings: list[Finding] = []
    for col in columns:
        if col.inferred_role == "constant" or (
            col.unique_count == 1 and col.null_count == 0
        ):
            findings.append(
                Finding(
                    rule_id="constant_column",
                    severity="warning",
                    title="Constant column",
                    description=(
                        f"Column '{col.name}' contains only 1 distinct value; "
                        "it provides no predictive variance."
                    ),
                    affected_columns=[col.name],
                    affected_rows=col.unique_count,
                    affected_percentage=100.0,
                )
            )
    return findings


def check_high_cardinality(columns: list[ColumnProfile]) -> list[Finding]:
    """Check for categorical columns with suspiciously high cardinality (>50%)."""
    findings: list[Finding] = []
    for col in columns:
        if col.inferred_role == "categorical":
            card_pct = float(col.statistics.get("cardinality_percentage", 0.0))
            if card_pct > 50.0 and col.unique_count > 20:
                findings.append(
                    Finding(
                        rule_id="high_cardinality_categorical",
                        severity="warning",
                        title="High cardinality categorical",
                        description=(
                            f"Column '{col.name}' has cardinality ratio of "
                            f"{card_pct:.1f}% ({col.unique_count:,} distinct values); "
                            "consider treating as identifier."
                        ),
                        affected_columns=[col.name],
                        affected_rows=col.unique_count,
                        affected_percentage=card_pct,
                    )
                )
    return findings


# =========================================================================
# NUMERIC & DOMAIN CONSTRAINT RULES
# =========================================================================

def check_negative_values(
    columns: list[ColumnProfile],
    allowed_negative_columns: list[str] | None = None,
    non_negative_columns: list[str] | None = None,
) -> list[Finding]:
    """Check for unexpected negative numbers in conventionally non-negative columns."""
    findings: list[Finding] = []
    allowed_set = set(allowed_negative_columns or [])

    # If explicit target list is provided, enforce strictly on those columns
    if non_negative_columns is not None:
        target_cols = set(non_negative_columns) - allowed_set
        for col in columns:
            if col.name in target_cols and col.inferred_role in ("numeric", "discrete"):
                neg_count = int(col.statistics.get("negatives_count", 0))
                neg_pct = float(col.statistics.get("negatives_percentage", 0.0))
                if neg_count > 0:
                    findings.append(
                        Finding(
                            rule_id="unexpected_negatives",
                            severity="warning",
                            title="Unexpected negative values",
                            description=(
                                f"Column '{col.name}' contains {neg_count:,} "
                                f"negative values ({neg_pct:.2f}%)."
                            ),
                            affected_columns=[col.name],
                            affected_rows=neg_count,
                            affected_percentage=neg_pct,
                        )
                    )
        return findings

    # Default heuristic checks using domain keyword matching
    for col in columns:
        if col.name in allowed_set:
            continue
        if col.inferred_role in ("numeric", "discrete"):
            name_lower = col.name.lower()
            if any(kw in name_lower for kw in NON_NEGATIVE_KEYWORDS):
                neg_count = int(col.statistics.get("negatives_count", 0))
                neg_pct = float(col.statistics.get("negatives_percentage", 0.0))
                if neg_count > 0:
                    findings.append(
                        Finding(
                            rule_id="unexpected_negatives",
                            severity="warning",
                            title="Unexpected negative values",
                            description=(
                                f"Column '{col.name}' contains {neg_count:,} "
                                f"negative values ({neg_pct:.2f}%)."
                            ),
                            affected_columns=[col.name],
                            affected_rows=neg_count,
                            affected_percentage=neg_pct,
                        )
                    )
    return findings


def check_numeric_outliers(
    columns: list[ColumnProfile],
    df: pl.DataFrame | None,
) -> list[Finding]:
    """Identify distribution tail observations using standard Tukey 1.5x IQR bounds."""
    if df is None:
        return []

    findings: list[Finding] = []
    total_rows = df.height
    if total_rows < 10:
        return []

    for col in columns:
        if col.inferred_role == "numeric" and col.name in df.columns:
            stats = col.statistics
            p25 = stats.get("p25")
            p75 = stats.get("p75")
            iqr = stats.get("iqr")

            if (
                isinstance(p25, (int, float))
                and isinstance(p75, (int, float))
                and isinstance(iqr, (int, float))
                and iqr > 0
            ):
                lower_bound = p25 - 1.5 * iqr
                upper_bound = p75 + 1.5 * iqr

                # Fast Polars boolean sum for out-of-bounds rows
                series = df[col.name].drop_nulls()
                outliers = int(((series < lower_bound) | (series > upper_bound)).sum())
                if outliers > 0:
                    outlier_pct = round((outliers / total_rows) * 100, 2)
                    findings.append(
                        Finding(
                            rule_id="numeric_outliers",
                            severity="info",
                            title="Distribution tail values (IQR)",
                            description=(
                                f"Column '{col.name}' has {outliers:,} observations "
                                f"({outlier_pct:.2f}%) outside 1.5x IQR bounds "
                                f"[{lower_bound:.2f}, {upper_bound:.2f}]. "
                                "Common in heavy-tailed empirical distributions."
                            ),
                            affected_columns=[col.name],
                            affected_rows=outliers,
                            affected_percentage=outlier_pct,
                        )
                    )
    return findings


# =========================================================================
# TEMPORAL CHRONOLOGY INVERSION RULES
# =========================================================================

def check_chronology_inversion(df: pl.DataFrame | None) -> list[Finding]:
    """Check for temporal inversion where an end timestamp precedes its start."""
    if df is None:
        return []

    findings: list[Finding] = []
    cols_set = set(df.columns)
    evaluated_pairs: set[tuple[str, str]] = set()
    candidate_pairs: list[tuple[str, str]] = list(CHRONOLOGY_PAIRS)

    # Dynamically match temporal sibling columns sharing a common prefix
    temporal_cols = [c for c in df.columns if df[c].dtype.is_temporal()]
    for col_a in temporal_cols:
        col_a_lower = col_a.lower()
        for start_sfx, end_sfx in DYNAMIC_TEMPORAL_SUFFIX_PAIRS:
            if col_a_lower.endswith(start_sfx):
                prefix = col_a[: len(col_a) - len(start_sfx)]
                # Look for corresponding sibling column with the end suffix
                for col_b in temporal_cols:
                    if col_b != col_a and col_b.lower() == f"{prefix.lower()}{end_sfx}":
                        candidate_pairs.append((col_a, col_b))

    for start_name, end_name in candidate_pairs:
        pair_key = (start_name, end_name)
        if pair_key in evaluated_pairs:
            continue
        evaluated_pairs.add(pair_key)

        if start_name in cols_set and end_name in cols_set:
            start_s = df[start_name]
            end_s = df[end_name]

            if start_s.dtype.is_temporal() and end_s.dtype.is_temporal():
                # Compare only rows where both start and end timestamps are populated
                valid_mask = start_s.is_not_null() & end_s.is_not_null()
                inversions = int(
                    (end_s.filter(valid_mask) < start_s.filter(valid_mask)).sum()
                )

                if inversions > 0:
                    total_valid = int(valid_mask.sum())
                    pct = (
                        round((inversions / total_valid) * 100, 2)
                        if total_valid > 0
                        else 0.0
                    )
                    findings.append(
                        Finding(
                            rule_id="chronology_inversion",
                            severity="critical",
                            title="Chronological inversion",
                            description=(
                                f"Found {inversions:,} rows ({pct:.2f}%) where "
                                f"'{end_name}' occurs before '{start_name}'."
                            ),
                            affected_columns=[start_name, end_name],
                            affected_rows=inversions,
                            affected_percentage=pct,
                        )
                    )
    return findings


# =========================================================================
# MASTER QUALITY RULE EVALUATION PIPELINE
# =========================================================================

def evaluate_quality_rules(
    columns: list[ColumnProfile],
    duplicates: DuplicateSummary,
    df: pl.DataFrame | None = None,
    *,
    allowed_negative_columns: list[str] | None = None,
    non_negative_columns: list[str] | None = None,
) -> list[Finding]:
    """Run all automated data quality and anomaly rules across dataset profiles."""
    findings: list[Finding] = []
    findings.extend(check_missingness(columns))
    findings.extend(check_duplicates(duplicates))
    findings.extend(check_constant_columns(columns))
    findings.extend(check_high_cardinality(columns))
    findings.extend(
        check_negative_values(
            columns,
            allowed_negative_columns=allowed_negative_columns,
            non_negative_columns=non_negative_columns,
        )
    )
    findings.extend(check_numeric_outliers(columns, df))
    findings.extend(check_chronology_inversion(df))
    return findings
