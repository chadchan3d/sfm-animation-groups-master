# -*- coding: utf-8 -*-
"""Offline preparation qualification of the CPM item-8 probe and evidence reader.

Runs the ACTUAL item-8 probe file as SFM runs a Scripts-menu script
(PyRun_FileExFlags into the shared __main__ dictionary) inside the R15 suite's
fake SFM game root, with the ACTUAL R15 launcher and the exact item-7 candidate
app (a real ProdWindow), under real PySide/Qt 4.8 (embedded 2.7.5) and the
behavioural Qt 4.8 model (2.7.5 and 3.10). Also qualifies the offline evidence
reader against the candidate's own retained log formats and file formats, and
the static fixture/pin manifest against its repository sources.

Stubbed boundaries only (SFM scene and DME): the scene readers' leaf
(side_snapshot), p03_model_animsets / p01_all_supported_flex_bindings rows,
dm(). binding_snapshot is the candidate's own. The canonical broker is either a
strict recording fake or the REAL shared-package broker.

Mocks cannot qualify real DME objects, the real installed deployment or the real
broker under SFM; those are the live item-8 campaign.

Usage: --phase=run   (internal: --child=<scenario> --qt=<real|model> --root=<dir>)
"""
from __future__ import print_function

import ast
import gc
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import types
import weakref

_THIS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_THIS, os.pardir, os.pardir))
sys.path.insert(0, os.path.join(_REPO, "cpm", "convergence", "tests"))
sys.path.insert(0, _THIS)
import test_cpm_app_r15_namespace_isolation as r15  # noqa: E402
import item8_evidence_reader as reader  # noqa: E402

PROBE = os.path.join(_THIS, "CPM_Item8_Probe.py")
DRIVER = os.path.join(_THIS, "ITEM8_GENERATION_DRIVER.ps1")
MANIFEST = os.path.join(_THIS, "ITEM8_FIXTURE_MANIFEST.json")
APP = os.path.join(_REPO, "cpm", "app", "SFM_Character_Preset_Manager.py")
LAUNCHER = os.path.join(_REPO, "cpm", "app", "launcher", "SFM_Character_Preset_Manager.py")
DESIGN = os.path.join(_REPO, "cpm", "qualification", "ITEM8_POST_CLEANUP_REAL_SFM_QUALIFICATION_DESIGN.md")
SHARED_PACKAGE_PARENT = os.path.join(_REPO, "tests", "sidecar", "qualification", "candidate_b2c_correction6")
FIXTURE_ROOT = os.path.join(r15.tempfile.gettempdir(), "cpm_item8_probe_fixture")
CLASSIFY_ROOT = os.path.join(r15.tempfile.gettempdir(), "cpm_item8_classify_g1")
CANDIDATE = "bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5"
PREVIOUS = "9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900"
ITEM6_APP = "1e8668717f9a4a1def0900c6b51e20cb9a7676cc365244eab5c31233f133eeeb"
LAUNCHER_SHA = "996ca483d625d37feb8d8f38a8d13db16f999d4189d98434db9c284a0a458c51"
G1 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
G2 = "54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7"
RESULTS = []
c = r15.c
PY2 = r15.PY2
_TEXT = r15._TEXT if hasattr(r15, "_TEXT") else (unicode if PY2 else str)  # noqa: F821


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


def _manifest():
    return json.loads(_read(MANIFEST).decode("ascii"))


# ===========================================================================
# Static: pins, probe shape, forbidden behaviour
# ===========================================================================
FORBIDDEN_NAMES = set([
    "get_broker", "acquire", "acquire_or_reuse_views", "acquire_cohort", "acquire_view_lease", "open_stage",
    "release", "release_view_lease", "register_unreleased_lease", "retry_unreleased_leases",
    "invalidate_generation", "prod_cpm_authorize_operation", "prod_cpm_open_adapter", "prod_cpm_open_fit_stage",
    "prod_cpm_release_fit_stage", "prod_probe_semantic_provider", "prod_scope", "semantic_provider_ready",
    "prod_cpm_request_stale_rebuild_if_needed", "prod_cpm_run_stale_rebuild", "get_semantic_provider",
    "log_line", "reset_log", "prod_resolve", "g11a_resolve_target", "G18AN_POST_FIT_ACTION_STATE",
    "QTimer", "singleShot", "QMessageBox", "QDialog", "QWidget", "exec_", "show", "connect", "installEventFilter",
    "setattr", "delattr", "StartUndo", "FinishUndo", "AbortUndoableOperation", "SetValue", "reload",
    "execfile", "exec", "eval", "processEvents", "remove", "unlink", "rename", "rmtree", "makedirs",
    "mkdir", "write_side", "prod_apply", "fit_stage", "guard", "StartProdTool", "close", "deleteLater",
])
ALLOWED_NS_CALLS = set(["p03_model_animsets", "p01_all_supported_flex_bindings", "binding_snapshot", "dm"])
ALLOWED_BROKER_CALLS = set(["outstanding_lease_count", "unreleased_lease_count", "provider_counters",
                            "view_cache_entry_count", "recent_diagnostics", "ledger_snapshot"])


def _names_used(tree):
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
    return out


def _const(node):
    """String constant of an AST node (Python 2 Str / Index(Str), Python 3 Constant)."""
    if type(node).__name__ == "Index":
        node = node.value
    return getattr(node, "s", getattr(node, "value", None))


def _call_closure(tree, roots):
    defs = dict((n.name, n) for n in tree.body if isinstance(n, ast.FunctionDef))
    seen = {}

    def visit(name):
        if name in seen or name not in defs:
            return
        names = set()
        for n in ast.walk(defs[name]):
            if isinstance(n, ast.Call):
                f = n.func
                names.add(f.id if isinstance(f, ast.Name) else getattr(f, "attr", "?"))
        seen[name] = names
        for x in names:
            visit(x)
    for r in roots:
        visit(r)
    return seen


