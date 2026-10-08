# -*- coding: utf-8 -*-
"""Offline qualification of ITEM8_GENERATION_DRIVER.ps1 (qualification-only).

Python 3 (the frozen Checkpoint I generation tooling is Python-3-only) driving
Windows PowerShell 5.1. Nothing here touches SFM, the installed deployment, the
live Master or the real %PUBLIC% / Documents folders: every path is a sandbox
under the OS temp directory.

1. The driver's Section 1 is the frozen Session 2 section 2.1 block
   (SESSION2_RUNBOOK.md at 0597927) byte-for-byte, except its two placeholder
   lines, filled from -RepoRoot / -Game.
2. End to end in a sandbox SFM game root holding real G1 published by the real
   sidecar publisher, the real previous app (9a78fc96...), the real launcher,
   adapter, projection, Normalizer, shared package and sidecar reader bytes:
   attempt creation, preflight gates (residue, tamper, OWNER-1), deployment by
   temporary sibling + replacement, the real G1 -> exact G2 switch (frozen
   S2-PhaseA/S2-PhaseB), readback, log collection, exact G1 finalization
   (frozen S2-Finalize / S2-VerifyUntouched), qualification removal, and both
   dispositions (FAIL/INCONCLUSIVE restores 9a78fc96...; PASS keeps the
   candidate), sealing, and write-once refusals.

Usage: python test_item8_generation_driver.py
"""
from __future__ import print_function

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

_THIS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_THIS, os.pardir, os.pardir))
sys.path.insert(0, _THIS)
import item8_evidence_reader as reader  # noqa: E402

DRIVER = os.path.join(_THIS, "ITEM8_GENERATION_DRIVER.ps1")
MANIFEST = os.path.join(_THIS, "ITEM8_FIXTURE_MANIFEST.json")
PROBE = os.path.join(_THIS, "CPM_Item8_Probe.py")
SANDBOX = os.path.join(tempfile.gettempdir(), "cpm_item8_driver_sandbox")
CANDIDATE = "bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5"
PREVIOUS = "9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900"
G1 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
G2 = "54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7"
G1_SIDECAR = "bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b"
RESULTS = []
RUNS = []


def check(name, ok, value=None):
    RESULTS.append((name, bool(ok), value))
    print("[%s] %s" % ("PASS" if ok else "FAIL", name))
    if not ok and value is not None:
        print("      value: %r" % (value,))


def _read(path):
    with open(path, "rb") as f:
        return f.read()


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _write(path, data):
    d = os.path.dirname(path)
    if not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "wb") as f:
        f.write(data)


def _git_show(spec):
    return subprocess.check_output(["git", "-C", _REPO, "show", spec])


