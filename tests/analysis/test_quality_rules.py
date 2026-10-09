from datetime import datetime

import polars as pl

from datapulse import analyze
from datapulse.analysis.quality_rules import (
    check_chronology_inversion,
    check_constant_columns,
    check_duplicates,
    check_high_cardinality,
    check_missingness,
    check_negative_values,
    check_numeric_outliers,
)
from datapulse.models.report import ColumnProfile, DuplicateSummary


def test_check_missingness():
    cols = [
        ColumnProfile(
            name="col_severe",
            physical_type="Float64",
            null_count=60,
            missing_percentage=60.0,
        ),
        ColumnProfile(
            name="col_moderate",
            physical_type="Float64",
            null_count=30,
            missing_percentage=30.0,
        ),
        ColumnProfile(
            name="col_good",
            physical_type="Float64",
            null_count=5,
            missing_percentage=5.0,
        ),
    ]

    findings = check_missingness(cols)
    assert len(findings) == 2
    assert findings[0].severity == "critical"
    assert findings[0].affected_columns == ["col_severe"]
    assert findings[1].severity == "warning"
    assert findings[1].affected_columns == ["col_moderate"]


def test_check_duplicates():
    dup_severe = DuplicateSummary(
        total_rows=100,
        unique_rows=80,
        duplicate_rows=20,
        duplicate_percentage=20.0,
    )
    findings = check_duplicates(dup_severe)
    assert len(findings) == 1
    assert findings[0].severity == "critical"
    assert findings[0].rule_id == "duplicate_rows"

    dup_clean = DuplicateSummary(
        total_rows=100,
        unique_rows=100,
        duplicate_rows=0,
        duplicate_percentage=0.0,
    )
    assert len(check_duplicates(dup_clean)) == 0


def test_check_constant_columns():
    cols = [
        ColumnProfile(
            name="const_col",
            physical_type="String",
            inferred_role="constant",
            unique_count=1,
            null_count=0,
        ),
        ColumnProfile(
            name="varying_col",
            physical_type="String",
            inferred_role="categorical",
            unique_count=5,
            null_count=0,
        ),
    ]

    findings = check_constant_columns(cols)
    assert len(findings) == 1
    assert findings[0].affected_columns == ["const_col"]
    assert findings[0].title == "Constant column"


def test_check_high_cardinality():
    cols = [
        ColumnProfile(
            name="messy_category",
            physical_type="String",
            inferred_role="categorical",
            unique_count=100,
            statistics={"cardinality_percentage": 75.0},
        )
    ]

    findings = check_high_cardinality(cols)
    assert len(findings) == 1
    assert findings[0].affected_columns == ["messy_category"]


def test_check_negative_values():
    cols = [
        ColumnProfile(
            name="fare_amount",
            physical_type="Float64",
            inferred_role="numeric",
            statistics={"negatives_count": 15, "negatives_percentage": 1.5},
        ),
        ColumnProfile(
            name="temperature",
            physical_type="Float64",
            inferred_role="numeric",
            statistics={"negatives_count": 10, "negatives_percentage": 10.0},
        ),
    ]

    findings = check_negative_values(cols)
    assert len(findings) == 1
    assert findings[0].affected_columns == ["fare_amount"]


def test_check_numeric_outliers():
    # 20 regular items, 1 extreme outlier
    data = [10.0] * 10 + [12.0] * 10 + [500.0]
    df = pl.DataFrame({"metric": data})

    cols = [
        ColumnProfile(
            name="metric",
            physical_type="Float64",
            inferred_role="numeric",
            statistics={"p25": 10.0, "p75": 12.0, "iqr": 2.0},
        )
    ]

    findings = check_numeric_outliers(cols, df)
    assert len(findings) == 1
    assert findings[0].affected_columns == ["metric"]
    assert "Numeric outliers detected" in findings[0].title


def test_check_chronology_inversion():
    df = pl.DataFrame(
        {
            "pickup_datetime": [
                datetime(2025, 1, 1, 10, 0),
                datetime(2025, 1, 1, 12, 0),
            ],
            "dropoff_datetime": [
                datetime(2025, 1, 1, 10, 30),
                datetime(2025, 1, 1, 11, 0),  # Dropoff before pickup!
            ],
        }
    )

    findings = check_chronology_inversion(df)
    assert len(findings) == 1
    assert findings[0].severity == "critical"
    assert findings[0].title == "Chronological inversion"
    assert "dropoff_datetime" in findings[0].affected_columns


def test_evaluate_quality_rules_end_to_end(tmp_path):
    df = pl.DataFrame(
        {
            "fare_amount": [10.0, -5.0, 15.0, 20.0],
            "pickup_datetime": [
                datetime(2025, 1, 1, 10, 0),
                datetime(2025, 1, 1, 12, 0),
                datetime(2025, 1, 1, 14, 0),
                datetime(2025, 1, 1, 16, 0),
            ],
            "dropoff_datetime": [
                datetime(2025, 1, 1, 10, 30),
                datetime(2025, 1, 1, 11, 30),  # inversion
                datetime(2025, 1, 1, 14, 30),
                datetime(2025, 1, 1, 16, 30),
            ],
            "all_same": ["X", "X", "X", "X"],
        }
    )

    file_path = tmp_path / "anomalous.parquet"
    df.write_parquet(file_path)

    report = analyze(file_path)

    assert len(report.findings) >= 2
    titles = [f.title for f in report.findings]
    assert "Unexpected negative values" in titles
    assert "Chronological inversion" in titles
    assert "Constant column" in titles

    assert len(report.warnings) >= 2
