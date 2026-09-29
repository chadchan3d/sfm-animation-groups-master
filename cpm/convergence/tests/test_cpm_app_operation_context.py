# -*- coding: utf-8 -*-
"""CPM convergence Step 3 -- offline qualification of the CPM Operation
Authority Context in the application source
(cpm/app/SFM_Character_Preset_Manager.py).

Same technique as the Step 2b suite (whose helpers this reuses): production
functions and ProdWindow methods are extracted verbatim by name and run in a
namespace whose stubs cover only SFM/Qt/DME boundaries and library I/O. The
authority path is real (canonical broker + CPM adapter + published
sidecars). Authority opens and durable writes are instrumented on one event
timeline so ordering can be asserted.

Phases: --phase=publish (Python 3), --phase=suite (Python 2.7.5),
--phase=compare. Offline only; no real-SFM claim.
"""
import copy
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import types

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import test_cpm_app_canonical_route as route  # noqa: E402
import test_cpm_authority_adapter as base  # noqa: E402

cpm = route.cpm
adapter_mod = route.adapter_mod
PY2 = route.PY2
_TEXT = route._TEXT

FIXTURE_ROOT = os.path.join(tempfile.gettempdir(), "cpm_app_step3_fixture")
G1_DIR = os.path.join(FIXTURE_ROOT, "g1")
G2_DIR = os.path.join(FIXTURE_ROOT, "g2")
LIVE_DIR = os.path.join(FIXTURE_ROOT, "live")
LIBRARY_DIR = os.path.join(FIXTURE_ROOT, "library")
MASTER_NAME = base.MASTER_NAME
DIGEST_PY3 = os.path.join(FIXTURE_ROOT, "digest_py3.json")
DIGEST_PY27 = os.path.join(FIXTURE_ROOT, "digest_py27.json")

RESULTS = route.RESULTS
check = route.check
raises = route.raises
_canon = route._canon

# G1 live vocabulary plus "Thigh", a miss under G1 that G2 resolves to Body Morphs.
BINDINGS = route._bindings_from_pairs(list(base.LIVE_BINDINGS) + [(u"Thigh", u"thigh")])
IDENTITY = dict(route.IDENTITY)

STEP3_EXTRACT = [
    "PROD_CPM_OPERATION_CONTEXT_SCHEMA", "PROD_CPM_STALE_SCOPE_MESSAGE", "ProdCpmOperationAuthorityError",
    "prod_cpm_pure_scalar_types", "PROD_CPM_PURE_SCALARS", "prod_cpm_detached",
    "prod_cpm_context_matches_identity", "prod_cpm_reclassify_outcome", "prod_cpm_authorize_operation",
    "prod_save", "prod_update_preset", "prod_set_override", "prod_clear_override",
    "prod_verify_apply_abort_baseline", "prod_abort_apply_and_verify",
]


class Timeline(object):
    events = []

    @classmethod
    def add(cls, *event):
        cls.events.append(event)

    @classmethod
    def kinds(cls):
        return [e[0] for e in cls.events]

    @classmethod
    def reset(cls):
        cls.events = []


class Store(object):
    files = {}


class _Recovery(RuntimeError):
    pass


