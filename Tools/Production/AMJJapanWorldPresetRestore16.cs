// Runtime compatibility fix for Worldbuilder 1.6 restoring the AMJ Japan preset.
// Other Worldbuilder presets, already loaded games and random Environment worlds remain untouched.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using HarmonyLib;
using RimWorld;
using RimWorld.Planet;
using Verse;
using Worldbuilder;

namespace AncientMedievalJapan.WorldMap
{
    [StaticConstructorOnStartup]
    public static class AMJJapanWorldPresetRestore
    {
        private const string PresetName = "AMJ_Japan_World_Prototype";

        static AMJJapanWorldPresetRestore()
        {
            var target = AccessTools.Method(typeof(World_FinalizeInit_Patch), "RestoreTerrain");
            var before = typeof(AMJJapanWorldPresetRestore).GetMethod(
                "BeforeRestoreTerrain", BindingFlags.Static | BindingFlags.NonPublic);
            var after = typeof(AMJJapanWorldPresetRestore).GetMethod(
                "AfterRestoreTerrain", BindingFlags.Static | BindingFlags.NonPublic);
            if (target == null || before == null || after == null)
            {
                Log.Error("[AMJ Japan World] Worldbuilder terrain restore hooks unavailable");
                return;
            }
            new Harmony("sucro.amj.japanworld.restoreterrain").Patch(target,
                prefix: new HarmonyMethod(before), postfix: new HarmonyMethod(after));
        }

        private static bool IsOurPreset(WorldPreset preset)
        {
            return preset != null && preset.saveTerrain &&
                String.Equals(preset.name, PresetName, StringComparison.Ordinal);
        }

        // Harmony shares the original viable-land denominator between prefix
        // and postfix. Worldbuilder replaces terrain after normal faction
        // generation, so retaining all original settlements overcrowds Japan.
        private static void BeforeRestoreTerrain(WorldGrid worldGrid, WorldPreset preset,
            out int __state)
        {
            __state = 0;
            if (!IsOurPreset(preset)) return;
            var surface = worldGrid == null ? null : worldGrid.Surface;
            if (surface == null)
                throw new InvalidOperationException("Japan preset has no surface layer");
            var ocean = DefDatabase<BiomeDef>.GetNamed("Ocean");
            for (int i = 0; i < surface.TilesCount; i++)
            {
                var tile = surface[i];
                if (tile.PrimaryBiome != null && tile.PrimaryBiome != ocean &&
                    tile.hilliness != Hilliness.Impassable)
                    __state++;
                // Worldbuilder can leave original random-world mutators behind.
                tile.mutatorsNullable = null;
            }
            if (__state == 0)
                throw new InvalidOperationException("Original world has no viable land");
            Log.Message("[AMJ Japan World] cleared original mutators; original viable land=" +
                __state + " of " + surface.TilesCount);
        }

        private static bool IsEligibleJapaneseSettlementTile(WorldGrid grid,
            PlanetTile position, BiomeDef ocean)
        {
            if (!position.Valid || position.Layer != grid.Surface)
                return false;
            var tile = grid[position] as SurfaceTile;
            return tile != null && tile.PrimaryBiome != null &&
                tile.PrimaryBiome != ocean &&
                tile.hilliness != Hilliness.Impassable;
        }

