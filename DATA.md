# Data dictionary

Timestamps are IST clock time as published by the source. `station_code` is normalized
(trimmed, upper-cased); case and whitespace variants of the same station are merged.
`source_type` is `gauge` or `dam`.

## stations

Station master, one row per station.

| Column | Description |
| --- | --- |
| `station_code` | Station identifier |
| `name` | Station name |
| `lat`, `lon` | Coordinates (decimal degrees) |
| `type` | Station type (`Base`, `Level`, `Inflow`) |
| `nearest_town` | Nearest town |
| `warning_level` | Warning level (m) |
| `danger_level` | Danger level (m) |
| `frl` | Full reservoir level (m) |
| `mwl` | Maximum water level (m) |
| `highest_flow_level` | Highest flood level on record (m) |

## daily

Full history, one row per station, parameter and day.

| Column | Description |
| --- | --- |
| `station_code` | Station identifier |
| `datatype_code` | Source parameter code (see below) |
| `variable` | Parameter name |
| `unit` | Unit of measurement |
| `date_ist` | Date (IST) |
| `min`, `mean`, `max`, `sum` | Daily aggregates of the readings |
| `n_obs` | Number of readings in the day |
| `source_type` | `gauge` or `dam` |

Use `sum` for rainfall and `min`/`mean`/`max` for levels, flows and temperature.

## hourly

Native sub-daily readings, last three years only, one row per station, parameter and
timestamp.

| Column | Description |
| --- | --- |
| `station_code` | Station identifier |
| `station_code_raw` | Station identifier as stored by the source |
| `datetime` | Timestamp (IST) |
| `datatype_code` | Source parameter code (see below) |
| `variable` | Parameter name |
| `unit` | Unit of measurement |
| `value` | Reading |
| `source_type` | `gauge` or `dam` |

## Parameters

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

Codes outside this table are carried through with the variable set to the lowercased
code and no unit.
