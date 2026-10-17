# AMJ WorldMap Coordination (main only)

This file records current owner status and handoffs. Confirmed design, statistics, provenance and implementation are owned by `Docs/Design.md`, `Docs/DataProvenance.md`, `Docs/Data/` and `Tools/`.

## WORLDMAP-INTERMEDIATE-FOREST-OWNERSHIP-20261018 — accepted design, implementation open

**Owner:** WorldMap for the Japan fixed-world-only intermediate-temperate forest BiomeDef, its local vegetation weights and regional north/south subdivisions; Environment remains owner of ordinary four biomes, natural-world generation and common PlantDefs. **Status:** OWNERSHIP DECIDED / BIOME XML AND REGION RULES NOT YET IMPLEMENTED. Re-evaluate Subalpine/Alpine distribution only after the WorldMap intermediate-temperate forest is implemented; avoid implementing proposed 10°C/2°C trial thresholds. Separately progress the already reported excessive settlement density and relief-based hilliness design. Canonical accepted responsibility/sequence: `Docs/Design.md`. No RimWorld run, DLL/XML replacement, or release acceptance by this decision.

## WORLDMAP-REVISED-16-NATIVE-PASS-20261017 — mountain visual acceptance open

**Owner:** WorldMap. **State: ACTIVE / REVISED PACKAGE SOURCE AND RUNTIME PASS / AUTHOR HIGHLAND VISUAL ACCEPTANCE OPEN / NO WORKSHOP.**

- Revised fixed-world source: WorldMap main `d3783c6779525d75e1f750bc3e874492190fca1e`. One-shot manually authorized Project [Actions #39042174500](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/actions/runs/39042174500) completed successfully: new Japan world, valid nonplayer settlement positions, one or more eligible subalpine/alpine settlement sites, exactly three impassable alpine summit tiles (Fuji/Tateyama/Hakusan), same accepted island mask, new colony, save and separate-process reload, Unity ERROR 0.
- Compared with original baselines, subalpine 1,268 → 4,562 tiles and alpine 33 → 55. High alpine is still ~0.11% of land; **do not declare the author's insufficient-alpine concern fully accepted without actual revised-map visual assessment**. Ecology, virtual seasons, 1.7, Workshop remain independent incomplete scope.
- The original author-playtested shape prototype is preserved in Project Actions #39022443969. The revised asset transfer from the production-run staging branch `asset-transfer/worldmap-revised-39042174500` replaces the root XML/DLL as one source-matched package. See the formal owner documents for files, hashes, source coverage and known limitations. The Project owns only the isolated native host; WorldMap owns source, finished payload and this acceptance status.
- WorldMap development must not be paused until the author's four visible issues are accepted. Do not automatically launch new multi-profile runs, modify Environment's ordinary random-world behavior or publish Steam Workshop.
