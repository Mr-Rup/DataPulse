# Contributing to DataPulse

Thank you for your interest in contributing to DataPulse!

We have prepared a comprehensive, step-by-step developer and contributor guide detailing how to set up your environment, write quality rules, add semantic roles, implement file readers, add CLI commands, and adhere to our code conventions:

👉 **[Read the DataPulse Developer & Contributor Guide](docs/CONTRIBUTING.md)**

---

### Quick Verification Commands

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Check code formatting & linting
uv run ruff check .

# Check static types
uv run pyright

# Build distribution packages
uv build
```