def build_namespace(app):
    route.Env.live_root = LIVE_DIR
    route.Env.bindings = BINDINGS
    ns = route.build_namespace(app)
    for name in STEP3_EXTRACT:
        route._run_source(app.top_text(name), "app:%s" % name, ns)

    real_open = ns["prod_cpm_open_adapter"]

    def instrumented_open():
        Timeline.add("authority-open")
        return real_open()
    ns["prod_cpm_open_adapter"] = instrumented_open

    def write_json(path, record):
        Timeline.add("durable-write", os.path.basename(path))
        Store.files[path] = copy.deepcopy(record)
    ns["p02_safe_write_json"] = write_json
    ns["p02_read_json"] = lambda path: copy.deepcopy(Store.files[path])
    ns["prod_paths"] = lambda identity: {"profile": os.path.join(LIBRARY_DIR, "character.json")}
    ns["prod_load_character"] = lambda identity: copy.deepcopy(
        Store.files.get(os.path.join(LIBRARY_DIR, "character.json")))
    import time as _time
    ns["time"] = _time
    ns["prod_resource_snapshot"] = lambda *a, **k: None
    ns["prod_action_timing"] = lambda *a, **k: None
    ns["prod_discover"] = lambda identity, kind: []
    ns["prod_assert_unique_preset_name_items"] = lambda items, kind, name: None
    ns["p03_capture_values"] = lambda accepted: (dict((k, 0.25) for k in accepted), None)
    ns["prod_capture_body_snapshot"] = lambda identity, accepted, operation_context=None: {
        "values": dict((k, 0.5) for k in accepted), "bone_scales": [], "existing_scaled": [],
        "expected_bone_keys": []}
    ns["uuid"] = types.ModuleType("uuid_stub")
    ns["uuid"].uuid4 = lambda: types.SimpleNamespace(hex="0" * 32) if not PY2 else _Hex()
    ns["prod_validate_preset"] = lambda identity, record, kind: None
    ns["prod_validate_bone_scale_map_against_keys"] = lambda a, b: None
    ns["prod_validate_context_token"] = lambda token: True
    ns["prod_unique_path"] = lambda identity, kind, name, pid: os.path.join(LIBRARY_DIR, "%s_preset.json" % kind)
    ns["PROD_Q1_INDEXED_CAPTURE_PARITY"] = False
    ns["prod_reread_selected_record"] = lambda identity, item, kind: copy.deepcopy(item["record"])
    ns["prod_preset_dir"] = lambda identity, kind: LIBRARY_DIR
    ns["p03_verify_baselines"] = lambda accepted, baselines: sorted(accepted.keys()) == sorted(baselines)
    ns["same_time_refresh"] = lambda *a, **k: Timeline.add("scene-refresh")

    class _SfmApp(object):
        @staticmethod
        def GetHeadTimeInSeconds():
            return 0.0
    ns["sfmApp"] = _SfmApp
    ns["ProdRecoveryUnverifiedError"] = _Recovery
    return ns


class _Hex(object):
    hex = "0" * 32


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _broker():
    return route._broker()


def _no_outstanding(label):
    b = _broker()
    check("idle.%s.no_outstanding_lease" % label, b.outstanding_lease_count() == 0)
    check("idle.%s.no_open_provider" % label, b.provider_counters()["current_open_provider_count"] == 0)


def _swap(directory):
    base._copy_dir_files(directory, LIVE_DIR)


def _fresh_scope(ns):
    return ns["prod_scope"](IDENTITY)


def _authority_opens():
    return Timeline.kinds().count("authority-open")


def _first_index(kind):
    kinds = Timeline.kinds()
    return kinds.index(kind) if kind in kinds else None


def _last_index(kind):
    kinds = Timeline.kinds()
    return len(kinds) - 1 - kinds[::-1].index(kind) if kind in kinds else None


# ---------------------------------------------------------------------------
# Context shape and purity
# ---------------------------------------------------------------------------

def _walk_types(value, found):
    if isinstance(value, dict):
        for k, v in value.items():
            _walk_types(k, found)
            _walk_types(v, found)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _walk_types(v, found)
    else:
        found.add(type(value).__name__)
    return found


