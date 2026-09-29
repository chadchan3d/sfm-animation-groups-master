# -*- coding: utf-8 -*-
"""CPM convergence Step 4 -- offline qualification of Clothing Fit
per-target authority (Gfit) in cpm/app/SFM_Character_Preset_Manager.py.

The real ProdWindow.fit_selected / fit_stage and the real Fit authority
helpers are extracted verbatim and driven one queued Qt turn at a time. The
native Fit planner/mutation (g11a_safe_plan's native mapping, prod_apply_match)
are replaced by recording stubs; the semantic warning query inside planning
is the real p03_unmapped_relevant_controls, fed by the real stage authority.
Lease counts are sampled during planning, mutation, verification and at the
moment the next target is scheduled.

Phases: --phase=publish (Python 3), --phase=suite (Python 2.7.5),
--phase=compare. Offline only: native Fit mutation/Undo is not executed.
"""
import copy
import hashlib
import os
import shutil
import sys
import tempfile

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import test_cpm_app_canonical_route as route  # noqa: E402
import test_cpm_app_operation_context as opctx  # noqa: E402
import test_cpm_authority_adapter as base  # noqa: E402

cpm = route.cpm
adapter_mod = route.adapter_mod
PY2 = route.PY2
_TEXT = route._TEXT
check = route.check
raises = route.raises
_canon = route._canon
RESULTS = route.RESULTS
Timeline = opctx.Timeline

FIXTURE_ROOT = os.path.join(tempfile.gettempdir(), "cpm_app_step4_fixture")
G1_DIR = os.path.join(FIXTURE_ROOT, "g1")
G2_DIR = os.path.join(FIXTURE_ROOT, "g2")
LIVE_DIR = os.path.join(FIXTURE_ROOT, "live")
LIBRARY_DIR = os.path.join(FIXTURE_ROOT, "library")
MASTER_NAME = base.MASTER_NAME
DIGEST_PY3 = os.path.join(FIXTURE_ROOT, "digest_py3.json")
DIGEST_PY27 = os.path.join(FIXTURE_ROOT, "digest_py27.json")

# Point the Step 3 helpers at this suite's own fixture tree.
opctx.G1_DIR, opctx.G2_DIR, opctx.LIVE_DIR, opctx.LIBRARY_DIR = G1_DIR, G2_DIR, LIVE_DIR, LIBRARY_DIR

IDENTITY = dict(route.IDENTITY)

# Target FLEX vocabularies. "Belly" is structurally matched to the source; the
# rest are unmatched and reach the semantic warning query.
TARGETS = {
    u"TargetA": [u"Belly", u"chest", u"Skirt", u"Shirt", u"Tail", u"Ghost", u"WINK"],
    u"TargetB": [u"Belly", u"Hips"],
    u"TargetC": [u"Belly"],
    u"TargetD": [u"Belly", u"Skirt"],   # grows an uncovered literal after its mutation
}
# Hand-audited existing warning rule: unmatched + resolved to exact
# "Body Morphs" or "Clothing" (Shirt -> Clothing/Tops, Tail -> Other, Ghost
# absent, WINK conflict are not warnings).
EXPECTED_WARNINGS = {
    u"TargetA": [(u"Body Morphs", u"chest"), (u"Clothing", u"Skirt")],
    u"TargetB": [(u"Body Morphs", u"Hips")],
    u"TargetC": [],
}


class FitState(object):
    applied = set()
    grown = set()
    samples = []
    plans = []


def _broker():
    return route._broker()


def _leases():
    return _broker().outstanding_lease_count()


_ACQUIRE_EVENTS = ("fully_reused_no_provider_open", "cohort_acquired")


def _diag_mark():
    diags = _broker().recent_diagnostics()
    return diags[-1] if diags else None


def _acquisitions_since(mark):
    """Canonical acquire_or_reuse_views calls recorded by the broker after
    ``mark`` (observations of the Master are not acquisitions)."""
    diags = _broker().recent_diagnostics()
    start = 0
    for i, entry in enumerate(diags):
        if entry is mark:
            start = i + 1
    return len([e for e in diags[start:] if e["event"] in _ACQUIRE_EVENTS])


def _target_bindings(name):
    literals = list(TARGETS[name])
    if name in FitState.grown and name in FitState.applied:
        literals.append(u"Zzz")
    return [{"literal": lit, "shape": u"%s_%s" % (name, lit), "global_key": (name, lit)} for lit in literals]


