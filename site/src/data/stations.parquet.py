"""Station master joined to what each station has actually reported."""

import sys
from pathlib import Path

import polars as pl

DATA = Path(__file__).resolve().parents[3] / "data"

STAGE = (pl.col("max").is_between(-100, 5000)) & (~pl.col("max").is_nan())

daily = pl.scan_parquet(DATA / "daily" / "*.parquet")

activity = daily.group_by("station_code").agg(
    rows=pl.len(),
    days=pl.col("date_ist").n_unique(),
    # Named parameters only, so this counts the same thing the page's own
    # parameter total does. Undefined codes carry no unit.
    parameters=pl.col("variable").filter(pl.col("unit").is_not_null()).n_unique(),
    first_date=pl.col("date_ist").min().cast(pl.Utf8),
    last_date=pl.col("date_ist").max().cast(pl.Utf8),
)

level = daily.filter((pl.col("variable") == "water_level") & STAGE)

# Stage carries misplaced decimal points, which a maximum picks up every time.
# Judge each reading against its own station's spread, with a floor so that a
# gauge held at a near constant level does not reject its own floods.
spread = level.group_by("station_code").agg(
    base=pl.col("max").median(),
    span=pl.max_horizontal(
        pl.lit(10.0), 8 * (pl.col("max").quantile(0.75) - pl.col("max").quantile(0.25))
    ),
)

stage = (
    level.join(spread, on="station_code")
    .filter((pl.col("max") - pl.col("base")).abs() <= pl.col("span"))
    .group_by("station_code")
    .agg(level_max=pl.col("max").max(), level_days=pl.col("date_ist").n_unique())
)

out = (
    pl.scan_csv(DATA / "stations.csv")
    .join(activity, on="station_code", how="left")
    .join(stage, on="station_code", how="left")
    .with_columns(
        source_type=pl.when(pl.col("type") == "Inflow")
        .then(pl.lit("dam"))
        .otherwise(pl.lit("gauge")),
        rows=pl.col("rows").fill_null(0),
        days=pl.col("days").fill_null(0),
        parameters=pl.col("parameters").fill_null(0),
        level_days=pl.col("level_days").fill_null(0),
        level_max=pl.col("level_max").round(2),
    )
    .sort("station_code")
    .collect()
)

out.write_parquet(sys.stdout.buffer, compression="zstd", compression_level=19)
