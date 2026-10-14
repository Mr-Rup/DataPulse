# =========================================================================
# DataPulse Terminal Report Formatter
# Rich tables and panels displaying dataset overviews, missingness grids,
# column statistics, quality findings, correlations, and key candidates.
# =========================================================================

from typing import Any

import polars as pl
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from datapulse.models.report import AnalysisReport, ColumnProfile

console = Console()

# =========================================================================
# SECTION FORMATTING HELPERS
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


def display_numeric(
    report: AnalysisReport, columns: list[str] | None = None
) -> None:
    """Display numeric statistics table including quantiles, zeros, and negatives."""
    cols_filter = set(columns) if columns else None
    numeric_cols = [
        col
        for col in report.columns
        if col.inferred_role == "numeric" and "mean" in col.statistics
        and (cols_filter is None or col.name in cols_filter)
    ]
    if not numeric_cols:
        return
    num_table = Table(title="Numeric Statistics")
    num_table.add_column("Column", style="bold")
    num_table.add_column("Mean", justify="right")
    num_table.add_column("Std", justify="right")
    num_table.add_column("Min", justify="right")
    num_table.add_column("Median", justify="right")
    num_table.add_column("Max", justify="right")
    num_table.add_column("Zeros %", justify="right")
    num_table.add_column("Neg %", justify="right")
    for col in numeric_cols:
        s = col.statistics
        mean_str = f"{float(s['mean']):.2f}" if s.get("mean") is not None else "-"
        std_str = f"{float(s['std']):.2f}" if s.get("std") is not None else "-"
        min_str = f"{float(s['min']):.2f}" if s.get("min") is not None else "-"
        med_val = s.get("median", s.get("50%"))
        med_str = f"{float(med_val):.2f}" if med_val is not None else "-"
        max_str = f"{float(s['max']):.2f}" if s.get("max") is not None else "-"
        zeros_pct = f"{float(s.get('zeros_percentage', 0.0)):.2f}%"
        neg_pct = f"{float(s.get('negatives_percentage', 0.0)):.2f}%"
        num_table.add_row(
            col.name,
            mean_str,
            std_str,
            min_str,
            med_str,
            max_str,
            zeros_pct,
            neg_pct,
        )
    console.print(num_table)


def display_categorical(
    report: AnalysisReport, columns: list[str] | None = None
) -> None:
    """Display categorical analysis table with distinct counts and mode values."""
    cols_filter = set(columns) if columns else None
    cat_cols = [
        col
        for col in report.columns
        if col.inferred_role == "categorical"
        and (cols_filter is None or col.name in cols_filter)
    ]
    if not cat_cols:
        return
    cat_table = Table(title="Categorical Analysis")
    cat_table.add_column("Column", style="bold")
    cat_table.add_column("Distinct", justify="right")
    cat_table.add_column("Cardinality %", justify="right")
    cat_table.add_column("Mode / Top Value")
    cat_table.add_column("Top Value %", justify="right")
    for col in cat_cols:
        s = col.statistics
        uniq = s.get("unique_count", col.unique_count)
        card = s.get("cardinality_percentage", 0.0)
        top_cats = s.get("top_categories", [])
        top_val = "-"
        top_pct = "-"
        if isinstance(top_cats, list) and top_cats:
            first = top_cats[0]
            if isinstance(first, dict):
                top_val = str(first.get("value", "-"))
                top_pct = f"{float(first.get('percentage', 0.0)):.2f}%"
        elif "mode" in s and s["mode"] is not None:
            top_val = str(s["mode"])
        cat_table.add_row(
            col.name,
            f"{int(uniq):,}",
            f"{float(card):.2f}%",
            top_val,
            top_pct,
        )
    console.print(cat_table)


def display_temporal(
    report: AnalysisReport, columns: list[str] | None = None
) -> None:
    """Display date and timestamp ranges with duration spans."""
    cols_filter = set(columns) if columns else None
    temporal_cols = [
        col
        for col in report.columns
        if col.inferred_role == "temporal"
        and (cols_filter is None or col.name in cols_filter)
    ]
    if not temporal_cols:
        return
    temp_table = Table(title="Date/Time Analysis")
    temp_table.add_column("Column", style="bold")
    temp_table.add_column("Minimum")
    temp_table.add_column("Maximum")
    temp_table.add_column("Span (Days)", justify="right")
    temp_table.add_column("Distinct", justify="right")
    for col in temporal_cols:
        s = col.statistics
        span_days = s.get("span_days")
        span_str = f"{float(span_days):.2f}" if span_days is not None else "-"
        uniq = s.get("unique_count", col.unique_count)
        temp_table.add_row(
            col.name,
            str(s.get("minimum", "-")),
            str(s.get("maximum", "-")),
            span_str,
            f"{int(uniq):,}",
        )
    console.print(temp_table)


