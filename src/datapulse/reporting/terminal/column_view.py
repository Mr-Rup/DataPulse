# =========================================================================
# DataPulse Terminal Column Profile View
# Exhaustive single-column statistical breakdown and anomaly audit.
# =========================================================================

from rich.panel import Panel
from rich.table import Table

from datapulse.models.report import AnalysisReport, ColumnProfile
from datapulse.reporting.terminal.console import console

# =========================================================================
# SINGLE COLUMN PROFILE RENDERER
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
