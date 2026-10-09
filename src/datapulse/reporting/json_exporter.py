from pathlib import Path

from datapulse.models.report import AnalysisReport


def export_json(
    report: AnalysisReport, output_path: str | Path, indent: int = 2
) -> Path:
    """Save an AnalysisReport as formatted JSON."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.to_json(indent=indent), encoding="utf-8")
    return path
