#!/usr/bin/env python3
"""One opt-in real-game acceptance after production XML export.

Two isolated launches: Worldbuilder Mod preset -> first Japan colony/map/save;
vanilla autostart.rws -> loaded Japan colony. Never mutates the source game.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET

import environment_quickstart16 as quick
import stage_integrations as host

SOURCE = Path(__file__).with_name("JapanWorldPlayableAcceptance16.cs")
PACKAGE = "sucro.amj.japanworld.acceptance"
PRESET_PACKAGE = "sucro.amj.japanworld"
QUICKSTART = "AMJJapanPlayableAcceptance"


def execute(game, saved, scratch, environment, phase, arguments, marker, seconds):
    if marker.exists():
        raise RuntimeError("Refusing previous acceptance marker: " + str(marker))
    log = scratch / ("accept-" + phase + "-unity.log")
    output = scratch / ("accept-" + phase + "-launcher.log")
    args = ["xvfb-run", "-a", "-s", "-screen 0 1280x720x24",
            str(game / "RimWorldLinux"), "-savedatafolder=" + str(saved),
            "-logFile", str(log), "-screen-width", "1280", "-screen-height", "720",
            *arguments]
    with output.open("wb") as out:
        process = subprocess.Popen(args, cwd=game, env=environment, stdout=out,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            process.wait(timeout=seconds)
        except subprocess.TimeoutExpired as exc:
            import signal
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)
            tail = log.read_text(errors="replace")[-14000:] if log.exists() else "no log"
            raise RuntimeError("Japan " + phase + " timed out:\n" + tail) from exc
    native_log = log.read_text(errors="replace") if log.is_file() else ""
    parsed = host.classify_unity_log(native_log)
    if process.returncode != 0 or parsed.get("error_count") or not marker.is_file():
        raise RuntimeError("Japan " + phase + " FAIL; exit=" + str(process.returncode) +
                           " marked=" + str(marker.is_file()) +
                           " errors=" + str(parsed.get("errors", [])[:5]) +
                           "\nUnity log tail:\n" + native_log[-15000:])
    return {"result": "PASS", "exit_code": process.returncode, "unity_errors": 0,
            "tile_id": int(marker.read_text().strip())}


def run(game, saved, scratch, output, managed, harmony, quickdll, wb,
        envdll, sdk, environment, fixture):
    """Called once at the end of a manually requested production run."""
    project = ET.fromstring(quick.compile_project(SOURCE, managed, harmony, quickdll, envdll))
    for el in project.findall("./PropertyGroup/AssemblyName"):
        el.text = "JapanWorldPlayableAcceptance16"
    ref = ET.SubElement(project.find("./ItemGroup"), "Reference", {"Include": "Worldbuilder"})
    ET.SubElement(ref, "HintPath").text = str(wb)
    ET.SubElement(ref, "Private").text = "false"
    project_path = scratch / "accept-build" / "Acceptance.csproj"
    project_path.parent.mkdir(parents=True)
    ET.ElementTree(project).write(project_path, encoding="utf-8", xml_declaration=True)
    compiled = scratch / "accept-compiled"
    build = subprocess.run([str(sdk), "build", str(project_path), "--nologo", "-c",
                            "Release", "-p:NuGetAudit=false", "--output", str(compiled)],
                           env=environment, capture_output=True, text=True, timeout=360)
    if build.returncode:
        raise RuntimeError("Japan acceptance C# build failed: " +
                           (build.stdout + build.stderr)[-8000:])
    binary = compiled / "JapanWorldPlayableAcceptance16.dll"
    if not binary.is_file():
        raise RuntimeError("Japan acceptance native DLL absent")
    shutil.copy2(binary, fixture / "Assemblies" / binary.name)

    mod = game / "Mods" / "AMJ_JapanWorld_PresetAcceptance"
    if mod.exists():
        raise RuntimeError("Refusing to overwrite acceptance Mod staging")
    shutil.copytree(output, mod)
    meta = ET.parse(mod / "About" / "About.xml")
    if meta.getroot().findtext("packageId") != PRESET_PACKAGE:
        raise RuntimeError("Published Japan preset identity mismatch")
    config_path = saved / "Config" / "ModsConfig.xml"
    config = ET.parse(config_path)
    active = config.getroot().find("activeMods")
    if active is None:
        raise RuntimeError("Missing isolated ModsConfig.activeMods")
    ET.SubElement(active, "li").text = PRESET_PACKAGE
    config.write(config_path, encoding="utf-8", xml_declaration=True)

    # The producer had already written an identical preset to its disposable
    # savedata. Delete only that generated scratch copy to prove Mod discovery.
    duplicate = saved / "Worldbuilder" / "AMJ_Japan_World_Prototype"
    if duplicate.is_symlink():
        raise RuntimeError("Generated preset savedata unexpectedly symlinked")
    if duplicate.is_dir():
        shutil.rmtree(duplicate)

    new_marker = scratch / "new-game-ready.txt"
    reload_marker = scratch / "reloaded-game-ready.txt"
    environment = environment.copy()
    environment["RIMWORLD_QUICKSTART"] = QUICKSTART
    environment["AMJ_JAPAN_ACCEPT_NEW_READY"] = str(new_marker)
    environment.pop("AMJ_JAPAN_ACCEPT_RELOAD_READY", None)
    report = scratch / "acceptance-quickstart.json"
    first = execute(game, saved, scratch, environment, "new", [
        "-quickstart=" + QUICKSTART, "-quickstartreport=" + str(report),
        "-quickstarttimeout=520"], new_marker, 540)
    if not report.exists():
        raise RuntimeError("Quickstarts native new-game verification report absent")
    verified = json.loads(report.read_text())
    if (verified.get("passed") is not True or verified.get("failed") != 0 or
        verified.get("logErrors") != 0 or verified.get("logTruncated") is True or
        verified.get("quickstart") != QUICKSTART):
        raise RuntimeError("Native new-game verification did not pass: " +
                           json.dumps(verified)[-5000:])

    environment.pop("RIMWORLD_QUICKSTART", None)
    environment["AMJ_JAPAN_ACCEPT_RELOAD_READY"] = str(reload_marker)
    second = execute(game, saved, scratch, environment, "reload",
                     [], reload_marker, 360)
    if first["tile_id"] != second["tile_id"]:
        raise RuntimeError("Saved settlement tile changed between game processes")
    receipt = {"result": "PASS", "version": "1.6",
               "scenario": QUICKSTART,
               "new_game": first, "save_reload": second,
               "preset_mod": PRESET_PACKAGE,
               "mod_files": ["About/About.xml",
                             "Worldbuilder/AMJ_Japan_World_Prototype/Preset.xml",
                             "Worldbuilder/AMJ_Japan_World_Prototype/TerrainData.xml"]}
    (output / "playability-acceptance.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print("AMJ Japan playability acceptance " + json.dumps(receipt), flush=True)
