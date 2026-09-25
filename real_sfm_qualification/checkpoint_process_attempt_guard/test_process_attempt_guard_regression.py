# -*- coding: utf-8 -*-
"""
Offline regression for the SCOPE-AWARE process-lifetime admission guard in
production (audit_external_runtime/Rebuild_Control_Groups_Normalizer.py).

This supersedes the original broad one-attempt-per-process guard (commit
f3efd132ad5456a583df5917ef85576db0690c60), which received PARTIAL real-SFM
qualification through snapshot #5 (fresh/cancel/one completed Selected
command/armed/refused-with-unchanged-log/session-change/still-refused,
all independently verified against the actual preserved artifacts) before
being intentionally superseded when the one-attempt-per-process product
policy itself was rejected as too restrictive -- see LEDGER.md's F3-Guard
row for the corrected historical record. Astra's original ">1 Selected
shot = batch" classification proposal was REVIEWED AND REJECTED as
unsupported by the evidence and harmful to the intended Selected Shot(s)
feature; the revised, corrected contract instead uses exactly two workload
classes -- SELECTED_SCOPE (any proper subset of project shots, any size)
and FULL_SCOPE (All Shots, or a Selected Shot(s) request whose resolved
shot set exactly equals the complete project shot set) -- and three
process states -- UNUSED, SELECTED_USED, FULL_SCOPE_STARTED. No numeric
shot/target/model/control/memory threshold is used anywhere.

A second, independent-review-driven correction (2026-09-24) replaced the
classifier's original NAME-based full-scope-equivalence check (weaker than
the contract, since duplicate shot names could collapse distinct shots)
with the same CANONICAL IDENTITY (handle-OR-native-pointer) semantics
_resolve_selected_scope() already uses for its own scope resolution,
re-resolved against a FRESH sfmApp.GetShots() snapshot taken after the
scope dialog's own nested Qt event loop has run.

No real SFM environment is available offline, but PySide's QtCore IS
importable standalone with the real embedded Python 2.7.5 (confirmed
throughout this project), so this test extracts the guard's own pure-
Python/Qt helper functions VERBATIM (by source line range, not retyped)
and exercises them against REAL QtCore.QObject instances, plus static,
source-position analysis against the actual deployed production script
text for everything that cannot be exercised as an isolated function.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_process_attempt_guard_regression.py
"""
import gc
import hashlib
import os
import sys

from PySide import QtCore

PRODUCTION_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..",
        "audit_external_runtime",
        "Rebuild_Control_Groups_Normalizer.py",
    )
)
EXPECTED_PRODUCTION_SHA256 = "1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7"
EXPECTED_PRODUCTION_SHA256_PRE_COPY_CLOSEOUT = "2c0edbb8a95f96147e6310fe1c039da7ee053f5e985f11bb3535dda8aa5ec23d"
EXPECTED_PRODUCTION_SHA256_SCOPE_AWARE_NAME_BASED = "1f2b87f2954d1944c06497a8adcda4de1e1663a148d655bf7cd6f3ace4f757dc"
EXPECTED_PRODUCTION_SHA256_BROAD_GUARD = "6170d2a248845281b5f5d38dfea4b9f2decf908b8e3b79e80f4ada18d2f54625"
EXPECTED_PRODUCTION_SHA256_PRE_GUARD = "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"

# Source line ranges for the guard's own pure-Python/Qt helpers, verified
# against the actual file via grep/Read immediately before writing this
# test (not assumed from memory).
NATIVE_PTR_RANGE = (867, 877)
CONSTANTS_MARKER_NAMES_RANGE = (196, 212)
PROBE_ERROR_RANGE = (843, 844)
MARKER_ERROR_CLASS_RANGE = (847, 857)
TO_UNICODE_RANGE = (899, 909)
FIND_NAMED_MARKER_RANGE = (5676, 5718)
INSTALL_NAMED_MARKER_RANGE = (5721, 5772)
PROCESS_STATE_CONSTANTS_RANGE = (5775, 5780)
READ_PROCESS_SCOPE_STATE_RANGE = (5783, 5825)
RESOLVE_SHOT_IDENTITY_RANGE = (5828, 5909)
CLASSIFY_SCOPE_REQUEST_RANGE = (5912, 5992)
SCOPE_MODE_CONSTANTS_RANGE = (8492, 8493)

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s\n" % label)
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s\n" % label)


with open(PRODUCTION_PATH, "rb") as f:
    production_bytes = f.read()
