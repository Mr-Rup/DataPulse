"""DataPulse: Automated tabular exploratory data analysis toolkit."""

__version__ = "0.2.0"

from datapulse.api import analyze
from datapulse.config import AnalysisConfig, load_config
from datapulse.exceptions import (
    ConfigurationError,
    DataPulseError,
    IngestionError,
    SchemaError,
    UnsupportedFormatError,
)
from datapulse.models.report import AnalysisReport
from datapulse.reporting import export_html, export_json

__all__ = [
    "AnalysisConfig",
    "AnalysisReport",
    "ConfigurationError",
    "DataPulseError",
    "IngestionError",
    "SchemaError",
    "UnsupportedFormatError",
    "analyze",
    "export_html",
    "export_json",
    "load_config",
    "__version__",
]
