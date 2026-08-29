import argparse
import json
from pathlib import Path

import polars as pl

import aggregate
import fetch

DATA = Path("data")
MANIFEST = DATA / "manifest.json"


def _norm(code):
    return (code or "").strip().upper()


def build_stations(static, geo):
    g = {_norm(x["stationCode"]): x for x in geo}
    types = {}
    rows = []
    codes = {_norm(x["stationCode"]) for x in static} | set(g)
    smap = {_norm(x["stationCode"]): x for x in static}
    for c in sorted(codes):
        s = smap.get(c, {})
        gx = g.get(c, {})
        t = s.get("type") or gx.get("type")
        types[c] = "dam" if t == "Inflow" else "gauge"
        rows.append({
            "station_code": c,
            "name": gx.get("name"),
            "lat": gx.get("lat"),
            "lon": gx.get("lon"),
            "type": t,
            "nearest_town": s.get("nearestTown"),
            "warning_level": s.get("warningLevel"),
            "danger_level": s.get("dangerLevel"),
            "frl": s.get("frl"),
            "mwl": s.get("mwl"),
            "highest_flow_level": s.get("highestFlowLevel"),
        })
    return pl.DataFrame(rows), types


def write_stations(df):
    DATA.mkdir(parents=True, exist_ok=True)
    df.write_csv(DATA / "stations.csv")
    features = []
    for r in df.iter_rows(named=True):
        if r["lat"] is None or r["lon"] is None:
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": {k: r[k] for k in r if k not in ("lat", "lon")},
        })
    (DATA / "stations.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features})
    )


def load_manifest():
    return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}


def save_manifest(m):
    DATA.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=0, sort_keys=True))


def process(df):
    aggregate.write_daily(aggregate.daily(df), DATA)
    aggregate.write_hourly(aggregate.hourly(df), DATA)


def run(update, limit):
    client = fetch.new_client()
    static, geo = fetch.stations(client)
    stations, types = build_stations(static, geo)
    write_stations(stations)

    # Query with the original stored code (case/whitespace matters to the API); variants are
    # merged later by normalize(). Manifest is therefore keyed by the original code too.
    codes = sorted({p["id"]["stationCode"] for p in fetch.observed_pairs(client)})
    if limit:
        codes = codes[:limit]
    manifest = load_manifest() if update else {}

    for n, code in enumerate(codes, 1):
        since = None
        if update and manifest.get(code):
            # Re-fetch from the start of the last stored day so that day's daily aggregate is
            # recomputed over all its hours, not just the tail. Overlap is de-duped on write.
            since = manifest[code][:10] + "T00:00:00"
        try:
            rows = fetch.history(client, code, since=since)
        except RuntimeError as e:
            print(f"[{n}/{len(codes)}] {code}: SKIPPED ({e})")
            continue
        df = aggregate.normalize(rows, types)
        if df.is_empty():
            continue
        process(df)
        manifest[code] = df.select(pl.col("datetime").max()).item().isoformat()
        print(f"[{n}/{len(codes)}] {code}: {df.height} rows -> {manifest[code]}")
        save_manifest(manifest)

    aggregate.prune_hourly(DATA)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["backfill", "update"])
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    run(update=args.command == "update", limit=args.limit)


if __name__ == "__main__":
    main()
