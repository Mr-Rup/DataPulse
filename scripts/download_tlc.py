import argparse
import sys
import urllib.request
from pathlib import Path

TLC_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"


def download_file(url: str, destination: Path, force: bool = False) -> None:
    """Download a remote file with progress reporting."""

    if destination.exists() and not force:
        print(f"File already exists: {destination} (use --force to redownload)")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading: {url} -> {destination}")

    def progress_hook(block_num: int, block_size: int, total_size: int) -> None:
        downloaded = block_num * block_size
        if total_size > 0:
            percentage = min(100.0, (downloaded / total_size) * 100)
            downloaded_mb = downloaded / (1024 ** 2)
            total_mb = total_size / (1024 ** 2)
            sys.stdout.write(
                f"\rProgress: {percentage:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)"
            )
            sys.stdout.flush()
        else:
            downloaded_mb = downloaded / (1024 ** 2)
            sys.stdout.write(f"\rDownloaded: {downloaded_mb:.1f} MB")
            sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, destination, reporthook=progress_hook)
        print("\nDownload complete.")
    except Exception as exc:
        print(f"\nDownload failed: {exc}")
        if destination.exists():
            destination.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download NYC TLC taxi trip datasets and lookup files."
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Target year (default: 2025).",
    )
    parser.add_argument(
        "--month",
        type=int,
        default=1,
        help="Target month (default: 1).",
    )
    parser.add_argument(
        "--dest-dir",
        type=str,
        default="data/raw",
        help="Destination directory (default: data/raw).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force redownload even if file exists.",
    )
    parser.add_argument(
        "--skip-lookup",
        action="store_true",
        help="Skip downloading taxi_zone_lookup.csv.",
    )

    args = parser.parse_args()
    dest_dir = Path(args.dest_dir)

    parquet_filename = f"yellow_tripdata_{args.year}-{args.month:02d}.parquet"
    parquet_url = f"{TLC_BASE_URL}/{parquet_filename}"
    parquet_dest = dest_dir / parquet_filename

    download_file(parquet_url, parquet_dest, force=args.force)

    if not args.skip_lookup:
        lookup_dest = dest_dir / "taxi_zone_lookup.csv"
        download_file(LOOKUP_URL, lookup_dest, force=args.force)


if __name__ == "__main__":
    main()
