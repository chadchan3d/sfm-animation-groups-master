# -*- coding: utf-8 -*-
"""CPM convergence -- consolidated offline qualification of Blueprint
section 20 Suite 2 (callback ownership) and gates C7 (AuthorityUnavailable
boundary), C8 (lease lifecycle / no-idle-lease), C9 (expected-generation
reauthorization) and C10 (canonical package/broker identity).

Each named requirement is exercised here directly against the current
application source (extracted verbatim, as in the Step 2b-4 suites), the CPM
adapter/projection modules, and the real canonical broker; earlier suites
are reused for helpers only. Every check name is prefixed with its gate.

Phases: --phase=publish (Python 3), --phase=suite (Python 2.7.5),
--phase=compare. Offline only: nothing here demonstrates native SFM
transaction/Undo behavior or real-SFM coexistence.
"""
import ast
import hashlib
import io
import os
import shutil
import sys
import tempfile

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import test_cpm_app_canonical_route as route  # noqa: E402
import test_cpm_app_operation_context as opctx  # noqa: E402
import test_cpm_app_clothing_fit as fit  # noqa: E402
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

FIXTURE_ROOT = os.path.join(tempfile.gettempdir(), "cpm_convergence_gates_fixture")
G1_DIR = os.path.join(FIXTURE_ROOT, "g1")
G2_DIR = os.path.join(FIXTURE_ROOT, "g2")
LIVE_DIR = os.path.join(FIXTURE_ROOT, "live")
CORRUPT_DIR = os.path.join(FIXTURE_ROOT, "corrupt")
EMPTY_DIR = os.path.join(FIXTURE_ROOT, "no_sidecar")
STALE_DIR = os.path.join(FIXTURE_ROOT, "stale")
LIBRARY_DIR = os.path.join(FIXTURE_ROOT, "library")
MASTER_NAME = base.MASTER_NAME
DIGEST_PY3 = os.path.join(FIXTURE_ROOT, "digest_py3.json")
DIGEST_PY27 = os.path.join(FIXTURE_ROOT, "digest_py27.json")

for _mod in (opctx, fit):
    _mod.G1_DIR, _mod.G2_DIR, _mod.LIVE_DIR, _mod.LIBRARY_DIR = G1_DIR, G2_DIR, LIVE_DIR, LIBRARY_DIR

# G2 for the gates: G1 + "Thigh" (Body Morphs) and "Ghost" placed in two
# groups. Both are genuine misses under G1; under G2 Thigh positively resolves
# and Ghost is a conflict.
MASTER_G2 = base.MASTER_G2.replace(
    u'\t\t\t"control"\t\t"Smile"\n', u'\t\t\t"control"\t\t"Smile"\n\t\t\t"control"\t\t"Ghost"\n').replace(
    u'\t\t"control"\t\t"Thigh"\n', u'\t\t"control"\t\t"Thigh"\n\t\t"control"\t\t"ghost"\n')
IDENTITY = dict(route.IDENTITY)
PROFILE = os.path.join(LIBRARY_DIR, "character.json")


def _broker():
    return route._broker()


def _leases():
    return _broker().outstanding_lease_count()


def _counters():
    return _broker().provider_counters()


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _swap(directory):
    base._copy_dir_files(directory, LIVE_DIR)


def _baseline(gate, label):
    check("%s.%s.leases_at_baseline" % (gate, label), _leases() == 0)
    check("%s.%s.no_open_provider" % (gate, label), _counters()["current_open_provider_count"] == 0)


def _plain_types(value, found):
    if isinstance(value, dict):
        for k, v in value.items():
            _plain_types(k, found)
            _plain_types(v, found)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for v in value:
            _plain_types(v, found)
    else:
        found.add(type(value).__name__)
    return found


_PLAIN = set(["NoneType", "bool", "int", "long", "float", "str", "unicode", "bytes"])


class LeaseSpy(object):
    """Broker proxy counting lease/release calls (real broker underneath)."""

    def __init__(self, real):
        self._real = real
        self.leased = 0
        self.released = 0

    def lease_view(self, view):
        self.leased += 1
        return self._real.lease_view(view)

    def release_view_lease(self, lease):
        self.released += 1
        return self._real.release_view_lease(lease)

    def __getattr__(self, name):
        return getattr(self._real, name)


# ---------------------------------------------------------------------------
# Suite 2 -- callback ownership
# ---------------------------------------------------------------------------