def static_pins():
    m = _manifest()
    app = _read(APP)
    check("pins.candidate_app_is_bfba4d3a", _sha(app) == CANDIDATE == m["apps"]["candidate_sha256"])
    check("pins.launcher_is_996ca483", _sha(_read(LAUNCHER).replace(b"\r\n", b"\n")) == LAUNCHER_SHA)
    try:
        prev = subprocess.check_output(["git", "-C", _REPO, "show", "9d405c8:cpm/app/SFM_Character_Preset_Manager.py"])
        check("pins.previous_app_restorable_from_git", _sha(prev) == PREVIOUS == m["apps"]["previous_installed_sha256"])
    except Exception as exc:  # noqa: BLE001
        check("pins.previous_app_restorable_from_git", False, repr(exc))
    design = _read(DESIGN).decode("utf-8")
    check("pins.design_g1_g2", G1 in design and G2 in design and CANDIDATE in design and PREVIOUS in design)
    check("pins.manifest_g1_g2", m["authority"]["G1"]["master_sha256"] == G1 and m["authority"]["G2"]["master_sha256"] == G2)
    s2 = _read(os.path.join(_REPO, "real_sfm_qualification", "cpm_session2", "SESSION2_RUNBOOK.md")).decode("utf-8")
    check("pins.manifest_authority_matches_session2", all(v in s2 for v in (
        m["authority"]["G1"]["sidecar_sha256"], m["authority"]["G1"]["manifest_sha256"], m["authority"]["G2"]["sidecar_sha256"])))
    master = _read(os.path.join(_REPO, "sfm_defaultanimationgroups.txt"))
    check("pins.repository_master_is_g1", _sha(master) == G1 and _sha(master + b"\n") == G2)
    probe = _read(PROBE).decode("ascii")
    check("pins.probe_candidate_and_launcher", 'CANDIDATE_APP_SHA256 = "%s"' % CANDIDATE in probe
          and 'LAUNCHER_SHA256 = "%s"' % LAUNCHER_SHA in probe)
    check("pins.reader_candidate", reader.CANDIDATE_APP_SHA256 == CANDIDATE and reader.LAUNCHER_SHA256 == LAUNCHER_SHA
          and reader.G1_MASTER == G1 and reader.G2_MASTER == G2)
    drv = _read(DRIVER).decode("ascii")
    pins = dict(re.findall(r'^\$([A-Z_]+_SHA)\s*= "([0-9a-f]{64})"', drv, re.M))
    check("pins.driver_probe_sha", pins.get("PROBE_SHA") == _sha(_read(PROBE)), pins.get("PROBE_SHA"))
    check("pins.driver_manifest_sha", pins.get("FIXTURE_MANIFEST_SHA") == _sha(_read(MANIFEST)))
    check("pins.driver_candidate_previous", pins.get("CANDIDATE_SHA") == CANDIDATE and pins.get("PREVIOUS_SHA") == PREVIOUS)
    accepted = os.path.join(_REPO, "real_sfm_qualification", "cpm_session4", "raw", "S4A", "deploy_after_removal.txt")
    check("pins.driver_accepted_inventory", pins.get("ACCEPTED_SCRIPTS_SHA") == _sha(_read(accepted))
          == m["deployment"]["accepted_scripts_inventory"]["sha256"])
    # Accepted installed inventory: every pinned dependency and package file is the installed line.
    inv = dict(l.split("\t") for l in _read(accepted).decode("utf-8").split("\n") if l)
    deps_ok = all(inv.get(k) == v for k, v in m["deployment"]["unchanged_menu_dependencies"].items())
    pkg = m["deployment"]["shared_package"]
    side = m["deployment"]["sidecar_reader"]
    pkg_ok = len(pkg["files"]) == 23 and all(inv.get(pkg["menu_relative_dir"] + "/" + n) == s for n, s in pkg["files"].items())
    side_ok = len(side["files"]) == 3 and all(inv.get(side["menu_relative_dir"] + "/" + n) == s for n, s in side["files"].items())
    check("pins.manifest_dependencies_are_accepted_installed", deps_ok and pkg_ok and side_ok)
    check("pins.accepted_inventory_installed_app_is_previous", inv.get("ChadChan3D_CPM/SFM_Character_Preset_Manager.py") == PREVIOUS)
    # Repository sources of the unchanged dependencies (installed bytes may be raw CRLF working-tree bytes).
    def same(path, s):
        raw = _read(path)
        return s in (_sha(raw), _sha(raw.replace(b"\r\n", b"\n")))
    src_ok = (same(os.path.join(_REPO, "cpm", "convergence", "cpm_authority_adapter.py"),
                   m["deployment"]["unchanged_menu_dependencies"]["sfm/mainmenu/ChadChan3D/cpm_authority_adapter.py"])
              and same(os.path.join(_REPO, "cpm", "convergence", "cpm_compat_v1_projection.py"),
                       m["deployment"]["unchanged_menu_dependencies"]["sfm/mainmenu/ChadChan3D/cpm_compat_v1_projection.py"])
              and same(os.path.join(_REPO, "audit_external_runtime", "Rebuild_Control_Groups_Normalizer.py"),
                       m["deployment"]["unchanged_menu_dependencies"]["sfm/mainmenu/ChadChan3D/Rebuild_Control_Groups_Normalizer.py"])
              and all(same(os.path.join(SHARED_PACKAGE_PARENT, "sfm_master_authority_productionized", n), s)
                      for n, s in pkg["files"].items())
              and all(same(os.path.join(_REPO, "tools", "sfm_master_sidecar", n), s) for n, s in side["files"].items()))
    check("pins.manifest_dependencies_match_repository_sources", src_ok)
    # Generation tooling pins (LF-normalized) equal the repository files and appear in the driver.
    gt = m["generation_tooling"]
    tools = dict([("real_sfm_qualification/checkpoint_i_generation_replacement/I_Generation_Publisher.py", gt["publisher_lf_sha256"]),
                  ("real_sfm_qualification/checkpoint_i_generation_replacement/I_Generation_Helper.py", gt["helper_lf_sha256"])]
                 + list(gt["repository_sidecar_tools_lf_sha256"].items()) + list(gt["repository_semantic_core_lf_sha256"].items()))
    tools_ok = all(_sha(_read(os.path.join(_REPO, *k.split("/"))).replace(b"\r\n", b"\n")) == v for k, v in tools.items())
    in_driver = all(('"%s" = "%s"' % (k, v)) in drv for k, v in tools.items())
    check("pins.generation_tools_match_repository_and_driver", tools_ok and in_driver and len(tools) == 14, len(tools))
    try:
        diff = subprocess.check_output(["git", "-C", _REPO, "diff", "--stat", "0597927", "HEAD", "--", "tools/",
                                        "real_sfm_qualification/checkpoint_i_generation_replacement/",
                                        "real_sfm_qualification/cpm_session2/SESSION2_RUNBOOK.md"])
        check("pins.generation_tooling_unchanged_since_session2_freeze", diff.strip() == b"", diff)
    except Exception as exc:  # noqa: BLE001
        check("pins.generation_tooling_unchanged_since_session2_freeze", False, repr(exc))


def static_fixtures():
    m = _manifest()
    harness = _read(os.path.join(_REPO, "real_sfm_qualification", "cpm_session4", "CPM_S4_Rollback_Harness.py")).decode("ascii")
    consts = {}
    for name in ("MIA", "SOURCE", "TARGET1", "TARGET2"):
        node = re.search(r"^    %s = (\{.*?\})\n" % name, harness, re.M | re.S).group(1)
        consts[name] = ast.literal_eval(node.replace("u\"", "\""))
    k, mia = m["fixtures"]["krystal"], m["fixtures"]["mia"]
    check("fixtures.mia_matches_session4_harness", mia["animset"] == {
        "animset_name": consts["MIA"]["animset_name"], "model": consts["MIA"]["model"], "checksum": consts["MIA"]["checksum"]})
    check("fixtures.krystal_matches_session4_harness",
          k["source"] == consts["SOURCE"]
          and k["fit_target"] == {"animset_name": consts["TARGET1"]["name"], "model": consts["TARGET1"]["model"],
                                  "checksum": consts["TARGET1"]["checksum"]}
          and k["unselected_peer"] == {"animset_name": consts["TARGET2"]["name"], "model": consts["TARGET2"]["model"],
                                       "checksum": consts["TARGET2"]["checksum"]})
    probe = _read(PROBE).decode("ascii")
    fx = ast.literal_eval(re.search(r"    FIXTURES = (\(.*?\n    \))\n", probe, re.S).group(1))
    expected = [(k["source"]["animset_name"], k["source"]["model"], k["source"]["checksum"]),
                (k["fit_target"]["animset_name"], k["fit_target"]["model"], k["fit_target"]["checksum"]),
                (k["unselected_peer"]["animset_name"], k["unselected_peer"]["model"], k["unselected_peer"]["checksum"]),
                (mia["animset"]["animset_name"], mia["animset"]["model"], mia["animset"]["checksum"])]
    check("fixtures.probe_fixture_table_equals_manifest", list(fx) == expected, fx)
    s3 = _read(os.path.join(_REPO, "real_sfm_qualification", "cpm_session3", "SESSION3_RUNBOOK.md")).decode("utf-8")
    check("fixtures.session3_runbook_identities", u"`krystal20201` (checksum −1441261258)" in s3
          and u"`assaultsuitbody1` (−791536511)" in s3 and u"`loinclothbra_chadfix_071` (480892851)" in s3)
    arm = json.loads(_read(os.path.join(_REPO, "real_sfm_qualification", "cpm_session4", "raw", "S4A", "s1_arm.json"))
                     .decode("utf-8-sig"))
    lits = arm["scene"]["mia1"]
    cls = mia["g1_classification"]
    check("fixtures.mia_literals_partitioned", sorted(cls["body"] + cls["expression"] + cls["other"]) == sorted(lits)
          and len(cls["body"]) == 46 and len(cls["expression"]) == 58 and len(cls["other"]) == 4)
    check("fixtures.qualifying_controls_mono_and_classified",
          mia["body_control"]["literal"] in cls["body"] and sorted(lits[mia["body_control"]["literal"]]) == ["mono"]
          and mia["expression_control"]["literal"] in cls["expression"]
          and sorted(lits[mia["expression_control"]["literal"]]) == ["mono"])
    pv = m["planned_values"]
    check("fixtures.planned_changes_meaningful",
          abs(pv["C_body"]["update"] - pv["C_body"]["move_away_before_apply"]) >= pv["minimum_meaningful_change"]
          and abs(pv["C_body"]["save"] - pv["C_body"]["update"]) >= pv["minimum_meaningful_change"]
          and abs(pv["C_expression"]["save"] - pv["C_expression"]["move_away_before_apply"]) >= pv["minimum_meaningful_change"]
          and abs(pv["C_body"]["update"] - pv["D_body"]["move_away_before_apply"]) >= pv["minimum_meaningful_change"])
    names = m["campaign_preset_names"]
    check("fixtures.campaign_names_safe", all(re.match(r"^I8 <attempt> [A-Z0-9 ]+$", v) for k2, v in names.items() if k2 != "rule"))


