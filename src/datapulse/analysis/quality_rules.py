import polars as pl

from datapulse.models.report import (
    ColumnProfile,
    DuplicateSummary,
    Finding,
)

NON_NEGATIVE_KEYWORDS = (
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
    "rate",
    "fee",
    "tip",
    "toll",
)

CHRONOLOGY_PAIRS = (
    ("tpep_pickup_datetime", "tpep_dropoff_datetime"),
    ("pickup_datetime", "dropoff_datetime"),
    ("started_at", "ended_at"),
    ("start_time", "end_time"),
    ("start_date", "end_date"),
    ("created_at", "updated_at"),
    ("valid_from", "valid_to"),
    ("departure_time", "arrival_time"),
)


def check_missingness(columns: list[ColumnProfile]) -> list[Finding]:
    """Check for columns with severe or moderate missing values."""

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
                        f"missing values ({col.null_count:,} nulls)."
                    ),
                    affected_columns=[col.name],
                    affected_rows=col.null_count,
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
                        f"missing values ({col.null_count:,} nulls)."
                    ),
                    affected_columns=[col.name],
                    affected_rows=col.null_count,
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
    """Check for columns with zero variance (single value)."""

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
    """Check for categorical columns with suspiciously high cardinality."""

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


def check_negative_values(columns: list[ColumnProfile]) -> list[Finding]:
    """Check for unexpected negative numbers in conventionally non-negative columns."""

    findings: list[Finding] = []
    for col in columns:
        if col.inferred_role == "numeric":
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
    columns: list[ColumnProfile], df: pl.DataFrame | None
) -> list[Finding]:
    """Check for extreme numerical outliers using Tukey IQR rule."""

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

                series = df[col.name].drop_nulls()
                outliers = int(((series < lower_bound) | (series > upper_bound)).sum())
                if outliers > 0:
                    outlier_pct = round((outliers / total_rows) * 100, 2)
                    severity = "warning" if outlier_pct > 5.0 else "info"
                    findings.append(
                        Finding(
                            rule_id="numeric_outliers",
                            severity=severity,
                            title="Numeric outliers detected",
                            description=(
                                f"Column '{col.name}' has {outliers:,} values "
                                f"({outlier_pct:.2f}%) outside IQR bounds "
                                f"[{lower_bound:.2f}, {upper_bound:.2f}]."
                            ),
                            affected_columns=[col.name],
                            affected_rows=outliers,
                            affected_percentage=outlier_pct,
                        )
                    )
    return findings


def check_chronology_inversion(df: pl.DataFrame | None) -> list[Finding]:
    """Check for temporal inversion where end timestamp is earlier than start."""

    if df is None:
        return []

    findings: list[Finding] = []
    cols_set = set(df.columns)

    for start_name, end_name in CHRONOLOGY_PAIRS:
        if start_name in cols_set and end_name in cols_set:
            start_s = df[start_name]
            end_s = df[end_name]

            if start_s.dtype.is_temporal() and end_s.dtype.is_temporal():
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


def evaluate_quality_rules(
    columns: list[ColumnProfile],
    duplicates: DuplicateSummary,
    df: pl.DataFrame | None = None,
) -> list[Finding]:
    """Run all automated data quality and anomaly rules."""

    findings: list[Finding] = []
    findings.extend(check_missingness(columns))
    findings.extend(check_duplicates(duplicates))
    findings.extend(check_constant_columns(columns))
    findings.extend(check_high_cardinality(columns))
    findings.extend(check_negative_values(columns))
    findings.extend(check_numeric_outliers(columns, df))
    findings.extend(check_chronology_inversion(df))

    return findings
