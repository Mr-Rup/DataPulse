"""DataPulse: Automated tabular exploratory data analysis toolkit."""

__version__ = "0.1.0"

from datapulse.api import analyze
from datapulse.config import AnalysisConfig
from datapulse.models.report import AnalysisReport

__all__ = [
    "AnalysisConfig",
    "AnalysisReport",
    "analyze",
    "__version__",
]
