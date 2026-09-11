# Data dictionary

## Terms

A **station** is a gauge on a river or a dam. A **parameter** is what the station
measures, which the portal identifies by a three character **datatype code**:
`HHS` for a river level, `MPS` for rainfall. A **reading** is one number for one
station, one parameter and one moment.

Timestamps are IST throughout, exactly as published, with no conversion.

## What is in the dataset

| File | One row is | Stations | Rows | Period |
| --- | --- | --- | --- | --- |
| `data/stations.csv`, `data/stations.geojson` | a station | 1,747 | 1,747 | current |
| `daily/year=YYYY.parquet` | a station, parameter and day | 1,654 | 34.7 million | 1900 to today, dense from about 1975 |
| `hourly/year=YYYY/month=MM.parquet` | a station, parameter and reading | 1,636 | 58.4 million | a rolling three years |

The two reading tiers hold the same measurements at different resolutions. Daily
covers the whole record, so it is the one to start from. Hourly is about forty
times the size per year, so only the last three years are kept and anything
older survives as its daily summary alone.

One day at the Ganga gauge at Kanpur, in `daily/year=2024.parquet`:

| station_code | datatype_code | variable | unit | date_ist | min | mean | max | sum | n_obs | source_type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 012-MGD2LKN | HHS | water_level | m | 2024-09-12 | 111.59 | 111.647 | 111.7 | 2679.53 | 24 | gauge |

The 24 hourly readings behind it are in `hourly/year=2024/month=09.parquet`.

## stations

The station master, one row per station. Most columns come straight from the
portal and are filled unevenly, so the counts below are worth reading before
joining on any of them.

| Column | What it holds |
| --- | --- |
| `station_code` | The join key, trimmed and upper-cased. One station can appear on the portal under several spellings, and those are merged into a single code here. |
| `name` | Usually a town, barrage or dam. Not unique: 15 names are shared by more than one station, so join on `station_code` instead. |
| `lat`, `lon` | Decimal degrees. Present for 1,746 of the 1,747 stations. |
| `type` | The portal's own classification. `Base` (1,393) and `Level` (208) are river gauges; `Inflow` (146) is a dam or reservoir. The reading tables carry the same split as `source_type`. |
| `nearest_town` | Filled for 128 stations and blank for the rest. |
| `warning_level` | Metres, on the same datum as `water_level`. The level at which the Commission warns. Filled for 1,014 stations. |
| `danger_level` | Metres. The level at which it declares danger, typically a metre above the warning level. Filled for 1,035 stations. |
| `frl` | Full reservoir level in metres: the height a reservoir is licensed to hold. Filled for 149 stations, 140 of them `Inflow`. |
| `mwl` | Maximum water level in metres: the highest the structure is designed to take. Filled for 125 stations. |
| `highest_flow_level` | The highest level the portal lists as ever recorded at this station, in metres. Filled for 1,532 stations, and not recomputed from the readings. |

`stations.geojson` carries the same rows as point features, with `lat` and `lon`
moved into the geometry and the 1 station without coordinates dropped.

## daily

One row per station, parameter and IST calendar day, summarising that day's
readings.

| Column | What it holds |
| --- | --- |
| `station_code`, `source_type` | As in `stations`, where `source_type` is `gauge` or `dam`. |
| `datatype_code` | The portal's code for the parameter. |
| `variable`, `unit` | The code resolved to a name and a unit, or null for the 55 codes listed below that have no published definition. |
| `date_ist` | The calendar day the readings fall on. |
| `min`, `mean`, `max` | Across the day's readings. |
| `sum` | The day's readings added together. This is the number you want for rainfall, where each reading is an increment of the day's total. For a level, a flow or a temperature it is an artefact of how often the station reported, so use `mean` or `max` there. |
| `n_obs` | How many readings the row summarises. Half of all rows rest on 2 readings or fewer and a tenth on 24 or more, because reporting frequency varies by station and has changed over time. |

## hourly

One row per reading, for the last three years.

| Column | What it holds |
| --- | --- |
| `station_code`, `datatype_code`, `variable`, `unit`, `source_type` | As in `daily`. |
| `station_code_raw` | The spelling the portal used before normalisation, such as `012-mgd2lkn` for `012-MGD2LKN`. Kept so a row can be traced back to the request that fetched it. |
| `datetime` | The reading's timestamp. Most stations report on the hour. |
| `value` | The reading, in `unit`. |

## Parameters

The portal publishes no key to its datatype codes. These 26 are mapped here to a
name and a unit; they account for 91% of the daily rows.

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

A further 55 codes appear in the data with no definition to map them to. Rather
than drop the 2.9 million rows they carry, the dataset keeps them with `variable`
set to the lowercased code and `unit` left null. The largest are `MHS`, `MWS`,
`BAT`, `MWI` and `MEP`; the full set is `MHS`, `MWS`, `BAT`, `MWI`, `MEP`, `MTP`,
`MW1`, `MHH`, `HQ2`, `MW2`, `MHA`, `MSD`, `STR`, `GHT`, `MTA`, `GBT`, `MOD`,
`IOR`, `IEP`, `MPT`, `MWA`, `GPC`, `GPR`, `IQ0`, `MOE`, `MPC`, `RH1`, `MSM`,
`HZX`, `GW2`, `GWA`, `GTA`, `GHS`, `GBD`, `GOR`, `IC0`, `IOL`, `IHR`, `MS3`,
`MPD`, `GEP`, `MEW`, `MTU`, `MPI`, `IOS`, `HZA`, `SCT`, `MET`, `INF`, `MWR`,
`HHY`, `MPH`, `QWQ`, `MBS` and `RHR`.

## How a reading gets here

Each API response carries two values for a reading, a raw one and a validated
one. Where both are present the validated value wins, and the raw value is not
kept.

A reading is dropped if it has no timestamp, no value, a timestamp before 1900,
or a timestamp more than two days in the future. Everything else is kept as
published.

## Known problems in the source

These survive into the dataset because correcting them would mean guessing.
Filter for them before analysis.

**Misplaced decimal points in water levels.** Kanpur, whose gauge sits around
108 m, has days reading 1110.98 and 111870. These are rare, roughly 0.3% of that
station's rows, but an annual maximum picks one up every time. Comparing each
reading against its own station's median catches them, since no river varies by
a factor of ten.

**Sentinel values instead of nulls.** `-9990` appears in place of a missing water
level, and large negatives and five-figure totals in place of missing rainfall.
Nothing marks them as absent.

**Datum changes mid-record.** Some stations switch from an absolute elevation to
a gauge-relative reading partway through their history, so their levels drop by
hundreds of metres from one year to the next without any note. Check that a
station's levels are on one scale before plotting its full record.
