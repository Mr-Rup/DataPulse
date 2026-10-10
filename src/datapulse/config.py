# =========================================================================
# DataPulse Configuration Engine
# Strict Pydantic models for profiling hyperparameters, thresholds,
# missing sentinels, and configuration file parsers (JSON, TOML).
# =========================================================================

import json
import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# =========================================================================
# PROFILING CONFIGURATION MODEL
# =========================================================================

class AnalysisConfig(BaseModel):
    """Configuration settings for dataset profiling and quality evaluation."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    max_categories: int = Field(
        default=20,
        gt=0,
        description="Max top categories to profile in detail per column",
    )
    compute_correlations: bool = Field(
        default=True,
        description="Enable or disable pairwise correlation calculations",
    )
    correlation_method: Literal["pearson", "spearman"] = Field(
        default="pearson",
        description="Correlation calculation method",
    )
    min_correlation: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Minimum absolute correlation threshold to record",
    )
    max_correlation_columns: int = Field(
        default=30,
        gt=0,
        description="Maximum numeric columns evaluated in pairwise correlation matrix",
    )
    missing_sentinels: list[str] = Field(
        default_factory=lambda: [
            "NA",
            "N/A",
            "null",
            "NULL",
            "none",
            "NONE",
            "-999",
            "NaN",
            "nan",
        ],
        description="String values treated as missing data in text columns",
    )
    column_roles: dict[str, str] = Field(
        default_factory=dict,
        description="Explicit user overrides for column semantic roles",
    )
    allowed_negative_columns: list[str] = Field(
        default_factory=list,
        description="Columns allowed to have negative values without warnings",
    )
    non_negative_columns: list[str] | None = Field(
        default=None,
        description="Explicit columns strictly required to be non-negative",
    )
    sheet_name: str | None = Field(
        default=None,
        description="Sheet name to read when profiling Excel files",
    )
    separator: str | None = Field(
        default=None,
        description="Delimiter character for CSV files",
    )
    include_full_path: bool = Field(
        default=False,
        description="Whether to include absolute file path in report metadata",
    )


# =========================================================================
# CONFIGURATION FILE LOADER
# =========================================================================

def load_config(config_path: str | Path) -> AnalysisConfig:
    """Load configuration from a JSON or TOML file with validation."""
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

    # Allow nesting under an optional [datapulse] section
    if "datapulse" in data and isinstance(data["datapulse"], dict):
        data = data["datapulse"]

    return AnalysisConfig.model_validate(data)
