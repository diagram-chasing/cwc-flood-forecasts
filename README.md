# flood-forecast-system

Tidy dataset of river water level, discharge, rainfall, temperature and reservoir
readings published by the [Central Water Commission](https://ffs.india-water.gov.in)
on its Flood Forecast System portal.

Each reading is a measurement taken at a CWC river gauge or dam, covering ~1,900
stations across India and 25 parameters. Records reach back to the 1960s for some
stations.

View the raw dataset on the [Releases](../../releases) page.

## Data

The station master is published in the repository as
[CSV](data/stations.csv) and [GeoJSON](data/stations.geojson), one row per station
with coordinates and flood thresholds (warning, danger, FRL, MWL, highest flood level).

The readings are published as [Parquet](../../releases) on the Releases page, in two
tiers:

* `daily/year=YYYY.parquet` - full history, one row per station, parameter and day,
  carrying `min`, `mean`, `max`, `sum` and observation count. Use `sum` for rainfall
  and `min`/`mean`/`max` for levels and flows.
* `hourly/year=YYYY/month=MM.parquet` - native sub-daily readings, last three years
  only, one row per station, parameter and timestamp.

See [DATA.md](DATA.md) for the schema and data dictionary.

## Generate

Install [uv](https://docs.astral.sh/uv/), then run:

```sh
uv sync
uv run python run.py backfill
uv run python run.py update
```

## License

This flood-forecast-system dataset is made available under the
[Open Database License](https://opendatacommons.org/licenses/odbl/1-0/).

Some individual contents of the database are under copyright by the Central Water
Commission.

You are free:

* **To share**: To copy, distribute and use the database.
* **To create**: To produce works from the database.
* **To adapt**: To modify, transform and build upon the database.

As long as you:

* **Attribute**: You must attribute any public use of the database, or works produced from the database, in the manner specified in the ODbL. For any use or redistribution of the database, or works produced from it, you must make clear to others the license of the database and keep intact any notices on the original database.
* **Share-Alike**: If you publicly use any adapted version of this database, or works produced from an adapted database, you must also offer that adapted database under the ODbL.
* **Keep open**: If you redistribute the database, or an adapted version of it, then you may use technological measures that restrict the work (such as DRM) as long as you also redistribute a version without such measures.

## Source

The data comes from the [Flood Forecast System](https://ffs.india-water.gov.in)
portal operated by the Central Water Commission.

## AI declaration

Code and documentation in this repository were written with AI assistance.
