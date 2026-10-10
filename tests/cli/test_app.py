import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from datapulse import __version__
from datapulse.cli.app import app
from datapulse.config import AnalysisConfig, load_config

runner = CliRunner()


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(
        "id,fare,tip,passenger_count,category\n"
        "1,10.5,2.0,1,A\n"
        "2,15.0,3.0,2,B\n"
        "3,20.0,4.5,1,A\n"
        "4,12.0,1.5,1,B\n"
        "5,8.0,0.0,3,C\n",
        encoding="utf-8",
    )
    return csv_file


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "analyze" in result.stdout
    assert "profile" in result.stdout
    assert "version" in result.stdout


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"DataPulse v{__version__}" in result.stdout

    result_cmd = runner.invoke(app, ["version"])
    assert result_cmd.exit_code == 0
    assert f"DataPulse v{__version__}" in result_cmd.stdout


def test_cli_analyze_terminal(sample_csv: Path):
    result = runner.invoke(app, ["analyze", str(sample_csv)])
    assert result.exit_code == 0
    assert "Dataset Overview" in result.stdout or "DATA QUALITY" in result.stdout


def test_cli_analyze_html(sample_csv: Path, tmp_path: Path):
    html_out = tmp_path / "custom_report.html"
    result = runner.invoke(
        app,
        ["analyze", str(sample_csv), "--format", "html", "--output", str(html_out)],
    )
    assert result.exit_code == 0
    assert html_out.exists()
    content = html_out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "test_data.csv" in content


def test_cli_analyze_json_stdout(sample_csv: Path):
    result = runner.invoke(
        app,
        ["analyze", str(sample_csv), "--format", "json"],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["schema_version"] == "1.0.0"
    assert parsed["summary"]["row_count"] == 5


def test_cli_analyze_json_file(sample_csv: Path, tmp_path: Path):
    json_out = tmp_path / "out.json"
    result = runner.invoke(
        app,
        ["analyze", str(sample_csv), "--format", "json", "-o", str(json_out)],
    )
    assert result.exit_code == 0
    assert json_out.exists()
    parsed = json.loads(json_out.read_text(encoding="utf-8"))
    assert parsed["summary"]["row_count"] == 5


def test_cli_analyze_with_config(sample_csv: Path, tmp_path: Path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        "[datapulse]\n"
        "max_categories = 5\n"
        "compute_correlations = false\n",
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        [
            "analyze",
            str(sample_csv),
            "--config",
            str(cfg_file),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["summary"]["row_count"] == 5
    assert len(parsed["correlations"]) == 0


def test_cli_profile_alias(sample_csv: Path):
    result = runner.invoke(app, ["profile", str(sample_csv), "--quiet"])
    assert result.exit_code == 0


def test_cli_invalid_format(sample_csv: Path):
    result = runner.invoke(app, ["analyze", str(sample_csv), "--format", "xml"])
    assert result.exit_code != 0
    all_output = result.stdout + (result.stderr if hasattr(result, "stderr") else "")
    assert "Invalid format" in all_output or result.exit_code == 2


def test_load_config_json(tmp_path: Path):
    json_path = tmp_path / "conf.json"
    json_path.write_text(
        json.dumps({"max_categories": 5, "min_correlation": 0.8}),
        encoding="utf-8",
    )
    cfg = load_config(json_path)
    assert isinstance(cfg, AnalysisConfig)
    assert cfg.max_categories == 5
    assert cfg.min_correlation == 0.8


def test_load_config_toml(tmp_path: Path):
    toml_path = tmp_path / "conf.toml"
    toml_path.write_text(
        "max_categories = 10\ncompute_correlations = false\n",
        encoding="utf-8",
    )
    cfg = load_config(toml_path)
    assert cfg.max_categories == 10
    assert cfg.compute_correlations is False


def test_load_config_forbids_extra_keys(tmp_path: Path):
    json_path = tmp_path / "typo_conf.json"
    json_path.write_text(
        json.dumps({"max_catgories": 10}),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_config(json_path)


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("does_not_exist.toml")


def test_load_config_invalid_format(tmp_path: Path):
    txt_path = tmp_path / "conf.txt"
    txt_path.write_text("hello=world", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported configuration format"):
        load_config(txt_path)
