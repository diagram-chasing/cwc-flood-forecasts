"""Water level by day of the year, across every station and every year."""

import sys
from pathlib import Path

import polars as pl

DATA = Path(__file__).resolve().parents[3] / "data"

STAGE = (pl.col("mean").is_between(-100, 5000)) & (~pl.col("mean").is_nan())

level = (
    pl.scan_parquet(DATA / "daily" / "*.parquet")
    .filter((pl.col("variable") == "water_level") & STAGE)
    .select("station_code", "mean", doy=pl.col("date_ist").dt.ordinal_day())
)

# Stage is an absolute elevation, so stations are not comparable until each is
# expressed against its own median. The same subtraction handles the misplaced
# decimal points the source carries: a reading eight interquartile ranges from
# its station's median is a typo, not a flood. Percentiles cannot be rolled up
# client side, so they are computed here.
out = (
    level.join(
        level.group_by("station_code").agg(
            base=pl.col("mean").median(),
            span=pl.max_horizontal(
                pl.lit(10.0),
                8 * (pl.col("mean").quantile(0.75) - pl.col("mean").quantile(0.25)),
            ),
        ),
        on="station_code",
    )
    .with_columns(a=pl.col("mean") - pl.col("base"))
    .filter(pl.col("a").abs() <= pl.col("span"))
    .group_by("doy")
    .agg(
        level_p25=pl.col("a").quantile(0.25),
        level_p50=pl.col("a").median(),
        level_p75=pl.col("a").quantile(0.75),
        stations=pl.col("station_code").n_unique(),
    )
    .sort("doy")
    .collect()
)

out.write_parquet(sys.stdout.buffer)
