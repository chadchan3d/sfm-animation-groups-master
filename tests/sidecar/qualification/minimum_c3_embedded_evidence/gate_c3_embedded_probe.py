# -*- coding: utf-8 -*-
# MINIMUM C3 -- embedded Python 2.7.5 qualification of command-boundary
# source freshness, old-generation retirement, active-lease drain,
# terminal close, and next-command lazy G2 readmission. Real SFM,
# Qt/main-event thread, event-loop scheduling (no long main-thread
# sleeps). Read-only w.r.t. the real project: never calls sfmApp/vs/
# native Rebuild, never touches Character Preset, never mutates the
# project. G1/G2 fixture generations were pre-compiled on desktop
# Python 3 (the production compiler/writer/manifest pipeline is
# Python-3-only) and deployed as static files; this probe only reads
# them and exercises the qualification owner/command-boundary logic.

import sys
import os
import time
import json
import shutil

try:
    unicode
except NameError:
    unicode = str

SCRATCH = r"C:\Users\REDACTED\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\67454949-e69f-4280-93d9-87c1f4464330\scratchpad"
GAME_SCRIPTS = r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts"
DEPLOY = os.path.join(GAME_SCRIPTS, "sfm", "gate_c3_deploy")
FIXTURES = os.path.join(DEPLOY, "fixtures")
LIVE_MASTER_PATH = os.path.join(DEPLOY, "master.txt")
LIVE_MANIFEST_PATH = os.path.join(DEPLOY, "manifest.json")
LIVE_GENERATIONS_DIR = os.path.join(DEPLOY, "generations")
REPO_TOOLS = r"E:\SFM Animation Group Master\tools"

RESULT_LOG_PATH = SCRATCH + r"\gate_c3_embedded_result.log"
STAGE_LOG_PATH = SCRATCH + r"\gate_c3_embedded_stage_markers.log"
DONE_MARKER_PATH = SCRATCH + r"\gate_c3_embedded_DONE.marker"
RESULTS_JSON_PATH = SCRATCH + r"\gate_c3_embedded_results.json"

_lines = []


def log(msg):
    line = msg if isinstance(msg, unicode) else (msg.decode("utf-8", "replace") if isinstance(msg, str) else unicode(msg))
    _lines.append(u"[%.3f] %s" % (time.time(), line))
    f = open(RESULT_LOG_PATH, "wb")
    try:
        f.write((u"\n".join(_lines) + u"\n").encode("utf-8"))
    finally:
        f.close()


def mark_stage(name):
    ts = time.time()
    f = open(STAGE_LOG_PATH, "ab")
    try:
        f.write(("%s %r\n" % (name, ts)).encode("ascii"))
    finally:
        f.close()
    log(u"STAGE %s" % name)


_pass = [0]
_fail = [0]


def check(label, condition, detail=u""):
    if condition:
        _pass[0] += 1
        log(u"  PASS: %s %s" % (label, detail))
    else:
        _fail[0] += 1
        log(u"  FAIL: %s %s" % (label, detail))
    return condition


log(u"Minimum C3 embedded probe loaded, pid=%r sys.version=%r" % (os.getpid(), sys.version))

_qt_available = False
try:
    from PySide import QtCore
    _qt_available = True
    log(u"PySide import PASS")
except Exception as exc:
    log(u"PySide import FAILED: %r" % (exc,))

state = {}


def _guarded(fn):
    def wrapper():
        try:
            fn()
        except Exception:
            import traceback
            log(u"UNCAUGHT EXCEPTION in %s:\n%s" % (fn.__name__, traceback.format_exc()))
            marker = open(DONE_MARKER_PATH, "wb")
            try:
                marker.write(b"done-with-exception\n")
            finally:
                marker.close()
    return wrapper


def schedule(delay_ms, fn):
    QtCore.QTimer.singleShot(delay_ms, _guarded(fn))


class _PE(Exception):
    pass


def sufficient_snapshot():
    so = state["so"]
    return so.ResourceSnapshot(400 * 1024 * 1024, 800 * 1024 * 1024, 300 * 1024 * 1024,
                                free_vas=2000 * 1024 * 1024, largest_free_region=1500 * 1024 * 1024)


