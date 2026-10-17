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

        private static void BeforeRestoreTerrain(WorldGrid worldGrid, WorldPreset preset)
        {
            if (!IsOurPreset(preset)) return;
            var surface = worldGrid == null ? null : worldGrid.Surface;
            if (surface == null)
                throw new InvalidOperationException("Japan preset has no surface layer");
            // Worldbuilder restores mutators listed in the preset but can leave
            // random-world mutators behind on omitted tiles.
            for (int i = 0; i < surface.TilesCount; i++)
                surface[i].mutatorsNullable = null;
            Log.Message("[AMJ Japan World] cleared original tile mutators before preset restore: " +
                surface.TilesCount);
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
            WorldPreset preset)
        {
            if (!IsOurPreset(preset)) return;
            if (world == null || worldGrid == null || worldGrid.Surface == null)
                throw new InvalidOperationException("Japan preset has no finalized world grid");
            var ocean = DefDatabase<BiomeDef>.GetNamed("Ocean");
            var factionSettlements = Utils.GetSurfaceWorldObjects<Settlement>();
            var stranded = factionSettlements.Where(s =>
                !IsEligibleJapaneseSettlementTile(worldGrid, s.Tile, ocean)).ToList();
            if (stranded.Count == 0)
            {
                Log.Message("[AMJ Japan World] restored terrain: all " +
                    factionSettlements.Count + " non-player faction settlements on passable land");
                return;
            }

            // Worldbuilder restores the preset *after* the original random-world
            // faction generator placed bases.  Preset.saveBases is intentionally
            // false so leaving the old bases alone creates "ocean factions".
            // Relocate the original Settlement objects instead of deleting or
            // duplicating them: keep names, factions, load IDs and relationships.
            var available = new List<PlanetTile>();
            var surface = worldGrid.Surface;
            for (int i = 0; i < surface.TilesCount; i++)
            {
                var tile = surface[i];
                PlanetTile position = tile.tile;
                if (!IsEligibleJapaneseSettlementTile(worldGrid, position, ocean) ||
                    world.worldObjects.AnyWorldObjectAt(position) ||
                    !TileFinder.IsValidTileForNewSettlement(position))
                    continue;
                available.Add(position);
            }
            if (available.Count < stranded.Count)
                throw new InvalidOperationException(
                    "Japan world lacks sufficient valid free land for " +
                    stranded.Count + " stranded faction settlements (" +
                    available.Count + " candidate tiles)");

            // Deterministic, dispersed sampling of the actual WorldGrid ordering.
            // Reserve each destination only once.  Never select water,
            // impassable sacred summits or occupied sites.
            int stride = Math.Max(1, available.Count / stranded.Count);
            int offset = available.Count / 3;
            int moved = 0;
            for (int i = 0; i < stranded.Count; i++)
            {
                var settlement = stranded[i];
                int candidateIndex = (int)(((long)offset + (long)i * stride) % available.Count);
                var destination = available[candidateIndex];
                if (world.worldObjects.AnyWorldObjectAt(destination))
                    throw new InvalidOperationException(
                        "Japan faction destination was occupied after reservation: " + destination);
                world.worldObjects.Remove(settlement);
                settlement.Tile = destination;
                world.worldObjects.Add(settlement);
                moved++;
            }
            var remaining = Utils.GetSurfaceWorldObjects<Settlement>()
                .Count(s => !IsEligibleJapaneseSettlementTile(worldGrid, s.Tile, ocean));
            if (remaining != 0)
                throw new InvalidOperationException(
                    "Japan world still contains " + remaining + " invalid faction settlements");
            Log.Message("[AMJ Japan World] relocated " + moved +
                " random-world faction settlements onto passable Japan land; " +
                factionSettlements.Count + " total original non-player settlements retained");
        }
    }
}