def section_context(ns):
    sha1 = _sha(os.path.join(G1_DIR, MASTER_NAME))
    scope = _fresh_scope(ns)
    Timeline.reset()
    ctx = ns["prod_cpm_authorize_operation"](IDENTITY, scope, u"expression", u"Save Preset")
    check("context.one_authority_open", _authority_opens() == 1)
    check("context.keys", sorted(ctx.keys()) == sorted([
        "schema", "operation", "identity", "master_sha256", "compatibility_identity", "provider_capture",
        "runtime", "consumer_kind", "projection_contract", "semantic_policy_revision", "scope_authority",
        "live_signature", "membership", "persistence"]), sorted(ctx.keys()))
    check("context.generation", ctx["master_sha256"] == sha1 and ctx["scope_authority"]["provider_sha256"] == sha1)
    check("context.compatibility_identity", ctx["compatibility_identity"] == [
        u"cpm-compat-identity-v1", sha1, u"cpm_compat_v1", u"master-category-operation-scope-v1"])
    check("context.provenance", ctx["runtime"] == {"api_version": u"1.0.0-b2a",
                                                    "build_id": u"package-boundary-corrected-2026-09-22"}
          and ctx["consumer_kind"] == u"cpm_compat_v1" and ctx["projection_contract"] == u"cpm-compat-v1")
    check("context.membership", ctx["membership"]["kind"] == u"expression"
          and sorted(ctx["membership"]["descriptors"].keys()) == sorted(scope["expression"].keys()))
    check("context.persistence_capture_is_g18an_shape", ctx["persistence"]["last_validated_provider"] == {
        "provider_contract": u"sfm-character-semantic-provider-v1", "source_sha256": sha1,
        "fold_policy": u"ascii-a-z-v1", "provider_generation": 1}, _canon(ctx["persistence"]))
    allowed = set(["NoneType", "bool", "int", "long", "float", "str", "unicode", "bytes"])
    types_found = _walk_types(ctx, set())
    # Type names differ by interpreter (Python 2 str/unicode); record the verdict only.
    check("context.plain_data_only", types_found <= allowed, None if types_found <= allowed else sorted(types_found))
    ctx["membership"]["descriptors"].clear()
    check("context.detached_from_scope", len(scope["expression"]) > 0)
    for label, value in (("object", object()), ("generator", (x for x in [1])), ("closure", lambda: None),
                         ("adapter", _shim_adapter())):
        raises("context.refuses_%s" % label, (ns["ProdCpmOperationAuthorityError"],),
               lambda v=value: ns["prod_cpm_detached"]({"x": [v]}))
    review_ctx = ns["prod_cpm_authorize_operation"](IDENTITY, scope, None, u"Review Flex")
    check("context.review_has_no_membership", review_ctx["membership"] is None)
    _no_outstanding("context")
    return scope


def _shim_adapter():
    return route._shim_adapter_module().open_canonical_authority(os.path.join(LIVE_DIR, MASTER_NAME))


# ---------------------------------------------------------------------------
# Save / Update
# ---------------------------------------------------------------------------

def section_save(ns):
    Store.files.clear()
    for kind in (u"expression", u"body"):
        scope = _fresh_scope(ns)
        Timeline.reset()
        Timeline.add("prompt-returned")
        path = ns["prod_save"](IDENTITY, kind, u"Fixture %s" % kind, scope=scope, operation_context=u"token")
        kinds = Timeline.kinds()
        check("save.%s.succeeds_no_r6_refusal" % kind, path == os.path.join(LIBRARY_DIR, "%s_preset.json" % kind))
        check("save.%s.authorized_after_prompt" % kind, _first_index("authority-open") > _first_index("prompt-returned"))
        check("save.%s.authorized_before_first_write" % kind,
              _first_index("authority-open") < _first_index("durable-write"))
        check("save.%s.no_authority_after_first_write" % kind,
              _last_index("authority-open") < _first_index("durable-write"), kinds)
        check("save.%s.single_authorization" % kind, _authority_opens() == 1, kinds)
        profile = Store.files[os.path.join(LIBRARY_DIR, "character.json")]
        check("save.%s.character_capture_from_context" % kind, profile["last_validated_provider"] == {
            "provider_contract": u"sfm-character-semantic-provider-v1", "source_sha256": scope["authority"]["provider_sha256"],
            "fold_policy": u"ascii-a-z-v1", "provider_generation": 1})
        record = Store.files[path]
        check("save.%s.preset_capture_unchanged" % kind,
              record["capture_provider"] == ns["prod_provider_capture"](scope["provider_descriptor"])
              and record["capture_semantic_policy"] == ns["PROD_SEMANTIC_POLICY"])
        check("save.%s.membership" % kind, sorted(record["values"].keys()) == sorted(scope[kind].keys()))
    check("save.no_historical_provider", route.Env.forbidden_calls == [], route.Env.forbidden_calls)
    _no_outstanding("save")


