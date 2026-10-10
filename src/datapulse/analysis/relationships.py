import math
from typing import Literal

import polars as pl

from datapulse.models.report import (
    ColumnProfile,
    CorrelationPair,
    Finding,
    KeyCandidate,
)


def compute_correlations(
    df: pl.DataFrame,
    numeric_cols: list[str],
    method: Literal["pearson", "spearman"] = "pearson",
    min_threshold: float = 0.0,
    max_correlation_columns: int = 30,
) -> list[CorrelationPair]:
    """Compute pairwise numeric correlation coefficients and joint sample sizes."""

    # Filter to numeric columns actually present in df with non-constant variance
    valid_cols: list[str] = []
    for col in numeric_cols:
        if col in df.columns and df[col].dtype.is_numeric():
            series = df[col].drop_nulls()
            if series.len() > 2 and series.n_unique() > 1:
                valid_cols.append(col)

    if len(valid_cols) < 2 or df.height < 3:
        return []

    # Safeguard against combinatorial explosion on high-dimensional datasets
    if len(valid_cols) > max_correlation_columns:
        # Prioritize columns with higher non-null completeness
        valid_cols.sort(key=lambda c: df[c].null_count())
        valid_cols = valid_cols[:max_correlation_columns]

    pairs: list[tuple[str, str]] = [
        (col_a, col_b)
        for i, col_a in enumerate(valid_cols)
        for col_b in valid_cols[i + 1 :]
    ]

    exprs: list[pl.Expr] = []
    for idx, (col_a, col_b) in enumerate(pairs):
        exprs.append(pl.corr(col_a, col_b, method=method).alias(f"c_{idx}"))
        exprs.append(
            (pl.col(col_a).is_not_null() & pl.col(col_b).is_not_null())
            .sum()
            .alias(f"n_{idx}")
        )

    results_df = df.select(exprs)
    results: list[CorrelationPair] = []

    for idx, (col_a, col_b) in enumerate(pairs):
        raw_val = results_df[f"c_{idx}"][0]
        n_obs = int(results_df[f"n_{idx}"][0] or 0)

        if n_obs >= 2 and isinstance(raw_val, (int, float)) and not math.isnan(raw_val):
            coef = round(float(raw_val), 4)
            if abs(coef) >= min_threshold:
                results.append(
                    CorrelationPair(
                        column_a=col_a,
                        column_b=col_b,
                        coefficient=coef,
                        method=method,
                        common_observations=n_obs,
                    )
                )

    # Sort descending by absolute correlation strength
    results.sort(key=lambda p: abs(p.coefficient), reverse=True)
    return results


def find_key_candidates(
    columns: list[ColumnProfile], total_rows: int
) -> list[KeyCandidate]:
    """Identify primary key candidates with 100% uniqueness and zero missing values."""

    if total_rows == 0:
        return []

    candidates: list[KeyCandidate] = []
    for col in columns:
        if col.null_count == 0 and col.unique_count == total_rows:
            candidates.append(
                KeyCandidate(
                    column=col.name,
                    unique_count=col.unique_count,
                    is_primary_key_candidate=True,
                )
            )

    return candidates


def evaluate_collinear_findings(
    correlations: list[CorrelationPair], threshold: float = 0.90
) -> list[Finding]:
    """Flag highly collinear pairs as potential leakage or redundancy."""

    findings: list[Finding] = []
    for pair in correlations:
        if abs(pair.coefficient) >= threshold:
            findings.append(
                Finding(
                    rule_id="collinear_pair",
                    severity="warning",
                    title="High collinearity detected",
                    description=(
                        f"Columns '{pair.column_a}' and '{pair.column_b}' have "
                        f"{pair.method} correlation r = {pair.coefficient:.3f}; "
                        "potential feature redundancy or leakage."
                    ),
                    affected_columns=[pair.column_a, pair.column_b],
                    affected_rows=0,
                    affected_percentage=0.0,
                )
            )

    return findings
