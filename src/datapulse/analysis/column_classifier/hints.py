# =========================================================================
# DataPulse Column Classifier Naming Hints
# Substrings, suffixes, and token patterns used to infer semantic roles.
# =========================================================================

# Naming suffixes and tokens commonly indicating primary/foreign keys or codes
ID_SUFFIX_HINTS: tuple[str, ...] = (
    "_id",
    "id",
    "_key",
    "key",
    "code",
)

# Semantic substrings in column names indicating continuous metric measurements
METRIC_NAME_HINTS: tuple[str, ...] = (
    "fare",
    "amount",
    "price",
    "cost",
    "total",
    "fee",
    "tip",
    "units",
    "revenue",
    "count",
    "qty",
    "quantity",
    "val",
    "score",
    "temp",
    "speed",
    "distance",
    "rate",
    "pct",
    "percent",
)

# Semantic substrings in column names indicating discrete status or classification
CODE_NAME_HINTS: tuple[str, ...] = (
    "type",
    "status",
    "mode",
    "class",
    "group",
    "category",
)
