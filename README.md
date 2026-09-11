# CWC flood forecast system

Readings from the 1,747 river gauges and dams that India's Central Water
Commission publishes on its [Flood Forecast System](https://ffs.india-water.gov.in)
portal: water level, discharge, rainfall, temperature and reservoir state.
Scraped, normalised and published as Parquet.

Browse the data at
[diagram-chasing.github.io/cwc-flood-forecasts](https://diagram-chasing.github.io/cwc-flood-forecasts/).

## Files

| File | Rows | Where |
| --- | --- | --- |
| `data/stations.csv`, `data/stations.geojson` | One per station, with coordinates and published thresholds | This repository |
| `daily/year=YYYY.parquet` | One per station, parameter and day: `min`, `mean`, `max`, `sum`, `n_obs` | Monthly [releases](../../releases) |
| `hourly/year=YYYY/month=MM.parquet` | One per reading, last three years only | Monthly [releases](../../releases) |

Daily covers 1900 to today, but is sparse before 1975. Start there.
[DATA.md](DATA.md) defines every column and lists the known defects in the
source.

## Build the dataset

Install [uv](https://docs.astral.sh/uv/), then:

```sh
uv sync
uv run python run.py backfill   # full history for every station; takes hours
uv run python run.py update     # only readings newer than manifest.json
```

`update` re-fetches the last stored day so its daily summary is complete. Both
commands replace overlapping rows, so re-running is safe. Add `--limit N` to
stop after N stations.

A [workflow](.github/workflows/update.yml) runs `update` on the first of each
month and attaches the result to a release.

## Licence

[Open Database License](https://opendatacommons.org/licenses/odbl/1-0/). The
Commission may hold copyright in individual readings; the licence covers the
database, not every fact in it.

Nothing is modelled, interpolated or corrected. Code and documentation were
written with AI assistance.