def static_probe():
    raw = _read(PROBE)
    check("probe.ascii_lf", all(b < 128 for b in bytearray(raw)) and b"\r" not in raw)
    tree = ast.parse(raw)
    check("probe.one_function_then_guarded_call_and_delete",
          len(tree.body) == 2 and isinstance(tree.body[0], ast.FunctionDef) and tree.body[0].name == "_cpm_item8_probe_v1"
          and ast.get_docstring(tree) is None and type(tree.body[1]).__name__ in ("Try", "TryFinally"))
    try:
        compile(raw, PROBE, "exec")
        check("probe.compiles", True)
    except SyntaxError as exc:
        check("probe.compiles", False, repr(exc))
    used = _names_used(tree)
    check("probe.no_forbidden_names", not (used & FORBIDDEN_NAMES), sorted(used & FORBIDDEN_NAMES))
    bare = set(n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name))
    dynamic = bare & set(["compile", "exec", "eval", "execfile", "__import__"])
    check("probe.no_dynamic_code", dynamic <= set(["__import__"]), sorted(dynamic))  # __import__: next check
    imports = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "__import__"]
    check("probe.only_import_call_is_sys_exc_clear", len(imports) == 1 and _const(imports[0].args[0]) == "sys")
    ns_calls = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Subscript) and getattr(n.func.value, "id", None) == "ns":
            ns_calls.add(_const(n.func.slice))
    check("probe.cpm_calls_are_only_pure_scene_readers", ns_calls == ALLOWED_NS_CALLS, sorted(ns_calls))
    broker_calls = set(n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                       and getattr(n.func.value, "id", None) == "broker")
    check("probe.broker_calls_are_read_accessors", broker_calls == ALLOWED_BROKER_CALLS, sorted(broker_calls))
    text = raw.decode("ascii")
    code = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))
    check("probe.no_timing_or_notice_modes", not any(t in code.lower() for t in ("timing", "notice", "placeholder", "harness")))
    check("probe.no_removed_event_dependency", not any(t in text for t in ("PROD_PERF", "ASTRA_PERF", "PROD_ACTION_TIMING", "PROD_MODELS")))
    writes = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "open"
              and len(n.args) > 1 and getattr(n.args[1], "s", getattr(n.args[1], "value", None)) in ("wb", "ab")]
    modes = sorted(getattr(n.args[1], "s", getattr(n.args[1], "value", None)) for n in writes)
    check("probe.write_sites_are_write_once_and_append", modes == ["ab", "wb"], modes)
    # The candidate's scene readers the probe reuses are pure (no log, authority, mutation or Undo calls).
    app_tree = ast.parse(_read(APP))
    closure = _call_closure(app_tree, sorted(ALLOWED_NS_CALLS))
    bad = sorted(set(x for names in closure.values() for x in names
                     if any(t in x for t in ("log_line", "authorize", "adapter", "acquire", "stage", "provider", "Start",
                                             "Finish", "Abort", "write", "save", "SetValue", "set_value"))))
    check("probe.reused_cpm_readers_are_pure", len(closure) >= 4 and not bad, bad)


# ===========================================================================
# Evidence reader against the candidate's actual formats
# ===========================================================================
def _format_strings():
    """log_line format strings of the candidate: tag -> [format string]."""
    tree = ast.parse(_read(APP))
    out = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "log_line" and n.args:
            a = n.args[0]
            fmt = a.left if isinstance(a, ast.BinOp) else a
            s = getattr(fmt, "s", getattr(fmt, "value", None))
            if isinstance(s, str if not PY2 else basestring):  # noqa: F821
                tag = re.match(r"[A-Z0-9_]+", s)
                if tag:
                    out.setdefault(tag.group(0), []).append(s)
    return out


SAMPLES = {
    "G18AN_RUN": ("G18AN_RUN run_id=", (u"run-pid42", 42, False)),
    "PROD_R15_MODULE": ("PROD_R15_MODULE name=", ("chadchan3d_cpm_app", "cpm-private-loader-v1", "ready", CANDIDATE, "x/a.py")),
    "PROD_R15_WINDOW_REUSED": ("PROD_R15_WINDOW_REUSED", (u"run-pid42",)),
    "PROD_WINDOW_SHOWN": ("PROD_WINDOW_SHOWN", (0,)),
    "PROD_CLOSE_REQUEST": ("PROD_CLOSE_REQUEST", (None, False, False)),
    "PROD_CLOSE_FINALIZED": ("PROD_CLOSE_FINALIZED", None),
    "PROD_CPM_OPERATION_AUTHORIZED": ("PROD_CPM_OPERATION_AUTHORIZED", (u"Apply Preset", G1, u"body", u"in-scope")),
    "PROD_CPM_OPERATION_AUTHORIZATION_REFUSED": ("PROD_CPM_OPERATION_AUTHORIZATION_REFUSED", (u"Save Preset", u"generation-mismatch")),
    "PROD_CPM_STALE_GENERATION_REBUILD_SCHEDULED": ("PROD_CPM_STALE_GENERATION_REBUILD_SCHEDULED", ({"model": u"m"},)),
    "PROD_CPM_STALE_GENERATION_REBUILD": ("PROD_CPM_STALE_GENERATION_REBUILD identity", ({"model": u"m"},)),
    "PROD_OPERATION_BEGIN": ("PROD_OPERATION_BEGIN id", (3, u"Save Current Body", {"a": 1})),
    "PROD_OPERATION_END": ("PROD_OPERATION_END", (3, u"Save Current Body", u"END", None, None)),
    "PROD_CPM_FIT_STAGE_OPEN": ("PROD_CPM_FIT_STAGE_OPEN", (0, G1, 34)),
    "PROD_CPM_FIT_STAGE_RELEASED": ("PROD_CPM_FIT_STAGE_RELEASED", (0, True)),
    "CLOTHING_FIT_RESULT": ("CLOTHING_FIT_RESULT generation", (2, 1, 0, 0, 1, 1, 0, 0, 0, 0, [u"assaultsuitbody1"])),
    "PROD_MODEL_SWITCH_STAGE": ("PROD_MODEL_SWITCH_STAGE stage='scope-ready'", ({"model": u"m"}, u"healthy", True)),
}


