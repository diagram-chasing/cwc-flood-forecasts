# Data dictionary

A **station** is a river gauge or a dam, and a **parameter** is one thing it
measures, identified by a three-letter **datatype code** such as `HHS` for water
level or `MPS` for rainfall. A **reading** is one value for one station, one
parameter and one timestamp, and all timestamps are IST as published.

## Files

| File | One row is | Stations | Rows | Period |
| --- | --- | --- | --- | --- |
| `stations.parquet` | A station | 1,747 | 1,747 | Current |
| `daily.parquet` | A station, parameter and day | 1,654 | 34.7 M | 1900 to today, dense from 1975 |
| `hourly.parquet` | A reading | 1,636 | 58.4 M | Last three years |

Daily and hourly hold the same readings at different resolutions, but hourly
rows older than three years are dropped while their daily summaries remain.

For example, one day at the Ganga gauge at Kanpur in `daily.parquet`:

| station_code | datatype_code | variable | unit | date_ist | min | mean | max | sum | n_obs | source_type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 012-MGD2LKN | HHS | water_level | m | 2024-09-12 | 111.59 | 111.647 | 111.7 | 2679.53 | 24 | gauge |

## stations

Columns come from the portal and are unevenly filled, so the last column gives
the number of stations with a value.

| Column | Description | Filled |
| --- | --- | --- |
| `station_code` | Join key, trimmed and upper-cased, with variant spellings from the portal merged. | 1,747 |
| `name` | Town, barrage or dam. Not unique, since 15 names cover more than one station. | 1,747 |
| `lat`, `lon` | Decimal degrees. | 1,746 |
| `type` | Portal classification, where `Base` (1,393) and `Level` (208) are river gauges and `Inflow` (146) is a dam. Reading tables carry this as `source_type`. | 1,747 |
| `nearest_town` | | 128 |
| `warning_level` | Metres, on the same datum as `water_level`. | 1,014 |
| `danger_level` | Metres, typically 1 m above `warning_level`. | 1,035 |
| `frl` | Full reservoir level, metres. | 149 |
| `mwl` | Maximum water level, metres. | 125 |
| `highest_flow_level` | Highest level the portal reports for the station, metres, not recomputed from readings. | 1,532 |

The repository also holds the same rows as `data/stations.csv` and
`data/stations.geojson`, although the GeoJSON omits the one station without
coordinates.

## daily

One row per station, parameter and IST calendar day.

| Column | Description |
| --- | --- |
| `station_code`, `source_type` | As in `stations`, where `source_type` is `gauge` or `dam`. |
| `datatype_code` | Portal parameter code. |
| `variable`, `unit` | Resolved name and unit, or null for the 55 undefined codes listed under [Parameters](#parameters). |
| `date_ist` | Calendar day. |
| `min`, `mean`, `max` | Over the day's readings. |
| `sum` | Total of the day's readings, which is correct for rainfall because each reading is an increment, but meaningless for levels, flows and temperatures, where `mean` or `max` is the right choice. |
| `n_obs` | Number of readings behind the row. Half of all rows have 2 or fewer while a tenth have 24 or more. |

## hourly

One row per reading for the last three years.

| Column | Description |
| --- | --- |
| `station_code`, `datatype_code`, `variable`, `unit`, `source_type` | As in `daily`. |
| `station_code_raw` | Spelling used by the portal before normalisation, so a row can be traced to its request. |
| `datetime` | Reading timestamp. Most stations report hourly. |
| `value` | Reading, in `unit`. |

## Parameters

The portal publishes no key for its codes, so these 26 were mapped by hand and
cover 91% of daily rows.

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

A further 55 codes, carrying 2.9 M rows, have no known definition, so they are
kept with `variable` set to the lowercased code and `unit` null. In descending
row count they are `MHS`, `MWS`, `BAT`, `MWI`, `MEP`, `MTP`, `MW1`, `MHH`,
`HQ2`, `MW2`, `MHA`, `MSD`, `STR`, `GHT`, `MTA`, `GBT`, `MOD`, `IOR`, `IEP`,
`MPT`, `MWA`, `GPC`, `GPR`, `IQ0`, `MOE`, `MPC`, `RH1`, `MSM`, `HZX`, `GW2`,
`GWA`, `GTA`, `GHS`, `GBD`, `GOR`, `IC0`, `IOL`, `IHR`, `MS3`, `MPD`, `GEP`,
`MEW`, `MTU`, `MPI`, `IOS`, `HZA`, `SCT`, `MET`, `INF`, `MWR`, `HHY`, `MPH`,
`QWQ`, `MBS` and `RHR`.

## Processing

Each API record carries a raw and a validated value, and the validated one is
kept whenever it is present. A reading is dropped if it has no timestamp, no
value, a timestamp before 1900, or a timestamp more than two days in the
future, but nothing else is changed.

## Known defects

These are in the source and pass through unchanged, so filter for them before
analysis.

- **Misplaced decimal points.** Kanpur, which sits near 108 m, has days at
  1110.98 and 111870. Although these are only about 0.3% of that station's rows,
  every annual maximum catches one, so compare each reading to its station's
  median.
- **Sentinels instead of nulls.** `-9990` stands in for a missing water level,
  while large negatives and five-figure totals stand in for missing rainfall.
- **Datum changes.** Some stations switch from absolute elevation to
  gauge-relative levels mid-record, so their levels drop by hundreds of metres
  between years. Check that a station is on one scale before plotting its full
  record.
