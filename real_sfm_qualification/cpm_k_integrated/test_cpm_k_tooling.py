# -*- coding: utf-8 -*-
"""K-0 offline qualification of the K tooling (qualification-only).

  CPM_K_Probe.py, k_evidence_reader.py, K_DRIVER.ps1, K_FIXTURE_MANIFEST.json and the operator template
  (design: cpm/qualification/K_INTEGRATED_PRODUCT_WORKFLOW_QUALIFICATION_DESIGN.md, section 6).

Every K tool is derived from its already-qualified item-8 counterpart
(real_sfm_qualification/cpm_item8_post_cleanup/), and this test proves the derivation:
  - pins: K candidate app, driver pins equal the actual probe/manifest bytes, copied manifest
    sections equal the item-8 manifest and the repository sources, the expected K Scripts
    inventory is the accepted Session 4 inventory with exactly the app line changed;
  - probe: byte reconstruction from the pinned item-8 probe plus the declared delta list; the
    item-8 static purity rules re-run on the K probe; runtime (real PySide/Qt 4.8 + the Qt model)
    with a Normalizer-first REAL broker, a strict broker with both consumer kinds, refusals,
    write-once/append-only, and a different installed build;
  - reader: the production Normalizer's own log format strings and a real (redacted) Normalizer
    log, per-consumer views, idle and boundary rules, design section 5.4 resource rules;
  - driver (Python 3 only): the frozen Session 2 block byte-for-byte; sandbox end to end with the
    real generation tooling (exact G1 -> G2 -> G1), probe-only deployment, the installed app never
    changed, and every read-only STOP writing nothing;
  - design: every K-* function the runbook names exists in the driver; D1-D4 recorded.

Usage: python test_cpm_k_tooling.py --phase=run     (Python 2.7.5 SFM interpreter and Python 3.10)
       internal: --child=<scenario> --qt=<real|model> --root=<dir>
"""
from __future__ import print_function

import ast
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types

_THIS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_THIS, os.pardir, os.pardir))
_ITEM8 = os.path.join(_REPO, "real_sfm_qualification", "cpm_item8_post_cleanup")
sys.path.insert(0, os.path.join(_REPO, "cpm", "convergence", "tests"))
sys.path.insert(0, _ITEM8)
sys.path.insert(0, _THIS)
import test_cpm_app_r15_namespace_isolation as r15  # noqa: E402
import test_cpm_item8_probe as t8  # noqa: E402  (qualified helpers: purity rules, strict broker, scene stubs)
import item8_evidence_reader as base  # noqa: E402
import k_evidence_reader as reader  # noqa: E402

PROBE = os.path.join(_THIS, "CPM_K_Probe.py")
DRIVER = os.path.join(_THIS, "K_DRIVER.ps1")
MANIFEST = os.path.join(_THIS, "K_FIXTURE_MANIFEST.json")
TEMPLATE = os.path.join(_THIS, "templates", "K_OPERATOR_STEPS_TEMPLATE.md")
ITEM8_PROBE = os.path.join(_ITEM8, "CPM_Item8_Probe.py")
ITEM8_DRIVER = os.path.join(_ITEM8, "ITEM8_GENERATION_DRIVER.ps1")
ITEM8_MANIFEST = os.path.join(_ITEM8, "ITEM8_FIXTURE_MANIFEST.json")
DESIGN = os.path.join(_REPO, "cpm", "qualification", "K_INTEGRATED_PRODUCT_WORKFLOW_QUALIFICATION_DESIGN.md")
APP = os.path.join(_REPO, "cpm", "app", "SFM_Character_Preset_Manager.py")
NORMALIZER = os.path.join(_REPO, "audit_external_runtime", "Rebuild_Control_Groups_Normalizer.py")
NORMALIZER_LOG_SAMPLE = os.path.join(_ITEM8, "raw", "I8A1", "logs", "D_after_normalizer__sfm_rebuild_control_groups.txt")
S4_INVENTORY = os.path.join(_REPO, "real_sfm_qualification", "cpm_session4", "raw", "S4A", "deploy_after_removal.txt")
SHARED_PACKAGE_PARENT = os.path.join(_REPO, "tests", "sidecar", "qualification", "candidate_b2c_correction6")
FIXTURE_ROOT = os.path.join(tempfile.gettempdir(), "cpm_k_probe_fixture")
SANDBOX = os.path.join(tempfile.gettempdir(), "cpm_k_driver_sandbox")

CANDIDATE = "4e35f29242351317f2f961c27e19d66fcd3355cff964b081431fc2fff1f5b9d7"
S4_APP = "9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900"
ITEM8_APP = "bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5"
ITEM8_PROBE_SHA = "f503c0abaf63f891c108fd81c726b1101288a2dcf1091bf6a386388be1571257"
ITEM8_MANIFEST_SHA = "40b51416fb8e742b2512dd973ade07ccd0e618a58ebd6c96e9dd62efc1afeb2b"
EXPECTED_INVENTORY_SHA = "59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086"
S4_INVENTORY_SHA = "cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922"
G1 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
G2 = "54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7"
G1_SIDECAR = "bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b"
PY2 = sys.version_info[0] == 2
RESULTS = []

# ---------------------------------------------------------------------------
# The declared item-8 -> K probe delta list (old, new, count). Nothing else may differ.
# ---------------------------------------------------------------------------
PROBE_DELTAS = [
    ("""# -*- coding: ascii -*-
# CPM handoff section 22 item 8 -- post-cleanup real-SFM qualification probe.
#
# QUALIFICATION-ONLY. Not product code. Deployed temporarily to the ChadChan3D
# Scripts menu for one item-8 attempt and removed at closeout (ITEM8_RUNBOOK.md).
# A new item-8 revision, not a repinned historical probe: it has no timing
# block, no notice/placeholder harness and no other mode.
#""", """# -*- coding: ascii -*-
# K -- integrated CPM/Normalizer product workflow qualification probe.
#
# QUALIFICATION-ONLY. Not product code. Deployed temporarily to the ChadChan3D
# Scripts menu for one K attempt and removed at closeout
# (cpm/qualification/K_INTEGRATED_PRODUCT_WORKFLOW_QUALIFICATION_DESIGN.md).
# Derived from the item-8 probe by a declared delta list (test_cpm_k_tooling.py):
# K pins and attempt root, a read-only broker-diagnostics tail, a free-VAS
# sample and a census of the Normalizer's shared-__main__ names. No other mode.
#""", 1),
    ("#   - writes only campaign evidence, under the attempt named by\n"
     "#     %PUBLIC%\\Documents\\CPM_Item8\\ACTIVE_ATTEMPT.txt;",
     "#   - writes only campaign evidence, under the attempt named by\n"
     "#     %PUBLIC%\\Documents\\CPM_K\\ACTIVE_ATTEMPT.txt;", 1),
    ("_cpm_item8_probe_v1", "_cpm_k_probe_v1", 3),
    ('PROBE_VERSION = "cpm-item8-probe-1"', 'PROBE_VERSION = "cpm-k-probe-1"', 1),
    ('SCHEMA = "cpm-item8-probe-record-v1"', 'SCHEMA = "cpm-k-probe-record-v1"', 1),
    ('SNAPSHOT_SCHEMA = "cpm-item8-scene-snapshot-v1"', 'SNAPSHOT_SCHEMA = "cpm-k-scene-snapshot-v1"', 1),
    ('CANDIDATE_APP_SHA256 = "%s"' % ITEM8_APP, 'CANDIDATE_APP_SHA256 = "%s"' % CANDIDATE, 1),
    ("    # Explicit fixture animation sets (ITEM8_FIXTURE_MANIFEST.json); nothing else is snapshotted.",
     "    # Explicit fixture animation sets (K_FIXTURE_MANIFEST.json); nothing else is snapshotted.", 1),
    ('''                      "PROD_RUN_ID", "PROD_OUTPUT_PATH", "_chadchan3d_cpm_launcher_v1")
''', '''                      "PROD_RUN_ID", "PROD_OUTPUT_PATH", "_chadchan3d_cpm_launcher_v1")
    # The production Normalizer runs in SFM's shared __main__ (carried K/L note): recorded, never touched.
    NORMALIZER_MAIN_SENTINELS = ("StartRebuildControlGroups", "RebuildControlGroupsProductionRun", "RebuildScopeDialog",
                                 "OUTPUT_PATH", "PRODUCTION_REVISION", "SCOPE_SELECTED", "SCOPE_ALL")
    DIAGNOSTICS_TAIL = 16
''', 1),
    ('root = os.path.join(public, "Documents", "CPM_Item8")', 'root = os.path.join(public, "Documents", "CPM_K")', 1),
    ('"no active item-8 attempt (%s missing)"', '"no active K attempt (%s missing)"', 1),
    ('''        try:
            out["ledger"] = json.loads(json.dumps(broker.ledger_snapshot(), default=text))
''', '''        try:
            tail = []
            for entry in broker.recent_diagnostics()[-DIAGNOSTICS_TAIL:]:
                detail = entry.get("detail") if isinstance(entry, dict) else None
                summary = {}
                if isinstance(detail, dict):
                    for key, value in detail.items():
                        if isinstance(value, (list, tuple)):
                            summary[text(key)] = sorted(text(v) for v in value) if len(value) <= 8 else len(value)
                        elif isinstance(value, dict):
                            summary[text(key)] = {"keys": len(value)}
                        else:
                            summary[text(key)] = plain(value)
                tail.append({"event": text(entry.get("event")) if isinstance(entry, dict) else text(entry),
                             "t": plain(entry.get("t")) if isinstance(entry, dict) else None, "detail": summary})
            out["diagnostics_tail"] = tail
        except Exception as exc:
            out["diagnostics_tail"] = fail("broker.diagnostics_tail", exc)
        try:
            out["ledger"] = json.loads(json.dumps(broker.ledger_snapshot(), default=text))
''', 1),
    ('''                    ("PrivateUsage", ctypes.c_size_t),
                ]
''', '''                    ("PrivateUsage", ctypes.c_size_t),
                ]

            class MEMSTAT(ctypes.Structure):
                _fields_ = [
                    ("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
''', 1),
    ('''            user32.GetGuiResources.restype = wintypes.DWORD
''', '''            user32.GetGuiResources.restype = wintypes.DWORD
            kernel32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MEMSTAT)]
            kernel32.GlobalMemoryStatusEx.restype = wintypes.BOOL
''', 1),
    ('''            out["gdi_objects"] = int(user32.GetGuiResources(handle, 0))
''', '''            status = MEMSTAT()
            status.dwLength = ctypes.sizeof(MEMSTAT)
            if kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                out["total_virtual"] = int(status.ullTotalVirtual)
                out["avail_virtual"] = int(status.ullAvailVirtual)
            else:
                out["vas_error"] = "GlobalMemoryStatusEx failed"
                errors["resources.vas"] = out["vas_error"]
            out["gdi_objects"] = int(user32.GetGuiResources(handle, 0))
''', 1),
    ('''                      "main_dict_size": len(main_dict)}
''', '''                      "normalizer_names_in_main": sorted(n for n in NORMALIZER_MAIN_SENTINELS if n in main_dict),
                      "main_dict_size": len(main_dict)}
''', 1),
    ('("installed_probe_sha256", os.path.join(menu, "CPM_Item8_Probe.py"))',
     '("installed_probe_sha256", os.path.join(menu, "CPM_K_Probe.py"))', 1),
    ("CPM_ITEM8_PROBE", "CPM_K_PROBE", 3),
]
NORMALIZER_SENTINELS = ["OUTPUT_PATH", "PRODUCTION_REVISION", "RebuildControlGroupsProductionRun", "RebuildScopeDialog",
                        "SCOPE_ALL", "SCOPE_SELECTED", "StartRebuildControlGroups"]


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


