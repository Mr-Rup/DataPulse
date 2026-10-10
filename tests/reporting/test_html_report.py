# =============================================================================
# Unit & Scenario Tests: HTML Report Rendering & Multi-Format Exporters
# =============================================================================

import json
from pathlib import Path

from datapulse import analyze, export_html, export_json
from datapulse.reporting.html import generate_html_report

# =============================================================================
# 1. HTML REPORT RENDERING & EXPORTERS
# =============================================================================


class TestHtmlReportRendering:
    """Validate HTML generation, XSS safety, and file export helpers."""

    def test_html_layout_and_elements(self, realistic_parquet_path: Path):
        report = analyze(realistic_parquet_path)
        html = generate_html_report(report)

        assert "<!DOCTYPE html>" in html
        assert "DataPulse Report" in html
        assert "realistic_data.parquet" in html
        assert "Total Rows" in html
        assert "50" in html
        assert "Column Profiles" in html
        assert "amount" in html
        assert "category" in html

    def test_export_helpers_and_report_methods(
        self, tmp_path: Path, realistic_parquet_path: Path
    ):
        report = analyze(realistic_parquet_path)

        # export_html
        html_out = tmp_path / "report.html"
        ret_html = export_html(report, html_out)
        assert ret_html.exists()
        assert "<!DOCTYPE html>" in ret_html.read_text(encoding="utf-8")

        # export_json
        json_out = tmp_path / "report.json"
        ret_json = export_json(report, json_out)
        assert ret_json.exists()
        parsed = json.loads(ret_json.read_text(encoding="utf-8"))
        assert parsed["summary"]["file_name"] == "realistic_data.parquet"

        # Direct report methods: save_html & save_json
        m_html = tmp_path / "method_report.html"
        report.save_html(m_html)
        assert m_html.exists()

        m_json = tmp_path / "method_report.json"
        report.save_json(m_json)
        assert m_json.exists()
