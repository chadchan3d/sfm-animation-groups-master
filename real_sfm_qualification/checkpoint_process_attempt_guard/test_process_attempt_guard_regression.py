# -*- coding: utf-8 -*-
"""
Offline regression for the process-lifetime one-resource-consuming-attempt
guard added directly to production
(audit_external_runtime/Rebuild_Control_Groups_Normalizer.py), per the
Astra-authorized implementation contract (2026-09-24), following F2-R1-R3's
real-SFM FAIL result ("LEGITIMATE SAME-PROCESS REINVOCATION IS NOT RELIABLY
SUSTAINABLE").

This is a gate-only change: two refusal/arming hooks plus one marker-name
constant, one exception class, and two small helper functions
(_find_process_attempt_marker / _install_process_attempt_marker). No
existing execution semantics were touched -- the diff against the prior
committed production script is a pure, zero-deletion 204-line addition
(git diff --stat), independently confirmed below via source inspection
rather than trusted from that diff-stat claim alone.

No real SFM environment is available offline, but PySide's QtCore IS
importable standalone with the real embedded Python 2.7.5 (confirmed
throughout this project), so this test extracts the guard's own pure-
Python/Qt helper functions VERBATIM (by source line range, not retyped)
and exercises them against REAL QtCore.QObject instances -- the same
established pattern used by test_f2_r1_diagnostic_regression.py and
test_marker_persistence_probe_regression.py. Everything that cannot be
exercised as an isolated function (the two hook sites themselves, since
they live inside a class/function that depends on the full production
run machinery) is instead proven by static, source-position analysis
against the actual, deployed production script text -- reading the exact
same file this test pins by SHA-256, not a hand-copied paraphrase.

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
EXPECTED_PRODUCTION_SHA256 = "6170d2a248845281b5f5d38dfea4b9f2decf908b8e3b79e80f4ada18d2f54625"
EXPECTED_PRODUCTION_SHA256_BEFORE_GUARD = "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"

# Source line ranges for the guard's own pure-Python/Qt helpers, verified
# against the actual file via grep/Read immediately before writing this
# test (not assumed from memory).
MARKER_NAME_RANGE = (170, 172)
PROBE_ERROR_RANGE = (803, 804)
MARKER_ERROR_CLASS_RANGE = (807, 812)
TO_UNICODE_RANGE = (854, 864)
FIND_MARKER_RANGE = (5631, 5662)
INSTALL_MARKER_RANGE = (5665, 5715)

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
    "production.sha256_matches_pinned_post_guard_candidate",
)
expect(
    production_sha256 != EXPECTED_PRODUCTION_SHA256_BEFORE_GUARD,
    "production.sha256_differs_from_pre_guard_baseline_as_expected",
)


def extract(range_tuple, lines=production_lines):
    start, end = range_tuple
    return "\n".join(lines[start - 1:end])


sys.stdout.write("--- Extracted guard helpers (verbatim, real QtCore) ---\n")

ns = {"QtCore": QtCore}
exec(compile(extract(MARKER_NAME_RANGE), "<marker_name>", "exec"), ns)
exec(compile(extract(PROBE_ERROR_RANGE), "<probe_error>", "exec"), ns)
exec(compile(extract(MARKER_ERROR_CLASS_RANGE), "<marker_error>", "exec"), ns)
exec(compile(extract(TO_UNICODE_RANGE), "<to_unicode>", "exec"), ns)
exec(compile(extract(FIND_MARKER_RANGE), "<find_marker>", "exec"), ns)
exec(compile(extract(INSTALL_MARKER_RANGE), "<install_marker>", "exec"), ns)

NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME = ns["NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME"]
NormalizerProcessAttemptMarkerError = ns["NormalizerProcessAttemptMarkerError"]
_find_process_attempt_marker = ns["_find_process_attempt_marker"]
_install_process_attempt_marker = ns["_install_process_attempt_marker"]

expect(
    NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME
    == u"__SFM_REBUILD_CONTROL_GROUPS_PROCESS_ATTEMPT_CONSUMED__",
    "marker_name.exact_expected_literal",
)
expect(
    NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME
    != "__SFM_REBUILD_CONTROL_GROUPS_CONTEXTUALIZER_RUNNING__",
    "marker_name.independent_of_run_lock_name",
)

sys.stdout.write(
    "\n--- Behavioral: lookup against real QtCore.QObject instances ---\n"
)

main_window_1 = QtCore.QObject()
expect(
    _find_process_attempt_marker(main_window_1) is None,
    "find_marker.absent_on_fresh_main_window",
)

marker_1 = _install_process_attempt_marker(main_window_1)
expect(marker_1 is not None, "install_marker.returns_the_installed_marker")
expect(
    unicode(marker_1.objectName()) == NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME,
    "install_marker.installed_objectName_is_exact",
)

found_1 = _find_process_attempt_marker(main_window_1)
expect(
    found_1 is not None and unicode(found_1.objectName()) == NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME,
    "find_marker.present_after_install",
)

sys.stdout.write(
    "\n--- Item 12 & 13: no accumulation across repeated refusal-style lookups ---\n"
)

main_window_2 = QtCore.QObject()
lookup_a = _find_process_attempt_marker(main_window_2)
lookup_b = _find_process_attempt_marker(main_window_2)
expect(
    lookup_a is None and lookup_b is None,
    "find_marker.repeated_lookup_on_absent_marker_stays_absent",
)
expect(
    not hasattr(main_window_2, "_sfm_rebuild_control_groups_process_attempt_marker_keepalive"),
    "find_marker.repeated_lookup_never_creates_a_keepalive_list_ie_never_installs",
)
expect(
    len(main_window_2.findChildren(QtCore.QObject)) == 0,
    "find_marker.repeated_lookup_adds_zero_children_ie_zero_markers_created",
)

sys.stdout.write(
    "\n--- Item 14: marker carries no scene/controller/authority payload ---\n"
)

expect(
    type(marker_1) is QtCore.QObject,
    "install_marker.returned_object_is_a_plain_QObject_not_a_subclass",
)
keepalive_list = getattr(
    main_window_1,
    "_sfm_rebuild_control_groups_process_attempt_marker_keepalive",
    None,
)
expect(
    isinstance(keepalive_list, list) and len(keepalive_list) == 1,
    "install_marker.keepalive_list_has_exactly_one_entry_after_one_install",
)
expect(
    all(isinstance(item, QtCore.QObject) and type(item) is QtCore.QObject for item in keepalive_list),
    "install_marker.keepalive_list_contains_only_plain_QObject_instances",
)
for forbidden_token in ("DmeControlGroup", "aset", "capture_tree", "master_index", "GetRootControlGroup"):
    expect(
        forbidden_token not in extract(INSTALL_MARKER_RANGE) and forbidden_token not in extract(FIND_MARKER_RANGE),
        "install_marker.source_never_references_%s" % forbidden_token,
    )

sys.stdout.write(
    "\n--- Same-invocation gc.collect() survival (matches F2-R1-R3 hardening pattern) ---\n"
)

gc.collect()
expect(
    _find_process_attempt_marker(main_window_1) is not None,
    "find_marker.survives_an_explicit_same_invocation_gc_collect",
)

sys.stdout.write("\n--- Item 6: lookup error fails closed (never treated as absent) ---\n")


class _FakeMainWindowFindChildrenRaises(object):
    def findChildren(self, cls):
        raise RuntimeError("simulated findChildren failure")


raised_lookup = False
try:
    _find_process_attempt_marker(_FakeMainWindowFindChildrenRaises())
except NormalizerProcessAttemptMarkerError:
    raised_lookup = True
expect(raised_lookup, "find_marker.findChildren_exception_raises_MarkerError_not_absent")


class _PoisonedObjectName(object):
    def objectName(self):
        raise RuntimeError("simulated objectName() failure")


class _FakeMainWindowOneBadChild(object):
    def findChildren(self, cls):
        return [_PoisonedObjectName()]


raised_lookup_2 = False
try:
    _find_process_attempt_marker(_FakeMainWindowOneBadChild())
except NormalizerProcessAttemptMarkerError:
    raised_lookup_2 = True
expect(raised_lookup_2, "find_marker.objectName_exception_on_any_child_raises_MarkerError_fail_closed")

sys.stdout.write("\n--- Item 7: installation error fails closed ---\n")

ns_poisoned_install = {}


class _FakeQObjectRaisesOnSetObjectName(object):
    def __init__(self, parent):
        pass

    def setObjectName(self, name):
        raise RuntimeError("simulated setObjectName failure")


class _FakeQtCoreModuleBadSetObjectName(object):
    QObject = _FakeQObjectRaisesOnSetObjectName


ns_poisoned_install["QtCore"] = _FakeQtCoreModuleBadSetObjectName
exec(compile(extract(MARKER_NAME_RANGE), "<marker_name2>", "exec"), ns_poisoned_install)
exec(compile(extract(MARKER_ERROR_CLASS_RANGE), "<marker_error2>", "exec"), ns_poisoned_install)
exec(compile(extract(TO_UNICODE_RANGE), "<to_unicode2>", "exec"), ns_poisoned_install)
exec(compile(extract(FIND_MARKER_RANGE), "<find_marker2>", "exec"), ns_poisoned_install)
exec(compile(extract(INSTALL_MARKER_RANGE), "<install_marker2>", "exec"), ns_poisoned_install)

raised_install = False
try:
    ns_poisoned_install["_install_process_attempt_marker"](object())
except ns_poisoned_install["NormalizerProcessAttemptMarkerError"]:
    raised_install = True
expect(raised_install, "install_marker.setObjectName_exception_raises_MarkerError_fail_closed")

sys.stdout.write("\n--- Item 8: installation-verification failure fails closed ---\n")


class _AlwaysEmptyFindChildrenMainWindow(QtCore.QObject):
    # A REAL QtCore.QObject subclass (required: PySide's real
    # QtCore.QObject(parent) constructor rejects a non-QObject parent
    # outright, so a plain Python fake cannot reach the verify step at
    # all -- confirmed directly). Overriding findChildren() in a Python
    # subclass is itself a real, supported PySide pattern (confirmed
    # directly): calls made from our own Python code resolve to this
    # override, so real marker installation succeeds structurally
    # (a real child QObject really is parented and really is named)
    # while this override makes the internal post-install verify
    # lookup behave as if nothing were ever found.
    def findChildren(self, cls):
        return []


raised_verify = False
verify_message = ""
try:
    fake_for_verify = _AlwaysEmptyFindChildrenMainWindow()
    _install_process_attempt_marker(fake_for_verify)
except NormalizerProcessAttemptMarkerError as exc:
    raised_verify = True
    verify_message = unicode(exc)
expect(raised_verify, "install_marker.verify_step_finding_nothing_raises_MarkerError_fail_closed")
expect(
    "could not be verified" in verify_message,
    "install_marker.verify_failure_message_is_explicit",
)

sys.stdout.write(
    "\n--- Static source-position proofs against the actual deployed production script ---\n"
)

# Item 1 & 13 (static): _install_process_attempt_marker is called from
# exactly ONE call site in the whole file -- the arming block inside
# start() -- never from the refusal path in StartRebuildControlGroups(),
# so a dialog cancel or a refused invocation can never arm.
install_call_count = production_text.count("_install_process_attempt_marker(")
expect(
    install_call_count == 2,
    "script.install_marker_referenced_exactly_twice_total_def_plus_one_call_site",
)

def_index = production_text.index("def _install_process_attempt_marker(main_window):")
start_def_index = production_text.index("    def start(self):")
folds_call_index = production_text.index("self.collect_scope_master_wanted_folds()")
install_call_index = production_text.index(
    "_install_process_attempt_marker(\n                    guard_main_window\n                )"
)
expect(
    def_index < start_def_index < install_call_index < folds_call_index,
    "script.the_one_install_call_site_sits_between_start_def_and_folds_collection",
)

# Item 2 (static): a genuine bounded preflight rejection exists inside
# start() BEFORE the arm point (the no-open-document guard), proving
# that path leaves the allowance unused.
no_document_raise_index = production_text.index('"No SFM document is open."')
expect(
    start_def_index < no_document_raise_index < install_call_index,
    "script.no_open_document_bounded_rejection_sits_before_arming",
)

# Item 3 (static): the process-attempt-marker refusal check in
# StartRebuildControlGroups() is positioned before the _choose_scope()
# call site (the only such call site in the file).
choose_scope_call_index = production_text.index(") = _choose_scope()")
marker_check_index = production_text.index("process_attempt_marker_present = (")
start_rebuild_def_index = production_text.index("def StartRebuildControlGroups():")
expect(
    start_rebuild_def_index < marker_check_index < choose_scope_call_index,
    "script.public_entry_marker_refusal_check_precedes_choose_scope_call",
)

# Item 4 (static): the arm block's own recheck (_find_process_attempt_
# marker against guard_main_window) is textually positioned before its
# own install call.
arm_recheck_index = production_text.index(
    "guard_existing_marker = (\n                    _find_process_attempt_marker(\n                        guard_main_window\n                    )\n                )"
)
expect(
    start_def_index < arm_recheck_index < install_call_index,
    "script.arm_block_rechecks_marker_state_before_installing",
)

# Item 5 (static): nothing that yields the Qt event loop appears between
# the install call and the folds-collection call that immediately
# follows it.
between_install_and_folds = production_text[install_call_index:folds_call_index]
for forbidden_token in ("processEvents", "exec_(", "QTimer", "QMessageBox", "dialog."):
    expect(
        forbidden_token not in between_install_and_folds,
        "script.no_event_loop_yield_between_install_and_folds_collection_%s" % forbidden_token.rstrip("(").rstrip("."),
    )

# Items 9, 10, 11, 12 (static): the marker and its keepalive attribute
# are referenced ONLY by the constant definition, the exception-class
# comment, and the two helper functions -- never by any cleanup path
# (release_run_lock / final_report / abort), so no code path anywhere
# clears it once installed, regardless of outcome.
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
    expect(
        NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME not in text,
        "script.%s_never_references_the_process_attempt_marker_name" % label,
    )
    expect(
        "_sfm_rebuild_control_groups_process_attempt_marker_keepalive" not in text,
        "script.%s_never_references_the_marker_keepalive_attribute" % label,
    )

expect(
    production_text.count(".deleteLater()") == 1,
    "script.exactly_one_deleteLater_call_in_whole_file_ie_no_new_deletion_path_added",
)
expect(
    production_text.count("_sfm_rebuild_control_groups_process_attempt_marker_keepalive") == 2,
    "script.keepalive_identifier_appears_exactly_twice_ie_only_inside_install_marker",
)
expect(
    production_text.count("NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME") == 5,
    "script.marker_name_identifier_appears_exactly_five_times_ie_fully_accounted_for",
)

# Item 15 (static): the only write-mode open() of the production log
# lives inside start() (RebuildControlGroupsProductionRun's own method),
# strictly after StartRebuildControlGroups()'s refusal checks, which
# only ever return before RebuildControlGroupsProductionRun is even
# constructed -- so a refused invocation cannot reach it, and the prior
# production log is never truncated by a refusal.
log_open_index = production_text.index('self.fp = open(\n                OUTPUT_PATH,\n                "w"\n            )')
expect(
    start_def_index < log_open_index < start_rebuild_def_index,
    "script.the_only_log_truncating_open_call_lives_inside_start_not_reachable_from_refusal",
)
expect(
    production_text.count('OUTPUT_PATH,\n                "w"') == 1,
    "script.exactly_one_write_mode_open_of_the_production_log_in_the_whole_file",
)

# Item 16 (static): StartRebuildControlGroups()'s own source text (the
# whole function, refusal branches included) contains none of the
# substantial-work identifiers a refused invocation must never reach.
start_rebuild_func_text = production_text[start_rebuild_def_index:production_text.index("\nStartRebuildControlGroups()\n")]
for forbidden_token in (
    "collect_scope_master_wanted_folds",
    "acquire_master_index_via_qualified_authority",
    "NATIVE_REBUILD",
    "capture_tree",
    "GetRootControlGroup",
):
    expect(
        forbidden_token not in start_rebuild_func_text,
        "script.StartRebuildControlGroups_never_references_%s" % forbidden_token,
    )
# And confirm the refusal branch itself performs no more than the
# lookup + user-facing message + return (no RebuildControlGroupsProductionRun
# construction reachable from either marker-error or marker-present branch).
refusal_branch_text = start_rebuild_func_text[
    start_rebuild_func_text.index("process_attempt_marker_present = ("):
    start_rebuild_func_text.index("    try:\n        (\n            scope_mode,")
]
expect(
    "RebuildControlGroupsProductionRun(" not in refusal_branch_text,
    "script.refusal_branch_never_constructs_the_production_run_object",
)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))

if FAIL_COUNT[0]:
    sys.exit(1)
