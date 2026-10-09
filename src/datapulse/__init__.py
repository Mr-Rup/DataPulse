"""DataPulse: Automated tabular exploratory data analysis toolkit."""

__version__ = "0.1.0"

from datapulse.api import analyze
from datapulse.config import AnalysisConfig
from datapulse.models.report import AnalysisReport
from datapulse.reporting import export_html, export_json

__all__ = [
    "AnalysisConfig",
    "AnalysisReport",
    "analyze",
    "export_html",
    "export_json",
    "__version__",
]
