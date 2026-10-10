# =========================================================================
# Unit & Scenario Tests: Dataset Profiler Core Engine
# =========================================================================

from datetime import date
from pathlib import Path

import polars as pl
import pytest

from datapulse.profiling.profiler import DatasetProfiler

# =========================================================================
# CORE DATASET & DIMENSION PROFILING
# =========================================================================

class TestDatasetProfilerEngine:
    """Validate dataset overview, missing value calculation, duplicates, and quality."""

    def test_overview_and_dimensions(self, realistic_parquet_path: Path):
        profiler = DatasetProfiler(realistic_parquet_path)
        overview = profiler.get_overview()

        assert overview["file_name"] == "realistic_data.parquet"
        assert overview["row_count"] == 50
        assert overview["column_count"] == 12
        assert "amount" in overview["columns"]

    def test_missing_values_and_column_quality(self, realistic_parquet_path: Path):
        profiler = DatasetProfiler(realistic_parquet_path)
        missing = profiler.get_missing_values(sentinels=["NA", "N/A"])

        # Check mixed_missing column breakdown
        row_miss = missing.filter(pl.col("column") == "mixed_missing").to_dicts()[0]
        assert row_miss["null_count"] >= 1
        assert row_miss["empty_count"] >= 1
        assert row_miss["sentinel_count"] >= 2
        assert row_miss["total_missing_count"] >= 4

        # Check column quality table
        quality = profiler.get_column_quality()
        amt_q = quality.filter(pl.col("column") == "amount").to_dicts()[0]
        assert amt_q["category"] == "numeric"
        assert amt_q["missing_percentage"] == 0.0

    def test_duplicate_summary(self, realistic_parquet_path: Path):
        profiler = DatasetProfiler(realistic_parquet_path)
        summary = profiler.get_duplicate_summary()

        assert summary["total_rows"] == 50
        assert summary["unique_rows"] == 48
        assert summary["duplicate_rows"] == 2
        assert summary["duplicate_percentage"] == 4.0


# =========================================================================
# ROLE-SPECIFIC STATISTICAL AGGREGATIONS
# =========================================================================

class TestProfilerAggregations:
    """Validate numeric, categorical, and temporal summary aggregations."""

    def test_numeric_and_categorical_statistics(self, realistic_parquet_path: Path):
        profiler = DatasetProfiler(realistic_parquet_path)

        # Numeric stats
        num_stats = profiler.get_numeric_statistics()
        assert "amount" in num_stats.columns
        assert "statistic" in num_stats.columns

        # Categorical stats
        cat_stats = profiler.get_categorical_statistics()
        cat_col = cat_stats.filter(pl.col("column") == "category").to_dicts()[0]
        assert cat_col["unique_count"] == 4

    def test_temporal_statistics(self, tmp_path: Path):
        data = pl.DataFrame(
            {
                "trip_date": pl.Series(
                    "trip_date",
                    [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 1)],
                    dtype=pl.Date,
                )
            }
        )
        file_path = tmp_path / "temporal.parquet"
        data.write_parquet(file_path)

        profiler = DatasetProfiler(file_path)
        stats = profiler.get_temporal_statistics()
        assert stats.height == 1
        assert stats["column"][0] == "trip_date"
        assert stats["minimum"][0] == "2025-01-01"
        assert stats["maximum"][0] == "2025-01-02"
        assert stats["unique_count"][0] == 2


# =========================================================================
# PROFILER INPUT VALIDATION
# =========================================================================

class TestProfilerValidation:
    """Validate exception handling for nonexistent or unsupported files."""

    def test_rejects_missing_or_unsupported(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            DatasetProfiler(tmp_path / "nonexistent.parquet")

        txt_file = tmp_path / "sample.unsupported"
        txt_file.write_text("data", encoding="utf-8")
        with pytest.raises(ValueError):
            DatasetProfiler(txt_file)
