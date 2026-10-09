import argparse

from datapulse.profiling.profiler import DatasetProfiler
from datapulse.reporting.terminal import display_profile


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Profile a local Parquet dataset."
    )
    parser.add_argument(
        "file_path",
        help="Path to the Parquet file.",
    )

    args = parser.parse_args()
    profiler = DatasetProfiler(args.file_path)
    display_profile(profiler)

if __name__ == "__main__":
    main()