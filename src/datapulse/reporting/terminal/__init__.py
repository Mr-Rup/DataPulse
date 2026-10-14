# =========================================================================
# DataPulse Terminal Reporting Engine
# Interactive Rich tables, section dispatchers, and query formatters.
# =========================================================================

from datapulse.reporting.terminal.column_view import display_column_profile
from datapulse.reporting.terminal.console import console
from datapulse.reporting.terminal.formatter import (
    SECTION_HANDLERS,
    display_profile,
    display_report,
)
from datapulse.reporting.terminal.query_view import (
    display_file_info,
    display_query_results,
)
from datapulse.reporting.terminal.roles import (
    display_boolean,
    display_categorical,
    display_identifiers,
    display_numeric,
    display_temporal,
    display_text,
)
from datapulse.reporting.terminal.sections import (
    display_correlations,
    display_duplicates,
    display_findings,
    display_keys,
    display_missing,
    display_overview,
    display_quality,
    display_schema,
)

__all__ = [
    "SECTION_HANDLERS",
    "console",
    "display_boolean",
    "display_categorical",
    "display_column_profile",
    "display_correlations",
    "display_duplicates",
    "display_file_info",
    "display_findings",
    "display_identifiers",
    "display_keys",
    "display_missing",
    "display_numeric",
    "display_overview",
    "display_profile",
    "display_quality",
    "display_query_results",
    "display_report",
    "display_schema",
    "display_temporal",
    "display_text",
]
