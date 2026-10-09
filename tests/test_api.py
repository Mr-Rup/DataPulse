import polars as pl
import pytest

from datapulse import __version__, analyze
from datapulse.models.report import AnalysisReport


@pytest.fixture
def sample_parquet(tmp_path):
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


def test_analyze_produces_valid_report(sample_parquet):
    report = analyze(sample_parquet)

    assert isinstance(report, AnalysisReport)
    assert report.schema_version == "1.0.0"
    assert report.metadata.datapulse_version == __version__
    assert report.metadata.source_name == "sample.parquet"
    assert report.metadata.elapsed_seconds >= 0.0

    assert report.summary.row_count == 3
    assert report.summary.column_count == 3
    assert "trip_distance" in report.summary.schema

    assert report.duplicates.total_rows == 3
    assert report.duplicates.unique_rows == 3
    assert report.duplicates.duplicate_rows == 0

    assert len(report.missing_values) == 3
    trip_distance_missing = [
        m for m in report.missing_values if m.column == "trip_distance"
    ][0]
    assert trip_distance_missing.null_count == 1
    assert trip_distance_missing.missing_percentage == pytest.approx(33.33, abs=0.01)

    assert len(report.columns) == 3
    names = [c.name for c in report.columns]
    assert "trip_distance" in names
    assert "fare_amount" in names

    assert isinstance(report.to_dict(), dict)
    assert isinstance(report.to_json(), str)


def test_analyze_rejects_missing_file(tmp_path):
    missing_file = tmp_path / "missing.parquet"

    with pytest.raises(FileNotFoundError):
        analyze(missing_file)


def test_analyze_rejects_unsupported_file(tmp_path):
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("a,b\n1,2\n", encoding="utf-8")

    with pytest.raises(ValueError):
        analyze(txt_file)


def test_analyze_csv(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("col_a,col_b\n10,foo\n20,bar\n", encoding="utf-8")

    report = analyze(csv_file)
    assert report.summary.file_name == "test.csv"
    assert report.summary.row_count == 2
    assert report.summary.column_count == 2
    assert "col_a" in report.summary.schema


def test_analyze_json(tmp_path):
    json_file = tmp_path / "test.json"
    content = '[{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]'
    json_file.write_text(content, encoding="utf-8")

    report = analyze(json_file)
    assert report.summary.file_name == "test.json"
    assert report.summary.row_count == 2
    assert report.summary.column_count == 2


def test_analyze_excel(tmp_path):
    excel_file = tmp_path / "test.xlsx"
    df = pl.DataFrame({"metric": [1, 2], "score": [90.5, 85.0]})
    df.write_excel(excel_file)

    report = analyze(excel_file)
    assert report.summary.file_name == "test.xlsx"
    assert report.summary.row_count == 2
    assert report.summary.column_count == 2
