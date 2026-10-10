# DataPulse CLI Reference Manual

Comprehensive reference for the `datapulse` command-line interface.

---

## Command Overview

DataPulse provides a dual-invocation CLI:
1. **Direct root execution:** `datapulse <file_path> [options]`
2. **Explicit subcommand:** `datapulse analyze <file_path> [options]`
3. **Alias subcommand:** `datapulse profile <file_path> [options]`
4. **Version utility:** `datapulse version` or `datapulse -v / --version`

---

## Global Invocations & Flags

```bash
# Check version
datapulse --version
datapulse -v
datapulse version

# Display CLI help manual
datapulse --help
datapulse analyze --help
```

---

## Command Syntax & Options

### `datapulse [analyze] <file_path> [OPTIONS]`

Profiles a tabular dataset from disk, executes quality rules, and renders or saves a report.

#### Positional Arguments

| Argument | Type | Description |
| :--- | :--- | :--- |
| `file_path` | `Path` (Required) | Path to dataset (`.parquet`, `.csv`, `.tsv`, `.json`, `.ndjson`, `.xlsx`, `.xls`). |

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

---

#### Configuration & Profiling Controls

| Option | Short | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--config` | `-c` | `Path` | `None` | Path to a custom TOML or JSON configuration file. |
| `--max-categories` | | `int` | `20` | Maximum top category frequencies to track per column. |
| `--correlations` / `--no-correlations` | | `bool` | `True` | Enable or disable pairwise Pearson/Spearman correlation computations. |
| `--sheet-name` | | `str` | `None` | Sheet name to read when profiling Excel workbooks (`.xlsx`, `.xls`). |
| `--separator` | | `str` | `None` | Delimiter override character for delimited text files (e.g., `","`, `"\t"`, `";"`). |

---

## Practical Examples by Scenario

### 1. Terminal Inspection
```bash
# Quickest terminal summary (no subcommand needed)
datapulse data/customers.csv

# Explicit analyze verb
datapulse analyze data/customers.parquet
```

### 2. Interactive HTML Dashboard
```bash
# Quick export to 'customers_report.html'
datapulse data/customers.csv --html

# Custom output destination
datapulse data/customers.csv -o reports/audit_2026.html
```

### 3. Pipeline JSON Streaming & Export
```bash
# Stream JSON directly to terminal or pipe to jq
datapulse data/customers.csv --json | jq .summary

# Save JSON directly to disk
datapulse data/customers.csv -o data/metrics.json
```

### 4. Excel Workbooks & Custom Delimiters
```bash
# Read specific Excel sheet
datapulse financial_model.xlsx --sheet-name "Revenue_Q3" --html

# Tab-separated file with custom categories
datapulse access_logs.tsv --separator "\t" --max-categories 50
```

### 5. Custom Configuration File
```bash
# Load validation thresholds and sentinels from TOML
datapulse transactions.parquet -c config/prod_audit.toml -o audit.html
```

---

## Zero-Installation Execution (`uvx`)

You can run DataPulse directly from the command line without installing it into an environment:

```bash
uvx datapulse data/dataset.csv --html
```
