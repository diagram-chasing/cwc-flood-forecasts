import json
import time

import httpx

BASE = "https://ffs.india-water.gov.in"

# datatype code -> (variable, unit, kind). kind is "stat" or "sum".
DATATYPES = {
    "HHS": ("water_level", "m", "stat"),
    "HHA": ("water_level", "m", "stat"),
    "HHX": ("water_level", "m", "stat"),
    "HHT": ("water_level", "m", "stat"),
    "HZS": ("water_level", "m", "stat"),
    "HZF": ("water_level", "m", "stat"),
    "HQ0": ("discharge", "cumec", "stat"),
    "HTW": ("water_temp", "degC", "stat"),
    "MPS": ("rainfall", "mm", "sum"),
    "MPA": ("rainfall", "mm", "sum"),
    "MPM": ("rainfall", "mm", "sum"),
    "MPN": ("rainfall", "mm", "sum"),
    "MTN": ("air_temp_min", "degC", "stat"),
    "MTX": ("air_temp_max", "degC", "stat"),
    "MTW": ("water_temp", "degC", "stat"),
    "MTD": ("air_temp", "degC", "stat"),
    "FIN": ("reservoir_inflow", "cumec", "stat"),
    "FOU": ("reservoir_outflow", "cumec", "stat"),
    "FOL": ("reservoir_outflow", "cumec", "stat"),
    "IBD": ("reservoir_storage", "mcm", "stat"),
    "ISD": ("reservoir_storage", "mcm", "stat"),
    "IWA": ("reservoir_level", "m", "stat"),
    "IW2": ("reservoir_level", "m", "stat"),
    "ITA": ("reservoir_area", "sqkm", "stat"),
    "IHS": ("reservoir_level", "m", "stat"),
    "IPC": ("reservoir_percent", "pct", "stat"),
}

TYPES = ("Level", "Inflow", "Base")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": BASE + "/",
    "Origin": BASE,
}


def variable_of(code):
    return DATATYPES.get(code, (code.lower(), None, "stat"))


def _expr(field, operator, value):
    return {"expression": {"valueIsRelationField": False, "fieldName": field,
                           "operator": operator, "value": value}}


def _get(client, path, spec=None):
    params = None if spec is None else {"specification": json.dumps(spec, separators=(",", ":"))}
    for attempt in range(6):
        try:
            r = client.get(BASE + path, params=params)
            if r.status_code == 200:
                return r.json()
        except httpx.HTTPError:
            pass
        time.sleep(min(60, 2 ** attempt))
    raise RuntimeError(f"failed after retries: {path}")


def new_client():
    return httpx.Client(timeout=300, headers=HEADERS)


def stations(client):
    static = _get(client, "/iam/api/flood-forecast-static/")
    geo = []
    for t in TYPES:
        spec = {"where": _expr("layerStationStationCode.floodForecastStaticStationCode.type", "eq", t)}
        geo += _get(client, "/iam/api/layer-station-geo/specification/", spec)
    return static, geo


def observed_pairs(client):
    pairs = []
    for t in TYPES:
        spec = {"where": _expr("stationCode.floodForecastStaticStationCode.type", "eq", t)}
        pairs += _get(client, "/iam/api/new-entry-data-aggregate/specification/", spec)
    return pairs


def history(client, code, since=None):
    where = _expr("id.stationCode", "eq", code)
    spec = {"where": where} if since is None else {"where": where, "and": _expr("id.dataTime", "gt", since)}
    return _get(client, "/iam/api/new-entry-data/specification/", spec)