class _QtCore(object):
    class QObject(object):
        pass

    class QCoreApplication(object):
        @staticmethod
        def instance():
            return None

    class QThread(object):
        @staticmethod
        def currentThread():
            return None

    class QTimer(object):
        scheduled = []

        @classmethod
        def singleShot(cls, delay, callback):
            cls.scheduled.append((delay, callback, _leases()))


def build_namespace(app):
    ns = opctx.build_namespace(app)
    for name in ("prod_body_source", "prod_body_source_live_from_baseline"):
        route._run_source(app.top_text(name), "app:%s" % name, ns)
    ns["QtCore"] = _QtCore
    ns["traceback"] = __import__("traceback")
    ns["p03_verify_baselines"] = lambda accepted, baselines: True
    ns["p03_native_index"] = lambda gm: {"native": u"index"}
    ns["prod_fit_expected_skip_error"] = lambda exc: False
    ns["g11a_resolve_target"] = lambda identity: {"animset": identity["name"], "gm": None, "name": identity["name"]}
    ns["p03_target_bindings"] = _target_bindings
    warn_fn = ns["p03_unmapped_relevant_controls"]

    def safe_plan(source, target_row):
        # Native mapping stub; the semantic warning query is the real one.
        name = target_row["name"]
        target_list = _target_bindings(name)
        mapping = {"mappings": [{"target": {"global_key": b["global_key"]}} for b in target_list if b["literal"] == u"Belly"]}
        provider = source["provider"]
        FitState.plans.append((name, provider, _leases()))
        warnings = warn_fn({"provider": provider}, target_list, mapping)
        return {"identity": {"name": name}, "mapping": mapping, "entries": [], "warnings": warnings,
                "changed_sides": 0 if name in FitState.applied else 1}
    ns["g11a_safe_plan"] = safe_plan

    def apply_match(plan, phase_callback=None, operation_context=None):
        name = plan["identity"]["name"]
        FitState.samples.append(("mutation", name, _leases()))
        Timeline.add("native-write", name)
        FitState.applied.add(name)
        phase_callback(u"native-commit", {"target": name})
        return {"phase": u"committed-verified"}
    ns["prod_apply_match"] = apply_match
    return ns


class FitWindow(route.FakeWindow):
    def __init__(self, scope, selected):
        route.FakeWindow.__init__(self)
        self.identity = dict(IDENTITY)
        self.provider_health = {"status": u"healthy"}
        self.scope = scope
        self.selected = [dict(item) for item in selected]
        self.fit_active = False
        self.fit_generation = 0
        self.closing_requested = False
        self.scene_activity_suspended = False
        self.modal_deferred_fit_stage = None
        self.fit_stage_running = False
        self.status = []
        self.ended = []
        self.finished = []

        class Button(object):
            def setEnabled(self, value):
                pass
        self.fit_button = Button()

    def fit_checked_identities(self):
        return [dict(item) for item in self.selected]

    def operation_begin(self, label, pin_context=False):
        self.operation = {"operation_id": 1, "context": u"token", "label": label}
        return True

    def operation_end(self, label):
        self.operation = None
        self.ended.append(label)

    def operation_revalidate(self):
        Timeline.add("scene-revalidate")

    def operation_mark_phase(self, *a, **k):
        pass

    def set_status(self, text, kind=None):
        self.status.append(text)

    def fit_set_enabled(self, value):
        pass

    def fit_clear_checks(self):
        pass

    def fit_show_partial_failure(self):
        pass

    def current(self):
        return dict(self.identity)

    def fit_finish(self, generation):
        self.finished.append(generation)
        self.fit_active = False
        self.operation_end("Clothing Fit")


def install_window_methods(ns, app):
    methods = {}
    for name in ("fit_selected", "fit_stage", "prod_cpm_request_stale_rebuild_if_needed",
                 "prod_cpm_run_stale_rebuild", "semantic_provider_ready"):
        route._run_source(app.method_text("ProdWindow", name), "app:ProdWindow.%s" % name, ns, methods)
    for name, fn in methods.items():
        setattr(FitWindow, name, fn)

    def select_model(self, index):
        self.select_calls.append(index)
        adapter, health = ns["prod_probe_semantic_provider"](self.identity)
        self.provider_health = health
        self.scope = ns["prod_scope"](self.identity, adapter) if health["status"] == u"healthy" else None
    FitWindow.select_model = select_model


