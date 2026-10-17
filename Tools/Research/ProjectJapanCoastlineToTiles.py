#!/usr/bin/env python3
"""Classify RimWorld world tile centres against the modern AMJ Japan coastline.

RESEARCH ONLY: tile mask intermediate, not Worldbuilder preset or native test.
Input CSV: tile_id,longitude,latitude from the *real* WorldGrid.LongLatOf.
Optional synthetic grid is only for repeatable algorithm testing.
Requires shapely >= 2, numpy and Python >= 3.9.
"""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from shapely import contains_xy
from shapely.geometry import Point, shape

REQUIRED = {"Honshu", "Shikoku", "Kyushu", "Sado", "Awaji", "Oki", "Tsushima", "Iki"}
EXCLUDED = {
    "Hokkaido": (142.0, 43.0),
    "Okinawa": (127.70, 26.20),
    "Tanegashima (undecided)": (130.98, 30.60),
    "Yakushima (undecided)": (130.52, 30.34),
}


def load_coastline(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if obj.get("type") != "FeatureCollection":
        raise ValueError("GeoJSON FeatureCollection required")
    features = []
    for feature in obj.get("features", []):
        name = feature["properties"]["name"]
        geom = shape(feature["geometry"])
        if geom.geom_type != "Polygon" or not geom.is_valid or geom.is_empty:
            raise ValueError("Invalid island polygon: " + name)
        features.append((name, geom))
    names = [name for name, _ in features]
    if not REQUIRED.issubset(names) or len(names) != len(set(names)):
        raise ValueError("Missing required island or repeated name")
    for label, coords in EXCLUDED.items():
        if any(poly.covers(Point(coords)) for _, poly in features):
            raise ValueError("Out-of-scope island included: " + label)
    return features


def load_tile_centres(path):
    tiles = []
    ids = set()
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        rows = csv.DictReader(handle)
        if not {"tile_id", "longitude", "latitude"}.issubset(rows.fieldnames or ()):
            raise ValueError("Missing CSV columns: tile_id, longitude, latitude")
        for item in rows:
            idx = int(item["tile_id"])
            lon, lat = float(item["longitude"]), float(item["latitude"])
            if (idx < 0 or idx in ids or not math.isfinite(lon) or
                    not math.isfinite(lat) or not -180 <= lon <= 180 or
                    not -90 <= lat <= 90):
                raise ValueError("Invalid or repeated world tile: " + str(item))
            ids.add(idx)
            tiles.append((idx, lon, lat))
    if not tiles:
        raise ValueError("No tile positions")
    return tiles


def synthetic_grid(step):
    if not math.isfinite(step) or not 0 < step <= 5:
        raise ValueError("Invalid step")
    width, height = round(360 / step), round(180 / step)
    if width * height > 1000000:
        raise ValueError("Synthetic fixture too large")
    return [
        (i * width + j, -180 + (j + 0.5) * 360 / width, -90 + (i + 0.5) * 180 / height)
        for i in range(height) for j in range(width)
    ]


def project(features, positions, longitude_scale=11.0, latitude_scale=13.0,
            gis_lon=135.5, gis_lat=36.0, virtual_lon=0.0, virtual_lat=0.0):
    """Reverse-map inflated imaginary planet positions onto physical GIS.

    No representation of real Earth scale or actual sunshine is implied.
    """
    if not (math.isfinite(longitude_scale) and math.isfinite(latitude_scale) and
            longitude_scale > 0 and latitude_scale > 0):
        raise ValueError("Invalid enlargement scale")
    idx = np.array([v[0] for v in positions], dtype=np.int64)
    wlon = np.array([v[1] for v in positions], dtype=np.float64)
    wlat = np.array([v[2] for v in positions], dtype=np.float64)
    real_lon = gis_lon + (wlon - virtual_lon) / longitude_scale
    real_lat = gis_lat + (wlat - virtual_lat) / latitude_scale
    islands = np.full(len(idx), "", dtype=object)
    for name, geom in features:
        present = contains_xy(geom, real_lon, real_lat)
        if np.any(present & (islands != "")):
            raise ValueError("Overlapping island mapping: " + name)
        islands[present] = name
    return idx, wlon, wlat, real_lon, real_lat, islands


def write_tiles(source_path, output_csv, output_qa, data, *, mode,
                longitude_scale, latitude_scale, gis_lon, gis_lat, virtual_lon, virtual_lat):
    ids, glon, glat, real_lon, real_lat, names = data
    by_island = dict(sorted(Counter(str(n) for n in names if n).items()))
    land_count = sum(by_island.values())
    with Path(output_csv).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("tile_id", "globe_longitude", "globe_latitude",
                         "gis_longitude", "gis_latitude", "is_land", "island"))
        for tid, vlon, vlat, lon, lat, island in zip(
                ids, glon, glat, real_lon, real_lat, names):
            writer.writerow((int(tid), f"{vlon:.6f}", f"{vlat:.6f}",
                             f"{lon:.6f}", f"{lat:.6f}", int(bool(island)), island))
    qa = {
        "status": "RESEARCH_ONLY_NOT_WORLDBUILDER_PRESET",
        "input_kind": mode,
        "external_tile_centres_csv_provided": mode == "supplied",
        "native_grid_provenance_verified": False,
        "not_a_runtime_test": True,
        "source_sha256": hashlib.sha256(Path(source_path).read_bytes()).hexdigest(),
        "total_samples": len(ids), "land_samples": land_count,
        "ocean_samples": len(ids) - land_count,
        "land_percent": round(100 * land_count / len(ids), 4),
        "land_by_island": by_island,
        "transform": {
            "gis_origin_lon": gis_lon, "gis_origin_lat": gis_lat,
            "virtual_origin_lon": virtual_lon, "virtual_origin_lat": virtual_lat,
            "longitude_enlargement": longitude_scale,
            "latitude_enlargement": latitude_scale,
            "not_physical_earth_latitude": True,
        },
        "missing_layers": (
            ["actual RimWorld planet tile IDs and centres"] if mode != "supplied" else []
        ) + ["verified grid topology", "DEM", "hilliness", "rivers", "lakes",
             "biomes", "temperature", "rainfall",
             "Worldbuilder TerrainData.xml", "game-runtime tests"],
    }
    Path(output_qa).write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    return qa


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coastline", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--tile-centers", type=Path)
    mode.add_argument("--synthetic-grid-step", type=float)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-qa", type=Path, required=True)
    parser.add_argument("--gis-lon", type=float, default=135.5)
    parser.add_argument("--gis-lat", type=float, default=36.0)
    parser.add_argument("--globe-lon", type=float, default=0.0)
    parser.add_argument("--globe-lat", type=float, default=0.0)
    parser.add_argument("--lon-scale", type=float, default=11.0)
    parser.add_argument("--lat-scale", type=float, default=13.0)
    args = parser.parse_args(argv)
    features = load_coastline(args.coastline)
    positions = (load_tile_centres(args.tile_centers) if args.tile_centers
                 else synthetic_grid(args.synthetic_grid_step))
    projection = project(features, positions, args.lon_scale, args.lat_scale,
                         args.gis_lon, args.gis_lat, args.globe_lon, args.globe_lat)
    report = write_tiles(
        args.coastline, args.output_csv, args.output_qa, projection,
        mode="supplied" if args.tile_centers else "synthetic",
        longitude_scale=args.lon_scale, latitude_scale=args.lat_scale,
        gis_lon=args.gis_lon, gis_lat=args.gis_lat,
        virtual_lon=args.globe_lon, virtual_lat=args.globe_lat)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    main()
