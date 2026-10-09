from datetime import date, datetime

import polars as pl
import pytest

from datapulse import analyze
from datapulse.profiling.boolean import profile_boolean
from datapulse.profiling.categorical import profile_categorical
from datapulse.profiling.column_profiler import profile_column
from datapulse.profiling.identifier import profile_identifier
from datapulse.profiling.numeric import profile_numeric
from datapulse.profiling.temporal import profile_temporal
from datapulse.profiling.text import profile_text


def test_numeric_profiling():
    series = pl.Series("fares", [10.0, -5.0, 0.0, 20.0, 15.0])
    stats = profile_numeric(series, 5)

    assert stats["count"] == 5
    assert stats["zeros_count"] == 1
    assert stats["zeros_percentage"] == 20.0
    assert stats["negatives_count"] == 1
    assert stats["negatives_percentage"] == 20.0
    assert stats["min"] == -5.0
    assert stats["max"] == 20.0
    assert stats["median"] == 10.0
    assert stats["p25"] is not None
    assert stats["p75"] is not None
    assert stats["iqr"] is not None
    assert stats["skewness"] is not None


def test_numeric_profiling_all_null():
    series = pl.Series("empty", [None, None], dtype=pl.Float64)
    stats = profile_numeric(series, 2)

    assert stats["count"] == 0
    assert stats["mean"] is None
    assert stats["zeros_count"] == 0
    assert stats["negatives_count"] == 0


def test_categorical_profiling():
    series = pl.Series("city", ["NY", "LA", "NY", "SF", "NY", "LA"] * 10)
    stats = profile_categorical(series, len(series), max_categories=2)

    assert stats["count"] == 60
    assert stats["unique_count"] == 3
    top_cats = stats["top_categories"]
    assert isinstance(top_cats, list)
    assert len(top_cats) == 2
    first_cat = top_cats[0]
    assert isinstance(first_cat, dict)
    assert first_cat["value"] == "NY"
    assert first_cat["count"] == 30
    assert first_cat["percentage"] == 50.0


def test_categorical_profiling_all_null():
    series = pl.Series("empty", [None, None], dtype=pl.String)
    stats = profile_categorical(series, 2)

    assert stats["count"] == 0
    assert stats["unique_count"] == 0
    assert stats["mode"] is None
    assert stats["top_categories"] == []


def test_temporal_profiling():
    series = pl.Series(
        "dates",
        [datetime(2025, 1, 1), datetime(2025, 1, 11), datetime(2025, 1, 6)],
        dtype=pl.Datetime,
    )
    stats = profile_temporal(series, 3)

    assert stats["count"] == 3
    assert stats["minimum"] == "2025-01-01 00:00:00"
    assert stats["maximum"] == "2025-01-11 00:00:00"
    assert stats["span_days"] == 10.0
    assert stats["unique_count"] == 3


def test_temporal_profiling_all_null():
    series = pl.Series("dates", [None, None], dtype=pl.Date)
    stats = profile_temporal(series, 2)

    assert stats["count"] == 0
    assert stats["minimum"] is None
    assert stats["maximum"] is None
    assert stats["span_days"] is None


def test_boolean_profiling():
    series = pl.Series("flag", [True, False, True, True])
    stats = profile_boolean(series, 4)

    assert stats["count"] == 4
    assert stats["true_count"] == 3
    assert stats["true_percentage"] == 75.0
    assert stats["false_count"] == 1
    assert stats["false_percentage"] == 25.0


def test_boolean_profiling_binary_ints():
    series = pl.Series("flag_int", [1, 0, 1, 0, 1])
    stats = profile_boolean(series, 5)

    assert stats["count"] == 5
    assert stats["true_count"] == 3
    assert stats["true_percentage"] == 60.0
    assert stats["false_count"] == 2
    assert stats["false_percentage"] == 40.0


def test_text_profiling():
    series = pl.Series(
        "comments",
        [
            "This is a longer customer note.",
            "Another detailed observation provided by staff.",
            "",
        ],
    )
    stats = profile_text(series, 3)

    assert stats["count"] == 3
    assert stats["min_length"] == 0
    assert stats["max_length"] == 47
    assert stats["empty_count"] == 1
    assert stats["empty_percentage"] == pytest.approx(33.33, abs=0.01)


def test_identifier_profiling():
    series = pl.Series("user_id", [101, 102, 103, 101, 104])
    stats = profile_identifier(series, 5)

    assert stats["count"] == 5
    assert stats["unique_count"] == 4
    assert stats["duplicate_count"] == 1
    assert stats["uniqueness_percentage"] == 80.0


def test_column_profiler_dispatch():
    s_num = pl.Series("num", [1.0, 2.0])
    s_cat = pl.Series("cat", ["A", "B"])
    s_const = pl.Series("const", [99, 99])

    assert "mean" in profile_column(s_num, 2, "numeric")
    assert "top_categories" in profile_column(s_cat, 2, "categorical")
    assert profile_column(s_const, 2, "constant")["constant_value"] == "99"


def test_analyze_integration_rich_stats(tmp_path):
    df = pl.DataFrame(
        {
            "user_id": [1, 2, 3, 4],
            "fare": [10.5, -2.0, 0.0, 25.0],
            "city": ["NY", "LA", "NY", "SF"],
            "is_active": [True, False, True, True],
            "created_at": [
                date(2025, 1, 1),
                date(2025, 1, 5),
                date(2025, 1, 10),
                date(2025, 1, 15),
            ],
        }
    )
    file_path = tmp_path / "rich.parquet"
    df.write_parquet(file_path)

    report = analyze(file_path)

    fare_col = next(c for c in report.columns if c.name == "fare")
    assert fare_col.inferred_role == "numeric"
    assert fare_col.statistics["negatives_count"] == 1
    assert fare_col.statistics["zeros_count"] == 1

    city_col = next(c for c in report.columns if c.name == "city")
    assert city_col.inferred_role == "categorical"
    assert city_col.statistics["mode"] == "NY"

    flag_col = next(c for c in report.columns if c.name == "is_active")
    assert flag_col.inferred_role == "boolean"
    assert flag_col.statistics["true_count"] == 3

    time_col = next(c for c in report.columns if c.name == "created_at")
    assert time_col.inferred_role == "temporal"
    assert time_col.statistics["span_days"] == 14.0
