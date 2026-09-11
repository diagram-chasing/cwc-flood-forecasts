# CWC flood forecast system

Water level, discharge, rainfall, temperature and reservoir readings from the
1,747 river gauges and dams on India's Central Water Commission
[Flood Forecast System](https://ffs.india-water.gov.in) portal, scraped and
published as Parquet.

Browse the data at
[diagram-chasing.github.io/cwc-flood-forecasts](https://diagram-chasing.github.io/cwc-flood-forecasts/).

## Files

| File | One row is | Size |
| --- | --- | --- |
| `stations.parquet` | A station, with coordinates and published thresholds | 50 KB |
| `daily.parquet` | A station, parameter and day: `min`, `mean`, `max`, `sum`, `n_obs` | 225 MB |
| `hourly.parquet` | A reading, last three years only | 94 MB |

Start with daily, which runs from 1900 to today but is sparse before 1975.
[data/README.md](data/README.md) has links to view or download each file, and
[DATA.md](DATA.md) explains every column along with the known problems in the
source data.

## Build the dataset

Install [uv](https://docs.astral.sh/uv/), then:

```sh
uv sync
uv run python run.py backfill   # full history for every station; takes hours
uv run python run.py update     # only readings newer than manifest.json
uv run python run.py publish    # flatten data/ into dist/*.parquet
```

Both commands can be re-run safely, since overlapping rows are replaced rather
than duplicated. Add `--limit N` to stop after N stations. A
[workflow](.github/workflows/update.yml) runs `update` on the first of each
month and attaches the result to a release.

## Licence

The dataset is released under the
[Open Database License](https://opendatacommons.org/licenses/odbl/1-0/). The
underlying readings belong to the Central Water Commission, so credit them when
you use the data.

Code and documentation were written with AI assistance.
