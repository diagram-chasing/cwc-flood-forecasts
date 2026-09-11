---
title: CWC flood forecast system
---

```js
import {feature, merge} from "npm:topojson-client@3.1.0";
```

```js
// Arrow returns row proxies and epoch milliseconds; make both plain JavaScript.
function rows(table) {
  return table.toArray().map((row) => {
    const d = row.toJSON();
    if (d.month != null) d.month = new Date(d.month);
    return d;
  });
}

const coverage = rows(await FileAttachment("data/coverage.parquet").parquet());
const parameters = rows(await FileAttachment("data/parameters.parquet").parquet());
const seasonal = rows(await FileAttachment("data/seasonal.parquet").parquet());
const stations = rows(await FileAttachment("data/stations.parquet").parquet());
const stationAnnual = rows(await FileAttachment("data/station-annual.parquet").parquet());
const topology = await FileAttachment("data/india-states.topo.json").json();
const states = feature(topology, topology.objects.states);
const outline = merge(topology, topology.objects.states.geometries);
```

```js
const readings = d3.sum(coverage, (d) => d.rows);
const latest = d3.max(stations, (d) => d.last_date);
const named = parameters.filter((d) => d.unit).length;

const integer = d3.format(",");
const decimal = d3.format(",.2f");

// Water rises through these: the river, then the two levels the Commission
// forecasts against, then the rain that drives both.
const WATER = "var(--water)";
const DEEP = "var(--water-deep)";
const RAIN = "var(--rain)";
const WARNING = "var(--warning)";
const DANGER = "var(--danger)";
const FAINT = "var(--theme-foreground-faintest)";

// Before 1965 the record is 67,000 scattered readings, a fifth of a percent of
// the whole. Charting from 1900 would flatten everything after it.
const since = new Date(Date.UTC(1965, 0, 1));
const sinceYear = 1965;
const thisYear = d3.max(coverage, (d) => d.month).getUTCFullYear();
const years = [sinceYear, thisYear];

const percent = d3.format(".0%");

// Day of the year onto a leap year, so the axis ticks read as months. The year
// is scaffolding, so the tooltip prints the day and month only.
const doy = (d) => new Date(Date.UTC(2020, 0, d.doy));
const wholeYear = [new Date(Date.UTC(2020, 0, 1)), new Date(Date.UTC(2020, 11, 31))];
const dayLabel = d3.utcFormat("%-d %B");
const metres = (d) => `${d > 0 ? "+" : ""}${d3.format(".2f")(d)} m`;

// Only a station with a published danger level can be counted against it, and
// only in a year it reported a water level at all.
const gauged = new Set(stations.filter((d) => d.danger_level != null).map((d) => d.station_code));
const dangerYears = d3
  .rollups(
    stationAnnual.filter((d) => d.year >= sinceYear && d.level_max != null && gauged.has(d.station_code)),
    (v) => ({
      crossed: v.filter((d) => d.danger_days > 0).length,
      below: v.filter((d) => d.danger_days === 0).length
    }),
    (d) => d.year
  )
  .flatMap(([year, v]) => [
    {year, outcome: "Crossed its danger level", stations: v.crossed, share: v.crossed / (v.crossed + v.below)},
    {year, outcome: "Stayed below", stations: v.below, share: v.below / (v.crossed + v.below)}
  ])
  .sort((a, b) => d3.ascending(a.year, b.year));

const dangerColor = {
  domain: ["Crossed its danger level", "Stayed below"],
  range: [DANGER, DEEP],
  legend: true,
  label: null
};

const sourceColor = {domain: ["gauge", "dam"], range: [WATER, DEEP], legend: true, label: null};
```

# CWC flood forecast system

<div class="lede">
  Every daily reading from a Central Water Commission river gauge or dam since 1900,
  as published on the Commission's Flood Forecast System portal.
</div>

<div class="grid grid-cols-4">
  <div class="card">
    <h2>Stations</h2>
    <p class="big">${integer(stations.length)}</p>
  </div>
  <div class="card">
    <h2>Daily readings</h2>
    <p class="big">${integer(readings)}</p>
  </div>
  <div class="card">
    <h2>Named parameters</h2>
    <p class="big">${named}</p>
  </div>
  <div class="card">
    <h2>Latest reading</h2>
    <p class="big small">${latest}</p>
  </div>
</div>