def _reset():
    FitState.applied = set()
    FitState.grown = set()
    FitState.samples = []
    FitState.plans = []
    _QtCore.QTimer.scheduled = []
    Timeline.reset()


def _run_next(win):
    """Run the next queued zero-delay Fit turn; returns the lease count
    sampled when it was scheduled."""
    for i, (delay, callback, leases) in enumerate(_QtCore.QTimer.scheduled):
        if delay == 0:
            del _QtCore.QTimer.scheduled[i]
            callback()
            return leases
    return None


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _targets(*names):
    return [{"name": n, "model": u"models/%s.mdl" % n} for n in names]


def _no_outstanding(label):
    b = _broker()
    check("idle.%s.no_outstanding_lease" % label, b.outstanding_lease_count() == 0)
    check("idle.%s.no_open_provider" % label, b.provider_counters()["current_open_provider_count"] == 0)


# ---------------------------------------------------------------------------
# Adapter stage unit behavior
# ---------------------------------------------------------------------------

def section_stage_unit(ns):
    shim = route._shim_adapter_module()
    adapter = shim.open_canonical_authority(os.path.join(LIVE_DIR, MASTER_NAME))
    sha1 = _sha(os.path.join(G1_DIR, MASTER_NAME))
    stage = adapter.open_stage(sha1, [u"Belly", u"Skirt"])
    check("stage.lease_held_while_open", _leases() == 1 and not stage.is_released())
    check("stage.generation", stage.generation == sha1)
    answers = stage.query_many([u"Skirt"])
    check("stage.covered_query_answers", answers[u"Skirt"]["resolved_path"] == u"Clothing")
    before = _broker().provider_counters()["total_provider_opens"]
    raises("stage.uncovered_fails_closed", (adapter_mod.CpmAuthorityUnavailable,), lambda: stage.query_many([u"Tail"]))
    check("stage.uncovered_no_new_acquisition", _broker().provider_counters()["total_provider_opens"] == before)
    check("stage.release_ok", stage.release() is None and stage.is_released() and _leases() == 0)
    check("stage.release_clears_refs", stage._view is None and stage._lease is None and stage._broker is None)
    raises("stage.released_query_fails_closed", (adapter_mod.CpmAuthorityUnavailable,), lambda: stage.query_many([u"Skirt"]))
    check("stage.release_idempotent", stage.release() is None)
    raises("stage.wrong_generation_refused", (adapter_mod.CpmGenerationMismatch,), lambda: adapter.open_stage(u"a" * 64, [u"Belly"]))
    check("stage.refused_holds_no_lease", _leases() == 0)
    stage2 = adapter.open_stage(sha1, [u"Belly"])
    stage2._view.authorization.invalidate()
    raises("stage.revoked_authorization_fails_closed", (adapter_mod.CpmAuthorityUnavailable,), lambda: stage2.query_many([u"Belly"]))
    stage2.release()
    _no_outstanding("stage_unit")


# ---------------------------------------------------------------------------
# One Fit under G1
# ---------------------------------------------------------------------------

