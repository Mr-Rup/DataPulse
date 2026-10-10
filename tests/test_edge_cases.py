from pathlib import Path

import polars as pl

from datapulse import analyze


def test_single_row_dataset(tmp_path: Path):
    file_path = tmp_path / "single_row.csv"
    file_path.write_text("id,val,category\n1,42.5,A\n", encoding="utf-8")

    report = analyze(file_path)
    assert report.summary.row_count == 1
    assert report.summary.column_count == 3
    assert len(report.columns) == 3
    assert report.correlations == []


def test_single_column_dataset(tmp_path: Path):
    file_path = tmp_path / "single_col.parquet"
    df = pl.DataFrame({"metric": [10.0, 20.0, 30.0, 40.0, 50.0]})
    df.write_parquet(file_path)

    report = analyze(file_path)
    assert report.summary.row_count == 5
    assert report.summary.column_count == 1
    assert report.correlations == []


def test_all_null_columns(tmp_path: Path):
    file_path = tmp_path / "all_null.csv"
    file_path.write_text("a,b,c\n,,\n,,\n,,\n", encoding="utf-8")

    report = analyze(file_path)
    assert report.summary.row_count == 3
    for col in report.columns:
        assert col.null_count == 3
        assert col.missing_percentage == 100.0


def test_all_nan_float_column(tmp_path: Path):
    file_path = tmp_path / "all_nan.parquet"
    df = pl.DataFrame({"nan_col": [float("nan"), float("nan"), float("nan")]})
    df.write_parquet(file_path)

    report = analyze(file_path)
    col = report.columns[0]
    assert col.nan_count == 3
    assert col.total_missing_count == 3
    assert col.missing_percentage == 100.0


def test_all_inf_float_column(tmp_path: Path):
    file_path = tmp_path / "all_inf.parquet"
    df = pl.DataFrame({"inf_col": [float("inf"), float("-inf"), float("inf")]})
    df.write_parquet(file_path)

    report = analyze(file_path)
    col = report.columns[0]
    assert col.statistics.get("infinite_count") == 3


def test_all_constant_column(tmp_path: Path):
    file_path = tmp_path / "constant.csv"
    file_path.write_text("state,zip\nCA,94105\nCA,94105\nCA,94105\n", encoding="utf-8")

    report = analyze(file_path)
    const_findings = [f for f in report.findings if f.rule_id == "constant_column"]
    assert len(const_findings) >= 1


def test_huge_numeric_magnitudes(tmp_path: Path):
    file_path = tmp_path / "magnitudes.parquet"
    df = pl.DataFrame({"huge": [1e20, -1e20, 1e-20, 0.0]})
    df.write_parquet(file_path)

    report = analyze(file_path)
    assert report.summary.row_count == 4
    json_str = report.to_json()
    assert "huge" in json_str


def test_unicode_and_special_character_column_names(tmp_path: Path):
    file_path = tmp_path / "unicode_headers.csv"
    file_path.write_text(
        "📈 revenue (USD) / día,naïve_café,user.id@domain\n100,5,foo\n200,8,bar\n",
        encoding="utf-8",
    )

    report = analyze(file_path)
    assert report.summary.column_count == 3
    names = [c.name for c in report.columns]
    assert "📈 revenue (USD) / día" in names
    assert "naïve_café" in names

    # Verify HTML and JSON exports preserve and escape headers cleanly
    html = report.save_html(tmp_path / "unicode.html").read_text(encoding="utf-8")
    assert "📈 revenue (USD) / día" in html
    assert "naïve_café" in html

    json_str = report.to_json()
    assert "📈 revenue (USD) / día" in json_str