production_sha256 = hashlib.sha256(production_bytes).hexdigest()
production_text = production_bytes.decode("utf-8")
production_lines = production_text.splitlines()

expect(
    production_sha256 == EXPECTED_PRODUCTION_SHA256,
    "production.sha256_matches_pinned_canonical_identity_candidate",
)
expect(
    production_sha256 not in (
        EXPECTED_PRODUCTION_SHA256_PRE_COPY_CLOSEOUT,
        EXPECTED_PRODUCTION_SHA256_SCOPE_AWARE_NAME_BASED,
        EXPECTED_PRODUCTION_SHA256_BROAD_GUARD,
        EXPECTED_PRODUCTION_SHA256_PRE_GUARD,
    ),
    "production.sha256_differs_from_all_four_superseded_baselines",
)


def extract(range_tuple, lines=production_lines):
    start, end = range_tuple
    return "\n".join(lines[start - 1:end])


sys.stdout.write("--- Extracted guard helpers (verbatim, real QtCore) ---\n")


class _FakeShot(object):
    # Carries a canonical identity (uid) independent of its display name,
    # exposed exactly as native_ptr()/the inline handle-resolution code
    # expect: a `.this` attribute (native_ptr(obj) does long(obj.this))
    # and a GetHandle() method. Two _FakeShot instances built from the
    # same (name, uid) spec via separate calls represent two DIFFERENT
    # Python wrapper objects referring to the SAME underlying shot --
    # exactly the stale-pre-dialog-object-vs-fresh-post-dialog-refetch
    # scenario the real guard must handle correctly.
    def __init__(self, name, uid):
        self._name = name
        self._uid = uid
        self.this = uid

    def GetName(self):
        return self._name

    def GetHandle(self):
        return self._uid


class _FakeSfmAppShots(object):
    def __init__(self, specs):
        # specs: list of (name, uid) tuples. Builds FRESH _FakeShot
        # instances on every GetShots() call, distinct Python objects
        # from whatever a caller separately built from the same specs --
        # simulating that the scope dialog's own nested Qt event loop
        # ran since any earlier snapshot/resolution.
        self._specs = list(specs)

    def GetShots(self):
        return [_FakeShot(name, uid) for (name, uid) in self._specs]


def make_scope_shots(specs):
    # Simulates _resolve_selected_scope()'s own output: a list of
    # already-resolved shot objects, built as SEPARATE instances from
    # whatever _FakeSfmAppShots.GetShots() will independently construct.
    return [_FakeShot(name, uid) for (name, uid) in specs]


def build_ns(project_specs):
    ns = {
        "QtCore": QtCore,
        "sfmApp": _FakeSfmAppShots(project_specs),
    }
    for range_tuple in (
        NATIVE_PTR_RANGE,
        CONSTANTS_MARKER_NAMES_RANGE,
        PROBE_ERROR_RANGE,
        MARKER_ERROR_CLASS_RANGE,
        TO_UNICODE_RANGE,
        FIND_NAMED_MARKER_RANGE,
        INSTALL_NAMED_MARKER_RANGE,
        PROCESS_STATE_CONSTANTS_RANGE,
        READ_PROCESS_SCOPE_STATE_RANGE,
        SCOPE_MODE_CONSTANTS_RANGE,
        RESOLVE_SHOT_IDENTITY_RANGE,
        CLASSIFY_SCOPE_REQUEST_RANGE,
    ):
        exec(compile(extract(range_tuple), "<guard_defs>", "exec"), ns)
    return ns


PROJECT_SPECS = [(u"shot1", 1), (u"shot2", 2), (u"shot3", 3), (u"shot4", 4), (u"shot5", 5)]
PROJECT_SHOT_NAMES = [name for (name, uid) in PROJECT_SPECS]

ns = build_ns(PROJECT_SPECS)

NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME = ns["NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME"]
NORMALIZER_PROCESS_STATE_FULL_SCOPE_STARTED_MARKER_NAME = ns["NORMALIZER_PROCESS_STATE_FULL_SCOPE_STARTED_MARKER_NAME"]
NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME_LEGACY = ns["NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME_LEGACY"]
NormalizerProcessAttemptMarkerError = ns["NormalizerProcessAttemptMarkerError"]
PROCESS_SCOPE_STATE_UNUSED = ns["PROCESS_SCOPE_STATE_UNUSED"]
PROCESS_SCOPE_STATE_SELECTED_USED = ns["PROCESS_SCOPE_STATE_SELECTED_USED"]
PROCESS_SCOPE_STATE_FULL_SCOPE_STARTED = ns["PROCESS_SCOPE_STATE_FULL_SCOPE_STARTED"]
SCOPE_REQUEST_CLASS_SELECTED_SCOPE = ns["SCOPE_REQUEST_CLASS_SELECTED_SCOPE"]
SCOPE_REQUEST_CLASS_FULL_SCOPE = ns["SCOPE_REQUEST_CLASS_FULL_SCOPE"]
SCOPE_SELECTED = ns["SCOPE_SELECTED"]
SCOPE_ALL = ns["SCOPE_ALL"]
_find_named_process_marker = ns["_find_named_process_marker"]
_install_named_process_marker = ns["_install_named_process_marker"]
_read_process_scope_state = ns["_read_process_scope_state"]
_classify_scope_request = ns["_classify_scope_request"]

expect(
    NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME
    != NORMALIZER_PROCESS_STATE_FULL_SCOPE_STARTED_MARKER_NAME
    != NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME_LEGACY,
    "marker_names.all_three_distinct",
)


def arm(main_window, project_specs, scope_mode, selected_specs):
    """Simulates the full public-entry + arming sequence for one request,
    using the extracted real functions, and returns the resulting
    (allowed, refusal_reason, state_after)."""
    local_ns = build_ns(project_specs)
    read_state = local_ns["_read_process_scope_state"]
    classify = local_ns["_classify_scope_request"]
    install = local_ns["_install_named_process_marker"]
    st_full = local_ns["PROCESS_SCOPE_STATE_FULL_SCOPE_STARTED"]
    st_selected_used = local_ns["PROCESS_SCOPE_STATE_SELECTED_USED"]
    st_unused = local_ns["PROCESS_SCOPE_STATE_UNUSED"]
    cls_full = local_ns["SCOPE_REQUEST_CLASS_FULL_SCOPE"]
    name_full = local_ns["NORMALIZER_PROCESS_STATE_FULL_SCOPE_STARTED_MARKER_NAME"]
    name_selected = local_ns["NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME"]

    pre_state = read_state(main_window)
    if pre_state == st_full:
        return False, "pre_dialog_full_scope_started", read_state(main_window)

    # scope_shots mirrors _resolve_selected_scope()'s own output: already-
    # resolved shot objects, built as separate instances from whatever a
    # fresh sfmApp.GetShots() call will independently construct at
    # classification time (matching the real dialog's own nested event
    # loop having run since any earlier resolution).
    scope_shots = make_scope_shots(selected_specs)

    requested_class = classify(scope_mode, scope_shots)

    post_state = read_state(main_window)
    if post_state == st_full:
        return False, "post_dialog_full_scope_started", read_state(main_window)
    if post_state == st_selected_used and requested_class == cls_full:
        return False, "selected_used_refuses_full_scope", read_state(main_window)

    # Arming.
    arm_state = read_state(main_window)
    if arm_state == st_full:
        return False, "arm_full_scope_started", read_state(main_window)
    if arm_state == st_selected_used and requested_class == cls_full:
        return False, "arm_selected_used_refuses_full_scope", read_state(main_window)

    if arm_state == st_unused:
        target_name = name_full if requested_class == cls_full else name_selected
        install(main_window, target_name)

    return True, None, read_state(main_window)


sys.stdout.write("\n--- Items 1-9: state-transition matrix (behavioral, real QtCore) ---\n")

mw1 = QtCore.QObject()
allowed, reason, state_after = arm(mw1, PROJECT_SPECS, SCOPE_SELECTED, PROJECT_SPECS[:1])
expect(allowed and state_after == PROCESS_SCOPE_STATE_SELECTED_USED, "item1.UNUSED_plus_1_selected_shot_allow_to_SELECTED_USED")

mw2 = QtCore.QObject()
allowed, reason, state_after = arm(mw2, PROJECT_SPECS, SCOPE_SELECTED, PROJECT_SPECS[:4])
expect(allowed and state_after == PROCESS_SCOPE_STATE_SELECTED_USED, "item2.UNUSED_plus_4_of_5_selected_shots_allow_to_SELECTED_USED")

allowed, reason, state_after = arm(mw2, PROJECT_SPECS, SCOPE_SELECTED, PROJECT_SPECS[:1])
expect(allowed and state_after == PROCESS_SCOPE_STATE_SELECTED_USED, "item3.SELECTED_USED_plus_1_selected_shot_allow")

