# =========================================================================
# DataPulse Quality Rules Domain Constants
# Static keywords, pre-defined chronology pairs, and temporal suffixes.
# =========================================================================

# Substrings commonly associated with quantities that cannot physically be negative
NON_NEGATIVE_KEYWORDS: tuple[str, ...] = (
    "fare",
    "amount",
    "distance",
    "price",
    "cost",
    "count",
    "passenger",
    "trip",
    "duration",
    "age",
    "qty",
    "quantity",
    "length",
    "width",
    "height",
    "weight",
    "volume",
    "speed",
    "fee",
    "tip",
    "toll",
)

# Standard predefined pairs of start-and-end event timestamps
CHRONOLOGY_PAIRS: tuple[tuple[str, str], ...] = (
    ("tpep_pickup_datetime", "tpep_dropoff_datetime"),
    ("pickup_datetime", "dropoff_datetime"),
    ("started_at", "ended_at"),
    ("start_time", "end_time"),
    ("start_date", "end_date"),
    ("created_at", "updated_at"),
    ("valid_from", "valid_to"),
    ("departure_time", "arrival_time"),
)

# Dynamic suffix pairings used to automatically discover paired temporal columns
DYNAMIC_TEMPORAL_SUFFIX_PAIRS: tuple[tuple[str, str], ...] = (
    ("_start", "_end"),
    ("_begin", "_finish"),
    ("_pickup", "_dropoff"),
    ("_opened", "_closed"),
    ("_created", "_updated"),
    ("_dispatched", "_received"),
    ("_departure", "_arrival"),
    ("_in", "_out"),
)