def _manifest():
    return json.loads(_read(MANIFEST).decode("ascii"))


def _driver_pin(name):
    m = re.search(r'^\$%s\s*=\s*"([0-9a-f]{64})"' % re.escape(name), _read(DRIVER).decode("ascii"), re.M)
    return m.group(1) if m else None


# ===========================================================================
# Static: pins and manifest
# ===========================================================================
def static_pins():
    m, m8 = _manifest(), json.loads(_read(ITEM8_MANIFEST).decode("ascii"))
    check("pins.repository_app_is_k_candidate", _sha(_read(APP)) == CANDIDATE == m["apps"]["k_candidate_sha256"])
    check("pins.item8_tooling_unchanged", _sha(_read(ITEM8_PROBE)) == ITEM8_PROBE_SHA and _sha(_read(ITEM8_MANIFEST)) == ITEM8_MANIFEST_SHA)
    check("pins.driver_probe_pin_is_probe_file", _driver_pin("PROBE_SHA") == _sha(_read(PROBE)), _driver_pin("PROBE_SHA"))
    check("pins.driver_manifest_pin_is_manifest_file", _driver_pin("FIXTURE_MANIFEST_SHA") == _sha(_read(MANIFEST)))
    check("pins.driver_candidate_and_inventory", _driver_pin("CANDIDATE_SHA") == CANDIDATE and _driver_pin("S4_APP_SHA") == S4_APP
          and _driver_pin("EXPECTED_SCRIPTS_SHA") == EXPECTED_INVENTORY_SHA and _driver_pin("ACCEPTED_SCRIPTS_SHA") == S4_INVENTORY_SHA
          and _driver_pin("FIXTURE_DOCUMENT_SHA") == m["fixture_document"]["sha256"])
    check("pins.reader_candidate", reader.CANDIDATE_APP_SHA256 == CANDIDATE and reader.G1_MASTER == G1 and reader.G2_MASTER == G2
          and reader.NORMALIZER_SHA256 == m["normalizer"]["installed_sha256"])
    # Copied manifest sections equal the qualified item-8 manifest.
    for key in ("authority", "generation_tooling"):
        check("manifest.copied.%s" % key, m[key] == m8[key])
    d, d8 = m["deployment"], m8["deployment"]
    for key in ("unchanged_menu_dependencies", "shared_package", "sidecar_reader", "accepted_scripts_inventory",
                "historical_menu_content_requiring_owner_disposition", "scripts_root"):
        check("manifest.copied.deployment.%s" % key, d[key] == d8[key])
    check("manifest.copied.fixture_identity", all(m["fixture_document"][k] == m8["fixture_document"][k]
                                                  for k in ("sha256", "bytes", "film_clips", "file_name", "encoding"))
          and m["fixtures"]["krystal"] == m8["fixtures"]["krystal"]
          and m["fixtures"]["mia"]["animset"] == m8["fixtures"]["mia"]["animset"])
    check("manifest.absent_list_superset", set(d8["expected_absent_before_deploy"]) <= set(d["expected_absent_before_deploy"])
          and "sfm/mainmenu/ChadChan3D/CPM_K_Probe.py" in d["expected_absent_before_deploy"])
    # Manifest dependencies equal the repository sources (byte forms as installed).
    srcs = {"sfm/mainmenu/ChadChan3D/SFM_Character_Preset_Manager.py": os.path.join(_REPO, "cpm", "app", "launcher", "SFM_Character_Preset_Manager.py"),
            "sfm/mainmenu/ChadChan3D/cpm_authority_adapter.py": os.path.join(_REPO, "cpm", "convergence", "cpm_authority_adapter.py"),
            "sfm/mainmenu/ChadChan3D/cpm_compat_v1_projection.py": os.path.join(_REPO, "cpm", "convergence", "cpm_compat_v1_projection.py"),
            "sfm/mainmenu/ChadChan3D/Rebuild_Control_Groups_Normalizer.py": NORMALIZER}
    bad = [rel for rel, pin in d["unchanged_menu_dependencies"].items() if not _byte_form_matches(srcs[rel], pin)]
    check("manifest.dependencies_equal_repository_sources", not bad, bad)
    # Expected K inventory: the accepted Session 4 inventory with exactly the app line changed.
    s4 = _read(S4_INVENTORY)
    old = ("ChadChan3D_CPM/SFM_Character_Preset_Manager.py\t%s" % S4_APP).encode("ascii")
    new = ("ChadChan3D_CPM/SFM_Character_Preset_Manager.py\t%s" % CANDIDATE).encode("ascii")
    check("inventory.s4_pinned_and_one_app_line", _sha(s4) == S4_INVENTORY_SHA and s4.count(old) == 1)
    check("inventory.expected_is_s4_plus_app_line", _sha(s4.replace(old, new)) == EXPECTED_INVENTORY_SHA
          == d["expected_scripts_inventory"]["expected_sha256"])
    # Scope plan, budget, decisions.
    runs = m["normalizer"]["runs"]
    check("plan.normalizer_budget", all(len(v) <= m["normalizer"]["budget_per_process"] == 4 for v in runs.values())
          and sorted(runs) == ["K1", "K2"], runs)
    check("plan.no_all_shots", "D2=B" in m["normalizer"]["all_shots"] and "All" not in json.dumps(runs))
    check("plan.scope_states", m["scope_states"]["DIV"]["playhead"] == "shot10" and m["scope_states"]["DIV"]["selection"] == ["shot9"]
          and m["scope_states"]["CONV"]["playhead"] == "shot3" and m["scope_states"]["CONV"]["selection"] == ["shot3"]
          and "selection first" in m["scope_states"]["DIV"]["order"])
    check("plan.shot12_excluded", "EXCLUDED" in m["shots"]["shot12"]["role"] and "shot10" in m["shots"]
          and m["shots"]["shot9"]["animation_sets"] == {"krystalv21": "models/domibun/characters/starfox/krystalv2.mdl"})
    check("plan.decisions_recorded", m["decisions"]["D1"].startswith("A:") and m["decisions"]["D2"].startswith("B:")
          and m["decisions"]["D3"].startswith("B:") and m["decisions"]["D4"].startswith("YES"))
    check("plan.resource_thresholds_match_reader", not hasattr(reader, "STOP_MIN_AVAIL_VIRTUAL") and reader.STOP_MAX_PRIVATE == 3600 * 10 ** 6
          and reader.FAIL_PRIVATE_DELTA == 10 * 10 ** 6 and reader.FAIL_COUNTER_STEP == 10 and reader.NORMALIZER_BUDGET == 4)
    # K-0 amendment: free VAS is telemetry only; the Normalizer's own mem_ok=False is the primary memory/VAS STOP.
    stops = m["resources"]["stop_before_next_normalizer_command"]
    check("plan.amendment_no_vas_stop", len(stops) == 3 and stops[0].startswith("any Normalizer mem_ok=False")
          and not [x for x in stops if "avail_virtual" in x or "VAS" in x.split("(")[0]]
          and any("avail_virtual" in x for x in m["resources"]["telemetry_recorded_not_gated"])
          and "K1A1" in m["resources"]["amendment"] and "421 MB" in m["resources"]["amendment"], stops)
    tmpl = _read(TEMPLATE).decode("utf-8")
    check("template.placeholder_and_rules", "<attempt>" in tmpl and "selection first, playhead second" in tmpl
          and "OWNER-1" in tmpl and "D1 = A" in tmpl)


