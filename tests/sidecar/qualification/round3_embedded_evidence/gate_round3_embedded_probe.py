# -*- coding: utf-8 -*-
# ROUND 3 -- embedded Python 2.7.5 acceptance of the subtractive foundation
# simplification/repair. Real SFM, Qt/main-event thread, event-loop
# scheduling (no long main-thread sleeps). Read-only: never calls
# sfmApp/vs/native Rebuild, never touches Character Preset, never mutates
# the project.

import sys
import os
import time
import json

try:
    unicode
except NameError:
    unicode = str

SCRATCH = r"C:\Users\REDACTED\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\67454949-e69f-4280-93d9-87c1f4464330\scratchpad"
GAME_SCRIPTS = r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts"
DEPLOY = os.path.join(GAME_SCRIPTS, "sfm", "gate_round3_deploy")
OFFICIAL_SIDECAR_PATH = os.path.join(DEPLOY, "official_sidecar.bin")
LARGE_FAMILY_PATH = os.path.join(DEPLOY, "large_family.bin")
SOURCE_SHA256 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
LARGE_FAMILY_SOURCE_SHA256 = "bb385318dca9adacd36f6fbdd568ccccd3af9460ffb51a618e42ec212cac0841"

RESULT_LOG_PATH = SCRATCH + r"\gate_round3_embedded_result.log"
STAGE_LOG_PATH = SCRATCH + r"\gate_round3_embedded_stage_markers.log"
DONE_MARKER_PATH = SCRATCH + r"\gate_round3_embedded_DONE.marker"
RESULTS_JSON_PATH = SCRATCH + r"\gate_round3_embedded_results.json"

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


log(u"Round3 embedded probe loaded, pid=%r sys.version=%r" % (os.getpid(), sys.version))

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


def _ns(so, suffix=""):
    return so.NamespaceIdentity(
        source_path="embedded_round3_master", source_sha256=SOURCE_SHA256,
        artifact_sha256="embedded-round3-artifact", format_version=0, authority_version=0,
        profile_version="normalizer-v1-groupfile-no-backslash" + suffix,
    )


REPO_TOOLS = r"E:\SFM Animation Group Master\tools"


def phase_begin():
    mark_stage("BEGIN")
    if sys.path.count(DEPLOY) == 0:
        sys.path.insert(0, DEPLOY)
    if sys.path.count(os.path.join(DEPLOY, "qualification")) == 0:
        sys.path.insert(0, os.path.join(DEPLOY, "qualification"))
    if sys.path.count(SCRATCH) == 0:
        sys.path.insert(0, SCRATCH)
    if sys.path.count(REPO_TOOLS) == 0:
        sys.path.insert(0, REPO_TOOLS)

    import bounded_provider
    import bounded_view
    import resource_budgets
    import session_owner as so
    import gate_a2_compat_producer as cp
    from sfm_master_sidecar import reader as prod_reader

    state["bounded_provider"] = bounded_provider
    state["bounded_view"] = bounded_view
    state["resource_budgets"] = resource_budgets
    state["so"] = so
    state["cp"] = cp

    check("session_owner has no _EpochCoverage class (Repair F removal is real in this runtime)",
          not hasattr(so, "_EpochCoverage"))

    budgets = so.ViewBudgets.from_qualification_defaults(resource_budgets)
    guard = so.GuardPolicy.provisional_default()
    check("GuardPolicy has no committed-ceiling criterion in this runtime (Repair D removal is real)",
          not hasattr(guard, "min_committed_ceiling_reserve_bytes"))
    state["budgets"] = budgets
    state["guard"] = guard

    prov0 = prod_reader.SidecarReader.open_generation_path(OFFICIAL_SIDECAR_PATH, SOURCE_SHA256)
    wrapper = prov0.wrapper_path()
    occs = list(prov0.iter_occurrences())
    prov0.close()

    def folds_under(prefix):
        s = set()
        full_prefix = wrapper + u"/" + prefix
        for o in occs:
            fp = o["full_path"]
            if fp == full_prefix or fp.startswith(full_prefix + u"/"):
                s.add(cp.ascii_fold_unicode(o["literal"]))
        return s

    state["folds_A"] = folds_under(u"Fingers")
    state["folds_B"] = folds_under(u"RigArms")
    log(u"folds_A=%d folds_B=%d" % (len(state["folds_A"]), len(state["folds_B"])))

    mark_stage("MODULE_IMPORT_END")
    schedule(100, phase_1_init_and_lazy)