def section_update(ns):
    scope = _fresh_scope(ns)
    path = os.path.join(LIBRARY_DIR, "expression_existing.json")
    if not os.path.isdir(LIBRARY_DIR):
        os.makedirs(LIBRARY_DIR)
    with open(path, "wb") as f:
        f.write(b"{}")
    record = {"schema_version": 3, "record_kind": u"preset", "preset_id": u"preset-existing", "kind": u"expression",
              "name": u"Existing", "values": {}}
    item = {"source": u"v3", "path": path, "record": record}
    Timeline.reset()
    Timeline.add("prompt-returned")
    result = ns["prod_update_preset"](IDENTITY, item, scope=scope, operation_context=u"token")
    check("update.succeeds_not_fail_closed", result == path)
    check("update.authorized_after_prompt_before_write",
          _first_index("prompt-returned") < _first_index("authority-open") < _first_index("durable-write"))
    check("update.no_authority_after_write", _last_index("authority-open") < _first_index("durable-write"))
    check("update.single_authorization", _authority_opens() == 1)
    written = Store.files[path]
    check("update.capture_unchanged", written["capture_provider"] == ns["prod_provider_capture"](scope["provider_descriptor"]))
    check("update.membership", sorted(written["values"].keys()) == sorted(scope["expression"].keys()))
    _no_outstanding("update")
    return item


def section_prompt_generation_change(ns, app, item):
    """G1 -> G2 while the Save/Update prompt is open: rejected before any
    durable write, stale scope rebuilt once, action not replayed."""
    for label in ("save", "update"):
        scope = _fresh_scope(ns)
        win = route.FakeWindow()
        win.identity = dict(IDENTITY)
        win.provider_health = {"status": u"healthy"}
        win.scope = scope
        check("prompt.%s.pre_prompt_check_passes" % label, ns["prod_scope_matches_identity"](scope, IDENTITY) is True)
        Timeline.reset()
        route._QtStub.QTimer.scheduled = []
        _swap(G2_DIR)
        try:
            Timeline.add("prompt-returned")
            if label == "save":
                fn = lambda: ns["prod_save"](IDENTITY, u"expression", u"Stale", scope=scope, operation_context=u"token")
            else:
                fn = lambda: ns["prod_update_preset"](IDENTITY, item, scope=scope, operation_context=u"token")
            exc = raises("prompt.%s.rejected" % label, (RuntimeError,), fn)
            check("prompt.%s.stale_error" % label, exc is not None and "stale" in _TEXT(exc))
            check("prompt.%s.no_durable_write" % label, "durable-write" not in Timeline.kinds(), Timeline.kinds())
            win_methods(ns, app)
            check("prompt.%s.rebuild_scheduled" % label, win.prod_cpm_request_stale_rebuild_if_needed() is True
                  and len(route._QtStub.QTimer.scheduled) == 1)
            win.select_calls = []
            route._QtStub.QTimer.scheduled[0][1]()
            check("prompt.%s.rebuilt_current" % label, win.scope["authority"]["provider_sha256"] == _sha(os.path.join(G2_DIR, MASTER_NAME)))
            check("prompt.%s.no_replay" % label, "durable-write" not in Timeline.kinds() and win.select_calls == [3])
        finally:
            _swap(G1_DIR)
    _no_outstanding("prompt")


def win_methods(ns, app):
    methods = {}
    for name in ("prod_cpm_request_stale_rebuild_if_needed", "prod_cpm_run_stale_rebuild", "semantic_provider_ready",
                 "review_decision", "review_reclassify"):
        route._run_source(app.method_text("ProdWindow", name), "app:ProdWindow.%s" % name, ns, methods)
    for name, fn in methods.items():
        setattr(route.FakeWindow, name, fn)

    def select_model(self, index):
        self.select_calls.append(index)
        adapter, health = ns["prod_probe_semantic_provider"](self.identity)
        self.provider_health = health
        self.scope = ns["prod_scope"](self.identity, adapter) if health["status"] == u"healthy" else None
    route.FakeWindow.select_model = select_model


# ---------------------------------------------------------------------------
# Apply: postcommit and abort verification use the pinned context
# ---------------------------------------------------------------------------

