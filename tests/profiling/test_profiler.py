import polars as pl
import pytest

from datapulse.profiling.profiler import DatasetProfiler


@pytest.fixture
def sample_parquet(tmp_path):
    """Create a small Parquet dataset for testing."""

    data = pl.DataFrame(
        {
            "trip_distance": [2.5, 4.0, None],
            "fare_amount": [10.0, 15.0, 20.0],
            "passenger_count": [1, 2, 1],
        }
    )

    file_path = tmp_path / "sample.parquet"
    data.write_parquet(file_path)

    return file_path


def test_profiler_overview(sample_parquet):
    profiler = DatasetProfiler(sample_parquet)

    overview = profiler.get_overview()

    assert overview["file_name"] == "sample.parquet"
    assert overview["row_count"] == 3
    assert overview["column_count"] == 3


def test_profiler_missing_values(sample_parquet):
    profiler = DatasetProfiler(sample_parquet)

    missing = profiler.get_missing_values()

    trip_distance = missing.filter(pl.col("column") == "trip_distance")

    assert trip_distance["null_count"][0] == 1
    assert trip_distance["non_missing_count"][0] == 2
    assert trip_distance["missing_percentage"][0] == pytest.approx(33.33, abs=0.01)

    fare_amount = missing.filter(pl.col("column") == "fare_amount")

    assert fare_amount["null_count"][0] == 0
    assert fare_amount["missing_percentage"][0] == 0.0


def test_profiler_numeric_statistics(sample_parquet):
    profiler = DatasetProfiler(sample_parquet)

    statistics = profiler.get_numeric_statistics()

    assert statistics.width == 4
    assert "statistic" in statistics.columns
    assert "trip_distance" in statistics.columns
    assert "fare_amount" in statistics.columns


def test_profiler_categorical_statistics(tmp_path):
    data = pl.DataFrame(
        {
            "payment_type": ["Cash", "Card", "Cash", "Card"],
            "borough": ["Queens", "Manhattan", "Queens", "Queens"],
            "fare_amount": [10.0, 20.0, 15.0, 25.0],
        }
    )

    file_path = tmp_path / "categorical.parquet"
    data.write_parquet(file_path)

    profiler = DatasetProfiler(file_path)
    statistics = profiler.get_categorical_statistics()

    payment_type = statistics.filter(pl.col("column") == "payment_type")

    assert payment_type["unique_count"][0] == 2
    assert payment_type["cardinality_percentage"][0] == 50.0

    borough = statistics.filter(pl.col("column") == "borough")

    assert borough["unique_count"][0] == 2
    assert borough["cardinality_percentage"][0] == 50.0

    assert "fare_amount" not in statistics["column"].to_list()


def test_profiler_rejects_missing_file(tmp_path):
    missing_file = tmp_path / "missing.parquet"

    with pytest.raises(FileNotFoundError):
        DatasetProfiler(missing_file)


def test_profiler_rejects_unsupported_file(tmp_path):
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("fare_amount\n10.0\n", encoding="utf-8")

    with pytest.raises(ValueError):
        DatasetProfiler(txt_file)


def test_profiler_duplicate_summary(tmp_path):
    data = pl.DataFrame(
        {
            "name": ["A", "B", "A"],
            "value": [10, 20, 10],
        }
    )

    file_path = tmp_path / "duplicates.parquet"
    data.write_parquet(file_path)

    profiler = DatasetProfiler(file_path)
    summary = profiler.get_duplicate_summary()

    assert summary["total_rows"] == 3
    assert summary["unique_rows"] == 2
    assert summary["duplicate_rows"] == 1
    assert summary["duplicate_percentage"] == pytest.approx(33.33)


def test_profiler_temporal_statistics(tmp_path):
    from datetime import date

    data = pl.DataFrame(
        {
            "trip_date": pl.Series(
                "trip_date",
                [
                    date(2025, 1, 1),
                    date(2025, 1, 2),
                    date(2025, 1, 1),
                ],
                dtype=pl.Date,
            )
        }
    )

    file_path = tmp_path / "temporal.parquet"
    data.write_parquet(file_path)

    profiler = DatasetProfiler(file_path)
    statistics = profiler.get_temporal_statistics()

    assert statistics.height == 1
    assert statistics["column"][0] == "trip_date"
    assert statistics["minimum"][0] == "2025-01-01"
    assert statistics["maximum"][0] == "2025-01-02"
    assert statistics["unique_count"][0] == 2


def test_profiler_column_quality(sample_parquet):
    profiler = DatasetProfiler(sample_parquet)
    quality = profiler.get_column_quality()

    trip_distance = quality.filter(pl.col("column") == "trip_distance")

    assert trip_distance["category"][0] == "numeric"
    assert trip_distance["null_count"][0] == 1
    assert trip_distance["unique_count"][0] == 2
    assert trip_distance["missing_percentage"][0] == pytest.approx(33.33, abs=0.01)
