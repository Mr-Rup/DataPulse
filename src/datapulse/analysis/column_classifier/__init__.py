# =========================================================================
# DataPulse Column Classifier Package
# Inference engine classifying physical Polars types into analytical roles.
# =========================================================================

from datapulse.analysis.column_classifier.engine import (
    classify_column,
    classify_columns,
)
from datapulse.analysis.column_classifier.hints import (
    CODE_NAME_HINTS,
    ID_SUFFIX_HINTS,
    METRIC_NAME_HINTS,
)
from datapulse.analysis.column_classifier.models import ColumnClassification

__all__ = [
    "CODE_NAME_HINTS",
    "ID_SUFFIX_HINTS",
    "METRIC_NAME_HINTS",
    "ColumnClassification",
    "classify_column",
    "classify_columns",
]
