import argparse
from pathlib import Path

from datapulse.api import analyze
from datapulse.reporting.terminal import display_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile a dataset with DataPulse.")
    parser.add_argument("file_path", help="Path to dataset file.")
    parser.add_argument(
        "--format",
        choices=["terminal", "html", "json"],
        default="terminal",
        help="Report output format.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save report output.",
    )

    args = parser.parse_args()
    report = analyze(args.file_path)

    if args.format == "terminal":
        display_report(report)
    elif args.format == "html":
        out = Path(args.output) if args.output else Path("report.html")
        report.save_html(out)
        print(f"Report saved to {out}")
    elif args.format == "json":
        if args.output:
            report.save_json(args.output)
            print(f"JSON saved to {args.output}")
        else:
            print(report.to_json())


if __name__ == "__main__":
    main()
