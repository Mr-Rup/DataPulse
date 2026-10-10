# =============================================================================
# Unit & Scenario Tests: Edge Cases & Boundary Conditions
# =============================================================================

from pathlib import Path

import polars as pl

from datapulse import analyze

# =============================================================================
# 1. BOUNDARY & UNUSUAL DATASET SHAPES
# =============================================================================


class TestDatasetEdgeCases:
    """Validate boundary behavior for extreme dimensions, types, and magnitudes."""

    def test_single_row_and_single_column(self, tmp_path: Path):
        # Single row
        r1_path = tmp_path / "single_row.csv"
        r1_path.write_text("id,val,category\n1,42.5,A\n", encoding="utf-8")
        rep_r1 = analyze(r1_path)
        assert rep_r1.summary.row_count == 1
        assert rep_r1.summary.column_count == 3
        assert rep_r1.correlations == []

        # Single column
        c1_path = tmp_path / "single_col.parquet"
        pl.DataFrame({"metric": [10.0, 20.0, 30.0, 40.0, 50.0]}).write_parquet(c1_path)
        rep_c1 = analyze(c1_path)
        assert rep_c1.summary.row_count == 5
        assert rep_c1.summary.column_count == 1
        assert rep_c1.correlations == []

    def test_all_null_nan_inf_constants(self, tmp_path: Path):
        # All null
        null_path = tmp_path / "all_null.csv"
        null_path.write_text("a,b,c\n,,\n,,\n,,\n", encoding="utf-8")
        rep_null = analyze(null_path)
        assert rep_null.summary.row_count == 3
        assert all(c.null_count == 3 for c in rep_null.columns)

        # All NaN
        nan_path = tmp_path / "all_nan.parquet"
        pl.DataFrame(
            {"nan_col": [float("nan"), float("nan"), float("nan")]}
        ).write_parquet(nan_path)
        rep_nan = analyze(nan_path)
        assert rep_nan.columns[0].nan_count == 3

        # All Inf
        inf_path = tmp_path / "all_inf.parquet"
        pl.DataFrame(
            {"inf_col": [float("inf"), float("-inf"), float("inf")]}
        ).write_parquet(inf_path)
        rep_inf = analyze(inf_path)
        assert rep_inf.columns[0].statistics.get("infinite_count") == 3

        # All Constant
        const_path = tmp_path / "constant.csv"
        const_path.write_text(
            "state,zip\nCA,94105\nCA,94105\nCA,94105\n", encoding="utf-8"
        )
        rep_const = analyze(const_path)
        assert any(f.rule_id == "constant_column" for f in rep_const.findings)

    def test_huge_magnitudes_and_unicode_headers(self, tmp_path: Path):
        # Huge numbers
        huge_path = tmp_path / "huge.parquet"
        pl.DataFrame({"huge": [1e20, -1e20, 1e-20, 0.0]}).write_parquet(huge_path)
        rep_huge = analyze(huge_path)
        assert rep_huge.summary.row_count == 4

        # Unicode and emojis in column headers
        uni_path = tmp_path / "unicode_headers.csv"
        uni_path.write_text(
            "📈 revenue (USD) / día,naïve_café,user.id@domain\n100,5,foo\n200,8,bar\n",
            encoding="utf-8",
        )
        rep_uni = analyze(uni_path)
        assert rep_uni.summary.column_count == 3
        assert "📈 revenue (USD) / día" in [c.name for c in rep_uni.columns]
