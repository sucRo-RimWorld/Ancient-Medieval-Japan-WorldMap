#!/usr/bin/env python3
"""Build a Japan Worldbuilder preset once on the established isolated native 1.6 host.
This is a production artifact generator; no research test scenarios are invoked.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
# Shared isolated native host implementation stays in the Project repository.
# WorldMap source lives in this separate owner; supply Project's host helpers
# via PYTHONPATH (from the owning manual Project workflow), never vendor them.
legacy_host=Path(__file__).resolve().parents[1] / 'PersistentHost'
if legacy_host.is_dir():
    sys.path.insert(0, str(legacy_host))
import environment_quickstart16 as quick
import stage_integrations as host

SOURCE=Path(__file__).resolve().parents[1]/"Production"/"JapanWorldPresetBuilder16.cs"
RUNTIME_SOURCE=Path(__file__).resolve().parents[1]/"Production"/"AMJJapanWorldPresetRestore16.cs"
RESEARCH=Path(__file__).resolve().parents[1]/"Research"
PACKAGE="sucro.amj.japanworld.builder"
SCENARIO="AMJJapanWorldPresetBuilder"
MODS=(
 ("Framework_Harmony","brrainz.harmony"),
 ("Framework_RimLogging","rimworks.rimlogging"),
 ("Framework_Quickstarts","rimworks.quickstarts"),
 ("MO_VEF","oskarpotocki.vanillafactionsexpanded.core"),
 ("AMJ_Worldbuilder_Research","ferny.worldbuilder"),
 ("AMJ_Environment","sucro.ancientmedievaljapan.environment"),
)

def checked(command,*,env=None,timeout=360,allow_partial=False):
    p=subprocess.run(command,env=env,capture_output=True,text=True,timeout=timeout)
    if p.returncode and not allow_partial:
        raise RuntimeError("Command failed: "+str(command[:3])+" "+(p.stderr+p.stdout)[-3000:])
    return p

def launch(game, saved, scratch, environment, phase, produced):
    """Accept exported production data without generating an unrelated colony."""
    marker = Path(str(produced) + ".ready")
    if marker.exists():
        raise RuntimeError("Production completion marker already exists: " + str(marker))
    log = scratch / (phase + "-unity.log")
    out = scratch / (phase + "-launcher.log")
    timeout_seconds = 880 if phase == "preset" else 455
    args = ["xvfb-run", "-a", "-s", "-screen 0 1280x720x24",
            str(game / "RimWorldLinux"), "-savedatafolder=" + str(saved),
            "-logFile", str(log), "-quickstart=" + SCENARIO,
            "-screen-width", "1280", "-screen-height", "720"]
    completed = False
    with out.open("wb") as stream:
        process = subprocess.Popen(args, cwd=game, env=environment, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic() + timeout_seconds
            while process.poll() is None:
                if marker.is_file():
                    if phase == "coordinates":
                        valid = produced.is_file() and produced.stat().st_size > 100
                    else:
                        valid = ((produced / "Preset.xml").is_file()
                                 and (produced / "TerrainData.xml").is_file())
                    if not valid:
                        raise RuntimeError("Completed export has missing source files: " + phase)
                    # C# is parked after durable export and before any local map starts.
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=12)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=10)
                    completed = True
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(args, timeout_seconds)
                try:
                    process.wait(timeout=min(2, remaining))
                except subprocess.TimeoutExpired:
                    if log.is_file():
                        current_log = log.read_text(errors="replace")
                        if host.classify_unity_log(current_log).get("error_count"):
                            raise RuntimeError("Native " + phase +
                                               " Unity ERROR during export:\n" +
                                               current_log[-16000:])
        except (subprocess.TimeoutExpired, RuntimeError) as exc:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
            tail = log.read_text(errors="replace")[-12000:] if log.is_file() else "no Unity log"
            raise RuntimeError("Native " + phase + " export failed: " + str(exc) +
                               "\nUnity log tail:\n" + tail) from exc
    complete_log = log.read_text(errors="replace") if log.is_file() else ""
    observed = host.classify_unity_log(complete_log)
    if not completed or observed.get("error_count") or not complete_log:
        raise RuntimeError("Native " + phase + " failed; exported=" + str(completed) +
                           " exit=" + str(process.returncode) +
                           " ERROR=" + str(observed.get("errors", [])[:4]) +
                           " Unity log tail:\n" + complete_log[-16000:])
    print("AMJ Japan production " + phase +
          " exported; stopped before local colony generation", flush=True)

def main(root,output,gis,acceptance=False):
    root=host.assert_root(root)
    source_game=root/"game"
    if not (source_game/"Version.txt").read_text().startswith("1.6."):
        raise RuntimeError("Expected isolated RimWorld Linux 1.6")
    for folder,pid in MODS:
        src=source_game/"Mods"/folder
        if src.is_symlink() or host.pid_of(src)!=pid or not (src/".amj-test-stage.json").exists():
            raise RuntimeError("Pinned provider absent: "+folder)
    sdk=Path.home()/".dotnet/dotnet"
    if not sdk.exists():
        raise RuntimeError("Native dotnet SDK missing")
    if output.exists():
        raise RuntimeError("Refusing overwrite of existing production artifact directory")
    with tempfile.TemporaryDirectory(prefix="amj-japan-world-production-",dir=root/"runs") as temp:
        scratch=Path(temp)
        game=scratch/"game"
        checked(["cp","-a","--reflink=auto",str(source_game),str(game)],timeout=360)
        mods=game/"Mods"
        managed=game/"RimWorldLinux_Data"/"Managed"
        harmony=host._native16_library(mods/"Framework_Harmony","0Harmony.dll")
        quickdll=host._native16_library(mods/"Framework_Quickstarts","Quickstarts.dll")
        wb=host._native16_library(mods/"AMJ_Worldbuilder_Research","Worldbuilder.dll")
        envdll=host._native16_library(mods/"AMJ_Environment","AncientMedievalJapanEnvironment.dll")
        project=ET.fromstring(quick.compile_project(SOURCE,managed,harmony,quickdll,envdll))
        for el in project.findall("./PropertyGroup/AssemblyName"):
            el.text="JapanWorldPresetBuilder16"
        ref=ET.SubElement(project.find("./ItemGroup"),"Reference",{"Include":"Worldbuilder"})
        ET.SubElement(ref,"HintPath").text=str(wb)
        ET.SubElement(ref,"Private").text="false"
        proj=scratch/"net481"/"Builder.csproj"
        proj.parent.mkdir()
        ET.ElementTree(project).write(proj,encoding="utf-8",xml_declaration=True)
        environment=os.environ.copy()
        environment.update({"DOTNET_CLI_HOME":str(scratch/"dotnet-home"),
                            "NUGET_PACKAGES":str(scratch/"nuget-packages"),
                            "DOTNET_CLI_TELEMETRY_OPTOUT":"1"})
        compiled=scratch/"compiled"
        checked([str(sdk),"build",str(proj),"--nologo","-c","Release",
                 "-p:NuGetAudit=false","--output",str(compiled)],
                env=environment,timeout=360)
        binary=compiled/"JapanWorldPresetBuilder16.dll"
        if not binary.is_file():
            raise RuntimeError("Production builder assembly missing")

        # This is a real runtime component shipped with the standalone Japan
        # preset. Worldbuilder otherwise retains the prior random planet's
        # tile mutators on tiles absent from the saved mutator list.
        runtime_project=ET.fromstring(quick.compile_project(
            RUNTIME_SOURCE,managed,harmony,quickdll,envdll))
        for el in runtime_project.findall("./PropertyGroup/AssemblyName"):
            el.text="AMJJapanWorldPresetRestore16"
        runtime_ref=ET.SubElement(runtime_project.find("./ItemGroup"),"Reference",
                                  {"Include":"Worldbuilder"})
        ET.SubElement(runtime_ref,"HintPath").text=str(wb)
        ET.SubElement(runtime_ref,"Private").text="false"
        runtime_proj=scratch/"runtime-net481"/"Runtime.csproj"
        runtime_proj.parent.mkdir(parents=True)
        ET.ElementTree(runtime_project).write(runtime_proj,encoding="utf-8",xml_declaration=True)
        runtime_compiled=scratch/"runtime-compiled"
        checked([str(sdk),"build",str(runtime_proj),"--nologo","-c","Release",
                 "-p:NuGetAudit=false","--output",str(runtime_compiled)],
                env=environment,timeout=360)
        runtime_binary=runtime_compiled/"AMJJapanWorldPresetRestore16.dll"
        if not runtime_binary.is_file():
            raise RuntimeError("Japan preset runtime assembly missing")
        fixture=mods/"AMJ_JapanWorld_BuildOnly"
        (fixture/"About").mkdir(parents=True)
        (fixture/"Assemblies").mkdir()
        meta=ET.Element("ModMetaData")
        ET.SubElement(meta,"name").text="AMJ Japan World production build only"
        ET.SubElement(meta,"packageId").text=PACKAGE
        versions=ET.SubElement(meta,"supportedVersions")
        ET.SubElement(versions,"li").text="1.6"
        ET.ElementTree(meta).write(fixture/"About/About.xml",encoding="utf-8",xml_declaration=True)
        shutil.copy2(binary,fixture/"Assemblies"/binary.name)
        saved=scratch/"save"
        config=saved/"Config"
        config.mkdir(parents=True)
        data=ET.Element("ModsConfigData")
        ET.SubElement(data,"version").text=(source_game/"Version.txt").read_text().strip()
        active=ET.SubElement(data,"activeMods")
        for pid in ("brrainz.harmony","ludeon.rimworld",
                    "oskarpotocki.vanillafactionsexpanded.core",
                    "ferny.worldbuilder","rimworks.rimlogging","rimworks.quickstarts",
                    "sucro.ancientmedievaljapan.environment",PACKAGE):
            ET.SubElement(active,"li").text=pid
        ET.SubElement(data,"knownExpansions")
        ET.ElementTree(data).write(config/"ModsConfig.xml",encoding="utf-8",xml_declaration=True)
        (config/"Prefs.xml").write_text("<PrefsData><devMode>True</devMode><resetModsConfigOnCrash>False</resetModsConfigOnCrash></PrefsData>")
        home=scratch/"home"
        home.mkdir()
        environment.update({"HOME":str(home),"XDG_CONFIG_HOME":str(home/".config"),
                            "XDG_DATA_HOME":str(home/".local/share"),
                            "RIMWORLD_QUICKSTART":SCENARIO})
        environment.pop("STEAM_COMPAT_DATA_PATH",None)
        centres=scratch/"native-centres.csv"
        environment["AMJ_JAPAN_COORDINATE_EXPORT"]=str(centres)
        launch(game,saved,scratch,environment,"coordinates",centres)
        if not centres.is_file():
            raise RuntimeError("Real RimWorld tile coordinates not exported")
        coast=scratch/"coast.geojson"
        checked([gis,str(RESEARCH/"BuildJapanCoastlinePrototype.py"),
                 "--output",str(coast),"--report",str(scratch/"coast-qa.json")],timeout=120)
        mask=scratch/"landmask.csv"
        checked([gis,str(RESEARCH/"ProjectJapanCoastlineToTiles.py"),
                 "--coastline",str(coast),"--tile-centers",str(centres),
                 "--output-csv",str(mask),"--output-qa",str(scratch/"landmask-qa.json")],timeout=210)
        regional=scratch/"regional.csv"
        terrain=checked([gis,str(RESEARCH/"BuildJapanRegionalTerrain.py"),
                         "--land-mask",str(mask),"--output",str(regional),
                         "--report",str(scratch/"regional-qa.json"),
                         "--fetch","--max-tiles","120"],timeout=510,allow_partial=True)
        if not regional.is_file():
            raise RuntimeError("Regional terrain missing: "+terrain.stderr[-800:])
        presetdir=scratch/"export"
        del environment["AMJ_JAPAN_COORDINATE_EXPORT"]
        environment.update({"AMJ_JAPAN_WORLD_MASK_CSV":str(mask),
                            "AMJ_JAPAN_REGIONAL_CSV":str(regional),
                            "AMJ_JAPAN_PRESET_OUT":str(presetdir)})
        launch(game,saved,scratch,environment,"preset",presetdir)
        if not (presetdir/"Preset.xml").is_file() or not (presetdir/"TerrainData.xml").is_file():
            raise RuntimeError("Worldbuilder XML pair not exported")
        (output/"Worldbuilder"/"AMJ_Japan_World_Prototype").mkdir(parents=True)
        dest=output/"Worldbuilder"/"AMJ_Japan_World_Prototype"
        shutil.copy2(presetdir/"Preset.xml",dest/"Preset.xml")
        shutil.copy2(presetdir/"TerrainData.xml",dest/"TerrainData.xml")
        shutil.copy2(scratch/"regional-qa.json",output/"regional-qa.json")
        shutil.copy2(scratch/"landmask-qa.json",output/"landmask-qa.json")
        (output/"About").mkdir()
        shutil.copy2(Path(__file__).resolve().parent/"AMJ-Japan-World"/"About"/"About.xml",output/"About"/"About.xml")
        (output/"Assemblies").mkdir()
        shutil.copy2(runtime_binary,output/"Assemblies"/runtime_binary.name)
        if acceptance:
            import accept_japan_world_preset16 as playable
            playable.run(game,saved,scratch,output,managed,harmony,quickdll,wb,
                         envdll,sdk,environment,fixture)
        print(json.dumps({"result":"GENERATED","preset_files":[str(p.name) for p in dest.iterdir()],
                          "regional_quality":json.loads((output/"regional-qa.json").read_text()).get("status")},
                         ensure_ascii=False))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("/srv/amj-rimworld"))
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--gis-python",required=True)
    p.add_argument("--acceptance",action="store_true",
                   help="Run one additional game start and genuine saved-game reload")
    a=p.parse_args()
    main(a.root,a.output,a.gis_python,a.acceptance)
