import time
from datetime import UTC, datetime
from pathlib import Path

from datapulse import __version__
from datapulse.analysis.column_classifier import classify_columns
from datapulse.analysis.quality_rules import evaluate_quality_rules
from datapulse.analysis.relationships import (
    compute_correlations,
    evaluate_collinear_findings,
    find_key_candidates,
)
from datapulse.config import AnalysisConfig
from datapulse.models.report import (
    AnalysisReport,
    ColumnProfile,
    DatasetSummary,
    DuplicateSummary,
    MissingSummary,
    ReportMetadata,
)
from datapulse.profiling.profiler import DatasetProfiler


def analyze(
    file_path: str | Path,
    config: AnalysisConfig | None = None,
) -> AnalysisReport:
    """Analyze a dataset and produce a structured AnalysisReport."""

    start_time = time.perf_counter()
    path = Path(file_path)

    profiler = DatasetProfiler(
        path,
        sheet_name=config.sheet_name if config else None,
        separator=config.separator if config else None,
        sample_size=config.sample_size if config else None,
        sample_method=config.sample_method if config else "head",
    )

    overview = profiler.get_overview()
    missing_df = profiler.get_missing_values()
    duplicate_dict = profiler.get_duplicate_summary()
    quality_df = profiler.get_column_quality()

    summary = DatasetSummary(
        file_name=overview["file_name"],
        file_size_mb=overview["file_size_mb"],
        row_count=overview["row_count"],
        column_count=overview["column_count"],
        schema=overview["schema"],
    )

    duplicates = DuplicateSummary(
        total_rows=int(duplicate_dict["total_rows"]),
        unique_rows=int(duplicate_dict["unique_rows"]),
        duplicate_rows=int(duplicate_dict["duplicate_rows"]),
        duplicate_percentage=float(duplicate_dict["duplicate_percentage"]),
    )

    missing_values = [
        MissingSummary(
            column=row["column"],
            null_count=int(row["null_count"]),
            non_missing_count=int(row["non_missing_count"]),
            missing_percentage=float(row["missing_percentage"]),
        )
        for row in missing_df.iter_rows(named=True)
    ]

    quality_map = {row["column"]: row for row in quality_df.iter_rows(named=True)}

    classifications = classify_columns(profiler.data)
    max_categories = config.max_categories if config else 20

    columns: list[ColumnProfile] = []
    for col_name, dtype_str in overview["schema"].items():
        q_info = quality_map.get(col_name, {})
        classification = classifications.get(col_name)
        role = (
            classification.inferred_role
            if classification
            else q_info.get("category", "unknown")
        )
        conf = classification.confidence if classification else 1.0
        reason = classification.reason if classification else ""

        stats = profiler.profile_column(
            col_name,
            role=role,
            max_categories=max_categories,
        )

        profile = ColumnProfile(
            name=col_name,
            physical_type=dtype_str,
            inferred_role=role,
            confidence=conf,
            inference_reason=reason,
            null_count=int(q_info.get("null_count", 0)),
            missing_percentage=float(q_info.get("missing_percentage", 0.0)),
            unique_count=int(q_info.get("unique_count", 0)),
            statistics=stats,
        )
        columns.append(profile)

    elapsed = round(time.perf_counter() - start_time, 4)

    metadata = ReportMetadata(
        datapulse_version=__version__,
        created_at=datetime.now(UTC).isoformat(),
        source_name=path.name,
        source_path=str(path.resolve()),
        file_size_mb=summary.file_size_mb,
        elapsed_seconds=elapsed,
    )

    compute_corr = config.compute_correlations if config else True
    if compute_corr:
        corr_method = config.correlation_method if config else "pearson"
        min_threshold = config.min_correlation if config else 0.50
        method_literal = "spearman" if corr_method == "spearman" else "pearson"
        numeric_col_names = [c.name for c in columns if c.inferred_role == "numeric"]
        correlations = compute_correlations(
            profiler.data,
            numeric_col_names,
            method=method_literal,
            min_threshold=min_threshold,
        )
    else:
        correlations = []

    key_candidates = find_key_candidates(columns, summary.row_count)

    findings = evaluate_quality_rules(columns, duplicates, df=profiler.data)
    collinear_findings = evaluate_collinear_findings(correlations)
    findings.extend(collinear_findings)

    warnings = [
        f"[{f.severity.upper()}] {f.title}: {f.description}"
        for f in findings
        if f.severity in ("warning", "critical")
    ]

    return AnalysisReport(
        schema_version="1.0.0",
        metadata=metadata,
        summary=summary,
        duplicates=duplicates,
        missing_values=missing_values,
        columns=columns,
        findings=findings,
        warnings=warnings,
        correlations=correlations,
        key_candidates=key_candidates,
    )
