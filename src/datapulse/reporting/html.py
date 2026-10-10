from html import escape
from pathlib import Path

from datapulse.models.report import AnalysisReport

HTML_CSS = """
:root {
    --bg-body: #0b0f19;
    --bg-card: #111827;
    --bg-card-hover: #1f2937;
    --border: #1f2937;
    --border-light: #374151;
    --text-primary: #f9fafb;
    --text-secondary: #9ca3af;
    --text-muted: #6b7280;
    --primary: #38bdf8;
    --success: #10b981;
    --warning: #f59e0b;
    --critical: #ef4444;
    --info: #6366f1;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    background-color: var(--bg-body);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    padding: 24px;
}
.container { max-width: 1320px; margin: 0 auto; }
header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}
.logo-group { display: flex; align-items: center; gap: 12px; }
.logo-badge {
    background: linear-gradient(135deg, #38bdf8 0%, #6366f1 100%);
    color: #fff;
    font-weight: 800;
    font-size: 16px;
    padding: 6px 12px;
    border-radius: 8px;
}
.file-title { font-size: 20px; font-weight: 700; color: var(--text-primary); }
.meta-badges { display: flex; gap: 8px; align-items: center; }
.badge {
    display: inline-flex;
    align-items: center;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.badge-type { background: #1e293b; color: #94a3b8; border: 1px solid #334155; }
.badge-neutral { background: #1f2937; color: #d1d5db; }
.badge-critical {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
}
.badge-warning {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.3);
}
.badge-info {
    background: rgba(99, 102, 241, 0.15);
    color: #818cf8;
    border: 1px solid rgba(99, 102, 241, 0.3);
}
.badge-success {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}
.role-numeric { background: rgba(56, 189, 248, 0.15); color: #38bdf8; }
.role-categorical { background: rgba(168, 85, 247, 0.15); color: #c084fc; }
.role-temporal { background: rgba(16, 185, 129, 0.15); color: #34d399; }
.role-boolean { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
.role-text { background: rgba(6, 182, 212, 0.15); color: #22d3ee; }
.role-identifier { background: rgba(99, 102, 241, 0.15); color: #818cf8; }
.role-constant { background: rgba(107, 114, 128, 0.15); color: #9ca3af; }
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.metric-label {
    font-size: 11px;
    color: var(--text-secondary);
    text-transform: uppercase;
    font-weight: 600;
}
.metric-value { font-size: 22px; font-weight: 700; color: var(--text-primary); }
.section-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
}
.section-title {
    font-size: 16px;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.finding-card {
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.finding-critical {
    background: rgba(239, 68, 68, 0.08);
    border-left: 4px solid var(--critical);
}
.finding-warning {
    background: rgba(245, 158, 11, 0.08);
    border-left: 4px solid var(--warning);
}
.finding-info {
    background: rgba(99, 102, 241, 0.08);
    border-left: 4px solid var(--info);
}
.finding-header { display: flex; align-items: center; gap: 10px; }
.finding-title { font-weight: 600; font-size: 13px; color: var(--text-primary); }
.finding-desc { font-size: 12px; color: var(--text-secondary); }
.table-container { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; text-align: left; }
.data-table th {
    background: rgba(255, 255, 255, 0.02);
    color: var(--text-secondary);
    font-size: 12px;
    font-weight: 600;
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
    text-transform: uppercase;
}
.data-table td {
    padding: 12px;
    border-bottom: 1px solid var(--border);
    color: var(--text-primary);
}
.data-table tr:hover td { background: var(--bg-card-hover); }
.progress-wrap { width: 140px; display: flex; flex-direction: column; gap: 4px; }
.progress-bar { height: 4px; background: var(--critical); border-radius: 2px; }
.progress-text {
    font-size: 11px;
    color: var(--text-secondary);
    font-family: monospace;
}
.stat-pill {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
    margin-right: 4px;
    display: inline-block;
    margin-bottom: 4px;
}
.cat-pills-row { margin-top: 4px; }
.cat-pill {
    background: rgba(168, 85, 247, 0.1);
    color: #d8b4fe;
    border: 1px solid rgba(168, 85, 247, 0.2);
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 10px;
    margin-right: 4px;
    display: inline-block;
}
.search-box {
    background: #1e293b;
    border: 1px solid #334155;
    color: #fff;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 13px;
    width: 240px;
    outline: none;
}
.search-box:focus { border-color: var(--primary); }
.font-mono {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
.font-bold { font-weight: 700; }
.text-right { text-align: right; }
.text-muted { color: var(--text-muted); }
.empty-state {
    color: var(--text-secondary);
    padding: 16px 0;
    font-style: italic;
}
footer {
    text-align: center;
    color: var(--text-muted);
    font-size: 12px;
    padding-top: 24px;
    border-top: 1px solid var(--border);
    margin-top: 32px;
}
"""


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

    findings_html = ""
    if report.findings:
        cards = []
        for f in report.findings:
            sev = f.severity.lower()
            cols_text = escape(", ".join(f.affected_columns))
            cols_badge = (
                f"<span class='badge badge-neutral'>{cols_text}</span>"
                if f.affected_columns
                else ""
            )
            card = (
                f"<div class='finding-card finding-{sev}'>"
                f"<div class='finding-header'>"
                f"<span class='badge badge-{sev}'>{escape(f.severity.upper())}</span>"
                f"<span class='finding-title'>{escape(f.title)}</span>"
                f"{cols_badge}"
                f"</div>"
                f"<div class='finding-desc'>{escape(f.description)}</div>"
                f"</div>"
            )
            cards.append(card)
        findings_html = "\n".join(cards)
    else:
        findings_html = (
            "<div class='empty-state'>"
            "No automated quality anomalies detected. Dataset looks clean!"
            "</div>"
        )

    col_rows = []
    for col in report.columns:
        role = escape(col.inferred_role)
        stats_items = []
        for k, v in col.statistics.items():
            if k in ("top_categories", "25%", "50%", "75%"):
                continue
            if v is not None:
                stats_items.append(
                    f"<span class='stat-pill'>{escape(k)}: "
                    f"<strong>{escape(str(v))}</strong></span>"
                )

        stats_summary = (
            " ".join(stats_items)
            if stats_items
            else "<span class='text-muted'>-</span>"
        )

        top_cats = col.statistics.get("top_categories", [])
        if isinstance(top_cats, list) and top_cats:
            cat_pills = [
                f"<span class='cat-pill'>{escape(str(c.get('value', '')))} "
                f"({float(c.get('percentage', 0.0)):.1f}%)</span>"
                for c in top_cats[:5]
                if isinstance(c, dict)
            ]
            if cat_pills:
                pills_html = " ".join(cat_pills)
                stats_summary += f"<div class='cat-pills-row'>{pills_html}</div>"

        missing_width = min(col.missing_percentage, 100)
        missing_bar = (
            "<div class='progress-wrap'>"
            f"<div class='progress-bar' style='width: {missing_width:.1f}%'></div>"
            f"<span class='progress-text'>{col.total_missing_count:,} "
            f"({col.missing_percentage:.1f}%)</span>"
            "</div>"
        )

        esc_type = escape(col.physical_type)
        row = (
            f"<tr class='col-row' data-name='{escape(col.name.lower())}' "
            f"data-role='{role}'>"
            f"<td class='font-mono font-bold'>{escape(col.name)}</td>"
            f"<td><span class='badge badge-type'>{esc_type}</span></td>"
            f"<td><span class='badge badge-role role-{role}'>{role}</span></td>"
            f"<td>{missing_bar}</td>"
            f"<td class='text-right font-mono'>{col.unique_count:,}</td>"
            f"<td class='stats-cell'>{stats_summary}</td>"
            f"</tr>"
        )
        col_rows.append(row)
    columns_table_html = "\n".join(col_rows)

    correlations_html = ""
    if report.correlations:
        corr_rows = []
        for pair in report.correlations[:20]:
            abs_coef = abs(pair.coefficient)
            sev_class = (
                "badge-critical"
                if abs_coef >= 0.85
                else ("badge-warning" if abs_coef >= 0.60 else "badge-neutral")
            )
            coef_str = f"{pair.coefficient:+.4f}"
            corr_rows.append(
                f"<tr>"
                f"<td class='font-mono'>{escape(pair.column_a)}</td>"
                f"<td class='font-mono'>{escape(pair.column_b)}</td>"
                f"<td class='text-right font-mono font-bold'>{coef_str}</td>"
                f"<td><span class='badge {sev_class}'>{abs_coef:.2f}</span></td>"
                f"<td class='text-muted'>{escape(pair.method)}</td>"
                f"</tr>"
            )
        correlations_html = (
            "<div class='section-card'>"
            "<div class='section-title'>Top Pairwise Correlations</div>"
            "<div class='table-container'>"
            "<table class='data-table'>"
            "<thead><tr>"
            "<th>Column A</th><th>Column B</th>"
            "<th class='text-right'>Coefficient (r)</th>"
            "<th>Strength</th><th>Method</th>"
            "</tr></thead>"
            f"<tbody>{' '.join(corr_rows)}</tbody>"
            "</table></div></div>"
        )

    key_candidates_html = ""
    if report.key_candidates:
        key_rows = []
        for key in report.key_candidates:
            key_rows.append(
                f"<tr>"
                f"<td class='font-mono font-bold'>{escape(key.column)}</td>"
                f"<td class='text-right font-mono'>{key.unique_count:,}</td>"
                f"<td><span class='badge badge-success'>"
                f"Primary Key Candidate (100% Unique)</span></td>"
                f"</tr>"
            )
        key_candidates_html = (
            "<div class='section-card'>"
            "<div class='section-title'>Key & Identifier Candidates</div>"
            "<div class='table-container'>"
            "<table class='data-table'>"
            "<thead><tr>"
            "<th>Column</th><th class='text-right'>Unique Values</th>"
            "<th>Candidate Status</th>"
            "</tr></thead>"
            f"<tbody>{' '.join(key_rows)}</tbody>"
            "</table></div></div>"
        )

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

    <script>
        const sBox = document.getElementById('column-search');
        sBox?.addEventListener('input', function(e) {{
            const query = e.target.value.toLowerCase().trim();
            const rows = document.querySelectorAll('.col-row');
            rows.forEach(row => {{
                const name = row.getAttribute('data-name') || '';
                const role = row.getAttribute('data-role') || '';
                if (name.includes(query) || role.includes(query)) {{
                    row.style.display = '';
                }} else {{
                    row.style.display = 'none';
                }}
            }});
        }});
    </script>
</body>
</html>"""

    return html


def export_html(report: AnalysisReport, output_path: str | Path) -> Path:
    """Generate and write a self-contained HTML report to disk."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    html_content = generate_html_report(report)
    path.write_text(html_content, encoding="utf-8")
    return path