def section_apply(ns, app):
    scope = _fresh_scope(ns)
    ctx = ns["prod_cpm_authorize_operation"](IDENTITY, scope, u"expression", u"Apply Preset")
    built = {"baselines": sorted(scope["expression"].keys())}
    _swap(G2_DIR)
    try:
        Timeline.reset()
        live = ns["prod_live_bindings_for_cached_scope"](IDENTITY, scope, u"expression", authority_context=ctx)
        check("apply.postcommit_readback_under_g2_uses_pinned_membership",
              sorted(live["accepted"].keys()) == sorted(ctx["membership"]["descriptors"].keys()))
        check("apply.postcommit_readback_no_authority_open", _authority_opens() == 0, Timeline.kinds())
        restored = ns["prod_verify_apply_abort_baseline"](IDENTITY, u"expression", scope, built, None, authority_context=ctx)
        check("apply.abort_verify_under_g2_pinned", restored is True and _authority_opens() == 0)

        class _Dm(object):
            aborted = []

            def AbortUndoableOperation(self):
                Timeline.add("native-abort")
        verified = ns["prod_abort_apply_and_verify"](
            _Dm(), IDENTITY, u"expression", scope, built, None, ValueError("fixture failure"), authority_context=ctx)
        check("apply.abort_and_verify_restored_under_pinned_membership", verified is True)
        check("apply.abort_path_no_authority_open", _authority_opens() == 0
              and Timeline.kinds()[:2] == ["native-abort", "scene-refresh"], Timeline.kinds())
        stale_membership = dict(ctx, membership={"kind": u"expression", "descriptors": {}})
        raises("apply.readback_rejects_membership_drift", (RuntimeError,), lambda: ns["prod_live_bindings_for_cached_scope"](
            IDENTITY, scope, u"expression", authority_context=stale_membership))
        raises("apply.unpinned_readback_would_see_g2", (RuntimeError,), lambda: ns["prod_live_bindings_for_cached_scope"](
            IDENTITY, scope, u"expression"))
    finally:
        _swap(G1_DIR)

    # Static routing inside prod_apply (its native transaction is not executed offline).
    import ast
    tree = ast.parse(app.top_text("prod_apply").encode("utf-8"))
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            kw = set(k.arg for k in node.keywords)
            calls.append((node.lineno, name, kw))
    calls.sort()
    auth = [c for c in calls if c[1] == "prod_cpm_authorize_operation"]
    start_undo = [c for c in calls if c[1] == "StartUndo"]
    late = [c for c in calls if c[1] in ("prod_live_bindings_for_cached_scope", "prod_abort_apply_and_verify")]
    check("apply.static.single_authorization", len(auth) == 1)
    check("apply.static.authorized_before_mutation", auth and start_undo and auth[0][0] < start_undo[0][0])
    check("apply.static.every_late_check_pinned", len(late) == 3 and all("authority_context" in c[2] for c in late))
    forbidden = [c for c in calls if c[1] in ("prod_cpm_open_adapter", "prod_current_provider_descriptor",
                                             "get_semantic_provider", "prod_probe_semantic_provider")
                 or (c[1] == "prod_scope" and start_undo and c[0] > start_undo[0][0])]
    check("apply.static.no_reacquisition", not forbidden, forbidden)
    abort_tree = ast.parse(app.top_text("prod_abort_apply_and_verify").encode("utf-8"))
    passes = [n for n in ast.walk(abort_tree) if isinstance(n, ast.Call)
              and getattr(n.func, "id", None) == "prod_verify_apply_abort_baseline"
              and "authority_context" in set(k.arg for k in n.keywords)]
    check("apply.static.abort_helper_forwards_context", len(passes) == 1)
    _no_outstanding("apply")


# ---------------------------------------------------------------------------
# Review / Reclassify
# ---------------------------------------------------------------------------

class ReviewWindow(route.FakeWindow):
    def __init__(self, ns, literal, state):
        route.FakeWindow.__init__(self)
        self.ns = ns
        self.record = (literal, state)
        self.status = []
        self.published = []
        self.selected_review = []
        self.revalidate_hook = None

    def review_current_record(self):
        return self.record

    def current(self):
        return dict(self.identity)

    def disable_semantic_scene_actions(self):
        pass

    def operation_mark_phase(self, *a, **k):
        pass

    def operation_revalidate(self):
        Timeline.add("scene-revalidate")
        if self.revalidate_hook:
            self.revalidate_hook()

    def apply_scope_to_ui(self, scope, identity=None):
        self.published.append(scope)

    def review_select_literal(self, literal, state):
        self.selected_review.append((literal, state))

    def set_status(self, text, kind=None):
        self.status.append(text)

    def guard(self, label, work):
        try:
            return work()
        except Exception as exc:
            self.error = exc
            self.prod_cpm_request_stale_rebuild_if_needed()
            return None