def reader_formats():
    fmts = _format_strings()
    for tag, (prefix, args) in sorted(SAMPLES.items()):
        cands = [f for f in fmts.get(tag, []) if f.startswith(prefix)]
        if len(cands) != 1:
            check("reader.format_present_in_candidate.%s" % tag, False, cands)
            continue
        line = cands[0] if args is None else cands[0] % args
        parsed = reader.parse_log(u"[12:34:56.789012] " + line + u"\n")
        ok = len(parsed["events"]) == 1 and parsed["events"][0]["tag"] == tag and not parsed["historical_or_removed"]
        check("reader.parses_candidate_format.%s" % tag, ok, line)
    # Remaining reader tags exist in the candidate (PROD_PROVIDER_HEALTH, PROD_APPLY, PROD_SAVE, PROD_UPDATE,
    # CLOTHING_FIT_STAGE, PROD_RESOURCE) with the matched prefix.
    extra = {"PROD_PROVIDER_HEALTH": "PROD_PROVIDER_HEALTH status=", "PROD_APPLY": "PROD_APPLY outcome='committed'",
             "PROD_SAVE": "PROD_SAVE=PASS model=", "PROD_UPDATE": "PROD_UPDATE=PASS model=",
             "CLOTHING_FIT_STAGE": "CLOTHING_FIT_STAGE=PASS generation=", "PROD_RESOURCE": "PROD_RESOURCE label="}
    for tag, prefix in sorted(extra.items()):
        check("reader.format_present_in_candidate.%s" % tag, any(f.startswith(prefix) for f in fmts.get(tag, [])))
    samples = [("PROD_SAVE", "PROD_SAVE=PASS model=", (u"models/annoad/foxbase/mia/mia.mdl", u"body", u"I8 X C BODY", 46, 0, 0,
                                                      u"p", True, False)),
               ("PROD_UPDATE", "PROD_UPDATE=PASS model=", (u"m", u"body", u"I8 X C BODY", 46, 0, 0, u"p", True, False)),
               ("PROD_APPLY", "PROD_APPLY outcome='committed'", (u"m", u"body", u"I8 X C BODY", 1, 0, 0)),
               ("PROD_RESOURCE", "PROD_RESOURCE label=", (u"MODEL_RENDER_BEFORE_SCOPE", 1.0, 2.0, 3.0, 4, 5, 6, 7, 8))]
    for tag, prefix, args in samples:
        cand = [f for f in fmts.get(tag, []) if f.startswith(prefix)]
        try:
            line = cand[0] % args
            parsed = reader.parse_log(u"[12:34:56] " + line)
            check("reader.parses_candidate_format.%s" % tag, [e["tag"] for e in parsed["events"]] == [tag], line)
        except Exception as exc:  # noqa: BLE001
            check("reader.parses_candidate_format.%s" % tag, False, repr(exc))
    keys = set(fmts)
    check("reader.current_tags_all_exist_in_candidate", all(t in keys for t, _ in reader.CURRENT_EVENTS),
          [t for t, _ in reader.CURRENT_EVENTS if t not in keys])
    check("reader.no_removed_tag_is_current", not set(t for t, _ in reader.CURRENT_EVENTS) & set(
        ["PROD_PERF", "ASTRA_PERF", "PROD_ACTION_TIMING", "PROD_MODELS", "G18AN_PROVIDER_FORCE_MODE"]))
    check("candidate.no_removed_events", not set(["PROD_PERF", "ASTRA_PERF", "PROD_ACTION_TIMING", "G18AN_PROVIDER_FORCE_MODE"]) & keys)
    fit = fmts.get("CLOTHING_FIT_RESULT", [])
    check("candidate.fit_result_current_format_only", len(fit) == 1 and fit[0].startswith("CLOTHING_FIT_RESULT generation="), fit)
    # Historical Session 4 log: its CLOTHING_FIT_RESULT=PASS line is flagged, never counted as a current Fit result.
    s4 = _read(os.path.join(_REPO, "real_sfm_qualification", "cpm_session4", "raw", "SFM_CSP_G18AN_SaveNewCopy.log")).decode("utf-8", "replace")
    parsed = reader.parse_log(s4)
    flagged = [f["label"] for f in parsed["historical_or_removed"]]
    check("reader.historical_fit_result_not_counted", not reader.events_of(parsed, "CLOTHING_FIT_RESULT")
          and any(l.startswith("CLOTHING_FIT_RESULT=PASS") for l in flagged), flagged[:5])
    check("reader.historical_log_flags_removed_timing", any(l.startswith("PROD_PERF") or l.startswith("ASTRA_PERF")
                                                             for l in flagged), sorted(set(flagged)))


def reader_files():
    root = os.path.join(FIXTURE_ROOT, "reader")
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(os.path.join(root, "scene_snapshots"))
    # Preset readback against the candidate's own saved-value writer.
    tree = ast.parse(_read(APP))
    fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "p02_saved_value_record"][0]
    ns = {}
    exec(compile(ast.Module(body=[fn], **({} if PY2 else {"type_ignores": []})), "app:p02_saved_value_record", "exec"), ns)
    mono = ns["p02_saved_value_record"]({"shape": "MONO"}, {"sides": {"mono": {"evaluated": 0.8}}})
    stereo = ns["p02_saved_value_record"]({"shape": "STEREO"}, {"sides": {"left": {"evaluated": 0.1}, "right": {"evaluated": 0.2}}})
    record = {"values": {u"flex.Fat": mono, u"flex.LipBiteL": stereo}}
    check("reader.preset_value_mono", reader.preset_value(record, u"Fat") == {"mono": 0.8})
    check("reader.preset_value_stereo", reader.preset_value(record, u"LipBiteL") == {"left": 0.1, "right": 0.2})
    try:
        reader.preset_value(record, u"Missing")
        check("reader.preset_value_missing_raises", False)
    except KeyError:
        check("reader.preset_value_missing_raises", True)
    # Library footprint classification (Session 2 S2-B allowed set).
    before = {"Body Presets/A--preset-abcde.json": "1", "character.json": "2", "library.json": "3"}
    after = dict(before, **{"Body Presets/I8 X E G2--preset-0f1a2.json": "9", "character.json": "4", "character.json.bak": "5"})
    rules = [("new-preset", "Body Presets", "I8 X E G2"), ("changed", "character.json"), ("optional", "character.json.bak")]
    check("reader.library_allowed_footprint", reader.classify_library_diff(before, after, rules)["ok"])
    check("reader.library_identical_metadata_allowed", reader.classify_library_diff(
        before, dict(before, **{"Body Presets/I8 X E G2--preset-0f1a2-2.json": "9"}), rules)["ok"])
    bad = dict(after, **{"library.json": "x"})
    check("reader.library_extra_change_rejected", not reader.classify_library_diff(before, bad, rules)["ok"])
    check("reader.library_missing_preset_rejected", not reader.classify_library_diff(before, before, rules)["ok"])
    check("reader.library_removal_rejected", not reader.classify_library_diff(before, dict((k, v) for k, v in after.items()
                                                                                         if k != "library.json"), rules)["ok"])
    check("reader.library_expression_folder", reader.classify_library_diff(
        before, dict(before, **{"Expressions/I8 X C EXPR--preset-12345.json": "1"}),
        [("new-preset", "Expressions", "I8 X C EXPR")])["ok"])
    # Idle checks: zero is idle, non-zero is a problem, an unobserved value is never idle.
    base = {"broker_before": {"observed": True, "runtime_loaded": True, "broker_constructed": True, "outstanding_leases": 0,
                              "unreleased_lease_registry": 0, "provider_counters": {"current_open_provider_count": 0}},
            "window": {"observed": True, "slot_occupied": True, "owned_by_private_module": True, "operation": None,
                       "fit_active": False, "fit_stage_running": False, "modal_deferred_fit_stage_pending": False, "busy": False},
            "acquisition_by_probe": {"determinable": True, "probe_caused_acquisition": False}}
    check("reader.idle_zero", reader.idle_check(base)["idle"])
    nonzero = json.loads(json.dumps(base)); nonzero["broker_before"]["outstanding_leases"] = 1
    check("reader.idle_nonzero_lease", not reader.idle_check(nonzero)["idle"] and reader.idle_check(nonzero)["problems"])
    unobs = json.loads(json.dumps(base)); unobs["broker_before"]["outstanding_leases"] = {"observed": False, "error": "x"}
    r = reader.idle_check(unobs)
    check("reader.idle_unobserved_is_not_idle", not r["idle"] and "outstanding_leases" in r["unobserved"] and not r["problems"], r)
    nobroker = json.loads(json.dumps(base)); nobroker["broker_before"]["broker_constructed"] = False
    check("reader.idle_without_broker_is_unobserved", not reader.idle_check(nobroker)["idle"])
    busy = json.loads(json.dumps(base)); busy["window"]["fit_stage_running"] = True
    check("reader.idle_running_fit_stage_rejected", not reader.idle_check(busy)["idle"])
    acq = json.loads(json.dumps(base)); acq["acquisition_by_probe"] = {"determinable": True, "probe_caused_acquisition": True}
    check("reader.idle_probe_acquisition_rejected", not reader.idle_check(acq)["idle"])
    # Probe records / snapshots / seal integrity.
    snap = {"schema": reader.SNAPSHOT_SCHEMA, "seq": 1, "scene": {"fixture_sets": {"mia1": {"Fat": {"mono": {"evaluated": 0.5}}}}}}
    data = json.dumps(snap).encode("utf-8")
    with open(os.path.join(root, "scene_snapshots", "probe_0001.json"), "wb") as f:
        f.write(data)
    rec = {"schema": reader.PROBE_SCHEMA, "seq": 1, "scene_snapshot": {"observed": True, "file": "scene_snapshots/probe_0001.json",
                                                                     "sha256": _sha(data)}}
    with open(os.path.join(root, "probe.jsonl"), "wb") as f:
        f.write((json.dumps(rec) + "\n").encode("utf-8"))
    loaded = reader.load_snapshot(root, reader.load_probe_records(root)[0])
    check("reader.snapshot_loaded_and_hash_verified", reader.snapshot_value(loaded, "mia1", "Fat") == 0.5)
    snap2 = json.loads(json.dumps(snap)); snap2["scene"]["fixture_sets"]["mia1"]["Fat"]["mono"]["evaluated"] = 0.8
    check("reader.snapshot_diff", reader.snapshot_diff(snap, snap2, "mia1")["changed"] == ["Fat"]
          and reader.snapshot_diff(snap, snap, "mia1")["changed"] == []
          and not reader.snapshot_diff(snap, snap2, "krystal20201")["comparable"])
    with open(os.path.join(root, "scene_snapshots", "probe_0001.json"), "ab") as f:
        f.write(b" ")
    try:
        reader.load_snapshot(root, reader.load_probe_records(root)[0])
        check("reader.snapshot_tamper_detected", False)
    except ValueError:
        check("reader.snapshot_tamper_detected", True)
    with open(os.path.join(root, "probe.jsonl"), "ab") as f:
        f.write((json.dumps(dict(rec, seq=3)) + "\n").encode("utf-8"))
    try:
        reader.load_probe_records(root)
        check("reader.seq_gap_detected", False)
    except ValueError:
        check("reader.seq_gap_detected", True)
    lines = []
    for base_dir, _d, files in os.walk(root):
        for name in files:
            rel = os.path.relpath(os.path.join(base_dir, name), root).replace(os.sep, "/")
            lines.append("%s  %s" % (_sha(_read(os.path.join(base_dir, name))), rel))
    with open(os.path.join(root, "SHA256SUMS.txt"), "wb") as f:
        f.write(("\n".join(sorted(lines)) + "\n").encode("utf-8"))
    check("reader.sums_verify", reader.verify_sha256sums(root)["ok"])
    with open(os.path.join(root, "probe.jsonl"), "ab") as f:
        f.write(b"\n")
    check("reader.sums_tamper_detected", not reader.verify_sha256sums(root)["ok"])


