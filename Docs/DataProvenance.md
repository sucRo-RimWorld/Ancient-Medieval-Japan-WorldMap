# Data provenance / Third-party data notice

## Scope

The executable assembly `Assemblies/AMJJapanWorldPresetRestore16.dll` was built from AMJ WorldMap's own C# source (see `Tools/Production/AMJJapanWorldPresetRestore16.cs` in original Project commit `b0f43fdc9f7f419c289b57fe75b654b174e18a91`). No third-party game binaries or Worldbuilder DLLs are included.

The shipped `Worldbuilder/AMJ_Japan_World_Prototype/Preset.xml` and `TerrainData.xml` are **generated derivative geographic/game-grid data from the original 1.6 prototype**, *not* the current new DEM10B z9/faction/summit revision. Their packaged archive is the original accepted Project [Actions run #39022443969](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/actions/runs/39022443969), artifact 12097720526, ZIP SHA-256 `cc93538edd549ed97c3564014013ff4ea0702202e6d70076c641c1061c57cdd2`.

These XML files contain **map-specific derived values**, not the underlying providers' original map-tile PNGs, raw shapefiles, or complete data sets. The provenance and attribution below apply independently from this repository's original-source MIT license.

## Geographic coastline

- GSHHG / Global Self-consistent Hierarchical High-resolution Geography (version 2.3.6, intermediate shorelines), through `basemap-data==2.0.0` and `Tools/Research/BuildJapanCoastlinePrototype.py`.
- The original GSHHG source and derived coastline are subject to the GSHHG distribution and GNU Lesser General Public License, version 3 or later (LGPL-3.0-or-later). Original data and source details: https://www.soest.hawaii.edu/pwessel/gshhg/ ; https://pypi.org/project/basemap-data/ ; license https://www.gnu.org/licenses/lgpl-3.0.html .
- GIS transformations used for the emitted coast/land mask are available in `Tools/Research/BuildJapanCoastlinePrototype.py` and `ProjectJapanCoastlineToTiles.py`. The original provider's raw dataset remains separately obtainable from the upstream; it is not bundled here.

## Elevation / climate

- Prototype land elevations: Geospatial Information Authority of Japan (GSI / 国土地理院), public DEMGM z8 map tiles, https://maps.gsi.go.jp/development/demtile.html and https://maps.gsi.go.jp/development/index.html . The original elevation imagery is **not** embedded in the repo; source processing is in `Tools/Research/BuildJapanRegionalTerrain.py` history at WorldMap commit `95da41bcf386482a2a42ee7e8fbcad2fb58bffe4`. Later **source-only** research changed to GSI DEM10B z9 but did not regenerate these old XML files.
- Japan Meteorological Agency (JMA / 気象庁), 1991–2020 thirty-year meteorological normals (twelve selected stations); https://www.data.jma.go.jp/stats/en/normal/normal.html . Temperature and rainfall outside the station locations were modeled by geographic interpolation and a lapse assumption, **not observed** at every world tile, and are not direct evidence for historical medieval climate.
- Rivers, biomes and forests are model outputs, not surveyed medieval river routes or forests.

## Boundaries

These files support the author's original playable **RimWorld 1.6** shape prototype. Shape accepted. They **do not yet include** the subsequent open changes for relocated faction bases, improved subalpine/alpine distribution, ordinary highland settlement or sacred-summit protection. No 1.7 compatibility or public Workshop release acceptance is implied. Do not attribute third-party geographic source data to the AMJ MIT original-code license alone.
