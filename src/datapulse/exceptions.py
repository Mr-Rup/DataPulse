# =========================================================================
# DataPulse Exception Hierarchy
# Strongly-typed domain exceptions for ingestion, schema, and configuration.
# Subclasses inherit from ValueError/TypeError for 100% backward compatibility.
# =========================================================================

# =========================================================================
# BASE EXCEPTION DEFINITION
# =========================================================================

class DataPulseError(Exception):
    """Base exception for all errors raised by the DataPulse toolkit."""


# =========================================================================
# DOMAIN-SPECIFIC EXCEPTION SUBCLASSES
# =========================================================================

class IngestionError(DataPulseError, ValueError):
    """Raised when dataset ingestion, format sniffing, or parsing fails."""


class UnsupportedFormatError(IngestionError):
    """Raised when an unrecognized or unsupported file extension is encountered."""


class ConfigurationError(DataPulseError, ValueError):
    """Raised when an invalid configuration file, schema, or option is provided."""


class SchemaError(DataPulseError, ValueError):
    """Raised when dataset schema, column resolution, or query evaluation fails."""
