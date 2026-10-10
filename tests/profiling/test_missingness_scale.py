import time
from pathlib import Path

import polars as pl
import pytest
from pydantic import ValidationError

from datapulse import AnalysisConfig, analyze
from datapulse.profiling.numeric import profile_numeric
from datapulse.profiling.profiler import DatasetProfiler


@pytest.fixture
def missingness_dataset(tmp_path: Path) -> Path:
    csv_file = tmp_path / "missingness.csv"
    data = {
        "id": list(range(1, 11)),
        "val_float": [
            1.0, 2.0, None, float("nan"),
            float("inf"), float("-inf"), 5.0, 6.0, 7.0, 8.0,
        ],
        "val_text": [
            "apple", None, "", "   ", "N/A",
            "banana", "missing", "?", "null", "cherry",
        ],
        "category": ["A", "B", "None", "unknown", "C", "A", "", "B", "N/A", "A"],
    }
    df = pl.DataFrame(data)
    df.write_csv(csv_file)
    return csv_file


@pytest.fixture
def synthetic_parquet(tmp_path: Path) -> Path:
    pq_file = tmp_path / "synthetic_10k.parquet"
    data = {
        "id": list(range(1, 10001)),
        "val_a": [float(i) for i in range(1, 10001)],
        "val_b": [float(i * 2) for i in range(1, 10001)],
        "group": [f"G_{i % 10}" for i in range(1, 10001)],
    }
    df = pl.DataFrame(data)
    df.write_parquet(pq_file)
    return pq_file


def test_missingness_breakdown_detection(missingness_dataset: Path):
    sentinels = ["N/A", "missing", "?", "null", "None", "unknown"]
    prof = DatasetProfiler(missingness_dataset)
    missing_df = prof.get_missing_values(sentinels=sentinels)
    missing_map = {row["column"]: row for row in missing_df.iter_rows(named=True)}

    # val_float: 1 null, 1 nan, 0 empty, 0 sentinel -> total_missing = 2
    float_miss = missing_map["val_float"]
    assert float_miss["null_count"] == 1
    assert float_miss["nan_count"] == 1
    assert float_miss["empty_count"] == 0
    assert float_miss["sentinel_count"] == 0
    assert float_miss["total_missing_count"] == 2
    assert float_miss["missing_percentage"] == 20.0

    # val_text: 1 null, 2 empty, 4 sentinels -> total = 7
    text_miss = missing_map["val_text"]
    assert text_miss["null_count"] == 1
    assert text_miss["nan_count"] == 0
    assert text_miss["empty_count"] == 2
    assert text_miss["sentinel_count"] == 4
    assert text_miss["total_missing_count"] == 7
    assert text_miss["missing_percentage"] == 70.0


def test_numeric_nan_inf_handling():
    series = pl.Series(
        "val",
        [1.0, 2.0, None, float("nan"), float("inf"), float("-inf"), 5.0, 6.0, 7.0, 8.0],
    )
    stats = profile_numeric(series, total_rows=10)

    assert stats["nan_count"] == 1
    assert stats["infinite_count"] == 2
    assert stats["effective_missing_count"] == 2  # 1 null + 1 nan

    # Clean subset: 1.0, 2.0, 5.0, 6.0, 7.0, 8.0 -> sum = 29.0, n = 6, mean ≈ 4.8333
    assert stats["min"] == 1.0
    assert stats["max"] == 8.0
    assert isinstance(stats["mean"], (int, float))
    assert round(stats["mean"], 3) == 4.833


def test_pydantic_config_validation():
    # Valid default config
    cfg = AnalysisConfig()
    assert cfg.min_correlation == 0.5
    assert "N/A" in cfg.missing_sentinels

    # Invalid correlation method
    with pytest.raises(ValidationError):
        AnalysisConfig.model_validate({"correlation_method": "kendall"})

    # Invalid correlation bounds
    with pytest.raises(ValidationError):
        AnalysisConfig(min_correlation=1.5)

    with pytest.raises(ValidationError):
        AnalysisConfig(min_correlation=-0.5)

    # Extra/typo fields forbidden
    with pytest.raises(ValidationError):
        AnalysisConfig.model_validate({"sample_size": 100})

    with pytest.raises(ValidationError):
        AnalysisConfig.model_validate({"max_catgories": 10})


def test_full_dataset_scale_performance(synthetic_parquet: Path):
    start = time.perf_counter()
    report = analyze(synthetic_parquet)
    elapsed = time.perf_counter() - start

    assert report.summary.row_count == 10000
    assert len(report.columns) == 4
    assert elapsed < 1.0  # Must complete well within 1 second on 10k rows
