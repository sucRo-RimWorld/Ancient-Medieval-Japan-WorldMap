// One consolidated real-game acceptance for the independently exported Worldbuilder preset.
// This assembly is never included in the Workshop Mod; only the isolated native host loads it.
using System;
using System.IO;
using System.Linq;
using RimWorks.Quickstarts;
using RimWorks.Quickstarts.Verification;
using RimWorld;
using RimWorld.Planet;
using UnityEngine;
using Verse;
using Worldbuilder;

namespace AncientMedievalJapan.WorldMap
{
    public sealed class AMJJapanPlayableAcceptance : AbstractQuickstart
    {
        private const string PresetName = "AMJ_Japan_World_Prototype";
        private const string SaveName = "autostart";
        private bool saved;
        public override TaggedString description { get { return "Load Japan preset, settle, save once."; } }
        public override float planetCoverage { get { return 1.0f; } }
        public override int mapSize { get { return 150; } }
        public override string seed { get { return "AMJ-Japan-World-1.6-Playable"; } }

        public override void PreGenerateWorld()
        {
            var preset = WorldPresetManager.GetPreset(PresetName);
            if (preset == null || !preset.saveTerrain)
                throw new InvalidDataException("Production Japan Worldbuilder preset unavailable");
            World_ExposeData_Patch.WorldPresetName = PresetName;
            PlanetLayerSettingsDefOf.Surface.settings.subdivisions = preset.myLittlePlanetSubcount;
        }

        public override void PostApplyConfiguration()
        {
            if (Find.WorldGrid.Surface.TilesCount != 590492)
                throw new InvalidDataException("Japan preset has unexpected world grid size");
            PlanetTile candidate = PlanetTile.Invalid;
            for (int i = 0; i < Find.WorldGrid.Surface.TilesCount; i++)
            {
                var tile = Find.WorldGrid[i];
                if (tile.WaterCovered || tile.PrimaryBiome == BiomeDefOf.Ocean)
                    continue;
                if (Find.WorldObjects.AnyWorldObjectAt(tile.tile) ||
                    !TileFinder.IsValidTileForNewSettlement(tile.tile))
                    continue;
                candidate = tile.tile;
                break;
            }
            if (!candidate.Valid)
                throw new InvalidDataException("No Japan land tile available for colony");
            Find.GameInitData.startingTile = candidate;
            Log.Message("[AMJ Japan acceptance] world preset selected, settlement tile=" + candidate);
        }

        public override void PostLoaded()
        {
            var map = Find.CurrentMap;
            if (map == null || !map.IsPlayerHome || map.Tile.Tile.WaterCovered)
                throw new InvalidDataException("Japan preset did not generate a valid player home map");
            var surface = Find.WorldGrid.Surface;
            int land = 0, roads = 0, seaRivers = 0, seaMutators = 0;
            for (int i = 0; i < surface.TilesCount; i++)
            {
                var tile = surface[i];
                if (!tile.WaterCovered) land++;
                if (tile.potentialRoads != null) roads += tile.potentialRoads.Count;
                if (tile.WaterCovered)
                {
                    if (tile.potentialRivers != null) seaRivers += tile.potentialRivers.Count;
                    if (tile.Mutators.Count > 0) seaMutators += tile.Mutators.Count;
                }
            }
            if (land != 50810 || roads != 0 || seaRivers != 0 || seaMutators != 0)
                throw new InvalidDataException("Japan Worldbuilder terrain data did not survive restore: " +
                    "land=" + land + " roads=" + roads + " seaRivers=" + seaRivers +
                    " seaMutators=" + seaMutators);
            string reportPath = System.Environment.GetEnvironmentVariable("AMJ_JAPAN_ACCEPT_NEW_READY");
            if (String.IsNullOrWhiteSpace(reportPath))
                throw new InvalidDataException("Acceptance completion path absent");
            GameDataSaveLoader.SaveGame(SaveName);
            string savedPath = GenFilePaths.FilePathForSavedGame(SaveName);
            if (!File.Exists(savedPath) || new FileInfo(savedPath).Length < 1024)
                throw new IOException("RimWorld failed to save Japan colony");
            File.WriteAllText(reportPath, map.Tile.tileId.ToString());
            saved = true;
            Log.Message("[AMJ Japan acceptance] playable Japan colony saved tile=" + map.Tile);
        }

        public override QuickstartVerification Verify()
        {
            var result = new QuickstartVerification();
            result.Assert("Worldbuilder preset loaded, colony generated and autostart.rws saved",
                () => saved);
            return result;
        }
    }

    // The second independent RimWorld process automatically loads autostart.rws
    // through original Root_Entry. Only game-loaded state produces this marker.
    public sealed class AMJJapanSaveLoadAcceptance : GameComponent
    {
        public AMJJapanSaveLoadAcceptance(Game game) { }
        public override void LoadedGame()
        {
            var path = System.Environment.GetEnvironmentVariable("AMJ_JAPAN_ACCEPT_RELOAD_READY");
            if (String.IsNullOrEmpty(path)) return;
            LongEventHandler.ExecuteWhenFinished(() =>
            {
                try
                {
                    string previous = System.Environment.GetEnvironmentVariable("AMJ_JAPAN_ACCEPT_NEW_READY");
                    if (String.IsNullOrWhiteSpace(previous) || !File.Exists(previous))
                        throw new IOException("Missing original Japan settlement tile receipt");
                    int expected = Int32.Parse(File.ReadAllText(previous).Trim());
                    var map = Find.CurrentMap;
                    if (map == null || !map.IsPlayerHome || map.Tile.tileId != expected ||
                        map.Tile.Tile.WaterCovered || Find.WorldGrid.Surface.TilesCount != 590492)
                        throw new InvalidDataException("Loaded Japan world or settlement differs");
                    File.WriteAllText(path, map.Tile.tileId.ToString());
                    Log.Message("[AMJ Japan acceptance] save/reload preserved player settlement at tile " +
                        map.Tile);
                    Application.Quit(0);
                }
                catch (Exception ex)
                {
                    Log.Error("[AMJ Japan acceptance] real save/reload failed: " + ex);
                    Application.Quit(2);
                }
            });
        }
    }
}
