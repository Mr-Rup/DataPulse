from dataclasses import dataclass


@dataclass
class AnalysisConfig:
    """Configuration settings for dataset profiling."""

    max_categories: int = 20
    sample_size: int | None = None
    sheet_name: str | None = None
    separator: str | None = None
