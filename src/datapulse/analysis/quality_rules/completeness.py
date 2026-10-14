# =========================================================================
# DataPulse Completeness & Structural Quality Rules
# Detection of severe missingness, duplicate rows, and zero variance columns.
# =========================================================================

from datapulse.models.report import (
    ColumnProfile,
    DuplicateSummary,
    Finding,
)

# =========================================================================
# MISSINGNESS & DUPLICATE CHECKS
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


# =========================================================================
# VARIANCE & CARDINALITY CHECKS
# =========================================================================

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