allowed, reason, state_after = arm(mw2, PROJECT_SPECS, SCOPE_SELECTED, PROJECT_SPECS[1:3])
expect(allowed and state_after == PROCESS_SCOPE_STATE_SELECTED_USED, "item4.SELECTED_USED_plus_several_selected_shots_allow")

allowed, reason, state_after = arm(mw2, PROJECT_SPECS, SCOPE_ALL, PROJECT_SPECS)
expect(not allowed and state_after == PROCESS_SCOPE_STATE_SELECTED_USED, "item5.refused_All_after_SELECTED_USED_leaves_state_unchanged")

allowed, reason, state_after = arm(mw2, PROJECT_SPECS, SCOPE_SELECTED, PROJECT_SPECS[4:5])
expect(allowed and state_after == PROCESS_SCOPE_STATE_SELECTED_USED, "item6.another_selected_request_after_refused_All_still_allowed")

mw3 = QtCore.QObject()
allowed, reason, state_after = arm(mw3, PROJECT_SPECS, SCOPE_ALL, PROJECT_SPECS)
expect(allowed and state_after == PROCESS_SCOPE_STATE_FULL_SCOPE_STARTED, "item7.UNUSED_plus_All_allow_to_FULL_SCOPE_STARTED")

allowed, reason, state_after = arm(mw3, PROJECT_SPECS, SCOPE_SELECTED, PROJECT_SPECS[:1])
expect(not allowed and reason == "pre_dialog_full_scope_started", "item8.FULL_SCOPE_STARTED_plus_Selected_refuse")

allowed, reason, state_after = arm(mw3, PROJECT_SPECS, SCOPE_ALL, PROJECT_SPECS)
expect(not allowed and reason == "pre_dialog_full_scope_started", "item9.FULL_SCOPE_STARTED_plus_All_refuse")

sys.stdout.write("\n--- Items 10-11: full-scope-equivalence classification (canonical identity) ---\n")

expect(
    _classify_scope_request(SCOPE_SELECTED, make_scope_shots(PROJECT_SPECS))
    == SCOPE_REQUEST_CLASS_FULL_SCOPE,
    "item10.selected_set_equal_to_complete_project_set_classifies_FULL_SCOPE",
)
expect(
    _classify_scope_request(SCOPE_SELECTED, make_scope_shots(PROJECT_SPECS[:-1]))
    == SCOPE_REQUEST_CLASS_SELECTED_SCOPE,
    "item11a.selected_proper_subset_all_minus_one_classifies_SELECTED_SCOPE",
)
big_project_specs = [(u"shot%d" % i, 1000 + i) for i in range(50)]
big_project_ns = build_ns(big_project_specs)
expect(
    big_project_ns["_classify_scope_request"](SCOPE_SELECTED, make_scope_shots(big_project_specs[:40]))
    == SCOPE_REQUEST_CLASS_SELECTED_SCOPE,
    "item11b.large_40_of_50_selected_proper_subset_classifies_SELECTED_SCOPE_not_a_size_threshold",
)
expect(
    _classify_scope_request(SCOPE_ALL, make_scope_shots(PROJECT_SPECS))
    == SCOPE_REQUEST_CLASS_FULL_SCOPE,
    "item10b.scope_mode_ALL_is_unconditionally_FULL_SCOPE",
)

sys.stdout.write(
    "\n--- Canonical-identity classification: adversarial coverage (independent-review correction) ---\n"
)

# 1. unique-name exact full selection -> FULL_SCOPE (already item10 above).
expect(
    _classify_scope_request(SCOPE_SELECTED, make_scope_shots(PROJECT_SPECS))
    == SCOPE_REQUEST_CLASS_FULL_SCOPE,
    "adv1.unique_name_exact_full_selection_classifies_FULL_SCOPE",
)

# 2. unique-name proper subset -> SELECTED_SCOPE (already item11a above).
expect(
    _classify_scope_request(SCOPE_SELECTED, make_scope_shots(PROJECT_SPECS[:2]))
    == SCOPE_REQUEST_CLASS_SELECTED_SCOPE,
    "adv2.unique_name_proper_subset_classifies_SELECTED_SCOPE",
)

# 3-5. duplicate shot names in the project must NOT collapse identity.
# Two distinct shots both named "shotA" (uid 10 and uid 11), plus two
# other, uniquely-named shots.
DUPE_SPECS = [(u"shotA", 10), (u"shotA", 11), (u"shot2", 2), (u"shot3", 3)]
dupe_ns = build_ns(DUPE_SPECS)
dupe_classify = dupe_ns["_classify_scope_request"]

