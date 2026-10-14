# =========================================================================
# DataPulse Domain Constraints & Outlier Quality Rules
# Range restrictions, unexpected negative quantities, and Tukey outliers.
# =========================================================================

import polars as pl

from datapulse.analysis.quality_rules.constants import NON_NEGATIVE_KEYWORDS
from datapulse.models.report import ColumnProfile, Finding

# =========================================================================
# RANGE & DOMAIN INTEGRITY CHECKS
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


# =========================================================================
# NUMERIC DISTRIBUTION OUTLIER CHECKS
# =========================================================================

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