# ===========================================================================
# Fixture classification re-derivation (real G1 Master, candidate prod_scope)
# ===========================================================================
def classification():
    import test_cpm_app_canonical_route as route
    from_name = route.MASTER_NAME
    master_path = os.path.join(CLASSIFY_ROOT, from_name)
    if not PY2:
        if os.path.isdir(CLASSIFY_ROOT):
            shutil.rmtree(CLASSIFY_ROOT)
        os.makedirs(CLASSIFY_ROOT)
        shutil.copyfile(os.path.join(_REPO, "sfm_defaultanimationgroups.txt"), master_path)
        sys.path.insert(0, os.path.join(_REPO, "tools"))
        from sfm_master_sidecar import publisher
        publisher.publish(master_path, CLASSIFY_ROOT)
    if not os.path.isfile(os.path.join(CLASSIFY_ROOT, "manifest.json")):
        check("classification.g1_fixture_published", False, "run this test under Python 3.10 first (publishes the G1 fixture)")
        return
    check("classification.g1_fixture_published", _sha(_read(master_path)) == G1)
    m = _manifest()["fixtures"]["mia"]
    lits = sorted(m["g1_classification"]["body"] + m["g1_classification"]["expression"] + m["g1_classification"]["other"])
    route.Env.live_root = CLASSIFY_ROOT
    route.Env.bindings = [{"literal": l, "shape": l.lower(), "global_key": (u"mia1", i)} for i, l in enumerate(lits)]
    ns = route.build_namespace(route.AppSource(APP))
    ident = {"model": m["animset"]["model"], "checksum": m["animset"]["checksum"], "animset_name": m["animset"]["animset_name"]}
    adapter, health = ns["prod_probe_semantic_provider"](ident)
    scope = ns["prod_scope"](ident, adapter)
    adapter = None
    check("classification.scope_is_g1_healthy", health["status"] == u"healthy" and scope["authority"]["provider_sha256"] == G1)
    check("classification.body_equals_manifest", sorted(scope["body"]) == m["g1_classification"]["body"])
    check("classification.expression_equals_manifest", sorted(scope["expression"]) == m["g1_classification"]["expression"])
    counts = scope["semantic"]["counts"]
    check("classification.no_miss_or_conflict", counts.get("miss") == 0 and counts.get("conflict") == 0, counts)
    b = route._broker()
    check("classification.idle_after", b.outstanding_lease_count() == 0 and b.provider_counters()["current_open_provider_count"] == 0)
    route.Env.bindings = []


# ===========================================================================
# Child: the actual probe in the R15 environment
# ===========================================================================
class StrictBroker(object):
    """Records every method call; only the read accessors are permitted."""

    def __init__(self, fail=None):
        self.calls = []
        self.fail = fail or set()
        self.leases, self.unreleased, self.views = 0, 0, []
        self.counters = {"current_open_provider_count": 0, "peak_open_provider_count": 1, "total_provider_opens": 3,
                         "total_provider_closes": 3, "active_cohort_id": None}
        broker = self

        class Cache(object):
            def all_views(self):
                broker.calls.append("_view_cache.all_views")
                return list(broker.views)
        self._view_cache = Cache()

    def _rec(self, name):
        self.calls.append(name)
        if name in self.fail:
            raise RuntimeError("injected %s failure" % name)

    def outstanding_lease_count(self):
        self._rec("outstanding_lease_count")
        return self.leases

    def unreleased_lease_count(self):
        self._rec("unreleased_lease_count")
        return self.unreleased

    def provider_counters(self):
        self._rec("provider_counters")
        return dict(self.counters)

    def view_cache_entry_count(self):
        self._rec("view_cache_entry_count")
        return len(self.views)

    def recent_diagnostics(self):
        self._rec("recent_diagnostics")
        return [{"event": "cohort_acquired", "detail": {"views": ["cpm_compat_v1"]}}]

    def ledger_snapshot(self):
        self._rec("ledger_snapshot")
        return {"retained_views": 1}

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        self.calls.append("FORBIDDEN:" + name)
        raise AssertionError("probe touched broker.%s" % name)


class View(object):
    consumer_kind = "cpm_compat_v1"
    estimated_bytes = 1234

    class semantic_generation(object):
        master_sha256 = G1

    class coverage(object):
        @staticmethod
        def covered_keys():
            return ("a", "b")

    def live_lease_count(self):
        return 0

    def is_stale(self):
        return False


