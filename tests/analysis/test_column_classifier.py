# =============================================================================
# Unit & Scenario Tests: Column Classification
# =============================================================================

from datetime import datetime

import polars as pl

from datapulse.analysis.column_classifier import (
    classify_column,
    classify_columns,
)

# =============================================================================
# 1. PHYSICAL & INVARIANT CLASSIFICATION
# =============================================================================


class TestPhysicalAndInvariantClassification:
    """Validate physical data types and invariant columns (nulls, constants, booleans)."""

    def test_trivial_and_primitive_types(self):
        # All null series
        null_series = pl.Series("empty_col", [None, None, None], dtype=pl.String)
        res_null = classify_column(null_series, 3)
        assert res_null.inferred_role == "other"

        # Constant series
        const_series = pl.Series("status", ["active", "active", "active"])
        res_const = classify_column(const_series, 3)
        assert res_const.inferred_role == "constant"
        assert res_const.confidence == 1.0

        # Physical boolean series
        bool_series = pl.Series("is_member", [True, False, True])
        res_bool = classify_column(bool_series, 3)
        assert res_bool.inferred_role == "boolean"
        assert res_bool.confidence == 1.0

        # Temporal Datetime series
        date_series = pl.Series(
            "created_at",
            [datetime(2025, 1, 1), datetime(2025, 1, 2)],
            dtype=pl.Datetime,
        )
        res_date = classify_column(date_series, 2)
        assert res_date.inferred_role == "temporal"
        assert res_date.confidence == 1.0


# =============================================================================
# 2. SEMANTIC CLASSIFICATION ON REALISTIC DATA
# =============================================================================


class TestSemanticClassification:
    """Validate heuristic role inference on realistic multifaceted dataset columns."""

    def test_realistic_dataset_column_inference(
        self, realistic_tabular_df: pl.DataFrame
    ):
        total_rows = len(realistic_tabular_df)

        # Continuous numeric amount
        res_amt = classify_column(realistic_tabular_df["amount"], total_rows)
        assert res_amt.inferred_role == "numeric"
        assert "continuous" in res_amt.alternative_roles

        # Discrete coded integer (payment_type: 1, 2, 3)
        res_code = classify_column(realistic_tabular_df["payment_type"], total_rows)
        assert res_code.inferred_role == "categorical"
        assert "Low-cardinality" in res_code.reason or "code" in res_code.reason

        # Float identifier (float_id: 1001.0 .. 1050.0)
        res_fid = classify_column(realistic_tabular_df["float_id"], total_rows)
        assert res_fid.inferred_role == "identifier"
        assert "numeric" in res_fid.alternative_roles

        # Unique integer identifier (id: 1..50)
        res_id = classify_column(realistic_tabular_df["id"], total_rows)
        assert res_id.inferred_role == "identifier"

        # Free-form text descriptions
        res_text = classify_column(realistic_tabular_df["description"], total_rows)
        assert res_text.inferred_role == "text"

        # Low-cardinality string categories
        res_cat = classify_column(realistic_tabular_df["category"], total_rows)
        assert res_cat.inferred_role == "categorical"

        # Constant column
        res_cst = classify_column(realistic_tabular_df["constant_col"], total_rows)
        assert res_cst.inferred_role == "constant"


# =============================================================================
# 3. OVERRIDES & BATCH DATAFRAME INFERENCE
# =============================================================================


class TestClassificationOverridesAndBatch:
    """Validate user configuration overrides and full DataFrame batch classification."""

    def test_user_role_overrides_take_precedence(self):
        df = pl.DataFrame({"user_id": [101, 102, 103], "fare": [10.5, 20.0, 15.25]})
        overrides = {"user_id": "categorical", "fare": "text"}
        results = classify_columns(df, column_roles=overrides)

        assert results["user_id"].inferred_role == "categorical"
        assert results["user_id"].confidence == 1.0
        assert "User-specified override" in results["user_id"].reason

        assert results["fare"].inferred_role == "text"
        assert results["fare"].confidence == 1.0

    def test_batch_classification_dataframe(self, realistic_tabular_df: pl.DataFrame):
        classifications = classify_columns(realistic_tabular_df)

        assert classifications["amount"].inferred_role == "numeric"
        assert classifications["category"].inferred_role == "categorical"
        assert classifications["is_active"].inferred_role == "boolean"
        assert classifications["description"].inferred_role == "text"
        assert classifications["order_start"].inferred_role == "temporal"
