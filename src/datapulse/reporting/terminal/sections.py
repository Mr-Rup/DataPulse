# =========================================================================
# DataPulse Terminal High-Level Section Renderers
# Visual tables for dataset overviews, missingness, schema, and quality.
# =========================================================================

from rich.panel import Panel
from rich.table import Table

from datapulse.models.report import AnalysisReport
from datapulse.reporting.terminal.console import console

# =========================================================================
# OVERVIEW & SCHEMA RENDERERS
# =========================================================================

def display_overview(report: AnalysisReport) -> None:
    """Display high-level dataset dimensions, file size, and execution time."""
    summary = report.summary
    console.print(
        Panel(
            f"[bold]File:[/bold] {summary.file_name}\n"
            f"[bold]Path:[/bold] {report.metadata.source_path}\n"
            f"[bold]Size:[/bold] {summary.file_size_mb} MB\n"
            f"[bold]Rows:[/bold] {summary.row_count:,}\n"
            f"[bold]Columns:[/bold] {summary.column_count}\n"
            f"[bold]Elapsed:[/bold] {report.metadata.elapsed_seconds:.4f}s",
            title="DataPulse | Dataset Overview",
        )
    )


def display_schema(
    report: AnalysisReport, columns: list[str] | None = None
) -> None:
    """Display table of column names and physical Polars data types."""
    schema_table = Table(title="Dataset Schema")
    schema_table.add_column("Column", style="bold")
    schema_table.add_column("Data Type", style="cyan")
    cols_filter = set(columns) if columns else None
    for column, dtype in report.summary.schema.items():
        if cols_filter is None or column in cols_filter:
            schema_table.add_row(column, dtype)
    console.print(schema_table)


# =========================================================================
# MISSINGNESS & DUPLICATE RENDERERS
# =========================================================================

def display_missing(
    report: AnalysisReport, columns: list[str] | None = None
) -> None:
    """Display comprehensive missingness accounting for nulls, NaNs, and sentinels."""
    missing_table = Table(title="Missing Values & Data Gaps")
    missing_table.add_column("Column", style="bold")
    missing_table.add_column("Nulls", justify="right")
    missing_table.add_column("NaNs", justify="right")
    missing_table.add_column("Empty/Sentinels", justify="right")
    missing_table.add_column("Total Missing", justify="right")
    missing_table.add_column("Missing %", justify="right")
    cols_filter = set(columns) if columns else None
    for item in report.missing_values:
        if cols_filter is None or item.column in cols_filter:
            empty_sentinels = item.empty_count + item.sentinel_count
            pct_color = "red" if item.missing_percentage > 50 else (
                "yellow" if item.missing_percentage > 10 else "white"
            )
            missing_table.add_row(
                item.column,
                f"{item.null_count:,}",
                f"{item.nan_count:,}",
                f"{empty_sentinels:,}",
                f"{item.total_missing_count:,}",
                f"[{pct_color}]{item.missing_percentage:.2f}%[/{pct_color}]",
            )
    console.print(missing_table)


def display_duplicates(report: AnalysisReport) -> None:
    """Display full-row duplicate counts and duplication percentage."""
    dup = report.duplicates
    duplicate_table = Table(title="Duplicate Row Analysis")
    duplicate_table.add_column("Metric", style="bold")
    duplicate_table.add_column("Value", justify="right")
    duplicate_table.add_row("Total Rows", f"{dup.total_rows:,}")
    duplicate_table.add_row("Unique Rows", f"{dup.unique_rows:,}")
    duplicate_table.add_row("Duplicate Rows", f"{dup.duplicate_rows:,}")
    dup_color = "red" if dup.duplicate_percentage > 10 else (
        "yellow" if dup.duplicate_percentage > 0 else "green"
    )
    duplicate_table.add_row(
        "Duplicate Percentage",
        f"[{dup_color}]{dup.duplicate_percentage:.2f}%[/{dup_color}]",
    )
    console.print(duplicate_table)


# =========================================================================
# QUALITY & ANOMALY FINDINGS RENDERERS
# =========================================================================