def phase_1_init_and_lazy():
    mark_stage("P1_INIT_LAZY_BEGIN")
    so = state["so"]
    so._reset_registry_for_testing()
    ns = _ns(so)
    owner1 = so.get_or_create_owner(ns, OFFICIAL_SIDECAR_PATH, sufficient_snapshot, state["guard"],
                                     state["budgets"], state["bounded_provider"], state["bounded_view"])
    owner2 = so.get_or_create_owner(ns, OFFICIAL_SIDECAR_PATH, sufficient_snapshot, state["guard"],
                                     state["budgets"], state["bounded_provider"], state["bounded_view"])
    owner3 = so.simulate_autoinit_call(ns, OFFICIAL_SIDECAR_PATH, sufficient_snapshot, state["guard"],
                                        state["budgets"], state["bounded_provider"], state["bounded_view"])
    check("1: 3 init call sites -> 1 owner object", owner1 is owner2 is owner3,
          "ids=%r,%r,%r" % (owner1.owner_id, owner2.owner_id, owner3.owner_id))
    check("1: init_call_count == 3", owner1.init_call_count == 3, "count=%d" % owner1.init_call_count)
    check("1: no provider before first acquisition (lazy admission)", owner1.provider is None)

    lease_a, view_a = owner1.acquire_view("ConsumerA", state["folds_A"], _PE)
    check("2: one admitted provider after first acquisition", owner1.provider_allocation_count == 1)

    state["owner"] = owner1
    state["lease_a"] = lease_a
    state["view_a"] = view_a
    state["view_a_id"] = view_a.view_id
    mark_stage("P1_INIT_LAZY_END")
    schedule(100, phase_2_foreign_lease)


def phase_2_foreign_lease():
    mark_stage("P2_FOREIGN_LEASE_BEGIN")
    so = state["so"]
    owner1 = state["owner"]
    ns2 = _ns(so, "-foreign")
    owner2 = so.get_or_create_owner(ns2, OFFICIAL_SIDECAR_PATH, sufficient_snapshot, state["guard"],
                                     state["budgets"], state["bounded_provider"], state["bounded_view"])
    lease_2a, view_2a = owner2.acquire_view("ConsumerForeign", state["folds_B"], _PE)

    try:
        owner2.get_view_via_lease(state["lease_a"])
        check("3: owner1's lease cannot authorize owner2", False, "did not raise")
    except so.LeaseRejected as exc:
        check("3: owner1's lease cannot authorize owner2", True, repr(exc))

    try:
        owner2.release_lease(state["lease_a"])
        check("3: owner1's lease cannot release/mutate owner2's lease", False, "did not raise")
    except so.LeaseRejected as exc:
        check("3: owner1's lease cannot release/mutate owner2's lease", True, repr(exc))

    check("3: owner2's lease remains valid after both foreign attempts",
          owner2.get_view_via_lease(lease_2a).view_id == view_2a.view_id)
    check("3: owner1's own lease still authorizes owner1",
          owner1.get_view_via_lease(state["lease_a"]).view_id == state["view_a_id"])

    state["owner2"] = owner2
    state["lease_2a"] = lease_2a
    mark_stage("P2_FOREIGN_LEASE_END")
    schedule(100, phase_3_release_close_registry)


