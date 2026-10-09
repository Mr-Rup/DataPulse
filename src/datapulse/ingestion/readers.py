from dataclasses import dataclass
from pathlib import Path

import polars as pl

SUPPORTED_EXTENSIONS = {
    ".parquet": "parquet",
    ".csv": "csv",
    ".json": "json",
    ".ndjson": "json",
    ".jsonl": "json",
    ".xlsx": "excel",
    ".xls": "excel",
}


@dataclass(frozen=True)
class SourceInfo:
    """Metadata describing an ingested data source."""

    file_path: Path
    file_name: str
    file_format: str
    file_size_mb: float


def read_source(
    file_path: str | Path,
    *,
    sheet_name: str | None = None,
    separator: str | None = None,
) -> tuple[pl.LazyFrame, SourceInfo]:
    """Read a tabular dataset from disk as a Polars LazyFrame."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a regular file: {path}")

    size_bytes = path.stat().st_size
    if size_bytes == 0:
        raise ValueError(f"Dataset file is empty: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS.keys()))
        raise ValueError(
            f"Unsupported file format '{path.suffix}'. Supported formats: {supported}"
        )

    file_format = SUPPORTED_EXTENSIONS[suffix]
    file_size_mb = round(size_bytes / (1024 ** 2), 2)
    source_info = SourceInfo(
        file_path=path,
        file_name=path.name,
        file_format=file_format,
        file_size_mb=file_size_mb,
    )

    try:
        if file_format == "parquet":
            lazy_frame = pl.scan_parquet(path)
        elif file_format == "csv":
            sep = separator or ","
            lazy_frame = pl.scan_csv(path, separator=sep)
        elif file_format == "json":
            if suffix in (".ndjson", ".jsonl"):
                lazy_frame = pl.scan_ndjson(path)
            else:
                try:
                    lazy_frame = pl.read_json(path).lazy()
                except Exception:
                    lazy_frame = pl.scan_ndjson(path)
        elif file_format == "excel":
            if sheet_name is not None:
                lazy_frame = pl.read_excel(path, sheet_name=sheet_name).lazy()
            else:
                lazy_frame = pl.read_excel(path).lazy()
        else:
            raise ValueError(f"Unsupported format handler: {file_format}")

        # Quick validation of schema to catch malformed files early
        _ = lazy_frame.collect_schema()
        return lazy_frame, source_info

    except Exception as exc:
        if isinstance(exc, (FileNotFoundError, ValueError)):
            raise
        raise ValueError(
            f"Failed to read {file_format} file '{path.name}': {exc}"
        ) from exc
