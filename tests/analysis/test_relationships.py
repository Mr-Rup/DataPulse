# =========================================================================
# Unit & Scenario Tests: Relationships & Primary Key Discovery
# =========================================================================

import polars as pl
import pytest

from datapulse import analyze
from datapulse.analysis.relationships import (
    compute_correlations,
    evaluate_collinear_findings,
    find_key_candidates,
)
from datapulse.models.report import ColumnProfile, CorrelationPair

# =========================================================================
# CORRELATION ANALYSIS & SAFEGUARDS
# =========================================================================

class TestCorrelationAnalysis:
    """Validate Pearson/Spearman computation, safeguards, and collinearity alerts."""

    def test_correlation_computation_and_invariants(self):
        # Perfect positive and negative correlations
        df = pl.DataFrame(
            {
                "x": [1.0, 2.0, 3.0, 4.0, 5.0],
                "y": [2.0, 4.0, 6.0, 8.0, 10.0],
                "z": [5.0, 4.0, 3.0, 2.0, 1.0],
                "const": [5.0, 5.0, 5.0, 5.0, 5.0],
            }
        )
        pairs = compute_correlations(df, ["x", "y", "z", "const"])
        assert len(pairs) == 3  # const column skipped (zero variance)

        xy = next(p for p in pairs if {p.column_a, p.column_b} == {"x", "y"})
        assert xy.coefficient == pytest.approx(1.0, abs=0.001)

        xz = next(p for p in pairs if {p.column_a, p.column_b} == {"x", "z"})
        assert xz.coefficient == pytest.approx(-1.0, abs=0.001)

        # Very small datasets (<3 rows) should produce empty pairs
        df_small = pl.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
        assert compute_correlations(df_small, ["a", "b"]) == []

    def test_correlation_safeguards_and_common_observations(self):
        # Joint non-null observations tracking (Nab)
        df_missing = pl.DataFrame(
            {
                "x": [1.0, 2.0, None, 4.0, 5.0],
                "y": [10.0, None, 30.0, 40.0, 50.0],
            }
        )
        pairs_missing = compute_correlations(df_missing, ["x", "y"])
        assert len(pairs_missing) == 1
        assert pairs_missing[0].common_observations == 3  # Only rows 0, 3, 4

        # Maximum correlation columns safeguard (variance ranking)
        wide_data = {
            f"col_{i}": [float(j * (i + 1)) for j in range(10)] for i in range(6)
        }
        df_wide = pl.DataFrame(wide_data)
        capped_pairs = compute_correlations(
            df_wide, list(wide_data.keys()), max_correlation_columns=3
        )
        assert len(capped_pairs) == 3  # 3 choose 2 = 3 pairs max

    def test_collinear_findings_evaluation(self):
        pairs = [
            CorrelationPair(column_a="fare", column_b="total", coefficient=0.98),
            CorrelationPair(column_a="speed", column_b="distance", coefficient=0.45),
        ]
        findings = evaluate_collinear_findings(pairs, threshold=0.90)
        assert len(findings) == 1
        assert findings[0].rule_id == "collinear_pair"
        assert findings[0].affected_columns == ["fare", "total"]


# =========================================================================
# PRIMARY KEY CANDIDATE DISCOVERY
# =========================================================================

class TestKeyCandidateDiscovery:
    """Validate primary key heuristic identification and end-to-end integration."""

    def test_find_key_candidates_logic(self):
        cols = [
            ColumnProfile(
                name="id", physical_type="Int64", null_count=0, unique_count=10
            ),
            ColumnProfile(
                name="code_with_null",
                physical_type="String",
                null_count=1,
                unique_count=9,
            ),
            ColumnProfile(
                name="category", physical_type="String", null_count=0, unique_count=3
            ),
        ]
        keys = find_key_candidates(cols, 10)
        assert len(keys) == 1
        assert keys[0].column == "id"
        assert keys[0].is_primary_key_candidate is True

    def test_end_to_end_relationships_pipeline(self, tmp_path):
        df = pl.DataFrame(
            {
                "row_id": [1, 2, 3, 4, 5],
                "units": [10.0, 20.0, 30.0, 40.0, 50.0],
                "revenue": [100.0, 200.0, 300.0, 400.0, 500.0],
            }
        )
        file_path = tmp_path / "relationships.parquet"
        df.write_parquet(file_path)

        report = analyze(file_path)

        # Primary key candidate
        pk_names = [
            k.column for k in report.key_candidates if k.is_primary_key_candidate
        ]
        assert "row_id" in pk_names

        # Perfect correlation and collinearity finding
        assert len(report.correlations) == 1
        assert report.correlations[0].coefficient == pytest.approx(1.0, abs=0.001)
        assert any(f.rule_id == "collinear_pair" for f in report.findings)