def fake_runtime(broker):
    rt = types.ModuleType("sfm_master_authority_productionized.runtime")
    rt.RUNTIME_API_VERSION = "1.0.0-b2a"
    rt.RUNTIME_BUILD_ID = "package-boundary-corrected-2026-09-22"
    rt.__file__ = "fake/runtime.py"
    rt._broker = broker
    rt.is_canonical = lambda: True
    rt.get_state = lambda: "READY"
    rt.get_actual_origin_dir = lambda: "fake"
    return rt


class Animset(object):
    """DME stand-in (weak-referenceable, so retention can be detected)."""

    def __init__(self, name):
        self.name = name


class Binding(dict):
    pass


class Scene(object):
    LITERALS = {"mia1": ["Fat", "SmileClosed", "LipBiteL"], "krystal20201": ["SrcA"],
                "assaultsuitbody1": ["FitA", "FitB"], "loinclothbra_chadfix_071": ["LoinA"], "foxmccouldwm1": ["Other"]}

    def __init__(self):
        self.refs = []
        self.undo_count, self.undo_desc = 7, u"Apply Body Preset"
        self.rows_extra = []

    def rows(self):
        m = _manifest()["fixtures"]
        ids = [m["mia"]["animset"], dict(m["krystal"]["source"]), dict(m["krystal"]["fit_target"]),
               dict(m["krystal"]["unselected_peer"]),
               {"animset_name": "foxmccouldwm1", "model": "models/other.mdl", "checksum": 5}] + self.rows_extra
        out = []
        for ident in ids:
            a = Animset(ident["animset_name"])
            self.refs.append(weakref.ref(a))
            out.append({"shot": object(), "animset": a, "gm": object(), "name": ident["animset_name"],
                        "model": ident["model"], "checksum": ident["checksum"]})
        return out

    def bindings(self, animset):
        out = []
        for lit in self.LITERALS.get(animset.name, []):
            b = Binding(literal=lit, shape="STEREO" if lit == "LipBiteL" else "MONO", global_key="%s:%s" % (animset.name, lit),
                        control=Animset("ctrl"))
            b["sides"] = [("left", {"a": animset}), ("right", {"a": animset})] if lit == "LipBiteL" else [("mono", {"a": animset})]
            self.refs.append(weakref.ref(b))
            out.append(b)
        return out

    def side_snapshot(self, control, side):
        return {"source": 0.25, "destination": 0.25, "evaluated": 0.25, "key_count": 0, "key0_time": None,
                "key0_value": None, "is_empty": True, "channel_id": "ch", "log_id": "log", "layer_id": "l",
                "destination_id": "d"}

    def IsUndoEnabled(self):
        return True

    def GetUndoItemCount(self):
        return self.undo_count

    def GetUndoDesc(self):
        return self.undo_desc


class Probe(object):
    def __init__(self, qt_mode, root, app_bytes=None):
        probe_bytes = _read(PROBE)                      # before the Env's path shim
        self.env = r15.Env(qt_mode, root)
        # SFM runs Scripts-menu files in __main__'s own dictionary: make the host dict that dictionary.
        main = types.ModuleType("__main__")
        main.__dict__.update(self.env.host)
        sys.modules["__main__"] = main
        self.env.host = main.__dict__
        if app_bytes is not None:
            self.env.deploy(impl_bytes=app_bytes)
        self.public = os.path.join(self.env.root, "public")
        self.i8root = os.path.join(self.public, "Documents", "CPM_Item8")
        os.makedirs(self.i8root)
        os.environ["PUBLIC"] = self.public
        self.path = os.path.join(self.env.menu_dir, "CPM_Item8_Probe.py")
        with open(self.path, "wb") as f:
            f.write(probe_bytes)
        self.attempt = os.path.join(self.i8root, "I8T1")

    def make_attempt(self, deployed=True):
        os.makedirs(os.path.join(self.attempt, "scene_snapshots"))
        with open(os.path.join(self.attempt, "authority_pins.json"), "wb") as f:
            f.write(b"{}")
        if deployed:
            self.mark_deployed()
        with open(os.path.join(self.i8root, "ACTIVE_ATTEMPT.txt"), "wb") as f:
            f.write(b"I8T1")

    def mark_deployed(self):
        with open(os.path.join(self.attempt, "deployment_after.json"), "wb") as f:
            f.write(b"{}")

    def run(self):
        """One Scripts-menu click on the probe (PyRun_FileExFlags into __main__)."""
        source = _read(self.path)
        code = compile(source, self.path, "exec", 0, True)
        buf = io.StringIO() if not PY2 else r15._Py2Buffer()
        old = sys.stdout
        sys.stdout = buf
        try:
            r15._host_exec(code, self.env.host)
        finally:
            sys.stdout = old
        return buf.getvalue()

    def records(self):
        path = os.path.join(self.attempt, "probe.jsonl")
        if not os.path.isfile(path):
            return []
        return [json.loads(l) for l in _read(path).decode("utf-8").splitlines() if l.strip()]


def _qt_names(env):
    return set(n for n in dir(env.app) if not n.startswith("__"))


