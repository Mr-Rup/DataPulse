# DataPulse Architecture & Technical Decisions (ADR Log)

## ADR-001: Standalone Architecture & Core Scope
- **Context:** DataPulse is designed as an automated, local-first exploratory data analysis (EDA) toolkit.
- **Decision:** Establish DataPulse as a focused, reusable, standalone Python package and CLI for automated tabular EDA.
- **Consequences:** Clear product identity, clean codebase, dedicated CLI, and standalone documentation.

## ADR-002: Python Runtime and Environment Tooling
- **Context:** Project uses Windows with Python 3.14.
- **Decision:** Use `uv` for lightning-fast package and environment management. Set `requires-python = ">=3.14,<3.15"`, ruff target version to `py314`, and pyright python version to `3.14`.
- **Consequences:** Consistent, modern Python tooling without version mismatches.

## ADR-003: Model and Data Structure Strategy
- **Context:** Report structures need to be stable, type-safe, and serializable to JSON and HTML.
- **Decision:** Use standard Python `@dataclass` classes with a lightweight `to_dict()` helper rather than external heavy validation frameworks like Pydantic for internal report models.
- **Consequences:** Zero unnecessary dependencies, predictable serialization, and matches author's clean coding style.

## ADR-004: Standard Built-in Exceptions Over Custom Hierarchies
- **Context:** Excessive custom exception boilerplate adds overhead without user value.
- **Decision:** Use standard built-in Python exceptions (`FileNotFoundError`, `ValueError`, `KeyError`) with descriptive, contextual error messages. Avoid empty exception class hierarchies.
- **Consequences:** Direct, readable code matching DataPulse's core style.

## ADR-005: Strict Phase-Wise Git Lifecycle
- **Context:** Need clear traceability, reviewable diffs, and clean git history across development phases.
- **Decision:** Each phase operates on a dedicated branch (`dp-N-<name>`), validates test/lint/types, commits with descriptive messages, pushes the branch for review, merges cleanly into `main`, and pushes `main`.
