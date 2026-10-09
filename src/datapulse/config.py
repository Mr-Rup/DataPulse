import json
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AnalysisConfig:
    """Configuration settings for dataset profiling."""

    max_categories: int = 20
    sample_size: int | None = None
    sample_method: str = "head"
    compute_correlations: bool = True
    correlation_method: str = "pearson"
    min_correlation: float = 0.50
    sheet_name: str | None = None
    separator: str | None = None


def load_config(config_path: str | Path) -> AnalysisConfig:
    """Load configuration from a JSON or TOML file."""

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    suffix = path.suffix.lower()
    content = path.read_text(encoding="utf-8")

    if suffix == ".json":
        data = json.loads(content)
    elif suffix in (".toml", ".tml"):
        data = tomllib.loads(content)
    else:
        raise ValueError(
            f"Unsupported configuration format '{suffix}'. "
            "Supported formats: .json, .toml"
        )

    # Allow nesting under a [datapulse] section
    if "datapulse" in data and isinstance(data["datapulse"], dict):
        data = data["datapulse"]

    valid_keys = {
        "max_categories",
        "sample_size",
        "sample_method",
        "compute_correlations",
        "correlation_method",
        "min_correlation",
        "sheet_name",
        "separator",
    }
    filtered = {k: v for k, v in data.items() if k in valid_keys}
    return AnalysisConfig(**filtered)