def display_boolean(
    report: AnalysisReport, columns: list[str] | None = None
) -> None:
    """Display boolean flag distribution counts and percentages."""
    cols_filter = set(columns) if columns else None
    bool_cols = [
        col
        for col in report.columns
        if col.inferred_role == "boolean" and "true_percentage" in col.statistics
        and (cols_filter is None or col.name in cols_filter)
    ]
    if not bool_cols:
        return
    bool_table = Table(title="Boolean Analysis")
    bool_table.add_column("Column", style="bold")
    bool_table.add_column("True Count", justify="right")
    bool_table.add_column("True %", justify="right")
    bool_table.add_column("False Count", justify="right")
    bool_table.add_column("False %", justify="right")
    for col in bool_cols:
        s = col.statistics
        bool_table.add_row(
            col.name,
            f"{int(s.get('true_count', 0)):,}",
            f"{float(s.get('true_percentage', 0.0)):.2f}%",
            f"{int(s.get('false_count', 0)):,}",
            f"{float(s.get('false_percentage', 0.0)):.2f}%",
        )
    console.print(bool_table)


def display_text(
    report: AnalysisReport, columns: list[str] | None = None
) -> None:
    """Display freeform text lengths and empty string percentages."""
    cols_filter = set(columns) if columns else None
    text_cols = [
        col
        for col in report.columns
        if col.inferred_role == "text" and "min_length" in col.statistics
        and (cols_filter is None or col.name in cols_filter)
    ]
    if not text_cols:
        return
    txt_table = Table(title="Text Analysis")
    txt_table.add_column("Column", style="bold")
    txt_table.add_column("Min Len", justify="right")
    txt_table.add_column("Max Len", justify="right")
    txt_table.add_column("Mean Len", justify="right")
    txt_table.add_column("Empty %", justify="right")
    for col in text_cols:
        s = col.statistics
        txt_table.add_row(
            col.name,
            f"{int(s.get('min_length', 0)):,}",
            f"{int(s.get('max_length', 0)):,}",
            f"{float(s.get('mean_length', 0.0)):.2f}",
            f"{float(s.get('empty_percentage', 0.0)):.2f}%",
        )
    console.print(txt_table)


def display_identifiers(
    report: AnalysisReport, columns: list[str] | None = None
) -> None:
    """Display identifier uniqueness percentages and duplicate counts."""
    cols_filter = set(columns) if columns else None
    id_cols = [
        col
        for col in report.columns
        if col.inferred_role == "identifier"
        and "uniqueness_percentage" in col.statistics
        and (cols_filter is None or col.name in cols_filter)
    ]
    if not id_cols:
        return
    id_table = Table(title="Identifier Analysis")
    id_table.add_column("Column", style="bold")
    id_table.add_column("Unique Count", justify="right")
    id_table.add_column("Uniqueness %", justify="right")
    id_table.add_column("Duplicate Count", justify="right")
    for col in id_cols:
        s = col.statistics
        id_table.add_row(
            col.name,
            f"{int(s.get('unique_count', col.unique_count)):,}",
            f"{float(s.get('uniqueness_percentage', 0.0)):.2f}%",
            f"{int(s.get('duplicate_count', 0)):,}",
        )
    console.print(id_table)


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


# =========================================================================
# COMPREHENSIVE TERMINAL REPORT FORMATTER
# =========================================================================

