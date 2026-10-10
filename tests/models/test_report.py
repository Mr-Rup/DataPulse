import json

from datapulse.models.report import (
    AnalysisReport,
    ColumnProfile,
    DatasetSummary,
    DuplicateSummary,
    MissingSummary,
    ReportMetadata,
)


def test_analysis_report_serialization():
    metadata = ReportMetadata(
        datapulse_version="0.1.0",
        created_at="2026-10-10T00:00:00Z",
        source_name="sample.parquet",
        source_path="/path/to/sample.parquet",
        file_size_mb=1.23,
        elapsed_seconds=0.0456,
    )
    summary = DatasetSummary(
        file_name="sample.parquet",
        file_size_mb=1.23,
        row_count=10,
        column_count=2,
        schema={"col_a": "Int64", "col_b": "String"},
    )
    duplicates = DuplicateSummary(
        total_rows=10,
        unique_rows=9,
        duplicate_rows=1,
        duplicate_percentage=10.0,
    )
    missing = [
        MissingSummary(
            column="col_a",
            null_count=1,
            non_missing_count=9,
            missing_percentage=10.0,
        )
    ]
    columns = [
        ColumnProfile(
            name="col_a",
            physical_type="Int64",
            inferred_role="numeric",
            null_count=1,
            missing_percentage=10.0,
            unique_count=9,
            statistics={"mean": 4.5},
        )
    ]

    report = AnalysisReport(
        schema_version="1.0.0",
        metadata=metadata,
        summary=summary,
        duplicates=duplicates,
        missing_values=missing,
        columns=columns,
    )

    data = report.to_dict()
    assert data["schema_version"] == "1.0.0"
    assert data["metadata"]["source_name"] == "sample.parquet"
    assert data["summary"]["row_count"] == 10
    assert data["duplicates"]["duplicate_rows"] == 1
    assert len(data["missing_values"]) == 1
    assert data["missing_values"][0]["column"] == "col_a"
    assert len(data["columns"]) == 1
    assert data["columns"][0]["statistics"]["mean"] == 4.5
    assert data["findings"] == []
    assert data["warnings"] == []

    json_str = report.to_json()
    parsed = json.loads(json_str)
    assert parsed["schema_version"] == "1.0.0"
    assert parsed["summary"]["file_name"] == "sample.parquet"


def test_analysis_report_rfc8259_compliance():
    metadata = ReportMetadata(
        datapulse_version="0.1.0",
        created_at="2026-10-10T00:00:00Z",
        source_name="nan_test.csv",
        source_path="nan_test.csv",
        file_size_mb=0.01,
        elapsed_seconds=0.01,
    )
    summary = DatasetSummary(
        file_name="nan_test.csv",
        file_size_mb=0.01,
        row_count=5,
        column_count=1,
        schema={"metric": "Float64"},
    )
    duplicates = DuplicateSummary(
        total_rows=5,
        unique_rows=5,
        duplicate_rows=0,
        duplicate_percentage=0.0,
    )
    columns = [
        ColumnProfile(
            name="metric",
            physical_type="Float64",
            inferred_role="numeric",
            null_count=1,
            missing_percentage=20.0,
            unique_count=4,
            statistics={
                "mean": float("nan"),
                "max": float("inf"),
                "min": float("-inf"),
                "regular": 42.0,
            },
        )
    ]
    report = AnalysisReport(
        schema_version="1.0.0",
        metadata=metadata,
        summary=summary,
        duplicates=duplicates,
        columns=columns,
    )

    # Must produce strictly valid JSON without raw unquoted NaN or Infinity
    json_str = report.to_json()
    assert "NaN" not in json_str
    assert "Infinity" not in json_str

    parsed = json.loads(json_str)
    stats = parsed["columns"][0]["statistics"]
    assert stats["mean"] is None
    assert stats["max"] is None
    assert stats["min"] is None
    assert stats["regular"] == 42.0