def section_suite2(ns, app):
    from sfm_master_authority_productionized import cohort as cohort_mod, views
    sha1 = _sha(os.path.join(G1_DIR, MASTER_NAME))
    literals = [u"Blink", u"bLiNk", u"Wink", u"Ghost", u"Skirt"]
    folds = cpm.request_folds_for_literals(literals)
    record = {}
    real_specs = cpm.make_request_specs
    real_init = cohort_mod.Cohort.__init__

    def spying_specs(requested, consumer_kind=cpm.CONSUMER_KIND):
        specs = real_specs(requested, consumer_kind)
        kind, (declared_folds, builder) = list(specs.items())[0]

        def seam(provider):
            record["provider_type"] = type(provider).__name__
            record["open_during_callback"] = _counters()["current_open_provider_count"]
            record["builder_declared"] = frozenset(builder.declared_request_folds)
            record["builder_scale"] = builder.declared_request_scale
            record["spec_folds"] = frozenset(declared_folds)
            return builder(provider)
        seam.declared_request_folds = builder.declared_request_folds
        seam.declared_request_scale = builder.declared_request_scale
        return {kind: (declared_folds, seam)}

    def spying_init(self, *args, **kwargs):
        real_init(self, *args, **kwargs)
        record["admission_folds"] = dict(self.requested_folds_by_consumer or {})

    adapter_mod.cpm.make_request_specs = spying_specs
    cohort_mod.Cohort.__init__ = spying_init
    try:
        adapter = route._shim_adapter_module().open_canonical_authority(os.path.join(LIVE_DIR, MASTER_NAME))
        opens_before = _counters()["total_provider_opens"]
        answers = adapter.query_many(literals)
    finally:
        adapter_mod.cpm.make_request_specs = real_specs
        cohort_mod.Cohort.__init__ = real_init
    view = _broker().cached_view((sha1, None, folds, cpm.CONSUMER_KIND))
    check("suite2.broker_invokes_cpm_builder_via_seam", record.get("provider_type") == "CandidatePackedProvider"
          or record.get("provider_type", "").endswith("Provider"), record.get("provider_type"))
    check("suite2.declared_requested_covered_agree", record.get("builder_declared") == folds == record.get("spec_folds")
          and view is not None and view.coverage.covered_keys() == folds)
    # Blink and bLiNk share one fold: 5 literals, 4 folds.
    check("suite2.request_scale_accurate", record.get("builder_scale") == len(folds) == 4)
    check("suite2.admission_receives_real_vocabulary",
          frozenset(record.get("admission_folds", {}).get(cpm.CONSUMER_KIND, ())) == folds, _canon(sorted(record.get("admission_folds", {}).get(cpm.CONSUMER_KIND, ()))))
    check("suite2.provider_open_during_callback_only", record.get("open_during_callback") == 1
          and _counters()["current_open_provider_count"] == 0
          and _counters()["total_provider_opens"] == _counters()["total_provider_closes"]
          and _counters()["total_provider_opens"] == opens_before + 1)
    payload_types = _plain_types(view.payload, set())
    coverage_types = set()
    for key in view.coverage.covered_keys():
        entry = view.coverage.lookup(key)
        _plain_types([entry.status, entry.destination, entry.occurrences], coverage_types)
    check("suite2.payload_plain_data_only", payload_types <= _PLAIN, None if payload_types <= _PLAIN else sorted(payload_types))
    check("suite2.coverage_compact_plain", coverage_types <= _PLAIN, None if coverage_types <= _PLAIN else sorted(coverage_types))
    walk_payload = cpm._walk(view.payload)
    check("suite2.estimated_bytes_covers_payload_coverage_envelope",
          view.estimated_bytes == cpm.estimate_retained_bytes(view.payload, view.coverage)
          and view.estimated_bytes > walk_payload + sum(cpm._walk(k) for k in view.coverage.covered_keys()))
    check("suite2.bounded_read_retains_nothing", route._state_is_detached(adapter) if hasattr(route, "_state_is_detached")
          else base._state_is_detached(adapter))
    check("suite2.bounded_read_no_lease", _leases() == 0)
    check("suite2.answers_complete", sorted(answers.keys()) == sorted(literals))

    # Unsupported result types / partial results never publish.
    b = _broker()
    entries_before = b.view_cache_entry_count()
    real_builder = cpm.build_cpm_compat_v1_projection(frozenset([u"blink", u"tail"]))

    class _Surprise(object):
        pass

    def poisoned(provider):
        class _Proxy(object):
            def wrapper_path(self):
                return provider.wrapper_path()

            def lookup_fold(self, query):
                return _Surprise() if query == b"tail" else provider.lookup_fold(query)
        return real_builder(_Proxy())
    poisoned.declared_request_folds = real_builder.declared_request_folds
    poisoned.declared_request_scale = real_builder.declared_request_scale
    raises("suite2.unsupported_result_fails_closed", (cpm.CpmProjectionError,), lambda: b.acquire_or_reuse_views(
        os.path.join(LIVE_DIR, MASTER_NAME), {"cpm_gate_poison": (frozenset([u"blink", u"tail"]), poisoned)},
        shipped_root=LIVE_DIR, expected_generation=sha1))
    check("suite2.partial_result_not_published", b.view_cache_entry_count() == entries_before
          and b.cached_view((sha1, None, frozenset([u"blink", u"tail"]), "cpm_gate_poison")) is None)
    check("suite2.provider_closed_after_failed_callback", _counters()["current_open_provider_count"] == 0)

    def omitting(provider):
        payload, coverage, est = cpm.build_cpm_compat_v1_projection(frozenset([u"blink"]))(provider)
        return payload, coverage, est
    omitting.declared_request_folds = frozenset([u"blink", u"tail"])
    omitting.declared_request_scale = 2
    # A (non-CPM) builder that omits declared coverage is still published by
    # the broker under its own covered key; CPM view validation rejects it.
    omitted = b.acquire_or_reuse_views(os.path.join(LIVE_DIR, MASTER_NAME),
                                       {"cpm_gate_omit": (frozenset([u"blink", u"tail"]), omitting)},
                                       shipped_root=LIVE_DIR, expected_generation=sha1)["cpm_gate_omit"]
    raises("suite2.omitted_coverage_view_rejected_by_cpm", (cpm.CpmProjectionError,),
           lambda: cpm.validate_view(omitted, frozenset([u"blink", u"tail"]), "cpm_gate_omit"))
    raises("suite2.real_cpm_builder_cannot_omit", (cpm.CpmProjectionError,), lambda: cpm.build_cpm_compat_v1_projection(
        frozenset([u"blink", u"tail"]))(_OmittingProvider()))
    dropping = route.base._ProxyBroker(_broker(), acquire_or_reuse_views=lambda mp, specs, **kw: _broker().acquire_or_reuse_views(
        mp, {cpm.CONSUMER_KIND: (frozenset([u"blink"]), cpm.build_cpm_compat_v1_projection(frozenset([u"blink"])))}, **kw))
    exc = raises("suite2.missing_coverage_fails_closed", (adapter_mod.CpmAuthorityUnavailable,),
                 lambda: route._make_adapter(LIVE_DIR, dropping).query_many([u"Blink", u"Tail"]) if hasattr(route, "_make_adapter")
                 else base._make_adapter(LIVE_DIR, dropping).query_many([u"Blink", u"Tail"]))
    check("suite2.uncovered_never_absent", exc is not None and exc.reason == u"projection-invalid")
    raises("suite2.interpreter_uncovered_raises", (cpm.CpmProjectionError,),
           lambda: cpm.interpret_exact_answer(u"Tail", {"contract": cpm.PAYLOAD_CONTRACT, "families_by_fold": {}}))

    # Held stage: the explicit exception to "retain nothing".
    stage = adapter.open_stage(sha1, [u"Belly", u"Skirt"])
    check("suite2.stage_holds_exactly_one_lease", _leases() == 1 and stage._view is not None and stage._lease is not None)
    check("suite2.stage_view_is_detached_view", type(stage._view).__name__ == "DetachedView")
    mark = fit._diag_mark()
    raises("suite2.stage_uncovered_fails_closed", (adapter_mod.CpmAuthorityUnavailable,), lambda: stage.query_many([u"Tail"]))
    check("suite2.stage_uncovered_no_acquisition", fit._acquisitions_since(mark) == 0)
    stage.release()
    check("suite2.stage_release_clears_refs", stage._view is None and stage._lease is None and _leases() == 0)

    # No production CPM route opens authority outside the broker.
    provider_openers = set(["candidate_packed_provider_r3a2b", "candidate_packed_provider", "selection", "sidecar_contract",
                            "publisher", "reader", "compiler", "BoundedProvider", "open_path", "lookup_fold"])
    for name in ("cpm_authority_adapter.py", "cpm_compat_v1_projection.py"):
        with open(os.path.join(route.MODULE_DIR, name), "rb") as f:
            tree = ast.parse(f.read())
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                used.update(a.name for a in node.names)
                if isinstance(node, ast.ImportFrom) and node.module:
                    used.update(node.module.split("."))
            elif isinstance(node, ast.Attribute) and node.attr in ("open_path", "BoundedProvider"):
                used.add(node.attr)
        bad = used & provider_openers
        check("suite2.%s_opens_no_provider_directly" % name, not bad, sorted(bad))
    check("suite2.app_reachability_excludes_historical_provider",
          _reachability_ok(app))
    _baseline("suite2", "end")