        private static void AfterRestoreTerrain(World world, WorldGrid worldGrid,
            WorldPreset preset, int __state)
        {
            if (!IsOurPreset(preset)) return;
            if (world == null || worldGrid == null || worldGrid.Surface == null ||
                __state <= 0)
                throw new InvalidOperationException("Japan preset missing restoration context");

            var ocean = DefDatabase<BiomeDef>.GetNamed("Ocean");
            var surface = worldGrid.Surface;
            int japanEligibleLand = 0;
            for (int i = 0; i < surface.TilesCount; i++)
            {
                if (IsEligibleJapaneseSettlementTile(worldGrid, surface[i].tile, ocean))
                    japanEligibleLand++;
            }
            if (japanEligibleLand == 0)
                throw new InvalidOperationException("Restored Japan has no viable land");

            // The original 100%-coverage random-world faction generation ran
            // BEFORE Worldbuilder replaced its terrain with the much smaller
            // Japanese islands. Scale base *counts* by viable land instead of
            // moving every original base onto Japan. Preserve one existing base
            // for each generated non-player faction, plus proportionally
            // distributed extras, preserving their actual Settlement identity.
            var originals = Utils.GetSurfaceWorldObjects<Settlement>()
                .Where(s => s.Faction != null && !s.Faction.IsPlayer).ToList();
            var byFaction = originals.GroupBy(s => s.Faction)
                .Select(g => g.OrderBy(s =>
                    IsEligibleJapaneseSettlementTile(worldGrid, s.Tile, ocean) ? 0 : 1)
                    .ToList()).ToList();
            int proportionalCount = (int)Math.Round(
                originals.Count * Math.Min(1.0, (double)japanEligibleLand / __state),
                MidpointRounding.AwayFromZero);
            int targetCount = Math.Min(originals.Count,
                Math.Max(byFaction.Count, proportionalCount));
            var keep = new HashSet<Settlement>();
            // Keep a representative of every existing faction even if the
            // scaled target is below the faction count. Prefer a site already
            // on Japanese land, reducing the number of required relocations.
            foreach (var group in byFaction)
                keep.Add(group[0]);
            for (int rank = 1; keep.Count < targetCount; rank++)
            {
                bool added = false;
                foreach (var group in byFaction)
                {
                    if (group.Count <= rank) continue;
                    keep.Add(group[rank]);
                    added = true;
                    if (keep.Count == targetCount) break;
                }
                if (!added)
                    throw new InvalidOperationException(
                        "Japan settlement-density allocation exhausted candidates");
            }
            int removed = 0;
            foreach (var settlement in originals)
            {
                if (keep.Contains(settlement)) continue;
                world.worldObjects.Remove(settlement);
                removed++;
            }
            var stranded = originals.Where(s => keep.Contains(s) &&
                !IsEligibleJapaneseSettlementTile(worldGrid, s.Tile, ocean)).ToList();
            if (stranded.Count != 0)
            {
                // The remaining stranded bases must be moved (not duplicated)
                // onto an unused, engine-approved site on Japanese land.
                var available = new List<PlanetTile>();
                for (int i = 0; i < surface.TilesCount; i++)
                {
                    PlanetTile position = surface[i].tile;
                    if (!IsEligibleJapaneseSettlementTile(worldGrid, position, ocean) ||
                        world.worldObjects.AnyWorldObjectAt(position) ||
                        !TileFinder.IsValidTileForNewSettlement(position))
                        continue;
                    available.Add(position);
                }
                if (available.Count < stranded.Count)
                    throw new InvalidOperationException(
                        "Japan lacks " + stranded.Count + " free relocation tiles (" +
                        available.Count + " candidates)");
                int stride = Math.Max(1, available.Count / stranded.Count);
                int offset = available.Count / 3;
                for (int i = 0; i < stranded.Count; i++)
                {
                    var settlement = stranded[i];
                    int index = (int)(((long)offset + (long)i * stride) % available.Count);
                    var destination = available[index];
                    if (world.worldObjects.AnyWorldObjectAt(destination))
                        throw new InvalidOperationException(
                            "Japan relocation destination occupied: " + destination);
                    world.worldObjects.Remove(settlement);
                    settlement.Tile = destination;
                    world.worldObjects.Add(settlement);
                }
            }
            var remaining = Utils.GetSurfaceWorldObjects<Settlement>()
                .Where(s => s.Faction != null && !s.Faction.IsPlayer).ToList();
            int invalid = remaining.Count(s =>
                !IsEligibleJapaneseSettlementTile(worldGrid, s.Tile, ocean));
            int missingFactions = byFaction.Count(g =>
                !remaining.Any(s => s.Faction == g[0].Faction));
            if (invalid != 0 || missingFactions != 0 ||
                remaining.Count != targetCount || removed + targetCount != originals.Count)
                throw new InvalidOperationException(
                    "Japan base density/placement invariant failed: invalid=" + invalid +
                    " lost factions=" + missingFactions +
                    " count=" + remaining.Count + " expected=" + targetCount);
            Log.Message("[AMJ Japan World] adjusted faction settlement density: original=" +
                originals.Count + " retained=" + targetCount + " removed=" + removed +
                " relocated=" + stranded.Count + " factions=" + byFaction.Count +
                " originalViableLand=" + __state +
                " japanViableLand=" + japanEligibleLand);
        }
    }
}
