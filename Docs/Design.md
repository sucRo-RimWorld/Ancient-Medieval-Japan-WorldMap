# Ancient & Medieval Japan - WorldMap — Design

**Repository:** `sucRo-RimWorld/Ancient-Medieval-Japan-WorldMap`. This is the **single canonical owner** of the optional fixed Japan archipelago Worldbuilder map preset and its future production release. The original Project [JapanWorldMapCandidate research](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/blob/main/Docs/Research/JapanWorldMapCandidate.md) is prior research/evidence and superseded prototypes, **not another active implementation owner**.

**Author decision 2026-10-17:** feature work is temporarily **PAUSED** until Environment's forest composition and intermediate-temperate-band decision are mature. Migration of the already playable source into this repo does not resume map development, trigger tests or authorize a Workshop release.

## Purpose and user-visible target

An **optional**, fixed ancient-to-medieval Japanese world for RimWorld 1.6/target 1.7, built as a Worldbuilder saved preset. It is not a replacement for Environment's procedural/random planet. Target the Japanese islands supported by the original polygon selection (Honshu, Shikoku, Kyushu and ten other selected island polygons), **without Hokkaido or Ryukyu/Okinawa**, and preserve geography-specific climate and biomes rather than using the virtual globe's fantasy latitude as evidence of real Japanese vegetation.

The current 1.6 prototype has 590,492 planet tiles, 50,810 land-labelled tiles and 13 island components. A **recognized shape** is already demonstrable, but this is **not** an accepted final grid size, historical coastline, reliable ecological distribution or recommended normal public release. The generated preset is not committed source; its licensed-GIS/terrain inputs are re-created by the builder.

## Confirmed original native 1.6 behavior (not release)

Pinned source: Project `b0f43fdc9f7f419c289b57fe75b654b174e18a91`. Manual [Project Actions #39022443969](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/actions/runs/39022443969); original [downloadable artifact #12097720526](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/actions/runs/39022443969/artifacts/12097720526), ZIP SHA256 `cc93538edd549ed97c3564014013ff4ea0702202e6d70076c641c1061c57cdd2`. Original RimWorld Linux **1.6** + original Worldbuilder + Harmony, VEF and Environment; exported `Worldbuilder/AMJ_Japan_World_Prototype/Preset.xml`, `TerrainData.xml` and one original runtime mutator-restore DLL. Generated colony, saved and loaded in a second game process, each **PASS**, exit 0 and Unity ERROR 0, tile ID 6. The 1.6 source is unchanged by the ownership-only migration; **no new game run** is claimed.

**Demonstration install, not a release:** install the generated output as an ordinary 1.6 Mod directory with `About/About.xml`, `Assemblies/` and `Worldbuilder/AMJ_Japan_World_Prototype/` inside. It requires original **Worldbuilder** (`ferny.worldbuilder`) and **AMJ Environment** (`sucro.ancientmedievaljapan.environment`); actual profile additionally used Harmony and Vanilla Expanded Framework. Select the saved Worldbuilder Japan prototype when creating a world. Do not infer 1.7/Windows performance or fully ecological map accuracy.

## Source of truth and constraints

- `Tools/Production/JapanWorldPresetBuilder16.cs`: in-game original terrain/preset export.
- `Tools/Production/AMJJapanWorldPresetRestore16.cs`: shipped runtime component, limited to this preset, preserving Worldbuilder's terrain mutator reset and avoiding random-world changes.
- `Tools/Production/build_japan_world_preset16.py`: temporary isolated production build, explicitly requested, using the Project shared native 1.6 host helpers (not duplicated here). The `--acceptance` option uses `accept_japan_world_preset16.py` and `JapanWorldPlayableAcceptance16.cs`; **never** a PR/push-triggered native test.
- `Tools/Research/BuildJapanCoastlinePrototype.py` and `ProjectJapanCoastlineToTiles.py`: transform GSHHG/basemap-data coastline into original native tile mask. Retain original GSHHG LGPL-3.0-or-later source attribution and derivative disclosures before public release; do **not** commit original provider polygon data without license review.
- `Tools/Research/BuildJapanRegionalTerrain.py`: bounded official GSI DEMGM z8 pixel reading, JMA 1991–2020 12-station monthly temperature and 12-station annual rainfall interpolation; create provisional Kira WI+CI biome classes. Never claim medieval observations or exact forest composition.

Current approximate forest/mountain 1.6 land-tile counts are Warm 32,893 (64.7%), Cool 16,616 (32.7%), Subalpine 1,268 (2.5%), Alpine 33 (0.1%). **These are research output, not historical vegetation proportions.** Temperature band classes only; an intermediate-temperate forest band is currently **absent**. Elevation provenance: 50,438 actual samples, 338 labelled local DEM estimates, 34 missing elevation sources given only separate 1m *gameplay* fallbacks. The exact terrain, rain, rivers and forest outputs should not be used as historical claims. The current Worldbuilder virtual-planet latitude causes **incorrect local seasons**, a separate unresolved fix.

The island mask uses independently sourced modern GSHHG and explicitly excludes Hokkaido, Okinawa, Yakushima and Tanegashima for the current prototype; this is a **design exclusion** not proof those islands were historically absent. Current DEM z8 misses some high/narrow summits; rainfall has twelve-station IDW smoothing and the in-game river network is a relief-guided procedural heuristic, **not surveyed original medieval river lines**.

## Ownership boundary, backlog and stop

1. **Environment** owns biome identities, regional tree species, intermediate-temperate ecosystem decision and a future twelve wild-food inclusion. WorldMap merely assigns **known, loaded** Environment BiomeDefs on its fixed preset. Never independently add a competing Forest BiomeDef to WorldMap.
2. **WorldMap** owns its preset resolution, coastline/river/elevation representation, geo-position mapping, static biome placement, Worldbuilder compatibility and optional packaged map.
3. Grains/Rice/Wild Food supply balance is evaluated in full AMJ separately; the presence of natural foods does not require WorldMap to implement food production or PlantDefs.
4. Future development may resume **after Environment's forest-band/species decisions**; completion of all wild-food gather Jobs is **not** a prerequisite. Then reevaluate WI/CI transitional forest logic and peak elevation fidelity, grid cost, virtual latitude seasons, 1.7 and final geographic acceptance in a single bounded development+acceptance slice. Do not run unchanged producer simply for PASS totals.
5. **No Steam/public release** until original GIS/DEM terms and attribution, Mod package identity, true Worldbuilder selection, available platform profiles, geographic/ecological limits, privacy/publication gates and acceptance are satisfied.

## Existing version and release status

`About.xml` currently declares **1.6 only**, `packageId=sucro.amj.japanworld`. No new version number, 1.7 support, Steam item, independent distributed source build or new release is claimed by this migration. Original generated XML/DLL remains an archived Project Actions artifact, not a currently committed standalone retail payload.
