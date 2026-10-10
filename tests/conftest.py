# =============================================================================
# DataPulse Test Suite Fixtures (conftest.py)
# =============================================================================
# Canonical, multi-column realistic test fixtures representing complex
# real-world data distributions (continuous, discrete, float IDs, booleans,
# temporal pairs, diverse missingness tokens, outliers, and duplicates).
# =============================================================================

from datetime import datetime, timedelta
from pathlib import Path

import polars as pl
import pytest


@pytest.fixture
def realistic_tabular_df() -> pl.DataFrame:
    """Generate a realistic 50-row DataFrame with multifaceted data patterns:
    - Continuous numeric measurements (including negatives and tail outliers)
    - Discrete coded integers (low-cardinality codes)
    - Float identifiers (1001.0 .. 1050.0)
    - High-cardinality unique integer IDs
    - Low-cardinality categorical strings
    - Native Boolean flags and integer binary indicators (0/1)
    - Free-form text descriptions
    - Paired temporal timestamps (with an intentional chronological inversion)
    - Unified missingness (nulls, NaNs, empty strings, whitespace, sentinels)
    - Exact duplicate rows
    - All-constant column
    """
    row_count = 48  # plus 2 duplicates makes 50 rows
    base_time = datetime(2025, 1, 1, 10, 0, 0)

    # Base records
    ids = list(range(1, row_count + 1))
    float_ids = [float(1000 + i) for i in ids]

    # Amounts: mostly positive (10.0 to 300.0), two negative values, two extreme outliers
    amounts = [15.0 + (i * 4.5) for i in range(row_count)]
    amounts[5] = -25.5
    amounts[12] = -10.0
    amounts[25] = 4500.0  # Tukey outlier
    amounts[38] = 7200.0  # Tukey outlier

    # Coded integer: values 1, 2, 3
    payment_types = [(i % 3) + 1 for i in range(row_count)]

    # Categorical: low cardinality
    categories = [
        ["Electronics", "Apparel", "Home", "Books"][i % 4] for i in range(row_count)
    ]

    # Booleans: native and 0/1 int
    is_active = [(i % 2 == 0) for i in range(row_count)]
    flag_int = [1 if i % 2 == 0 else 0 for i in range(row_count)]

    # Free text
    descriptions = [
        f"Order #{i} processed standard shipment express handling verified."
        for i in range(row_count)
    ]

    # Temporal pairs: order_start -> order_end (row 7 has order_end < order_start)
    order_start = [base_time + timedelta(hours=i) for i in range(row_count)]
    order_end = [base_time + timedelta(hours=i, minutes=45) for i in range(row_count)]
    order_end[7] = order_start[7] - timedelta(hours=2)  # Inverted chronology

    # Unified missingness column
    mixed_missing: list[str | None] = ["Valid" for _ in range(row_count)]
    mixed_missing[2] = None  # Native Polars null
    mixed_missing[4] = ""  # Empty string
    mixed_missing[6] = "   "  # Whitespace-only string
    mixed_missing[8] = "NA"  # Configurable sentinel
    mixed_missing[10] = "N/A"  # Configurable sentinel

    # Constant column
    constant_col = ["FIXED_VALUE" for _ in range(row_count)]

    data = {
        "id": ids,
        "float_id": float_ids,
        "amount": amounts,
        "payment_type": payment_types,
        "category": categories,
        "is_active": is_active,
        "flag_int": flag_int,
        "description": descriptions,
        "order_start": order_start,
        "order_end": order_end,
        "mixed_missing": mixed_missing,
        "constant_col": constant_col,
    }

    df = pl.DataFrame(data)

    # Append 2 duplicate rows (duplicate row 0 and row 1)
    dup_rows = df.slice(0, 2)
    return pl.concat([df, dup_rows])


@pytest.fixture
def realistic_csv_path(tmp_path: Path, realistic_tabular_df: pl.DataFrame) -> Path:
    """Write the realistic tabular dataset to a temporary CSV file."""
    csv_file = tmp_path / "realistic_data.csv"
    realistic_tabular_df.write_csv(csv_file)
    return csv_file


@pytest.fixture
def realistic_parquet_path(tmp_path: Path, realistic_tabular_df: pl.DataFrame) -> Path:
    """Write the realistic tabular dataset to a temporary Parquet file."""
    parquet_file = tmp_path / "realistic_data.parquet"
    realistic_tabular_df.write_parquet(parquet_file)
    return parquet_file


@pytest.fixture
def realistic_json_path(tmp_path: Path, realistic_tabular_df: pl.DataFrame) -> Path:
    """Write the realistic tabular dataset to a temporary JSON file."""
    json_file = tmp_path / "realistic_data.json"
    realistic_tabular_df.write_json(json_file)
    return json_file
