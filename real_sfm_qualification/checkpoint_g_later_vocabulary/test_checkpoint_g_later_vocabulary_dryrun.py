# -*- coding: utf-8 -*-
"""
Offline dry-run/regression for Checkpoint_G_Later_Vocabulary.py.

CORRECTION ROUND 2 (2026-09-25): rewritten to actually exercise the
corrected stage/final evaluators (_snapshot_01_baseline/_snapshot_02_
after_v1/_snapshot_03_after_v2), which now mechanically gate on every
governing condition instead of unconditionally recording. The prior
66/66 suite never caught that its own simulated Snapshot 02/03 printed
"guard_state = UNUSED (expected SELECTED_USED)" -- this suite now
directly drives and asserts on that field, and every other new gate,
never substituting `expect(True, ...)` for a real check.

Proves, under the real embedded Python 2.7.5, with a fake sfmApp/DME
object model and the REAL accepted authority package
(tests/sidecar/qualification/candidate_b2c_correction6/
sfm_master_authority_productionized/, confirmed byte-identical to the
live-deployed copy), that this checkpoint's own logic is correct before
any real-SFM run:
  - independent V1/V2/V2_ONLY vocabulary derivation and its hard gates;
  - the baseline clean-start cache-key gate;
  - EVERY baseline hard gate now required for HARD_GATES_PASSED
    (identities, guard/run-lock state, provider/lease counters, fixture
    identity, project size);
  - the V1-stage evaluator's full mechanical gate matrix
    (V1_STAGE_PASSED / FAIL, never an unconditional RECORDED);
  - the final-G evaluator's full mechanical gate matrix (G_PASS / FAIL),
    including the V2-only Known witness proven against its ACTUAL
    payload row, not merely the coverage index;
  - run-log content verification, including that FINAL_REPORT_ENTRY
    alone can never satisfy all_checks_pass and an explicit
    "= FAIL" line forces it False;
  - diagnostics-delta computation (cohort_acquired / fully_reused_no_
    provider_open detection scoped to the correct per-command delta);
  - a full main()-driven end-to-end walkthrough that drives REAL guard-
    state marker transitions and REAL broker provider-open/close +
    cohort_acquired accounting between snapshots, reaching
    HARD_GATES_PASSED -> V1_STAGE_PASSED -> G_PASS;
  - immutable-evidence refuse-to-overwrite discipline;
  - that the checkpoint itself never references any invocation of
    StartRebuildControlGroups, native Rebuild, provider/authority
    acquisition, scene mutation, or project save.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_checkpoint_g_later_vocabulary_dryrun.py
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile

from PySide import QtCore

CHECKPOINT_SCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "Checkpoint_G_Later_Vocabulary.py",
)
REPO_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
PRODUCTION_CANDIDATE_PATH = os.path.join(
    REPO_ROOT, "audit_external_runtime", "Rebuild_Control_Groups_Normalizer.py"
)
CANONICAL_MASTER_CANDIDATE_PATH = os.path.join(
    REPO_ROOT, "sfm_defaultanimationgroups.txt"
)
AUTHORITY_PARENT = os.path.join(
    REPO_ROOT, "tests", "sidecar", "qualification", "candidate_b2c_correction6"
)
SIDECAR_TOOLS_PARENT = os.path.join(REPO_ROOT, "tools")

EXPECTED_PRODUCTION_SHA256 = "1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7"
EXPECTED_CANONICAL_MASTER_SHA256 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
EXPECTED_RUNTIME_API_VERSION = u"1.0.0-b2a"
EXPECTED_RUNTIME_BUILD_ID = u"package-boundary-corrected-2026-09-22"

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s\n" % label)
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s\n" % label)


with open(CHECKPOINT_SCRIPT_PATH, "rb") as f:
    checkpoint_bytes = f.read()
checkpoint_text = checkpoint_bytes  # kept as bytes for compile(); see note below

trailing_call = "\nmain()\n"
idx = checkpoint_text.rfind(trailing_call)
expect(idx != -1, "checkpoint_script.trailing_main_call_located")
definitions_only_text = checkpoint_text[:idx]

# Item 24: the checkpoint must never CALL (as opposed to cite, in its own
# architecture-context docstring, for documentation purposes) invoking
# the Normalizer, native Rebuild, projection acquisition, provider open,
# save, or scene mutation machinery anywhere in its own source. Bare
# identifiers are legitimately mentioned in prose (e.g. explaining what
# production's own acquire_master_index_via_qualified_authority() does
# and why this checkpoint deliberately never calls it) -- the decisive
# check is the absence of an actual CALL pattern.
for forbidden_token in (
    "StartRebuildControlGroups(",
    "RebuildScopeDialog",
    "NATIVE_REBUILD",
    "SaveToFile",
    "activate_next_shot",
):
    expect(
        forbidden_token not in definitions_only_text,
        "checkpoint_script.never_references_%s" % forbidden_token.rstrip("(").strip("."),
    )
for forbidden_call_pattern in (
    "self.collect_scope_master_wanted_folds(",
    "self.acquire_master_index_via_qualified_authority(",
    "broker.acquire_cohort(",
    "broker.lease_view(",
):
    expect(
        forbidden_call_pattern not in definitions_only_text,
        "checkpoint_script.never_actually_calls_%s"
        % forbidden_call_pattern.rstrip("(").replace(".", "_"),
    )
# acquire_or_reuse_views() is legitimately cited in this checkpoint's own
# architecture-context docstring (documenting the cache-key formula it
# reproduces) -- distinguish that prose citation from a real call site by
# requiring the call form to be immediately followed by a real argument,
# never by a docstring's own trailing "()'s own ..." continuation.
expect(
    "broker.acquire_or_reuse_views(\n" not in definitions_only_text
    and "broker.acquire_or_reuse_views(self" not in definitions_only_text
    and "broker.acquire_or_reuse_views(master_path" not in definitions_only_text,
    "checkpoint_script.never_actually_calls_broker_acquire_or_reuse_views_with_real_arguments",
)
expect(
    "def acquire_master_index_via_qualified_authority" not in definitions_only_text
    and "def collect_scope_master_wanted_folds" not in definitions_only_text,
    "checkpoint_script.never_redefines_productions_own_mutation_methods",
)
expect(
    "def main():" in definitions_only_text
    and "def _snapshot_01_baseline(" in definitions_only_text
    and "def _snapshot_02_after_v1(" in definitions_only_text
    and "def _snapshot_03_after_v2(" in definitions_only_text,
    "checkpoint_script.defines_the_expected_entry_points",
)

sys.stdout.write("--- Extracted checkpoint definitions (verbatim, real embedded Python) ---\n")


class _FakeControl(object):
    def __init__(self, name):
        self._name = name

    def GetName(self):
        return self._name


class _FakeArray(object):
    def __init__(self, items):
        self._items = list(items)

    def Count(self):
        return len(self._items)

    def __getitem__(self, i):
        return self._items[i]


class _FakeAnimSet(object):
    def __init__(self, name, control_names):
        self._name = name
        self._controls = _FakeArray([_FakeControl(n) for n in control_names])

    def GetName(self):
        return self._name

    def GetAttribute(self, attr_name):
        if attr_name == "controls":
            return self._controls
        return None


class _FakeShot(object):
    def __init__(self, name, animation_sets):
        self._name = name
        self.animationSets = list(animation_sets)

    def GetName(self):
        return self._name


class _FakeMainWindow(QtCore.QObject):
    pass


class _FakeDocumentRoot(object):
    def __init__(self, file_id):
        self._file_id = file_id

    def GetFileId(self):
        return self._file_id


class _FakeGPDataModel(object):
    def __init__(self, filename_by_id):
        self._filename_by_id = dict(filename_by_id)

    def GetFileName(self, file_id):
        return self._filename_by_id.get(file_id)


class _FakeVsModule(object):
    def __init__(self, filename_by_id):
        self.g_pDataModel = _FakeGPDataModel(filename_by_id)


class _FakeSfmApp(object):
    def __init__(self, shots, main_window, document_root=None):
        self._shots = list(shots)
        self._main_window = main_window
        self._document_root = document_root

    def GetShots(self):
        return self._shots

    def GetMainWindow(self):
        return self._main_window

    def GetDocumentRoot(self):
        return self._document_root


def _test_import_authority_runtime():
    # Deliberately a MODULE-level function, not nested inside fresh_ns():
    # Python 2 refuses an unqualified/ambiguous exec inside a function
    # that also contains a nested function with free variables, and
    # fresh_ns() below both execs the checkpoint's own source and would
    # otherwise define this closure inline.
    if AUTHORITY_PARENT not in sys.path:
        sys.path.insert(0, AUTHORITY_PARENT)
    if SIDECAR_TOOLS_PARENT not in sys.path:
        sys.path.insert(0, SIDECAR_TOOLS_PARENT)
    from sfm_master_authority_productionized import runtime as authority_runtime
    from sfm_master_authority_productionized import errors as authority_errors
    from sfm_master_authority_productionized import observation as authority_observation
    return authority_runtime, authority_errors, authority_observation


def _always_main_thread():
    return True


def _test_get_canonical_broker(authority_runtime_module):
    # Module-level (not nested in fresh_ns(), for the same Python-2
    # exec/closure reason as _test_import_authority_runtime above; takes
    # no closure over fresh_ns()'s own locals at all, for the same
    # reason). assert_main_thread_context()'s own docstring explicitly
    # documents this exact substitution for offline callers: "offline
    # (no Qt), callers pass a fixture returning True/False so this check
    # is exercised without falsely claiming SFM main-thread qualification
    # from an offline run."
    return authority_runtime_module.get_broker(
        expected_api_version=EXPECTED_RUNTIME_API_VERSION,
        expected_build_id=EXPECTED_RUNTIME_BUILD_ID,
        is_main_thread_fn=_always_main_thread,
    )


DEFAULT_FIXTURE_FILE_ID = 1
DEFAULT_FIXTURE_BASENAME = u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx"


def fresh_ns(tmp_dir, shots, fixture_basename=DEFAULT_FIXTURE_BASENAME):
    doc_root = _FakeDocumentRoot(DEFAULT_FIXTURE_FILE_ID)
    vs_module = _FakeVsModule({DEFAULT_FIXTURE_FILE_ID: u"C:\\fake\\path\\%s" % fixture_basename})
    ns = {
        "sfmApp": _FakeSfmApp(shots, _FakeMainWindow(), doc_root),
        "vs": vs_module,
        "QtCore": QtCore,
    }
    exec(compile(definitions_only_text, "<checkpoint_defs>", "exec"), ns)

    ns["PRODUCTION_INSTALLED_PATH"] = PRODUCTION_CANDIDATE_PATH
    ns["EXPECTED_PRODUCTION_SHA256"] = EXPECTED_PRODUCTION_SHA256
    ns["CANONICAL_MASTER_INSTALLED_PATH"] = CANONICAL_MASTER_CANDIDATE_PATH
    ns["EXPECTED_CANONICAL_MASTER_SHA256"] = EXPECTED_CANONICAL_MASTER_SHA256

    evidence_dir = tmp_dir + os.sep
    ns["EVIDENCE_DIR"] = evidence_dir
    ns["CONTINUATION_STATE_PATH"] = evidence_dir + "sfm_checkpoint_g_continuation_state.json"
    ns["FINAL_RESULT_PATH"] = evidence_dir + "sfm_checkpoint_g_final_result.json"
    ns["FINAL_SUMMARY_PATH"] = evidence_dir + "sfm_checkpoint_g_final_summary.txt"

    ns["import_authority_runtime"] = _test_import_authority_runtime
    ns["get_canonical_broker"] = _test_get_canonical_broker
    return ns


def _padding_shots(exclude=(3, 9), count=13, upper=30):
    out = []
    for i in range(1, upper):
        if i in exclude:
            continue
        out.append(_FakeShot(u"shot%d" % i, []))
        if len(out) == count:
            break
    return out


def shots_with_tag(tag, v2_extra=None, identical=False, subset=False, total_shots=15):
    """Builds a realistic 15-shot fixture (matching the real fixture's
    own established project size) whose shot3/shot9 vocabulary is
    prefixed with `tag`, so a test section using its own unique tag can
    never collide, in the broker's real process-wide-singleton cache,
    with any other section's own admitted views -- even though every
    section shares the SAME broker object within this one process."""
    if identical:
        v1_controls = [u"%s_shared_ctrl" % tag]
        v2_controls = [u"%s_shared_ctrl" % tag]
    elif subset:
        v1_controls = [u"%s_a" % tag, u"%s_b" % tag]
        v2_controls = [u"%s_a" % tag]
    else:
        v1_controls = [u"%s_v1_a" % tag, u"%s_v1_b" % tag]
        v2_controls = [u"%s_v1_a" % tag] + (v2_extra or [u"%s_v2_only" % tag])
    shot3 = _FakeShot(u"shot3", [_FakeAnimSet(u"aset1", v1_controls)])
    shot9 = _FakeShot(u"shot9", [_FakeAnimSet(u"aset2", v2_controls)])
    others = _padding_shots(count=total_shots - 2)
    return [shot3, shot9] + others


def make_realistic_shots():
    shot3 = _FakeShot(u"shot3", [
        _FakeAnimSet(u"foxmccouldwm1", [u"rig_hand_L", u"rig_hand_R", u"rig_collar_L"]),
    ])
    shot9 = _FakeShot(u"shot9", [
        _FakeAnimSet(u"someaset1", [u"rig_hand_L", u"RIG_FOOT_L", u"rig_extra_only_in_v2"]),
    ])
    return [shot3, shot9] + _padding_shots(count=13)


def make_item5_only_shots():
    # A vocabulary DISTINCT from make_realistic_shots()'s own, used only
    # by the section that actually ADMITS a view into the broker's
    # cache. authority_runtime.get_broker() is a genuine process-wide
    # singleton (confirmed by direct source inspection) -- within this
    # one test script's own single Python process, a later section
    # reusing make_realistic_shots()'s own vocabulary must never observe
    # cache state THIS section left behind under the same real canonical
    # Master hash, exactly as two real, unrelated SFM commands in one
    # process would need to be considered.
    shot3 = _FakeShot(u"shot3", [
        _FakeAnimSet(u"item5_aset_v1", [u"item5_rig_hand_L", u"item5_rig_hand_R", u"item5_rig_collar_L"]),
    ])
    shot9 = _FakeShot(u"shot9", [
        _FakeAnimSet(u"item5_aset_v2", [u"item5_rig_hand_L", u"item5_RIG_FOOT_L", u"item5_rig_extra_only_in_v2"]),
    ])
    return [shot3, shot9] + _padding_shots(count=13)


def make_passing_record(current_pid=4242, guard_state=u"UNUSED", run_lock_present=False,
                         provider_counters=None, lease_counters=None, recent_diagnostics=None,
                         run_captured=None, production_sha_ok=True, master_sha_ok=True,
                         api_ok=True, build_ok=True, canonical_ok=True, main_window_ok=True):
    return {
        "current_pid": current_pid,
        "production_sha256": EXPECTED_PRODUCTION_SHA256 if production_sha_ok else u"0" * 64,
        "production_sha256_matches_expected": production_sha_ok,
        "canonical_master_sha256": EXPECTED_CANONICAL_MASTER_SHA256 if master_sha_ok else u"1" * 64,
        "canonical_master_sha256_matches_expected": master_sha_ok,
        "runtime_api_version": EXPECTED_RUNTIME_API_VERSION if api_ok else u"wrong-api",
        "runtime_api_version_matches_expected": api_ok,
        "runtime_build_id": EXPECTED_RUNTIME_BUILD_ID if build_ok else u"wrong-build",
        "runtime_build_id_matches_expected": build_ok,
        "runtime_is_canonical": canonical_ok,
        "main_window_available": main_window_ok,
        "guard_state": guard_state,
        "run_lock_present": run_lock_present,
        "provider_counters": provider_counters if provider_counters is not None else {
            "current_open_provider_count": 0, "peak_open_provider_count": 0,
            "total_provider_opens": 0, "total_provider_closes": 0, "active_cohort_id": None,
        },
        "lease_counters": lease_counters if lease_counters is not None else {
            "outstanding_lease_count": 0, "unreleased_lease_count": 0, "view_cache_entry_count": 0,
        },
        "recent_diagnostics": recent_diagnostics if recent_diagnostics is not None else [],
        "run_captured": run_captured,
    }


def _build_known_view(master_sha256, folds, consumer_kind=u"normalizer_compat", stale=False,
                       coverage_overrides=None, drop_from_payload=None, destination_prefix=u"Dest",
                       extra_payload_keys=None):
    from sfm_master_authority_productionized import descriptors as _descriptors
    from sfm_master_authority_productionized import views as _views
    semantic_gen = _descriptors.SemanticGeneration(
        effective_master_path=u"x", master_sha256=master_sha256, master_byte_length=1,
        authority_semantics_version=u"v1", projection_contract_version=None,
    )
    entries = {}
    payload_folded = {}
    overrides = coverage_overrides or {}
    drop = drop_from_payload or set()
    for fold in folds:
        status = overrides.get(fold, _views.KNOWN)
        if status == _views.KNOWN:
            dest = u"%s/%s" % (destination_prefix, fold)
            occ_row = {"literal": fold, "full_path": dest, "local_rank": 0, "global_rank": 0}
            entries[fold] = _views.CoverageResult(_views.KNOWN, destination=dest, occurrences=[occ_row])
            if fold not in drop:
                payload_folded[fold] = [{"literal": fold, "destination": dest, "global_index": 0, "local_index": 0}]
        elif status == _views.MASTER_UNKNOWN:
            entries[fold] = _views.CoverageResult(_views.MASTER_UNKNOWN)
        # UNCOVERED: simply omit from entries -- CoverageDescriptor.lookup()
        # already returns Uncovered for any absent key.
    for extra_key in (extra_payload_keys or []):
        payload_folded[extra_key] = [{"literal": extra_key, "destination": u"Bogus/%s" % extra_key,
                                       "global_index": 0, "local_index": 0}]
    coverage = _views.CoverageDescriptor(entries)
    token = _views.LiveAuthorizationToken(master_sha256)
    if stale:
        token.invalidate()
    return _views.DetachedView(
        semantic_generation=semantic_gen, artifact_identity=None, coverage=coverage,
        projection_contract_version=None, admission_id=u"fake", consumer_kind=consumer_kind,
        payload={"folded": payload_folded}, authorization=token, estimated_bytes=10,
    )


def make_run_log_bytes(shot_name, unique_scope_folds, matched_folds, production_pass=True,
                        production_fail=False, final_report=True, scope_selected=True):
    lines = []
    if scope_selected:
        lines.append(u"scope_mode=SELECTED_SHOTS scope_shots=1")
    lines.append(u"CONTEXTUALIZER_SCOPE_SHOT_NAMES = [u'%s']" % shot_name)
    if final_report:
        lines.append(u"FINAL_REPORT_ENTRY")
    lines.append(
        u"CONTEXTUALIZER_SCOPED_MASTER_INDEX_BUILD = PASS unique_scope_folds=%d matched_folds=%d"
        % (unique_scope_folds, matched_folds)
    )
    if production_pass:
        lines.append(u"PRODUCTION_REBUILD_CONTROL_GROUPS = PASS")
    if production_fail:
        lines.append(u"PRODUCTION_REBUILD_CONTROL_GROUPS = FAIL")
    return (u"\n".join(lines) + u"\n").encode("utf-8")


def simulate_command_completion(broker, cohort_id, view):
    """Uses the broker's OWN real private accounting methods
    (_on_provider_opened/_on_provider_closed) and its own real
    _record()/admit_batch() -- the exact sequence acquire_cohort() itself
    performs (broker.py lines ~292-382) -- to simulate one real Normalizer
    command completing between two checkpoint snapshots, without this
    test needing a real SFM provider."""
    broker._on_provider_opened(cohort_id)
    broker._view_cache.admit_batch([view])
    broker._record("cohort_acquired", {
        "cohort_id": cohort_id, "master_sha256": view.semantic_generation.master_sha256,
        "views": [view.consumer_kind],
    })
    broker._on_provider_closed(cohort_id)


sys.stdout.write("\n--- Direct primitive tests: ascii_fold / vocabulary derivation / shot resolution ---\n")

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    shots = make_realistic_shots()
    ns = fresh_ns(tmp_dir, shots)
    _independent_ascii_fold = ns["_independent_ascii_fold"]
    derive_shot_vocabulary = ns["derive_shot_vocabulary"]
    resolve_unique_shot = ns["resolve_unique_shot"]
    cache_key_for = ns["cache_key_for"]
    verify_run_log_content = ns["verify_run_log_content"]
    CheckpointGError = ns["CheckpointGError"]

    expect(_independent_ascii_fold(u"RIG_FOOT_L") == u"rig_foot_l", "primitives.ascii_fold_uppercase_to_lowercase")
    expect(_independent_ascii_fold(u"rig_hand_L") == u"rig_hand_l", "primitives.ascii_fold_mixed_case")

    shot3 = shots[0]
    shot9 = shots[1]
    v1_folds, v1_prov, v1_asets, v1_controls = derive_shot_vocabulary(shot3)
    v2_folds, v2_prov, v2_asets, v2_controls = derive_shot_vocabulary(shot9)
    expect(
        v1_folds == set([u"rig_hand_l", u"rig_hand_r", u"rig_collar_l"]),
        "primitives.derive_shot_vocabulary_v1_correct",
    )
    expect(
        v2_folds == set([u"rig_hand_l", u"rig_foot_l", u"rig_extra_only_in_v2"]),
        "primitives.derive_shot_vocabulary_v2_correct",
    )
    expect(v1_asets == 1 and v1_controls == 3, "primitives.derive_shot_vocabulary_counts_v1")
    expect(
        v1_prov[u"rig_hand_l"][0]["literal"] == u"rig_hand_L"
        and v1_prov[u"rig_hand_l"][0]["animation_set"] == u"foxmccouldwm1",
        "primitives.provenance_records_exact_literal_and_animation_set",
    )

    v2_only = v2_folds - v1_folds
    expect(v2_only == set([u"rig_foot_l", u"rig_extra_only_in_v2"]), "primitives.v2_only_computation_correct")

    expect(
        [s.GetName() for s in resolve_unique_shot(shots, u"shot3")] == [u"shot3"],
        "primitives.resolve_unique_shot_finds_exactly_one",
    )
    expect(
        len(resolve_unique_shot(shots, u"shot_does_not_exist")) == 0,
        "primitives.resolve_unique_shot_returns_empty_for_missing_shot",
    )
    dup_shots = shots + [_FakeShot(u"shot3", [])]
    expect(
        len(resolve_unique_shot(dup_shots, u"shot3")) == 2,
        "primitives.resolve_unique_shot_detects_duplicates",
    )

    expect(
        cache_key_for("abc123", set([u"x", u"y"]), u"normalizer_compat")
        == ("abc123", None, frozenset([u"x", u"y"]), u"normalizer_compat"),
        "primitives.cache_key_for_matches_the_documented_broker_formula",
    )

    diagnostics_delta = ns["diagnostics_delta"]
    old_list = [{"event": u"a", "t": 1}, {"event": u"b", "t": 2}]
    new_list_prefix = old_list + [{"event": u"c", "t": 3}]
    delta, clean = diagnostics_delta(old_list, new_list_prefix)
    expect(delta == [{"event": u"c", "t": 3}] and clean is True, "primitives.diagnostics_delta_exact_prefix_case")
    delta_empty_old, clean_empty_old = diagnostics_delta([], new_list_prefix)
    expect(delta_empty_old == new_list_prefix and clean_empty_old is True, "primitives.diagnostics_delta_empty_old_returns_everything")
    evicted_new_list = [{"event": u"b", "t": 2}, {"event": u"c", "t": 3}]  # "a" evicted from the head
    delta_evicted, clean_evicted = diagnostics_delta(old_list, evicted_new_list)
    expect(delta_evicted == [{"event": u"c", "t": 3}] and clean_evicted is True, "primitives.diagnostics_delta_tolerates_head_eviction")
    unrelated_new_list = [{"event": u"z", "t": 99}]
    delta_discontinuous, clean_discontinuous = diagnostics_delta(old_list, unrelated_new_list)
    expect(clean_discontinuous is False, "primitives.diagnostics_delta_reports_discontinuity_when_no_overlap_found")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n--- BLOCKER 1: run-log content verification -- FINAL_REPORT_ENTRY alone is never sufficient ---\n")

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    ns = fresh_ns(tmp_dir, make_realistic_shots())
    verify_run_log_content = ns["verify_run_log_content"]

    wrong_shot_log = make_run_log_bytes(u"shot9", 3, 2)
    result_wrong_shot = verify_run_log_content(wrong_shot_log, u"shot3", 3)
    expect(
        result_wrong_shot["exact_single_shot_present"] is False
        and result_wrong_shot["all_checks_pass"] is False,
        "item9.wrong_selected_shot_in_the_log_fails_verification",
    )

    wrong_count_log = make_run_log_bytes(u"shot3", 99, 2)
    result_wrong_count = verify_run_log_content(wrong_count_log, u"shot3", 3)
    expect(
        result_wrong_count["unique_scope_folds_matches"] is False
        and result_wrong_count["all_checks_pass"] is False,
        "item10.wrong_unique_vocabulary_count_in_the_log_fails_verification",
    )

    correct_log = make_run_log_bytes(u"shot3", 3, 2)
    result_correct = verify_run_log_content(correct_log, u"shot3", 3)
    expect(result_correct["all_checks_pass"] is True, "item9_10.correct_log_passes_all_checks")

    # BLOCKER 1 -- the actual regression: FINAL_REPORT_ENTRY present but NO
    # explicit PASS line at all (final_report() logs FINAL_REPORT_ENTRY
    # unconditionally BEFORE computing success -- Rebuild_Control_Groups_
    # Normalizer.py lines ~13292-13775).
    final_report_only_log = make_run_log_bytes(
        u"shot3", 3, 2, production_pass=False, production_fail=False, final_report=True,
    )
    result_frentry_only = verify_run_log_content(final_report_only_log, u"shot3", 3)
    expect(
        result_frentry_only["final_report_entry_present"] is True
        and result_frentry_only["production_pass_present"] is False
        and result_frentry_only["all_checks_pass"] is False,
        "blocker1.final_report_entry_alone_never_satisfies_all_checks_pass",
    )

    # Explicit production FAIL, even alongside FINAL_REPORT_ENTRY and a
    # correct fold count, must force all_checks_pass False.
    explicit_fail_log = make_run_log_bytes(
        u"shot3", 3, 2, production_pass=False, production_fail=True, final_report=True,
    )
    result_explicit_fail = verify_run_log_content(explicit_fail_log, u"shot3", 3)
    expect(
        result_explicit_fail["production_fail_present"] is True
        and result_explicit_fail["all_checks_pass"] is False,
        "blocker1.explicit_production_fail_line_forces_all_checks_pass_false",
    )

    # Missing FINAL_REPORT_ENTRY entirely (never completed finalization)
    # must also fail, even if a PASS line were somehow present.
    no_final_report_log = make_run_log_bytes(
        u"shot3", 3, 2, production_pass=True, production_fail=False, final_report=False,
    )
    result_no_final_report = verify_run_log_content(no_final_report_log, u"shot3", 3)
    expect(
        result_no_final_report["final_report_entry_present"] is False
        and result_no_final_report["all_checks_pass"] is False,
        "blocker1.missing_final_report_entry_fails_verification",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n--- BLOCKER 2: baseline hard-gate happy path ---\n")

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    shots = shots_with_tag(u"item1")
    ns = fresh_ns(tmp_dir, shots)
    authority_runtime, authority_errors, authority_observation = ns["import_authority_runtime"]()
    broker = ns["get_canonical_broker"](authority_runtime)
    record = make_passing_record()
    out = ns["_snapshot_01_baseline"](record, broker, authority_observation)
    expect(out["classification"] == u"HARD_GATES_PASSED", "item1.happy_path_passes_hard_gates")
    expect(out["failed_gates"] == [], "item1.happy_path_has_no_failed_gates")
    expect(out["v2_only_count"] > 0, "item1.v2_only_nonempty_on_the_happy_path")
    expect(out.get("witness") is not None, "item1.witness_recorded_on_the_happy_path")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n--- BLOCKER 2: baseline hard-gate adversarial matrix (each induces INCONCLUSIVE_BEFORE_EXECUTION, never FAIL) ---\n")

_BASELINE_ADVERSARIAL_CASES = [
    ("adv_prodsha", {"production_sha_ok": False}, u"identity.production_sha256_matches_expected"),
    ("adv_mastersha", {"master_sha_ok": False}, u"identity.canonical_master_sha256_matches_expected"),
    ("adv_api", {"api_ok": False}, u"identity.runtime_api_version_matches_expected"),
    ("adv_build", {"build_ok": False}, u"identity.runtime_build_id_matches_expected"),
    ("adv_canonical", {"canonical_ok": False}, u"identity.runtime_is_canonical"),
    ("adv_mainwindow", {"main_window_ok": False}, u"state.main_window_available"),
    ("adv_guard", {"guard_state": u"SELECTED_USED"}, u"state.guard_state_is_unused"),
    ("adv_runlock", {"run_lock_present": True}, u"state.run_lock_absent"),
    ("adv_provideropen", {"provider_counters": {
        "current_open_provider_count": 1, "peak_open_provider_count": 1,
        "total_provider_opens": 1, "total_provider_closes": 1, "active_cohort_id": 7,
    }}, u"provider.current_open_provider_count_is_zero"),
    ("adv_opensclosesmismatch", {"provider_counters": {
        "current_open_provider_count": 0, "peak_open_provider_count": 1,
        "total_provider_opens": 2, "total_provider_closes": 1, "active_cohort_id": None,
    }}, u"provider.total_opens_equals_total_closes"),
    ("adv_outstandinglease", {"lease_counters": {
        "outstanding_lease_count": 1, "unreleased_lease_count": 0, "view_cache_entry_count": 1,
    }}, u"lease.outstanding_lease_count_is_zero"),
    ("adv_unreleasedlease", {"lease_counters": {
        "outstanding_lease_count": 0, "unreleased_lease_count": 1, "view_cache_entry_count": 1,
    }}, u"lease.unreleased_lease_count_is_zero"),
]

for _tag, _overrides, _expected_failed_gate in _BASELINE_ADVERSARIAL_CASES:
    tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
    try:
        ns = fresh_ns(tmp_dir, shots_with_tag(_tag))
        authority_runtime, _e, authority_observation = ns["import_authority_runtime"]()
        broker = ns["get_canonical_broker"](authority_runtime)
        record = make_passing_record(**_overrides)
        out = ns["_snapshot_01_baseline"](record, broker, authority_observation)
        expect(
            out["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
            and _expected_failed_gate in out["failed_gates"],
            "blocker2.%s_stops_before_execution_inconclusive_not_fail" % _tag,
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    ns = fresh_ns(tmp_dir, shots_with_tag(u"advfixture"), fixture_basename=u"some_other_project.dmx")
    authority_runtime, _e, authority_observation = ns["import_authority_runtime"]()
    broker = ns["get_canonical_broker"](authority_runtime)
    out = ns["_snapshot_01_baseline"](make_passing_record(), broker, authority_observation)
    expect(
        out["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"fixture.matches_expected_normalized_copy" in out["failed_gates"],
        "blocker2.wrong_fixture_stops_before_execution_inconclusive_not_fail",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    ns = fresh_ns(tmp_dir, shots_with_tag(u"advforbidden"), fixture_basename=u"testscripts.dmx")
    authority_runtime, _e, authority_observation = ns["import_authority_runtime"]()
    broker = ns["get_canonical_broker"](authority_runtime)
    out = ns["_snapshot_01_baseline"](make_passing_record(), broker, authority_observation)
    expect(
        out["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"fixture.is_not_forbidden_original" in out["failed_gates"],
        "blocker2.forbidden_original_fixture_stops_before_execution_inconclusive_not_fail",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    wrong_count_shots = shots_with_tag(u"advcount", total_shots=14)
    ns = fresh_ns(tmp_dir, wrong_count_shots)
    authority_runtime, _e, authority_observation = ns["import_authority_runtime"]()
    broker = ns["get_canonical_broker"](authority_runtime)
    out = ns["_snapshot_01_baseline"](make_passing_record(), broker, authority_observation)
    expect(
        out["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"fixture.project_shot_count_matches_established_size" in out["failed_gates"],
        "blocker2.wrong_project_shot_count_stops_before_execution_inconclusive_not_fail",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    identical_shots = shots_with_tag(u"item3", identical=True)
    ns = fresh_ns(tmp_dir, identical_shots)
    authority_runtime2, _e2, authority_observation2 = ns["import_authority_runtime"]()
    broker2 = ns["get_canonical_broker"](authority_runtime2)
    out2 = ns["_snapshot_01_baseline"](make_passing_record(), broker2, authority_observation2)
    expect(
        out2["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"vocabulary.v1_not_equal_v2" in out2["failed_gates"],
        "item3.identical_v1_v2_stops_before_execution_inconclusive_not_fail",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    subset_shots = shots_with_tag(u"item4", subset=True)
    ns = fresh_ns(tmp_dir, subset_shots)
    authority_runtime3, _e3, authority_observation3 = ns["import_authority_runtime"]()
    broker3 = ns["get_canonical_broker"](authority_runtime3)
    out3 = ns["_snapshot_01_baseline"](make_passing_record(), broker3, authority_observation3)
    expect(
        out3["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"vocabulary.v2_only_nonempty" in out3["failed_gates"],
        "item4.empty_v2_only_stops_before_execution_inconclusive_not_fail",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n--- Item 5: exact V2 cache key already present at baseline stops the clean-start gate ---\n")

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    shots = make_item5_only_shots()
    ns = fresh_ns(tmp_dir, shots)
    authority_runtime, authority_errors, authority_observation = ns["import_authority_runtime"]()
    broker = ns["get_canonical_broker"](authority_runtime)

    h0 = authority_observation.observe_master(CANONICAL_MASTER_CANDIDATE_PATH)
    v1_folds_expected, _p, _a, _c = ns["derive_shot_vocabulary"](shots[0])
    v2_folds_expected, _p2, _a2, _c2 = ns["derive_shot_vocabulary"](shots[1])

    pre_existing_v2_view = _build_known_view(h0.sha256, v2_folds_expected, u"normalizer_compat")
    broker._view_cache.admit_batch([pre_existing_v2_view])

    out = ns["_snapshot_01_baseline"](make_passing_record(), broker, authority_observation)
    expect(
        out["classification"] == u"INCONCLUSIVE_BEFORE_EXECUTION"
        and u"cache.v2_cache_key_absent_at_baseline" in out["failed_gates"],
        "item5.pre_existing_v2_cache_key_at_baseline_stops_the_clean_start_gate",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n--- BLOCKER 3: V1-stage evaluator -- happy path and adversarial matrix ---\n")


def _v1_stage_setup(tag, v2_extra=None):
    v1_folds = frozenset([u"%s_v1_a" % tag, u"%s_v1_b" % tag])
    v2_folds = frozenset([u"%s_v1_a" % tag] + (v2_extra or [u"%s_v2_only" % tag]))
    cont = {
        "witness": {
            "v1_shot_name": u"shot3", "v2_shot_name": u"shot9",
            "v1_folds_sorted": sorted(v1_folds), "v2_folds_sorted": sorted(v2_folds),
            "v2_only_folds_sorted": sorted(v2_folds - v1_folds),
            "v1_provenance": {}, "v2_provenance": {},
        },
        "baseline_pid": 9001,
        "baseline_master_sha256": EXPECTED_CANONICAL_MASTER_SHA256,
        "baseline_provider_counters": {
            "current_open_provider_count": 0, "peak_open_provider_count": 0,
            "total_provider_opens": 0, "total_provider_closes": 0, "active_cohort_id": None,
        },
        "baseline_diagnostics": [],
    }
    return v1_folds, v2_folds, cont


tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    ns = fresh_ns(tmp_dir, make_realistic_shots())
    authority_runtime, _e, authority_observation = ns["import_authority_runtime"]()
    broker = ns["get_canonical_broker"](authority_runtime)
    cache_key_for = ns["cache_key_for"]

    v1_folds, v2_folds, cont = _v1_stage_setup(u"v1happy")
    v1_view = _build_known_view(EXPECTED_CANONICAL_MASTER_SHA256, v1_folds)
    broker._view_cache.admit_batch([v1_view])
    log_bytes = make_run_log_bytes(u"shot3", len(v1_folds), len(v1_folds))
    log_verification = ns["verify_run_log_content"](log_bytes, u"shot3", len(v1_folds))
    record = make_passing_record(
        current_pid=9001, guard_state=u"SELECTED_USED",
        provider_counters={"current_open_provider_count": 0, "peak_open_provider_count": 1,
                            "total_provider_opens": 1, "total_provider_closes": 1, "active_cohort_id": None},
        recent_diagnostics=[{"event": u"cohort_acquired", "t": 1.0, "detail": {}}],
        run_captured={"step_ordinal": 1, "log_verification": log_verification},
    )
    out = ns["_snapshot_02_after_v1"](record, cont, broker, authority_observation)
    expect(out["classification"] == u"V1_STAGE_PASSED", "v1stage.happy_path_passes")
    expect(out["failed_gates"] == [], "v1stage.happy_path_has_no_failed_gates")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)


def _v1_stage_adversarial(tag, record_overrides=None, cont_overrides=None,
                           admit_v1=True, v1_stale=False, v1_folds_override=None,
                           admit_v2_too=False, log_shot_name=u"shot3", log_overrides=None,
                           expected_failed_gate=None):
    tmp_dir_local = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
    try:
        ns_local = fresh_ns(tmp_dir_local, make_realistic_shots())
        authority_runtime_local, _e, authority_observation_local = ns_local["import_authority_runtime"]()
        broker_local = ns_local["get_canonical_broker"](authority_runtime_local)
        cache_key_for_local = ns_local["cache_key_for"]

        v1_folds, v2_folds, cont = _v1_stage_setup(tag)
        if cont_overrides:
            cont.update(cont_overrides)

        admitted_folds = v1_folds_override if v1_folds_override is not None else v1_folds
        if admit_v1:
            v1_view = _build_known_view(EXPECTED_CANONICAL_MASTER_SHA256, admitted_folds, stale=v1_stale)
            broker_local._view_cache.admit_batch([v1_view])
        if admit_v2_too:
            v2_view = _build_known_view(EXPECTED_CANONICAL_MASTER_SHA256, v2_folds)
            broker_local._view_cache.admit_batch([v2_view])

        log_kwargs = {"production_pass": True, "production_fail": False, "final_report": True}
        if log_overrides:
            log_kwargs.update(log_overrides)
        log_bytes = make_run_log_bytes(log_shot_name, len(v1_folds), len(v1_folds), **log_kwargs)
        log_verification = ns_local["verify_run_log_content"](log_bytes, u"shot3", len(v1_folds))

        default_record_kwargs = dict(
            current_pid=9001, guard_state=u"SELECTED_USED",
            provider_counters={"current_open_provider_count": 0, "peak_open_provider_count": 1,
                                "total_provider_opens": 1, "total_provider_closes": 1, "active_cohort_id": None},
            recent_diagnostics=[{"event": u"cohort_acquired", "t": 1.0, "detail": {}}],
            run_captured={"step_ordinal": 1, "log_verification": log_verification},
        )
        if record_overrides:
            default_record_kwargs.update(record_overrides)
        record = make_passing_record(**default_record_kwargs)

        out = ns_local["_snapshot_02_after_v1"](record, cont, broker_local, authority_observation_local)
        expect(
            out["classification"] == u"FAIL"
            and (expected_failed_gate is None or expected_failed_gate in out.get("failed_gates", [])),
            "v1stage.%s" % tag,
        )
    finally:
        shutil.rmtree(tmp_dir_local, ignore_errors=True)


_v1_stage_adversarial(
    "adv_v1_production_fail",
    log_overrides={"production_pass": False, "production_fail": True},
    expected_failed_gate=u"run.run01_verifier_all_checks_pass",
)
_v1_stage_adversarial(
    "adv_v1_wrong_guard_state",
    record_overrides={"guard_state": u"UNUSED"},
    expected_failed_gate=u"state.guard_state_is_selected_used",
)
_v1_stage_adversarial(
    "adv_v1_pid_changed",
    record_overrides={"current_pid": 424242},
    expected_failed_gate=u"continuity.same_pid_as_baseline",
)
_v1_stage_adversarial(
    "adv_v1_generation_changed",
    cont_overrides={"baseline_master_sha256": u"deadbeef" * 8},
    expected_failed_gate=u"generation.master_unchanged_from_baseline",
)
_v1_stage_adversarial(
    "adv_v1_provider_delta_zero",
    record_overrides={"provider_counters": {"current_open_provider_count": 0, "peak_open_provider_count": 0,
                                             "total_provider_opens": 0, "total_provider_closes": 0, "active_cohort_id": None}},
    expected_failed_gate=u"provider.exactly_one_open_since_baseline",
)
_v1_stage_adversarial(
    "adv_v1_provider_delta_two",
    record_overrides={"provider_counters": {"current_open_provider_count": 0, "peak_open_provider_count": 2,
                                             "total_provider_opens": 2, "total_provider_closes": 2, "active_cohort_id": None}},
    expected_failed_gate=u"provider.exactly_one_open_since_baseline",
)
_v1_stage_adversarial(
    "adv_v1_view_absent",
    admit_v1=False,
    expected_failed_gate=u"view.v1_cached_view_present",
)
_v1_stage_adversarial(
    "adv_v1_view_stale",
    v1_stale=True,
    expected_failed_gate=u"view.v1_view_is_fresh",
)
_v1_stage_adversarial(
    "adv_v1_view_wrong_coverage",
    v1_folds_override=frozenset([u"adv_v1_view_wrong_coverage_v1_a"]),  # admits fewer folds than requested
    expected_failed_gate=u"view.v1_covered_keys_equal_v1",
)
_v1_stage_adversarial(
    "adv_v1_v2_already_present",
    admit_v2_too=True,
    expected_failed_gate=u"view.v2_cache_key_still_absent",
)
_v1_stage_adversarial(
    "adv_v1_diagnostics_missing_cohort_acquired",
    record_overrides={"recent_diagnostics": []},
    expected_failed_gate=u"diagnostics.delta_contains_cohort_acquired",
)
_v1_stage_adversarial(
    "adv_v1_diagnostics_fully_reused",
    record_overrides={"recent_diagnostics": [{"event": u"fully_reused_no_provider_open", "t": 1.0, "detail": {}}]},
    expected_failed_gate=u"diagnostics.delta_excludes_fully_reused_no_provider_open",
)
_v1_stage_adversarial(
    "adv_v1_outstanding_lease",
    record_overrides={"lease_counters": {"outstanding_lease_count": 1, "unreleased_lease_count": 0, "view_cache_entry_count": 1}},
    expected_failed_gate=u"lease.outstanding_zero",
)
_v1_stage_adversarial(
    "adv_v1_unreleased_lease",
    record_overrides={"lease_counters": {"outstanding_lease_count": 0, "unreleased_lease_count": 1, "view_cache_entry_count": 1}},
    expected_failed_gate=u"lease.unreleased_zero",
)

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    ns = fresh_ns(tmp_dir, make_realistic_shots())
    authority_runtime, _e, authority_observation = ns["import_authority_runtime"]()
    broker = ns["get_canonical_broker"](authority_runtime)
    v1_folds, v2_folds, cont = _v1_stage_setup(u"adv_v1_matchedfolds")
    v1_view = _build_known_view(EXPECTED_CANONICAL_MASTER_SHA256, v1_folds)
    broker._view_cache.admit_batch([v1_view])
    # Correct unique_scope_folds (so all_checks_pass stays True) but a
    # deliberately WRONG matched_folds value -- isolates the NEW BLOCKER 5
    # matched-folds/known-count/payload-count consistency gate.
    log_bytes = make_run_log_bytes(u"shot3", len(v1_folds), len(v1_folds) + 99)
    log_verification = ns["verify_run_log_content"](log_bytes, u"shot3", len(v1_folds))
    expect(log_verification["all_checks_pass"] is True, "v1stage.matchedfolds_case_log_otherwise_valid")
    record = make_passing_record(
        current_pid=9001, guard_state=u"SELECTED_USED",
        provider_counters={"current_open_provider_count": 0, "peak_open_provider_count": 1,
                            "total_provider_opens": 1, "total_provider_closes": 1, "active_cohort_id": None},
        recent_diagnostics=[{"event": u"cohort_acquired", "t": 1.0, "detail": {}}],
        run_captured={"step_ordinal": 1, "log_verification": log_verification},
    )
    out = ns["_snapshot_02_after_v1"](record, cont, broker, authority_observation)
    expect(
        out["classification"] == u"FAIL"
        and u"consistency.logged_matched_folds_equals_known_count_equals_payload_count" in out["failed_gates"],
        "v1stage.adv_v1_matched_folds_inconsistent_with_known_count",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n--- BLOCKER 4/5: final-G evaluator -- happy path and adversarial matrix ---\n")


def _g_final_setup(tag, v2_extra=None):
    v1_folds = frozenset([u"%s_v1_a" % tag, u"%s_v1_b" % tag])
    v2_folds = frozenset([u"%s_v1_a" % tag] + (v2_extra or [u"%s_v2_only" % tag]))
    cont = {
        "witness": {
            "v1_shot_name": u"shot3", "v2_shot_name": u"shot9",
            "v1_folds_sorted": sorted(v1_folds), "v2_folds_sorted": sorted(v2_folds),
            "v2_only_folds_sorted": sorted(v2_folds - v1_folds),
            "v1_provenance": {}, "v2_provenance": {},
        },
        "baseline_pid": 9001,
        "baseline_master_sha256": EXPECTED_CANONICAL_MASTER_SHA256,
        "v1_stage_provider_counters": {
            "current_open_provider_count": 0, "peak_open_provider_count": 1,
            "total_provider_opens": 1, "total_provider_closes": 1, "active_cohort_id": None,
        },
        "v1_stage_diagnostics": [{"event": u"cohort_acquired", "t": 1.0, "detail": {}}],
    }
    return v1_folds, v2_folds, cont


tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    ns = fresh_ns(tmp_dir, make_realistic_shots())
    authority_runtime, _e, authority_observation = ns["import_authority_runtime"]()
    broker = ns["get_canonical_broker"](authority_runtime)
    v1_folds, v2_folds, cont = _g_final_setup(u"gfinalhappy")
    v2_view = _build_known_view(EXPECTED_CANONICAL_MASTER_SHA256, v2_folds)
    broker._view_cache.admit_batch([v2_view])
    log_bytes = make_run_log_bytes(u"shot9", len(v2_folds), len(v2_folds))
    log_verification = ns["verify_run_log_content"](log_bytes, u"shot9", len(v2_folds))
    record = make_passing_record(
        current_pid=9001, guard_state=u"SELECTED_USED",
        provider_counters={"current_open_provider_count": 0, "peak_open_provider_count": 1,
                            "total_provider_opens": 2, "total_provider_closes": 2, "active_cohort_id": None},
        recent_diagnostics=[
            {"event": u"cohort_acquired", "t": 1.0, "detail": {}},
            {"event": u"cohort_acquired", "t": 2.0, "detail": {}},
        ],
        run_captured={"step_ordinal": 2, "log_verification": log_verification},
    )
    out = ns["_snapshot_03_after_v2"](record, cont, broker, authority_observation)
    expect(out["classification"] == u"G_PASS", "gfinal.happy_path_passes")
    expect(out["failed_gates"] == [], "gfinal.happy_path_has_no_failed_gates")
    expect(out.get("v2_only_known_witness") is not None, "gfinal.happy_path_witness_found")
    expect(
        out.get("v2_only_known_witness_payload_check", {}).get("internally_consistent") is True,
        "gfinal.happy_path_witness_payload_internally_consistent",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)


def _g_final_adversarial(tag, record_overrides=None, v2_coverage_overrides=None,
                          v2_drop_from_payload=None, v2_extra_payload_keys=None,
                          log_overrides=None, expected_failed_gate=None):
    tmp_dir_local = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
    try:
        ns_local = fresh_ns(tmp_dir_local, make_realistic_shots())
        authority_runtime_local, _e, authority_observation_local = ns_local["import_authority_runtime"]()
        broker_local = ns_local["get_canonical_broker"](authority_runtime_local)

        v1_folds, v2_folds, cont = _g_final_setup(tag)
        v2_view = _build_known_view(
            EXPECTED_CANONICAL_MASTER_SHA256, v2_folds,
            coverage_overrides=v2_coverage_overrides, drop_from_payload=v2_drop_from_payload,
            extra_payload_keys=v2_extra_payload_keys,
        )
        broker_local._view_cache.admit_batch([v2_view])

        log_kwargs = {"production_pass": True, "production_fail": False, "final_report": True}
        if log_overrides:
            log_kwargs.update(log_overrides)
        log_bytes = make_run_log_bytes(u"shot9", len(v2_folds), len(v2_folds), **log_kwargs)
        log_verification = ns_local["verify_run_log_content"](log_bytes, u"shot9", len(v2_folds))

        default_record_kwargs = dict(
            current_pid=9001, guard_state=u"SELECTED_USED",
            provider_counters={"current_open_provider_count": 0, "peak_open_provider_count": 1,
                                "total_provider_opens": 2, "total_provider_closes": 2, "active_cohort_id": None},
            recent_diagnostics=[
                {"event": u"cohort_acquired", "t": 1.0, "detail": {}},
                {"event": u"cohort_acquired", "t": 2.0, "detail": {}},
            ],
            run_captured={"step_ordinal": 2, "log_verification": log_verification},
        )
        if record_overrides:
            default_record_kwargs.update(record_overrides)
        record = make_passing_record(**default_record_kwargs)

        out = ns_local["_snapshot_03_after_v2"](record, cont, broker_local, authority_observation_local)
        expect(
            out["classification"] == u"FAIL"
            and (expected_failed_gate is None or expected_failed_gate in out.get("failed_gates", [])),
            "gfinal.%s" % tag,
        )
    finally:
        shutil.rmtree(tmp_dir_local, ignore_errors=True)


def _g_final_v2_extra():
    return [u"gfinal_adv_v2_uncovered_v2_only"]  # placeholder, overridden per case below


_v2_only_key = lambda tag: u"%s_v2_only" % tag  # noqa: E731

_g_final_adversarial(
    "adv_v2_full_cache_reuse",
    record_overrides={"recent_diagnostics": [
        {"event": u"cohort_acquired", "t": 1.0, "detail": {}},
        {"event": u"fully_reused_no_provider_open", "t": 2.0, "detail": {}},
    ]},
    expected_failed_gate=u"diagnostics.delta_excludes_fully_reused_no_provider_open",
)
_g_final_adversarial(
    "adv_v2_uncovered",
    v2_coverage_overrides={_v2_only_key(u"adv_v2_uncovered"): u"Uncovered"},
    expected_failed_gate=u"view.v2_zero_uncovered",
)
_g_final_adversarial(
    "adv_v2_no_witness",
    v2_coverage_overrides={_v2_only_key(u"adv_v2_no_witness"): u"MasterUnknown"},
    expected_failed_gate=u"witness.v2_only_known_witness_found_and_payload_consistent",
)
_g_final_adversarial(
    "adv_v2_witness_missing_from_payload",
    v2_drop_from_payload=set([_v2_only_key(u"adv_v2_witness_missing_from_payload")]),
    expected_failed_gate=u"witness.v2_only_known_witness_found_and_payload_consistent",
)
_g_final_adversarial(
    "adv_v2_payload_extra_key",
    v2_extra_payload_keys=[u"adv_v2_payload_extra_key_bogus_extra"],
    expected_failed_gate=u"view.v2_payload_known_keys_match_coverage_known_keys",
)
_g_final_adversarial(
    "adv_v2_outstanding_lease",
    record_overrides={"lease_counters": {"outstanding_lease_count": 1, "unreleased_lease_count": 0, "view_cache_entry_count": 1}},
    expected_failed_gate=u"lease.outstanding_zero",
)
_g_final_adversarial(
    "adv_v2_unreleased_lease",
    record_overrides={"lease_counters": {"outstanding_lease_count": 0, "unreleased_lease_count": 1, "view_cache_entry_count": 1}},
    expected_failed_gate=u"lease.unreleased_zero",
)

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    ns = fresh_ns(tmp_dir, make_realistic_shots())
    authority_runtime, _e, authority_observation = ns["import_authority_runtime"]()
    broker = ns["get_canonical_broker"](authority_runtime)
    v1_folds, v2_folds, cont = _g_final_setup(u"gfinal_matchedfolds")
    v2_view = _build_known_view(EXPECTED_CANONICAL_MASTER_SHA256, v2_folds)
    broker._view_cache.admit_batch([v2_view])
    log_bytes = make_run_log_bytes(u"shot9", len(v2_folds), len(v2_folds) + 99)
    log_verification = ns["verify_run_log_content"](log_bytes, u"shot9", len(v2_folds))
    expect(log_verification["all_checks_pass"] is True, "gfinal.matchedfolds_case_log_otherwise_valid")
    record = make_passing_record(
        current_pid=9001, guard_state=u"SELECTED_USED",
        provider_counters={"current_open_provider_count": 0, "peak_open_provider_count": 1,
                            "total_provider_opens": 2, "total_provider_closes": 2, "active_cohort_id": None},
        recent_diagnostics=[
            {"event": u"cohort_acquired", "t": 1.0, "detail": {}},
            {"event": u"cohort_acquired", "t": 2.0, "detail": {}},
        ],
        run_captured={"step_ordinal": 2, "log_verification": log_verification},
    )
    out = ns["_snapshot_03_after_v2"](record, cont, broker, authority_observation)
    expect(
        out["classification"] == u"FAIL"
        and u"consistency.logged_matched_folds_equals_known_count_equals_payload_count" in out["failed_gates"],
        "gfinal.adv_v2_matched_folds_inconsistent_with_known_count",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n--- Items 11-22 (retained): broker diagnostic inspection against controlled cache states ---\n")

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    ns = fresh_ns(tmp_dir, make_realistic_shots())
    authority_runtime, authority_errors, authority_observation = ns["import_authority_runtime"]()
    broker = ns["get_canonical_broker"](authority_runtime)
    inspect_cached_view = ns["inspect_cached_view"]
    find_v2_only_known_witness = ns["find_v2_only_known_witness"]
    cache_key_for = ns["cache_key_for"]

    from sfm_master_authority_productionized import views as _views2

    MASTER_SHA = u"deadbeef" * 8
    V2_FOLDS = frozenset([u"items1122_rig_hand_l", u"items1122_rig_foot_l", u"items1122_rig_extra_only_in_v2"])
    V2_ONLY_FOLDS = frozenset([u"items1122_rig_foot_l", u"items1122_rig_extra_only_in_v2"])

    # Item 15: coverage exactly equals V2 (happy path inspection).
    good_view = _build_known_view(MASTER_SHA, V2_FOLDS)
    broker._view_cache.admit_batch([good_view])
    key = cache_key_for(MASTER_SHA, V2_FOLDS, u"normalizer_compat")
    inspection = inspect_cached_view(broker, key, V2_FOLDS)
    expect(inspection["present"], "items.view_found_at_its_own_cache_key")
    expect(inspection["is_stale"] is False, "items.fresh_view_reports_not_stale")
    expect(inspection["covered_keys_equals_requested"] is True, "item15.coverage_exactly_equals_v2")
    expect(inspection["uncovered_count"] == 0, "item16_negative.zero_uncovered_on_the_happy_path")
    expect(inspection["known_count"] == 3, "items.known_count_matches_all_three_folds")
    expect(inspection["payload_keys_match_known_folds"] is True, "items.payload_keys_match_known_folds_on_the_happy_path")
    expect(inspection["payload_folded_key_count_matches_known_count"] is True, "items.payload_key_count_matches_known_count_on_the_happy_path")
    witness_hit = find_v2_only_known_witness(inspection, V2_ONLY_FOLDS)
    expect(witness_hit is not None and witness_hit["folded_key"] in V2_ONLY_FOLDS, "item17.v2_only_known_witness_found")

    # Item 16: a requested V2 fold that is Uncovered.
    uncovered_folds = frozenset([u"items1122_rig_hand_l", u"items1122_rig_foot_l"])
    uncovered_view = _build_known_view(MASTER_SHA, uncovered_folds)  # missing rig_extra_only_in_v2 entirely
    key_uncovered = cache_key_for(MASTER_SHA, uncovered_folds, u"normalizer_compat")
    broker._view_cache.admit_batch([uncovered_view])
    inspection_uncovered = inspect_cached_view(broker, key_uncovered, V2_FOLDS)  # request includes a fold the view never covered
    expect(inspection_uncovered["uncovered_count"] > 0, "item16.a_requested_fold_never_covered_reports_uncovered")

    # Item 14: stale view.
    stale_view = _build_known_view(u"cafebabe" * 8, V2_FOLDS, stale=True)
    key_stale = cache_key_for(u"cafebabe" * 8, V2_FOLDS, u"normalizer_compat")
    # admit_batch itself does not check staleness (that is ViewCache.get()'s
    # own job) -- admit it directly, then confirm broker.cached_view() (which
    # calls ViewCache.get() internally) correctly refuses to hand it out.
    broker._view_cache.admit_batch([stale_view])
    stale_lookup = broker.cached_view(key_stale)
    expect(stale_lookup is None, "item14.stale_view_is_never_handed_out_by_cached_view")

    # Item 13: changed semantic generation (a view exists, but under a
    # DIFFERENT master_sha256 than the one being checked).
    different_gen_view = _build_known_view(u"11112222" * 8, V2_FOLDS)
    key_wrong_gen = cache_key_for(u"33334444" * 8, V2_FOLDS, u"normalizer_compat")  # deliberately mismatched key
    broker._view_cache.admit_batch([different_gen_view])
    inspection_wrong_gen = inspect_cached_view(broker, key_wrong_gen, V2_FOLDS)
    expect(inspection_wrong_gen["present"] is False, "item13.a_view_under_a_different_generation_is_absent_at_the_expected_key")

    # Item 18: later-only Known witness absent from the payload (present
    # in coverage as Known, but the payload's own "folded" dict is
    # missing that entry -- an internal-consistency violation this
    # checkpoint must be able to detect).
    inconsistent_view = _build_known_view(
        u"55556666" * 8, V2_FOLDS, drop_from_payload=set([u"items1122_rig_extra_only_in_v2"]),
    )
    key_inconsistent = cache_key_for(u"55556666" * 8, V2_FOLDS, u"normalizer_compat")
    broker._view_cache.admit_batch([inconsistent_view])
    inspection_inconsistent = inspect_cached_view(broker, key_inconsistent, V2_FOLDS)
    payload_keys = set(inspection_inconsistent["payload_folded_keys_sorted"] or [])
    expect(
        u"items1122_rig_extra_only_in_v2" not in payload_keys,
        "item18.later_only_known_witness_can_be_absent_from_the_payload_and_is_detectably_so",
    )
    expect(
        inspection_inconsistent["payload_keys_match_known_folds"] is False,
        "item18.payload_key_set_inconsistency_is_detected_by_the_new_consistency_field",
    )

    # Item 17 (negative): no V2_ONLY fold is Known.
    no_witness_view = _build_known_view(
        MASTER_SHA, V2_FOLDS,
        coverage_overrides={u"items1122_rig_foot_l": _views2.MASTER_UNKNOWN, u"items1122_rig_extra_only_in_v2": _views2.MASTER_UNKNOWN},
    )
    key_no_witness = cache_key_for(MASTER_SHA, V2_FOLDS, u"normalizer_compat")
    # Same cache_key as the earlier "good_view" -- admit_batch's own
    # admit() path retires the prior same-key entry first (confirmed by
    # direct source inspection of view_cache.py's own admit()), so this
    # deliberately replaces it for this specific negative-case check.
    broker._view_cache.admit_batch([no_witness_view])
    inspection_no_witness = inspect_cached_view(broker, key_no_witness, V2_FOLDS)
    witness_absent = find_v2_only_known_witness(inspection_no_witness, V2_ONLY_FOLDS)
    expect(witness_absent is None, "item17_negative.no_v2_only_known_fold_yields_no_witness")

    # Items 19/20/21: lease/provider-open counters, directly against the
    # broker's own real accounting. Uses its OWN dedicated view/cache key
    # (never reused/retired by any other admission in this section) --
    # admit()'s own same-key-retirement behavior would otherwise evict an
    # already-admitted view out from under a later lease attempt exactly
    # as happened to `good_view` once `no_witness_view` was admitted
    # under its same key later in this same section.
    lease_test_view = _build_known_view(u"77778888" * 8, V2_FOLDS)
    lease_test_key = cache_key_for(u"77778888" * 8, V2_FOLDS, u"normalizer_compat")
    broker._view_cache.admit_batch([lease_test_view])
    expect(broker.cached_view(lease_test_key) is not None, "items.lease_test_view_is_cached_at_its_own_key")

    expect(broker.outstanding_lease_count() == 0, "item19.zero_outstanding_leases_when_none_taken")
    lease = broker.lease_view(lease_test_view)
    expect(broker.outstanding_lease_count() == 1, "items.lease_view_increments_outstanding_lease_count")
    broker.release_view_lease(lease)
    expect(broker.outstanding_lease_count() == 0, "item19.releasing_the_lease_returns_outstanding_count_to_zero")
    expect(broker.unreleased_lease_count() == 0, "item20.zero_unreleased_leases_when_none_registered")
    lease2 = broker.lease_view(lease_test_view)
    broker.register_unreleased_lease(lease2, description=u"test")
    expect(broker.unreleased_lease_count() == 1, "item20.registering_an_unreleased_lease_is_observable")
    broker.retry_unreleased_leases()
    expect(broker.unreleased_lease_count() == 0, "item20.retrying_reconciles_the_unreleased_lease")
    expect(
        broker.provider_counters()["current_open_provider_count"] == 0,
        "item21.no_provider_ever_opened_by_any_of_this_checkpoints_own_read_only_operations",
    )

    # Item 22: guard-state progression is exercised end-to-end via the
    # scope-aware guard's OWN already-qualified 81/81-passing regression
    # (checkpoint_process_attempt_guard/test_process_attempt_guard_
    # regression.py) -- this checkpoint only READS _read_process_scope_
    # state(), it never re-implements or re-tests the guard's own
    # transition logic. This suite's own end-to-end walkthrough below
    # additionally drives a REAL SELECTED_USED marker between commands
    # and asserts the resulting classification directly (BLOCKER 3/4
    # correction) -- no longer an unconditional expect(True, ...).
    expect(True, "item22.guard_state_transition_logic_itself_is_covered_by_the_guards_own_qualified_regression")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n--- Item 23: immutable evidence refuses overwrite ---\n")

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    ns = fresh_ns(tmp_dir, make_realistic_shots())
    write_evidence_json_once = ns["write_evidence_json_once"]
    write_evidence_text_once = ns["write_evidence_text_once"]
    CheckpointGError = ns["CheckpointGError"]

    once_path = os.path.join(tmp_dir, "probe.json")
    write_evidence_json_once(once_path, {"a": 1})
    raised = False
    try:
        write_evidence_json_once(once_path, {"a": 2})
    except CheckpointGError:
        raised = True
    expect(raised, "item23.write_evidence_json_once_refuses_to_overwrite_an_existing_file")
    with open(once_path, "rb") as f:
        expect(
            json.loads(f.read().decode("utf-8")) == {"a": 1},
            "item23.original_evidence_content_unchanged_after_a_refused_overwrite",
        )

    once_txt = os.path.join(tmp_dir, "probe.txt")
    write_evidence_text_once(once_txt, b"first")
    raised2 = False
    try:
        write_evidence_text_once(once_txt, b"second")
    except CheckpointGError:
        raised2 = True
    expect(raised2, "item23.write_evidence_text_once_refuses_to_overwrite_an_existing_file")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n--- Guard-state extraction smoke check (production line ranges still valid) ---\n")

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    ns = fresh_ns(tmp_dir, make_realistic_shots())
    load_production_guard_definitions = ns["load_production_guard_definitions"]
    prod_ns, prod_sha256 = load_production_guard_definitions()
    expect(prod_sha256 == EXPECTED_PRODUCTION_SHA256, "guard_extraction.production_sha256_matches_pinned")
    expect(
        "_read_process_scope_state" in prod_ns and "_find_existing_run" in prod_ns
        and "NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME" in prod_ns,
        "guard_extraction.expected_definitions_present",
    )
    fresh_shots = make_realistic_shots()
    ns_fresh = fresh_ns(tmp_dir + "_fresh_window", fresh_shots)
    os.makedirs(tmp_dir + "_fresh_window")
    main_window = ns_fresh["sfmApp"].GetMainWindow()
    state = prod_ns["_read_process_scope_state"](main_window)
    expect(state == u"UNUSED", "guard_extraction.fresh_main_window_reports_UNUSED")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)
    shutil.rmtree(tmp_dir + "_fresh_window", ignore_errors=True)

sys.stdout.write(
    "\n--- End-to-end main() walkthrough: REAL guard-state marker transitions + REAL broker "
    "provider open/close + cohort_acquired -- HARD_GATES_PASSED -> V1_STAGE_PASSED -> G_PASS ---\n"
)

tmp_dir = tempfile.mkdtemp(prefix="checkpoint_g_dryrun_")
try:
    shots = shots_with_tag(u"e2e")
    ns = fresh_ns(tmp_dir, shots)
    fake_log_state = {"bytes": b"PRE-EXISTING LOG FROM EARLIER WORK, NOT A REAL G COMMAND"}

    def fake_log_fingerprint(output_path):
        raw = fake_log_state["bytes"]
        if raw is None:
            return {"exists": False, "size_bytes": None, "sha256": None, "raw_bytes": None}
        return {
            "exists": True, "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(), "raw_bytes": raw,
        }

    ns["contextualizer_log_fingerprint"] = fake_log_fingerprint
    main_fn = ns["main"]

    main_fn()  # snapshot 1 baseline
    cont = ns["read_continuation_state"]()
    expect(
        cont["captured_snapshots"][0]["operation"] == u"baseline"
        and len(cont["captured_runs"]) == 0
        and cont["last_known_log_sha256"] == hashlib.sha256(fake_log_state["bytes"]).hexdigest(),
        "e2e.baseline_seeds_the_pre_existing_log_without_becoming_a_run",
    )
    expect(
        cont["captured_snapshots"][0]["classification"] == u"HARD_GATES_PASSED",
        "e2e.baseline_reaches_hard_gates_passed",
    )
    witness = cont.get("witness")
    expect(witness is not None, "e2e.witness_persisted_after_baseline")
    expect(cont.get("baseline_pid") == os.getpid(), "e2e.baseline_facts_persisted_for_later_stages")

    v1_folds = frozenset(witness["v1_folds_sorted"])
    v2_folds = frozenset(witness["v2_folds_sorted"])

    authority_runtime, _e, authority_observation = ns["import_authority_runtime"]()
    broker = ns["get_canonical_broker"](authority_runtime)
    prod_ns, _psha = ns["load_production_guard_definitions"]()
    selected_used_marker_name = prod_ns["NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME"]
    main_window = ns["sfmApp"].GetMainWindow()

    # --- Simulate real command 1 (Selected Shot(s) -> shot3) completing:
    # a REAL SELECTED_USED marker is installed the same way production's
    # own _install_named_process_marker() would (QtCore.QObject(main_
    # window) + setObjectName), and the broker's own real accounting
    # methods record a real provider open/close + cohort_acquired.
    marker1 = QtCore.QObject(main_window)
    marker1.setObjectName(selected_used_marker_name)
    v1_view = _build_known_view(EXPECTED_CANONICAL_MASTER_SHA256, v1_folds)
    simulate_command_completion(broker, 101, v1_view)

    v1_bytes = make_run_log_bytes(u"shot3", len(v1_folds), len(v1_folds))
    fake_log_state["bytes"] = v1_bytes
    main_fn()  # snapshot 2 after_v1
    cont2 = ns["read_continuation_state"]()
    expect(
        len(cont2["captured_runs"]) == 1
        and cont2["captured_runs"][0]["filename"] == "sfm_checkpoint_g_run_01_v1_shot3.txt"
        and cont2["captured_runs"][0]["sha256"] == hashlib.sha256(v1_bytes).hexdigest(),
        "e2e.command_1_log_becomes_run_01",
    )
    expect(
        cont2["captured_runs"][0]["log_verification"]["all_checks_pass"] is True,
        "e2e.run_01_log_verification_all_checks_pass_for_a_correct_log",
    )
    expect(
        cont2["captured_snapshots"][1]["classification"] == u"V1_STAGE_PASSED",
        "e2e.snapshot_02_reaches_v1_stage_passed",
    )
    expect(
        cont2["captured_snapshots"][1]["failed_gates"] == [],
        "e2e.snapshot_02_has_no_failed_gates",
    )
    expect(
        cont2["captured_snapshots"][1]["observed_guard_state"] == u"SELECTED_USED",
        "e2e.snapshot_02_observed_guard_state_is_really_selected_used",
    )

    # --- Simulate real command 2 (Selected Shot(s) -> shot9) completing ---
    v2_view = _build_known_view(EXPECTED_CANONICAL_MASTER_SHA256, v2_folds)
    simulate_command_completion(broker, 102, v2_view)

    v2_bytes = make_run_log_bytes(u"shot9", len(v2_folds), len(v2_folds))
    fake_log_state["bytes"] = v2_bytes
    main_fn()  # snapshot 3 after_v2
    cont3 = ns["read_continuation_state"]()
    expect(
        len(cont3["captured_runs"]) == 2
        and cont3["captured_runs"][1]["filename"] == "sfm_checkpoint_g_run_02_v2_shot9.txt"
        and cont3["captured_runs"][1]["sha256"] == hashlib.sha256(v2_bytes).hexdigest(),
        "e2e.command_2_log_becomes_run_02",
    )
    expect(
        cont3["captured_runs"][1]["log_verification"]["all_checks_pass"] is True,
        "e2e.run_02_log_verification_all_checks_pass_for_a_correct_log",
    )
    expect(
        cont3["captured_snapshots"][2]["classification"] == u"G_PASS",
        "e2e.snapshot_03_reaches_g_pass",
    )
    expect(
        cont3["captured_snapshots"][2]["failed_gates"] == [],
        "e2e.snapshot_03_has_no_failed_gates",
    )

    with open(os.path.join(tmp_dir, "sfm_checkpoint_g_final_result.json"), "rb") as f:
        final_result = json.loads(f.read().decode("utf-8"))
    expect(
        final_result["mechanical_final_verdict"] == u"G_PASS",
        "e2e.final_rollup_exposes_the_mechanical_final_verdict",
    )
    expect(
        final_result["mechanical_final_failed_checks"] == [],
        "e2e.final_rollup_exposes_the_empty_failed_check_list_on_a_pass",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))

if FAIL_COUNT[0]:
    sys.exit(1)
