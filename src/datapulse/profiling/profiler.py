# =========================================================================
# DataPulse Dataset Profiler Engine
# High-performance Polars profiler aggregating missingness breakdowns,
# duplicate summaries, and schema quality metrics in single parallel passes.
# =========================================================================

from pathlib import Path

import polars as pl

from datapulse.analysis.column_classifier import classify_column
from datapulse.ingestion.readers import read_source
from datapulse.profiling.column_profiler import profile_column as calc_column_stats

# =========================================================================
# DATASET PROFILER CLASS DEFINITION
# =========================================================================

class DatasetProfiler:
    """Profile a tabular dataset using Polars with parallel aggregate expressions."""

    # -------------------------------------------------------------------------
    # Ingestion & Initialization
    # -------------------------------------------------------------------------

    def __init__(
        self,
        file_path: str | Path,
        *,
        sheet_name: str | None = None,
        separator: str | None = None,
    ) -> None:
        """Initialize profiler by lazily reading dataset and collecting to memory."""
        self.file_path = Path(file_path)
        self.lazy_data, self.source_info = read_source(
            self.file_path,
            sheet_name=sheet_name,
            separator=separator,
        )
        self.data = self.lazy_data.collect()

    # -------------------------------------------------------------------------
    # Dataset Overview & Metadata
    # -------------------------------------------------------------------------

    def get_overview(self) -> dict:
        """Return basic dataset metadata and column data types."""
        return {
            "file_name": self.source_info.file_name,
            "file_size_mb": self.source_info.file_size_mb,
            "row_count": self.data.height,
            "column_count": self.data.width,
            "columns": self.data.columns,
            "schema": {
                column: str(dtype) for column, dtype in self.data.schema.items()
            },
        }

    # -------------------------------------------------------------------------
    # Unified Missingness & Sentinel Accounting
    # -------------------------------------------------------------------------

    def get_missing_values(
        self,
        sentinels: list[str] | None = None,
    ) -> pl.DataFrame:
        """Calculate complete missingness: nulls, NaNs, empty strings, sentinels."""
        total_rows = self.data.height
        if total_rows == 0:
            return pl.DataFrame(
                schema={
                    "column": pl.String,
                    "null_count": pl.UInt32,
                    "nan_count": pl.UInt32,
                    "empty_count": pl.UInt32,
                    "sentinel_count": pl.UInt32,
                    "total_missing_count": pl.UInt32,
                    "non_missing_count": pl.UInt64,
                    "missing_percentage": pl.Float64,
                }
            )

        # Build batched aggregate expressions for a single parallel scan pass
        exprs: list[pl.Expr] = []
        for col in self.data.columns:
            dtype = self.data.schema[col]
            exprs.append(pl.col(col).null_count().alias(f"null__{col}"))
            if dtype.is_float():
                exprs.append(pl.col(col).is_nan().sum().alias(f"nan__{col}"))
            if dtype == pl.String:
                exprs.append(
                    (pl.col(col).str.strip_chars() == "")
                    .sum()
                    .alias(f"empty__{col}")
                )
                if sentinels:
                    exprs.append(
                        pl.col(col).is_in(sentinels).sum().alias(f"sentinel__{col}")
                    )

        agg_result = self.data.select(exprs).to_dicts()[0]

        missing_summary = []
        for col in self.data.columns:
            dtype = self.data.schema[col]
            null_count = int(agg_result.get(f"null__{col}", 0) or 0)
            nan_count = (
                int(agg_result.get(f"nan__{col}", 0) or 0)
                if dtype.is_float()
                else 0
            )
            empty_count = (
                int(agg_result.get(f"empty__{col}", 0) or 0)
                if dtype == pl.String
                else 0
            )
            sentinel_count = (
                int(agg_result.get(f"sentinel__{col}", 0) or 0)
                if (dtype == pl.String and sentinels)
                else 0
            )

            total_missing = null_count + nan_count + empty_count + sentinel_count
            non_missing = max(0, total_rows - total_missing)
            missing_pct = (total_missing / total_rows) * 100.0

            missing_summary.append(
                {
                    "column": col,
                    "null_count": null_count,
                    "nan_count": nan_count,
                    "empty_count": empty_count,
                    "sentinel_count": sentinel_count,
                    "total_missing_count": total_missing,
                    "non_missing_count": non_missing,
                    "missing_percentage": round(missing_pct, 2),
                }
            )

        return pl.DataFrame(
            missing_summary,
            schema={
                "column": pl.String,
                "null_count": pl.UInt32,
                "nan_count": pl.UInt32,
                "empty_count": pl.UInt32,
                "sentinel_count": pl.UInt32,
                "total_missing_count": pl.UInt32,
                "non_missing_count": pl.UInt64,
                "missing_percentage": pl.Float64,
            },
        )

    # -------------------------------------------------------------------------
    # Duplicate Rows Analysis
    # -------------------------------------------------------------------------

    def get_duplicate_summary(self) -> dict[str, int | float]:
        """Calculate complete duplicate-row counts and percentages."""
        total_rows = self.data.height
        unique_rows = self.data.n_unique()
        duplicate_rows = total_rows - unique_rows
        duplicate_percentage = (
            (duplicate_rows / total_rows) * 100 if total_rows > 0 else 0.0
        )
        return {
            "total_rows": total_rows,
            "unique_rows": unique_rows,
            "duplicate_rows": duplicate_rows,
            "duplicate_percentage": round(duplicate_percentage, 2),
        }

    # -------------------------------------------------------------------------
    # Role-Specific Aggregations
    # -------------------------------------------------------------------------

    def get_numeric_statistics(self) -> pl.DataFrame:
        """Calculate descriptive statistics for numeric columns via describe()."""
        numeric_columns = [
            name for name, dtype in self.data.schema.items() if dtype.is_numeric()
        ]
        if not numeric_columns:
            return pl.DataFrame()
        return self.data.select(numeric_columns).describe()

    def get_categorical_statistics(self) -> pl.DataFrame:
        """Summarize distinct counts and cardinality for categorical columns."""
        categorical_columns = [
            name
            for name, dtype in self.data.schema.items()
            if dtype == pl.String or dtype == pl.Categorical or dtype == pl.Enum
        ]
        if not categorical_columns:
            return pl.DataFrame(
                schema={
                    "column": pl.String,
                    "unique_count": pl.UInt32,
                    "cardinality_percentage": pl.Float64,
                }
            )

        total_rows = self.data.height
        summaries = []
        for column in categorical_columns:
            unique_count = self.data[column].n_unique()
            cardinality_percentage = (
                (unique_count / total_rows) * 100 if total_rows > 0 else 0.0
            )
            summaries.append(
                {
                    "column": column,
                    "unique_count": unique_count,
                    "cardinality_percentage": round(cardinality_percentage, 2),
                }
            )
        return pl.DataFrame(summaries)

    def get_temporal_statistics(self) -> pl.DataFrame:
        """Summarize boundary ranges and distinct counts for temporal columns."""
        temporal_columns = [
            name for name, dtype in self.data.schema.items() if dtype.is_temporal()
        ]
        schema = {
            "column": pl.String,
            "minimum": pl.String,
            "maximum": pl.String,
            "unique_count": pl.UInt32,
        }
        if not temporal_columns:
            return pl.DataFrame(schema=schema)

        summaries = []
        for column in temporal_columns:
            series = self.data[column]
            minimum = series.min()
            maximum = series.max()
            summaries.append(
                {
                    "column": column,
                    "minimum": str(minimum) if minimum is not None else "N/A",
                    "maximum": str(maximum) if maximum is not None else "N/A",
                    "unique_count": series.drop_nulls().n_unique(),
                }
            )
        return pl.DataFrame(summaries, schema=schema)

    # -------------------------------------------------------------------------
    # Column Quality & Profiler Dispatch
    # -------------------------------------------------------------------------

    def get_column_quality(
        self,
        sentinels: list[str] | None = None,
    ) -> pl.DataFrame:
        """Summarize column physical types, inferred roles, and missingness."""
        missing_df = self.get_missing_values(sentinels=sentinels)
        missing_map = {row["column"]: row for row in missing_df.iter_rows(named=True)}

        summaries = []
        total_rows = self.data.height

        for column, dtype in self.data.schema.items():
            series = self.data[column]
            m_info = missing_map.get(column, {})
            null_count = int(m_info.get("null_count", 0))
            nan_count = int(m_info.get("nan_count", 0))
            empty_count = int(m_info.get("empty_count", 0))
            sentinel_count = int(m_info.get("sentinel_count", 0))
            total_missing = int(m_info.get("total_missing_count", 0))
            missing_pct = float(m_info.get("missing_percentage", 0.0))

            non_null = series.drop_nulls()
            classification = classify_column(series, total_rows)
            category = classification.inferred_role

            summaries.append(
                {
                    "column": column,
                    "data_type": str(dtype),
                    "category": category,
                    "null_count": null_count,
                    "nan_count": nan_count,
                    "empty_count": empty_count,
                    "sentinel_count": sentinel_count,
                    "total_missing_count": total_missing,
                    "missing_percentage": missing_pct,
                    "unique_count": non_null.n_unique(),
                }
            )

        return pl.DataFrame(
            summaries,
            schema={
                "column": pl.String,
                "data_type": pl.String,
                "category": pl.String,
                "null_count": pl.UInt32,
                "nan_count": pl.UInt32,
                "empty_count": pl.UInt32,
                "sentinel_count": pl.UInt32,
                "total_missing_count": pl.UInt32,
                "missing_percentage": pl.Float64,
                "unique_count": pl.UInt32,
            },
        )

    def profile_column(
        self,
        column: str,
        role: str | None = None,
        max_categories: int = 20,
        sentinels: list[str] | None = None,
    ) -> dict[str, object]:
        """Profile a column using role-specific descriptive statistics dispatch."""
        series = self.data[column]
        total_rows = self.data.height

        if role is None:
            classification = classify_column(series, total_rows)
            role = classification.inferred_role

        return calc_column_stats(
            series,
            total_rows,
            role,
            max_categories=max_categories,
            sentinels=sentinels,
        )