expect(
    dupe_classify(SCOPE_SELECTED, make_scope_shots([(u"shotA", 10)]))
    == SCOPE_REQUEST_CLASS_SELECTED_SCOPE,
    "adv3.selecting_only_one_of_two_same_named_shots_is_a_proper_subset_SELECTED_SCOPE",
)
expect(
    dupe_classify(SCOPE_SELECTED, make_scope_shots([(u"shotA", 10), (u"shot2", 2), (u"shot3", 3)]))
    == SCOPE_REQUEST_CLASS_SELECTED_SCOPE,
    "adv4.one_same_named_shot_plus_all_other_distinct_shots_remains_SELECTED_SCOPE_missing_the_other_dupe",
)
expect(
    dupe_classify(SCOPE_SELECTED, make_scope_shots(DUPE_SPECS))
    == SCOPE_REQUEST_CLASS_FULL_SCOPE,
    "adv5.both_same_named_shots_plus_every_other_project_shot_classifies_FULL_SCOPE",
)

# 6. unresolved/ambiguous canonical identity -> fail closed.
ghost_ns = build_ns(PROJECT_SPECS)
ghost_shot = _FakeShot(u"ghost", 99999)  # uid not present in the project at all
raised = False
try:
    ghost_ns["_classify_scope_request"](SCOPE_SELECTED, [ghost_shot])
except ghost_ns["NormalizerProcessAttemptMarkerError"]:
    raised = True
expect(raised, "adv6a.selected_shot_with_no_canonical_match_in_the_fresh_project_set_fails_closed")


class _AmbiguousFakeShot(object):
    # A pathological object whose handle matches ONE real candidate but
    # whose native pointer (`.this`) matches a DIFFERENT real candidate
    # -- an internally inconsistent object that must never be silently
    # resolved to either one.
    def __init__(self, handle_value, ptr_value):
        self._handle_value = handle_value
        self.this = ptr_value

    def GetHandle(self):
        return self._handle_value


ambiguous_ns = build_ns(PROJECT_SPECS)
ambiguous_shot = _AmbiguousFakeShot(handle_value=1, ptr_value=2)
raised = False
try:
    ambiguous_ns["_classify_scope_request"](SCOPE_SELECTED, [ambiguous_shot])
except ambiguous_ns["NormalizerProcessAttemptMarkerError"]:
    raised = True
expect(raised, "adv6b.selected_shot_matching_two_different_real_candidates_by_handle_vs_pointer_fails_closed")

# 7. reordered UI selection does not affect the exact-identity-set result.
reorder_ns = build_ns(PROJECT_SPECS)
result_forward = reorder_ns["_classify_scope_request"](SCOPE_SELECTED, make_scope_shots(PROJECT_SPECS))
result_reversed = reorder_ns["_classify_scope_request"](SCOPE_SELECTED, make_scope_shots(list(reversed(PROJECT_SPECS))))
expect(
    result_forward == result_reversed == SCOPE_REQUEST_CLASS_FULL_SCOPE,
    "adv7.reordered_selection_still_classifies_FULL_SCOPE_identically",
)

# 8. existing 1-shot / 5-shot / large proper-subset behavior unchanged
#    under canonical-identity classification (re-proves items 1/2/11b).
expect(
    _classify_scope_request(SCOPE_SELECTED, make_scope_shots(PROJECT_SPECS[:1]))
    == SCOPE_REQUEST_CLASS_SELECTED_SCOPE,
    "adv8a.single_shot_selection_still_classifies_SELECTED_SCOPE",
)
five_shot_specs = [(u"shotA%d" % i, 2000 + i) for i in range(5)] + [(u"shotB", 2999)]
five_ns = build_ns(five_shot_specs)
expect(
    five_ns["_classify_scope_request"](SCOPE_SELECTED, make_scope_shots(five_shot_specs[:5]))
    == SCOPE_REQUEST_CLASS_SELECTED_SCOPE,
    "adv8b.five_of_six_shot_selection_still_classifies_SELECTED_SCOPE",
)

# 9. All Shots remains unconditionally FULL_SCOPE regardless of the
#    scope_shots argument's own contents (mirrors item10b, with an
#    intentionally-mismatched scope_shots argument to prove scope_mode
#    alone decides for SCOPE_ALL).
mismatched_ns = build_ns(PROJECT_SPECS)
expect(
    mismatched_ns["_classify_scope_request"](SCOPE_ALL, make_scope_shots(PROJECT_SPECS[:1]))
    == SCOPE_REQUEST_CLASS_FULL_SCOPE,
    "adv9.scope_mode_ALL_is_unconditionally_FULL_SCOPE_even_with_mismatched_scope_shots_argument",
)

