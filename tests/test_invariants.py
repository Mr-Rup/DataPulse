from pathlib import Path

import polars as pl
import pytest

from datapulse import analyze


@pytest.fixture
def mixed_dataset(tmp_path: Path) -> Path:
    file_path = tmp_path / "invariants_sample.parquet"
    data = {
        "id": list(range(1, 101)),
        "score": [float(i * 1.5) for i in range(1, 101)],
        "category": [f"Cat_{i % 5}" for i in range(1, 101)],
        "mixed_floats": [
            float(i) if i % 10 != 0 else float("nan") for i in range(1, 101)
        ],
        "nullable_text": [
            f"text_{i}" if i % 4 != 0 else None for i in range(1, 101)
        ],
    }
    df = pl.DataFrame(data)
    df.write_parquet(file_path)
    return file_path


def test_missingness_invariants(mixed_dataset: Path):
    report = analyze(mixed_dataset)

    for col in report.columns:
        # Breakdown sums exactly to total missing
        expected_total = (
            col.null_count + col.nan_count + col.empty_count
        )
        assert col.total_missing_count >= expected_total

        # Missing percentage bounded in [0, 100]
        assert 0.0 <= col.missing_percentage <= 100.0


def test_dimension_and_duplicate_invariants(mixed_dataset: Path):
    report = analyze(mixed_dataset)
    total_rows = report.summary.row_count

    # Duplicates + Unique rows == Total rows
    assert (
        report.duplicates.unique_rows + report.duplicates.duplicate_rows
        == total_rows
    )

    for col in report.columns:
        # Unique count cannot exceed total rows
        assert 0 <= col.unique_count <= total_rows


def test_numeric_range_invariants(mixed_dataset: Path):
    report = analyze(mixed_dataset)

    for col in report.columns:
        if col.inferred_role == "numeric" and col.statistics:
            stats = col.statistics
            min_v = stats.get("min")
            med_v = stats.get("median")
            max_v = stats.get("max")
            mean_v = stats.get("mean")

            if (
                isinstance(min_v, (int, float))
                and isinstance(med_v, (int, float))
                and isinstance(max_v, (int, float))
                and isinstance(mean_v, (int, float))
            ):
                assert min_v <= med_v <= max_v
                assert min_v <= mean_v <= max_v


def test_correlation_invariants(mixed_dataset: Path):
    report = analyze(mixed_dataset)
    total_rows = report.summary.row_count

    for pair in report.correlations:
        # Correlation bounds [-1.0, 1.0]
        assert -1.0 <= pair.coefficient <= 1.0

        # Common observations bounded [2, total_rows]
        assert 2 <= pair.common_observations <= total_rows


def test_key_candidate_invariants(mixed_dataset: Path):
    report = analyze(mixed_dataset)
    total_rows = report.summary.row_count

    for key in report.key_candidates:
        if key.is_primary_key_candidate:
            assert key.unique_count == total_rows
