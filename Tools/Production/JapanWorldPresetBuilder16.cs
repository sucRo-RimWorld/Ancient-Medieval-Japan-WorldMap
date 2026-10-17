// Production export path, not a regression Quickstart. Runs on an isolated RimWorld 1.6 host.
// AMJ_JAPAN_WORLD_MASK_CSV: complete ordered native WorldGrid projected coastline.
// AMJ_JAPAN_REGIONAL_CSV: per-land-tile elevation/temperature/biome from BuildJapanRegionalTerrain.py.
// AMJ_JAPAN_PRESET_OUT: empty directory outside game savedata for the finished two-file preset.
// The geographic model is provisional; absent DEM samples receive a documented latitude-only
// fallback, never a fabricated DEM height. Generated XML is not a completed historical map.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using RimWorks.Quickstarts;
using RimWorks.Quickstarts.Verification;
using RimWorld;
using RimWorld.Planet;
using Verse;
using Worldbuilder;

namespace AncientMedievalJapan.WorldMap
{
    public sealed class AMJJapanWorldPresetBuilder : AbstractQuickstart
    {
        private const string PresetName = "AMJ_Japan_World_Prototype";
        // Sacred *summit tile* protection, not blanket exclusion of the
        // surrounding inhabited mountain ranges and pilgrimage foothills.
        // These are the three traditionally named Japanese sacred mountains.
        // Coordinates locate the closest actual Japanese grid cell; they are
        // NOT substitute DEM measurements or invented historical climate data.
        private struct SacredSummit
        {
            public string Name;
            public double Longitude;
            public double Latitude;
            public SacredSummit(string name, double longitude, double latitude)
            {
                Name = name;
                Longitude = longitude;
                Latitude = latitude;
            }
        }

        private static readonly SacredSummit[] SacredSummits = {
            new SacredSummit("Fuji", 138.7272, 35.3606),
            new SacredSummit("Tateyama (Oyama)", 137.6190, 36.5750),
            new SacredSummit("Hakusan (Gozengamine)", 136.7715, 36.1550)
        };

        private static double SummitDistanceSquared(SacredSummit summit,
            double longitude, double latitude)
        {
            double dx = (longitude - summit.Longitude) *
                Math.Cos(summit.Latitude * Math.PI / 180.0);
            double dy = latitude - summit.Latitude;
            return dx * dx + dy * dy;
        }
        private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

        public override TaggedString description { get { return "Produce selectable Japan-shape + biome Worldbuilder preset."; } }
        public override float planetCoverage { get { return 1.0f; } }
        public override string seed { get { return "AMJ-Japan-World-1.6-Prototype"; } }
        public override int mapSize { get { return 250; } }

        private bool exported;
        public override QuickstartVerification Verify() {
            var result = new QuickstartVerification();
            result.Assert("real native world export produced", () => exported);
            return result;
        }

        private static bool TryAddGeographicMutator(SurfaceTile tile,
            PlanetLayer layer, TileMutatorDef mutator)
        {
            if (mutator == null || !mutator.IsValidTile(tile.tile, layer))
                return false;
            tile.AddMutator(mutator);
            return true;
        }

        private static void SignalExportReady(string path)
        {
            using (var file = new FileStream(path + ".ready", FileMode.CreateNew,
                                              FileAccess.Write, FileShare.None))
                file.WriteByte(1);
            // Wait until the production controller has received the completed
            // file export, rather than generate an unrelated local colony map.
            System.Threading.Thread.Sleep(System.Threading.Timeout.Infinite);
        }

        private struct Region
        {
            public string Biome;
            public float? Elevation;
            public float? Temperature;
            public float? Rainfall;
        }

        private static string RequiredPath(string key)
        {
            string path = System.Environment.GetEnvironmentVariable(key);
            if (String.IsNullOrWhiteSpace(path))
                throw new InvalidOperationException("Missing required environment variable: " + key);
            return Path.GetFullPath(path);
        }

