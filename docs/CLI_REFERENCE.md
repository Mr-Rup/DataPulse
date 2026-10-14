# DataPulse CLI Reference Manual

Comprehensive technical manual for the `datapulse` command-line interface.

---

## 📐 General Command Pattern

DataPulse follows a clean, predictable command syntax across all environments (PowerShell, CMD, Bash, Zsh):

```bash
datapulse <command> <file> [sub-target/column/section] [options]
```

### Command Dispatch & Default Execution
- **Direct file execution:** Running `datapulse <file>` automatically resolves to `datapulse analyze <file>`.
- **Command list:** `analyze`, `profile` (alias), `show`, `column`, `query`, `info`, `version`.
- **Global flags:** `--version` (`-v`), `--help`.

```bash
# Direct execution (defaults to analyze)
datapulse data/sales.csv

# Explicit analyze verb
datapulse analyze data/sales.csv

# View general help or command-specific options
datapulse --help
datapulse show --help
```

---

## 🛠️ Commands Reference

### 1. `datapulse [analyze] <file_path> [OPTIONS]`

Analyzes and profiles a dataset from disk, executes automated data quality audits, and renders terminal tables or saves reports.

#### Positional Arguments

| Argument | Type | Description |
| :--- | :--- | :--- |
| `file_path` | `Path` (Required) | Path to dataset (`.parquet`, `.csv`, `.tsv`, `.json`, `.ndjson`, `.xlsx`, `.xls`). |

#### Display & Filtering Options

| Option | Short | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--all` | `-a` | `flag` | `False` | Display full comprehensive report across all sections (bypassing the default 5–6 core summary view). |
| `--section` | `-s` | `str` | `None` | Display only a specific analytical section (e.g. `quality`, `numeric`, `missing`). |
| `--columns` | | `str` | `None` | Comma-separated column names to filter table output (e.g. `--columns age,salary`). |

#### Output Format & Destination Options

| Option | Short | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--format` | `-f` | `str` | `terminal` | Output format: `terminal`, `html`, or `json`. |
| `--output` | `-o` | `Path` | `None` | Destination path for report file (`.html` or `.json`). |
| `--html` | | `flag` | `False` | Shortcut flag to generate an interactive HTML dashboard. If `-o` is omitted, defaults to `<filename>_report.html`. |
| `--json` | | `flag` | `False` | Shortcut flag to output machine-readable JSON. If `-o` is omitted, streams JSON to stdout. |
| `--quiet` | `-q` | `flag` | `False` | Suppresses terminal banner outputs when writing reports to disk. |

> **Smart Output Auto-Detection:**  
> Specifying `-o report.html` automatically switches the format to `html`.  
> Specifying `-o data.json` automatically switches the format to `json`.

#### Profiling & Ingestion Controls

| Option | Short | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--config` | `-c` | `Path` | `None` | Path to custom TOML or JSON configuration file. |
| `--max-categories` | | `int` | `20` | Maximum top category frequencies to track per column. |
| `--correlations` / `--no-correlations` | | `bool` | `True` | Enable or disable pairwise Pearson/Spearman correlation computations. |
| `--sheet-name` | | `str` | `None` | Sheet name to read when profiling Excel workbooks (`.xlsx`, `.xls`). |
| `--separator` | | `str` | `None` | Delimiter override character for delimited text files (e.g., `","`, `"\t"`, `";"`). |

---

### 2. `datapulse show <file_path> [SECTION] [OPTIONS]`

Target an analytical section or filtered column view without displaying unneeded sections.

#### Positional Arguments

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `file_path` | `Path` (Required) | | Path to dataset file. |
| `section` | `str` (Optional) | `overview` | Analytical section to render (see table below). |

#### Available Sections

| Section Key | Aliases | Description |
| :--- | :--- | :--- |
| `overview` | | High-level dataset metrics (rows, columns, format, size, elapsed time). |
| `schema` | | Physical column types and Polars schema. |
| `missing` | | Detailed accounting of nulls, float NaNs, empty strings, and sentinels. |
| `duplicates` | `duplicate` | Full-row duplicate count and duplicate percentage. |
| `quality` | | Column quality score table with inferred analytical roles. |
| `numeric` | | Quantiles, mean, std dev, IQR, zero counts, and negative counts. |
| `categorical` | | Distinct counts, cardinality ratios, mode, and top categories. |
| `temporal` | `datetime`, `date` | Timestamp ranges, span duration, and unique counts. |
| `boolean` | `bool` | True/False distribution and percentage breakdown. |
| `text` | | Freeform text character length metrics (min, max, mean, median). |
| `identifiers` | `identifier`, `id` | Identifier uniqueness ratios and duplicate key counts. |
| `findings` | `anomalies` | Automated data quality alerts and anomaly explanations. |
| `correlations` | `corr` | Pairwise Pearson/Spearman correlations ($|r| \ge 0.50$). |
| `keys` | `key` | Primary key candidate evaluation (100% uniqueness, 0 nulls). |

#### Options

| Option | Short | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--columns` | | `str` | `None` | Comma-separated column names to filter section output. |
| `--config` | `-c` | `Path` | `None` | Path to configuration file. |
| `--sheet-name` | | `str` | `None` | Excel sheet name. |
| `--separator` | | `str` | `None` | Delimiter character override. |

