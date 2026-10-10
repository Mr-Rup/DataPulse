# =========================================================================
# DataPulse Public API Pipeline
# High-level entry point orchestrating dataset ingestion, missingness
# analysis, column profiling, relationship discovery, and report generation.
# =========================================================================

import time
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from datapulse import __version__
from datapulse.analysis.column_classifier import classify_columns
from datapulse.analysis.quality_rules import evaluate_quality_rules
from datapulse.analysis.relationships import (
    compute_correlations,
    evaluate_collinear_findings,
    find_key_candidates,
)
from datapulse.config import AnalysisConfig, load_config
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
    file_path: str | Path | pl.DataFrame | pl.LazyFrame,
    config: AnalysisConfig | str | Path | None = None,
) -> AnalysisReport:
    """Analyze a tabular dataset and produce a fully populated AnalysisReport."""
    start_time = time.perf_counter()
    # Resolve configuration options from object, file path, or defaults
    if config is None:
        cfg = AnalysisConfig()
    elif isinstance(config, (str, Path)):
        cfg = load_config(config)
    elif isinstance(config, AnalysisConfig):
        cfg = config
    else:
        raise TypeError(
            f"Invalid config type '{type(config).__name__}'. "
            "Expected AnalysisConfig, str, Path, or None."
        )
    # Determine source display name and resolution path
    if isinstance(file_path, (str, Path)):
        src_path = Path(file_path)
        source_name = src_path.name
        source_path_str = (
            str(src_path.resolve()) if cfg.include_full_path else src_path.name
        )
    else:
        source_name = "in_memory_dataframe"
        source_path_str = "memory"
    # Execute single-pass parallel profiling
    profiler = DatasetProfiler(
        file_path,
        sheet_name=cfg.sheet_name,
        separator=cfg.separator,
    )
    sentinels = cfg.missing_sentinels
    overview = profiler.get_overview()
    missing_df = profiler.get_missing_values(sentinels=sentinels)
    duplicate_dict = profiler.get_duplicate_summary()
    quality_df = profiler.get_column_quality(sentinels=sentinels)
    # Structural & Missingness Summaries
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

    # Column Classification & Role-Specific Profiling
    column_roles = cfg.column_roles
    classifications = classify_columns(profiler.data, column_roles=column_roles)
    max_categories = cfg.max_categories
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
    metadata = ReportMetadata(
        datapulse_version=__version__,
        created_at=datetime.now(UTC).isoformat(),
        source_name=source_name,
        source_path=source_path_str,
        file_size_mb=summary.file_size_mb,
        elapsed_seconds=elapsed,
    )
    # Correlation & Primary Key Discovery
    compute_corr = cfg.compute_correlations
    if compute_corr:
        corr_method = cfg.correlation_method
        min_threshold = cfg.min_correlation
        method_literal = "spearman" if corr_method == "spearman" else "pearson"
        numeric_col_names = [c.name for c in columns if c.inferred_role == "numeric"]
        max_corr_cols = cfg.max_correlation_columns
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
    # Quality Rules Evaluation & Report Assembly
    findings = evaluate_quality_rules(
        columns,
        duplicates,
        df=profiler.data,
        allowed_negative_columns=cfg.allowed_negative_columns,
        non_negative_columns=cfg.non_negative_columns,
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