<div class="grid grid-cols-2">
  <div class="card">
    <h2>Stations</h2>
    ${resize((width) => Plot.plot({
      width,
      height: 400,
      projection: {type: "mercator", domain: outline, inset: 4},
      marks: [
        Plot.geo(states, {fill: "var(--theme-background-alt)", stroke: "var(--theme-background)", strokeWidth: 0.4}),
        Plot.geo(outline, {stroke: FAINT, strokeWidth: 0.8}),
        Plot.dot(stations.filter((d) => d.lat != null), {
          x: "lon",
          y: "lat",
          r: 2.4,
          fill: WATER,
          fillOpacity: 0.75,
          channels: {Station: "name", Code: "station_code", Days: "days"},
          tip: {format: {x: null, y: null, Days: integer}}
        })
      ]
    }))}
  </div>
  <div class="card">
    <h2>Readings per month</h2>
    <h3>From 1965, where the record becomes continuous</h3>
    ${resize((width) => Plot.plot({
      width,
      height: 400,
      marginLeft: 56,
      x: {label: null, domain: [since, d3.max(coverage, (d) => d.month)]},
      y: {label: null, grid: true, nice: true, tickFormat: "s"},
      color: sourceColor,
      marks: [
        Plot.areaY(coverage, {
          x: "month",
          y: "rows",
          fill: "source_type",
          order: ["gauge", "dam"],
          curve: "step",
          tip: true
        }),
        Plot.ruleY([0])
      ]
    }))}
  </div>
</div>

<div class="grid grid-cols-2">
  <div class="card">
    <h2>Stations above their danger level</h2>
    <h3>Among the 1,035 with a danger level published, split by whether they crossed it</h3>
    ${resize((width) => Plot.plot({
      width,
      height: 300,
      marginLeft: 56,
      x: {label: null, domain: years, tickFormat: "d"},
      y: {label: null, grid: true, nice: true},
      color: dangerColor,
      marks: [
        Plot.areaY(dangerYears, {
          x: "year",
          y: "stations",
          fill: "outcome",
          order: ["Crossed its danger level", "Stayed below"],
          curve: "step",
          channels: {Share: "share"},
          tip: {format: {x: "d", y: integer, Share: percent}}
        }),
        Plot.ruleY([0])
      ]
    }))}
  </div>
  <div class="card">
    <h2>Water level through the year</h2>
    <h3>Metres against each station's own median, with the middle half shaded. Every year on record combined.</h3>
    ${resize((width) => Plot.plot({
      width,
      height: 300,
      marginLeft: 56,
      x: {type: "utc", domain: wholeYear, label: null, ticks: "month", tickFormat: "%b", grid: true},
      y: {label: null, grid: true, nice: true},
      marks: [
        Plot.areaY(seasonal, {x: doy, y1: "level_p25", y2: "level_p75", fill: DEEP, fillOpacity: 0.9}),
        Plot.lineY(seasonal, {
          x: doy,
          y: "level_p50",
          stroke: WATER,
          strokeWidth: 1.6,
          channels: {
            Day: doy,
            Median: "level_p50",
            "Middle half": (d) => `${metres(d.level_p25)} to ${metres(d.level_p75)}`,
            Stations: "stations"
          },
          tip: {format: {x: null, y: null, Day: dayLabel, Median: metres, Stations: integer}}
        }),
        Plot.ruleY([0], {stroke: FAINT})
      ]
    }))}
  </div>
</div>

<div class="card">
  <h2>What the stations measure</h2>
  <h3>Readings per parameter, with the number of stations reporting it. The 55
  codes the Commission publishes no definition for are grouped as one.</h3>
  ${resize((width) => Plot.plot({
    width,
    height: 340,
    marginLeft: 130,
    marginRight: 96,
    x: {label: null, grid: true, tickFormat: "s"},
    y: {label: null},
    marks: [
      Plot.barX(parameters, {
        x: "rows",
        y: "variable",
        sort: {y: "x", reverse: true},
        fill: (d) => (d.unit ? WATER : FAINT),
        channels: {Unit: (d) => d.unit || "none published", Stations: "stations", Since: "first_year"},
        tip: {format: {x: integer, y: null, Stations: integer, Since: "d"}}
      }),
      Plot.text(parameters, {
        x: "rows",
        y: "variable",
        text: (d) => `${integer(d.stations)} stations`,
        textAnchor: "start",
        dx: 6,
        fill: "var(--theme-foreground-muted)"
      }),
      Plot.ruleX([0])
    ]
  }))}