def section_review(ns, app):
    win_methods(ns, app)
    Store.files.clear()
    profile_path = os.path.join(LIBRARY_DIR, "character.json")

    # Decision on a genuine healthy miss.
    win = ReviewWindow(ns, u"Thigh", u"miss")
    win.identity = dict(IDENTITY)
    win.provider_health = {"status": u"healthy"}
    win.scope = _fresh_scope(ns)
    check("review.fixture_thigh_is_g1_miss", u"Thigh" in win.scope["unresolved"])
    Timeline.reset()
    win.review_decision(u"body")
    kinds = Timeline.kinds()
    check("review.decision_succeeds_no_r6_refusal", not hasattr(win, "error") and win.status == ["Flex choice saved."],
          [getattr(win, "error", None) and _TEXT(win.error), win.status])
    check("review.authorized_before_write", _first_index("authority-open") < _first_index("durable-write"), kinds)
    writes = [i for i, k in enumerate(kinds) if k == "durable-write"]
    opens = [i for i, k in enumerate(kinds) if k == "authority-open"]
    # Two writes to the character profile: prod_ensure_character, then the
    # override record. Two opens precede them: the existing pre-check and the
    # operation authorization. None occurs between the writes.
    check("review.writes_character_profile_twice", len(writes) == 2)
    check("review.no_authority_between_writes", not [i for i in opens if writes[0] < i < writes[-1]], kinds)
    check("review.authorization_precedes_writes", len([i for i in opens if i < writes[0]]) == 2, kinds)
    check("review.rebuild_is_separate_fresh_acquisition", len([i for i in opens if i > writes[-1]]) >= 1, kinds)
    saved = Store.files[profile_path]
    check("review.persistence_facts_from_context", saved["last_validated_provider"]["source_sha256"]
          == _sha(os.path.join(G1_DIR, MASTER_NAME)) and saved["semantic_overrides"][u"Thigh"]["decision"] == u"body")
    check("review.rebuilt_scope_applies_override", u"Thigh" in win.scope["body"] and u"Thigh" in win.scope["overrides"])

    # Ineligible literals are refused before any write.
    for literal, why in ((u"Belly", "resolved"), (u"Wink", "conflict")):
        win_bad = ReviewWindow(ns, literal, u"miss")
        win_bad.identity = dict(IDENTITY)
        win_bad.provider_health = {"status": u"healthy"}
        win_bad.scope = _fresh_scope(ns)
        Timeline.reset()
        win_bad.review_decision(u"body")
        check("review.refuses_%s_literal_before_write" % why, hasattr(win_bad, "error")
              and "durable-write" not in Timeline.kinds())

    # Stale generation before the decision: rejected with the scope still
    # selected, so the section 13 rebuild is scheduled; no write.
    win_stale = ReviewWindow(ns, u"Ghost", u"miss")
    win_stale.identity = dict(IDENTITY)
    win_stale.provider_health = {"status": u"healthy"}
    win_stale.scope = _fresh_scope(ns)
    route._QtStub.QTimer.scheduled = []
    _swap(G2_DIR)
    try:
        Timeline.reset()
        win_stale.review_decision(u"expression")
        check("review.stale_rejected_before_write", hasattr(win_stale, "error") and "durable-write" not in Timeline.kinds())
        check("review.stale_keeps_scope_for_rebuild", win_stale.scope is not None and len(route._QtStub.QTimer.scheduled) == 1)
    finally:
        _swap(G1_DIR)

    # Reclassify: the durable clear succeeds under G1; the Master moves to G2
    # before the rebuild, and G2 positively resolves Thigh. The two facts are
    # reported separately; no raise.
    win_re = ReviewWindow(ns, u"Thigh", u"reviewed")
    win_re.identity = dict(IDENTITY)
    win_re.provider_health = {"status": u"healthy"}
    win_re.scope = _fresh_scope(ns)
    check("reclassify.fixture_override_present", u"Thigh" in win_re.scope["overrides"])
    win_re.revalidate_hook = lambda: _swap(G2_DIR)
    try:
        Timeline.reset()
        win_re.review_reclassify()
        saved = Store.files[profile_path]
        check("reclassify.durable_edit_succeeded", not hasattr(win_re, "error") and u"Thigh" not in saved["semantic_overrides"],
              getattr(win_re, "error", None) and _TEXT(win_re.error))
        check("reclassify.rebuilt_under_new_authority", win_re.scope["authority"]["provider_sha256"] == _sha(os.path.join(G2_DIR, MASTER_NAME)))
        outcome = ns["prod_cpm_reclassify_outcome"](u"Thigh", win_re.scope)
        check("reclassify.outcome_separates_facts", outcome == {"durable_edit": True, "returned_to_review": False,
                                                                 "current_semantic_class": u"body-morphs",
                                                                 "current_semantic_status": u"resolved"}, _canon(outcome))
        check("reclassify.not_forced_back_to_review", win_re.selected_review == [] and win_re.status == ["Classification cleared."],
              win_re.status)
        check("reclassify.rebuild_after_write", _last_index("authority-open") > _first_index("durable-write"))
    finally:
        _swap(G1_DIR)

    # Reclassify returning to review keeps the existing flow.
    Store.files[profile_path]["semantic_overrides"][u"Thigh"] = {
        "source": u"user", "applies_when": u"master-miss", "decision": u"body", "created_at": u"x"}
    win_back = ReviewWindow(ns, u"Thigh", u"reviewed")
    win_back.identity = dict(IDENTITY)
    win_back.provider_health = {"status": u"healthy"}
    win_back.scope = _fresh_scope(ns)
    win_back.review_reclassify()
    check("reclassify.returns_to_review_when_still_miss", win_back.selected_review == [(u"Thigh", u"miss")]
          and win_back.status == ["Choose a new classification for this flex."])
    check("review.no_historical_provider", route.Env.forbidden_calls == [], route.Env.forbidden_calls)
    _no_outstanding("review")