def phase_begin():
    mark_stage("BEGIN")
    for p in (DEPLOY, os.path.join(DEPLOY, "qualification"), SCRATCH, REPO_TOOLS):
        if sys.path.count(p) == 0:
            sys.path.insert(0, p)

    import bounded_provider
    import bounded_view
    import resource_budgets
    import session_owner as so
    import command_boundary as cb
    from sfm_master_sidecar import manifest as sidecar_manifest
    from sfm_master_sidecar import format as fmt

    state["bounded_provider"] = bounded_provider
    state["bounded_view"] = bounded_view
    state["resource_budgets"] = resource_budgets
    state["so"] = so
    state["cb"] = cb
    state["manifest"] = sidecar_manifest

    so._reset_registry_for_testing()
    if os.path.isdir(LIVE_GENERATIONS_DIR):
        shutil.rmtree(LIVE_GENERATIONS_DIR)
    os.makedirs(LIVE_GENERATIONS_DIR)
    shutil.copy(os.path.join(FIXTURES, "master_g1.txt"), LIVE_MASTER_PATH)
    shutil.copy(os.path.join(FIXTURES, "manifest_g1.json"), LIVE_MANIFEST_PATH)
    for fn in os.listdir(os.path.join(FIXTURES, "generations")):
        shutil.copy(os.path.join(FIXTURES, "generations", fn), os.path.join(LIVE_GENERATIONS_DIR, fn))

    state["budgets"] = so.ViewBudgets.from_qualification_defaults(resource_budgets)
    state["guard"] = so.GuardPolicy.provisional_default()
    state["expected_format_version"] = fmt.FORMAT_CONTRACT_VERSION_EXPERIMENTAL
    state["expected_authority_version"] = fmt.AUTHORITY_SEMANTICS_VERSION_EXPERIMENTAL

    mark_stage("MODULE_IMPORT_END")
    schedule(100, phase_1_admit_g1)


def _prepare(profile_suffix="-c3embedded"):
    cb = state["cb"]
    return cb.prepare_command_boundary(
        LIVE_MASTER_PATH, LIVE_MANIFEST_PATH, LIVE_GENERATIONS_DIR, sufficient_snapshot,
        state["guard"], state["budgets"], state["bounded_provider"], state["bounded_view"],
        state["expected_format_version"], state["expected_authority_version"], profile_suffix,
    )


def phase_1_admit_g1():
    mark_stage("P1_ADMIT_G1_BEGIN")
    owner1, md1 = _prepare()
    lease_n, view_n = owner1.acquire_view("ConsumerN", {u"aaa"}, _PE)
    lease_p, view_p = owner1.acquire_view("ConsumerP", {u"bbb"}, _PE)
    check("1: G1 admitted, fold 'aaa' present", u"aaa" in view_n.payload["folded"])
    check("2: two active leases under G1", owner1.active_lease_count() == 2)
    check("2: one provider allocation for G1", owner1.provider_allocation_count == 1)
    state["owner1"] = owner1
    state["lease_n"] = lease_n
    state["lease_p"] = lease_p
    state["view_n"] = view_n
    mark_stage("P1_ADMIT_G1_END")
    schedule(100, phase_2_source_change_retire)


def phase_2_source_change_retire():
    mark_stage("P2_SOURCE_CHANGE_RETIRE_BEGIN")
    owner1 = state["owner1"]

    # 3: real fixture source SHA changes at this command boundary.
    shutil.copy(os.path.join(FIXTURES, "master_g2.txt"), LIVE_MASTER_PATH)
    shutil.copy(os.path.join(FIXTURES, "manifest_g2.json"), LIVE_MANIFEST_PATH)
    for fn in os.listdir(os.path.join(FIXTURES, "generations")):
        dst = os.path.join(LIVE_GENERATIONS_DIR, fn)
        if not os.path.exists(dst):
            shutil.copy(os.path.join(FIXTURES, "generations", fn), dst)

    owner2, md2 = _prepare()
    check("3: command boundary detects the source change (new owner object)", owner2 is not owner1)
    check("4: old G1 owner is RETIRED", owner1.state == state["so"].STATE_RETIRED)
    check("9: G2 not yet admitted (preparation stays lazy)", owner2.provider is None)

    so = state["so"]
    try:
        owner1.acquire_view("ConsumerNewAfterRetire", {u"aaa"}, _PE)
        check("5: new G1 acquisition refused after retirement", False, "did not raise")
    except so.ResourceRefused as exc:
        check("5: new G1 acquisition refused after retirement", True, repr(exc))

    try:
        envelope = owner1.get_view_via_lease(state["lease_n"])
        check("6: stale (RETIRED, not yet closed) lease payload remains inspectable",
              envelope.view_id == state["view_n"].view_id)
    except so.LeaseRejected as exc:
        check("6: stale (RETIRED, not yet closed) lease payload remains inspectable", False, repr(exc))

    state["owner2"] = owner2
    mark_stage("P2_SOURCE_CHANGE_RETIRE_END")
    schedule(100, phase_3_drain_close)


