# =========================================================================
# DataPulse JSON Exporter
# RFC 8259 compliant report serialization and disk writer.
# =========================================================================

from pathlib import Path

from datapulse.models.report import AnalysisReport

# =========================================================================
# JSON FILE EXPORTER
# =========================================================================

def export_json(
    report: AnalysisReport,
    output_path: str | Path,
    indent: int = 2,
) -> Path:
    """Save an AnalysisReport as formatted RFC 8259 JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.to_json(indent=indent), encoding="utf-8")
    return path
