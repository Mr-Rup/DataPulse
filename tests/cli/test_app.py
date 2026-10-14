# =========================================================================
# Unit & Scenario Tests: CLI Application & Configuration Loader
# =========================================================================

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from datapulse import __version__
from datapulse.cli.app import app
from datapulse.config import AnalysisConfig, load_config

runner = CliRunner()

# =========================================================================
# COMMAND-LINE INTERFACE COMMANDS & FORMATS
# =========================================================================

class TestCommandLineInterface:
    """Validate Typer CLI commands, format flags, and stdout/file outputs."""

    def test_cli_help_and_version(self):
        # Help
        res_help = runner.invoke(app, ["--help"])
        assert res_help.exit_code == 0
        assert "analyze" in res_help.stdout
        assert "version" in res_help.stdout

        # Version flag and command
        res_ver_flag = runner.invoke(app, ["--version"])
        assert res_ver_flag.exit_code == 0
        assert f"DataPulse v{__version__}" in res_ver_flag.stdout

        res_ver_cmd = runner.invoke(app, ["version"])
        assert res_ver_cmd.exit_code == 0
        assert f"DataPulse v{__version__}" in res_ver_cmd.stdout

    def test_cli_analyze_terminal_and_export_formats(
        self, realistic_csv_path: Path, tmp_path: Path
    ):
        # Terminal analysis
        res_term = runner.invoke(app, ["analyze", str(realistic_csv_path)])
        assert res_term.exit_code == 0
        assert "Dataset Overview" in res_term.stdout

        # HTML export
        html_out = tmp_path / "cli_report.html"
        res_html = runner.invoke(
            app,
            [
                "analyze",
                str(realistic_csv_path),
                "--format",
                "html",
                "-o",
                str(html_out),
            ],
        )
        assert res_html.exit_code == 0
        assert html_out.exists()
        assert "<!DOCTYPE html>" in html_out.read_text(encoding="utf-8")

        # JSON stdout and file export
        res_json = runner.invoke(
            app, ["analyze", str(realistic_csv_path), "--format", "json"]
        )
        assert res_json.exit_code == 0
        parsed_stdout = json.loads(res_json.stdout)
        assert parsed_stdout["schema_version"] == "1.0.0"
        assert parsed_stdout["summary"]["row_count"] == 50

        json_out = tmp_path / "cli_report.json"
        res_json_file = runner.invoke(
            app,
            [
                "analyze",
                str(realistic_csv_path),
                "--format",
                "json",
                "-o",
                str(json_out),
            ],
        )
        assert res_json_file.exit_code == 0
        assert json_out.exists()

    def test_cli_profile_alias_and_invalid_format(self, realistic_csv_path: Path):
        # Profile alias with --quiet
        res_prof = runner.invoke(app, ["profile", str(realistic_csv_path), "--quiet"])
        assert res_prof.exit_code == 0
        # Invalid format rejection
        res_inv = runner.invoke(
            app, ["analyze", str(realistic_csv_path), "--format", "xml"]
        )
        assert res_inv.exit_code != 0

    def test_cli_default_root_execution_and_smart_detection(
        self, realistic_csv_path: Path, tmp_path: Path
    ):
        # 1. Root execution without typing 'analyze'
        res_root = runner.invoke(app, [str(realistic_csv_path)])
        assert res_root.exit_code == 0
        assert "Dataset Overview" in res_root.stdout
        # 2. Smart auto-detection of format from -o .html
        html_out = tmp_path / "auto_detected.html"
        res_auto_html = runner.invoke(
            app, [str(realistic_csv_path), "-o", str(html_out)]
        )
        assert res_auto_html.exit_code == 0
        assert html_out.exists()
        assert "<!DOCTYPE html>" in html_out.read_text(encoding="utf-8")
        # 3. Smart auto-detection of format from -o .json
        json_out = tmp_path / "auto_detected.json"
        res_auto_json = runner.invoke(
            app, [str(realistic_csv_path), "-o", str(json_out)]
        )
        assert res_auto_json.exit_code == 0
        assert json_out.exists()

    def test_cli_quick_export_shortcut_flags(
        self, realistic_csv_path: Path, tmp_path: Path
    ):
        # Quick --html flag
        html_target = tmp_path / "quick_dashboard.html"
        res_html = runner.invoke(
            app, [str(realistic_csv_path), "--html", "-o", str(html_target)]
        )
        assert res_html.exit_code == 0
        assert html_target.exists()
        # Quick --json flag (stdout)
        res_json = runner.invoke(app, [str(realistic_csv_path), "--json"])
        assert res_json.exit_code == 0
        parsed = json.loads(res_json.stdout)
        assert parsed["schema_version"] == "1.0.0"

    def test_cli_analyze_all_and_section(self, realistic_csv_path: Path):
        # Comprehensive full report (--all)
        res_all = runner.invoke(app, [str(realistic_csv_path), "--all"])
        assert res_all.exit_code == 0
        assert "Dataset Overview" in res_all.stdout
        assert "Dataset Schema" in res_all.stdout

        # Single section via flag (--section quality)
        res_sec = runner.invoke(
            app, [str(realistic_csv_path), "--section", "quality"]
        )
        assert res_sec.exit_code == 0
        assert "Column Quality Summary" in res_sec.stdout

        # Invalid section name rejection
        res_inv = runner.invoke(
            app, [str(realistic_csv_path), "--section", "non_existent"]
        )
        assert res_inv.exit_code != 0

    def test_cli_show_command(self, realistic_csv_path: Path):
        # Default show (overview)
        res_show = runner.invoke(app, ["show", str(realistic_csv_path)])
        assert res_show.exit_code == 0
        assert "Dataset Overview" in res_show.stdout

        # Explicit section (numeric)
        res_num = runner.invoke(app, ["show", str(realistic_csv_path), "numeric"])
        assert res_num.exit_code == 0
        assert "Numeric Statistics" in res_num.stdout

        # Section with column filter
        res_filt = runner.invoke(
            app,
            [
                "show",
                str(realistic_csv_path),
                "missing",
                "--columns",
                "amount,mixed_missing",
            ],
        )
        assert res_filt.exit_code == 0
        assert "Missing Values & Data Gaps" in res_filt.stdout

        # Invalid section rejection
        res_bad = runner.invoke(app, ["show", str(realistic_csv_path), "bogus"])
        assert res_bad.exit_code != 0

    def test_cli_column_command(self, realistic_csv_path: Path):
        # Valid column deep-dive
        res_col = runner.invoke(
            app, ["column", str(realistic_csv_path), "amount"]
        )
        assert res_col.exit_code == 0
        assert "DataPulse | Column: amount" in res_col.stdout
        assert "Missingness Breakdown: amount" in res_col.stdout

        # Non-existent column error handling
        res_err = runner.invoke(
            app, ["column", str(realistic_csv_path), "missing_col"]
        )
        assert res_err.exit_code != 0

    def test_cli_query_command(self, realistic_csv_path: Path):
        # Direct SQL query
        res_sql = runner.invoke(
            app,
            [
                "query",
                str(realistic_csv_path),
                "SELECT * FROM self WHERE amount > 30",
            ],
        )
        assert res_sql.exit_code == 0
        assert "SQL Execution" in res_sql.stdout

        # Filter option query
        res_filt = runner.invoke(
            app,
            [
                "query",
                str(realistic_csv_path),
                "--filter",
                "amount > 30",
            ],
        )
        assert res_filt.exit_code == 0
        assert "Filter:" in res_filt.stdout

        # Column target with --gt filter
        res_gt = runner.invoke(
            app,
            [
                "query",
                str(realistic_csv_path),
                "amount",
                "--gt",
                "30",
            ],
        )
        assert res_gt.exit_code == 0
        assert "Filter:" in res_gt.stdout

        # Column target with --lt filter
        res_lt = runner.invoke(
            app,
            [
                "query",
                str(realistic_csv_path),
                "amount",
                "--lt",
                "30",
            ],
        )
        assert res_lt.exit_code == 0
        assert "Filter:" in res_lt.stdout

        # Column target with --equals filter
        res_eq = runner.invoke(
            app,
            [
                "query",
                str(realistic_csv_path),
                "is_active",
                "--equals",
                "true",
            ],
        )
        assert res_eq.exit_code == 0
        assert "Filter:" in res_eq.stdout

        # Preview default
        res_prev = runner.invoke(app, ["query", str(realistic_csv_path)])
        assert res_prev.exit_code == 0
        assert "Preview:" in res_prev.stdout

    def test_cli_info_command(self, realistic_csv_path: Path):
        # Fast metadata and schema inspection
        res_info = runner.invoke(app, ["info", str(realistic_csv_path)])
        assert res_info.exit_code == 0
        assert "DataPulse | File Information" in res_info.stdout
        assert "Schema Definition" in res_info.stdout