class _OmittingProvider(object):
    """Claims every requested fold is unknown except it answers nothing for
    'tail' -- the CPM builder's own completeness check must refuse."""
    def wrapper_path(self):
        return u"groupFile"

    def lookup_fold(self, query):
        if query == b"tail":
            return object()
        return type("MasterUnknown", (object,), {})()


def _reachability_ok(app):
    before = len(RESULTS)
    route.section_reachability(app)
    ours = RESULTS[before:]
    del RESULTS[before:]
    return all(ok for _, ok, _ in ours)


# ---------------------------------------------------------------------------
# C7 -- AuthorityUnavailable boundary
# ---------------------------------------------------------------------------

def _set_failure(kind):
    """Configure one controlled failure; returns an undo callable."""
    from sfm_master_authority_productionized import runtime
    if kind == "no_valid_authority":
        route.Env.live_root = EMPTY_DIR
        return lambda: setattr(route.Env, "live_root", LIVE_DIR)
    if kind == "stale_sidecar":
        route.Env.live_root = STALE_DIR
        return lambda: setattr(route.Env, "live_root", LIVE_DIR)
    if kind == "runtime_build_rejected":
        old = runtime.RUNTIME_BUILD_ID
        runtime.RUNTIME_BUILD_ID = "other-build"
        return lambda: setattr(runtime, "RUNTIME_BUILD_ID", old)
    if kind == "adapter_contract_failure":
        def wrong(real):
            def acquire(master_path, specs, **kwargs):
                (kind_, (folds, _)), = list(specs.items())
                narrowed = frozenset(list(folds)[:1])
                return real.acquire_or_reuse_views(master_path, {kind_: (narrowed, cpm.build_cpm_compat_v1_projection(narrowed))}, **kwargs)
            return route.base._ProxyBroker(real, acquire_or_reuse_views=acquire)
        route.Env.broker_wrapper = [wrong]
        return lambda: setattr(route.Env, "broker_wrapper", [])
    if kind == "expected_generation_rejected":
        _swap(G2_DIR)
        return lambda: _swap(G1_DIR)
    raise AssertionError(kind)


