import polars as pl
import pytest

from datapulse import analyze
from datapulse.analysis.relationships import (
    compute_correlations,
    evaluate_collinear_findings,
    find_key_candidates,
)
from datapulse.models.report import ColumnProfile, CorrelationPair


def test_compute_correlations_perfect():
    df = pl.DataFrame(
        {
            "x": [1.0, 2.0, 3.0, 4.0, 5.0],
            "y": [2.0, 4.0, 6.0, 8.0, 10.0],
            "z": [5.0, 4.0, 3.0, 2.0, 1.0],
        }
    )

    pairs = compute_correlations(df, ["x", "y", "z"])
    assert len(pairs) == 3

    xy = next(p for p in pairs if {p.column_a, p.column_b} == {"x", "y"})
    assert xy.coefficient == pytest.approx(1.0, abs=0.001)

    xz = next(p for p in pairs if {p.column_a, p.column_b} == {"x", "z"})
    assert xz.coefficient == pytest.approx(-1.0, abs=0.001)


def test_compute_correlations_handles_constant():
    df = pl.DataFrame(
        {
            "a": [1.0, 2.0, 3.0, 4.0],
            "const": [5.0, 5.0, 5.0, 5.0],
        }
    )

    pairs = compute_correlations(df, ["a", "const"])
    assert len(pairs) == 0


def test_compute_correlations_small_dataset():
    df = pl.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
    assert compute_correlations(df, ["a", "b"]) == []


def test_find_key_candidates():
    cols = [
        ColumnProfile(
            name="id",
            physical_type="Int64",
            null_count=0,
            unique_count=10,
        ),
        ColumnProfile(
            name="code_with_null",
            physical_type="String",
            null_count=1,
            unique_count=9,
        ),
        ColumnProfile(
            name="category",
            physical_type="String",
            null_count=0,
            unique_count=3,
        ),
    ]

    keys = find_key_candidates(cols, 10)
    assert len(keys) == 1
    assert keys[0].column == "id"
    assert keys[0].is_primary_key_candidate is True


def test_evaluate_collinear_findings():
    pairs = [
        CorrelationPair(column_a="fare", column_b="total", coefficient=0.98),
        CorrelationPair(column_a="speed", column_b="distance", coefficient=0.45),
    ]

    findings = evaluate_collinear_findings(pairs, threshold=0.90)
    assert len(findings) == 1
    assert findings[0].rule_id == "collinear_pair"
    assert findings[0].affected_columns == ["fare", "total"]


def test_analyze_integration_relationships(tmp_path):
    df = pl.DataFrame(
        {
            "row_id": [1, 2, 3, 4, 5],
            "units": [10.0, 20.0, 30.0, 40.0, 50.0],
            "revenue": [100.0, 200.0, 300.0, 400.0, 500.0],
        }
    )

    file_path = tmp_path / "relationships.parquet"
    df.write_parquet(file_path)

    report = analyze(file_path)

    assert len(report.key_candidates) >= 1
    pk_names = [k.column for k in report.key_candidates if k.is_primary_key_candidate]
    assert "row_id" in pk_names

    assert len(report.correlations) == 1
    pair = report.correlations[0]
    assert {pair.column_a, pair.column_b} == {"units", "revenue"}
    assert pair.coefficient == pytest.approx(1.0, abs=0.001)

    # Check collinearity warning
    assert any(f.rule_id == "collinear_pair" for f in report.findings)