# =========================================================================
# CONFIGURATION LOADING & VALIDATION
# =========================================================================

class TestConfigurationLoading:
    """Validate TOML/JSON configuration loading and typo rejection."""

    def test_load_valid_config_files(self, tmp_path: Path, realistic_csv_path: Path):
        # JSON config
        json_cfg = tmp_path / "conf.json"
        json_cfg.write_text(
            json.dumps({"max_categories": 5, "min_correlation": 0.8}), encoding="utf-8"
        )
        cfg_j = load_config(json_cfg)
        assert isinstance(cfg_j, AnalysisConfig)
        assert cfg_j.max_categories == 5
        assert cfg_j.min_correlation == 0.8

        # TOML config
        toml_cfg = tmp_path / "conf.toml"
        toml_cfg.write_text(
            "max_categories = 10\ncompute_correlations = false\n", encoding="utf-8"
        )
        cfg_t = load_config(toml_cfg)
        assert cfg_t.max_categories == 10
        assert cfg_t.compute_correlations is False

        # Run CLI with config file
        res_cli_cfg = runner.invoke(
            app,
            [
                "analyze",
                str(realistic_csv_path),
                "--config",
                str(toml_cfg),
                "--format",
                "json",
            ],
        )
        assert res_cli_cfg.exit_code == 0
        parsed = json.loads(res_cli_cfg.stdout)
        assert len(parsed["correlations"]) == 0

    def test_config_error_handling(self, tmp_path: Path):
        # Forbid extra keys (typo detection)
        typo_cfg = tmp_path / "typo.json"
        typo_cfg.write_text(json.dumps({"max_catgories": 10}), encoding="utf-8")
        with pytest.raises(ValidationError):
            load_config(typo_cfg)

        # Missing file
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent_file.toml")

        # Unsupported extension
        txt_cfg = tmp_path / "conf.txt"
        txt_cfg.write_text("key=val", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported configuration format"):
            load_config(txt_cfg)