def phase_3_release_close_registry():
    mark_stage("P3_RELEASE_CLOSE_BEGIN")
    so = state["so"]
    owner2 = state["owner2"]
    lease_2a = state["lease_2a"]

    owner2.release_lease(lease_2a)
    check("4: release removes owner-held record (no tombstone)", lease_2a.lease_id not in owner2._leases)
    leases_before_repeat = len(owner2._leases)
    r_repeat = owner2.release_lease(lease_2a)
    check("4: repeated release is a documented no-op", r_repeat == "already-released-noop")
    check("4: repeated release grows no central history", len(owner2._leases) == leases_before_repeat)

    owner1 = state["owner"]
    lease_a = state["lease_a"]
    lease_b, view_b = owner1.acquire_view("ConsumerB", state["folds_B"], _PE)
    r_deferred = owner1.close()
    check("5: close with active lease is deferred", r_deferred == "deferred-active-leases:2", repr(r_deferred))
    owner1.release_lease(lease_a)
    owner1.release_lease(lease_b)
    r_closed = owner1.close()
    check("6: terminal close succeeds once zero leases remain", r_closed == "closed", repr(r_closed))
    check("6: terminal close removes owner from the process registry",
          so._OWNER_REGISTRY.get(owner1.namespace_identity) is not owner1)

    r2_closed = owner2.close()
    check("6: owner2 terminal close also succeeds/idempotent",
          r2_closed in ("closed", "already-closed-noop"), repr(r2_closed))

    mark_stage("P3_RELEASE_CLOSE_END")
    schedule(100, phase_4_detached_views)


def phase_4_detached_views():
    mark_stage("P4_DETACHED_VIEWS_BEGIN")
    so = state["so"]
    ns = _ns(state["so"], "-detach")
    owner = so.get_or_create_owner(ns, OFFICIAL_SIDECAR_PATH, sufficient_snapshot, state["guard"],
                                    state["budgets"], state["bounded_provider"], state["bounded_view"])
    fold = sorted(state["folds_A"])[0]
    lease_a, view_a = owner.acquire_view("ConsumerDetachA", {fold}, _PE)
    lease_b, view_b = owner.acquire_view("ConsumerDetachB", {fold}, _PE)
    before = sorted([dict(r) for r in view_b.payload["folded"][fold]], key=lambda r: r["global_index"])

    view_a.payload["folded"][fold][0]["literal"] = "MUTATED_BY_EMBEDDED_TEST"
    view_a.payload["folded"][fold].append({"literal": "INJECTED", "destination": "x",
                                            "global_index": -1, "local_index": -1})

    after = sorted([dict(r) for r in view_b.payload["folded"][fold]], key=lambda r: r["global_index"])
    check("7: mutating view A's rows does not affect view B", before == after)

    owner.release_lease(lease_a)
    lease_c, view_c = owner.acquire_view("ConsumerDetachC", {fold}, _PE)
    reacquired = sorted([dict(r) for r in view_c.payload["folded"][fold]], key=lambda r: r["global_index"])
    check("7: reacquiring after mutated A returns authoritative unmutated data", reacquired == before)
    owner.release_lease(lease_b)
    owner.release_lease(lease_c)
    owner.close()

    mark_stage("P4_DETACHED_VIEWS_END")
    schedule(100, phase_5_negative_accounting)


def phase_5_negative_accounting():
    mark_stage("P5_NEG_ACCOUNTING_BEGIN")
    so = state["so"]
    cp = state["cp"]
    ns = _ns(so, "-negacct")
    owner = so.get_or_create_owner(ns, OFFICIAL_SIDECAR_PATH, sufficient_snapshot, state["guard"],
                                    state["budgets"], state["bounded_provider"], state["bounded_view"])
    NEG = cp.ascii_fold_unicode(u"Gate_Round3_Embedded_Neg_Sentinel")
    POS = sorted(state["folds_A"])[0]

    lease_pos, view_pos = owner.acquire_view("ConsumerPosOnly", {POS}, _PE)
    positive_only_bytes = view_pos.accounted_bytes
    owner.release_lease(lease_pos)

    lease_neg, view_neg = owner.acquire_view("ConsumerNegOnly", {NEG}, _PE)
    check("8: negative-only view has nonzero accounted size", view_neg.accounted_bytes > 0,
          "accounted_bytes=%d" % view_neg.accounted_bytes)
    check("8: negative fold correctly represented as proven-negative, not folded",
          NEG in view_neg.payload["proven_negative_folds"] and NEG not in view_neg.payload["folded"])

    lease_mixed, view_mixed = owner.acquire_view("ConsumerMixed", {POS, NEG}, _PE)
    check("8: mixed positive+negative accounting exceeds positive-only accounting",
          view_mixed.accounted_bytes > positive_only_bytes,
          "mixed=%d positive_only=%d" % (view_mixed.accounted_bytes, positive_only_bytes))

    owner.release_lease(lease_neg)
    owner.release_lease(lease_mixed)
    owner.close()

    state["ns_negacct_suffix"] = "-negacct"
    mark_stage("P5_NEG_ACCOUNTING_END")
    schedule(100, phase_6_decode_cache_bound)