def scenario_lifecycle(qt_mode, root):
    p = Probe(qt_mode, root)
    host_before = sorted(p.env.host)
    out = p.run()
    c("refuse.no_pointer_nothing_written", "REFUSED" in out and not os.listdir(p.i8root), out)
    c("refuse.no_pointer_main_unchanged", sorted(p.env.host) == host_before, sorted(set(p.env.host) ^ set(host_before)))
    p.make_attempt(deployed=False)
    out = p.run()
    c("refuse.not_deployed", "REFUSED" in out and "not deployed" in out and not p.records(), out)
    p.mark_deployed()
    # 1) Before CPM launch: no private module, no runtime.
    sys.modules.pop("sfm_master_authority_productionized.runtime", None)
    out = p.run()
    recs = p.records()
    c("before_launch.one_record", len(recs) == 1 and recs[0]["seq"] == 1, out)
    r = recs[0]
    c("before_launch.module_absent", r["module"] == {"observed": True, "present": False})
    c("before_launch.runtime_absent_explicit", r["broker_before"] == {"observed": True, "runtime_loaded": False,
                                                                     "broker_constructed": False}, r["broker_before"])
    c("before_launch.no_acquisition", r["acquisition_by_probe"] == {"determinable": True, "probe_constructed_broker": False,
                                                                    "probe_caused_acquisition": False})
    c("before_launch.window_slot_empty", r["window"] == {"observed": True, "slot_occupied": False})
    c("before_launch.snapshot_not_ready_explicit", r["scene_snapshot"]["observed"] is True and not json.loads(
        _read(os.path.join(p.attempt, "scene_snapshots", "probe_0001.json")).decode("utf-8"))["scene"]["observed"])
    c("before_launch.identity_candidate_and_launcher", r["identity"]["impl_is_candidate"] is True
      and r["identity"]["launcher_is_pinned"] is True and r["identity"]["installed_probe_sha256"] == _sha(_read(PROBE)))
    c("before_launch.host_isolation", r["host"]["probe_globals_is_main_dict"] is True and r["host"]["cpm_names_in_main"] == [])
    c("before_launch.main_dict_unchanged", sorted(p.env.host) == host_before, sorted(set(p.env.host) ^ set(host_before)))
    c("before_launch.resources_explicit", r["resources"].get("observed") is True and isinstance(r["resources"].get("handles"), int)
      or (r["resources"].get("observed") is False and "resources" in r["errors"]), r["resources"])
    # 2) CPM launched; strict broker; stubbed scene leaf; candidate's own binding_snapshot.
    broker = StrictBroker()
    broker.views = [View()]
    sys.modules["sfm_master_authority_productionized.runtime"] = fake_runtime(broker)
    p.env.click()
    p.env.settle()
    ns = p.env.module().__dict__
    window = p.env.slot()
    scene = Scene()
    ns["p03_model_animsets"] = scene.rows
    ns["p01_all_supported_flex_bindings"] = scene.bindings
    ns["side_snapshot"] = scene.side_snapshot
    ns["dm"] = lambda: scene
    ns_before = dict(ns)
    win_before = sorted(window.__dict__)
    qt_before = _qt_names(p.env)
    tops_before = len(p.env.app.topLevelWidgets())
    mods_before = set(sys.modules)
    host_before = sorted(p.env.host)
    trapped = []
    QtCore, QtGui = p.env.QtCore, p.env.QtGui
    saved = dict((n, getattr(mod, n)) for mod, n in ((QtCore, "QTimer"), (QtGui, "QMessageBox"), (QtGui, "QDialog")))

    def trap(name):
        def f(*a, **k):
            trapped.append(name)
            raise AssertionError("probe constructed %s" % name)
        return f
    QtCore.QTimer = trap("QTimer")
    QtGui.QMessageBox = trap("QMessageBox")
    QtGui.QDialog = trap("QDialog")
    try:
        out = p.run()
    finally:
        QtCore.QTimer, QtGui.QMessageBox, QtGui.QDialog = saved["QTimer"], saved["QMessageBox"], saved["QDialog"]
    recs = p.records()
    r = recs[-1]
    c("launched.second_record", len(recs) == 2 and r["seq"] == 2, out)
    m = r["module"]
    c("launched.module_identity", m["present"] and m["build_is_candidate"] and m["file_is_impl_path"]
      and m["loader_is_private_loader"] and m["state"] == "ready" and m["module_dict_is_main_dict"] is False
      and m["other_modules_defining_cpm"] == [] and m["id"] == "0x%x" % id(p.env.module()), m)
    w = r["window"]
    c("launched.window_owned_and_private", w["owned_by_private_module"] and w["function_globals_is_private_module"] is True
      and w["function_globals_is_main_dict"] is False and w["alive"] is True and w["id"] == "0x%x" % id(window), w)
    c("launched.window_idle_state", w["operation"] is None and w["fit_active"] is False and w["fit_stage_running"] is False
      and w["modal_deferred_fit_stage_pending"] is False and w["scope"] == {"present": False}, w)
    c("launched.census", r["census"]["observed"] and r["census"]["prodwindow_toplevel_total"] == 1
      and r["census"]["prodwindow_toplevel_owned"] == 1, r["census"])
    c("launched.historical_inactive", m["historical"]["semantic_provider_is_none"] is True and all(
        m["historical"][k] == 0 for k in reader.HISTORICAL_COUNTERS), m["historical"])
    c("launched.broker_only_read_accessors", set(broker.calls) <= ALLOWED_BROKER_CALLS | set(["_view_cache.all_views"])
      and not [x for x in broker.calls if x.startswith("FORBIDDEN")], broker.calls)
    c("launched.broker_before_after_observed", r["broker_before"]["outstanding_leases"] == 0
      and r["broker_after"]["provider_counters"]["total_provider_opens"] == 3 and r["broker_before"]["broker_id"] == "0x%x" % id(broker))
    c("launched.no_probe_acquisition", r["acquisition_by_probe"] == {"determinable": True, "probe_caused_acquisition": False,
                                                                     "changed": []}, r["acquisition_by_probe"])
    c("launched.broker_detail", r["broker_detail"]["views"][0]["master_sha256"] == G1
      and r["broker_detail"]["consumers_served"] == ["cpm_compat_v1"] and r["broker_detail"]["ledger"] == {"retained_views": 1})
    c("launched.no_timer_dialog_constructed", trapped == [], trapped)
    c("launched.module_namespace_unchanged", sorted(ns) == sorted(ns_before) and all(ns[k] is ns_before[k] for k in ns_before))
    c("launched.window_attributes_unchanged", sorted(window.__dict__) == win_before)
    c("launched.qapplication_attributes_unchanged", _qt_names(p.env) == qt_before)
    c("launched.no_new_toplevel_widgets", len(p.env.app.topLevelWidgets()) == tops_before)
    c("launched.main_dict_unchanged", sorted(p.env.host) == host_before, sorted(set(p.env.host) ^ set(host_before)))
    added = sorted(k for k in set(sys.modules) - mods_before if re.search(r"(?i)cpm|sfm|authority|chadchan", k))
    c("launched.no_cpm_or_authority_modules_imported", added == [], added)
    snap_meta = r["scene_snapshot"]
    snap = json.loads(_read(os.path.join(p.attempt, *snap_meta["file"].split("/"))).decode("utf-8"))
    c("snapshot.hash_matches_record", _sha(_read(os.path.join(p.attempt, *snap_meta["file"].split("/")))) == snap_meta["sha256"])
    sets = snap["scene"]["fixture_sets"]
    c("snapshot.only_explicit_fixture_sets", sorted(sets) == ["assaultsuitbody1", "krystal20201", "loinclothbra_chadfix_071", "mia1"],
      sorted(sets))
    c("snapshot.values_from_candidate_binding_snapshot", sets["mia1"]["Fat"] == {"mono": {
        "source": 0.25, "destination": 0.25, "evaluated": 0.25, "key_count": 0, "key0_time": None, "key0_value": None,
        "is_empty": True}} and sorted(sets["mia1"]["LipBiteL"]) == ["left", "right"], sets.get("mia1"))
    c("snapshot.undo_facts", snap["scene"]["undo"] == {"enabled": True, "count": 7, "desc": u"Apply Body Preset"})
    gc.collect()
    alive = [ref for ref in scene.refs if ref() is not None]
    c("snapshot.no_dme_objects_retained", scene.refs and not alive, len(alive))
    # 3) Identity mismatch of a fixture name is reported, not snapshotted.
    scene.rows_extra = [{"animset_name": "mia1", "model": "models/annoad/foxbase/mia/mia.mdl", "checksum": 999}]
    p.run()
    r = p.records()[-1]
    snap = json.loads(_read(os.path.join(p.attempt, *r["scene_snapshot"]["file"].split("/"))).decode("utf-8"))
    c("snapshot.identity_mismatch_reported", [x["identity_matches"] for x in snap["scene"]["fixtures_present"]["mia1"]] == [True, False]
      and snap["scene"]["duplicate_fixture_names"] == ["mia1"])
    scene.rows_extra = []
    # 4) Window state is reported, never acted on.
    window.operation = {"operation_id": 9, "kind": u"Clothing Fit", "phase": u"STAGE", "native_commit": None,
                        "durable_commit": None, "closing_requested": False, "context": object()}
    window.fit_active = True
    window.fit_stage_running = True
    p.run()
    r = p.records()[-1]
    c("busy.reported", r["window"]["operation"]["kind"] == u"Clothing Fit" and r["window"]["fit_stage_running"] is True)
    c("busy.reader_not_idle", not reader.idle_check(r)["idle"])
    c("busy.probe_did_not_change_state", window.operation["operation_id"] == 9 and window.fit_stage_running is True)
    window.operation, window.fit_active, window.fit_stage_running = None, False, False
    # 5) Observation failures are explicit, never zero.
    broker.fail = set(["outstanding_lease_count"])
    p.run()
    r = p.records()[-1]
    c("errors.broker_read_failure_explicit", r["broker_before"]["outstanding_leases"].get("observed") is False
      and "broker.outstanding_leases" in r["errors"], r["broker_before"])
    c("errors.acquisition_not_determinable", r["acquisition_by_probe"]["determinable"] is False)
    c("errors.reader_reports_unobserved", not reader.idle_check(r)["idle"] and "outstanding_leases" in reader.idle_check(r)["unobserved"])
    broker.fail = set()
    real_rows = ns["p03_model_animsets"]
    ns["p03_model_animsets"] = lambda: (_ for _ in ()).throw(RuntimeError("scene unavailable"))
    p.run()
    r = p.records()[-1]
    c("errors.scene_failure_explicit", r["scene_snapshot"]["observed"] is True and "scene" in r["errors"], r["errors"])
    ns["p03_model_animsets"] = real_rows
    import ctypes
    real_windll = ctypes.WinDLL
    ctypes.WinDLL = lambda *a, **k: (_ for _ in ()).throw(OSError("injected"))
    try:
        p.run()
    finally:
        ctypes.WinDLL = real_windll
    r = p.records()[-1]
    c("errors.resources_failure_explicit", r["resources"] == {"observed": False, "error": "injected"} and "resources" in r["errors"],
      r["resources"])
    sys.modules["sfm_master_authority_productionized.runtime"]._broker = None
    p.run()
    r = p.records()[-1]
    c("errors.no_broker_explicit", r["broker_before"]["broker_constructed"] is False and not reader.idle_check(r)["idle"])
    sys.modules["sfm_master_authority_productionized.runtime"]._broker = broker
    # 6) Write-once and append-only.
    jsonl = os.path.join(p.attempt, "probe.jsonl")
    prefix = _read(jsonl)
    nxt = len(p.records()) + 1
    taken = os.path.join(p.attempt, "scene_snapshots", "probe_%04d.json" % nxt)
    with open(taken, "wb") as f:
        f.write(b"OCCUPIED")
    p.run()
    r = p.records()[-1]
    c("write_once.existing_snapshot_not_overwritten", _read(taken) == b"OCCUPIED" and r["seq"] == nxt
      and r["scene_snapshot"]["observed"] is False and "scene_snapshot" in r["errors"])
    c("write_once.append_only", _read(jsonl).startswith(prefix))
    seqs = [x["seq"] for x in p.records()]
    c("write_once.seq_contiguous", seqs == list(range(1, len(seqs) + 1)), seqs)
    good = _read(jsonl)
    with open(jsonl, "ab") as f:
        f.write(b'{"partial":')
    size = os.path.getsize(jsonl)
    out = p.run()
    c("write_once.truncated_log_refused", "REFUSED" in out and os.path.getsize(jsonl) == size, out)
    with open(jsonl, "wb") as f:
        f.write(good)
    with open(os.path.join(p.attempt, "SHA256SUMS.txt"), "wb") as f:
        f.write(b"")
    before = _read(jsonl)
    out = p.run()
    c("write_once.sealed_attempt_refused", "REFUSED" in out and "sealed" in out and _read(jsonl) == before, out)
    c("reader.loads_probe_records", len(reader.load_probe_records(p.attempt)) == len(p.records()) == seqs[-1])