C7_FAILURES = ("no_valid_authority", "stale_sidecar", "expected_generation_rejected",
               "runtime_build_rejected", "adapter_contract_failure")


def section_c7(ns, app):
    fit.install_window_methods(ns, app)
    opctx.win_methods(ns, app)
    for kind in C7_FAILURES:
        opctx.Store.files.pop(PROFILE, None)
        scope_g1 = ns["prod_scope"](IDENTITY)
        undo = _set_failure(kind)
        writes_before = [e for e in Timeline.events if e[0] in ("durable-write", "native-write")]
        try:
            Timeline.reset()
            # Scope build / render health (not meaningful for an expected-generation pin).
            if kind != "expected_generation_rejected":
                adapter, health = ns["prod_probe_semantic_provider"](IDENTITY)
                check("c7.%s.health_unavailable_no_scope" % kind, adapter is None and health["status"] == u"unavailable",
                      _canon([health["status"], health["reason"]]))
                raises("c7.%s.scope_build_fails_not_absent" % kind, (Exception,), lambda: ns["prod_scope"](IDENTITY))
            # Operation authorization (Save/Update/Apply/Review/Fit start all begin here).
            raises("c7.%s.authorization_refused" % kind, (Exception,),
                   lambda: ns["prod_cpm_authorize_operation"](IDENTITY, scope_g1, u"expression", u"gate"))
            raises("c7.%s.save_refused" % kind, (Exception,), lambda: ns["prod_save"](
                IDENTITY, u"expression", u"Gate", scope=scope_g1, operation_context=u"token"))
            item = {"source": u"v3", "path": _existing_preset(), "record": {
                "schema_version": 3, "record_kind": u"preset", "preset_id": u"p", "kind": u"expression", "name": u"x", "values": {}}}
            raises("c7.%s.update_refused" % kind, (Exception,), lambda: ns["prod_update_preset"](
                IDENTITY, item, scope=scope_g1, operation_context=u"token"))
            review = opctx.ReviewWindow(ns, u"Ghost", u"miss")
            review.identity = dict(IDENTITY)
            review.provider_health = {"status": u"healthy"}
            review.scope = scope_g1
            review.review_decision(u"body")
            check("c7.%s.review_refused" % kind, hasattr(review, "error"))
            # Held-stage path (Fit target).
            win = fit.FitWindow(scope_g1, fit._targets(u"TargetC"))
            fit.FitState.applied = set()
            fit._QtCore.QTimer.scheduled = []
            win.fit_selected()
            if win.fit_active:
                fit._run_next(win)
            check("c7.%s.fit_no_target_write" % kind, "native-write" not in Timeline.kinds() and not win.fit_active)
            check("c7.%s.no_semantic_write_or_mutation" % kind,
                  not [e for e in Timeline.events if e[0] in ("durable-write", "native-write")], Timeline.kinds())
            check("c7.%s.no_review_population_written" % kind, u"Ghost" not in (
                (opctx.Store.files.get(PROFILE) or {}).get("semantic_overrides") or {}))
            check("c7.%s.no_historical_fallback" % kind, route.Env.forbidden_calls == [], route.Env.forbidden_calls)
        finally:
            undo()
        _baseline("c7", kind)
    # Healthy absence stays distinct from every failure above.
    scope = ns["prod_scope"](IDENTITY)
    check("c7.healthy_absence_is_miss", u"Ghost" in scope["unresolved"] and u"Wink" not in scope["unresolved"])