# 10. state-matrix behavior (items 1-9 above) is unchanged by the
#     canonical-identity correction -- already exercised end-to-end via
#     arm() above, using the same PROJECT_SPECS/DUPE_SPECS-style identity
#     objects throughout rather than name-only fakes.
mw_dupe_state = QtCore.QObject()
allowed, reason, state_after = arm(mw_dupe_state, DUPE_SPECS, SCOPE_SELECTED, [(u"shotA", 10)])
expect(allowed and state_after == PROCESS_SCOPE_STATE_SELECTED_USED, "adv10a.state_matrix_UNUSED_plus_selected_proper_subset_unaffected_by_duplicate_names")
allowed, reason, state_after = arm(mw_dupe_state, DUPE_SPECS, SCOPE_SELECTED, DUPE_SPECS)
expect(not allowed and state_after == PROCESS_SCOPE_STATE_SELECTED_USED, "adv10b.state_matrix_SELECTED_USED_refuses_full_scope_request_even_when_full_scope_equals_all_dupes")

sys.stdout.write("\n--- Item 15: malformed/unreadable/conflicting state fails closed ---\n")


class _FakeMainWindowFindChildrenRaises(object):
    def findChildren(self, cls):
        raise RuntimeError("simulated findChildren failure")


raised = False
try:
    _read_process_scope_state(_FakeMainWindowFindChildrenRaises())
except NormalizerProcessAttemptMarkerError:
    raised = True
expect(raised, "item15a.unreadable_lookup_fails_closed")

mw_conflict = QtCore.QObject()
_install_named_process_marker(mw_conflict, NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME)
_install_named_process_marker(mw_conflict, NORMALIZER_PROCESS_STATE_FULL_SCOPE_STARTED_MARKER_NAME)
raised = False
try:
    _read_process_scope_state(mw_conflict)
except NormalizerProcessAttemptMarkerError:
    raised = True
expect(raised, "item15b.both_state_markers_present_at_once_fails_closed_conflicting")

mw_dup = QtCore.QObject()
QtCore.QObject(mw_dup).setObjectName(NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME)
QtCore.QObject(mw_dup).setObjectName(NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME)
raised = False
try:
    _find_named_process_marker(mw_dup, NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME)
except NormalizerProcessAttemptMarkerError:
    raised = True
expect(raised, "item15c.duplicate_same_name_markers_fails_closed_malformed")

sys.stdout.write("\n--- Item 16: legacy marker requires restart, never assumed UNUSED/SELECTED_USED ---\n")

mw_legacy = QtCore.QObject()
QtCore.QObject(mw_legacy).setObjectName(NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME_LEGACY)
raised = False
raised_message = u""
try:
    _read_process_scope_state(mw_legacy)
except NormalizerProcessAttemptMarkerError as exc:
    raised = True
    raised_message = unicode(exc)
expect(raised, "item16a.legacy_marker_alone_requires_restart")
expect("legacy" in raised_message.lower(), "item16b.legacy_marker_error_message_identifies_itself_as_legacy")

mw_legacy_plus_new = QtCore.QObject()
QtCore.QObject(mw_legacy_plus_new).setObjectName(NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME_LEGACY)
QtCore.QObject(mw_legacy_plus_new).setObjectName(NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME)
raised = False
try:
    _read_process_scope_state(mw_legacy_plus_new)
except NormalizerProcessAttemptMarkerError:
    raised = True
expect(raised, "item16c.legacy_marker_present_requires_restart_even_alongside_a_new_scheme_marker")

sys.stdout.write("\n--- Fail-closed on install/verify errors (carried over from the broad guard's own proofs) ---\n")


class _AlwaysEmptyFindChildrenMainWindow(QtCore.QObject):
    def findChildren(self, cls):
        return []


raised = False
try:
    _install_named_process_marker(
        _AlwaysEmptyFindChildrenMainWindow(),
        NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME,
    )
except NormalizerProcessAttemptMarkerError:
    raised = True
expect(raised, "install.verify_step_finding_nothing_raises_fail_closed")


class _PoisonedObjectName(object):
    def objectName(self):
        raise RuntimeError("simulated objectName() failure")


class _FakeMainWindowOneBadChild(object):
    def findChildren(self, cls):
        return [_PoisonedObjectName()]


raised = False
try:
    _find_named_process_marker(_FakeMainWindowOneBadChild(), NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME)