def section_fit_g1(ns, app):
    install_window_methods(ns, app)
    _reset()
    sha1 = _sha(os.path.join(G1_DIR, MASTER_NAME))
    scope = ns["prod_scope"](IDENTITY)
    win = FitWindow(scope, _targets(u"TargetA", u"TargetB", u"TargetC"))
    Timeline.reset()
    win.fit_selected()
    check("fit.started", win.fit_active and win.fit_generation == 1)
    check("fit.gfit_is_generation_sha", win.fit_semantic_generation == sha1)
    check("fit.gfit_distinct_from_callback_generation", isinstance(win.fit_generation, int)
          and win.fit_semantic_generation != win.fit_generation)
    check("fit.start_authorized_once", Timeline.kinds().count("authority-open") == 1)
    check("fit.no_lease_after_start", _leases() == 0)

    vocab = ns["prod_cpm_fit_stage_vocabulary"](win.fit_authority_context, {"animset": u"TargetA"})
    source_literals = set(win.fit_authority_context["membership"]["descriptors"].keys())
    check("fit.vocabulary_is_source_plus_target", set(vocab) == source_literals | set(TARGETS[u"TargetA"]), vocab)
    target_only = set(cpm.cpm_fold(l) for l in TARGETS[u"TargetA"]) - set(cpm.cpm_fold(l) for l in source_literals)
    check("fit.target_only_folds_present", target_only >= set([u"skirt", u"shirt", u"tail", u"ghost", u"wink"]), sorted(target_only))

    schedule_leases = []
    for i in range(3):
        opens_before = Timeline.kinds().count("authority-open")
        leases_at_schedule = _run_next(win)
        schedule_leases.append(leases_at_schedule)
        check("fit.stage%d.one_authority_open" % i, Timeline.kinds().count("authority-open") == opens_before + 1)
    _run_next(win)  # the turn after the last target -> fit_finish
    check("fit.no_lease_when_any_next_target_scheduled",
          all(n == 0 for n in schedule_leases) and all(s[2] == 0 for s in _QtCore.QTimer.scheduled), schedule_leases)
    plans_by_target = {}
    for name, provider, leases in FitState.plans:
        plans_by_target.setdefault(name, []).append((provider, leases))
    for name in (u"TargetA", u"TargetB", u"TargetC"):
        entries = plans_by_target.get(name, [])
        check("fit.%s.planning_and_verify_same_stage" % name, len(entries) == 2 and entries[0][0] is entries[1][0]
              and type(entries[0][0]).__name__ == "CpmStageAuthority")
        check("fit.%s.stage_pinned_to_gfit" % name, entries and entries[0][0].generation == sha1)
        check("fit.%s.lease_held_through_planning_and_verify" % name, [e[1] for e in entries] == [1, 1])
        check("fit.%s.stage_released_after_verify" % name, entries and entries[0][0].is_released())
    check("fit.lease_held_through_mutation", [s[2] for s in FitState.samples] == [1, 1, 1])
    check("fit.writes_one_per_target", [e[1] for e in Timeline.events if e[0] == "native-write"] ==
          [u"TargetA", u"TargetB", u"TargetC"])
    check("fit.finished", win.finished == [1] and not win.fit_active and win.ended == ["Clothing Fit"])
    check("fit.accounting", [p["identity"]["name"] for p in win.fit_partial] == [u"TargetA", u"TargetB"]
          and [c["name"] for c in win.fit_changed] == [u"TargetC"] and win.fit_failed == [] and win.fit_unattempted == [])
    check("fit.context_cleared_after_finish", win.fit_authority_context is None and win.fit_semantic_generation is None)
    check("fit.no_historical_provider", route.Env.forbidden_calls == [], route.Env.forbidden_calls)
    _no_outstanding("fit_g1")
    return win


def section_warning_equivalence(ns):
    """The real warning rule, fed by the stage authority vs. by the
    Step 2a-qualified bounded adapter query, gives identical rows, and both
    match the hand audit (exact Body Morphs / Clothing only)."""
    sha1 = _sha(os.path.join(G1_DIR, MASTER_NAME))
    shim = route._shim_adapter_module()
    warn_fn = ns["p03_unmapped_relevant_controls"]
    for name, expected in sorted(EXPECTED_WARNINGS.items()):
        target_list = _target_bindings(name)
        mapping = {"mappings": [{"target": {"global_key": b["global_key"]}} for b in target_list if b["literal"] == u"Belly"]}
        stage = shim.open_canonical_authority(os.path.join(LIVE_DIR, MASTER_NAME)).open_stage(
            sha1, [b["literal"] for b in target_list])
        via_stage = warn_fn({"provider": stage}, target_list, mapping)
        stage.release()
        via_adapter = warn_fn({"provider": shim.open_canonical_authority(os.path.join(LIVE_DIR, MASTER_NAME))},
                              target_list, mapping)
        check("warning.%s.stage_equals_bounded_adapter" % name, _canon(via_stage) == _canon(via_adapter))
        check("warning.%s.hand_audit" % name, [(r["master_path"], r["literal"]) for r in via_stage] == expected,
              _canon(via_stage))
    _no_outstanding("warning")


# ---------------------------------------------------------------------------
# Generation change between targets
# ---------------------------------------------------------------------------