SECTION_HANDLERS = {
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
        if sec_key in ("schema", "missing", "quality", "numeric", "categorical",
                       "temporal", "datetime", "date", "boolean", "bool", "text",
                       "identifiers", "identifier", "id"):
            handler(report, columns=columns)  # type: ignore
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


# =========================================================================
# SINGLE COLUMN DEEP-DIVE INSPECTION
# =========================================================================

def display_column_profile(report: AnalysisReport, column_name: str) -> None:
    """Display an exhaustive statistical profile for a single column."""
    matched_col: ColumnProfile | None = None
    for col in report.columns:
        if col.name.lower() == column_name.lower():
            matched_col = col
            break
    if not matched_col:
        valid_cols = ", ".join([c.name for c in report.columns])
        raise ValueError(
            f"Column '{column_name}' not found. Available columns: {valid_cols}"
        )
    # Column Metadata Header
    conf_pct = int(matched_col.confidence * 100)
    console.print(
        Panel(
            f"[bold]Column:[/bold] {matched_col.name}\n"
            f"[bold]Physical Type:[/bold] {matched_col.physical_type}\n"
            f"[bold]Inferred Role:[/bold] [cyan]{matched_col.inferred_role}[/cyan] "
            f"({conf_pct}% confidence)\n"
            f"[bold]Classification Reason:[/bold] {matched_col.inference_reason}\n"
            f"[bold]Unique Count:[/bold] {matched_col.unique_count:,}",
            title=f"DataPulse | Column: {matched_col.name}",
        )
    )
    # Missingness accounting for this column
    miss_table = Table(title=f"Missingness Breakdown: {matched_col.name}")
    miss_table.add_column("Metric", style="bold")
    miss_table.add_column("Count", justify="right")
    miss_table.add_row("Null Values", f"{matched_col.null_count:,}")
    miss_table.add_row("Float NaNs", f"{matched_col.nan_count:,}")
    miss_table.add_row("Empty Strings", f"{matched_col.empty_count:,}")
    miss_table.add_row("Total Missing", f"{matched_col.total_missing_count:,}")
    miss_table.add_row("Missing Percentage", f"{matched_col.missing_percentage:.2f}%")
    console.print(miss_table)
    # Detailed role statistics
    stats = matched_col.statistics
    if stats:
        stat_table = Table(title=f"Distribution & Statistics: {matched_col.name}")
        stat_table.add_column("Metric", style="bold")
        stat_table.add_column("Value", justify="right")
        for k, v in stats.items():
            if k == "top_categories":
                continue
            val_str = f"{float(v):.4f}" if isinstance(v, float) else str(v)
            stat_table.add_row(k.replace("_", " ").title(), val_str)
        console.print(stat_table)
    # Top Categories if categorical
    top_cats = stats.get("top_categories", [])
    if isinstance(top_cats, list) and top_cats:
        cat_table = Table(title=f"Top Categories: {matched_col.name}")
        cat_table.add_column("Category Value", style="bold")
        cat_table.add_column("Frequency", justify="right")
        cat_table.add_column("Percentage", justify="right")
        for item in top_cats:
            if isinstance(item, dict):
                cat_table.add_row(
                    str(item.get("value", "-")),
                    f"{int(item.get('count', 0)):,}",
                    f"{float(item.get('percentage', 0.0)):.2f}%",
                )
        console.print(cat_table)
    # Quality Findings for this column
    col_findings = [
        f for f in report.findings if matched_col.name in f.affected_columns
    ]
    if col_findings:
        f_table = Table(title=f"Data Quality Alerts: {matched_col.name}")
        f_table.add_column("Severity")
        f_table.add_column("Title", style="bold")
        f_table.add_column("Description")
        for f in col_findings:
            sev_color = (
                "red"
                if f.severity == "critical"
                else ("yellow" if f.severity == "warning" else "blue")
            )
            f_table.add_row(
                f"[{sev_color}]{f.severity.upper()}[/{sev_color}]",
                f.title,
                f.description,
            )
        console.print(f_table)


# =========================================================================
# QUERY RESULTS & FILE INFO DISPLAY
# =========================================================================

def display_query_results(df: pl.DataFrame, title: str = "Query Results") -> None:
    """Render matching Polars DataFrame query results in a clean Rich table."""
    table = Table(title=f"{title} ({df.height:,} rows, {df.width} cols)")
    for col in df.columns:
        table.add_column(col, style="cyan")
    # Truncate row display if large to avoid terminal freeze
    display_rows = df.head(50)
    for row in display_rows.iter_rows():
        table.add_row(
            *[str(val) if val is not None else "[dim]null[/dim]" for val in row]
        )
    console.print(table)
    if df.height > 50:
        console.print(
            f"[dim]... showing first 50 rows of {df.height:,} total rows.[/dim]"
        )


def display_file_info(
    source_name: str,
    file_path: str,
    file_format: str,
    file_size_mb: float,
    schema: dict[str, Any],
    row_count: int | None = None,
) -> None:
    """Display instant file metadata and schema without full profiling overhead."""
    row_str = f"{row_count:,}" if row_count is not None else "Lazy (Not collected)"
    console.print(
        Panel(
            f"[bold]Source:[/bold] {source_name}\n"
            f"[bold]Path:[/bold] {file_path}\n"
            f"[bold]Format:[/bold] [cyan]{file_format.upper()}[/cyan]\n"
            f"[bold]Size:[/bold] {file_size_mb:.2f} MB\n"
            f"[bold]Rows:[/bold] {row_str}\n"
            f"[bold]Columns:[/bold] {len(schema)}",
            title="DataPulse | File Information",
        )
    )
    schema_table = Table(title="Schema Definition")
    schema_table.add_column("Column Name", style="bold")
    schema_table.add_column("Polars Data Type", style="cyan")
    for col_name, dtype in schema.items():
        schema_table.add_row(col_name, str(dtype))
    console.print(schema_table)
