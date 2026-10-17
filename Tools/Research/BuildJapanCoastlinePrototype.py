#!/usr/bin/env python3
"""Extract an independent modern Japan coastline research sample; NOT a RimWorld Mod.

Source basemap-data 2.0.0 / GSHHG 2.3.6 intermediate shorelines.
Derived coastline data retain LGPL-3.0-or-later provenance/notice obligations:
https://pypi.org/project/basemap-data/
This does not use or republish the SNAFU JapanWorld preset.
"""
import argparse
import json
from pathlib import Path
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, mapping

OUTPUT = Path(__file__).parent / "AMJ_Japan_Coastline_Research.geojson"
REPORT = Path(__file__).parent / "AMJ_Japan_Coastline_QA.json"

# Geographic representative points are selectors, not hand-drawn coastlines.
# Do NOT silently add the as-yet unapproved Tanegashima/Yakushima islands.
ISLAND_SEEDS = {
    "Honshu": (138.4, 36.1),
    "Shikoku": (133.5, 33.7),
    "Kyushu": (130.7, 32.7),
    "Sado": (138.35, 38.0),
    "Awaji": (134.82, 34.36),
    "Oki": (133.28, 36.25),
    "Tsushima": (129.35, 34.44),
    "Tsushima_south": (129.26, 34.19),
    "Iki": (129.72, 33.79),
    "Amakusa": (130.08, 32.37),
    "Amakusa_shimoshima": (130.35, 32.47),
    "Shodoshima": (134.28, 34.49),
    "Suo_Oshima": (132.31, 33.91),
}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--report', type=Path, default=REPORT)
    args = parser.parse_args(argv)
    # Basemap's intermediate GSHHG data (no external download in this script).
    bounds = (127.0, 29.0, 146.0, 46.5)
    baseline = Basemap(projection="cyl", llcrnrlon=bounds[0],
                       llcrnrlat=bounds[1], urcrnrlon=bounds[2],
                       urcrnrlat=bounds[3], resolution="i")
    polygons = []
    for index, (poly, level) in enumerate(zip(baseline.coastpolygons,
                                               baseline.coastpolygontypes)):
        if level != 1:  # land/water outer shoreline; lakes deferred
            continue
        geometry = Polygon(zip(*poly))
        if geometry.is_valid and not geometry.is_empty:
            polygons.append((index, geometry))

    features, selected, missing = [], set(), []
    for name, lonlat in ISLAND_SEEDS.items():
        hits = [(i, geom) for i, geom in polygons if geom.covers(Point(*lonlat))]
        if len(hits) != 1:
            missing.append({"name": name, "matches": len(hits)})
            continue
        index, geom = hits[0]
        if index in selected:
            raise RuntimeError("Multiple names select the same coastline: " + name)
        selected.add(index)
        features.append({
            "type": "Feature", "properties": {"name": name, "prototype": True},
            "geometry": mapping(geom),
        })

    names = {f["properties"]["name"] for f in features}
    must_have = {"Honshu", "Shikoku", "Kyushu", "Sado", "Awaji", "Oki", "Tsushima", "Iki"}
    assert must_have <= names, "Missing key islands: " + repr(sorted(must_have - names))
    retained = [geom for index, geom in polygons if index in selected]
    for label, point in {
        "Hokkaido": (142.0, 43.0), "Okinawa": (127.7, 26.2),
        "Yakushima (unapproved)": (130.52, 30.34),
        "Tanegashima (unapproved)": (130.98, 30.60),
    }.items():
        assert not any(geom.covers(Point(*point)) for geom in retained), label

    data = {
        "type": "FeatureCollection", "name": "AMJ_Japan_ResearchOnly_GSHHG",
        "description": "Modern shoreline; NOT historical coastline, RimWorld planet or Worldbuilder preset",
        "source": "GSHHG 2.3.6, via basemap-data 2.0.0",
        "source_license": "LGPL-3.0-or-later; preserve upstream attribution and license notices",
        "coordinate_system": "EPSG:4326", "features": features,
    }
    args.output.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
                      encoding="utf8")
    qa = {
        "status": "RESEARCH_ONLY", "features": len(features),
        "selected_names": sorted(names), "unmatched_optional_seeds": missing,
        "Hokkaido": "excluded", "Okinawa": "excluded",
        "Tanegashima_and_Yakushima": "not approved / excluded",
        "pending": ["historic shoreline", "additional small islands", "DEM/elevation",
                    "rivers", "biomes", "tile IDs", "Worldbuilder preset serialization",
                    "runtime verification", "GSHHG redistribution compliance"],
    }
    args.report.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(qa, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