def _byte_form_matches(path, pin):
    raw = _read(path)
    return any(_sha(data) == pin for data in (raw, raw.replace(b"\r\n", b"\n"), raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")))


# ===========================================================================
# Static: probe derivation and purity
# ===========================================================================
def static_probe():
    raw = _read(PROBE)
    text = _read(ITEM8_PROBE).decode("ascii")
    problems = []
    for old, new, count in PROBE_DELTAS:
        if text.count(old) != count:
            problems.append((old[:50], text.count(old), count))
        text = text.replace(old, new)
    check("probe.every_delta_matches_exactly", not problems, problems)
    check("probe.equals_item8_probe_plus_declared_deltas", text.encode("ascii") == raw)
    check("probe.ascii_lf", all(b < 128 for b in bytearray(raw)) and b"\r" not in raw)
    tree = ast.parse(raw)
    check("probe.one_function_then_guarded_call_and_delete",
          len(tree.body) == 2 and isinstance(tree.body[0], ast.FunctionDef) and tree.body[0].name == "_cpm_k_probe_v1"
          and ast.get_docstring(tree) is None and type(tree.body[1]).__name__ in ("Try", "TryFinally"))
    check("probe.compiles", compile(raw, PROBE, "exec") is not None)
    used = t8._names_used(tree)
    check("probe.no_forbidden_names", not (used & t8.FORBIDDEN_NAMES), sorted(used & t8.FORBIDDEN_NAMES))
    bare = set(n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name))
    check("probe.no_dynamic_code", (bare & set(["compile", "exec", "eval", "execfile", "__import__"])) <= set(["__import__"]))
    ns_calls = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Subscript) and getattr(n.func.value, "id", None) == "ns":
            ns_calls.add(t8._const(n.func.slice))
    check("probe.cpm_calls_are_only_pure_scene_readers", ns_calls == t8.ALLOWED_NS_CALLS, sorted(ns_calls))
    broker_calls = set(n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                       and getattr(n.func.value, "id", None) == "broker")
    check("probe.broker_calls_are_read_accessors", broker_calls == t8.ALLOWED_BROKER_CALLS, sorted(broker_calls))
    k32 = set(n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and getattr(n.func.value, "id", None) == "kernel32")
    check("probe.kernel32_calls_read_only", k32 == set(["GetCurrentProcess", "GetProcessHandleCount", "GlobalMemoryStatusEx"]), sorted(k32))
    writes = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "open"
              and len(n.args) > 1 and t8._const(n.args[1]) in ("wb", "ab")]
    check("probe.write_sites_are_write_once_and_append", sorted(t8._const(n.args[1]) for n in writes) == ["ab", "wb"])
    code = "\n".join(l for l in raw.decode("ascii").splitlines() if not l.lstrip().startswith("#"))
    check("probe.no_timing_or_notice_modes", not any(t in code.lower() for t in ("timing", "notice", "placeholder", "harness")))
    check("probe.no_normalizer_invocation", not any(t in code for t in ("StartRebuildControlGroups()", "_choose_scope", ".start()")))
    check("probe.normalizer_sentinels_declared", all(("\"%s\"" % s) in code for s in NORMALIZER_SENTINELS))
    nsrc = _read(NORMALIZER).decode("utf-8")
    check("probe.normalizer_sentinels_are_normalizer_names",
          all(re.search(r"^(def|class) %s\b|^%s = " % (s, s), nsrc, re.M) for s in NORMALIZER_SENTINELS),
          [s for s in NORMALIZER_SENTINELS if not re.search(r"^(def|class) %s\b|^%s = " % (s, s), nsrc, re.M)])


