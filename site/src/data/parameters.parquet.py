"""One row per parameter: how much of it there is and how many stations report it."""

import sys
from pathlib import Path

import polars as pl

DATA = Path(__file__).resolve().parents[3] / "data"

out = (
    pl.scan_parquet(DATA / "daily" / "*.parquet")
    .select("date_ist", "station_code", "variable", "unit")
    .with_columns(
        # The 55 codes the portal publishes no definition for arrive with no
        # unit. Fold them into one row rather than listing all 55.
        variable=pl.when(pl.col("unit").is_null())
        .then(pl.lit("undefined code"))
        .otherwise(pl.col("variable")),
        unit=pl.col("unit").fill_null(""),
    )
    .group_by("variable")
    .agg(
        rows=pl.len(),
        stations=pl.col("station_code").n_unique(),
        unit=pl.col("unit").first(),
        first_year=pl.col("date_ist").min().dt.year(),
        last_year=pl.col("date_ist").max().dt.year(),
    )
    .sort("rows", descending=True)
    .collect()
)

out.write_parquet(sys.stdout.buffer)