#### Examples
```bash
# View missingness across all columns
datapulse show data.csv missing

# View numeric stats for selected columns
datapulse show data.parquet numeric --columns fare_amount,trip_distance

# View automated quality alerts only
datapulse show data.csv findings
```

---

### 3. `datapulse column <file_path> <column_name> [OPTIONS]`

Provides an exhaustive, single-column statistical deep dive.

#### Positional Arguments

| Argument | Type | Description |
| :--- | :--- | :--- |
| `file_path` | `Path` (Required) | Path to dataset file. |
| `column_name` | `str` (Required) | Exact column name to profile. |

#### Output Details
- **Header Panel:** Physical Polars type, inferred semantic role, confidence %, classification rationale, and distinct count.
- **Missingness Breakdown:** Nulls, NaNs, empty strings, sentinels, and total missing %.
- **Distribution & Statistics:** Quantiles, mean, median, IQR, skewness, zeros, or category frequencies.
- **Data Quality Alerts:** Any critical, warning, or informational alerts impacting this column.

#### Options

| Option | Short | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--config` | `-c` | `Path` | `None` | Path to configuration file. |
| `--sheet-name` | | `str` | `None` | Excel sheet name. |
| `--separator` | | `str` | `None` | Delimiter character override. |

#### Example
```bash
datapulse column transactions.parquet fare_amount
```

---

### 4. `datapulse query <file_path> [TARGET_OR_SQL] [OPTIONS]`

Executes direct SQL queries or column filters against any tabular dataset using native Polars `SQLContext`.

#### Positional Arguments

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `file_path` | `Path` (Required) | | Path to dataset file. |
| `target_or_sql` | `str` (Optional) | `None` | Full SQL statement, column name, or filter expression. |

#### Querying Modes

1. **Direct SQL:**
   DataPulse registers the dataset in `pl.SQLContext` under table names: `self`, `df`, `table`, and the file's clean stem name:
   ```bash
   datapulse query data.csv "SELECT * FROM self WHERE fare_amount < 0"
   datapulse query data.parquet "SELECT category, count(*) FROM self GROUP BY category"
   ```

2. **Expression Filter (`--filter`):**
   ```bash
   datapulse query data.csv --filter "fare_amount < 0 AND trip_distance > 5"
   ```

3. **Column Threshold Filtering:**
   ```bash
   # Filter by greater-than
   datapulse query data.csv fare_amount --gt 100

   # Filter by less-than
   datapulse query data.csv age --lt 18

   # Filter by exact equality
   datapulse query data.csv payment_type --equals CASH
   ```

4. **Default Quick Preview:**
   ```bash
   datapulse query data.csv --limit 10
   ```

#### Options

| Option | Short | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--filter` | | `str` | `None` | Filter expression string. |
| `--equals` | | `str` | `None` | Match value for target column. |
| `--gt` | | `float` | `None` | Greater-than threshold for target column. |
| `--lt` | | `float` | `None` | Less-than threshold for target column. |
| `--limit` | `-n` | `int` | `50` | Maximum number of rows to return and display. |
| `--sheet-name` | | `str` | `None` | Excel sheet name. |
| `--separator` | | `str` | `None` | Delimiter character override. |

---

### 5. `datapulse info <file_path> [OPTIONS]`

Lightweight metadata and schema inspection without the computational overhead of full dataset profiling.

#### Positional Arguments

| Argument | Type | Description |
| :--- | :--- | :--- |
| `file_path` | `Path` (Required) | Path to dataset file. |

#### Output Details
- Source filename, absolute path, detected format, and file size in MB.
- Total row count (resolved lazily without eagerly reading entire dataset).
- Total column count and complete Polars physical schema table.

#### Options

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--sheet-name` | `str` | `None` | Excel sheet name. |
| `--separator` | `str` | `None` | Delimiter character override. |

#### Example
```bash
datapulse info large_dataset.parquet
```

---

### 6. `datapulse version`

Prints the current version of DataPulse and exits.

```bash
datapulse version
datapulse -v
datapulse --version
```

---

## ⚡ Instant Execution with `uvx`

You can run any DataPulse command without pre-installing the package:

```bash
# Instant profile
uvx --from git+https://github.com/Mr-Rup/polars-datapulse.git datapulse data.csv

# Instant SQL query
uvx --from git+https://github.com/Mr-Rup/polars-datapulse.git datapulse query data.csv "SELECT * FROM self LIMIT 5"
```
