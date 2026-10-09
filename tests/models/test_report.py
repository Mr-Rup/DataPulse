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
