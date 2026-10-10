# =========================================================================
# Unit & Scenario Tests: Report Models & RFC 8259 Serialization
# =========================================================================

import json

from datapulse.models.report import (
    AnalysisReport,
    ColumnProfile,
    DatasetSummary,
    DuplicateSummary,
    MissingSummary,
    ReportMetadata,
)

# =========================================================================
# REPORT SERIALIZATION & RFC 8259 COMPLIANCE
# =========================================================================

class TestReportSerialization:
    """Validate report dictionary conversion, JSON serialization, and RFC 8259 compliance."""

    def test_standard_report_serialization(self):
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
        assert data["columns"][0]["statistics"]["mean"] == 4.5

        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert parsed["schema_version"] == "1.0.0"
        assert parsed["summary"]["file_name"] == "sample.parquet"

    def test_rfc8259_strict_sanitization_of_nans_and_infinities(self):
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
            total_rows=5, unique_rows=5, duplicate_rows=0, duplicate_percentage=0.0
        )
        columns = [
            ColumnProfile(
                name="metric",
                physical_type="Float64",
                inferred_role="numeric",
                statistics={
                    "mean": float("nan"),
                    "min": float("-inf"),
                    "max": float("inf"),
                    "nested": {"score": float("nan"), "val": 42.0},
                    "list_vals": [1.0, float("nan"), float("inf")],
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

        json_str = report.to_json()

        # In strict RFC 8259, NaNs and Infinities must be None/null, never bare NaN or Infinity tokens
        assert "NaN" not in json_str
        assert "Infinity" not in json_str

        parsed = json.loads(json_str)
        metric_stats = parsed["columns"][0]["statistics"]
        assert metric_stats["mean"] is None
        assert metric_stats["min"] is None
        assert metric_stats["max"] is None
        assert metric_stats["nested"]["score"] is None
        assert metric_stats["nested"]["val"] == 42.0
        assert metric_stats["list_vals"] == [1.0, None, None]