def phase_3_drain_close():
    mark_stage("P3_DRAIN_CLOSE_BEGIN")
    owner1 = state["owner1"]
    so = state["so"]

    r_n = owner1.release_lease(state["lease_n"])
    check("7: release N -> 'released'", r_n == "released")
    check("7: provider remains alive because P is still active", owner1.provider.is_valid())
    r_close_deferred = owner1.close()
    check("8: close deferred while P still active", r_close_deferred == "deferred-active-leases:1", repr(r_close_deferred))

    r_p = owner1.release_lease(state["lease_p"])
    check("7: release P -> 'released'", r_p == "released")
    r_close = owner1.close()
    check("8: G1 closes once drained", r_close == "closed", repr(r_close))
    check("8: no provider overlap -- exactly one provider allocation across G1's whole lifetime",
          owner1.provider_allocation_count == 1)

    try:
        owner1.get_view_via_lease(state["lease_n"])
        check("11: stale G1 lease rejected once G1 is CLOSED (not merely RETIRED)", False, "did not raise")
    except so.LeaseRejected as exc:
        check("11: stale G1 lease rejected once G1 is CLOSED (not merely RETIRED)", True, repr(exc))

    mark_stage("P3_DRAIN_CLOSE_END")
    schedule(100, phase_4_admit_g2)


def phase_4_admit_g2():
    mark_stage("P4_ADMIT_G2_BEGIN")
    owner2 = state["owner2"]
    lease2, view2 = owner2.acquire_view("ConsumerG2", {u"ccc", u"aaa"}, _PE)
    check("9: G2 admitted only now, on this later explicit step", owner2.provider_allocation_count == 1)
    check("10: G2 changed semantic visible ('ccc' present)", u"ccc" in view2.payload["folded"])
    check("10: old fold 'aaa' correctly absent/proven-negative in G2", u"aaa" not in view2.payload["folded"])
    check("2: G2 receives a new authorization epoch", owner2.epoch >= 1)

    so = state["so"]
    owner1 = state["owner1"]
    try:
        owner1.acquire_view("ConsumerG1AfterG2", {u"ccc"}, _PE)
        check("11: old G1 owner remains rejected after G2 exists", False, "did not raise")
    except so.ResourceRefused as exc:
        check("11: old G1 owner remains rejected after G2 exists", True, repr(exc))

    state["owner2"] = owner2
    state["lease2"] = lease2
    mark_stage("P4_ADMIT_G2_END")
    schedule(100, phase_5_failure_recovery)


def phase_5_failure_recovery():
    mark_stage("P5_FAILURE_RECOVERY_BEGIN")
    so = state["so"]

    backup_path = LIVE_MANIFEST_PATH + ".bak"
    shutil.copy(LIVE_MANIFEST_PATH, backup_path)
    os.remove(LIVE_MANIFEST_PATH)
    try:
        _prepare()
        check("12: missing manifest/pointer refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("12: missing manifest/pointer refused recoverably", True, repr(exc))

    shutil.copy(backup_path, LIVE_MANIFEST_PATH)
    os.remove(backup_path)
    owner_retry, _ = _prepare()
    check("12: later explicit retry after correction succeeds", owner_retry is not None)
    check("12: retry reuses the existing G2 owner (nothing else changed)", owner_retry is state["owner2"])

    mark_stage("P5_FAILURE_RECOVERY_END")
    schedule(100, phase_6_cleanup)


def phase_6_cleanup():
    mark_stage("P6_CLEANUP_BEGIN")
    owner2 = state["owner2"]
    owner2.release_lease(state["lease2"])
    r = owner2.close()
    check("13: final cleanup -- G2 closes cleanly", r == "closed", repr(r))

    mark_stage("P6_CLEANUP_END")
    schedule(100, phase_done)


def phase_done():
    results = {"pass_count": _pass[0], "fail_count": _fail[0]}
    with open(RESULTS_JSON_PATH, "wb") as f:
        f.write(json.dumps(results, indent=2, default=str).encode("utf-8"))
    log(u"Minimum C3 embedded probe RESULT: %d PASS / %d FAIL" % (_pass[0], _fail[0]))
    mark_stage("DONE")
    marker = open(DONE_MARKER_PATH, "wb")
    try:
        marker.write(b"done\n")
    finally:
        marker.close()


if _qt_available:
    schedule(3000, phase_begin)
    log(u"Minimum C3 embedded probe scheduled.")
else:
    log(u"Qt not available -- probe NOT scheduled.")
