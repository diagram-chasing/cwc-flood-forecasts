"""Readings per month, split by gauge and dam."""

import sys
from pathlib import Path

import polars as pl

DATA = Path(__file__).resolve().parents[3] / "data"

out = (
    pl.scan_parquet(DATA / "daily" / "*.parquet")
    .select("date_ist", "station_code", "source_type")
    .with_columns(
        # A polars Date becomes Arrow Date32, which arrives in JavaScript as
        # days-since-epoch and plots in 1970.
        month=pl.col("date_ist").dt.truncate("1mo").cast(pl.Datetime("ms"))
    )
    .group_by("month", "source_type")
    .agg(rows=pl.len(), stations=pl.col("station_code").n_unique())
    .sort("month", "source_type")
    .collect()
)

out.write_parquet(sys.stdout.buffer)
