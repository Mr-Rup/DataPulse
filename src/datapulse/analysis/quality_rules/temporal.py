# =========================================================================
# DataPulse Temporal Chronology Rules
# Automated discovery of chronological inversions across event sequences.
# =========================================================================

import polars as pl

from datapulse.analysis.quality_rules.constants import (
    CHRONOLOGY_PAIRS,
    DYNAMIC_TEMPORAL_SUFFIX_PAIRS,
)
from datapulse.models.report import Finding

# =========================================================================
# CHRONOLOGY INVERSION CHECKS
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
