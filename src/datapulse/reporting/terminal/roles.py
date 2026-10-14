# =========================================================================
# DataPulse Terminal Role-Specific Renderers
# Statistical tables for numeric, categorical, temporal, text, and IDs.
# =========================================================================

from rich.table import Table

from datapulse.models.report import AnalysisReport
from datapulse.reporting.terminal.console import console

# =========================================================================
# NUMERIC & CATEGORICAL TABLES
# =========================================================================

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


# =========================================================================
# TEMPORAL, BOOLEAN, TEXT, AND IDENTIFIER TABLES
# =========================================================================

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