def scenario_pin_mismatch(qt_mode, root):
    """A different build installed: the probe reports it; the reader's identity check fails."""
    item6 = subprocess.check_output(["git", "-C", _REPO, "show", "7b69b52:cpm/app/SFM_Character_Preset_Manager.py"])
    c("pin.item6_bytes", _sha(item6) == ITEM6_APP)
    p = Probe(qt_mode, root, app_bytes=item6)
    p.make_attempt()
    sys.modules["sfm_master_authority_productionized.runtime"] = fake_runtime(StrictBroker())
    p.env.click()
    p.env.settle()
    p.run()
    r = p.records()[-1]
    c("pin.impl_not_candidate_reported", r["identity"]["impl_is_candidate"] is False
      and r["identity"]["installed_impl_sha256"] == ITEM6_APP)
    c("pin.module_build_not_candidate", r["module"]["build_is_candidate"] is False and r["module"]["build_sha256"] == ITEM6_APP)
    ic = reader.identity_check(r)
    c("pin.reader_identity_fails", not ic["ok"] and ic["checks"]["installed_impl_is_candidate"] is False
      and ic["checks"]["module_build_is_candidate"] is False, ic)


def scenario_real_broker(qt_mode, root):
    """The REAL shared-package broker: the probe's reads cause no acquisition."""
    p = Probe(qt_mode, root)
    p.make_attempt()
    sys.path.insert(0, SHARED_PACKAGE_PARENT)
    sys.path.insert(0, os.path.join(_REPO, "tools"))          # sfm_master_sidecar (installed as a sibling in SFM)
    for key in list(sys.modules):
        if key.startswith("sfm_master_authority_productionized"):
            del sys.modules[key]
    from sfm_master_authority_productionized import runtime
    broker = runtime.get_broker()
    c("realbroker.constructed_by_test", runtime._broker is broker)
    before = (broker.outstanding_lease_count(), broker.unreleased_lease_count(), dict(broker.provider_counters()),
              broker.view_cache_entry_count(), len(broker.recent_diagnostics()), json.dumps(broker.ledger_snapshot(), sort_keys=True,
                                                                                           default=str))
    p.env.click()
    p.env.settle()
    p.run()
    r = p.records()[-1]
    after = (broker.outstanding_lease_count(), broker.unreleased_lease_count(), dict(broker.provider_counters()),
             broker.view_cache_entry_count(), len(broker.recent_diagnostics()), json.dumps(broker.ledger_snapshot(), sort_keys=True,
                                                                                          default=str))
    c("realbroker.state_unchanged_by_probe", before == after, [before, after])
    c("realbroker.record_observed", r["broker_before"]["broker_constructed"] is True and r["broker_before"]["is_canonical"] is True
      and r["broker_before"]["outstanding_leases"] == 0 and r["broker_before"]["provider_counters"]["current_open_provider_count"] == 0,
      r["broker_before"])
    c("realbroker.no_probe_acquisition", r["acquisition_by_probe"] == {"determinable": True, "probe_caused_acquisition": False,
                                                                       "changed": []}, r["acquisition_by_probe"])
    c("realbroker.reader_idle", reader.idle_check(r)["idle"], reader.idle_check(r))
    c("realbroker.runtime_origin_recorded", r["broker_before"]["actual_origin_dir"].replace("\\", "/").endswith(
        "candidate_b2c_correction6/sfm_master_authority_productionized"), r["broker_before"].get("actual_origin_dir"))


SCENARIOS = [("lifecycle", scenario_lifecycle), ("pin_mismatch", scenario_pin_mismatch), ("real_broker", scenario_real_broker)]


def child_main(scenario, qt_mode, root):
    try:
        dict(SCENARIOS)[scenario](qt_mode, root)
    except BaseException:
        import traceback
        c("scenario_completed", False, traceback.format_exc()[-1500:])
    else:
        c("scenario_completed", True)
    sys.stdout.write("R15_CHILD_RESULT " + json.dumps(r15.CHILD_RESULTS) + "\n")
    sys.stdout.flush()


def run_child(name, mode):
    root = os.path.join(FIXTURE_ROOT, "%s_%s" % (mode, name))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--child=%s" % name, "--qt=%s" % mode,
                             "--root=%s" % root], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    output = proc.communicate()[0].decode("utf-8", "replace")
    for line in output.splitlines():
        if line.startswith("R15_CHILD_RESULT "):
            return json.loads(line[len("R15_CHILD_RESULT "):]), output
    return None, output


def main():
    args = dict(a.split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    if "--child" in args:
        child_main(args["--child"], args["--qt"], args["--root"])
        return
    print("Interpreter: %s" % sys.version.split()[0])
    if os.path.isdir(FIXTURE_ROOT):
        shutil.rmtree(FIXTURE_ROOT)
    os.makedirs(FIXTURE_ROOT)
    static_pins()
    static_fixtures()
    static_probe()
    reader_formats()
    reader_files()
    classification()
    modes = (["real"] if r15.qt_available() else []) + ["model"]
    print("Qt modes: %s" % ", ".join(modes))
    for mode in modes:
        for name, _ in SCENARIOS:
            records, output = run_child(name, mode)
            if records is None:
                check("%s.%s.child_reported" % (mode, name), False, output[-2000:])
                continue
            for cname, ok, value in records:
                check("%s.%s.%s" % (mode, name, cname), ok, value)
    passed = sum(1 for r in RESULTS if r[1])
    print("\nRESULT: %d/%d %s" % (passed, len(RESULTS), "ALL PASS" if passed == len(RESULTS) else "SOME FAILED"))
    if passed != len(RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
