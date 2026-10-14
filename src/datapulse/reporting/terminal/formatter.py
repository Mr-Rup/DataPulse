# =========================================================================
# DataPulse Terminal Report Formatter
# Central report coordinator dispatching default and custom section views.
# =========================================================================

from collections.abc import Callable
from typing import Any

from datapulse.models.report import AnalysisReport
from datapulse.reporting.terminal.console import console
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

# =========================================================================
# SECTION DISPATCH REGISTRY
# =========================================================================

SECTION_HANDLERS: dict[str, Callable[..., Any]] = {
    "overview": display_overview,
    "schema": display_schema,
    "missing": display_missing,
    "duplicates": display_duplicates,
    "duplicate": display_duplicates,
    "quality": display_quality,
    "numeric": display_numeric,
    "categorical": display_categorical,
    "temporal": display_temporal,
    "datetime": display_temporal,
    "date": display_temporal,
    "boolean": display_boolean,
    "bool": display_boolean,
    "text": display_text,
    "identifiers": display_identifiers,
    "identifier": display_identifiers,
    "id": display_identifiers,
    "findings": display_findings,
    "anomalies": display_findings,
    "correlations": display_correlations,
    "corr": display_correlations,
    "keys": display_keys,
    "key": display_keys,
}


# =========================================================================
# COMPREHENSIVE TERMINAL REPORT FORMATTER
# =========================================================================

def display_report(
    report: AnalysisReport,
    *,
    full: bool = False,
    section: str | None = None,
    columns: list[str] | None = None,
) -> None:
    """Display an AnalysisReport in terminal with filtering and section control."""
    # 1. Single section inspection
    if section:
        sec_key = section.strip().lower()
        if sec_key not in SECTION_HANDLERS:
            valid_secs = ", ".join(sorted(set(SECTION_HANDLERS.keys())))
            raise ValueError(
                f"Unknown section '{section}'. Available sections: {valid_secs}"
            )
        handler = SECTION_HANDLERS[sec_key]
        if sec_key in (
            "schema",
            "missing",
            "quality",
            "numeric",
            "categorical",
            "temporal",
            "datetime",
            "date",
            "boolean",
            "bool",
            "text",
            "identifiers",
            "identifier",
            "id",
        ):
            handler(report, columns=columns)
        else:
            handler(report)
        return

    # 2. Exhaustive Full Report
    if full:
        display_overview(report)
        display_schema(report, columns=columns)
        display_missing(report, columns=columns)
        display_duplicates(report)
        display_quality(report, columns=columns)
        display_numeric(report, columns=columns)
        display_categorical(report, columns=columns)
        display_temporal(report, columns=columns)
        display_boolean(report, columns=columns)
        display_text(report, columns=columns)
        display_identifiers(report, columns=columns)
        display_findings(report)
        display_correlations(report, limit=15)
        display_keys(report)
        return

    # 3. Default View (5-6 Core Features for Clean Terminal Output)
    display_overview(report)
    display_findings(report)
    display_duplicates(report)
    display_quality(report, columns=columns)
    display_missing(report, columns=columns)
    display_keys(report)
    if report.correlations:
        display_correlations(report, limit=5)
    console.print(
        "\n[dim]Tip: Run [bold]datapulse show <file> <section>[/bold] "
        "or [bold]datapulse <file> --all[/bold] for detailed role breakdowns.[/dim]\n"
    )


display_profile = display_report
