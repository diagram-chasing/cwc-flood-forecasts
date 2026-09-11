"""One row per station and year: the year's highest water level, how many days
it ran above the danger level, and the rainfall it caught."""

import sys
from pathlib import Path

import polars as pl

DATA = Path(__file__).resolve().parents[3] / "data"

# The source writes sentinels rather than nulls: -9990 for a missing stage,
# large negatives and five-figure totals for a missing rainfall reading.
RAIN = (pl.col("sum").is_between(0, 1000)) & (~pl.col("sum").is_nan())
STAGE = (pl.col("max").is_between(-100, 5000)) & (~pl.col("max").is_nan())

daily = pl.scan_parquet(DATA / "daily" / "*.parquet").with_columns(
    year=pl.col("date_ist").dt.year()
)

stations = pl.scan_csv(DATA / "stations.csv").select("station_code", "danger_level")

level = daily.filter((pl.col("variable") == "water_level") & STAGE)

# Stage also carries misplaced decimal points, which an annual maximum picks up
# every time: Kanpur reads 1110.98 m against a danger level of 114 m. Judge each
# reading against its own station's spread, with a floor so that a gauge held at
# a near constant level does not reject its own floods.
spread = level.group_by("station_code").agg(
    base=pl.col("max").median(),
    span=pl.max_horizontal(
        pl.lit(10.0), 8 * (pl.col("max").quantile(0.75) - pl.col("max").quantile(0.25))
    ),
)

days = daily.group_by("station_code", "year").agg(days=pl.col("date_ist").n_unique())

stage = (
    level.join(spread, on="station_code")
    .join(stations, on="station_code", how="left")
    .filter((pl.col("max") - pl.col("base")).abs() <= pl.col("span"))
    .group_by("station_code", "year")
    .agg(
        level_max=pl.col("max").max(),
        danger_days=pl.col("date_ist")
        .filter(pl.col("max") >= pl.col("danger_level"))
        .n_unique(),
    )
)

rain = (
    daily.filter((pl.col("variable") == "rainfall") & RAIN)
    .group_by("station_code", "year")
    .agg(rainfall=pl.col("sum").sum())
)

out = (
    days.join(stage, on=["station_code", "year"], how="left")
    .join(rain, on=["station_code", "year"], how="left")
    .with_columns(
        # This is the one file with real row count behind it, so it is typed down
        # to the source's own precision to stay inside the page's size budget.
        pl.col("level_max").round(2).cast(pl.Float32),
        pl.col("rainfall").round(0).cast(pl.Int32),
        pl.col("year").cast(pl.Int16),
        pl.col("days", "danger_days").cast(pl.UInt16),
    )
    .sort("station_code", "year")
    .collect()
)

out.write_parquet(sys.stdout.buffer, compression="zstd", compression_level=19)