# ===========================================================================
# Reader: Normalizer log grammar, views, idle, boundaries, resources
# ===========================================================================
def reader_checks():
    nsrc = _read(NORMALIZER).decode("utf-8")
    for fmt in ('"scope_mode=%s scope_shots=%d"', '"CONTEXTUALIZER_SCOPE_SHOT_NAMES = %r"', '"live Master SHA256=%s"',
                '"PRODUCTION_REBUILD_CONTROL_GROUPS = %s"', '"PRODUCTION_CONTEXTUALIZER = %s"', '"PRODUCTION_TERMINAL_RESULTS=%r"',
                '"PRODUCTION_REVISION = %s"', '"mem_ok=%r '):
        check("reader.normalizer_format_exists.%s" % re.sub(r"\W+", "_", fmt).strip("_")[:40], fmt in nsrc)
    sample = _read(NORMALIZER_LOG_SAMPLE).decode("utf-8")
    p = reader.parse_normalizer_log(sample)
    check("reader.real_log_parsed", p["scope_mode"] == "SELECTED_SHOTS" and p["scope_shots"] == 1 and p["shot_names"] == ["shot3"]
          and p["live_master_sha256"] == [G1] and p["mem_ok_true"] == 15 and p["mem_ok_false"] == 0 and p["cpm_lines"] == 0
          and p["terminal_results"] == [("foxmccouldwm1", "RECONCILED"), ("mia1", "RECONCILED")], p)
    check("reader.real_log_run_ok", reader.normalizer_run_check(p, ["shot3"], G1)["ok"], reader.normalizer_run_check(p, ["shot3"], G1))
    check("reader.wrong_generation_fails", not reader.normalizer_run_check(p, ["shot3"], G2)["ok"])
    check("reader.wrong_shot_fails", not reader.normalizer_run_check(p, ["shot9"], G1)["ok"])
    mutations = {
        "mem_ok_false": sample.replace("mem_ok=True", "mem_ok=False", 1),
        "rebuild_fail": sample.replace("PRODUCTION_REBUILD_CONTROL_GROUPS = PASS", "PRODUCTION_REBUILD_CONTROL_GROUPS = FAIL"),
        "two_shots": sample.replace("scope_mode=SELECTED_SHOTS scope_shots=1", "scope_mode=SELECTED_SHOTS scope_shots=2", 1),
        "cpm_line": sample + "\n[12:00:00.000000] PROD_APPLY outcome='committed'\n",
        "mixed_generation": sample + "\nlive Master SHA256=%s\n" % G2,
        "other_fail": sample.replace("PRODUCTION_DYNAMIC_ACCOUNTING = PASS", "PRODUCTION_DYNAMIC_ACCOUNTING = FAIL"),
    }
    for name, text in sorted(mutations.items()):
        check("reader.mutation_rejected.%s" % name, not reader.normalizer_run_check(reader.parse_normalizer_log(text), ["shot3"], G1)["ok"])
    check("reader.reuses_qualified_cpm_grammar", reader.parse_log is base.parse_log and reader.classify_library_diff is base.classify_library_diff
          and reader.verify_sha256sums is base.verify_sha256sums)

    def rec(views, leases=0, broker="0x1", res=None, constructed=True):
        return {"broker_before": {"observed": True, "runtime_loaded": True, "broker_constructed": constructed, "broker_id": broker,
                                  "outstanding_leases": leases, "unreleased_lease_registry": 0,
                                  "provider_counters": {"current_open_provider_count": 0}},
                "window": {"observed": True, "slot_occupied": False}, "acquisition_by_probe": {"determinable": True,
                                                                                                "probe_caused_acquisition": False},
                "broker_detail": {"broker_constructed": constructed, "views": views}, "resources": res or {"observed": True},
                "seq": 1}

    def view(kind, gen, live=0, stale=False):
        return {"consumer_kind": kind, "master_sha256": gen, "covered_keys": 3, "estimated_bytes": 10, "live_leases": live, "stale": stale}
    n_only = rec([view("normalizer_compat", G1)])
    both = rec([view("normalizer_compat", G1), view("cpm_compat_v1", G1)])
    check("views.per_consumer", reader.views_by_consumer(both) == {"normalizer_compat": {G1: {"views": 1, "live_leases": 0, "stale": 0}},
                                                                    "cpm_compat_v1": {G1: {"views": 1, "live_leases": 0, "stale": 0}}})
    check("views.idle_requires_no_live_view_lease", reader.k_idle_check(both)["idle"]
          and not reader.k_idle_check(rec([view("cpm_compat_v1", G1, live=1)]))["idle"])
    check("boundary.cpm_joins_normalizer_broker", reader.consumer_boundary(n_only, both, "cpm_compat_v1", G1)["ok"])
    lost = rec([view("cpm_compat_v1", G1)])
    check("boundary.lost_other_consumer_view_fails", not reader.consumer_boundary(n_only, lost, "cpm_compat_v1", G1)["ok"]
          and reader.consumer_boundary(n_only, lost, "cpm_compat_v1", G1)["other_consumer_views_lost"] == [G1])
    check("boundary.different_broker_fails", not reader.consumer_boundary(n_only, rec(both["broker_detail"]["views"], broker="0x2"),
                                                                          "cpm_compat_v1", G1)["ok"])
    check("boundary.wrong_generation_fails", not reader.consumer_boundary(n_only, both, "cpm_compat_v1", G2)["ok"])
    cold = rec([], constructed=False)
    cold["broker_before"] = {"observed": True, "runtime_loaded": False, "broker_constructed": False}
    check("boundary.normalizer_constructs_broker", reader.consumer_boundary(cold, n_only, "normalizer_compat", G1)["ok"])
    MB = 10 ** 6
    ok_res = {"observed": True, "avail_virtual": 900 * MB, "private_usage": 3100 * MB, "handles": 1200, "gdi_objects": 1200,
              "user_objects": 140}
    check("resources.stop_clear", not reader.resource_stop(rec([], res=ok_res))["stop"], reader.resource_stop(rec([], res=ok_res)))
    check("resources.python2_long_values_accepted", reader._is_int(3100 * MB) and reader._is_int(2 ** 40) and not reader._is_int(True)
          and not reader._is_int(3.5))
    high = dict(ok_res, private_usage=3601 * MB)
    # Regression (K1A1): a fresh fixture-loaded baseline with 528 MB free VAS (3,077 MB private) must not
    # STOP merely for being below 600 MB, nor for any low free VAS; mem_ok=False still STOPs.
    k1a1 = {"observed": True, "avail_virtual": 528838656, "total_virtual": 4294836224, "private_usage": 3076964352,
            "handles": 1157, "gdi_objects": 1121, "user_objects": 100}
    check("resources.regression_k1a1_528mb_vas_no_stop", not reader.resource_stop(rec([], res=k1a1))["stop"],
          reader.resource_stop(rec([], res=k1a1)))
    check("resources.regression_any_low_vas_no_stop", not reader.resource_stop(rec([], res=dict(k1a1, avail_virtual=50 * MB)))["stop"]
          and not reader.resource_stop(rec([], res=dict(k1a1, avail_virtual=None)))["stop"])
    check("resources.regression_mem_ok_false_still_stops", reader.resource_stop(rec([], res=k1a1), {"mem_ok_false": 1})["stop"]
          and "mem_ok=False" in reader.resource_stop(rec([], res=k1a1), {"mem_ok_false": 1})["reasons"][0])
    tel = reader.resource_telemetry(rec([], res=k1a1), reader.parse_normalizer_log(sample))
    vas_free = [int(x) for x in re.findall(r"\bmem_free=(\d+)", sample)]
    vas_large = [int(x) for x in re.findall(r"\blargest_free=(\d+)", sample)]
    check("resources.telemetry_recorded", tel["avail_virtual"] == 528838656 and tel["total_virtual"] == 4294836224
          and tel["normalizer_vas_samples"] == 10 and tel["normalizer_vas_ok_false"] == 0
          and tel["normalizer_vas_mem_free_min"] == min(vas_free) == 421031936
          and tel["normalizer_vas_largest_free_min"] == min(vas_large) == 191037440, tel)
    check("resources.stop_high_private", reader.resource_stop(rec([], res=high))["stop"])
    check("resources.stop_mem_ok_false", reader.resource_stop(rec([], res=ok_res), {"mem_ok_false": 1})["stop"])
    check("resources.stop_unobserved_is_stop", reader.resource_stop(rec([], res={"observed": False}))["stop"])

    def closed(seq, private, handles=1200, gdi=1200, user=140):
        r = rec([], res=dict(ok_res, private_usage=private, handles=handles, gdi_objects=gdi, user_objects=user))
        r["seq"] = seq
        return r
    flat = [closed(1, 3100 * MB), closed(2, 3105 * MB, handles=1205), closed(3, 3108 * MB, handles=1203)]
    check("resources.accumulation_flat_ok", reader.cpm_accumulation(flat)["ok"], reader.cpm_accumulation(flat))
    check("resources.accumulation_private_fail", not reader.cpm_accumulation([closed(1, 3100 * MB), closed(2, 3111 * MB)])["ok"])
    climb = [closed(1, 3100 * MB, user=140), closed(2, 3100 * MB, user=152), closed(3, 3100 * MB, user=164)]
    check("resources.accumulation_counter_twice_fail", not reader.cpm_accumulation(climb)["ok"])
    once = [closed(1, 3100 * MB, user=140), closed(2, 3100 * MB, user=152), closed(3, 3100 * MB, user=150)]
    check("resources.accumulation_counter_once_ok", reader.cpm_accumulation(once)["ok"])


def static_design():
    design = _read(DESIGN).decode("utf-8")
    drv = _read(DRIVER).decode("ascii")
    defined = set(re.findall(r"^function (K-[A-Za-z]+)", drv, re.M))
    named = set(re.findall(r"`(K-[A-Za-z]+)", design))
    check("design.every_named_k_function_exists", named and named <= defined, sorted(named - defined))
    check("design.k_pass_is_k1_k2_only", "K1 and K2" in design and "D2 = B" in design and "K3" in design)
    check("design.d3_selection_first", "selection first" in design.lower() and "playhead second" in design.lower())
    check("design.d1_no_new_mechanism", "D1 = A" in design)
    check("design.k0_status", "K PREPARED, NOT RUN" in design)


# ===========================================================================
# Probe runtime (child processes; R15 harness; real PySide/Qt 4.8 when importable + the Qt model)
# ===========================================================================
c = r15.c


class KProbe(t8.Probe):
    """The item-8 probe harness, rooted at the K attempt root and installing CPM_K_Probe.py."""

    def __init__(self, qt_mode, root, app_bytes=None):
        probe_bytes = _read(PROBE)
        self.env = r15.Env(qt_mode, root)
        main = types.ModuleType("__main__")
        main.__dict__.update(self.env.host)
        sys.modules["__main__"] = main
        self.env.host = main.__dict__
        if app_bytes is not None:
            self.env.deploy(impl_bytes=app_bytes)
        self.public = os.path.join(self.env.root, "public")
        self.i8root = os.path.join(self.public, "Documents", "CPM_K")
        os.makedirs(self.i8root)
        os.environ["PUBLIC"] = self.public
        self.path = os.path.join(self.env.menu_dir, "CPM_K_Probe.py")
        with open(self.path, "wb") as f:
            f.write(probe_bytes)
        self.attempt = os.path.join(self.i8root, "K1T1")

    def make_attempt(self, deployed=True):
        os.makedirs(os.path.join(self.attempt, "scene_snapshots"))
        with open(os.path.join(self.attempt, "authority_pins.json"), "wb") as f:
            f.write(b"{}")
        if deployed:
            self.mark_deployed()
        with open(os.path.join(self.i8root, "ACTIVE_ATTEMPT.txt"), "wb") as f:
            f.write(b"K1T1")


def _real_runtime():
    sys.path.insert(0, SHARED_PACKAGE_PARENT)
    sys.path.insert(0, os.path.join(_REPO, "tools"))
    for key in list(sys.modules):
        if key.startswith("sfm_master_authority_productionized"):
            del sys.modules[key]
    from sfm_master_authority_productionized import runtime
    return runtime


def _broker_state(broker):
    return (broker.outstanding_lease_count(), broker.unreleased_lease_count(), dict(broker.provider_counters()),
            broker.view_cache_entry_count(), len(broker.recent_diagnostics()), json.dumps(broker.ledger_snapshot(), sort_keys=True, default=str))