def _existing_preset():
    path = os.path.join(LIBRARY_DIR, "expression_existing.json")
    if not os.path.isfile(path):
        with open(path, "wb") as f:
            f.write(b"{}")
    return path


# ---------------------------------------------------------------------------
# C8 -- lease lifecycle / no-idle-lease
# ---------------------------------------------------------------------------

def section_c8(ns, app):
    opctx.Store.files.pop(PROFILE, None)
    spy = []

    def wrap(real):
        s = LeaseSpy(real)
        spy.append(s)
        return s
    route.Env.broker_wrapper = [wrap]
    try:
        _baseline("c8", "idle_before")
        scope = ns["prod_scope"](IDENTITY)
        leased = sum(s.leased for s in spy)
        released = sum(s.released for s in spy)
        check("c8.scope_build_short_leases", leased >= 1 and leased == released and _leases() == 0, [leased, released])
        types_found = _plain_types(scope, set())
        check("c8.pure_scope_survives_release", types_found <= _PLAIN and scope["semantic"]["rows"]
              and ns["prod_scope_pure_assert"](scope) is True)
        _baseline("c8", "ui_idle_after_scope")
        del spy[:]
        ctx = ns["prod_cpm_authorize_operation"](IDENTITY, scope, u"expression", u"gate")
        check("c8.reauthorization_another_short_lease", sum(s.leased for s in spy) == 1 == sum(s.released for s in spy)
              and _leases() == 0)
        check("c8.context_holds_no_lease", _plain_types(ctx, set()) <= _PLAIN)
    finally:
        route.Env.broker_wrapper = []

    # Durable writes happen with zero leases held (Save/Update/Review release boundary).
    samples = []
    real_write = ns["p02_safe_write_json"]

    def sampling_write(path, record):
        samples.append(_leases())
        return real_write(path, record)
    ns["p02_safe_write_json"] = sampling_write
    try:
        ns["prod_save"](IDENTITY, u"body", u"Gate Body", scope=scope, operation_context=u"token")
        ns["prod_update_preset"](IDENTITY, {"source": u"v3", "path": _existing_preset(), "record": {
            "schema_version": 3, "record_kind": u"preset", "preset_id": u"p", "kind": u"expression", "name": u"x",
            "values": {}}}, scope=scope, operation_context=u"token")
        opctx.win_methods(ns, app)
        review = opctx.ReviewWindow(ns, u"Ghost", u"miss")
        review.identity = dict(IDENTITY)
        review.provider_health = {"status": u"healthy"}
        review.scope = ns["prod_scope"](IDENTITY)
        review.review_decision(u"expression")
    finally:
        ns["p02_safe_write_json"] = real_write
    check("c8.durable_writes_hold_no_lease", samples and all(n == 0 for n in samples), samples)
    _baseline("c8", "after_save_update_review")

    # Apply late verification holds no lease. (The Review write above changed
    # the saved override revision, so the earlier scope is legitimately stale.)
    scope = ns["prod_scope"](IDENTITY)
    ctx = ns["prod_cpm_authorize_operation"](IDENTITY, scope, u"expression", u"Apply Preset")
    live = ns["prod_live_bindings_for_cached_scope"](IDENTITY, scope, u"expression", authority_context=ctx)
    check("c8.apply_late_verification_no_lease", live["accepted"] is not None and _leases() == 0)

    # Fit: exactly one stage lease per target, released before the next turn.
    fit.install_window_methods(ns, app)
    fit.FitState.applied = set()
    fit.FitState.plans = []
    fit.FitState.samples = []
    fit._QtCore.QTimer.scheduled = []
    win = fit.FitWindow(ns["prod_scope"](IDENTITY), fit._targets(u"TargetA", u"TargetC"))
    win.fit_selected()
    at_schedule = [fit._run_next(win), fit._run_next(win)]
    fit._run_next(win)
    check("c8.fit_stage_holds_exactly_one_lease", [s[2] for s in fit.FitState.samples] == [1, 1]
          and all(p[2] == 1 for p in fit.FitState.plans))
    check("c8.fit_releases_before_next_turn", at_schedule == [0, 0], at_schedule)
    _baseline("c8", "after_fit")

    # Failure and stale paths return to baseline.
    _swap(G2_DIR)
    try:
        raises("c8.stale_path_rejects", (RuntimeError,), lambda: ns["prod_cpm_authorize_operation"](IDENTITY, scope, None, u"gate"))
    finally:
        _swap(G1_DIR)
    _baseline("c8", "after_stale")
    fit.FitState.grown = set([u"TargetD"])
    fit._QtCore.QTimer.scheduled = []
    win = fit.FitWindow(ns["prod_scope"](IDENTITY), fit._targets(u"TargetD"))
    win.fit_selected()
    fit._run_next(win)
    fit.FitState.grown = set()
    check("c8.stage_uncovered_failure_recorded", len(win.fit_failed) == 1)
    _baseline("c8", "after_stage_uncovered")

    # Release failure uses the broker's durable registry (bounded read and stage).
    real = _broker()

    def failing_release(lease):
        raise RuntimeError("gate: release failure")
    before = real.unreleased_lease_count()
    proxy = route.base._ProxyBroker(real, release_view_lease=failing_release)
    adapter = adapter_mod.CpmAuthorityAdapter(proxy, os.path.join(LIVE_DIR, MASTER_NAME), LIVE_DIR)
    raises("c8.bounded_release_failure_fails_closed", (adapter_mod.CpmAuthorityUnavailable,), lambda: adapter.query_many([u"Blink"]))
    check("c8.bounded_release_failure_registered", real.unreleased_lease_count() == before + 1)
    stage = adapter.open_stage(_sha(os.path.join(G1_DIR, MASTER_NAME)), [u"Belly"])
    raises("c8.stage_release_failure_stops_fit", (ns["ProdCpmFitStop"],), lambda: ns["prod_cpm_release_fit_stage"](stage, 0))
    check("c8.stage_release_failure_registered", real.unreleased_lease_count() == before + 2)
    real.retry_unreleased_leases()
    check("c8.registry_reconciled", real.unreleased_lease_count() == before)
    _baseline("c8", "end")