        private static Dictionary<int, Region> ReadRegion(string path)
        {
            var records = new Dictionary<int, Region>();
            using (var reader = new StreamReader(path))
            {
                const string expected = "tile_id,gis_longitude,gis_latitude,island,elevation_m,annual_mean_c,proposed_biome,gsi_source,quality,annual_rainfall_mm,warmth_index,coldness_index";
                if (reader.ReadLine() != expected)
                    throw new InvalidDataException("Regional terrain schema differs from producer.");
                string line;
                while ((line = reader.ReadLine()) != null)
                {
                    var cells = line.Split(',');
                    if (cells.Length != 12) throw new InvalidDataException("Region row malformed");
                    int id = Int32.Parse(cells[0], Inv);
                    float height, temperature, rainfall, wi, ci;
                    if (!Single.TryParse(cells[9], NumberStyles.Float, Inv, out rainfall) ||
                        Single.IsNaN(rainfall) || Single.IsInfinity(rainfall) ||
                        rainfall < 0f || rainfall > 6000f)
                        throw new InvalidDataException("Invalid JMA-calibrated rainfall at tile " + id);
                    if (!Single.TryParse(cells[10], NumberStyles.Float, Inv, out wi) ||
                        Single.IsNaN(wi) || Single.IsInfinity(wi) || wi < 0f || wi > 240f ||
                        !Single.TryParse(cells[11], NumberStyles.Float, Inv, out ci) ||
                        Single.IsNaN(ci) || Single.IsInfinity(ci) || ci > 0f || ci < -240f ||
                        cells[6] != BiomeForClimate(wi, ci))
                        throw new InvalidDataException("Japan thermal-index biome mismatch at tile " + id);
                    if (!Single.TryParse(cells[5], NumberStyles.Float, Inv, out temperature) ||
                        Single.IsNaN(temperature) || Single.IsInfinity(temperature))
                        throw new InvalidDataException("Invalid modeled annual temperature at tile " + id);
                    records.Add(id, new Region {
                        Elevation = Single.TryParse(cells[4], NumberStyles.Float, Inv, out height) && height >= 0
                            ? (float?)height : null,
                        Temperature = temperature,
                        Biome = cells[6],
                        Rainfall = rainfall
                    });
                }
            }
            return records;
        }

        private static string BiomeForClimate(float warmthIndex, float coldnessIndex)
        {
            if (warmthIndex >= 85f && coldnessIndex >= -10f) return "AMJ_WarmTemperateForest";
            if (warmthIndex >= 45f) return "AMJ_CoolTemperateForest";
            if (warmthIndex >= 15f) return "AMJ_SubalpineForest";
            return "AMJ_AlpineZone";
        }

