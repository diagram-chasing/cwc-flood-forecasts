# Data

The dataset is three Parquet files, rebuilt monthly, whose columns are defined
in [DATA.md](../DATA.md).

| File | One row is | Size | View | Download |
| --- | --- | --- | --- | --- |
| `stations.parquet` | A station | 50 KB | [open](https://hyperparam.app/files?key=https://diagram-chasing.github.io/cwc-flood-forecasts/stations.parquet) | [stations.parquet](https://diagram-chasing.github.io/cwc-flood-forecasts/stations.parquet) |
| `daily.parquet` | A station, parameter and day, 1900 to today | 225 MB | [open](https://hyperparam.app/files?key=https://diagram-chasing.github.io/cwc-flood-forecasts/daily.parquet) | [daily.parquet](https://diagram-chasing.github.io/cwc-flood-forecasts/daily.parquet) |
| `hourly.parquet` | A reading, last three years | 94 MB | [open](https://hyperparam.app/files?key=https://diagram-chasing.github.io/cwc-flood-forecasts/hourly.parquet) | [hourly.parquet](https://diagram-chasing.github.io/cwc-flood-forecasts/hourly.parquet) |

The same files are attached to each monthly
[release](https://github.com/diagram-chasing/cwc-flood-forecasts/releases),
tagged `data-YYYY-MM`, and DuckDB or Polars can read them either by URL or
after downloading:

```sh
gh release download --repo diagram-chasing/cwc-flood-forecasts --pattern '*.parquet'
```

```sql
select * from 'daily.parquet' where station_code = '012-MGD2LKN';
```

Because rows are sorted by `station_code`, `datatype_code` and date in row
groups of one million, a filter on station code reads only a fraction of the
file.
