# DataPulse Architecture & Technical Decisions (ADR Log)

A record of key architectural choices and design rationales made during the development of DataPulse.

---

## ADR-001: Standalone Architecture & Core Scope
- **Context:** Automated exploratory data analysis tools need to be modular, fast, and reusable across projects.
- **Decision:** Establish DataPulse as a completely standalone, focused Python library and CLI dedicated strictly to tabular EDA.
- **Consequences:** Clear product identity, zero bloat, clean codebase, and self-contained documentation.

---

## ADR-002: Polars-First Execution Engine
- **Context:** Traditional Pandas-based profilers suffer from high memory duplication, single-threaded execution, and slow profiling on multi-gigabyte datasets.
- **Decision:** Build the entire ingestion, missingness, and statistical profiling engine directly on Polars and Rust multi-threading.
- **Consequences:** Blazing profiling speed (~1,200,000+ rows/second), zero-copy lazy frame evaluations, and minimal memory overhead.

---

## ADR-003: Modern Python Runtime & Packaging Tooling
- **Context:** The library must be fast to develop, test, and install across Windows, macOS, and Linux.
- **Decision:** Support Python `>=3.11` across all modern runtimes (3.11, 3.12, 3.13, 3.14). Standardize on `uv` for lightning-fast dependency management, while maintaining full compatibility with traditional `pip`.
- **Consequences:** Broad Python version support, sub-second test execution, and modern packaging via Hatchling.

---

## ADR-004: Strongly-Typed Pydantic Configuration with Typo Detection
- **Context:** User configuration for analytical thresholds, sentinels, and overrides requires schema validation and protection against misspelled options.
- **Decision:** Use Pydantic v2 for `AnalysisConfig` with `extra="forbid"`, custom sentinel validators, and bounds checking.
- **Consequences:** Clear validation error messages on configuration typos, predictable deserialization from TOML and JSON, and full IDE autocompletion.

---

## ADR-005: Dual CLI Ergonomics & Smart Format Auto-Detection
- **Context:** CLI users want minimal typing overhead without losing explicit subcommand capabilities.
- **Decision:** Support direct root execution (`datapulse data.csv`) alongside subcommands (`datapulse analyze data.csv`). Automatically infer report format from the output file extension (`-o report.html` -> HTML mode, `-o data.json` -> JSON mode), and provide shortcut flags (`--html`, `--json`).
- **Consequences:** Effortless command execution across CMD, PowerShell, and Bash with zero typing fatigue.

---

## ADR-006: Self-Contained Standalone HTML Reports
- **Context:** HTML audit reports are often viewed offline, behind enterprise firewalls, or in isolated air-gapped environments.
- **Decision:** Bundle the entire HTML dashboard with embedded Vanilla CSS and lightweight inline JavaScript. Zero external CDN dependencies (e.g., no external fonts or remote JavaScript bundles).
- **Consequences:** HTML reports open instantly anywhere, never break due to CDN outages, and respect strict enterprise security policies.
---

## ADR-007: Pure Polars Architecture (0% Pandas Overhead)
- **Context:** Legacy EDA libraries often retain hidden Pandas conversions, causing silent memory bloat and single-threaded CPU contention.
- **Decision:** Mandate a 100% pure Polars architecture across all components (ingestion, missingness, statistical calculations, classifications, and exports). Forbid any Pandas dependency or runtime conversion.
- **Consequences:** Predictable sub-second execution, native Rust multi-threading, low memory footprint, and full compatibility with in-memory Polars DataFrames and LazyFrames.

---

## ADR-008: Modular CLI Command Architecture & Polars SQL Querying
- **Context:** As command capabilities grew (section views, column profiles, SQL querying, metadata inspection), maintaining a monolithic `app.py` created unnecessary complexity. Users also needed the ability to query tabular data directly from the terminal without launching separate SQL clients.
- **Decision:** Decompose CLI commands into modular handlers under `datapulse.cli.commands` (`analyze`, `show`, `column`, `query`, `info`). Integrate Polars' native `SQLContext` in `datapulse query` to allow direct SQL and expression execution against any supported tabular file.
- **Consequences:** Clean separation of concerns, high maintainability, and direct SQL querying capability with zero database overhead.

