# =========================================================================
# Unit & Scenario Tests: Public API Pipeline (analyze)
# =========================================================================

from pathlib import Path

import polars as pl
import pytest

from datapulse import __version__, analyze
from datapulse.config import AnalysisConfig
from datapulse.models.report import AnalysisReport

# =========================================================================
# PUBLIC API END-TO-END PIPELINE
# =========================================================================

class TestPublicApiPipeline:
    """Validate end-to-end analyze() execution across file formats and in-memory frames."""

    def test_analyze_realistic_dataset(self, realistic_parquet_path: Path):
        report = analyze(realistic_parquet_path)

        assert isinstance(report, AnalysisReport)
        assert report.schema_version == "1.0.0"
        assert report.metadata.datapulse_version == __version__
        assert report.metadata.source_name == "realistic_data.parquet"
        assert report.metadata.elapsed_seconds >= 0.0

        assert report.summary.row_count == 50
        assert report.summary.column_count == 12
        assert "amount" in report.summary.schema

        assert report.duplicates.total_rows == 50
        assert report.duplicates.duplicate_rows == 2

        assert len(report.missing_values) == 12
        assert len(report.columns) == 12

        assert isinstance(report.to_dict(), dict)
        assert isinstance(report.to_json(), str)

    def test_analyze_multi_format_ingestion(
        self, realistic_csv_path: Path, realistic_json_path: Path, tmp_path: Path
    ):
        # CSV
        rep_csv = analyze(realistic_csv_path)
        assert rep_csv.summary.row_count == 50

        # JSON
        rep_json = analyze(realistic_json_path)
        assert rep_json.summary.row_count == 50

        # Excel
        excel_file = tmp_path / "test.xlsx"
        pl.DataFrame({"metric": [1, 2], "score": [90.5, 85.0]}).write_excel(excel_file)
        rep_excel = analyze(excel_file)
        assert rep_excel.summary.row_count == 2

    def test_analyze_metadata_path_privacy(self, realistic_csv_path: Path):
        # Default: full path privacy enabled (filename only)
        rep_private = analyze(
            realistic_csv_path, config=AnalysisConfig(include_full_path=False)
        )
        assert rep_private.metadata.source_path == realistic_csv_path.name

        # Explicit: full path included
        rep_full = analyze(
            realistic_csv_path, config=AnalysisConfig(include_full_path=True)
        )
        assert rep_full.metadata.source_path == str(realistic_csv_path)


# =========================================================================
# PUBLIC API INPUT VALIDATION
# =========================================================================

class TestPublicApiValidation:
    """Validate API exception raising for missing or unsupported inputs."""

    def test_rejects_missing_or_unsupported(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            analyze(tmp_path / "nonexistent.parquet")

        txt_file = tmp_path / "sample.unsupported"
        txt_file.write_text("a,b\n1,2\n", encoding="utf-8")
        with pytest.raises(ValueError):
            analyze(txt_file)
