import time
from pathlib import Path

import polars as pl
import pytest

from datapulse import AnalysisConfig, analyze
from datapulse.profiling.profiler import DatasetProfiler


@pytest.fixture
def synthetic_csv(tmp_path: Path) -> Path:
    csv_file = tmp_path / "synthetic_100.csv"
    data = {
        "id": list(range(1, 101)),
        "score": [i * 1.5 for i in range(1, 101)],
        "category": [f"Cat_{i % 5}" for i in range(1, 101)],
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


def test_sampling_head(synthetic_csv: Path):
    prof = DatasetProfiler(synthetic_csv, sample_size=15, sample_method="head")
    assert prof.data.height == 15
    assert prof.data["id"].to_list() == list(range(1, 16))


def test_sampling_random(synthetic_csv: Path):
    prof1 = DatasetProfiler(synthetic_csv, sample_size=15, sample_method="random")
    prof2 = DatasetProfiler(synthetic_csv, sample_size=15, sample_method="random")
    assert prof1.data.height == 15
    assert prof2.data.height == 15
    # Deterministic seed test
    assert prof1.data["id"].to_list() == prof2.data["id"].to_list()


def test_sampling_exceeds_total_rows(synthetic_csv: Path):
    prof = DatasetProfiler(synthetic_csv, sample_size=500, sample_method="head")
    assert prof.data.height == 100

    prof_rand = DatasetProfiler(
        synthetic_csv, sample_size=500, sample_method="random"
    )
    assert prof_rand.data.height == 100


def test_sampling_metadata(synthetic_csv: Path):
    cfg = AnalysisConfig(sample_size=25)
    report = analyze(synthetic_csv, config=cfg)
    assert report.metadata.sample_size == 25
    assert report.summary.row_count == 25


def test_invalid_config_parameters():
    with pytest.raises(ValueError, match="sample_size must be greater than 0"):
        AnalysisConfig(sample_size=0)

    with pytest.raises(ValueError, match="sample_size must be greater than 0"):
        AnalysisConfig(sample_size=-10)

    with pytest.raises(ValueError, match="sample_method must be either"):
        AnalysisConfig(sample_method="shuffle")

    with pytest.raises(ValueError, match="correlation_method must be"):
        AnalysisConfig(correlation_method="kendall")

    with pytest.raises(ValueError, match="min_correlation must be between"):
        AnalysisConfig(min_correlation=1.5)


def test_sampling_scale_performance(synthetic_parquet: Path):
    # Benchmark sampled analysis on parquet
    start = time.perf_counter()
    report = analyze(synthetic_parquet, config=AnalysisConfig(sample_size=1000))
    elapsed = time.perf_counter() - start

    assert report.summary.row_count == 1000
    assert elapsed < 0.50  # Must be fast (< 500ms)


def test_full_dataset_scale_performance(synthetic_parquet: Path):
    # 10k rows full profile with correlation
    start = time.perf_counter()
    report = analyze(synthetic_parquet)
    elapsed = time.perf_counter() - start

    assert report.summary.row_count == 10000
    assert len(report.columns) == 4
    assert elapsed < 1.0  # Must complete well within 1 second