# ---------------------------------------------------------------------------
# C9 -- expected-generation reauthorization
# ---------------------------------------------------------------------------

def section_c9(ns, app):
    sha1 = _sha(os.path.join(G1_DIR, MASTER_NAME))
    sha2 = _sha(os.path.join(G2_DIR, MASTER_NAME))
    # Local Review decisions made under G1 for two genuine G1 misses.
    opctx.Store.files[PROFILE] = {"schema_version": 3, "record_kind": u"character", "semantic_overrides": {
        u"Thigh": {"source": u"user", "applies_when": u"master-miss", "decision": u"expression", "created_at": u"x"},
        u"Ghost": {"source": u"user", "applies_when": u"master-miss", "decision": u"body", "created_at": u"x"}},
        "semantic_override_revision": 2, "model_ref": {}}
    scope = ns["prod_scope"](IDENTITY)
    check("c9.1_g1_scope_built", scope["authority"]["provider_sha256"] == sha1
          and u"Thigh" in scope["expression"] and u"Ghost" in scope["body"])
    ctx = ns["prod_cpm_authorize_operation"](IDENTITY, scope, u"expression", u"gate")
    check("c9.2_unchanged_g1_authorizes", ctx["master_sha256"] == sha1)
    fit.install_window_methods(ns, app)
    win = fit.FitWindow(scope, fit._targets(u"TargetC"))
    route._QtStub.QTimer.scheduled = []
    fit._QtCore.QTimer.scheduled = []
    _swap(G2_DIR)
    try:
        check("c9.3_g2_current", _sha(os.path.join(LIVE_DIR, MASTER_NAME)) == sha2)
        exc = raises("c9.4_stale_g1_rejected", (RuntimeError,),
                     lambda: ns["prod_cpm_authorize_operation"](IDENTITY, scope, u"expression", u"gate"))
        Timeline.reset()
        raises("c9.5_old_save_rejected", (RuntimeError,), lambda: ns["prod_save"](
            IDENTITY, u"expression", u"Old", scope=scope, operation_context=u"token"))
        check("c9.5_old_action_zero_writes", "durable-write" not in Timeline.kinds() and "native-write" not in Timeline.kinds())
        check("c9.6_rebuild_scheduled_for_stale_scope", win.prod_cpm_request_stale_rebuild_if_needed() is True)
        delay, callback, _ = fit._QtCore.QTimer.scheduled[0]
        callback()
        check("c9.6_stale_scope_discarded", win.select_calls == [3])
        check("c9.7_g2_scope_rebuilt", win.scope["authority"]["provider_sha256"] == sha2)
        check("c9.8_no_replay", "durable-write" not in Timeline.kinds())
        g2 = win.scope
        rows = dict((r["literal"], r) for r in g2["semantic"]["rows"])
        check("c9.9_g2_positive_overrides_local_review", rows[u"Thigh"]["semantic_class"] == u"body-morphs"
              and u"Thigh" not in g2["overrides"] and u"Thigh" not in g2["expression"] and u"Thigh" in g2["body"])
        check("c9.9_g2_conflict_overrides_local_review", rows[u"Ghost"]["semantic_status"] == u"conflict"
              and u"Ghost" in g2["conflicts"] and u"Ghost" not in g2["overrides"] and u"Ghost" not in g2["body"])
        path = ns["prod_save"](IDENTITY, u"expression", u"New", scope=g2, operation_context=u"token")
        check("c9.10_new_action_under_g2_proceeds", opctx.Store.files[path]["capture_provider"]["source_sha256"] == sha2)
    finally:
        _swap(G1_DIR)
        opctx.Store.files.pop(PROFILE, None)
    _baseline("c9", "end")


