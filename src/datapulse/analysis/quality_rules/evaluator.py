# =========================================================================
# DataPulse Quality Rules Evaluator
# Master orchestrator evaluating all completeness, domain, and temporal rules.
# =========================================================================

import polars as pl

from datapulse.analysis.quality_rules.completeness import (
    check_constant_columns,
    check_duplicates,
    check_high_cardinality,
    check_missingness,
)
from datapulse.analysis.quality_rules.constraints import (
    check_negative_values,
    check_numeric_outliers,
)
from datapulse.analysis.quality_rules.temporal import check_chronology_inversion
from datapulse.models.report import ColumnProfile, DuplicateSummary, Finding

# =========================================================================
# MASTER QUALITY EVALUATOR
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