def scenario_normalizer_first(qt_mode, root):
    """Normalizer-first: a REAL canonical broker exists before CPM; the Normalizer's names sit in the
    shared __main__; the probe observes without acquiring; CPM then joins the same broker."""
    p = KProbe(qt_mode, root)
    out = p.run()
    c("refuse.no_pointer_nothing_written", "CPM_K_PROBE REFUSED" in out and not os.listdir(p.i8root), out)
    p.make_attempt(deployed=False)
    out = p.run()
    c("refuse.not_deployed", "REFUSED" in out and "not deployed" in out and not p.records(), out)
    p.mark_deployed()
    runtime = _real_runtime()
    broker = runtime.get_broker()                       # constructed by the "Normalizer" before CPM exists
    for name in NORMALIZER_SENTINELS:
        p.env.host[name] = object()                     # the Normalizer's shared-__main__ bindings
    host_before = sorted(p.env.host)
    before = _broker_state(broker)
    out = p.run()
    r = p.records()[-1]
    c("normalizer_first.record", r["seq"] == 1 and r["schema"] == "cpm-k-probe-record-v1" and "CPM_K_PROBE seq=1" in out, out)
    c("normalizer_first.no_cpm_module", r["module"] == {"observed": True, "present": False})
    c("normalizer_first.broker_constructed_without_cpm", r["broker_before"]["broker_constructed"] is True
      and r["broker_before"]["is_canonical"] is True and r["broker_before"]["broker_id"] == "0x%x" % id(broker), r["broker_before"])
    c("normalizer_first.normalizer_names_recorded", r["host"]["normalizer_names_in_main"] == sorted(NORMALIZER_SENTINELS)
      and r["host"]["cpm_names_in_main"] == [], r["host"])
    c("normalizer_first.main_dict_unchanged", sorted(p.env.host) == host_before)
    c("normalizer_first.broker_unchanged_by_probe", _broker_state(broker) == before)
    c("normalizer_first.no_probe_acquisition", r["acquisition_by_probe"] == {"determinable": True, "probe_caused_acquisition": False,
                                                                             "changed": []}, r["acquisition_by_probe"])
    c("normalizer_first.diagnostics_tail_list", isinstance(r["broker_detail"].get("diagnostics_tail"), list), r["broker_detail"])
    res = r["resources"]
    c("normalizer_first.vas_sample", res.get("observed") is True and reader._is_int(res.get("avail_virtual"))
      and reader._is_int(res.get("total_virtual")) and res["avail_virtual"] <= res["total_virtual"], res)
    c("normalizer_first.reader_idle", reader.k_idle_check(r)["idle"], reader.k_idle_check(r))
    c("normalizer_first.identity", reader.identity_check(r)["checks"]["installed_impl_is_candidate"] is True
      and r["identity"]["installed_probe_sha256"] == _sha(_read(PROBE)))
    # CPM joins: same broker; still no acquisition by the probe.
    p.env.click()
    p.env.settle()
    before = _broker_state(broker)
    p.run()
    r2 = p.records()[-1]
    c("cpm_joins.module_candidate", r2["module"]["present"] and r2["module"]["build_is_candidate"] is True, r2["module"])
    c("cpm_joins.same_broker", r2["broker_before"]["broker_id"] == r["broker_before"]["broker_id"])
    c("cpm_joins.broker_unchanged_by_probe", _broker_state(broker) == before)
    c("cpm_joins.identity_ok_except_interpreter", all(v for k, v in reader.identity_check(r2)["checks"].items() if k != "python_2_7_5"),
      reader.identity_check(r2))
    c("cpm_joins.normalizer_names_still_recorded", r2["host"]["normalizer_names_in_main"] == sorted(NORMALIZER_SENTINELS))
    c("reader.loads_records", [x["seq"] for x in reader.load_probe_records(p.attempt)] == [1, 2])
    snap = reader.load_snapshot(p.attempt, r2)
    c("reader.loads_snapshot", snap["schema"] == "cpm-k-scene-snapshot-v1" and snap["seq"] == 2)


def scenario_strict(qt_mode, root):
    """A strict broker holding both consumer kinds: only read accessors; diagnostics summarised;
    a live view lease is visible to the reader; explicit failures; write-once and append-only."""
    p = KProbe(qt_mode, root)
    p.make_attempt()
    broker = t8.StrictBroker()

    class NView(t8.View):
        consumer_kind = "normalizer_compat"
    leased = NView()
    leased.live_lease_count = lambda: 1
    broker.views = [NView(), t8.View()]
    diag = [{"event": "cohort_acquired", "t": 1.5, "detail": {"views": ["normalizer_compat"], "generation": G1, "folds": list(range(20)),
                                                             "nested": {"a": 1}}}]
    broker.recent_diagnostics = lambda: (broker.calls.append("recent_diagnostics"), diag)[1]
    sys.modules["sfm_master_authority_productionized.runtime"] = t8.fake_runtime(broker)
    p.env.click()
    p.env.settle()
    p.run()
    r = p.records()[-1]
    c("strict.only_read_accessors", set(broker.calls) <= t8.ALLOWED_BROKER_CALLS | set(["_view_cache.all_views"])
      and not [x for x in broker.calls if x.startswith("FORBIDDEN")], broker.calls)
    tail = r["broker_detail"]["diagnostics_tail"]
    c("strict.diagnostics_tail_summary", tail == [{"event": "cohort_acquired", "t": 1.5, "detail": {
        "views": ["normalizer_compat"], "generation": G1, "folds": 20, "nested": {"keys": 1}}}], tail)
    c("strict.both_consumers_seen", sorted(reader.views_by_consumer(r)) == ["cpm_compat_v1", "normalizer_compat"])
    c("strict.idle_with_no_live_leases", reader.k_idle_check(r)["idle"], reader.k_idle_check(r))
    broker.views = [leased, t8.View()]
    p.run()
    r = p.records()[-1]
    c("strict.live_view_lease_not_idle", not reader.k_idle_check(r)["idle"]
      and "live lease" in " ".join(reader.k_idle_check(r)["problems"]), reader.k_idle_check(r))
    broker.recent_diagnostics = lambda: (_ for _ in ()).throw(RuntimeError("injected diag failure"))
    p.run()
    r = p.records()[-1]
    c("strict.diagnostics_failure_explicit", r["broker_detail"]["diagnostics_tail"].get("observed") is False
      and "broker.diagnostics_tail" in r["errors"], r["broker_detail"].get("diagnostics_tail"))
    import ctypes
    real_windll = ctypes.WinDLL
    ctypes.WinDLL = lambda *a, **k: (_ for _ in ()).throw(OSError("injected"))
    try:
        p.run()
    finally:
        ctypes.WinDLL = real_windll
    r = p.records()[-1]
    c("strict.resources_failure_explicit", r["resources"] == {"observed": False, "error": "injected"} and "resources" in r["errors"])
    c("strict.resources_failure_is_stop", reader.resource_stop(r)["stop"])
    jsonl = os.path.join(p.attempt, "probe.jsonl")
    prefix = _read(jsonl)
    nxt = len(p.records()) + 1
    taken = os.path.join(p.attempt, "scene_snapshots", "probe_%04d.json" % nxt)
    with open(taken, "wb") as f:
        f.write(b"OCCUPIED")
    p.run()
    r = p.records()[-1]
    c("write_once.existing_snapshot_not_overwritten", _read(taken) == b"OCCUPIED" and r["scene_snapshot"]["observed"] is False)
    c("write_once.append_only", _read(jsonl).startswith(prefix))
    with open(os.path.join(p.attempt, "SHA256SUMS.txt"), "wb") as f:
        f.write(b"")
    before = _read(jsonl)
    out = p.run()
    c("write_once.sealed_attempt_refused", "REFUSED" in out and "sealed" in out and _read(jsonl) == before, out)


def scenario_pin_mismatch(qt_mode, root):
    """The item-8 build installed instead of the K candidate: reported, and the reader's identity fails."""
    item8 = subprocess.check_output(["git", "-C", _REPO, "show", "2fe9a27:cpm/app/SFM_Character_Preset_Manager.py"])
    c("pin.item8_bytes", _sha(item8) == ITEM8_APP)
    p = KProbe(qt_mode, root, app_bytes=item8)
    p.make_attempt()
    sys.modules["sfm_master_authority_productionized.runtime"] = t8.fake_runtime(t8.StrictBroker())
    p.env.click()
    p.env.settle()
    p.run()
    r = p.records()[-1]
    ic = reader.identity_check(r)
    c("pin.not_candidate_reported", r["identity"]["impl_is_candidate"] is False and r["module"]["build_sha256"] == ITEM8_APP)
    c("pin.reader_identity_fails", not ic["ok"] and ic["checks"]["installed_impl_is_candidate"] is False
      and ic["checks"]["module_build_is_candidate"] is False, ic)


SCENARIOS = [("normalizer_first", scenario_normalizer_first), ("strict", scenario_strict), ("pin_mismatch", scenario_pin_mismatch)]


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
    proc = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--child=%s" % name, "--qt=%s" % mode, "--root=%s" % root],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    output = proc.communicate()[0].decode("utf-8", "replace")
    for line in output.splitlines():
        if line.startswith("R15_CHILD_RESULT "):
            return json.loads(line[len("R15_CHILD_RESULT "):]), output
    return None, output