def section_r6_boundary(ns):
    scope = _fresh_scope(ns)
    live = ns["prod_live_bindings_for_cached_scope"](IDENTITY, scope, u"expression")
    raises("r6.fit_warning_query_still_fail_closed", (ns["ProdCpmAuthorityNotMigrated"],),
           lambda: ns["p03_unmapped_relevant_controls"]({"provider": live["provider"]},
                                                        [{"literal": u"Belly", "shape": u"b", "global_key": u"k"}],
                                                        {"mappings": []}))
    raises("r6.contextless_ensure_character_still_refused", (ns["ProdCpmAuthorityNotMigrated"],),
           lambda: ns["prod_ensure_character"](IDENTITY))


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------

def _section(name, fn, *args):
    """Run one section; an unexpected exception is a named failure, and the
    Master fixture is restored to G1 for the next section."""
    try:
        result = fn(*args)
        check("section.%s.completed" % name, True)
        return result
    except Exception as exc:
        check("section.%s.completed" % name, False, "%s: %s" % (type(exc).__name__, exc))
        _swap(G1_DIR)
        return None


def run_suite():
    app = route.AppSource(route.APP_PATH)
    ns = build_namespace(app)
    _section("context", section_context, ns)
    _section("save", section_save, ns)
    item = _section("update", section_update, ns)
    if item is not None:
        _section("prompt_generation_change", section_prompt_generation_change, ns, app, item)
    _section("apply", section_apply, ns, app)
    _section("review", section_review, ns, app)
    _section("r6_boundary", section_r6_boundary, ns)
    check("suite.no_historical_provider_anywhere", route.Env.forbidden_calls == [], route.Env.forbidden_calls)
    _no_outstanding("suite_end")


def write_digest(path):
    route.write_digest(path)


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
    write_digest(DIGEST_PY3)


def phase_suite():
    if not (os.path.isfile(os.path.join(LIVE_DIR, MASTER_NAME)) and os.path.isfile(DIGEST_PY3)):
        print("RESULT: fixtures missing; run --phase=publish first")
        sys.exit(1)
    if not os.path.isdir(LIBRARY_DIR):
        os.makedirs(LIBRARY_DIR)
    run_suite()
    write_digest(DIGEST_PY27 if PY2 else DIGEST_PY3 + ".rerun")


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
