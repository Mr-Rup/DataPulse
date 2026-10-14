# =========================================================================
# DataPulse HTML Reporting Engine
# Interactive dashboard generator with embedded dark theme and live search.
# =========================================================================

from datapulse.reporting.html.components import (
    render_column_rows,
    render_correlations,
    render_findings,
    render_key_candidates,
)
from datapulse.reporting.html.generator import export_html, generate_html_report
from datapulse.reporting.html.scripts import HTML_SCRIPT
from datapulse.reporting.html.styles import HTML_CSS

__all__ = [
    "HTML_CSS",
    "HTML_SCRIPT",
    "export_html",
    "generate_html_report",
    "render_column_rows",
    "render_correlations",
    "render_findings",
    "render_key_candidates",
]