def section_generation_change(ns, app):
    install_window_methods(ns, app)
    _reset()
    sha2 = _sha(os.path.join(G2_DIR, MASTER_NAME))
    scope = ns["prod_scope"](IDENTITY)
    win = FitWindow(scope, _targets(u"TargetA", u"TargetB", u"TargetC"))
    win.fit_selected()
    _run_next(win)  # target 1 (TargetA) commits and verifies under G1
    check("gchange.target1_committed", [c["name"] for c in win.fit_committed_order] == [u"TargetA"] and _leases() == 0)
    base._copy_dir_files(G2_DIR, LIVE_DIR)
    try:
        writes_before = len([e for e in Timeline.events if e[0] == "native-write"])
        _run_next(win)  # target 2 attempts expected_generation=G1
        writes = [e[1] for e in Timeline.events if e[0] == "native-write"]
        check("gchange.target2_zero_writes", len(writes) == writes_before and u"TargetB" not in writes, writes)
        check("gchange.target1_still_committed", [c["name"] for c in win.fit_committed_order] == [u"TargetA"]
              and [p["identity"]["name"] for p in win.fit_partial] == [u"TargetA"])
        check("gchange.remaining_unattempted", [u["name"] for u in win.fit_unattempted] == [u"TargetB", u"TargetC"],
              _canon(win.fit_unattempted))
        check("gchange.target2_not_reported_failed", win.fit_failed == [], _canon(win.fit_failed))
        check("gchange.fit_terminated", not win.fit_active and win.ended == ["Clothing Fit"] and win.finished == [])
        check("gchange.existing_status_copy", win.status[-1] == "Clothing Fit stopped after changing 1 item.", win.status)
        check("gchange.no_lease_left", _leases() == 0)
        stage_calls = [d for d, c, l in _QtCore.QTimer.scheduled if d == 0]
        check("gchange.rebuild_scheduled_not_next_target", len(stage_calls) == 1)
        _run_next(win)  # the scheduled current-authority scope rebuild
        check("gchange.scope_rebuilt_under_g2", win.scope["authority"]["provider_sha256"] == sha2)
        check("gchange.old_fit_not_resumed", u"TargetB" not in [e[1] for e in Timeline.events if e[0] == "native-write"]
              and not [s for s in _QtCore.QTimer.scheduled if s[0] == 0])
        # A later, new user Fit runs under G2.
        win.selected = _targets(u"TargetC")
        FitState.applied = set()
        win.ended = []
        win.fit_selected()
        check("gchange.new_fit_under_g2", win.fit_semantic_generation == sha2 and win.fit_generation == 2)
        _run_next(win)
        _run_next(win)
        check("gchange.new_fit_completes", win.finished == [2] and [c["name"] for c in win.fit_changed] == [u"TargetC"])
    finally:
        base._copy_dir_files(G1_DIR, LIVE_DIR)
    check("gchange.no_historical_provider", route.Env.forbidden_calls == [], route.Env.forbidden_calls)
    _no_outstanding("gchange")


# ---------------------------------------------------------------------------
# Post-stage Uncovered, foreign modal, callback cancellation
# ---------------------------------------------------------------------------

def section_post_stage_uncovered(ns, app):
    install_window_methods(ns, app)
    _reset()
    FitState.grown = set([u"TargetD"])
    win = FitWindow(ns["prod_scope"](IDENTITY), _targets(u"TargetD", u"TargetC"))
    win.fit_selected()
    mark = _diag_mark()
    providers_before = _broker().provider_counters()["total_provider_opens"]
    _run_next(win)
    check("uncovered.single_stage_acquisition", _acquisitions_since(mark) == 1)
    check("uncovered.no_implicit_acquisition", _broker().provider_counters()["total_provider_opens"] <= providers_before + 1)
    check("uncovered.fails_closed_after_commit", len(win.fit_failed) == 1 and win.fit_failed[0]["committed"] is True
          and win.fit_failed[0]["verification"] == u"uncertain" and "outside this stage" in win.fit_failed[0]["reason"],
          _canon(win.fit_failed))
    check("uncovered.remaining_unattempted", [u["name"] for u in win.fit_unattempted] == [u"TargetC"])
    check("uncovered.lease_released", _leases() == 0)
    _no_outstanding("uncovered")