def display_quality(
    report: AnalysisReport, columns: list[str] | None = None
) -> None:
    """Display column quality table with role classification and null rates."""
    quality_table = Table(title="Column Quality Summary")
    quality_table.add_column("Column", style="bold")
    quality_table.add_column("Type", style="dim")
    quality_table.add_column("Inferred Role", style="cyan")
    quality_table.add_column("Missing", justify="right")
    quality_table.add_column("Missing %", justify="right")
    quality_table.add_column("Distinct", justify="right")
    cols_filter = set(columns) if columns else None
    for col in report.columns:
        if cols_filter is None or col.name in cols_filter:
            quality_table.add_row(
                col.name,
                col.physical_type,
                col.inferred_role,
                f"{col.total_missing_count:,}",
                f"{col.missing_percentage:.2f}%",
                f"{col.unique_count:,}",
            )
    console.print(quality_table)


def display_findings(report: AnalysisReport) -> None:
    """Display data quality findings, severe anomalies, and domain warnings."""
    if not report.findings:
        console.print(
            Panel(
                "[green]No quality anomalies detected. Dataset is clean![/green]",
                title="Data Quality Assessment",
            )
        )
        return
    findings_table = Table(title="Data Quality Findings & Anomalies")
    findings_table.add_column("Severity")
    findings_table.add_column("Rule ID", style="dim")
    findings_table.add_column("Columns")
    findings_table.add_column("Title", style="bold")
    findings_table.add_column("Description")
    for f in report.findings:
        sev_color = (
            "red"
            if f.severity == "critical"
            else ("yellow" if f.severity == "warning" else "blue")
        )
        cols_str = ", ".join(f.affected_columns) if f.affected_columns else "-"
        findings_table.add_row(
            f"[{sev_color}]{f.severity.upper()}[/{sev_color}]",
            f.rule_id,
            cols_str,
            f.title,
            f.description,
        )
    console.print(findings_table)


# =========================================================================
# CORRELATION & PRIMARY KEY CANDIDATE RENDERERS
# =========================================================================

def display_correlations(
    report: AnalysisReport, limit: int = 10
) -> None:
    """Display strongest pairwise numeric correlations and sample observations."""
    if not report.correlations:
        return
    top_corr = report.correlations[:limit]
    corr_table = Table(title=f"Top Numeric Correlations (Top {len(top_corr)})")
    corr_table.add_column("Column A", style="bold")
    corr_table.add_column("Column B", style="bold")
    corr_table.add_column("Correlation (r)", justify="right")
    corr_table.add_column("Pairs (N)", justify="right")
    corr_table.add_column("Method", style="dim")
    corr_table.add_column("Strength")
    for pair in top_corr:
        abs_val = abs(pair.coefficient)
        if abs_val >= 0.85:
            strength = "Very Strong"
            color = "red"
        elif abs_val >= 0.60:
            strength = "Strong"
            color = "yellow"
        elif abs_val >= 0.30:
            strength = "Moderate"
            color = "cyan"
        else:
            strength = "Weak"
            color = "white"
        n_str = (
            f"{pair.common_observations:,}"
            if pair.common_observations > 0
            else "-"
        )
        corr_table.add_row(
            pair.column_a,
            pair.column_b,
            f"[{color}]{pair.coefficient:+.4f}[/{color}]",
            n_str,
            pair.method,
            strength,
        )
    console.print(corr_table)


def display_keys(report: AnalysisReport) -> None:
    """Display potential primary key candidates with 100% uniqueness."""
    if not report.key_candidates:
        return
    key_table = Table(title="Key & Identifier Candidates")
    key_table.add_column("Column", style="bold")
    key_table.add_column("Unique Count", justify="right")
    key_table.add_column("Primary Key Candidate")
    for key in report.key_candidates:
        status = (
            "[green]Yes (100% unique, 0 nulls)[/green]"
            if key.is_primary_key_candidate
            else "[dim]No[/dim]"
        )
        key_table.add_row(
            key.column,
            f"{key.unique_count:,}",
            status,
        )
    console.print(key_table)
