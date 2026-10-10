# =========================================================================
# DataPulse Public API Pipeline
# High-level entry point orchestrating dataset ingestion, missingness
# analysis, column profiling, relationship discovery, and report generation.
# =========================================================================

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

# =========================================================================
# PUBLIC ANALYSIS PIPELINE
# =========================================================================

def analyze(
    file_path: str | Path,
    config: AnalysisConfig | None = None,
) -> AnalysisReport:
    """Analyze a tabular dataset and produce a fully populated AnalysisReport."""
    start_time = time.perf_counter()
    path = Path(file_path)

    # -------------------------------------------------------------------------
    # Dataset Profiling & Overview Extraction
    # -------------------------------------------------------------------------
    profiler = DatasetProfiler(
        path,
        sheet_name=config.sheet_name if config else None,
        separator=config.separator if config else None,
    )

    sentinels = config.missing_sentinels if config else None
    overview = profiler.get_overview()
    missing_df = profiler.get_missing_values(sentinels=sentinels)
    duplicate_dict = profiler.get_duplicate_summary()
    quality_df = profiler.get_column_quality(sentinels=sentinels)

    # -------------------------------------------------------------------------
    # Structural & Missingness Summaries
    # -------------------------------------------------------------------------
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
            column=str(row["column"]),
            null_count=int(row["null_count"]),
            nan_count=int(row["nan_count"]),
            empty_count=int(row["empty_count"]),
            sentinel_count=int(row["sentinel_count"]),
            total_missing_count=int(row["total_missing_count"]),
            non_missing_count=int(row["non_missing_count"]),
            missing_percentage=float(row["missing_percentage"]),
        )
        for row in missing_df.iter_rows(named=True)
    ]

    quality_map = {row["column"]: row for row in quality_df.iter_rows(named=True)}

    # -------------------------------------------------------------------------
    # Column Classification & Role-Specific Profiling
    # -------------------------------------------------------------------------
    column_roles = config.column_roles if config else None
    classifications = classify_columns(profiler.data, column_roles=column_roles)
    max_categories = config.max_categories if config else 20

    columns: list[ColumnProfile] = []
    for col_name, dtype_str in overview["schema"].items():
        q_info = quality_map.get(col_name, {})
        classification = classifications.get(col_name)
        role = (
            classification.inferred_role
            if classification
            else str(q_info.get("category", "unknown"))
        )
        conf = classification.confidence if classification else 1.0
        reason = classification.reason if classification else ""
        alt_roles = classification.alternative_roles if classification else []

        stats = profiler.profile_column(
            col_name,
            role=role,
            max_categories=max_categories,
            sentinels=sentinels,
        )

        profile = ColumnProfile(
            name=col_name,
            physical_type=dtype_str,
            inferred_role=role,
            confidence=conf,
            inference_reason=reason,
            alternative_roles=alt_roles,
            null_count=int(q_info.get("null_count", 0)),
            nan_count=int(q_info.get("nan_count", 0)),
            empty_count=int(q_info.get("empty_count", 0)),
            total_missing_count=int(q_info.get("total_missing_count", 0)),
            missing_percentage=float(q_info.get("missing_percentage", 0.0)),
            unique_count=int(q_info.get("unique_count", 0)),
            statistics=stats,
        )
        columns.append(profile)

    elapsed = round(time.perf_counter() - start_time, 4)
    inc_full_path = config.include_full_path if config else False
    src_path_str = str(path.resolve()) if inc_full_path else path.name

    metadata = ReportMetadata(
        datapulse_version=__version__,
        created_at=datetime.now(UTC).isoformat(),
        source_name=path.name,
        source_path=src_path_str,
        file_size_mb=summary.file_size_mb,
        elapsed_seconds=elapsed,
    )

    # -------------------------------------------------------------------------
    # Correlation & Primary Key Discovery
    # -------------------------------------------------------------------------
    compute_corr = config.compute_correlations if config else True
    if compute_corr:
        corr_method = config.correlation_method if config else "pearson"
        min_threshold = config.min_correlation if config else 0.50
        method_literal = "spearman" if corr_method == "spearman" else "pearson"
        numeric_col_names = [c.name for c in columns if c.inferred_role == "numeric"]
        max_corr_cols = config.max_correlation_columns if config else 30
        correlations = compute_correlations(
            profiler.data,
            numeric_col_names,
            method=method_literal,
            min_threshold=min_threshold,
            max_correlation_columns=max_corr_cols,
        )
    else:
        correlations = []

    key_candidates = find_key_candidates(columns, summary.row_count)

    # -------------------------------------------------------------------------
    # Quality Rules Evaluation & Report Assembly
    # -------------------------------------------------------------------------
    findings = evaluate_quality_rules(
        columns,
        duplicates,
        df=profiler.data,
        allowed_negative_columns=(
            config.allowed_negative_columns if config else None
        ),
        non_negative_columns=config.non_negative_columns if config else None,
    )
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