def section_modal_and_cancel(ns, app):
    install_window_methods(ns, app)
    _reset()
    win = FitWindow(ns["prod_scope"](IDENTITY), _targets(u"TargetC"))
    win.fit_selected()
    opens_before = Timeline.kinds().count("authority-open")
    win.scene_activity_suspended = True
    _run_next(win)
    check("modal.deferred_without_authority", win.modal_deferred_fit_stage == (1, 0)
          and Timeline.kinds().count("authority-open") == opens_before and _leases() == 0)
    win.scene_activity_suspended = False
    base._copy_dir_files(G2_DIR, LIVE_DIR)
    try:
        generation, index = win.modal_deferred_fit_stage
        mark = _diag_mark()
        win.fit_stage(generation, index)  # resume after the foreign modal ends
        check("modal.proof_at_resume_boundary", _acquisitions_since(mark) == 0
              and Timeline.kinds().count("authority-open") >= opens_before + 1)
        check("modal.generation_change_during_modal_stops_before_write",
              "native-write" not in Timeline.kinds() and [u["name"] for u in win.fit_unattempted] == [u"TargetC"])
    finally:
        base._copy_dir_files(G1_DIR, LIVE_DIR)
    _no_outstanding("modal")

    _reset()
    win2 = FitWindow(ns["prod_scope"](IDENTITY), _targets(u"TargetC"))
    win2.fit_selected()
    opens_before = Timeline.kinds().count("authority-open")
    win2.fit_stage(win2.fit_generation - 1, 0)  # stale callback-cancellation identity
    check("cancel.stale_callback_generation_ignored", Timeline.kinds().count("authority-open") == opens_before
          and "native-write" not in Timeline.kinds())
    _no_outstanding("cancel")


def section_r6(ns):
    scope = ns["prod_scope"](IDENTITY)
    live = ns["prod_live_bindings_for_cached_scope"](IDENTITY, scope, u"body")
    raises("r6.unexpected_caller_without_stage_still_refused", (ns["ProdCpmAuthorityNotMigrated"],),
           lambda: live["provider"].query_many([u"Belly"]))


def _section(name, fn, *args):
    try:
        result = fn(*args)
        check("section.%s.completed" % name, True)
        return result
    except Exception as exc:
        check("section.%s.completed" % name, False, "%s: %s" % (type(exc).__name__, exc))
        base._copy_dir_files(G1_DIR, LIVE_DIR)
        return None


def run_suite():
    app = route.AppSource(route.APP_PATH)
    ns = build_namespace(app)
    _section("stage_unit", section_stage_unit, ns)
    _section("fit_g1", section_fit_g1, ns, app)
    _section("warning_equivalence", section_warning_equivalence, ns)
    _section("generation_change", section_generation_change, ns, app)
    _section("post_stage_uncovered", section_post_stage_uncovered, ns, app)
    _section("modal_and_cancel", section_modal_and_cancel, ns, app)
    _section("r6", section_r6, ns)
    check("suite.no_historical_provider_anywhere", route.Env.forbidden_calls == [], route.Env.forbidden_calls)
    _no_outstanding("suite_end")


def phase_publish():
    if os.path.isdir(FIXTURE_ROOT):
        shutil.rmtree(FIXTURE_ROOT)
    os.makedirs(FIXTURE_ROOT)
    os.makedirs(LIBRARY_DIR)
    from sfm_master_sidecar import publisher
    for directory, body in ((G1_DIR, base.MASTER_G1), (G2_DIR, base.MASTER_G2)):
        result = publisher.publish(base._write_master(directory, body), directory)
        check("publish.%s" % os.path.basename(directory), os.path.isfile(str(result.generation_path)))
    base._copy_dir_files(G1_DIR, LIVE_DIR)
    if not all(r[1] for r in RESULTS):
        print("RESULT: setup failed")
        sys.exit(1)
    del RESULTS[:]
    run_suite()
    route.write_digest(DIGEST_PY3)


def phase_suite():
    if not (os.path.isfile(os.path.join(LIVE_DIR, MASTER_NAME)) and os.path.isfile(DIGEST_PY3)):
        print("RESULT: fixtures missing; run --phase=publish first")
        sys.exit(1)
    run_suite()
    route.write_digest(DIGEST_PY27 if PY2 else DIGEST_PY3 + ".rerun")


def phase_compare():
    route.DIGEST_PY3, route.DIGEST_PY27 = DIGEST_PY3, DIGEST_PY27
    route.phase_compare()


if __name__ == "__main__":
    phase = None
    for arg in sys.argv[1:]:
        if arg.startswith("--phase="):
            phase = arg.split("=", 1)[1]
    if phase not in ("publish", "suite", "compare"):
        print("usage: %s --phase=publish|suite|compare" % os.path.basename(sys.argv[0]))
        sys.exit(2)
    print("Interpreter: %s" % sys.version.split()[0])
    print("Phase: %s" % phase)
    {"publish": phase_publish, "suite": phase_suite, "compare": phase_compare}[phase]()
    passed = sum(1 for r in RESULTS if r[1])
    print("\nRESULT: %d/%d %s" % (passed, len(RESULTS), "ALL PASS" if passed == len(RESULTS) else "SOME FAILED"))
    if passed != len(RESULTS):
        sys.exit(1)
