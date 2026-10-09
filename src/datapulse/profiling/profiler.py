from pathlib import Path

import polars as pl

from datapulse.analysis.column_classifier import classify_column
from datapulse.ingestion.readers import read_source


class DatasetProfiler:
    """Profile a tabular dataset using Polars."""

    def __init__(
        self,
        file_path: str | Path,
        *,
        sheet_name: str | None = None,
        separator: str | None = None,
    ) -> None:
        self.file_path = Path(file_path)
        self.lazy_data, self.source_info = read_source(
            self.file_path,
            sheet_name=sheet_name,
            separator=separator,
        )
        self.data = self.lazy_data.collect()

    def get_overview(self) -> dict:
        """Return basic dataset metadata."""

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

    def get_missing_values(self) -> pl.DataFrame:
        """Calculate missing-value counts and percentages."""

        total_rows = self.data.height
        null_counts = self.data.null_count()

        missing_summary = []

        for column in self.data.columns:
            null_count = null_counts[column][0]
            non_missing_count = total_rows - null_count

            missing_percentage = (
                (null_count / total_rows) * 100 if total_rows > 0 else 0.0
            )

            missing_summary.append(
                {
                    "column": column,
                    "null_count": null_count,
                    "non_missing_count": non_missing_count,
                    "missing_percentage": round(missing_percentage, 2),
                }
            )

        return pl.DataFrame(
            missing_summary,
            schema={
                "column": pl.String,
                "null_count": pl.UInt32,
                "non_missing_count": pl.UInt64,
                "missing_percentage": pl.Float64,
            },
        )

    def get_duplicate_summary(self) -> dict[str, int | float]:
        """Calculate duplicate-row counts and percentages."""

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

    def get_numeric_statistics(self) -> pl.DataFrame:
        """Calculate descriptive statistics for numeric columns."""

        numeric_columns = [
            name for name, dtype in self.data.schema.items() if dtype.is_numeric()
        ]

        if not numeric_columns:
            return pl.DataFrame()

        return self.data.select(numeric_columns).describe()

    def get_categorical_statistics(self) -> pl.DataFrame:
        """Summarize distinct values and cardinality for each column."""

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
        """Summarize date and datetime columns."""

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

    def get_column_quality(self) -> pl.DataFrame:
        """Summarize column types and basic data-quality metrics."""

        summaries = []
        total_rows = self.data.height

        for column, dtype in self.data.schema.items():
            series = self.data[column]
            null_count = series.null_count()
            non_null = series.drop_nulls()

            classification = classify_column(series, total_rows)
            category = classification.inferred_role

            missing_percentage = (
                null_count / total_rows * 100 if total_rows > 0 else 0.0
            )

            summaries.append(
                {
                    "column": column,
                    "data_type": str(dtype),
                    "category": category,
                    "null_count": null_count,
                    "missing_percentage": round(missing_percentage, 2),
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
                "missing_percentage": pl.Float64,
                "unique_count": pl.UInt32,
            },
        )
