# =========================================================================
# Unit & Scenario Tests: Role-Specific Statistical Profilers
# =========================================================================

from datetime import datetime

import polars as pl

from datapulse import analyze
from datapulse.profiling.boolean import profile_boolean
from datapulse.profiling.categorical import profile_categorical
from datapulse.profiling.column_profiler import profile_column
from datapulse.profiling.identifier import profile_identifier
from datapulse.profiling.numeric import profile_numeric
from datapulse.profiling.temporal import profile_temporal
from datapulse.profiling.text import profile_text

# =========================================================================
# ROLE-SPECIFIC STATISTICAL EXTRACTORS
# =========================================================================

class TestRoleSpecificProfilers:
    """Validate statistics calculation for numeric, categorical, temporal, boolean, text, and IDs."""

    def test_numeric_and_null_profiling(self):
        series = pl.Series("fares", [10.0, -5.0, 0.0, 20.0, 15.0])
        stats = profile_numeric(series, 5)

        assert stats["count"] == 5
        assert stats["zeros_count"] == 1
        assert stats["negatives_count"] == 1
        assert stats["min"] == -5.0
        assert stats["max"] == 20.0
        assert stats["median"] == 10.0
        assert stats["skewness"] is not None

        # All-null numeric series
        empty_s = pl.Series("empty", [None, None], dtype=pl.Float64)
        empty_stats = profile_numeric(empty_s, 2)
        assert empty_stats["count"] == 0
        assert empty_stats["mean"] is None

    def test_categorical_and_temporal_profiling(self):
        # Categorical
        cat_s = pl.Series("city", ["NY", "LA", "NY", "SF", "NY", "LA"] * 10)
        cat_stats = profile_categorical(cat_s, len(cat_s), max_categories=2)
        assert cat_stats["count"] == 60
        assert cat_stats["unique_count"] == 3
        top_cats = cat_stats["top_categories"]
        assert isinstance(top_cats, list)
        assert len(top_cats) == 2
        assert top_cats[0]["value"] == "NY"
        assert top_cats[0]["percentage"] == 50.0

        # Temporal
        temp_s = pl.Series(
            "dates",
            [datetime(2025, 1, 1), datetime(2025, 1, 11), datetime(2025, 1, 6)],
            dtype=pl.Datetime,
        )
        temp_stats = profile_temporal(temp_s, 3)
        assert temp_stats["count"] == 3
        assert temp_stats["minimum"] == "2025-01-01 00:00:00"
        assert temp_stats["maximum"] == "2025-01-11 00:00:00"
        assert temp_stats["span_days"] == 10.0

    def test_boolean_text_and_identifier_profiling(self):
        # Boolean native and 0/1 int
        bool_s = pl.Series("flag", [True, False, True, True])
        b_stats = profile_boolean(bool_s, 4)
        assert b_stats["true_count"] == 3
        assert b_stats["true_percentage"] == 75.0

        int_flag_s = pl.Series("flag_int", [1, 0, 1, 0, 1])
        int_b_stats = profile_boolean(int_flag_s, 5)
        assert int_b_stats["true_count"] == 3

        # Text
        text_s = pl.Series(
            "comments", ["Note one.", "Longer customer feedback note.", ""]
        )
        t_stats = profile_text(text_s, 3)
        assert t_stats["count"] == 3
        assert t_stats["empty_count"] == 1

        # Identifier
        id_s = pl.Series("user_id", [101, 102, 103, 101, 104])
        id_stats = profile_identifier(id_s, 5)
        assert id_stats["unique_count"] == 4
        assert id_stats["duplicate_count"] == 1


# =========================================================================
# DISPATCHER & END-TO-END PROFILING
# =========================================================================

class TestColumnProfilerDispatcher:
    """Validate dynamic role-based dispatcher and integrated profiling."""

    def test_dispatcher_routing(self):
        s_num = pl.Series("num", [1.0, 2.0])
        s_cat = pl.Series("cat", ["A", "B"])
        s_const = pl.Series("const", [99, 99])

        assert "mean" in profile_column(s_num, 2, "numeric")
        assert "top_categories" in profile_column(s_cat, 2, "categorical")
        assert "constant_value" in profile_column(s_const, 2, "constant")

    def test_end_to_end_role_profiling(self, realistic_parquet_path):
        report = analyze(realistic_parquet_path)
        col_map = {c.name: c for c in report.columns}

        assert col_map["amount"].inferred_role == "numeric"
        assert "mean" in col_map["amount"].statistics

        assert col_map["category"].inferred_role == "categorical"
        assert "top_categories" in col_map["category"].statistics

        assert col_map["is_active"].inferred_role == "boolean"
        assert "true_percentage" in col_map["is_active"].statistics
