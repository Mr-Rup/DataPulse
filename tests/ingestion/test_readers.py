# =========================================================================
# Unit & Scenario Tests: Dataset Ingestion & Format Readers
# =========================================================================

from pathlib import Path

import polars as pl
import pytest

from datapulse.ingestion.readers import read_source

# =========================================================================
# CORE TABULAR FORMAT READERS
# =========================================================================

class TestTabularFormatReaders:
    """Validate standard ingestion across supported tabular formats."""

    def test_parquet_and_excel_ingestion(self, tmp_path: Path):
        # Parquet
        df_pq = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        pq_path = tmp_path / "test.parquet"
        df_pq.write_parquet(pq_path)
        lf_pq, info_pq = read_source(pq_path)
        assert info_pq.file_format == "parquet"
        assert lf_pq.collect().height == 3

        # Excel
        df_xl = pl.DataFrame({"metric": ["a", "b"], "score": [95, 88]})
        xl_path = tmp_path / "test.xlsx"
        df_xl.write_excel(xl_path)
        lf_xl, info_xl = read_source(xl_path)
        assert info_xl.file_format == "excel"
        assert lf_xl.collect().height == 2

    def test_json_and_ndjson_ingestion(self, tmp_path: Path):
        # JSON array
        json_path = tmp_path / "test.json"
        json_path.write_text(
            '[{"id": 1, "val": "a"}, {"id": 2, "val": "b"}]', encoding="utf-8"
        )
        lf_json, info_json = read_source(json_path)
        assert info_json.file_format == "json"
        assert lf_json.collect().height == 2

        # NDJSON
        ndjson_path = tmp_path / "test.ndjson"
        ndjson_path.write_text(
            '{"id": 1, "val": "a"}\n{"id": 2, "val": "b"}\n', encoding="utf-8"
        )
        lf_nd, info_nd = read_source(ndjson_path)
        assert info_nd.file_format == "json"
        assert lf_nd.collect().height == 2

    def test_real_dataset_taxi_lookup(self):
        path = Path("data/raw/taxi_zone_lookup.csv")
        if not path.exists():
            pytest.skip("taxi_zone_lookup.csv not present locally")

        lf, info = read_source(path)
        assert info.file_format == "csv"
        collected = lf.collect()
        assert collected.height == 265
        assert "LocationID" in collected.columns


# =========================================================================
# DELIMITERS, LINE TERMINATORS & ENCODING RESILIENCE
# =========================================================================

class TestDelimitersAndEncodingResilience:
    """Validate delimiter auto-sniffing, legacy CR line endings, and encoding fallbacks."""

    def test_delimiter_auto_detection(self, tmp_path: Path):
        # Standard CSV
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "id,name,value\n1,Alice,10.5\n2,Bob,20.0\n", encoding="utf-8"
        )
        lf_csv, _ = read_source(csv_file)
        assert lf_csv.collect().columns == ["id", "name", "value"]

        # Semicolon delimited (auto-sniffed)
        semi_file = tmp_path / "semi.csv"
        semi_file.write_text(
            "metric;value;flag\na;100;true\nb;200;false\n", encoding="utf-8"
        )
        lf_semi, _ = read_source(semi_file)
        assert lf_semi.collect().columns == ["metric", "value", "flag"]

        # Pipe delimited (auto-sniffed)
        pipe_file = tmp_path / "pipe.csv"
        pipe_file.write_text(
            "id|city|pop\n1|Tokyo|37000000\n2|Delhi|32000000\n", encoding="utf-8"
        )
        lf_pipe, _ = read_source(pipe_file)
        assert lf_pipe.collect().columns == ["id", "city", "pop"]

        # Native TSV extension
        tsv_file = tmp_path / "dataset.tsv"
        tsv_file.write_text(
            "id\tname\tscore\n1\tAlpha\t99.5\n2\tBeta\t88.0\n", encoding="utf-8"
        )
        lf_tsv, _ = read_source(tsv_file)
        assert lf_tsv.collect().columns == ["id", "name", "score"]

    def test_line_terminators_and_lossy_utf8(self, tmp_path: Path):
        # Legacy Mac / isolated CR (\r) line terminators
        cr_content = b"col_a,col_b,col_c\r1,10.5,foo\r2,20.0,bar\r3,30.5,baz\r"
        cr_file = tmp_path / "cr_ending.csv"
        cr_file.write_bytes(cr_content)
        lf_cr, _ = read_source(cr_file)
        assert lf_cr.collect().height == 3
        assert lf_cr.collect().columns == ["col_a", "col_b", "col_c"]

        # Latin-1 bytes with invalid UTF-8 sequence (handled gracefully via utf8-lossy)
        latin1_content = b"id,name\n1,Caf\xe9\n2,Na\xefve\n"
        latin1_file = tmp_path / "latin1.csv"
        latin1_file.write_bytes(latin1_content)
        lf_l1, _ = read_source(latin1_file)
        assert lf_l1.collect().height == 2

    def test_boston_housing_dataset_if_present(self):
        boston_path = Path(
            r"C:\Users\majum\Downloads\archive\Boston-house-price-data.csv"
        )
        if not boston_path.exists():
            pytest.skip("Boston housing dataset not present in downloads")

        lf, info = read_source(boston_path)
        assert info.file_format == "csv"
        collected = lf.collect()
        assert collected.height == 506
        assert collected.width == 14
        assert "MEDV" in collected.columns


# =========================================================================
# INGESTION VALIDATION & ERROR HANDLING
# =========================================================================

class TestIngestionValidation:
    """Validate diagnostic errors for missing, empty, or corrupt datasets."""

    def test_rejection_of_missing_and_empty_files(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            read_source(tmp_path / "nonexistent.parquet")

        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="empty"):
            read_source(empty_file)

        ws_file = tmp_path / "whitespace.json"
        ws_file.write_text("   \n\n\t  ", encoding="utf-8")
        with pytest.raises(ValueError, match="contains no data"):
            read_source(ws_file)

    def test_rejection_of_corrupt_files_and_unsupported_extensions(
        self, tmp_path: Path
    ):
        corrupt_json = tmp_path / "corrupt.json"
        corrupt_json.write_text('[{"id": 1, "unclosed": }', encoding="utf-8")
        with pytest.raises(ValueError, match="Failed to parse JSON file"):
            read_source(corrupt_json)

        invalid_json = tmp_path / "invalid.json"
        invalid_json.write_text("not a json document", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON structure"):
            read_source(invalid_json)

        unsupported = tmp_path / "data.unsupported"
        unsupported.write_text("content", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported file format"):
            read_source(unsupported)