        public override void PostApplyConfiguration()
        {
            string coordinateOutput = System.Environment.GetEnvironmentVariable("AMJ_JAPAN_COORDINATE_EXPORT");
            if (!String.IsNullOrWhiteSpace(coordinateOutput))
            {
                string path = Path.GetFullPath(coordinateOutput);
                if (File.Exists(path)) throw new IOException("Refusing coordinate overwrite.");
                using (var csv = new StreamWriter(path))
                {
                    csv.WriteLine("tile_id,longitude,latitude");
                    var existingGrid = Find.WorldGrid;
                    for (int i = 0; i < existingGrid.Surface.TilesCount; i++)
                    {
                        var pos = existingGrid.LongLatOf(existingGrid[i].tile);
                        csv.WriteLine(i.ToString(Inv) + "," +
                            pos.x.ToString("F8", Inv) + "," +
                            pos.y.ToString("F8", Inv));
                    }
                }
                exported = true;
                Log.Message("[AMJ Japan World] Exported real game grid: " + path);
                SignalExportReady(path);
                return;
            }
            string mask = RequiredPath("AMJ_JAPAN_WORLD_MASK_CSV");
            string regional = RequiredPath("AMJ_JAPAN_REGIONAL_CSV");
            string output = RequiredPath("AMJ_JAPAN_PRESET_OUT");
            if (!File.Exists(mask) || !File.Exists(regional))
                throw new FileNotFoundException("Missing land or regional CSV source.");

            // Never replace a preexisting user preset or overwrite a live game.
            if (Directory.Exists(output))
                throw new IOException("Preset output directory already exists: " + output);
            var data = ReadRegion(regional);
            var grid = Find.WorldGrid;
            int tileCount = grid.Surface.TilesCount;
            var ocean = DefDatabase<BiomeDef>.GetNamed("Ocean");
            int landCount = 0;
            int oceanCount = 0;
            int fallbackCount = 0;
            int expectedId = 0;
            var islands = new HashSet<string>(StringComparer.Ordinal);
            var kyushuStartCandidates = new List<PlanetTile>();
            var isJapanLand = new bool[tileCount];
            var sacredPeakTileIds = new int[SacredSummits.Length];
            var sacredPeakDistances = new double[SacredSummits.Length];
            for (int s = 0; s < SacredSummits.Length; s++)
            {
                sacredPeakTileIds[s] = -1;
                sacredPeakDistances[s] = Double.MaxValue;
            }

            using (var reader = new StreamReader(mask))
            {
                const string expected = "tile_id,globe_longitude,globe_latitude,gis_longitude,gis_latitude,is_land,island";
                if (reader.ReadLine() != expected)
                    throw new InvalidDataException("Native coastline mask schema mismatch.");
                string line;
                while ((line = reader.ReadLine()) != null)
                {
                    var cells = line.Split(',');
                    if (cells.Length != 7 || expectedId >= tileCount ||
                        cells[0] != expectedId.ToString(Inv))
                        throw new InvalidDataException("Native mask tile count/order mismatch at " + expectedId);
                    var tile = grid[expectedId] as SurfaceTile;
                    if (tile == null) throw new InvalidDataException("Non-surface grid tile");
                    bool isLand = cells[5] == "1";
                    if (!isLand && cells[5] != "0")
                        throw new InvalidDataException("Invalid land flag");
                    isJapanLand[expectedId] = isLand;
                    if (isLand)
                    {
                        if (String.IsNullOrEmpty(cells[6]))
                            throw new InvalidDataException("Land tile has no named island");
                        islands.Add(cells[6]);
                        Region r;
                        if (!data.TryGetValue(expectedId, out r) ||
                            String.IsNullOrEmpty(r.Biome) || !r.Temperature.HasValue)
                            throw new InvalidDataException("Regional climate/biome missing land tile: " + expectedId);
                        // Select a single closest grid cell for each sacred peak
                        // using the original GIS coordinates, not the virtual
                        // planet longitude or the low-resolution DEM maximum.
                        double gisLongitude, gisLatitude;
                        if (!Double.TryParse(cells[3], NumberStyles.Float, Inv,
                                out gisLongitude) ||
                            !Double.TryParse(cells[4], NumberStyles.Float, Inv,
                                out gisLatitude))
                            throw new InvalidDataException(
                                "Invalid GIS coordinate for Japan land tile " + expectedId);
                        for (int s = 0; s < SacredSummits.Length; s++)
                        {
                            double distance = SummitDistanceSquared(
                                SacredSummits[s], gisLongitude, gisLatitude);
                            if (distance < sacredPeakDistances[s])
                            {
                                sacredPeakDistances[s] = distance;
                                sacredPeakTileIds[s] = expectedId;
                            }
                        }
                        // Missing DEM retains original negative/nodata QA; only the
                        // gameplay elevation uses 1m. Both biome and temperature
                        // are produced together from JMA-monthly/Kira-WI/CI model.
                        float height = r.Elevation ?? 1f;
                        float temp = r.Temperature.Value;
                        string biome = r.Biome;
                        var def = DefDatabase<BiomeDef>.GetNamedSilentFail(biome);
                        if (def == null || def == ocean)
                            throw new InvalidDataException("Missing land BiomeDef " + biome);
                        if (!r.Elevation.HasValue) fallbackCount++;
                        tile.PrimaryBiome = def;
                        tile.elevation = Math.Max(1f, height);
                        tile.temperature = temp;
                        tile.rainfall = r.Rainfall.Value;
                        // A high-alpine BiomeDef is NOT inherently an
                        // impassable hilliness classification. Only specific
                        // sacred summit cells are made impassable below.
                        tile.hilliness = height > 1500 ? Hilliness.Mountainous :
                                         height > 650 ? Hilliness.LargeHills :
                                         height > 200 ? Hilliness.SmallHills : Hilliness.Flat;
                        if (cells[6] == "Kyushu" && tile.hilliness != Hilliness.Impassable)
                            kyushuStartCandidates.Add(tile.tile);
                        landCount++;
                    }
                    else
                    {
                        if (!String.IsNullOrEmpty(cells[6]) || data.ContainsKey(expectedId))
                            throw new InvalidDataException("Sea/land region mismatch");
                        tile.PrimaryBiome = ocean;
                        tile.elevation = -1f;
                        tile.rainfall = 0f;
                        tile.hilliness = Hilliness.Flat;
                        oceanCount++;
                    }
                    expectedId++;
                }
            }
            if (expectedId != tileCount || islands.Count != 13 || landCount == 0 ||
                landCount + oceanCount != tileCount || data.Count != landCount)
                throw new InvalidDataException("Japan coastline and regional source coverage mismatch.");

            // Summit protection is **per tile**. Other alpine/high mountain
            // cells retain Mountainous or lower hilliness and can support
            // settlement, subject to the original game's settlement rules.
            // Never manufacture 3776m/3015m/2702m raster elevations here:
            // the real z8 under-sampling is a separate source-data issue.
            var alpineZone = DefDatabase<BiomeDef>.GetNamed("AMJ_AlpineZone");
            var protectedPeakCells = new HashSet<int>();
            for (int s = 0; s < SacredSummits.Length; s++)
            {
                int id = sacredPeakTileIds[s];
                // <= ~20 km in geographic distance; beyond this the
                // original grid/GIS alignment is too weak to claim a summit.
                if (id < 0 || sacredPeakDistances[s] > 0.18d * 0.18d ||
                    !isJapanLand[id] || !protectedPeakCells.Add(id))
                    throw new InvalidDataException(
                        "Japan grid cannot resolve independent sacred summit " +
                        SacredSummits[s].Name);
                var summitTile = grid[id] as SurfaceTile;
                if (summitTile == null)
                    throw new InvalidDataException(
                        "Sacred summit is not a surface tile: " + id);
                summitTile.PrimaryBiome = alpineZone;
                summitTile.hilliness = Hilliness.Impassable;
                Log.Message("[AMJ Japan World Export] protected uninhabitable " +
                    SacredSummits[s].Name + " alpine summit at tile " + id);
            }

            // The seed world has arbitrary rivers and roads unrelated to Japan.
            // Erase its networks and flow distance before calculating rivers from
            // the selected coastline and GSI-derived elevations.
            int removedRoadLinks = 0;
            int removedRiverLinks = 0;
            for (int i = 0; i < tileCount; i++)
            {
                var tile = grid[i] as SurfaceTile;
                if (tile == null) throw new InvalidDataException("Non-surface tile during network cleanup");
                removedRoadLinks += tile.potentialRoads == null ? 0 : tile.potentialRoads.Count;
                removedRiverLinks += tile.potentialRivers == null ? 0 : tile.potentialRivers.Count;
                tile.potentialRoads = null;
                tile.potentialRivers = null;
                tile.riverDist = 0;
                tile.feature = null;
                tile.mutatorsNullable = null;
                tile.pollution = 0f;
                // Original random-world moisture has no relation to Japanese
                // geography. Reset on all cells, not only the new ocean.
                tile.swampiness = 0f;
            }
            Find.WorldFeatures.features.Clear();

            // Reuse the game's real drainage-tree/flow algorithm instead of
            // retaining river segments from the random source planet. The rain
            // field remains provisional: these are relief-following game rivers,
            // NOT surveyed historic Japanese watercourses.
            Rand.PushState();
            try
            {
                Rand.Seed = 162141109;
                new WorldGenStep_Rivers().GenerateFresh("AMJ-Japan-DEM-Rivers-1.6", grid.Surface);
            }
            finally
            {
                Rand.PopState();
            }

            // WorldGenStep_Rivers includes a short connection to coastal ocean
            // cells to generate mouths. This Worldbuilder preset only preserves
            // inland segments because sea tiles must not contain river mutators.
            int removedSeaRiverLinks = 0;
            int inlandRiverLinks = 0;
            for (int i = 0; i < tileCount; i++)
            {
                var tile = grid[i] as SurfaceTile;
                if (!isJapanLand[i])
                {
                    removedSeaRiverLinks += tile.potentialRivers == null ? 0 : tile.potentialRivers.Count;
                    tile.potentialRivers = null;
                    tile.riverDist = 0;
                }
                else if (tile.potentialRivers != null)
                {
                    removedSeaRiverLinks += tile.potentialRivers.RemoveAll(link =>
                        link.neighbor.tileId < 0 || link.neighbor.tileId >= tileCount ||
                        !isJapanLand[link.neighbor.tileId]);
                    if (tile.potentialRivers.Count == 0) tile.potentialRivers = null;
                    else inlandRiverLinks += tile.potentialRivers.Count;
                }
            }
            if (inlandRiverLinks == 0 || inlandRiverLinks % 2 != 0)
                throw new InvalidDataException("Japan relief-derived river links absent or non-symmetric.");
            // Swampiness is *playable local-ground moisture*, not an assertion
            // that any identified modern or historic wetland exists here.
            // Only flat, low-lying rainy cells adjoining a generated river
            // receive moderate moisture; no TemperateSwamp/ColdBog biome is
            // invented without an independently verified wetland polygon.
            int dampRiverLowlands = 0;
            for (int i = 0; i < tileCount; i++)
            {
                if (!isJapanLand[i]) continue;
                var tile = grid[i] as SurfaceTile;
                if (tile.hilliness != Hilliness.Flat || tile.elevation > 80f ||
                    tile.rainfall < 1300f || tile.Rivers == null || tile.Rivers.Count == 0)
                    continue;
                tile.swampiness = Math.Min(0.35f, 0.10f +
                    Math.Max(0f, tile.rainfall - 1300f) / 6000f);
                dampRiverLowlands++;
            }
            Log.Message("[AMJ Japan World Export] new DEM-derived provisional river segments=" +
                inlandRiverLinks / 2 + " coast links removed=" + removedSeaRiverLinks +
                " provisional damp river lowlands=" + dampRiverLowlands);

            // Raw Worldbuilder tileMutatorDefs must match the new Japanese coastline,
            // mountains and retained provisional river links. Leaving original
            // mutators produces inland "coasts" and rivers on the new ocean.
            int rebuiltCoasts = 0;
            int rebuiltMountains = 0;
            int rebuiltRivers = 0;
            for (int i = 0; i < tileCount; i++)
            {
                if (!isJapanLand[i]) continue;
                var tile = grid[i] as SurfaceTile;
                if (tile.hilliness == Hilliness.Mountainous ||
                    tile.hilliness == Hilliness.Impassable)
                {
                    if (TryAddGeographicMutator(tile, grid.Surface, TileMutatorDefOf.Mountain))
                        rebuiltMountains++;
                }
                if (Find.World.CoastDirectionAt(tile.tile).IsValid &&
                    TryAddGeographicMutator(tile, grid.Surface, TileMutatorDefOf.Coast))
                    rebuiltCoasts++;
                if (tile.Rivers != null && tile.Rivers.Count > 0 &&
                    TryAddGeographicMutator(tile, grid.Surface, TileMutatorDefOf.River))
                    rebuiltRivers++;
            }
            if (rebuiltRivers == 0)
                throw new InvalidDataException("Relief-derived rivers have no usable local-map river mutators.");
            Log.Message("[AMJ Japan World Export] discarded random-world road links=" +
                removedRoadLinks + " river links=" + removedRiverLinks +
                "; rebuilt Japanese-relief mutators coast=" + rebuiltCoasts +
                " mountain=" + rebuiltMountains + " river=" + rebuiltRivers);

            // The ordinary Quickstart continues into a local colony map after this export.
            // Pick a real, unoccupied Japanese land tile rather than the now-ocean
            // random-world starting tile (same contract as the accepted native mask run).
            PlanetTile startingTile = PlanetTile.Invalid;
            foreach (var candidate in kyushuStartCandidates)
            {
                if (Find.WorldObjects.AnyWorldObjectAt(candidate) ||
                    !TileFinder.IsValidTileForNewSettlement(candidate))
                    continue;
                startingTile = candidate;
                break;
            }
            if (!startingTile.Valid)
                throw new InvalidDataException("No valid Kyushu settlement tile in painted Japan world.");
            Find.GameInitData.startingTile = startingTile;
            Log.Message("[AMJ Japan World Export] valid Kyushu local map starting tile=" + startingTile);

            var preset = new WorldPreset {
                name = PresetName,
                Label = "AMJ Japan World (Prototype)",
                description = "Japan-only modern coastline, JMA-station-interpolated rainfall and DEM-based terrain/river routing. Geographic wetlands and medieval climate remain provisional.",
                saveTerrain = true,
                saveGenerationParameters = false,
                saveFactions = false,
                saveIdeologies = false,
                saveBases = false,
                saveMapMarkers = false,
                saveWorldFeatures = false,
                saveWorldTechLevel = false,
                worldInfo = Find.World.info
            };
            // Worldbuilder's serializer creates the build-specific raw tile arrays.
            // The source is on the owned isolated host, and the result is exported
            // to an explicit empty directory for packaging as Mod/Worldbuilder/<name>.
            if (!String.IsNullOrEmpty(WorldPresetManager.GetPreset(PresetName)?.name))
                throw new IOException("Refusing to collide with an existing Worldbuilder preset.");
            Log.Message("[AMJ Japan World Export] painted " + tileCount + " tiles; serializing Worldbuilder terrain.");
            WorldbuilderMod.SaveWorldDataToPreset(preset);
            Log.Message("[AMJ Japan World Export] Worldbuilder terrain serialization completed.");
            if (!WorldPresetManager.SavePreset(preset, null, null))
                throw new IOException("Worldbuilder failed to serialize Preset.xml");
            if (!File.Exists(preset.PresetFilePath) || !File.Exists(preset.TerrainDataFilePath))
                throw new IOException("Worldbuilder serialization did not produce both XML files.");

            Directory.CreateDirectory(output);
            File.Copy(preset.PresetFilePath, Path.Combine(output, "Preset.xml"));
            File.Copy(preset.TerrainDataFilePath, Path.Combine(output, "TerrainData.xml"));
            exported = true;
            Log.Message("[AMJ Japan World Export] name=" + PresetName +
                " islands=" + islands.Count + " land=" + landCount +
                " sea=" + oceanCount + " demFallback=" + fallbackCount +
                " output=" + output);
            SignalExportReady(output);
        }
    }
}
