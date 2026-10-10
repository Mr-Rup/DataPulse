# =========================================================================
# Unit & Scenario Tests: Data Quality Rules
# =========================================================================

from datetime import datetime

import polars as pl

from datapulse import analyze
from datapulse.analysis.quality_rules import (
    check_chronology_inversion,
    check_constant_columns,
    check_duplicates,
    check_high_cardinality,
    check_missingness,
    check_negative_values,
    check_numeric_outliers,
)
from datapulse.models.report import ColumnProfile, DuplicateSummary

# =========================================================================
# STRUCTURAL & COMPLETENESS RULES
# =========================================================================

class TestCompletenessAndStructuralRules:
    """Validate missingness, duplicate rows, constant columns, and cardinality."""

    def test_missingness_severity_thresholds(self):
        cols = [
            ColumnProfile(
                name="col_severe",
                physical_type="Float64",
                null_count=60,
                missing_percentage=60.0,
            ),
            ColumnProfile(
                name="col_moderate",
                physical_type="Float64",
                null_count=30,
                missing_percentage=30.0,
            ),
            ColumnProfile(
                name="col_good",
                physical_type="Float64",
                null_count=5,
                missing_percentage=5.0,
            ),
        ]
        findings = check_missingness(cols)
        assert len(findings) == 2
        assert findings[0].severity == "critical"
        assert findings[0].affected_columns == ["col_severe"]
        assert findings[1].severity == "warning"
        assert findings[1].affected_columns == ["col_moderate"]

    def test_duplicates_and_constants(self):
        dup_severe = DuplicateSummary(
            total_rows=100, unique_rows=80, duplicate_rows=20, duplicate_percentage=20.0
        )
        dup_findings = check_duplicates(dup_severe)
        assert len(dup_findings) == 1
        assert dup_findings[0].severity == "critical"
        assert dup_findings[0].rule_id == "duplicate_rows"

        cols = [
            ColumnProfile(
                name="const_col",
                physical_type="String",
                inferred_role="constant",
                unique_count=1,
            ),
            ColumnProfile(
                name="varying_col",
                physical_type="String",
                inferred_role="categorical",
                unique_count=5,
            ),
        ]
        const_findings = check_constant_columns(cols)
        assert len(const_findings) == 1
        assert const_findings[0].affected_columns == ["const_col"]

    def test_high_cardinality_category(self):
        cols = [
            ColumnProfile(
                name="messy_category",
                physical_type="String",
                inferred_role="categorical",
                unique_count=100,
                statistics={"cardinality_percentage": 75.0},
            )
        ]
        findings = check_high_cardinality(cols)
        assert len(findings) == 1
        assert findings[0].affected_columns == ["messy_category"]


# =========================================================================
# NUMERIC DOMAIN & DISTRIBUTION RULES
# =========================================================================

class TestNumericDomainAndDistributionRules:
    """Validate negative value detection, configuration overrides, and Tukey outliers."""

    def test_negative_values_detection_and_suppression(self):
        cols = [
            ColumnProfile(
                name="fare_amount",
                physical_type="Float64",
                inferred_role="numeric",
                statistics={"negatives_count": 15, "negatives_percentage": 1.5},
            ),
            ColumnProfile(
                name="temperature",
                physical_type="Float64",
                inferred_role="numeric",
                statistics={"negatives_count": 10, "negatives_percentage": 10.0},
            ),
        ]
        # By default, fare_amount is checked via keyword heuristics
        findings = check_negative_values(cols)
        assert len(findings) == 1
        assert findings[0].affected_columns == ["fare_amount"]

        # Suppressed by allowed_negative_columns
        suppressed = check_negative_values(
            cols, allowed_negative_columns=["fare_amount"]
        )
        assert len(suppressed) == 0

        # Explicit non_negative_columns list
        strict = check_negative_values(cols, non_negative_columns=["temperature"])
        assert len(strict) == 1
        assert strict[0].affected_columns == ["temperature"]

    def test_numeric_iqr_outliers_treated_as_info(self):
        data = [10.0] * 10 + [12.0] * 10 + [500.0]
        df = pl.DataFrame({"metric": data})
        cols = [
            ColumnProfile(
                name="metric",
                physical_type="Float64",
                inferred_role="numeric",
                statistics={"p25": 10.0, "p75": 12.0, "iqr": 2.0},
            )
        ]
        findings = check_numeric_outliers(cols, df)
        assert len(findings) == 1
        assert findings[0].affected_columns == ["metric"]
        assert "Distribution tail values" in findings[0].title
        assert findings[0].severity == "info"


# =========================================================================
# TEMPORAL CHRONOLOGY & END-TO-END PIPELINE
# =========================================================================

class TestTemporalChronologyAndPipeline:
    """Validate temporal inversion detection across naming patterns and end-to-end evaluation."""

    def test_chronology_inversion_detection(self):
        # Known pairs (pickup / dropoff)
        df_known = pl.DataFrame(
            {
                "pickup_datetime": [
                    datetime(2025, 1, 1, 10, 0),
                    datetime(2025, 1, 1, 12, 0),
                ],
                "dropoff_datetime": [
                    datetime(2025, 1, 1, 10, 30),
                    datetime(2025, 1, 1, 11, 0),
                ],
            }
        )
        findings_known = check_chronology_inversion(df_known)
        assert len(findings_known) == 1
        assert findings_known[0].severity == "critical"
        assert "dropoff_datetime" in findings_known[0].affected_columns

        # Dynamic suffix pairs (_dispatched / _received)
        df_dynamic = pl.DataFrame(
            {
                "task_dispatched": [
                    datetime(2025, 1, 1, 10, 0),
                    datetime(2025, 1, 1, 12, 0),
                ],
                "task_received": [
                    datetime(2025, 1, 1, 10, 30),
                    datetime(2025, 1, 1, 11, 0),
                ],
            }
        )
        findings_dynamic = check_chronology_inversion(df_dynamic)
        assert len(findings_dynamic) == 1
        assert "task_received" in findings_dynamic[0].affected_columns

    def test_quality_rules_on_realistic_fixture(self, realistic_parquet_path):
        report = analyze(realistic_parquet_path)
        rule_ids = {f.rule_id for f in report.findings}

        # The realistic fixture has duplicates, negative amounts, outliers, constant col, chronology inversion
        assert "duplicate_rows" in rule_ids
        assert "numeric_outliers" in rule_ids
        assert "constant_column" in rule_ids
        assert "chronology_inversion" in rule_ids