# ---------------------------------------------------------------------------
# C10 -- canonical package/broker identity
# ---------------------------------------------------------------------------

def section_c10(app):
    from sfm_master_authority_productionized import runtime, bootstrap
    broker, identity = adapter_mod.canonical_bootstrap(route.PACKAGE_PARENT, lambda: True)
    check("c10.resolves_qualified_package", os.path.normcase(os.path.dirname(os.path.abspath(runtime.__file__)))
          == os.path.normcase(os.path.join(route.PACKAGE_PARENT, "sfm_master_authority_productionized")))
    try:
        runtime.assert_expected_origin(os.path.join(route.PACKAGE_PARENT, "sfm_master_authority_productionized"))
        origin_ok = True
    except Exception:
        origin_ok = False
    check("c10.expected_origin_matches", origin_ok)
    check("c10.api_identity", identity["runtime_api_version"] == u"1.0.0-b2a")
    check("c10.build_identity", identity["runtime_build_id"] == u"package-boundary-corrected-2026-09-22")
    check("c10.runtime_module_canonical", runtime.is_canonical() and sys.modules[adapter_mod.RUNTIME_MODULE_NAME] is runtime)
    check("c10.broker_via_get_broker_singleton", broker is runtime.get_broker() and broker is runtime.get_broker())
    raises("c10.wrong_origin_refused", (adapter_mod.CpmAuthorityUnavailable,),
           lambda: adapter_mod.canonical_bootstrap(os.path.join(FIXTURE_ROOT, "elsewhere"), lambda: True))
    before = len(RESULTS)
    route.section_import(app)
    ours = RESULTS[before:]
    del RESULTS[before:]
    check("c10.cpm_same_name_shadow_refused", all(ok for _, ok, _ in ours), [n for n, ok, _ in ours if not ok])
    before = len(RESULTS)
    base.section_bootstrap()
    ours = RESULTS[before:]
    del RESULTS[before:]
    check("c10.bootstrap_formula_equals_normalizer_and_failures_closed", all(ok for _, ok, _ in ours),
          [n for n, ok, _ in ours if not ok])
    # Static: the production Normalizer and CPM both obtain the broker only
    # through the canonical runtime module's get_broker.
    with open(route.base.NORMALIZER_PATH, "rb") as f:
        norm = f.read().decode("utf-8")
    check("c10.normalizer_pinned", hashlib.sha256(norm.encode("utf-8")).hexdigest() == route.base.NORMALIZER_SHA256)
    check("c10.normalizer_uses_canonical_get_broker",
          u"from sfm_master_authority_productionized import runtime as authority_runtime" in norm
          and u"authority_runtime.get_broker(" in norm and u"Broker(" not in norm.replace(u"get_broker(", u""))
    with open(os.path.join(route.MODULE_DIR, "cpm_authority_adapter.py"), "rb") as f:
        adp = f.read().decode("utf-8")
    check("c10.cpm_uses_canonical_get_broker", u"runtime.get_broker(" in adp and u"Broker(" not in adp.replace(u"get_broker(", u""))
    # Not a check: the production Normalizer cannot run offline without
    # substituting its SFM/Qt module-level imports, which would replace the
    # decisive ownership path. Recorded as pending, never as PASS.
    print("NOTE c10.same_process_broker_with_real_normalizer: PENDING real-SFM coexistence proof")


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------

