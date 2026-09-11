# Data dictionary

A **station** is a river gauge or a dam. A **parameter** is one thing a station
measures, identified by a three-letter **datatype code** such as `HHS` (water
level) or `MPS` (rainfall). A **reading** is one value for one station, one
parameter and one timestamp.

All timestamps are IST, as published.

## Files

| File | One row is | Stations | Rows | Period |
| --- | --- | --- | --- | --- |
| `data/stations.csv`, `data/stations.geojson` | A station | 1,747 | 1,747 | Current |
| `daily/year=YYYY.parquet` | A station, parameter and day | 1,654 | 34.7 M | 1900 to today, dense from 1975 |
| `hourly/year=YYYY/month=MM.parquet` | A reading | 1,636 | 58.4 M | Last three years |

Daily and hourly hold the same readings at different resolutions. Hourly rows
older than three years are dropped; their daily summaries remain.

Example, one day at the Ganga gauge at Kanpur in `daily/year=2024.parquet`:

| station_code | datatype_code | variable | unit | date_ist | min | mean | max | sum | n_obs | source_type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 012-MGD2LKN | HHS | water_level | m | 2024-09-12 | 111.59 | 111.647 | 111.7 | 2679.53 | 24 | gauge |

## stations

Columns come from the portal and are unevenly filled. Counts are stations with
a value.

| Column | Description | Filled |
| --- | --- | --- |
| `station_code` | Join key. Trimmed and upper-cased; variant spellings on the portal are merged. | 1,747 |
| `name` | Town, barrage or dam. Not unique: 15 names cover more than one station. | 1,747 |
| `lat`, `lon` | Decimal degrees. | 1,746 |
| `type` | Portal classification. `Base` (1,393) and `Level` (208) are river gauges; `Inflow` (146) is a dam. Reading tables carry this as `source_type`. | 1,747 |
| `nearest_town` | | 128 |
| `warning_level` | Metres, same datum as `water_level`. | 1,014 |
| `danger_level` | Metres, typically 1 m above `warning_level`. | 1,035 |
| `frl` | Full reservoir level, metres. | 149 |
| `mwl` | Maximum water level, metres. | 125 |
| `highest_flow_level` | Highest level the portal reports for the station, metres. Not recomputed from readings. | 1,532 |

`stations.geojson` has the same rows as point features and omits the one
station without coordinates.

## daily

One row per station, parameter and IST calendar day.

| Column | Description |
| --- | --- |
| `station_code`, `source_type` | As in `stations`. `source_type` is `gauge` or `dam`. |
| `datatype_code` | Portal parameter code. |
| `variable`, `unit` | Resolved name and unit, or null for the 55 undefined codes listed under [Parameters](#parameters). |
| `date_ist` | Calendar day. |
| `min`, `mean`, `max` | Over the day's readings. |
| `sum` | Total of the day's readings. Correct for rainfall, where readings are increments. Meaningless for levels, flows and temperatures; use `mean` or `max`. |
| `n_obs` | Number of readings. Half of all rows have 2 or fewer, a tenth have 24 or more. |

## hourly

One row per reading, last three years.

| Column | Description |
| --- | --- |
| `station_code`, `datatype_code`, `variable`, `unit`, `source_type` | As in `daily`. |
| `station_code_raw` | Spelling used by the portal before normalisation, for tracing a row to its request. |
| `datetime` | Reading timestamp. Most stations report hourly. |
| `value` | Reading, in `unit`. |

## Parameters

The portal publishes no key for its codes. These 26 are mapped and cover 91% of
daily rows.

| Code | Variable | Unit |
| --- | --- | --- |
| `HHS`, `HHA`, `HHX`, `HHT`, `HZS`, `HZF` | water_level | m |
| `HQ0` | discharge | cumec |
| `HTW`, `MTW` | water_temp | degC |
| `MPS`, `MPA`, `MPM`, `MPN` | rainfall | mm |
| `MTN` | air_temp_min | degC |
| `MTX` | air_temp_max | degC |
| `MTD` | air_temp | degC |
| `FIN` | reservoir_inflow | cumec |
| `FOU`, `FOL` | reservoir_outflow | cumec |
| `IBD`, `ISD` | reservoir_storage | mcm |
| `IWA`, `IW2`, `IHS` | reservoir_level | m |
| `ITA` | reservoir_area | sqkm |
| `IPC` | reservoir_percent | pct |

55 further codes (2.9 M rows) have no known definition. They are kept with
`variable` set to the lowercased code and `unit` null. In descending row count:
`MHS`, `MWS`, `BAT`, `MWI`, `MEP`, `MTP`, `MW1`, `MHH`, `HQ2`, `MW2`, `MHA`,
`MSD`, `STR`, `GHT`, `MTA`, `GBT`, `MOD`, `IOR`, `IEP`, `MPT`, `MWA`, `GPC`,
`GPR`, `IQ0`, `MOE`, `MPC`, `RH1`, `MSM`, `HZX`, `GW2`, `GWA`, `GTA`, `GHS`,
`GBD`, `GOR`, `IC0`, `IOL`, `IHR`, `MS3`, `MPD`, `GEP`, `MEW`, `MTU`, `MPI`,
`IOS`, `HZA`, `SCT`, `MET`, `INF`, `MWR`, `HHY`, `MPH`, `QWQ`, `MBS`, `RHR`.

## Processing

Each API record carries a raw and a validated value. The validated value is
kept when present; the raw value is discarded.

A reading is dropped if it has no timestamp, no value, a timestamp before 1900,
or a timestamp more than two days in the future. Nothing else is changed.