except NormalizerProcessAttemptMarkerError:
    raised = True
expect(raised, "find.objectName_exception_on_any_child_fails_closed")

sys.stdout.write("\n--- No scene/authority payload retained; survives gc.collect() ---\n")

mw_payload = QtCore.QObject()
marker = _install_named_process_marker(mw_payload, NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME)
expect(type(marker) is QtCore.QObject, "install.returned_object_is_a_plain_QObject")
keepalive_list = getattr(mw_payload, "_sfm_rebuild_control_groups_process_attempt_marker_keepalive", None)
expect(isinstance(keepalive_list, list) and len(keepalive_list) == 1, "install.keepalive_has_exactly_one_entry")
gc.collect()
expect(
    _find_named_process_marker(mw_payload, NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME) is not None,
    "install.survives_an_explicit_gc_collect",
)
for forbidden_token in ("DmeControlGroup", "aset", "capture_tree", "master_index", "GetRootControlGroup"):
    expect(
        forbidden_token not in extract(INSTALL_NAMED_MARKER_RANGE) and forbidden_token not in extract(FIND_NAMED_MARKER_RANGE),
        "install.source_never_references_%s" % forbidden_token,
    )

sys.stdout.write(
    "\n--- Static source-position proofs against the actual deployed production script ---\n"
)

start_def_index = production_text.index("    def start(self):")
start_rebuild_def_index = production_text.index("def StartRebuildControlGroups():")
choose_scope_call_index = production_text.index(") = _choose_scope()")
folds_call_index = production_text.index("self.collect_scope_master_wanted_folds()")

# Item 12 (static): a dialog cancel returns (None, None) from
# _choose_scope(), and StartRebuildControlGroups()'s own
# "if scope_mode is None: return" sits before the request classifier and
# before RebuildControlGroupsProductionRun is ever constructed -- so
# cancel can never reach _classify_scope_request or any install call.
scope_none_check_index = production_text.index("if scope_mode is None:\n        return")
classify_call_index = production_text.index("requested_scope_class = _classify_scope_request(")
expect(
    choose_scope_call_index < scope_none_check_index < classify_call_index,
    "item12.cancel_none_check_sits_before_classification_and_construction",
)

# Item 13 (static): the existing bounded "No SFM document is open"
# rejection inside start() sits before the arm block's own install call
# site, so it leaves state unchanged.
no_document_raise_index = production_text.index('"No SFM document is open."')
expect(
    production_text.count("_install_named_process_marker(") == 2,
    "static.install_helper_referenced_exactly_twice_total_def_plus_one_call_site",
)
arm_install_call_index = production_text.rindex("_install_named_process_marker(")
expect(
    start_def_index < no_document_raise_index < arm_install_call_index,
    "item13.bounded_pre_arm_rejection_sits_before_the_install_call",
)

# Item 14 (static): neither new-scheme marker name, nor the legacy
# marker name, nor the keepalive attribute is ever referenced by any
# cleanup path (release_run_lock / final_report / abort) -- confirmed by
# extracting those three functions' own text and checking for absence,
# exactly as the broad guard's own test proved for its single marker.
release_lock_start = production_text.index("    def release_run_lock(self):")
release_lock_end = production_text.index("    def get_game_model(\n")
final_report_start = production_text.index("    def final_report(")
final_report_end = production_text.index("    def start(self):")
abort_start = production_text.index("    def abort(\n")
abort_end = production_text.index("    def section(\n")

release_lock_text = production_text[release_lock_start:release_lock_end]
final_report_text = production_text[final_report_start:final_report_end]
abort_text = production_text[abort_start:abort_end]

for label, text in (
    ("release_run_lock", release_lock_text),
    ("final_report", final_report_text),
    ("abort", abort_text),
):
    for marker_identifier in (
        "NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME",
        "NORMALIZER_PROCESS_STATE_FULL_SCOPE_STARTED_MARKER_NAME",
        "NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME_LEGACY",
        "_sfm_rebuild_control_groups_process_attempt_marker_keepalive",
    ):
        expect(
            marker_identifier not in text,
            "item14.%s_never_references_%s" % (label, marker_identifier),
        )

expect(
    production_text.count(".deleteLater()") == 1,
    "item14b.exactly_one_deleteLater_call_in_whole_file_ie_no_new_deletion_path",
)

