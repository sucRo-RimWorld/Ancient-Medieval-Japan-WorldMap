# Data provenance / Third-party data notice

## Scope

The bundled executable assembly `Assemblies/AMJJapanWorldPresetRestore16.dll` was rebuilt from AMJ WorldMap's own C# source at commit `d3783c6779525d75e1f750bc3e874492190fca1e` for original RimWorld Linux 1.6 and original Worldbuilder. No third-party game binaries or Worldbuilder DLLs are bundled.

The shipped Worldbuilder `Preset.xml`, `TerrainData.xml` and restore DLL are **the new revised 1.6 candidate** from WorldMap `d3783c6779525d75e1f750bc3e874492190fca1e`, generated/accepted by [Project Actions #39042174500](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/actions/runs/39042174500), artifact **12104393803**, ZIP SHA-256 `f446d5bef6535fe0441cffe0e28584818cf117ebef14e65b3fb846e8dc533550`. Exact source-to-owner Git Blob SHA for generated XML: `Preset.xml` `437b32995e13c92401c74ded0abea8a1adda3945`, `TerrainData.xml` `09aa354db56bbbcc349386041f5d59bf2672486b`. DLL was reconstructed from the validated staging Base64 and has destination Git Blob `3e3074a1b859f35fc43178141d63cabe6b89d76e`. The **superseded original shape prototype** remains in [Project Actions #39022443969](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/actions/runs/39022443969), artifact 12097720526, ZIP SHA-256 `cc93538edd549ed97c3564014013ff4ea0702202e6d70076c641c1061c57cdd2`.

These XML files contain **map-specific derived values**, not the underlying providers' original map-tile PNGs, raw shapefiles, or complete data sets. The provenance and attribution below apply independently from this repository's original-source MIT license.

## Geographic coastline

- GSHHG / Global Self-consistent Hierarchical High-resolution Geography (version 2.3.6, intermediate shorelines), through `basemap-data==2.0.0` and `Tools/Research/BuildJapanCoastlinePrototype.py`.
- The original GSHHG source and derived coastline are subject to the GSHHG distribution and GNU Lesser General Public License, version 3 or later (LGPL-3.0-or-later). Original data and source details: https://www.soest.hawaii.edu/pwessel/gshhg/ ; https://pypi.org/project/basemap-data/ ; license https://www.gnu.org/licenses/lgpl-3.0.html .
- GIS transformations used for the emitted coast/land mask are available in `Tools/Research/BuildJapanCoastlinePrototype.py` and `ProjectJapanCoastlineToTiles.py`. The original provider's raw dataset remains separately obtainable from the upstream; it is not bundled here.

## Elevation / climate

- Revised elevations: Geospatial Information Authority of Japan (GSI / 国土地理院), DEM10B `dem_png` **z9**, https://maps.gsi.go.jp/development/demtile.html and https://maps.gsi.go.jp/development/index.html . The producer generated a 50,810-land-cell fixed-world derivative from these modern elevations. It used 130 source PNG tiles (SHA-256 checksums retained in `Docs/Data/WorldMapRegionalQA16-20261017.json`); **none of the original elevation PNG imagery is bundled**. The earlier historical DEMGM z8 implementation is preserved in source history at commit `95da41bcf386482a2a42ee7e8fbcad2fb58bffe4`. The revised QA remains `PARTIAL_RESEARCH`, with 27 unresolved elevation cells and 204 local DEM estimates.
- Japan Meteorological Agency (JMA / 気象庁), 1991–2020 thirty-year meteorological normals (twelve selected stations); https://www.data.jma.go.jp/stats/en/normal/normal.html . Temperature and rainfall outside the station locations were modeled by geographic interpolation and a lapse assumption, **not observed** at every world tile, and are not direct evidence for historical medieval climate.
- Rivers, biomes and forests are model outputs, not surveyed medieval river routes or forests.

## Boundaries

The revised files have **native RimWorld 1.6 production, world-generation, settlement, highland, sacred-summit, save and reload acceptance** (Unity ERROR 0) from the run cited above. They preserve the previously author-approved coastline silhouette, but **the author has not yet visually approved the revised highland distribution**. Alpine remains just 55 of 50,810 land tiles (~0.11%). They do not establish medieval geographic/ecological accuracy, 1.7/Windows compatibility, existing-save replacement safety or public Workshop release permission. Do not attribute third-party geographic data to the AMJ MIT original-code license alone.
