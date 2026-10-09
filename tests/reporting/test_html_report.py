import json
from datetime import datetime

import polars as pl

from datapulse import analyze, export_html, export_json
from datapulse.reporting.html import generate_html_report


def test_generate_html_report(tmp_path):
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "fare": [10.0, 20.0, 30.0],
            "city": ["NY", "LA", "NY"],
            "created_at": [
                datetime(2025, 1, 1),
                datetime(2025, 1, 2),
                datetime(2025, 1, 3),
            ],
        }
    )
    file_path = tmp_path / "sample.parquet"
    df.write_parquet(file_path)

    report = analyze(file_path)
    html = generate_html_report(report)

    assert "<!DOCTYPE html>" in html
    assert "DataPulse Report" in html
    assert "sample.parquet" in html
    assert "Total Rows" in html
    assert "3" in html
    assert "Column Profiles" in html
    assert "fare" in html
    assert "city" in html


def test_export_html_and_json(tmp_path):
    df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    data_file = tmp_path / "test.parquet"
    df.write_parquet(data_file)

    report = analyze(data_file)

    # Test export_html
    html_out = tmp_path / "report.html"
    returned_html = export_html(report, html_out)
    assert returned_html.exists()
    assert returned_html.stat().st_size > 0
    assert "<!DOCTYPE html>" in returned_html.read_text(encoding="utf-8")

    # Test export_json
    json_out = tmp_path / "report.json"
    returned_json = export_json(report, json_out)
    assert returned_json.exists()
    parsed = json.loads(returned_json.read_text(encoding="utf-8"))
    assert parsed["summary"]["file_name"] == "test.parquet"

    # Test report methods
    method_html = tmp_path / "method_report.html"
    report.save_html(method_html)
    assert method_html.exists()

    method_json = tmp_path / "method_report.json"
    report.save_json(method_json)
    assert method_json.exists()
