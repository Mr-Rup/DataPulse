# =============================================================================
# Unit & Scenario Tests: CLI Application & Configuration Loader
# =============================================================================

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from datapulse import __version__
from datapulse.cli.app import app
from datapulse.config import AnalysisConfig, load_config

runner = CliRunner()


# =============================================================================
# 1. COMMAND-LINE INTERFACE COMMANDS & FORMATS
# =============================================================================


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


# =============================================================================
# 2. CONFIGURATION LOADING & VALIDATION
# =============================================================================


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