# ---------------------------------------------------------------------------
# 1. Frozen block equivalence
# ---------------------------------------------------------------------------
def frozen_block():
    md = _git_show("0597927:real_sfm_qualification/cpm_session2/SESSION2_RUNBOOK.md").decode("utf-8").replace("\r\n", "\n")
    cur = _read(os.path.join(_REPO, "real_sfm_qualification", "cpm_session2", "SESSION2_RUNBOOK.md")).decode("utf-8").replace("\r\n", "\n")
    check("frozen.runbook_unchanged_since_0597927", md == cur)
    block = re.search(r"### 2\.1 Set-up \(Windows PowerShell 5\.1\)\n.*?```powershell\n(.*?)```\n", md, re.S).group(1)
    frozen = block.split("\n")[:-1]
    drv = _read(DRIVER).decode("ascii").split("\n")
    start = drv.index("# ---- CPM Session 2 shell set-up. Fill the two placeholders, then paste the whole block. ----")
    section = drv[start:start + len(frozen)]
    diffs = [(i, a, b) for i, (a, b) in enumerate(zip(frozen, section)) if a != b]
    check("frozen.block_length", len(section) == len(frozen) == 158, len(frozen))
    check("frozen.only_placeholders_filled", diffs == [
        (1, '$R    = "<repository root>"', "$R    = $RepoRoot"),
        (2, '$GAME = "<SFM game>"            # the folder containing sfm.exe',
         "$GAME = $Game                 # the folder containing sfm.exe")], diffs)
    rest = "\n".join(drv[start + len(frozen):])
    for name in ("S2-Prepare", "S2-PhaseA", "S2-PhaseB", "S2-Finalize", "S2-VerifyUntouched", "S2-Inventory", "S2-Compare",
                 "Write-LibInventory", "Compare-LibInventory", "S2-Sha", "S2-New"):
        check("frozen.not_redefined.%s" % name, ("function %s" % name) not in rest)
    pythons = [l for l in rest.split("\n") if "& python" in l or "S2-Py " in l]
    check("frozen.no_generation_tooling_calls_outside_block", not any(t in rest for t in (
        "prepare-publish-g2", "activate-g2", "finalize --", "inventory --", "compare --"))
        and len(pythons) == 1 and "& python --version" in pythons[0], pythons)
    check("driver.ascii_lf", all(b < 128 for b in bytearray(_read(DRIVER))) and b"\r" not in _read(DRIVER))
    out = subprocess.check_output(["powershell.exe", "-NoProfile", "-Command",
                                   "$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('%s',[ref]$null,[ref]$e);"
                                   " if($e){$e|%%{$_.ToString()}} else {'PARSE OK'}; $PSVersionTable.PSVersion.Major" % DRIVER])
    lines = out.decode("utf-8", "replace").split()
    check("driver.parses_in_windows_powershell", "PARSE OK" in out.decode("utf-8", "replace"), out)
    check("driver.windows_powershell_5", lines[-1] == "5", lines[-1:])


