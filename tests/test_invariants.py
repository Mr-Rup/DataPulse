# =============================================================================
# Unit & Scenario Tests: Mathematical Property Invariants
# =============================================================================

from pathlib import Path

from datapulse import analyze

# =============================================================================
# 1. MATHEMATICAL PROPERTY INVARIANTS
# =============================================================================


class TestMathematicalInvariants:
    """Validate mathematical and statistical bounds that must hold universally."""

    def test_missingness_and_duplicate_bounds(self, realistic_parquet_path: Path):
        report = analyze(realistic_parquet_path)
        total_rows = report.summary.row_count

        # Duplicates + Unique rows == Total rows
        assert (
            report.duplicates.unique_rows + report.duplicates.duplicate_rows
            == total_rows
        )

        for col in report.columns:
            # Missing breakdown sums to at least null + nan + empty
            expected_min = col.null_count + col.nan_count + col.empty_count
            assert col.total_missing_count >= expected_min

            # Missing percentage bounded in [0, 100]
            assert 0.0 <= col.missing_percentage <= 100.0

            # Unique count cannot exceed total rows
            assert 0 <= col.unique_count <= total_rows

    def test_numeric_ranges_and_correlation_bounds(self, realistic_parquet_path: Path):
        report = analyze(realistic_parquet_path)
        total_rows = report.summary.row_count

        # Numeric min <= median <= max and min <= mean <= max
        for col in report.columns:
            if col.inferred_role == "numeric" and col.statistics:
                stats = col.statistics
                min_v = stats.get("min")
                med_v = stats.get("median")
                max_v = stats.get("max")
                mean_v = stats.get("mean")

                if (
                    isinstance(min_v, (int, float))
                    and isinstance(med_v, (int, float))
                    and isinstance(max_v, (int, float))
                    and isinstance(mean_v, (int, float))
                ):
                    assert min_v <= med_v <= max_v
                    assert min_v <= mean_v <= max_v

        # Correlation bounds [-1.0, 1.0] and Nab in [2, total_rows]
        for pair in report.correlations:
            assert -1.0 <= pair.coefficient <= 1.0
            assert 2 <= pair.common_observations <= total_rows

    def test_key_candidate_invariants(self, realistic_parquet_path: Path):
        report = analyze(realistic_parquet_path)
        total_rows = report.summary.row_count

        for key in report.key_candidates:
            if key.is_primary_key_candidate:
                assert key.unique_count == total_rows
