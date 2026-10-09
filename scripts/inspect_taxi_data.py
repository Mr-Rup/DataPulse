import sys
from pathlib import Path

import polars as pl

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

file_path = Path("data/raw/yellow_tripdata_2025-01.parquet")
data = pl.scan_parquet(file_path)

print("\n--- Dataset shape ---")
print(data.select(pl.len()).collect())

print("\n--- Column types ---")
print(data.collect_schema())

print("\n--- Pickup and dropoff time diagnostics ---")
time_summary = data.select(
    pl.col("tpep_pickup_datetime").min().alias("earliest_pickup"),
    pl.col("tpep_pickup_datetime").max().alias("latest_pickup"),
    pl.col("tpep_dropoff_datetime").min().alias("earliest_dropoff"),
    pl.col("tpep_dropoff_datetime").max().alias("latest_dropoff"),
    (
        pl.col("tpep_dropoff_datetime")
        < pl.col("tpep_pickup_datetime")
    ).sum().alias("negative_duration_rows"),
).collect()

print(time_summary)

print("\n--- Numeric column diagnostics ---")
numeric_summary = data.select(
    pl.col("trip_distance").min().alias("min_distance"),
    (pl.col("trip_distance") <= 0).sum().alias("nonpositive_distance_rows"),
    pl.col("fare_amount").min().alias("min_fare"),
    (pl.col("fare_amount") < 0).sum().alias("negative_fare_rows"),
    pl.col("total_amount").min().alias("min_total"),
    (pl.col("total_amount") < 0).sum().alias("negative_total_rows"),
).collect()

print(numeric_summary)


print("\n--- Examples: negative trip duration ---")

negative_duration_examples = (
    data.filter(
        pl.col("tpep_dropoff_datetime")
        < pl.col("tpep_pickup_datetime")
    )
    .select(
        "VendorID",
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "trip_distance",
        "fare_amount",
        "total_amount",
    )
    .limit(10)
    .collect()
)

print(negative_duration_examples)


print("\n--- Distance quality breakdown ---")

distance_summary = data.select(
    (pl.col("trip_distance") == 0).sum().alias("zero_distance_rows"),
    (pl.col("trip_distance") < 0).sum().alias("negative_distance_rows"),
    pl.col("trip_distance").is_null().sum().alias("null_distance_rows"),
).collect()

print(distance_summary)


print("\n--- Examples: negative fares ---")

negative_fare_examples = (
    data.filter(pl.col("fare_amount") < 0)
    .select(
        "VendorID",
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "trip_distance",
        "fare_amount",
        "total_amount",
        "payment_type",
    )
    .limit(10)
    .collect()
)

print(negative_fare_examples)

print("\n--- Negative fares by payment type ---")

negative_fare_breakdown = (
    data.filter(pl.col("fare_amount") < 0)
    .group_by("payment_type")
    .agg(
        pl.len().alias("negative_fare_rows"),
        pl.col("total_amount").mean().alias("mean_total_amount"),
        pl.col("fare_amount").min().alias("minimum_fare"),
    )
    .sort("negative_fare_rows", descending=True)
    .collect()
)

print(negative_fare_breakdown)


print("\n--- Negative fares with positive total amounts ---")

inconsistent_amounts = (
    data.filter(
        (pl.col("fare_amount") < 0)
        & (pl.col("total_amount") > 0)
    )
    .select(
        "payment_type",
        "fare_amount",
        "total_amount",
        "trip_distance",
    )
    .limit(10)
    .collect()
)

print(inconsistent_amounts)
