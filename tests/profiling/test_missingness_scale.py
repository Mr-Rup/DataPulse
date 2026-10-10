# =============================================================================
# Unit & Scenario Tests: Missingness Semantics & Pydantic Config Validation
# =============================================================================

from pathlib import Path

import polars as pl
import pytest
from pydantic import ValidationError

from datapulse import AnalysisConfig, analyze
from datapulse.profiling.numeric import profile_numeric
from datapulse.profiling.profiler import DatasetProfiler

# =============================================================================
# 1. UNIFIED MISSINGNESS ENGINE
# =============================================================================


class TestUnifiedMissingnessEngine:
    """Validate detection of nulls, NaNs, infinities, empty strings, and sentinels."""

    def test_missingness_breakdown_detection(self, tmp_path: Path):
        csv_file = tmp_path / "missingness.csv"
        data = {
            "id": list(range(1, 11)),
            "val_float": [
                1.0,
                2.0,
                None,
                float("nan"),
                float("inf"),
                float("-inf"),
                5.0,
                6.0,
                7.0,
                8.0,
            ],
            "val_text": [
                "apple",
                None,
                "",
                "   ",
                "N/A",
                "banana",
                "missing",
                "?",
                "null",
                "cherry",
            ],
        }
        pl.DataFrame(data).write_csv(csv_file)

        sentinels = ["N/A", "missing", "?", "null"]
        prof = DatasetProfiler(csv_file)
        missing_df = prof.get_missing_values(sentinels=sentinels)
        missing_map = {row["column"]: row for row in missing_df.iter_rows(named=True)}

        # val_float: 1 null, 1 nan, 0 empty, 0 sentinel -> total_missing = 2
        float_miss = missing_map["val_float"]
        assert float_miss["null_count"] == 1
        assert float_miss["nan_count"] == 1
        assert float_miss["total_missing_count"] == 2
        assert float_miss["missing_percentage"] == 20.0

        # val_text: 1 null, 2 empty/whitespace, 4 sentinels -> total = 7
        text_miss = missing_map["val_text"]
        assert text_miss["null_count"] == 1
        assert text_miss["empty_count"] == 2
        assert text_miss["sentinel_count"] == 4

    def test_numeric_nan_inf_handling(self):
        series = pl.Series(
            "val",
            [
                1.0,
                2.0,
                None,
                float("nan"),
                float("inf"),
                float("-inf"),
                5.0,
                6.0,
                7.0,
                8.0,
            ],
        )
        stats = profile_numeric(series, total_rows=10)

        assert stats["nan_count"] == 1
        assert stats["infinite_count"] == 2
        assert stats["effective_missing_count"] == 2
        assert stats["min"] == 1.0
        mean_val = stats["mean"]
        assert isinstance(mean_val, (int, float))
        assert round(mean_val, 3) == 4.833


# =============================================================================
# 2. PYDANTIC CONFIG VALIDATION
# =============================================================================


class TestPydanticConfigValidation:
    """Validate AnalysisConfig type checking, bounds, and typo rejection."""

    def test_strict_config_validation(self):
        # Valid defaults
        cfg = AnalysisConfig()
        assert cfg.min_correlation == 0.5
        assert "N/A" in cfg.missing_sentinels

        # Invalid correlation method
        with pytest.raises(ValidationError):
            AnalysisConfig.model_validate({"correlation_method": "kendall"})

        # Invalid bounds
        with pytest.raises(ValidationError):
            AnalysisConfig.model_validate({"min_correlation": 1.5})

        # Typos rejected via extra='forbid'
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            AnalysisConfig.model_validate({"min_correlaton": 0.7})


# =============================================================================
# 3. PERFORMANCE & SCALE BENCHMARK
# =============================================================================


class TestPerformanceAndScale:
    """Validate full dataset execution speed on synthetic 10k rows."""

    def test_scale_profiling_performance(self, tmp_path: Path):
        pq_file = tmp_path / "scale_10k.parquet"
        data = {
            "id": list(range(1, 10001)),
            "val_a": [float(i) for i in range(1, 10001)],
            "val_b": [float(i * 2) for i in range(1, 10001)],
            "group": [f"G_{i % 10}" for i in range(1, 10001)],
        }
        pl.DataFrame(data).write_parquet(pq_file)

        report = analyze(pq_file)
        assert report.summary.row_count == 10000
        assert report.summary.column_count == 4
        assert report.metadata.elapsed_seconds < 2.0
