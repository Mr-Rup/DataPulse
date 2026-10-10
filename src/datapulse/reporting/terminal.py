from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from datapulse.models.report import AnalysisReport
from datapulse.profiling.profiler import DatasetProfiler

console = Console()


def display_report(report: AnalysisReport) -> None:
    """Display an AnalysisReport in the terminal."""

    summary = report.summary
    console.print(
        Panel(
            f"[bold]File:[/bold] {summary.file_name}\n"
            f"[bold]Size:[/bold] {summary.file_size_mb} MB\n"
            f"[bold]Rows:[/bold] {summary.row_count:,}\n"
            f"[bold]Columns:[/bold] {summary.column_count}\n"
            f"[bold]Elapsed:[/bold] {report.metadata.elapsed_seconds:.4f}s",
            title="DataPulse | Dataset Overview",
        )
    )

    schema_table = Table(title="Dataset Schema")
    schema_table.add_column("Column")
    schema_table.add_column("Data Type")

    for column, dtype in summary.schema.items():
        schema_table.add_row(column, dtype)

    console.print(schema_table)

    missing_table = Table(title="Missing Values & Data Gaps")
    missing_table.add_column("Column")
    missing_table.add_column("Nulls", justify="right")
    missing_table.add_column("NaNs", justify="right")
    missing_table.add_column("Empty/Sentinels", justify="right")
    missing_table.add_column("Total Missing", justify="right")
    missing_table.add_column("Missing %", justify="right")

    for item in report.missing_values:
        empty_sentinels = item.empty_count + item.sentinel_count
        missing_table.add_row(
            item.column,
            f"{item.null_count:,}",
            f"{item.nan_count:,}",
            f"{empty_sentinels:,}",
            f"{item.total_missing_count:,}",
            f"{item.missing_percentage:.2f}%",
        )

    console.print(missing_table)

    dup = report.duplicates
    duplicate_table = Table(title="Duplicate Row Analysis")
    duplicate_table.add_column("Metric")
    duplicate_table.add_column("Value", justify="right")

    duplicate_table.add_row("Total Rows", f"{dup.total_rows:,}")
    duplicate_table.add_row("Unique Rows", f"{dup.unique_rows:,}")
    duplicate_table.add_row("Duplicate Rows", f"{dup.duplicate_rows:,}")
    duplicate_table.add_row("Duplicate Percentage", f"{dup.duplicate_percentage:.2f}%")

    console.print(duplicate_table)

    quality_table = Table(title="Column Quality Summary")
    quality_table.add_column("Column")
    quality_table.add_column("Type")
    quality_table.add_column("Role")
    quality_table.add_column("Missing", justify="right")
    quality_table.add_column("Missing %", justify="right")
    quality_table.add_column("Distinct", justify="right")

    for col in report.columns:
        quality_table.add_row(
            col.name,
            col.physical_type,
            col.inferred_role,
            f"{col.total_missing_count:,}",
            f"{col.missing_percentage:.2f}%",
            f"{col.unique_count:,}",
        )

    console.print(quality_table)

    # 1. Numeric Analysis
    numeric_cols = [
        col
        for col in report.columns
        if col.inferred_role == "numeric" and "mean" in col.statistics
    ]
    if numeric_cols:
        num_table = Table(title="Numeric Statistics")
        num_table.add_column("Column")
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

    # 2. Categorical Analysis
    cat_cols = [col for col in report.columns if col.inferred_role == "categorical"]
    if cat_cols:
        cat_table = Table(title="Categorical Analysis")
        cat_table.add_column("Column")
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

    # 3. Temporal Analysis
    temporal_cols = [col for col in report.columns if col.inferred_role == "temporal"]
    if temporal_cols:
        temp_table = Table(title="Date/Time Analysis")
        temp_table.add_column("Column")
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

    # 4. Boolean Analysis
    bool_cols = [
        col
        for col in report.columns
        if col.inferred_role == "boolean" and "true_percentage" in col.statistics
    ]
    if bool_cols:
        bool_table = Table(title="Boolean Analysis")
        bool_table.add_column("Column")
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

    # 5. Text Analysis
    text_cols = [
        col
        for col in report.columns
        if col.inferred_role == "text" and "min_length" in col.statistics
    ]
    if text_cols:
        txt_table = Table(title="Text Analysis")
        txt_table.add_column("Column")
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

    # 6. Identifier Analysis
    id_cols = [
        col
        for col in report.columns
        if col.inferred_role == "identifier"
        and "uniqueness_percentage" in col.statistics
    ]
    if id_cols:
        id_table = Table(title="Identifier Analysis")
        id_table.add_column("Column")
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

    if report.findings:
        findings_table = Table(title="Data Quality Findings & Anomalies")
        findings_table.add_column("Severity")
        findings_table.add_column("Rule ID")
        findings_table.add_column("Columns")
        findings_table.add_column("Title")
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

    if report.correlations:
        top_corr = report.correlations[:10]
        corr_table = Table(title="Top Numeric Correlations")
        corr_table.add_column("Column A")
        corr_table.add_column("Column B")
        corr_table.add_column("Correlation (r)", justify="right")
        corr_table.add_column("Method")
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

            corr_table.add_row(
                pair.column_a,
                pair.column_b,
                f"[{color}]{pair.coefficient:+.4f}[/{color}]",
                pair.method,
                strength,
            )
        console.print(corr_table)

    if report.key_candidates:
        key_table = Table(title="Key & Identifier Candidates")
        key_table.add_column("Column")
        key_table.add_column("Unique Count", justify="right")
        key_table.add_column("Primary Key Candidate")

        for key in report.key_candidates:
            status = (
                "[green]Yes (100% unique, 0 nulls)[/green]"
                if key.is_primary_key_candidate
                else "No"
            )
            key_table.add_row(
                key.column,
                f"{key.unique_count:,}",
                status,
            )
        console.print(key_table)


def display_profile(target: AnalysisReport | DatasetProfiler) -> None:
    """Display profile for an AnalysisReport or DatasetProfiler in the terminal."""

    if isinstance(target, AnalysisReport):
        display_report(target)
        return

    from datapulse.api import analyze

    report = analyze(target.file_path)
    display_report(report)
