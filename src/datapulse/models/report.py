import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ReportMetadata:
    """Metadata describing the profiling run."""

    datapulse_version: str
    created_at: str
    source_name: str
    source_path: str
    file_size_mb: float
    elapsed_seconds: float


@dataclass
class DatasetSummary:
    """High-level summary of dataset dimensions and schema."""

    file_name: str
    file_size_mb: float
    row_count: int
    column_count: int
    schema: dict[str, str]


@dataclass
class DuplicateSummary:
    """Summary of duplicate rows within the dataset."""

    total_rows: int
    unique_rows: int
    duplicate_rows: int
    duplicate_percentage: float


@dataclass
class MissingSummary:
    """Missing value breakdown for an individual column."""

    column: str
    null_count: int
    non_missing_count: int
    missing_percentage: float


@dataclass
class ColumnProfile:
    """Statistical profile and metadata for a single column."""

    name: str
    physical_type: str
    inferred_role: str = "unknown"
    confidence: float = 1.0
    inference_reason: str = ""
    null_count: int = 0
    missing_percentage: float = 0.0
    unique_count: int = 0
    statistics: dict[str, Any] = field(default_factory=dict)


@dataclass
class Finding:
    """An observed data quality finding or anomaly."""

    rule_id: str
    severity: str
    title: str
    description: str
    affected_columns: list[str] = field(default_factory=list)
    affected_rows: int = 0
    affected_percentage: float = 0.0


@dataclass
class AnalysisReport:
    """Structured report produced by DataPulse."""

    schema_version: str
    metadata: ReportMetadata
    summary: DatasetSummary
    duplicates: DuplicateSummary
    missing_values: list[MissingSummary] = field(default_factory=list)
    columns: list[ColumnProfile] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert the report to a dictionary representation."""

        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize the report to a JSON string."""

        return json.dumps(self.to_dict(), indent=indent)
