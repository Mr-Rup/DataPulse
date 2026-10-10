from dataclasses import dataclass
from pathlib import Path

import polars as pl

SUPPORTED_EXTENSIONS = {
    ".parquet": "parquet",
    ".csv": "csv",
    ".tsv": "csv",
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


def _sniff_csv_properties(
    path: Path, user_sep: str | None = None
) -> tuple[str, str]:
    """Sniff line terminator and field delimiter from leading bytes of a
    CSV/TSV file.
    """

    with open(path, "rb") as f:
        sample_bytes = f.read(65536)

    stripped = sample_bytes.strip()
    if not stripped:
        raise ValueError(f"Dataset file contains no data: {path}")

    # 1. Line terminator (eol_char):
    # If \r is present and NO \n is present in sample, it uses classic CR (\r).
    # Otherwise default to \n (Polars handles both LF and CRLF with \n).
    if b"\r" in sample_bytes and b"\n" not in sample_bytes:
        eol_char = "\r"
    else:
        eol_char = "\n"

    # 2. Field separator:
    if user_sep is not None:
        return user_sep, eol_char

    if path.suffix.lower() == ".tsv":
        return "\t", eol_char

    try:
        sample_text = sample_bytes.decode("utf-8")
    except UnicodeDecodeError:
        sample_text = sample_bytes.decode("latin-1", errors="replace")

    lines = [line.strip() for line in sample_text.split(eol_char) if line.strip()]
    if not lines:
        return ",", eol_char

    candidates = [",", "\t", ";", "|"]
    best_sep = ","
    best_score = -1

    first_few = lines[:5]
    for cand in candidates:
        counts = [line.count(cand) for line in first_few]
        if counts[0] > 0:
            if len(counts) > 1 and all(c == counts[0] for c in counts):
                score = counts[0] * 100
            elif all(c > 0 for c in counts):
                score = counts[0] * 10
            else:
                score = counts[0]
            if score > best_score:
                best_score = score
                best_sep = cand

    return best_sep, eol_char


def _sniff_json_format(path: Path) -> str:
    """Inspect leading bytes to determine whether a JSON file is standard
    JSON or NDJSON.
    """

    with open(path, "rb") as f:
        chunk = f.read(4096).strip()
        if not chunk:
            raise ValueError(f"Dataset file contains no data: {path}")

        first_char = chr(chunk[0])
        if first_char == "[":
            return "json"
        if first_char == "{":
            lines = chunk.splitlines()
            if len(lines) > 1 and lines[1].strip().startswith(b"{"):
                return "ndjson"
            return "json"

        raise ValueError(
            f"Invalid JSON structure in '{path.name}': "
            f"must begin with '[' or '{{', found '{first_char}'."
        )


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
    file_size_mb = round(size_bytes / (1024**2), 2)
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
            sep, eol = _sniff_csv_properties(path, user_sep=separator)
            lazy_frame = pl.scan_csv(
                path,
                separator=sep,
                eol_char=eol,
                infer_schema_length=10000,
                encoding="utf8-lossy",
                truncate_ragged_lines=True,
            )
        elif file_format == "json":
            if suffix in (".ndjson", ".jsonl"):
                lazy_frame = pl.scan_ndjson(path)
            else:
                json_type = _sniff_json_format(path)
                if json_type == "json":
                    try:
                        lazy_frame = pl.read_json(path).lazy()
                    except Exception as json_err:
                        try:
                            lazy_frame = pl.scan_ndjson(path)
                            _ = lazy_frame.collect_schema()
                        except Exception:
                            raise ValueError(
                                f"Failed to parse JSON file '{path.name}': {json_err}"
                            ) from json_err
                else:
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