# ===========================================================================
# Driver (Python 3 + Windows PowerShell 5.1): frozen block and sandbox end to end
# ===========================================================================
def frozen_block():
    md = subprocess.check_output(["git", "-C", _REPO, "show", "0597927:real_sfm_qualification/cpm_session2/SESSION2_RUNBOOK.md"]
                                 ).decode("utf-8").replace("\r\n", "\n")
    block = re.search(r"### 2\.1 Set-up \(Windows PowerShell 5\.1\)\n.*?```powershell\n(.*?)```\n", md, re.S).group(1)
    frozen = block.split("\n")[:-1]
    drv = _read(DRIVER).decode("ascii").split("\n")
    start = drv.index("# ---- CPM Session 2 shell set-up. Fill the two placeholders, then paste the whole block. ----")
    section = drv[start:start + len(frozen)]
    diffs = [(i, a, b) for i, (a, b) in enumerate(zip(frozen, section)) if a != b]
    check("frozen.block_length", len(section) == len(frozen) == 158, len(frozen))
    check("frozen.only_placeholders_filled", diffs == [
        (1, '$R    = "<repository root>"', "$R    = $RepoRoot"),
        (2, '$GAME = "<SFM game>"            # the folder containing sfm.exe', "$GAME = $Game                 # the folder containing sfm.exe")], diffs)
    i8 = _read(ITEM8_DRIVER).decode("ascii")
    sec1 = lambda t: t[t.index("# ===========================================================================\n# Section 1"):
                       t.index("# ===========================================================================\n# Section 2")]
    check("frozen.section1_identical_to_item8_driver", sec1(_read(DRIVER).decode("ascii")) == sec1(i8))
    rest = "\n".join(drv[start + len(frozen):])
    for name in ("S2-Prepare", "S2-PhaseA", "S2-PhaseB", "S2-Finalize", "S2-VerifyUntouched", "S2-Inventory", "S2-Compare",
                 "Write-LibInventory", "Compare-LibInventory", "S2-Sha", "S2-New"):
        check("frozen.not_redefined.%s" % name, ("function %s" % name) not in rest)
    pythons = [l for l in rest.split("\n") if "& python" in l or "S2-Py " in l]
    check("frozen.no_generation_tooling_calls_outside_block", not any(t in rest for t in (
        "prepare-publish-g2", "activate-g2", "finalize --", "inventory --", "compare --"))
        and len(pythons) == 1 and "& python --version" in pythons[0], pythons)
    check("driver.never_writes_the_app", not re.search(r"(Copy-Item|Replace|WriteAll\w*)[^\n]*\$APP_DST", rest)
          and "$APP_DST + " not in rest, re.findall(r"[^\n]*\$APP_DST[^\n]*", rest))
    check("driver.ascii_lf", all(b < 128 for b in bytearray(_read(DRIVER))) and b"\r" not in _read(DRIVER))
    script = os.path.join(tempfile.gettempdir(), "cpm_k_parse.ps1")
    _write(script, ("$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('%s',[ref]$null,[ref]$e);"
                    " if($e){$e|%%{$_.ToString()}} else {'PARSE OK'}; $PSVersionTable.PSVersion.Major\n" % DRIVER).encode("ascii"))
    out = subprocess.check_output(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script]).decode("utf-8", "replace")
    check("driver.parses_in_windows_powershell", "PARSE OK" in out, out)
    check("driver.windows_powershell_5", out.split()[-1] == "5", out.split()[-1:])


def _git_show(spec):
    return subprocess.check_output(["git", "-C", _REPO, "show", spec])


def _inventory(scripts):
    rows = []
    for b, _d, files in os.walk(scripts):
        for f in files:
            p = os.path.join(b, f)
            rows.append(os.path.relpath(p, scripts).replace(os.sep, "/") + "\t" + _sha(_read(p)))
    rows.sort()
    return ("\n".join(rows) + "\n").encode("utf-8")


def build_sandbox():
    if os.path.isdir(SANDBOX):
        shutil.rmtree(SANDBOX)
    m = _manifest()
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
    app = os.path.join(scripts, "ChadChan3D_CPM", "SFM_Character_Preset_Manager.py")
    _write(app, _git_show("9d405c8:cpm/app/SFM_Character_Preset_Manager.py"))      # the Session 4 accepted state
    srcs = {"sfm/mainmenu/ChadChan3D/SFM_Character_Preset_Manager.py": os.path.join(_REPO, "cpm", "app", "launcher", "SFM_Character_Preset_Manager.py"),
            "sfm/mainmenu/ChadChan3D/cpm_authority_adapter.py": os.path.join(_REPO, "cpm", "convergence", "cpm_authority_adapter.py"),
            "sfm/mainmenu/ChadChan3D/cpm_compat_v1_projection.py": os.path.join(_REPO, "cpm", "convergence", "cpm_compat_v1_projection.py"),
            "sfm/mainmenu/ChadChan3D/Rebuild_Control_Groups_Normalizer.py": NORMALIZER}
    for rel, pin in m["deployment"]["unchanged_menu_dependencies"].items():
        _write(os.path.join(scripts, *rel.split("/")), t8_pinned(srcs[rel], pin))
    pkg_src = os.path.join(SHARED_PACKAGE_PARENT, "sfm_master_authority_productionized")
    for name, pin in m["deployment"]["shared_package"]["files"].items():
        _write(os.path.join(menu, "sfm_master_authority_productionized", name), t8_pinned(os.path.join(pkg_src, name), pin))
    for name, pin in m["deployment"]["sidecar_reader"]["files"].items():
        _write(os.path.join(menu, "sfm_master_sidecar", name), t8_pinned(os.path.join(_REPO, "tools", "sfm_master_sidecar", name), pin))
    _write(os.path.join(menu, "CPM_Session1_Probe.py"), _read(os.path.join(_REPO, "real_sfm_qualification", "cpm_session1", "CPM_Session1_Probe.py")))
    _write(os.path.join(scripts, "sfm", "mainmenu", "SFM_Character_Slider_Preset_Tool_0.1.1.py"), b"APP_ATTR = '_sfm_character_slider_preset_tool_window'\n")
    _write(os.path.join(scripts, "sfm", "gate_r2_deploy", "sfm_master_sidecar", "__init__.py"), b"# historical copy\n")
    accepted = _inventory(scripts)                                                     # Session 4 accepted (9a78fc96...)
    _write(os.path.join(SANDBOX, "accepted_inventory.txt"), accepted)
    _write(app, _read(APP))                                                            # pre-K U3: the K candidate installed
    expected = accepted.replace(("\t%s" % S4_APP).encode("ascii"), ("\t%s" % CANDIDATE).encode("ascii"))
    chars = os.path.join(SANDBOX, "docs", "SFM Character Preset Manager", "Characters")
    _write(os.path.join(chars, "mia--2e6533ed1490", "character.json"), b'{"profile": 1}\n')
    _write(os.path.join(chars, "krystal2020--7d2aee52ef3a", "Body Presets", "Body--preset-aaaaa.json"), b"{}\n")
    _write(os.path.join(SANDBOX, "docs", "testscripts.dmx"), b"<fixture>")
    os.makedirs(os.path.join(SANDBOX, "public", "Documents"))
    _write(os.path.join(SANDBOX, "public", "Documents", "SFM_CSP_G18AN_SaveNewCopy.log"), b"[00:00:00.000000] G18AN_RUN x\n")
    _write(os.path.join(SANDBOX, "public", "Documents", "sfm_rebuild_control_groups.txt"), _read(NORMALIZER_LOG_SAMPLE))
    return {"game": game, "scripts": scripts, "menu": menu, "cfg": cfg, "auth": auth, "app": app, "chars": chars,
            "expected_sha": _sha(expected), "accepted_sha": _sha(accepted), "doc": os.path.join(SANDBOX, "docs", "testscripts.dmx")}