</div>

<div class="controls">${picker}</div>

```js
// Place the element with ${picker}; view() would render the generator's value.
// Fifteen names are shared by more than one station, so the code goes in too.
const picker = Inputs.select(
  stations.slice().sort((a, b) => d3.ascending(a.name ?? "", b.name ?? "")),
  {
    label: "Station",
    format: (d) => `${d.name ?? "unnamed"} (${d.station_code})`,
    value: stations.find((d) => d.station_code === "012-MGD2LKN")
  }
);
const picked = Generators.input(picker);
```

```js
const annual = stationAnnual.filter((d) => d.station_code === picked.station_code);
const dangerDays = d3.sum(annual, (d) => d.danger_days);

// Two thirds of stations have a danger level and slightly fewer have a warning
// level, so the subtitle covers all three cases.
const thresholds = picked.danger_level == null
  ? "The Commission publishes no thresholds for this station"
  : picked.warning_level == null
  ? `Danger level ${decimal(picked.danger_level)}, no warning level published`
  : `Warning level ${decimal(picked.warning_level)}, danger level ${decimal(picked.danger_level)}`;
```

<div class="grid grid-cols-4">
  <div class="card">
    <h2>Days reported</h2>
    <p class="big water">${integer(picked.days)}</p>
  </div>
  <div class="card">
    <h2>Named parameters</h2>
    <p class="big water">${picked.parameters}</p>
  </div>
  <div class="card">
    <h2>Days above danger</h2>
    <p class="big water">${picked.danger_level == null ? "n/a" : integer(dangerDays)}</p>
  </div>
  <div class="card">
    <h2>Record</h2>
    <p class="big small">${picked.first_date ? `${picked.first_date} to ${picked.last_date}` : "no readings"}</p>
  </div>
</div>

<div class="grid grid-cols-2">
  <div class="card">
    <h2>Highest water level per year</h2>
    <h3>Metres. ${thresholds}</h3>
    ${resize((width) => Plot.plot({
      width,
      height: 250,
      marginLeft: 56,
      // Fixed across stations, so switching to a sparse one shows how little it has.
      x: {label: null, domain: years, tickFormat: "d"},
      y: {label: null, grid: true, nice: true},
      marks: [
        Plot.areaY(annual, {x: "year", y: "level_max", fill: DEEP, fillOpacity: 0.35, curve: "step"}),
        Plot.lineY(annual, {x: "year", y: "level_max", stroke: WATER, strokeWidth: 1.4, curve: "step"}),
        picked.warning_level == null ? null
          : Plot.ruleY([picked.warning_level], {stroke: WARNING, strokeDasharray: "4,3"}),
        picked.danger_level == null ? null
          : Plot.ruleY([picked.danger_level], {stroke: DANGER, strokeDasharray: "4,3"}),
        Plot.dot(annual.filter((d) => d.danger_days > 0), {
          x: "year",
          y: "level_max",
          r: 3,
          fill: DANGER,
          channels: {"Days above danger": "danger_days"},
          tip: true
        })
      ]
    }))}
  </div>
  <div class="card">
    <h2>Rainfall per year</h2>
    <h3>Millimetres, summed from the station's daily totals</h3>
    ${resize((width) => Plot.plot({
      width,
      height: 250,
      marginLeft: 56,
      x: {label: null, domain: years, tickFormat: "d"},
      y: {label: null, grid: true, nice: true, reverse: true, zero: true},
      marks: [
        Plot.rectY(annual, {x: "year", y: "rainfall", interval: 1, fill: RAIN, fillOpacity: 0.8, tip: true}),
        Plot.ruleY([0], {stroke: FAINT})
      ]
    }))}
  </div>
</div>

```js
const table = stations.map((d) => ({
  Station: d.name ?? "unnamed",
  Code: d.station_code,
  Type: d.source_type,
  "Danger level": d.danger_level,
  First: d.first_date ?? "",
  Last: d.last_date ?? "",
  Days: d.days
}));

const search = Inputs.search(table, {placeholder: "Search 1,747 stations"});
const found = Generators.input(search);
```

<div class="card table-card">
  <div style="padding: 1rem 1rem 0;">${search}</div>
  ${Inputs.table(found, {
    rows: 16,
    sort: "Days",
    reverse: true,
    format: {"Danger level": (d) => (d == null ? "" : decimal(d)), Days: integer},
    align: {"Danger level": "right", Days: "right"}
  })}
</div>
