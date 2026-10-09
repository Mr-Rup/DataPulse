from datetime import datetime

import polars as pl

from datapulse.analysis.column_classifier import (
    classify_column,
    classify_columns,
)


def test_classify_constant_column():
    series = pl.Series("status", ["active", "active", "active"])
    result = classify_column(series, 3)

    assert result.inferred_role == "constant"
    assert result.confidence == 1.0


def test_classify_boolean_column():
    series = pl.Series("is_member", [True, False, True])
    result = classify_column(series, 3)

    assert result.inferred_role == "boolean"
    assert result.confidence == 1.0


def test_classify_temporal_column():
    series = pl.Series(
        "created_at",
        [datetime(2025, 1, 1), datetime(2025, 1, 2)],
        dtype=pl.Datetime,
    )
    result = classify_column(series, 2)

    assert result.inferred_role == "temporal"
    assert result.confidence == 1.0


def test_classify_numeric_float():
    series = pl.Series("fare_amount", [10.5, 20.0, 15.25])
    result = classify_column(series, 3)

    assert result.inferred_role == "numeric"
    assert result.confidence > 0.9


def test_classify_coded_integer_category():
    # Like payment_type (1, 2, 1, 2, 3)
    series = pl.Series("payment_type", [1, 2, 1, 2, 3, 1, 2] * 20)
    result = classify_column(series, len(series))

    assert result.inferred_role == "categorical"
    assert "Low-cardinality" in result.reason or "code" in result.reason


def test_classify_integer_identifier():
    # Like PULocationID with moderate-to-high cardinality and ID hint
    series = pl.Series("PULocationID", list(range(1, 101)))
    result = classify_column(series, len(series))

    assert result.inferred_role == "identifier"


def test_classify_text_column():
    descriptions = [
        "Customer reported an unexpected delay during rush hour near central station.",
        "Driver was polite, vehicle clean, arrived slightly ahead of scheduled time.",
        "Traffic diversion due to road maintenance caused additional mileage.",
    ]
    series = pl.Series("notes", descriptions * 10)
    result = classify_column(series, len(series))

    assert result.inferred_role == "text"


def test_classify_string_category():
    series = pl.Series("borough", ["Manhattan", "Brooklyn", "Queens"] * 10)
    result = classify_column(series, len(series))

    assert result.inferred_role == "categorical"


def test_classify_all_null():
    series = pl.Series("empty_col", [None, None, None], dtype=pl.String)
    result = classify_column(series, 3)

    assert result.inferred_role == "other"


def test_classify_columns_dataframe():
    df = pl.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "fare": [10.0, 15.5, 20.0, 25.0],
            "payment_type": [1, 2, 1, 2],
            "flag": [True, False, True, False],
            "city": ["NY", "NY", "LA", "SF"],
        }
    )

    classifications = classify_columns(df)

    assert classifications["fare"].inferred_role == "numeric"
    assert classifications["payment_type"].inferred_role == "categorical"
    assert classifications["flag"].inferred_role == "boolean"
    assert classifications["city"].inferred_role == "categorical"