def t8_pinned(path, pin):
    raw = _read(path)
    for data in (raw, raw.replace(b"\r\n", b"\n"), raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")):
        if _sha(data) == pin:
            return data
    raise AssertionError("no byte form of %s matches %s" % (path, pin))


PS_PRELUDE = r"""
$ErrorActionPreference = "Continue"
$env:PUBLIC = "%(public)s"
. "%(driver)s" -RepoRoot "%(repo)s" -Game "%(game)s" | Out-Null
$CHARACTERS = "%(chars)s"
$ACCEPTED_SCRIPTS = "%(sandbox)s\accepted_inventory.txt"
$ACCEPTED_SCRIPTS_SHA = "%(accepted_sha)s"
$EXPECTED_SCRIPTS_SHA = "%(expected_sha)s"
$FIXTURE_DOCUMENT_SHA = "%(doc_sha)s"
function Step([string]$Name, [scriptblock]$Body) {
    "<<STEP $Name BEGIN>>"
    try { & $Body 2>&1 | ForEach-Object { "$_" }; "<<END $Name OK>>" } catch { "<<END $Name STOP>> $($_.Exception.Message)" }
}
"""


def run_ps(p, body):
    script = PS_PRELUDE % {"public": os.path.join(SANDBOX, "public"), "driver": DRIVER, "repo": _REPO, "game": p["game"],
                           "chars": p["chars"], "sandbox": SANDBOX, "accepted_sha": p["accepted_sha"],
                           "expected_sha": p["expected_sha"], "doc_sha": _sha(_read(p["doc"]))} + body
    path = os.path.join(SANDBOX, "step.ps1")
    _write(path, script.encode("ascii"))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PATH=os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", ""))
    out = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", path],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env).stdout.decode("utf-8", "replace")
    steps = {}
    for m in re.finditer(r"<<STEP (\S+) BEGIN>>(.*?)<<END \1 (OK|STOP)>>([^\n]*)", out, re.S):
        steps[m.group(1)] = (m.group(3), m.group(2) + m.group(4))
    return steps, out


def attempt(name):
    return os.path.join(SANDBOX, "public", "Documents", "CPM_K", name)


def st(steps, name):
    return steps.get(name, ("MISSING", ""))[0]


def sandbox_end_to_end():
    p = build_sandbox()
    master = os.path.join(p["cfg"], "sfm_defaultanimationgroups.txt")
    check("sandbox.production_g1_and_k_candidate_installed", _sha(_read(master)) == G1 and _sha(_read(p["app"])) == CANDIDATE
          and os.path.isfile(os.path.join(p["auth"], "sfm_master_0_%s.sfmsidecar" % G1_SIDECAR)))
    temp_before = set(n for n in os.listdir(tempfile.gettempdir()) if n.startswith(("cpm_k_preflight_", "cpm_k_expected_", "cpm_k_inventory_")))
    wrong_doc = os.path.join(SANDBOX, "docs", "other.dmx")
    _write(wrong_doc, b"<other>")
    steps, out = run_ps(p, """
Step preflight_before_new { K-Preflight K1T1 -Owner1Recorded }
Step new_wrong_document { K-New K1T1 "%(wrong)s" }
Step new { K-New K1T1 "%(doc)s" }
Step new_again { K-New K1T1 "%(doc)s" }
Step preflight_owner1_missing { K-Preflight K1T1 }
""" % {"doc": p["doc"], "wrong": wrong_doc})
    check("gate.preflight_requires_new", st(steps, "preflight_before_new") == "STOP")
    check("gate.wrong_fixture_document_refused", st(steps, "new_wrong_document") == "STOP"
          and "not the pinned" in steps["new_wrong_document"][1], steps.get("new_wrong_document"))
    check("new.created", st(steps, "new") == "OK" and all(os.path.exists(os.path.join(attempt("K1T1"), f)) for f in (
        "authority_pins.json", "fixture_manifest.json", "operator_steps.md", "scene_snapshots", "library_inventories",
        "preset_readback", "logs", "restoration")), out[-1500:])
    pins = json.loads(_read(os.path.join(attempt("K1T1"), "authority_pins.json")).decode("utf-8"))
    check("new.pins", pins["k_candidate_app_sha256"] == CANDIDATE and pins["probe_sha256"] == _sha(_read(PROBE))
          and pins["fixture_manifest_sha256"] == _sha(_read(MANIFEST)) and pins["G1"]["master_sha256"] == G1
          and pins["G2"]["master_sha256"] == G2 and pins["expected_scripts_inventory_sha256"] == p["expected_sha"])
    check("new.operator_record", b"attempt `K1T1`" in _read(os.path.join(attempt("K1T1"), "operator_steps.md")))
    check("new.write_once", st(steps, "new_again") == "STOP")
    o1 = steps.get("preflight_owner1_missing", ("", ""))
    check("gate.owner1_required", o1[0] == "STOP" and "OWNER-1" in o1[1] and "SFM_Character_Slider_Preset_Tool_0.1.1.py" in out, o1)
    # Read-only STOPs write nothing.
    gates = []
    harness = os.path.join(p["menu"], "CPM_S4_Rollback_Harness.py")
    gates.append(("harness_residue", lambda: _write(harness, b"x"), lambda: os.remove(harness), "PRESENT:"))
    i8ptr = os.path.join(SANDBOX, "public", "Documents", "CPM_Item8", "ACTIVE_ATTEMPT.txt")
    gates.append(("item8_pointer_residue", lambda: _write(i8ptr, b"I8A1"), lambda: os.remove(i8ptr), "PRESENT:"))
    adapter = os.path.join(p["menu"], "cpm_authority_adapter.py")
    good = _read(adapter)
    gates.append(("changed_dependency", lambda: _write(adapter, good + b"\n# tampered\n"), lambda: _write(adapter, good), "UNEXPECTED SCRIPTS"))
    unexpected = os.path.join(p["scripts"], "sfm", "mainmenu", "Unexpected_Script.py")
    gates.append(("unexpected_script", lambda: _write(unexpected, b"x"), lambda: os.remove(unexpected), "+sfm/mainmenu/Unexpected_Script.py"))
    k_app = _read(p["app"])
    gates.append(("installed_app_not_candidate", lambda: _write(p["app"], _git_show("2fe9a27:cpm/app/SFM_Character_Preset_Manager.py")),
                  lambda: _write(p["app"], k_app), ITEM8_APP))
    gates.append(("fixture_changed", lambda: _write(p["doc"], b"<changed>"), lambda: _write(p["doc"], b"<fixture>"), "fixture document changed"))
    for name, setup, undo, marker in gates:
        setup()
        steps, out = run_ps(p, "Step g { K-Preflight K1T1 -Owner1Recorded }\n")
        undo()
        check("gate.%s_stops" % name, st(steps, "g") == "STOP" and marker in out, out[-900:])
    check("gate.read_only_stops_wrote_nothing", not os.listdir(os.path.join(attempt("K1T1"), "restoration"))
          and not os.path.exists(os.path.join(attempt("K1T1"), "generation")))
    temp_after = set(n for n in os.listdir(tempfile.gettempdir()) if n.startswith(("cpm_k_preflight_", "cpm_k_expected_", "cpm_k_inventory_")))
    check("gate.no_temporary_files_leaked", temp_after == temp_before, sorted(temp_after - temp_before))
    # K2-style attempt: preflight, probe deployment, run-time evidence, the one generation transition.
    preset_rel = "krystal2020--7d2aee52ef3a/Body Presets/K K1T1 A2 BODY--preset-0a1b2.json"
    steps, out = run_ps(p, """
Step preflight { K-Preflight K1T1 -Owner1Recorded }
Step preflight_again { K-Preflight K1T1 -Owner1Recorded }
Step deploy { K-DeployProbe K1T1 }
Step deploy_again { K-DeployProbe K1T1 }
Step new_while_active { K-New K9T1 "%(doc)s" }
Step lib_before { K-Library K1T1 library_A1_before_save }
Step switch { K-GenerationSwitch K1T1 }
Step switch_again { K-GenerationSwitch K1T1 }
Step readback_missing { K-Readback K1T1 A2 "*/Body Presets/K K1T1 A2 BODY--preset-*.json" }
""" % {"doc": p["doc"]})
    check("preflight.ok", st(steps, "preflight") == "OK" and "S2 BASELINE OK" in out and "K PREFLIGHT OK" in out, out[-2000:])
    before = json.loads(_read(os.path.join(attempt("K1T1"), "deployment_before.json")).decode("utf-8"))
    check("preflight.record", before["installed_app_sha256"] == CANDIDATE and before["owner1_recorded"] is True
          and before["scripts_inventory_equals_expected"] is True and before["fixture_document_sha256"] == _sha(b"<fixture>")
          and before["normalizer_log"]["exists"] is True and before["python_for_generation_tooling"].startswith("Python 3."), before)
    check("preflight.inventory_is_expected", _sha(_read(os.path.join(attempt("K1T1"), "restoration", "scripts_inventory_before_deploy.txt")))
          == p["expected_sha"])
    check("preflight.write_once", st(steps, "preflight_again") == "STOP")
    check("deploy.ok_probe_only", st(steps, "deploy") == "OK" and "K READY" in out and _read(os.path.join(p["menu"], "CPM_K_Probe.py")) == _read(PROBE)
          and _sha(_read(p["app"])) == CANDIDATE, out[-1500:])
    check("deploy.pointer", _read(os.path.join(SANDBOX, "public", "Documents", "CPM_K", "ACTIVE_ATTEMPT.txt")) == b"K1T1")
    after = json.loads(_read(os.path.join(attempt("K1T1"), "deployment_after.json")).decode("utf-8"))
    check("deploy.record", after["installed_app_sha256"] == CANDIDATE and after["installed_probe_sha256"] == _sha(_read(PROBE)))
    diff = sorted(set(_read(os.path.join(attempt("K1T1"), "restoration", "scripts_inventory_after_deploy.txt")).decode("utf-8").split("\n"))
                  ^ set(_read(os.path.join(attempt("K1T1"), "restoration", "scripts_inventory_before_deploy.txt")).decode("utf-8").split("\n")))
    check("deploy.exactly_one_probe_line", diff == ["sfm/mainmenu/ChadChan3D/CPM_K_Probe.py\t%s" % _sha(_read(PROBE))], diff)
    check("deploy.write_once", st(steps, "deploy_again") == "STOP")
    check("deploy.single_active_attempt", st(steps, "new_while_active") == "STOP" and not os.path.exists(attempt("K9T1")))
    check("switch.ok_exact_g2", st(steps, "switch") == "OK" and "S2 PHASE A OK" in out and "S2 G2 ACTIVE OK" in out
          and _sha(_read(master)) == G2, out[-2500:])
    check("switch.only_one_transition", st(steps, "switch_again") == "STOP")
    check("readback.zero_matches_stops", st(steps, "readback_missing") == "STOP")
    _write(os.path.join(p["chars"], *preset_rel.split("/")), json.dumps({"values": {"flex.Fat": {"representation": "MONO", "mono": 0.3}}}).encode("utf-8"))
    late = os.path.join(p["menu"], "Late_Unexpected.py")
    _write(late, b"x")
    steps, out = run_ps(p, """
Step readback { K-Readback K1T1 A2 "*/Body Presets/K K1T1 A2 BODY--preset-*.json" }
Step lib_after { K-Library K1T1 library_A3_after_save }
Step lib_compare { K-LibraryCompare K1T1 library_A1_before_save library_A3_after_save }
Step logs { K-CollectLogs K1T1 N1 }
Step remove_too_early { K-RemoveProbe K1T1 }
""")
    check("readback.copied_and_parsed", st(steps, "readback") == "OK" and reader.preset_value(reader.load_json(
        os.path.join(attempt("K1T1"), "preset_readback", "A2.json")), "Fat") == {"mono": 0.3})
    src = json.loads(_read(os.path.join(attempt("K1T1"), "preset_readback", "A2.source.json")).decode("utf-8"))
    check("readback.source_relative_to_characters_root", src["characters_relative_path"] == preset_rel)
    libdiff = reader.classify_library_diff(reader.load_library_inventory(os.path.join(attempt("K1T1"), "library_inventories", "library_A1_before_save.txt")),
                                           reader.load_library_inventory(os.path.join(attempt("K1T1"), "library_inventories", "library_A3_after_save.txt")), [])
    check("library.whole_root_inventory_sees_new_preset", libdiff["added"] == [preset_rel] and "LIBRARY DIFFERENT" in out, libdiff)
    nlog = os.path.join(attempt("K1T1"), "logs", "N1__sfm_rebuild_control_groups.txt")
    check("logs.normalizer_log_collected_and_parsed", st(steps, "logs") == "OK" and reader.normalizer_run_check(
        reader.parse_normalizer_log(_read(nlog).decode("utf-8")), ["shot3"], G1)["ok"])
    check("remove.unexpected_change_stops_and_is_named", st(steps, "remove_too_early") == "STOP"
          and "+sfm/mainmenu/ChadChan3D/Late_Unexpected.py" in out, out[-1200:])
    os.remove(late)
    check("remove.refusal_left_no_record", not os.path.exists(os.path.join(attempt("K1T1"), "restoration", "qualification_removal.json")))
    steps, out = run_ps(p, """
Step disposition_too_early { K-Disposition K1T1 -Verdict PASS }
Step finalize { K-Finalize K1T1 }
Step remove { K-RemoveProbe K1T1 }
Step disposition { K-Disposition K1T1 -Verdict PASS }
Step disposition_again { K-Disposition K1T1 -Verdict FAIL }
""")
    check("disposition.requires_removal", st(steps, "disposition_too_early") == "STOP")
    check("finalize.exact_g1", st(steps, "finalize") == "OK" and "S2 RESTORED EXACT G1" in out and _sha(_read(master)) == G1
          and sorted(n for n in os.listdir(p["auth"]) if n.endswith(".sfmsidecar")) == ["sfm_master_0_%s.sfmsidecar" % G1_SIDECAR], out[-2000:])
    check("remove.ok", st(steps, "remove") == "OK" and not os.path.exists(os.path.join(p["menu"], "CPM_K_Probe.py"))
          and not os.path.exists(os.path.join(SANDBOX, "public", "Documents", "CPM_K", "ACTIVE_ATTEMPT.txt")), out[-1500:])
    rem = json.loads(_read(os.path.join(attempt("K1T1"), "restoration", "qualification_removal.json")).decode("utf-8"))
    check("remove.app_and_fixture_unchanged", rem["installed_app_sha256"] == CANDIDATE and rem["fixture_document_sha256"] == _sha(b"<fixture>"))
    check("disposition.pass_app_unchanged", st(steps, "disposition") == "OK" and _sha(_read(p["app"])) == CANDIDATE, out[-1500:])
    check("disposition.final_inventory_expected", _sha(_read(os.path.join(attempt("K1T1"), "restoration", "scripts_inventory_final.txt")))
          == p["expected_sha"])
    disp = json.loads(_read(os.path.join(attempt("K1T1"), "restoration", "disposition.json")).decode("utf-8"))
    check("disposition.record", disp["verdict"] == "PASS" and disp["installed_app_sha256"] == CANDIDATE
          and disp["authority_restoration"] == "restore_compare.json")
    check("disposition.sealed_and_verifiable", reader.verify_sha256sums(attempt("K1T1"))["ok"])
    check("disposition.write_once", st(steps, "disposition_again") == "STOP")
    # K1-style attempt: no transition -> untouched proof; a FAIL verdict still never changes the app.
    steps, out = run_ps(p, """
Step new { K-New K1T2 "%(doc)s" }
Step preflight { K-Preflight K1T2 -Owner1Recorded }
Step deploy { K-DeployProbe K1T2 }
Step finalize { K-Finalize K1T2 }
Step remove { K-RemoveProbe K1T2 }
Step disposition { K-Disposition K1T2 -Verdict FAIL }
""" % {"doc": p["doc"]})
    check("k1.flow", all(st(steps, s) == "OK" for s in ("new", "preflight", "deploy", "finalize", "remove", "disposition")),
          dict((k, v[0]) for k, v in steps.items()))
    check("k1.untouched_authority_proof", "S2 UNTOUCHED" in out and json.loads(_read(os.path.join(
        attempt("K1T2"), "generation", "untouched_compare.json")).decode("utf-8-sig"))["exact_match"] is True)
    check("k1.fail_verdict_never_changes_app", _sha(_read(p["app"])) == CANDIDATE and json.loads(_read(os.path.join(
        attempt("K1T2"), "restoration", "disposition.json")).decode("utf-8"))["verdict"] == "FAIL")
    # A fixture changed during an attempt: removal STOPs (and writes no record).
    steps, out = run_ps(p, """
Step new { K-New K1T3 "%(doc)s" }
Step preflight { K-Preflight K1T3 -Owner1Recorded }
Step deploy { K-DeployProbe K1T3 }
""" % {"doc": p["doc"]})
    _write(p["doc"], b"<saved by mistake>")
    steps2, out2 = run_ps(p, "Step remove { K-RemoveProbe K1T3 }\n")
    check("fixture.changed_document_stops_removal", st(steps, "deploy") == "OK" and st(steps2, "remove") == "STOP"
          and "fixture document changed" in out2 and not os.path.exists(os.path.join(attempt("K1T3"), "restoration", "qualification_removal.json")),
          out2[-800:])
    check("sandbox.real_public_untouched", not os.path.exists(os.path.join(os.environ.get("PUBLIC", "x"), "Documents", "CPM_K", "K1T1")))


def main():
    args = dict(a.split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    if "--child" in args:
        child_main(args["--child"], args["--qt"], args["--root"])
        return
    if args.get("--phase") != "run":
        print("usage: %s --phase=run" % os.path.basename(sys.argv[0]))
        sys.exit(2)
    print("Interpreter: %s" % sys.version.split()[0])
    if os.path.isdir(FIXTURE_ROOT):
        shutil.rmtree(FIXTURE_ROOT)
    os.makedirs(FIXTURE_ROOT)
    static_pins()
    static_probe()
    reader_checks()
    static_design()
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
    if PY2:
        print("(driver checks run under Python 3: the frozen generation tooling is Python-3-only)")
    else:
        frozen_block()
        sandbox_end_to_end()
    passed = sum(1 for r in RESULTS if r[1])
    print("\nRESULT: %d/%d %s" % (passed, len(RESULTS), "ALL PASS" if passed == len(RESULTS) else "SOME FAILED"))
    if passed != len(RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
