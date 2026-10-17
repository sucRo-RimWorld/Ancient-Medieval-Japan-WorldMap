# AMJ WorldMap Agent Instructions

## Start here
1. Read this file and **`main:Docs/Coordination.md`** before any work. This document and Coordination are missing from the initial empty repository history; both are first introduced by this owner migration.
2. Read [Project AGENTS](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/blob/main/AGENTS.md) and [Project SharedRules](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/blob/main/Docs/SharedRules.md) for PR-only changes, no automatic costly native runs, minimal tests and stop conditions.
3. Read [Design](Docs/Design.md) and affected source. Project's earlier [Japan WorldMap research](https://github.com/sucRo-RimWorld/Ancient-Medieval-Japan-Project/blob/main/Docs/Research/JapanWorldMapCandidate.md) is historical evidence, not a competing active specification.

## Ownership and state
- **Owner:** this repository owns the **optional fixed Japan Worldbuilder 1.6 map preset**, original coastline projection, regional DEM/JMA raster sampling and four-band provisional biome classification, selected-preset restore compatibility C#, build/export and later packaging.
- **PAUSED by author as of 2026-10-17:** preserve the verified 1.6 prototype; do not initiate new map/biome tuning, expensive producer runs, 1.7/MO matrix, Steam releases or vegetation redesign until Environment's native forest-band/representative tree decisions stabilize. Complete transfer of already-written source and documentation is permitted; do not silently resume feature work.
- **Boundary:** Environment owns procedural biome/climate/vegetation and wild foods; WorldMap may assign explicit fixed-world tile biomes without changing Environment's ordinary random-world behavior. No duplicate Environment PlantDefs/biomes.
- **Existing code is a provisional playable research prototype, not a signed-off geographic distribution**. Proven scope: RimWorld Linux 1.6 original Worldbuilder+Environment world creation/colony/save-reload, as pinned in Design. Incomplete: intermediate-temperate forests, historic ecology, terrain resolution, virtual globe seasonality, 1.7, packaging/performance and Workshop.

## Source and dependency
- Production C#/Python: `Tools/Production/`; licensed GIS-derived research sources: `Tools/Research/`. Source evidence and accepted parameters: `Docs/Design.md`.
- A **manual** production run may use the Project's already-established isolated native 1.6 test-host library (`Tools/PersistentHost/environment_quickstart16.py`, `stage_integrations.py`) via `PYTHONPATH`; do not fork or vendor their large shared host, create PR/push-native test triggers, or assume runner access has been granted to this new repo.
- No GSHHG/GSI raw tiles, original game binaries, third-party Worldbuilder binaries, previously generated terrain preset binary/XML or user save files may be copied as committed redistributable source merely because a test artifact exists. Observe data licensing and derivative provenance.
- Changes: branch → PR → inspect real triggered checks → merge → verify main SHA. Do not write `main` directly. `Docs/Coordination.md` on `main` records handoffs/status only, not definitive design. Do not create branch-specific competing Coordination.
