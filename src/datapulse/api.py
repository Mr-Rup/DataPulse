import time
from datetime import UTC, datetime
from pathlib import Path

from datapulse import __version__
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
    )

    overview = profiler.get_overview()
    missing_df = profiler.get_missing_values()
    duplicate_dict = profiler.get_duplicate_summary()
    numeric_df = profiler.get_numeric_statistics()
    categorical_df = profiler.get_categorical_statistics()
    temporal_df = profiler.get_temporal_statistics()
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

    quality_map = {
        row["column"]: row
        for row in quality_df.iter_rows(named=True)
    }

    numeric_stats: dict[str, dict[str, float | None]] = {}
    if numeric_df.width > 0:
        for row in numeric_df.iter_rows(named=True):
            stat_name = str(row["statistic"])
            for col_name in numeric_df.columns:
                if col_name == "statistic":
                    continue
                if col_name not in numeric_stats:
                    numeric_stats[col_name] = {}
                raw_val = row[col_name]
                numeric_stats[col_name][stat_name] = (
                    float(raw_val) if raw_val is not None else None
                )

    categorical_stats: dict[str, dict[str, float | int]] = {}
    if categorical_df.height > 0:
        for row in categorical_df.iter_rows(named=True):
            col_name = row["column"]
            categorical_stats[col_name] = {
                "unique_count": int(row["unique_count"]),
                "cardinality_percentage": float(row["cardinality_percentage"]),
            }

    temporal_stats: dict[str, dict[str, str | int]] = {}
    if temporal_df.height > 0:
        for row in temporal_df.iter_rows(named=True):
            col_name = row["column"]
            temporal_stats[col_name] = {
                "minimum": str(row["minimum"]),
                "maximum": str(row["maximum"]),
                "unique_count": int(row["unique_count"]),
            }

    columns: list[ColumnProfile] = []
    for col_name, dtype_str in overview["schema"].items():
        q_info = quality_map.get(col_name, {})
        stats: dict[str, object] = {}

        if col_name in numeric_stats:
            stats.update(numeric_stats[col_name])
        if col_name in categorical_stats:
            stats.update(categorical_stats[col_name])
        if col_name in temporal_stats:
            stats.update(temporal_stats[col_name])

        profile = ColumnProfile(
            name=col_name,
            physical_type=dtype_str,
            inferred_role=q_info.get("category", "unknown"),
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

    return AnalysisReport(
        schema_version="1.0.0",
        metadata=metadata,
        summary=summary,
        duplicates=duplicates,
        missing_values=missing_values,
        columns=columns,
        findings=[],
        warnings=[],
    )