def phase_6_decode_cache_bound():
    mark_stage("P6_DECODE_BOUND_BEGIN")
    so = state["so"]
    ns_lf = so.NamespaceIdentity(
        source_path="embedded_round3_large_family", source_sha256=LARGE_FAMILY_SOURCE_SHA256,
        artifact_sha256="embedded-round3-lf-artifact", format_version=0, authority_version=0,
        profile_version="normalizer-v1-groupfile-no-backslash-lfdecodebound",
    )
    strict_budgets = so.ViewBudgets(one_family_result_rows=1, one_snapshot_rows=5000,
                                     total_pinned_bytes=100000000, estimated_bytes_per_row=256,
                                     decode_cache_estimated_bytes_budget=64)
    owner = so.get_or_create_owner(ns_lf, LARGE_FAMILY_PATH, sufficient_snapshot, state["guard"],
                                    strict_budgets, state["bounded_provider"], state["bounded_view"])
    big_fold = state["cp"].ascii_fold_unicode(u"BigFamilyControl")
    try:
        owner.acquire_view("ConsumerRefused", {big_fold}, _PE)
        check("9: over-budget family request refused (setup sanity)", False, "did not raise")
    except so.ResourceRefused:
        check("9: decode cache bound enforced after a refused (over-budget) request",
              owner.provider.string_cache_estimated_bytes() <= strict_budgets.decode_cache_estimated_bytes_budget,
              "estimated=%d" % owner.provider.string_cache_estimated_bytes())
    owner.close()

    mark_stage("P6_DECODE_BOUND_END")
    schedule(100, phase_7_semantic_parity)


def phase_7_semantic_parity():
    mark_stage("P7_SEMANTIC_PARITY_BEGIN")
    so = state["so"]
    bounded_view = state["bounded_view"]
    ns = _ns(so, "-semparity")
    owner = so.get_or_create_owner(ns, OFFICIAL_SIDECAR_PATH, sufficient_snapshot, state["guard"],
                                    state["budgets"], state["bounded_provider"], state["bounded_view"])
    real_pos_fold = sorted(state["folds_A"])[0]
    lease, view = owner.acquire_view("ConsumerSemParity", {real_pos_fold}, _PE)
    check("10: representative positive fold present in folded",
          real_pos_fold in view.payload["folded"] and len(view.payload["folded"][real_pos_fold]) > 0)

    NEG = state["cp"].ascii_fold_unicode(u"Gate_Round3_Embedded_SemParity_Neg")
    lease_neg, view_neg = owner.acquire_view("ConsumerSemParityNeg", {NEG}, _PE)
    check("10: representative negative fold proven absent, never a false positive",
          NEG in view_neg.payload["proven_negative_folds"] and NEG not in view_neg.payload["folded"])

    owner.release_lease(lease)
    owner.release_lease(lease_neg)
    r = owner.close()
    check("11: clean final release/close", r == "closed", repr(r))

    mark_stage("P7_SEMANTIC_PARITY_END")
    schedule(100, phase_done)


def phase_done():
    results = {"pass_count": _pass[0], "fail_count": _fail[0]}
    with open(RESULTS_JSON_PATH, "wb") as f:
        f.write(json.dumps(results, indent=2, default=str).encode("utf-8"))
    log(u"Round3 embedded probe RESULT: %d PASS / %d FAIL" % (_pass[0], _fail[0]))
    mark_stage("DONE")
    marker = open(DONE_MARKER_PATH, "wb")
    try:
        marker.write(b"done\n")
    finally:
        marker.close()


if _qt_available:
    schedule(3000, phase_begin)
    log(u"Round3 embedded probe scheduled.")
else:
    log(u"Qt not available -- probe NOT scheduled.")