def _section(name, fn, *args):
    try:
        fn(*args)
        check("section.%s.completed" % name, True)
    except Exception as exc:
        check("section.%s.completed" % name, False, "%s: %s" % (type(exc).__name__, exc))
        route.Env.live_root = LIVE_DIR
        route.Env.broker_wrapper = []
        _swap(G1_DIR)


def run_suite():
    app = route.AppSource(route.APP_PATH)
    ns = fit.build_namespace(app)
    _section("suite2", section_suite2, ns, app)
    _section("c7", section_c7, ns, app)
    _section("c8", section_c8, ns, app)
    _section("c9", section_c9, ns, app)
    _section("c10", section_c10, app)
    check("suite.no_historical_provider_anywhere", route.Env.forbidden_calls == [], route.Env.forbidden_calls)
    _baseline("suite", "end")


def phase_publish():
    if os.path.isdir(FIXTURE_ROOT):
        shutil.rmtree(FIXTURE_ROOT)
    os.makedirs(FIXTURE_ROOT)
    os.makedirs(LIBRARY_DIR)
    os.makedirs(EMPTY_DIR)
    from sfm_master_sidecar import publisher
    for directory, body in ((G1_DIR, base.MASTER_G1), (G2_DIR, MASTER_G2)):
        result = publisher.publish(base._write_master(directory, body), directory)
        check("publish.%s" % os.path.basename(directory), os.path.isfile(str(result.generation_path)))
    base._copy_dir_files(G1_DIR, LIVE_DIR)
    # Its own Master generation with no published sidecar (a G1-identical
    # Master would legitimately be served from the broker's G1 cache).
    with open(os.path.join(EMPTY_DIR, MASTER_NAME), "wb") as f:
        f.write(base.MASTER_G1.replace(u'\t\t"control"\t\t"Hips"\n', u'\t\t"control"\t\t"Hips"\n\t\t"control"\t\t"NoSidecarOnly"\n').encode("utf-8"))
    base._copy_dir_files(G1_DIR, STALE_DIR)
    shutil.copyfile(os.path.join(G2_DIR, MASTER_NAME), os.path.join(STALE_DIR, MASTER_NAME))
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
