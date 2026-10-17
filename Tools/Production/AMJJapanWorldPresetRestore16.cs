// Runtime compatibility fix for Worldbuilder 1.6 restoring the AMJ Japan preset.
// Other Worldbuilder presets and random AMJ Environment worlds remain untouched.
using System;
using System.Reflection;
using HarmonyLib;
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
            var patch = typeof(AMJJapanWorldPresetRestore).GetMethod(
                "BeforeRestoreTerrain", BindingFlags.Static | BindingFlags.NonPublic);
            if (target == null || patch == null)
            {
                Log.Error("[AMJ Japan World] Worldbuilder terrain restore hook unavailable");
                return;
            }
            new Harmony("sucro.amj.japanworld.restoreterrain").Patch(
                target, prefix: new HarmonyMethod(patch));
        }

        private static void BeforeRestoreTerrain(WorldGrid worldGrid, WorldPreset preset)
        {
            if (preset == null || !preset.saveTerrain ||
                !String.Equals(preset.name, PresetName, StringComparison.Ordinal))
                return;
            var surface = worldGrid == null ? null : worldGrid.Surface;
            if (surface == null)
                throw new InvalidOperationException("Japan preset has no surface layer");
            // Worldbuilder's native RawDataToTiles() restores only the mutator
            // entries listed in its file. Tiles omitted from that file retain
            // random-world mutators unless the previous state is cleared first.
            for (int i = 0; i < surface.TilesCount; i++)
                surface[i].mutatorsNullable = null;
            Log.Message("[AMJ Japan World] cleared original tile mutators before preset restore: " +
                surface.TilesCount);
        }
    }
}