# ---------------------------------------------------------------------------
# 2. Sandbox end to end
# ---------------------------------------------------------------------------
def pinned_bytes(path, pin):
    raw = _read(path)
    for data in (raw, raw.replace(b"\r\n", b"\n"), raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")):
        if _sha(data) == pin:
            return data
    raise AssertionError("no byte form of %s matches %s" % (path, pin))


def build_sandbox():
    if os.path.isdir(SANDBOX):
        shutil.rmtree(SANDBOX)
    m = json.loads(_read(MANIFEST).decode("ascii"))
    game = os.path.join(SANDBOX, "game")
    scripts = os.path.join(game, "usermod", "scripts")
    menu = os.path.join(scripts, "sfm", "mainmenu", "ChadChan3D")
    cfg = os.path.join(game, "usermod", "cfg")
    auth = os.path.join(cfg, "sfm_shared_authority")
    os.makedirs(auth)
    shutil.copyfile(os.path.join(_REPO, "sfm_defaultanimationgroups.txt"), os.path.join(cfg, "sfm_defaultanimationgroups.txt"))
    sys.path.insert(0, os.path.join(_REPO, "tools"))
    from sfm_master_sidecar import publisher
    publisher.publish(os.path.join(cfg, "sfm_defaultanimationgroups.txt"), auth)
    _write(os.path.join(scripts, "ChadChan3D_CPM", "SFM_Character_Preset_Manager.py"),
           _git_show("9d405c8:cpm/app/SFM_Character_Preset_Manager.py"))
    sources = {"sfm/mainmenu/ChadChan3D/SFM_Character_Preset_Manager.py": os.path.join(_REPO, "cpm", "app", "launcher", "SFM_Character_Preset_Manager.py"),
               "sfm/mainmenu/ChadChan3D/cpm_authority_adapter.py": os.path.join(_REPO, "cpm", "convergence", "cpm_authority_adapter.py"),
               "sfm/mainmenu/ChadChan3D/cpm_compat_v1_projection.py": os.path.join(_REPO, "cpm", "convergence", "cpm_compat_v1_projection.py"),
               "sfm/mainmenu/ChadChan3D/Rebuild_Control_Groups_Normalizer.py": os.path.join(_REPO, "audit_external_runtime", "Rebuild_Control_Groups_Normalizer.py")}
    for rel, pin in m["deployment"]["unchanged_menu_dependencies"].items():
        _write(os.path.join(scripts, *rel.split("/")), pinned_bytes(sources[rel], pin))
    pkg_src = os.path.join(_REPO, "tests", "sidecar", "qualification", "candidate_b2c_correction6", "sfm_master_authority_productionized")
    for name, pin in m["deployment"]["shared_package"]["files"].items():
        _write(os.path.join(menu, "sfm_master_authority_productionized", name), pinned_bytes(os.path.join(pkg_src, name), pin))
    _write(os.path.join(menu, "sfm_master_authority_productionized", "runtime.pyc"), b"bytecode")
    for name, pin in m["deployment"]["sidecar_reader"]["files"].items():
        _write(os.path.join(menu, "sfm_master_sidecar", name), pinned_bytes(os.path.join(_REPO, "tools", "sfm_master_sidecar", name), pin))
    _write(os.path.join(menu, "CPM_Session1_Probe.py"), _read(os.path.join(_REPO, "real_sfm_qualification", "cpm_session1", "CPM_Session1_Probe.py")))
    # Historical content of the kind the accepted inventory holds (OWNER-1).
    _write(os.path.join(scripts, "sfm", "mainmenu", "SFM_Character_Slider_Preset_Tool_0.1.1.py"),
           b"APP_ATTR = '_sfm_character_slider_preset_tool_window'\n")
    _write(os.path.join(scripts, "sfm", "gate_r2_deploy", "sfm_master_sidecar", "__init__.py"), b"# historical copy\n")
    _write(os.path.join(scripts, "sfm", "mainmenu", "ChadChan3D", "Checkpoint_X.py"), b"print('historical')\n")
    lib = os.path.join(SANDBOX, "docs", "SFM Character Preset Manager", "Characters", "mia--2e6533ed1490")
    _write(os.path.join(lib, "character.json"), b'{"profile": 1}\n')
    _write(os.path.join(lib, "Body Presets", "Body--preset-aaaaa.json"), b"{}\n")
    _write(os.path.join(SANDBOX, "docs", "krystal_fixture.dmx"), b"<krystal>")
    _write(os.path.join(SANDBOX, "docs", "mia_fixture.dmx"), b"<mia>")
    os.makedirs(os.path.join(SANDBOX, "public", "Documents"))
    _write(os.path.join(SANDBOX, "public", "Documents", "SFM_CSP_G18AN_SaveNewCopy.log"), b"[00:00:00.000000] G18AN_RUN x\n")
    return {"game": game, "scripts": scripts, "menu": menu, "cfg": cfg, "auth": auth, "lib": lib}


PS_PRELUDE = r"""
$ErrorActionPreference = "Continue"
$env:PUBLIC = "%(public)s"
. "%(driver)s" -RepoRoot "%(repo)s" -Game "%(game)s" | Out-Null
$LIB = "%(lib)s"
$ACCEPTED_SCRIPTS = "%(sandbox)s\accepted_inventory.txt"
if (-not (Test-Path -LiteralPath $ACCEPTED_SCRIPTS)) { I8-ScriptsInventory $ACCEPTED_SCRIPTS | Out-Null }
$ACCEPTED_SCRIPTS_SHA = S2-Sha $ACCEPTED_SCRIPTS
function Step([string]$Name, [scriptblock]$Body) {
    "<<STEP $Name BEGIN>>"
    try { & $Body 2>&1 | ForEach-Object { "$_" }; "<<END $Name OK>>" } catch { "<<END $Name STOP>> $($_.Exception.Message)" }
}
"""


def run_ps(paths, body):
    script = PS_PRELUDE % {"public": os.path.join(SANDBOX, "public"), "driver": DRIVER, "repo": _REPO, "game": paths["game"],
                           "lib": paths["lib"], "sandbox": SANDBOX} + body
    path = os.path.join(SANDBOX, "step.ps1")
    with open(path, "wb") as f:
        f.write(script.encode("ascii"))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
               PATH=os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", ""))
    out = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", path],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env).stdout.decode("utf-8", "replace")
    RUNS.append(out)
    with open(os.path.join(SANDBOX, "ps_transcript_%02d.txt" % len(RUNS)), "wb") as f:
        f.write(out.encode("utf-8"))
    steps = {}
    for m in re.finditer(r"<<STEP (\S+) BEGIN>>(.*?)<<END \1 (OK|STOP)>>([^\n]*)", out, re.S):
        steps[m.group(1)] = (m.group(3), m.group(2) + m.group(4))
    return steps, out


def attempt(name):
    return os.path.join(SANDBOX, "public", "Documents", "CPM_Item8", name)


def sandbox_end_to_end():
    p = build_sandbox()
    app = os.path.join(p["scripts"], "ChadChan3D_CPM", "SFM_Character_Preset_Manager.py")
    master = os.path.join(p["cfg"], "sfm_defaultanimationgroups.txt")
    check("sandbox.master_and_sidecar_are_production_g1", _sha(_read(master)) == G1
          and os.path.isfile(os.path.join(p["auth"], "sfm_master_0_%s.sfmsidecar" % G1_SIDECAR)))
    temp_before = set(n for n in os.listdir(tempfile.gettempdir()) if n.startswith("cpm_item8_preflight_"))
    docs = 'I8-New T1 -KrystalDocument "%s" -MiaDocument "%s"' % (os.path.join(SANDBOX, "docs", "krystal_fixture.dmx"),
                                                                 os.path.join(SANDBOX, "docs", "mia_fixture.dmx"))
    steps, out = run_ps(p, """
Step preflight_before_new { I8-Preflight T1 -Owner1Recorded }
Step new_t1 { %(docs)s }
Step new_t1_again { %(docs)s }
Step preflight_owner1_missing { I8-Preflight T1 }
""" % {"docs": docs})
    check("gate.preflight_requires_new", steps.get("preflight_before_new", ("",))[0] == "STOP", out[-1500:])
    check("new.created", steps.get("new_t1", ("",))[0] == "OK" and all(os.path.exists(os.path.join(attempt("T1"), f)) for f in (
        "authority_pins.json", "fixture_manifest.json", "operator_steps.md", "scene_snapshots", "library_inventories",
        "preset_readback", "logs", "restoration")), steps.get("new_t1"))
    pins = json.loads(_read(os.path.join(attempt("T1"), "authority_pins.json")).decode("utf-8"))
    check("new.authority_pins", pins["candidate_app_sha256"] == CANDIDATE and pins["previous_installed_app_sha256"] == PREVIOUS
          and pins["G1"]["master_sha256"] == G1 and pins["G2"]["master_sha256"] == G2 and pins["probe_sha256"] == _sha(_read(PROBE)))
    fm = json.loads(_read(os.path.join(attempt("T1"), "fixture_manifest.json")).decode("utf-8"))
    check("new.fixture_documents_hashed", fm["documents"]["krystal"]["sha256"] == _sha(b"<krystal>")
          and fm["documents"]["mia"]["sha256"] == _sha(b"<mia>") and fm["static_manifest_sha256"] == _sha(_read(MANIFEST)))
    check("new.operator_steps_from_template", b"attempt `T1`" in _read(os.path.join(attempt("T1"), "operator_steps.md")))
    check("new.write_once", steps.get("new_t1_again", ("",))[0] == "STOP")
    o1 = steps.get("preflight_owner1_missing", ("", ""))
    check("gate.owner1_required", o1[0] == "STOP" and "OWNER-1" in o1[1] and "SFM_Character_Slider_Preset_Tool_0.1.1.py" in out
          and "sfm/gate_r2_deploy/sfm_master_sidecar" in out, o1)
    check("gate.owner1_stop_writes_nothing", not os.listdir(os.path.join(attempt("T1"), "restoration"))
          and not os.path.exists(os.path.join(attempt("T1"), "generation")))
    # Residue and tamper gates (read-only STOPs).
    harness = os.path.join(p["menu"], "CPM_S4_Rollback_Harness.py")
    _write(harness, b"x")
    steps, out = run_ps(p, "Step residue { I8-Preflight T1 -Owner1Recorded }\n")
    check("gate.harness_residue_stops", steps.get("residue", ("",))[0] == "STOP" and "PRESENT:" in out, out[-800:])
    os.remove(harness)
    pointer = os.path.join(SANDBOX, "public", "Documents", "CPM_Session4", "ACTIVE_CAMPAIGN.txt")
    _write(pointer, b"S4A")
    steps, out = run_ps(p, "Step pointer { I8-Preflight T1 -Owner1Recorded }\n")
    check("gate.old_campaign_pointer_stops", steps.get("pointer", ("",))[0] == "STOP", out[-800:])
    os.remove(pointer)
    adapter = os.path.join(p["menu"], "cpm_authority_adapter.py")
    good = _read(adapter)
    _write(adapter, good + b"\n# tampered\n")
    steps, out = run_ps(p, "Step tamper { I8-Preflight T1 -Owner1Recorded }\n")
    check("gate.changed_dependency_stops", steps.get("tamper", ("",))[0] == "STOP" and "cpm_authority_adapter.py" in out, out[-800:])
    _write(adapter, good)
    unexpected = os.path.join(p["scripts"], "sfm", "mainmenu", "Unexpected_Qualification_Script.py")
    _write(unexpected, b"print('x')\n")
    steps, out = run_ps(p, "Step unexpected_script { I8-Preflight T1 -Owner1Recorded }\n")
    check("gate.unexpected_script_stops_and_is_named", steps.get("unexpected_script", ("",))[0] == "STOP"
          and "+sfm/mainmenu/Unexpected_Qualification_Script.py" in out, out[-800:])
    os.remove(unexpected)
    extra = os.path.join(p["scripts"], "ChadChan3D_CPM", "SFM_Character_Preset_Manager.pyc")
    _write(extra, b"x")
    steps, out = run_ps(p, "Step private_extra { I8-Preflight T1 -Owner1Recorded }\n")
    check("gate.private_folder_extra_file_stops", steps.get("private_extra", ("",))[0] == "STOP", out[-800:])
    os.remove(extra)
    check("gate.read_only_stops_wrote_nothing", not os.listdir(os.path.join(attempt("T1"), "restoration"))
          and not os.path.exists(os.path.join(attempt("T1"), "generation")))
    temp_after = set(n for n in os.listdir(tempfile.gettempdir()) if n.startswith("cpm_item8_preflight_"))
    check("gate.no_temporary_inventory_leaked", temp_after == temp_before, sorted(temp_after - temp_before))
    # Preflight, deployment, run-time evidence, generation switch.
    lib_preset = "Body Presets/I8 T1 E G2--preset-0a1b2.json"
    steps, out = run_ps(p, """
Step preflight { I8-Preflight T1 -Owner1Recorded }
Step preflight_again { I8-Preflight T1 -Owner1Recorded }
Step deploy { I8-Deploy T1 }
Step deploy_again { I8-Deploy T1 }
Step new_while_active { I8-New T9 -KrystalDocument "%(k)s" -MiaDocument "%(m)s" }
Step lib_e1 { I8-Library T1 library_E1_before_prompt }
Step switch { I8-GenerationSwitch T1 }
Step lib_compare { I8-LibraryCompare T1 library_E1_before_prompt library_E2_g2_active_prompt_open }
Step readback_missing { I8-Readback T1 E_g2_save "Body Presets/I8 T1 E G2--preset-*.json" }
""" % {"k": os.path.join(SANDBOX, "docs", "krystal_fixture.dmx"), "m": os.path.join(SANDBOX, "docs", "mia_fixture.dmx")})
    check("preflight.ok", steps.get("preflight", ("",))[0] == "OK" and "S2 BASELINE OK" in out and "I8 PREFLIGHT OK" in out, out[-2000:])
    before = json.loads(_read(os.path.join(attempt("T1"), "deployment_before.json")).decode("utf-8"))
    check("preflight.record", before["installed_app_sha256"] == PREVIOUS and before["owner1_recorded"] is True
          and before["historical_full_cpm_files"] == ["sfm/mainmenu/SFM_Character_Slider_Preset_Tool_0.1.1.py"]
          and before["historical_package_copies"] == ["sfm/gate_r2_deploy/sfm_master_sidecar"]
          and before["scripts_inventory_equals_accepted"] is True and before["cpm_log"]["exists"] is True
          and before["python_for_generation_tooling"].startswith("Python 3."), before)
    check("preflight.generation_baseline_exact_g1", json.loads(_read(os.path.join(attempt("T1"), "generation", "baseline_inventory.json"))
                                                                .decode("utf-8-sig"))["master_sha256"] == G1)
    check("preflight.write_once", steps.get("preflight_again", ("",))[0] == "STOP")
    check("deploy.ok", steps.get("deploy", ("",))[0] == "OK" and "I8 DEPLOYED" in out, out[-1500:])
    check("deploy.candidate_installed", _sha(_read(app)) == CANDIDATE and not os.path.exists(app + ".item8tmp"))
    check("deploy.backup_is_previous", _sha(_read(os.path.join(attempt("T1"), "restoration", "installed_app_backup.py"))) == PREVIOUS)
    check("deploy.probe_installed", _read(os.path.join(p["menu"], "CPM_Item8_Probe.py")) == _read(PROBE))
    check("deploy.pointer", _read(os.path.join(SANDBOX, "public", "Documents", "CPM_Item8", "ACTIVE_ATTEMPT.txt")) == b"T1")
    after = json.loads(_read(os.path.join(attempt("T1"), "deployment_after.json")).decode("utf-8"))
    check("deploy.record", after["installed_app_sha256"] == CANDIDATE and after["installed_probe_sha256"] == _sha(_read(PROBE)))
    check("deploy.write_once", steps.get("deploy_again", ("",))[0] == "STOP")
    check("deploy.single_active_attempt", steps.get("new_while_active", ("",))[0] == "STOP"
          and not os.path.exists(attempt("T9")))
    check("switch.ok", steps.get("switch", ("",))[0] == "OK" and "S2 PHASE A OK" in out and "S2 G2 ACTIVE OK" in out, out[-2500:])
    check("switch.live_master_is_exact_g2", _sha(_read(master)) == G2)
    act = json.loads(_read(os.path.join(attempt("T1"), "generation", "g2_activation_record.json")).decode("utf-8-sig"))
    check("switch.activation_record", act["success"] is True and act["pre_activation_master_sha256"] == G1
          and act["post_activation_master_sha256"] == G2)
    check("switch.library_inventory_identical", "LIBRARY IDENTICAL" in steps.get("lib_compare", ("", ""))[1])
    check("readback.zero_matches_stops", steps.get("readback_missing", ("",))[0] == "STOP")
    record = {"values": {"flex.Fat": {"representation": "MONO", "mono": 0.8}}}
    _write(os.path.join(p["lib"], *lib_preset.split("/")), json.dumps(record).encode("utf-8"))
    late = os.path.join(p["menu"], "Late_Unexpected.py")
    _write(late, b"x")
    steps, out = run_ps(p, """
Step remove_with_unexpected_file { I8-RemoveQualificationDeployment T1 }
""")
    check("remove.unexpected_change_stops_and_is_named", steps.get("remove_with_unexpected_file", ("",))[0] == "STOP"
          and "+sfm/mainmenu/ChadChan3D/Late_Unexpected.py" in out, out[-1200:])
    os.remove(late)
    # The refused removal wrote its write-once record path? It must not have: retrying is possible.
    check("remove.refusal_left_no_record", not os.path.exists(os.path.join(attempt("T1"), "restoration", "qualification_removal.json")))
    steps, out = run_ps(p, """
Step readback { I8-Readback T1 E_g2_save "Body Presets/I8 T1 E G2--preset-*.json" }
Step logs { I8-CollectLogs T1 F_final }
Step disposition_too_early { I8-Disposition T1 -Verdict INCONCLUSIVE }
Step finalize { I8-Finalize T1 }
Step disposition_before_removal { I8-Disposition T1 -Verdict INCONCLUSIVE }
Step remove { I8-RemoveQualificationDeployment T1 }
Step disposition { I8-Disposition T1 -Verdict INCONCLUSIVE }
""")
    rb = os.path.join(attempt("T1"), "preset_readback", "E_g2_save.json")
    check("readback.copied_and_parsed", steps.get("readback", ("",))[0] == "OK"
          and reader.preset_value(reader.load_json(rb), "Fat") == {"mono": 0.8})
    src = json.loads(_read(os.path.join(attempt("T1"), "preset_readback", "E_g2_save.source.json")).decode("utf-8"))
    check("readback.source_record", src["library_relative_path"] == lib_preset and src["sha256"] == _sha(_read(rb)))
    check("logs.collected", steps.get("logs", ("",))[0] == "OK"
          and _read(os.path.join(attempt("T1"), "logs", "F_final__SFM_CSP_G18AN_SaveNewCopy.log")).startswith(b"[00:00:00"))
    check("finalize.exact_g1", steps.get("finalize", ("",))[0] == "OK" and "S2 RESTORED EXACT G1" in out
          and _sha(_read(master)) == G1, out[-2000:])
    check("finalize.g2_sidecar_removed", sorted(n for n in os.listdir(p["auth"]) if n.endswith(".sfmsidecar"))
          == ["sfm_master_0_%s.sfmsidecar" % G1_SIDECAR])
    check("disposition.requires_removal_first", steps.get("disposition_before_removal", ("",))[0] == "STOP"
          and steps.get("disposition_too_early", ("",))[0] == "STOP")
    check("remove.ok", steps.get("remove", ("",))[0] == "OK" and not os.path.exists(os.path.join(p["menu"], "CPM_Item8_Probe.py"))
          and not os.path.exists(os.path.join(SANDBOX, "public", "Documents", "CPM_Item8", "ACTIVE_ATTEMPT.txt")), out[-1500:])
    check("remove.candidate_still_installed_pending_adjudication",
          json.loads(_read(os.path.join(attempt("T1"), "restoration", "qualification_removal.json")).decode("utf-8"))
          ["installed_app_sha256"] == CANDIDATE)
    check("remove.live_evidence_sealed", os.path.isfile(os.path.join(attempt("T1"), "restoration", "live_evidence_sha256.txt")))
    check("disposition.inconclusive_restores_previous", steps.get("disposition", ("",))[0] == "OK" and _sha(_read(app)) == PREVIOUS,
          out[-1500:])
    final = os.path.join(attempt("T1"), "restoration", "scripts_inventory_final.txt")
    check("disposition.inventory_equals_accepted", _read(final) == _read(os.path.join(SANDBOX, "accepted_inventory.txt")))
    check("disposition.sealed_and_verifiable", reader.verify_sha256sums(attempt("T1"))["ok"], reader.verify_sha256sums(attempt("T1")))
    live = dict(l.split("  ", 1)[::-1] for l in _read(os.path.join(attempt("T1"), "restoration", "live_evidence_sha256.txt"))
                .decode("utf-8").split("\n") if l)
    sums = dict(l.split("  ", 1)[::-1] for l in _read(os.path.join(attempt("T1"), "SHA256SUMS.txt")).decode("utf-8").split("\n") if l)
    check("disposition.live_evidence_unchanged_at_seal", all(sums.get(k) == v for k, v in live.items()))
    disp = json.loads(_read(os.path.join(attempt("T1"), "restoration", "disposition.json")).decode("utf-8"))
    check("disposition.record", disp["verdict"] == "INCONCLUSIVE" and disp["installed_app_sha256"] == PREVIOUS
          and disp["authority_restoration"] == "restore_compare.json")
    # PASS path in a new attempt: candidate retained; untouched authority proven.
    # One physical document serves both fixture contexts (owner decision): pass the same path twice.
    same = os.path.join(SANDBOX, "docs", "mia_fixture.dmx")
    docs2 = 'I8-New T2 -KrystalDocument "%s" -MiaDocument "%s"' % (same, same)
    steps, out = run_ps(p, """
Step new { %(docs)s }
Step preflight { I8-Preflight T2 -Owner1Recorded }
Step deploy { I8-Deploy T2 }
Step finalize { I8-Finalize T2 }
Step remove { I8-RemoveQualificationDeployment T2 }
Step disposition { I8-Disposition T2 -Verdict PASS }
Step disposition_again { I8-Disposition T2 -Verdict FAIL }
""" % {"docs": docs2})
    check("pass.flow", all(steps.get(s, ("",))[0] == "OK" for s in ("new", "preflight", "deploy", "finalize", "remove", "disposition")),
          dict((k, v[0]) for k, v in steps.items()))
    fm2 = json.loads(_read(os.path.join(attempt("T2"), "fixture_manifest.json")).decode("utf-8"))
    check("new.one_document_for_both_contexts", fm2["documents"]["krystal"]["sha256"] == fm2["documents"]["mia"]["sha256"]
          == _sha(b"<mia>") and fm2["documents"]["krystal"]["path"] == fm2["documents"]["mia"]["path"])
    check("pass.authority_untouched_proof", "S2 UNTOUCHED" in out and json.loads(_read(os.path.join(
        attempt("T2"), "generation", "untouched_compare.json")).decode("utf-8-sig"))["exact_match"] is True)
    check("pass.candidate_retained", _sha(_read(app)) == CANDIDATE)
    acc = dict(l.split("\t") for l in _read(os.path.join(SANDBOX, "accepted_inventory.txt")).decode("utf-8").split("\n") if l)
    fin = dict(l.split("\t") for l in _read(os.path.join(attempt("T2"), "restoration", "scripts_inventory_final.txt"))
               .decode("utf-8").split("\n") if l)
    diff = sorted(k for k in set(acc) | set(fin) if acc.get(k) != fin.get(k))
    check("pass.only_app_line_differs", diff == ["ChadChan3D_CPM/SFM_Character_Preset_Manager.py"]
          and fin[diff[0]] == CANDIDATE, diff)
    check("pass.disposition_write_once", steps.get("disposition_again", ("",))[0] == "STOP" and _sha(_read(app)) == CANDIDATE)
    check("pass.sealed", reader.verify_sha256sums(attempt("T2"))["ok"])
    steps, out = run_ps(p, """
Step new { %(docs)s }
Step preflight { I8-Preflight T3 -Owner1Recorded }
""" % {"docs": docs.replace("T1", "T3")})
    check("pass.later_preflight_refuses_until_policy_decided", steps.get("preflight", ("", ""))[0] == "STOP"
          and CANDIDATE in steps["preflight"][1], steps.get("preflight"))
    check("sandbox.real_documents_untouched", not os.path.exists(os.path.join(os.environ.get("PUBLIC") or tempfile.gettempdir(),
                                                                              "Documents", "CPM_Item8", "T1")))


def main():
    print("Interpreter: %s" % sys.version.split()[0])
    if sys.version_info[0] < 3:
        print("This driver test needs Python 3 (the frozen generation tooling is Python-3-only).")
        sys.exit(2)
    frozen_block()
    sandbox_end_to_end()
    passed = sum(1 for r in RESULTS if r[1])
    print("\nRESULT: %d/%d %s" % (passed, len(RESULTS), "ALL PASS" if passed == len(RESULTS) else "SOME FAILED"))
    if passed != len(RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
