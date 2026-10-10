from pathlib import Path

import polars as pl
import pytest

from datapulse.ingestion.readers import read_source


def test_read_source_parquet(tmp_path):
    df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    file_path = tmp_path / "test.parquet"
    df.write_parquet(file_path)

    lf, info = read_source(file_path)

    assert info.file_format == "parquet"
    assert info.file_name == "test.parquet"
    assert info.file_size_mb >= 0.0

    collected = lf.collect()
    assert collected.height == 3
    assert collected.width == 2


def test_read_source_csv(tmp_path):
    csv_content = "id,name,value\n1,Alice,10.5\n2,Bob,20.0\n"
    file_path = tmp_path / "test.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    lf, info = read_source(file_path)

    assert info.file_format == "csv"
    collected = lf.collect()
    assert collected.height == 2
    assert collected.columns == ["id", "name", "value"]


def test_read_source_csv_custom_separator(tmp_path):
    csv_content = "id;name;value\n1;Alice;10.5\n2;Bob;20.0\n"
    file_path = tmp_path / "semicolon.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    lf, info = read_source(file_path, separator=";")

    assert info.file_format == "csv"
    collected = lf.collect()
    assert collected.height == 2
    assert collected.columns == ["id", "name", "value"]


def test_read_source_ndjson(tmp_path):
    json_lines = '{"id": 1, "val": "a"}\n{"id": 2, "val": "b"}\n'
    file_path = tmp_path / "test.ndjson"
    file_path.write_text(json_lines, encoding="utf-8")

    lf, info = read_source(file_path)

    assert info.file_format == "json"
    collected = lf.collect()
    assert collected.height == 2
    assert collected.columns == ["id", "val"]


def test_read_source_json_array(tmp_path):
    json_array = '[{"id": 1, "val": "a"}, {"id": 2, "val": "b"}]'
    file_path = tmp_path / "test.json"
    file_path.write_text(json_array, encoding="utf-8")

    lf, info = read_source(file_path)

    assert info.file_format == "json"
    collected = lf.collect()
    assert collected.height == 2
    assert collected.columns == ["id", "val"]


def test_read_source_excel(tmp_path):
    df = pl.DataFrame({"metric": ["a", "b"], "score": [95, 88]})
    file_path = tmp_path / "test.xlsx"
    df.write_excel(file_path)

    lf, info = read_source(file_path)

    assert info.file_format == "excel"
    collected = lf.collect()
    assert collected.height == 2
    assert collected.columns == ["metric", "score"]


def test_read_source_rejects_missing_file(tmp_path):
    missing = tmp_path / "nonexistent.parquet"
    with pytest.raises(FileNotFoundError):
        read_source(missing)


def test_read_source_rejects_empty_file(tmp_path):
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        read_source(empty)


def test_read_source_rejects_whitespace_only_file(tmp_path):
    ws_file = tmp_path / "whitespace.json"
    ws_file.write_text("   \n\n\t  ", encoding="utf-8")
    with pytest.raises(ValueError, match="contains no data"):
        read_source(ws_file)


def test_read_source_corrupt_json_reports_error(tmp_path):
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text('[{"id": 1, "unclosed": }', encoding="utf-8")
    with pytest.raises(ValueError, match="Failed to parse JSON file"):
        read_source(corrupt)


def test_read_source_invalid_json_leading_character(tmp_path):
    invalid = tmp_path / "invalid.json"
    invalid.write_text("not a json document", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON structure"):
        read_source(invalid)


def test_read_source_rejects_unsupported_extension(tmp_path):
    unsupported = tmp_path / "data.unsupported"
    unsupported.write_text("content", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported file format"):
        read_source(unsupported)


def test_read_source_real_taxi_zone_lookup():
    path = Path("data/raw/taxi_zone_lookup.csv")
    if not path.exists():
        pytest.skip("taxi_zone_lookup.csv not present locally")

    lf, info = read_source(path)
    assert info.file_format == "csv"
    collected = lf.collect()
    assert collected.height == 265
    assert "LocationID" in collected.columns
    assert "Borough" in collected.columns


def test_read_source_csv_cr_line_endings(tmp_path):
    # Classic Mac / legacy CR (\r) line terminators
    content = b"col_a,col_b,col_c\r1,10.5,foo\r2,20.0,bar\r3,30.5,baz\r"
    file_path = tmp_path / "cr_ending.csv"
    file_path.write_bytes(content)

    lf, info = read_source(file_path)
    assert info.file_format == "csv"
    collected = lf.collect()
    assert collected.height == 3
    assert collected.columns == ["col_a", "col_b", "col_c"]


def test_read_source_tsv_auto_detection(tmp_path):
    tsv_content = "id\tname\tscore\n1\tAlpha\t99.5\n2\tBeta\t88.0\n"
    file_path = tmp_path / "dataset.tsv"
    file_path.write_text(tsv_content, encoding="utf-8")

    lf, info = read_source(file_path)
    assert info.file_format == "csv"
    collected = lf.collect()
    assert collected.height == 2
    assert collected.columns == ["id", "name", "score"]


def test_read_source_semicolon_auto_detection(tmp_path):
    content = "metric;value;flag\na;100;true\nb;200;false\n"
    file_path = tmp_path / "semicolon_auto.csv"
    file_path.write_text(content, encoding="utf-8")

    lf, info = read_source(file_path)
    assert info.file_format == "csv"
    collected = lf.collect()
    assert collected.height == 2
    assert collected.columns == ["metric", "value", "flag"]


def test_read_source_pipe_auto_detection(tmp_path):
    content = "id|city|population\n1|Tokyo|37000000\n2|Delhi|32000000\n"
    file_path = tmp_path / "pipe_auto.csv"
    file_path.write_text(content, encoding="utf-8")

    lf, info = read_source(file_path)
    assert info.file_format == "csv"
    collected = lf.collect()
    assert collected.height == 2
    assert collected.columns == ["id", "city", "population"]


def test_read_source_utf8_lossy_fallback(tmp_path):
    # Latin-1 bytes with invalid UTF-8 sequence: e.g. Café with 0xE9
    latin1_content = b"id,name\n1,Caf\xe9\n2,Na\xefve\n"
    file_path = tmp_path / "latin1.csv"
    file_path.write_bytes(latin1_content)

    lf, info = read_source(file_path)
    assert info.file_format == "csv"
    collected = lf.collect()
    assert collected.height == 2
    assert collected.columns == ["id", "name"]


def test_read_source_boston_housing_cr_if_available():
    boston_path = Path(r"C:\Users\majum\Downloads\archive\Boston-house-price-data.csv")
    if not boston_path.exists():
        pytest.skip("Boston housing dataset not present in downloads")

    lf, info = read_source(boston_path)
    assert info.file_format == "csv"
    collected = lf.collect()
    assert collected.height == 506
    assert collected.width == 14
    assert "MEDV" in collected.columns
    assert "CRIM" in collected.columns

