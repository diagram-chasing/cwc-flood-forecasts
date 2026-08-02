from datetime import datetime
from pathlib import Path

import polars as pl

from fetch import DATATYPES

MIN_YEAR = 1900
HOURLY_YEARS = 3

_META = pl.DataFrame(
    [(c, v[0], v[1], v[2]) for c, v in DATATYPES.items()],
    schema=["datatype_code", "variable", "unit", "kind"],
    orient="row",
)


def normalize(rows, types=None):
    recs = []
    for r in rows:
        i = r["id"]
        value = r.get("dataValidatedValue")
        if value is None:
            value = r.get("dataValue")
        recs.append((i["stationCode"], i["datatypeCode"], i["dataTime"], value))
    if not recs:
        return pl.DataFrame()
    df = pl.DataFrame(recs, schema=["station_code_raw", "datatype_code", "datetime", "value"], orient="row")
    df = df.with_columns(
        pl.col("station_code_raw").str.strip_chars().str.to_uppercase().alias("station_code"),
        pl.col("datetime").str.to_datetime("%Y-%m-%dT%H:%M:%S", strict=False),
        pl.col("value").cast(pl.Float64, strict=False),
    )
    cutoff = datetime.now().replace(microsecond=0)
    df = df.filter(
        pl.col("datetime").is_not_null()
        & pl.col("value").is_not_null()
        & (pl.col("datetime").dt.year() >= MIN_YEAR)
        & (pl.col("datetime") <= pl.lit(cutoff).dt.offset_by("2d"))
    )
    df = df.join(_META, on="datatype_code", how="left").with_columns(
        pl.col("variable").fill_null(pl.col("datatype_code").str.to_lowercase()),
        pl.col("kind").fill_null(pl.lit("stat")),
    )
    st = (types or {})
    df = df.with_columns(
        pl.col("station_code").replace_strict(st, default="gauge").alias("source_type")
    )
    return df


def daily(df):
    return (
        df.with_columns(pl.col("datetime").dt.date().alias("date_ist"))
        .group_by(["station_code", "datatype_code", "variable", "unit", "source_type", "date_ist"])
        .agg(
            pl.col("value").min().alias("min"),
            pl.col("value").mean().alias("mean"),
            pl.col("value").max().alias("max"),
            pl.col("value").sum().alias("sum"),
            pl.len().alias("n_obs"),
        )
        .sort(["station_code", "datatype_code", "date_ist"])
    )


def hourly(df):
    cutoff = datetime.now().replace(year=datetime.now().year - HOURLY_YEARS)
    return (
        df.filter(pl.col("datetime") >= pl.lit(cutoff))
        .select(["station_code", "station_code_raw", "datetime", "datatype_code",
                 "variable", "unit", "value", "source_type"])
        .sort(["station_code", "datatype_code", "datetime"])
    )


def _upsert(new, path, keys):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = pl.read_parquet(path).join(new.select(keys).unique(), on=keys, how="anti")
        new = pl.concat([old, new], how="diagonal")
    new.sort(keys).write_parquet(path)


def write_daily(df, root):
    keys = ["station_code", "datatype_code", "date_ist"]
    for (year,), part in df.group_by(pl.col("date_ist").dt.year().alias("y"), maintain_order=True):
        _upsert(part, Path(root) / "daily" / f"year={year}.parquet", keys)


def write_hourly(df, root):
    keys = ["station_code", "datatype_code", "datetime"]
    for (year, month), part in df.group_by(pl.col("datetime").dt.year().alias("y"),
                                           pl.col("datetime").dt.month().alias("m"), maintain_order=True):
        _upsert(part, Path(root) / "hourly" / f"year={year}" / f"month={month:02d}.parquet", keys)


def prune_hourly(root):
    cutoff = datetime.now().year - HOURLY_YEARS
    for d in (Path(root) / "hourly").glob("year=*"):
        if int(d.name.split("=")[1]) < cutoff:
            for f in d.glob("*.parquet"):
                f.unlink()
            d.rmdir()
