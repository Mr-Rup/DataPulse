# =========================================================================
# DataPulse Column Classification Models
# Data structures representing inferred analytical roles and confidence.
# =========================================================================

from dataclasses import dataclass, field

# =========================================================================
# DATA STRUCTURES
# =========================================================================

@dataclass(frozen=True)
class ColumnClassification:
    """Analytical classification of a dataset column."""

    name: str
    physical_type: str
    inferred_role: str
    confidence: float
    reason: str
    alternative_roles: list[str] = field(default_factory=list)
