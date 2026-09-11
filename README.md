# CWC flood forecast system

River levels, discharge, rainfall, temperature and reservoir readings from the
1,747 river gauges and dams the Central Water Commission reports on, scraped
from its [Flood Forecast System portal](https://ffs.india-water.gov.in) and
published as Parquet.

Browse it at
[diagram-chasing.github.io/cwc-flood-forecasts](https://diagram-chasing.github.io/cwc-flood-forecasts/).

The record holds 34.7 million station-parameter-days. It reaches back to 1900
and only becomes dense around 1975, so treat anything earlier as scattered.

## The data

The station master is in this repository as [CSV](data/stations.csv) and
[GeoJSON](data/stations.geojson): one row per station, with coordinates and
whichever of the warning, danger, full reservoir, maximum water and highest
flood levels the Commission publishes for it.

The readings themselves are too large for a repository and are attached to the
monthly [releases](../../releases) instead, in two tiers:

* `daily/year=YYYY.parquet` covers the whole record, one row per station,
  parameter and day, carrying that day's `min`, `mean`, `max`, `sum` and
  reading count. Start here.
* `hourly/year=YYYY/month=MM.parquet` holds the individual readings behind the
  last three years, one row per station, parameter and timestamp. Older ones are
  pruned as they age out.

[DATA.md](DATA.md) defines every column, lists the parameter codes, and describes
the three quality problems in the source worth knowing about before you analyse
anything.

## Building it yourself

Install [uv](https://docs.astral.sh/uv/), then `uv sync`. There are two
commands, and which one you want depends on whether you already have the data.

```sh
uv run python run.py backfill   # every reading from every station, from scratch
uv run python run.py update     # only what is new since the last run
```

`backfill` walks all 1,747 stations and requests their full history, which takes
hours and is what you want on an empty checkout. `update` reads `manifest.json`
to find where each station left off and asks only for readings after that,
re-fetching the last stored day so its daily summary is recomputed over all of
its hours. Overlapping rows are replaced, not duplicated, so running either
command twice is safe.

A [scheduled workflow](.github/workflows/update.yml) runs `update` monthly and
attaches the result to a release.

Add `--limit N` to either command to stop after N stations, which is the quick
way to check that the portal is still answering.

## Licence

The database is offered under the
[Open Database License](https://opendatacommons.org/licenses/odbl/1-0/): use it,
change it and build on it freely, as long as you credit this dataset, release
any adapted database under the same licence, and do not lock it behind DRM
without also offering an unrestricted copy.

The Commission holds copyright in some of the individual readings. The ODbL
covers the database, not every fact inside it, so check with the Commission
before republishing large extracts as its data rather than as yours.

## Source

Everything here comes from the
[Flood Forecast System](https://ffs.india-water.gov.in) portal, which the
Central Water Commission operates. Nothing is modelled, interpolated or
corrected on the way through.

## AI declaration

Code and documentation in this repository were written with AI assistance.
