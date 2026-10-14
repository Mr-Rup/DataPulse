# =========================================================================
# DataPulse HTML Report Stylesheet
# Clean, modern, responsive dark-mode CSS tokens and components.
# =========================================================================

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
