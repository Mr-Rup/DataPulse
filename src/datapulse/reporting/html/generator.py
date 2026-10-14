# =========================================================================
# DataPulse HTML Report Generator & Exporter
# Assembles standalone HTML dashboards and writes reports to disk.
# =========================================================================

from html import escape
from pathlib import Path

from datapulse.models.report import AnalysisReport
from datapulse.reporting.html.components import (
    render_column_rows,
    render_correlations,
    render_findings,
    render_key_candidates,
)
from datapulse.reporting.html.scripts import HTML_SCRIPT
from datapulse.reporting.html.styles import HTML_CSS

# =========================================================================
# REPORT HTML DOCUMENT ASSEMBLY
# =========================================================================

def generate_html_report(report: AnalysisReport) -> str:
    """Generate a self-contained, interactive HTML document from an AnalysisReport."""
    summary = report.summary
    meta = report.metadata
    dup = report.duplicates

    total_nulls = sum(col.null_count for col in report.columns)
    total_cells = summary.row_count * summary.column_count
    overall_null_pct = (
        round((total_nulls / total_cells) * 100, 2) if total_cells > 0 else 0.0
    )

    findings_html = render_findings(report.findings)
    columns_table_html = render_column_rows(report.columns)
    correlations_html = render_correlations(report.correlations)
    key_candidates_html = render_key_candidates(report.key_candidates)

    time_str = escape(meta.created_at[:19])
    dup_str = f"{dup.duplicate_rows:,} ({dup.duplicate_percentage:.1f}%)"
    version_str = escape(meta.datapulse_version)
    source_str = escape(meta.source_path)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataPulse Report &bull; {escape(summary.file_name)}</title>
    <style>{HTML_CSS}</style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-group">
                <span class="logo-badge">DATAPULSE</span>
                <span class="file-title">{escape(summary.file_name)}</span>
            </div>
            <div class="meta-badges">
                <span class="badge badge-neutral">v{version_str}</span>
                <span class="badge badge-neutral">{meta.elapsed_seconds:.3f}s</span>
                <span class="badge badge-neutral">{time_str}</span>
            </div>
        </header>

        <section class="metrics-grid">
            <div class="metric-card">
                <span class="metric-label">Total Rows</span>
                <span class="metric-value">{summary.row_count:,}</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">Total Columns</span>
                <span class="metric-value">{summary.column_count}</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">File Size</span>
                <span class="metric-value">{summary.file_size_mb:.2f} MB</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">Duplicate Rows</span>
                <span class="metric-value">{dup_str}</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">Overall Missing</span>
                <span class="metric-value">{overall_null_pct:.1f}%</span>
            </div>
            <div class="metric-card">
                <span class="metric-label">Findings & Alerts</span>
                <span class="metric-value">{len(report.findings)}</span>
            </div>
        </section>

        <section class="section-card">
            <div class="section-title">
                Data Quality Findings & Anomalies
                <span class="badge badge-neutral">{len(report.findings)} items</span>
            </div>
            {findings_html}
        </section>

        <section class="section-card">
            <div class="section-title">
                Column Profiles ({summary.column_count})
                <input type="text" id="column-search" class="search-box"
                       placeholder="Filter columns by name or role...">
            </div>
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Column</th>
                            <th>Physical Type</th>
                            <th>Inferred Role</th>
                            <th>Missing Values</th>
                            <th class="text-right">Distinct</th>
                            <th>Statistics & Distribution</th>
                        </tr>
                    </thead>
                    <tbody id="columns-body">
                        {columns_table_html}
                    </tbody>
                </table>
            </div>
        </section>

        {correlations_html}

        {key_candidates_html}

        <footer>
            Generated by DataPulse Automated EDA Engine &bull; {source_str}
        </footer>
    </div>

    <script>{HTML_SCRIPT}</script>
</body>
</html>"""

    return html


# =========================================================================
# REPORT FILE EXPORTER
# =========================================================================

def export_html(report: AnalysisReport, output_path: str | Path) -> Path:
    """Generate and write a self-contained HTML report to disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    html_content = generate_html_report(report)
    path.write_text(html_content, encoding="utf-8")
    return path