# Item 17 (static, offline-provable half): the state-reading function
# takes only main_window -- never a document/session/scene reference --
# so its result cannot depend on which document is open. Real cross-
# document persistence itself is proven by the real-SFM checkpoint.
expect(
    "def _read_process_scope_state(main_window):" in production_text,
    "item17.state_reader_signature_is_main_window_only_not_document_scoped",
)
expect(
    "GetCurrentDocument" not in extract(READ_PROCESS_SCOPE_STATE_RANGE),
    "item17b.state_reader_never_references_a_document_or_session_object",
)

# Item 18 (static): a SECOND, distinct _read_process_scope_state() call
# exists after the _choose_scope() call site, proving the modal dialog's
# own nested event loop is accounted for by a reread rather than trusting
# the pre-dialog read.
read_state_def_index = production_text.index("_read_process_scope_state(main_window):")
read_state_all_indices = [
    i for i in range(len(production_text))
    if production_text.startswith("_read_process_scope_state(", i)
]
read_state_call_indices = [
    i for i in read_state_all_indices if i != read_state_def_index
]
# def line + 3 real call sites (arm-time, pre-dialog, post-dialog) = 4
# total occurrences of the substring "_read_process_scope_state(" (the
# def line itself also contains this substring, right after "def ").
expect(
    len(read_state_all_indices) == 4 and len(read_state_call_indices) == 3,
    "item18a.process_scope_state_is_read_exactly_three_times_pre_dialog_post_dialog_and_at_arm",
)
post_dialog_read_call_index = [
    i for i in read_state_call_indices if i > choose_scope_call_index
][0]
expect(
    choose_scope_call_index < post_dialog_read_call_index,
    "item18b.a_reread_call_exists_strictly_after_the_choose_scope_call_site",
)

# Items 19-22 (static): StartRebuildControlGroups()'s own full source
# text (both refusal branches included) never references substantial-
# work identifiers -- a refused request performs zero provider
# acquisition, zero Master scope traversal, zero discovery, zero native
# work.
start_rebuild_func_text = production_text[start_rebuild_def_index:production_text.index("\nStartRebuildControlGroups()\n")]
for forbidden_token in (
    "collect_scope_master_wanted_folds",
    "acquire_master_index_via_qualified_authority",
    "NATIVE_REBUILD",
    "capture_tree",
    "GetRootControlGroup",
    "discover_rig_context",
):
    expect(
        forbidden_token not in start_rebuild_func_text,
        "item19_22.StartRebuildControlGroups_never_references_%s" % forbidden_token,
    )

# Item 23 (static): the only write-mode open() of the production log
# lives inside start(), strictly after StartRebuildControlGroups()'s own
# refusal checks, which only ever return before
# RebuildControlGroupsProductionRun is even constructed.
log_open_index = production_text.index('self.fp = open(\n                OUTPUT_PATH,\n                "w"\n            )')
expect(
    start_def_index < log_open_index < start_rebuild_def_index,
    "item23a.the_only_log_truncating_open_call_lives_inside_start_not_reachable_from_refusal",
)
expect(
    production_text.count('OUTPUT_PATH,\n                "w"') == 1,
    "item23b.exactly_one_write_mode_open_of_the_production_log_in_the_whole_file",
)

# Item 24 (static, partial -- see also git diff --stat / git diff review
# cited in INSTRUCTIONS.md/LEDGER.md for the full proof): the core
# mutation pipeline's own defining names are all still present and
# structurally unchanged in position relative to the guard.
for still_present in (
    "class RebuildControlGroupsProductionRun(",
    "def collect_scope_master_wanted_folds(",
    "def acquire_master_index_via_qualified_authority(",
    "def _resolve_selected_scope(",
):
    expect(
        still_present in production_text,
        "item24.core_mutation_pipeline_identifier_still_present_%s" % still_present.strip("( )"),
    )

# Independent-review correction proof (static): the classifier's own
# extracted source no longer contains any shot-NAME-based equality
# check -- only the canonical handle/native-pointer identity mechanism.
classify_source_text = extract(CLASSIFY_SCOPE_REQUEST_RANGE)
resolve_identity_source_text = extract(RESOLVE_SHOT_IDENTITY_RANGE)
for forbidden_token in ("GetName(", "selected_names", "all_names"):
    expect(
        forbidden_token not in classify_source_text,
        "correction.classifier_no_longer_uses_name_based_identity_%s" % forbidden_token.rstrip("("),
    )
expect(
    "GetHandle(" in resolve_identity_source_text and "native_ptr(" in resolve_identity_source_text,
    "correction.classifier_helper_uses_canonical_handle_and_native_pointer_identity",
)
sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))

if FAIL_COUNT[0]:
    sys.exit(1)
