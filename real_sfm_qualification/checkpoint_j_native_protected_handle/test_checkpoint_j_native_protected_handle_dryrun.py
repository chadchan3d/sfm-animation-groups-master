# -*- coding: utf-8 -*-
"""
Offline regression for Checkpoint J's own reusable definitions
(Checkpoint_J_Native_Protected_Handle.py -- source-review-revision-2,
instance-level native-rebuild wrap + fail-closed run_target_transaction
guard + mechanically-pinned workload identity + derived handle-hygiene
gate + actual authority-runtime-identity gates + protected-Master-SHA
gate).

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_checkpoint_j_native_protected_handle_dryrun.py

Never touches the live SFM Master. Uses only disposable temp files created
and deleted by this test itself, and fake sfmApp/vs/sfmClipEditor/QtCore
object models for the SFM-only helpers (same technique Checkpoint G's own
test suite already uses).

Technique (same discipline every earlier checkpoint in this project uses):
  every reusable, non-SFM-dependent block of the real script is extracted
  VERBATIM by exact, pinned line range and exec()'d into an isolated
  namespace, so what this suite exercises is the ACTUAL deployed logic,
  never a reimplementation of it. The remaining, SFM-dependent top-level
  flow (sfmApp/PySide-driven dialog polling) cannot run offline; its own
  syntax compatibility is instead proven directly, by compiling the whole
  file under the real embedded Python 2.7.5 (below).
"""
import ctypes
import hashlib
import os
import py_compile
import sys
import tempfile
import time

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Checkpoint_J_Native_Protected_Handle.py")
EXPECTED_SCRIPT_SHA256 = "9ac2c85dad7c3eea41dcce815fe16bb122f860d9280713b99a84c8da1754903d"
EXPECTED_SCRIPT_SIZE = 77509

# Pinned, exact line ranges (1-indexed, inclusive) of the reusable blocks
# -- see the checkpoint script's own "BEGIN/END PINNED BLOCK" markers at
# these boundaries (or, for small stable pre-existing helpers that predate
# this checkpoint's own pinned-block convention, a directly-confirmed
# def-to-def range).
EXCEPTIONS_RANGE = (205, 226)
FACT_HELPERS_RANGE = (245, 273)
PROBE_HELPER_RANGE = (284, 409)
WRAPPER_INSTALLER_RANGE = (420, 535)
INSTANCE_LOCATOR_RANGE = (565, 640)
GUARD_RANGE = (665, 718)
WORKLOAD_IDENTITY_RANGE = (730, 847)
EVENT_ORDER_AND_VERDICT_RANGE = (858, 1036)

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label, detail=None):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s%s\n" % (label, ("" if detail is None else " -- %r" % (detail,))))
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s%s\n" % (label, ("" if detail is None else " -- %r" % (detail,))))


def read_script_lines():
    with open(SCRIPT_PATH, "rb") as f:
        data = f.read()
    return data, data.decode("ascii").splitlines(True)


def extract_block(all_lines, line_range):
    start, end = line_range
    return "".join(all_lines[start - 1:end])


# ---------------------------------------------------------------------------
# 0. Identity / syntax compatibility.
# ---------------------------------------------------------------------------

script_bytes, script_lines = read_script_lines()
script_sha = hashlib.sha256(script_bytes).hexdigest()
expect(script_sha == EXPECTED_SCRIPT_SHA256, "identity.script_sha256_matches_pinned", script_sha)
expect(len(script_bytes) == EXPECTED_SCRIPT_SIZE, "identity.script_size_matches_pinned", len(script_bytes))

_compiled_ok = True
_compiled_exc = None
try:
    py_compile.compile(SCRIPT_PATH, doraise=True)
except Exception as exc:
    _compiled_ok = False
    _compiled_exc = exc
expect(_compiled_ok, "identity.script_compiles_under_embedded_python27", _compiled_exc)
try:
    _pyc_path = SCRIPT_PATH + "c"
    if os.path.exists(_pyc_path):
        os.remove(_pyc_path)
except Exception:
    pass

exceptions_block_text = extract_block(script_lines, EXCEPTIONS_RANGE)
fact_helpers_block_text = extract_block(script_lines, FACT_HELPERS_RANGE)
probe_block_text = extract_block(script_lines, PROBE_HELPER_RANGE)
wrapper_block_text = extract_block(script_lines, WRAPPER_INSTALLER_RANGE)
instance_locator_block_text = extract_block(script_lines, INSTANCE_LOCATOR_RANGE)
guard_block_text = extract_block(script_lines, GUARD_RANGE)
workload_identity_block_text = extract_block(script_lines, WORKLOAD_IDENTITY_RANGE)
verdict_block_text = extract_block(script_lines, EVENT_ORDER_AND_VERDICT_RANGE)

expect("class CheckpointJError" in exceptions_block_text and "class CheckpointJInstrumentationNotReadyError" in exceptions_block_text,
       "identity.exceptions_range_is_correctly_pinned")
expect("def b_to_unicode" in fact_helpers_block_text and "def b_name" in fact_helpers_block_text and "def b_native_ptr" in fact_helpers_block_text,
       "identity.fact_helpers_range_is_correctly_pinned")
expect("PROBE_GENERIC_READ" in probe_block_text and "def matrix_all_probe_handles_closed" in probe_block_text,
       "identity.probe_helper_range_is_correctly_pinned")
expect("def make_wrappers" in wrapper_block_text and "return missing" in wrapper_block_text,
       "identity.wrapper_installer_range_is_correctly_pinned")
expect("def locate_run_instance" in instance_locator_block_text and "def wrap_run_instance_native_rebuild" in instance_locator_block_text,
       "identity.instance_locator_range_is_correctly_pinned")
expect("def make_run_target_transaction_guard" in guard_block_text and "def install_run_target_transaction_guard" in guard_block_text,
       "identity.guard_range_is_correctly_pinned")
expect("def resolve_unique_shot" in workload_identity_block_text and "def production_log_single_native_rebuild" in workload_identity_block_text,
       "identity.workload_identity_range_is_correctly_pinned")
expect("def validate_event_order" in verdict_block_text and "def find_protected_master_sha256_ok" in verdict_block_text and "def classify_j_verdict" in verdict_block_text,
       "identity.verdict_range_is_correctly_pinned")

# Static structural proof (this project's established technique when a
# purely behavioral proof would be ambiguous): in probe_access's SOURCE
# TEXT, every failure-branch `return` that reports success=False occurs
# BEFORE the CloseHandle call textually -- i.e. a failed handle is
# structurally unreachable to CloseHandle.
_probe_access_start = probe_block_text.find("def probe_access(")
_probe_access_body = probe_block_text[_probe_access_start:probe_block_text.find("\n\ndef probe_matrix", _probe_access_start)]
_fail_return_idx = _probe_access_body.find('"success": False,')
_close_handle_idx = _probe_access_body.find("_probe_close_handle(handle)")
expect(_fail_return_idx != -1 and _close_handle_idx != -1 and _fail_return_idx < _close_handle_idx,
       "probe_access.failure_return_precedes_close_handle_call_in_source",
       (_fail_return_idx, _close_handle_idx))

# Static structural proof that a failed instance-wrap/guard-not-ready
# state mechanically raises rather than silently continuing (guard
# behavior, not a raise in the outer script -- see round-2 correction).
expect("raise CheckpointJInstrumentationNotReadyError(" in guard_block_text,
       "identity.guard_mechanically_raises_when_not_ready")

# Static structural proof that the J1 baseline handle-hygiene check is
# textually positioned BEFORE the production exec() call -- i.e. it is
# genuinely a pre-production gate, not merely present somewhere in the
# file.
_j1_hygiene_idx = script_bytes.find(b'"j1.baseline_handles_all_closed"')
_exec_production_idx = script_bytes.find(b"exec(compile(production_bytes,")
expect(_j1_hygiene_idx != -1 and _exec_production_idx != -1 and _j1_hygiene_idx < _exec_production_idx,
       "identity.j1_baseline_hygiene_check_precedes_production_exec_in_source",
       (_j1_hygiene_idx, _exec_production_idx))

ns = {}
# The pinned blocks are extracted by exact line range and therefore do not
# carry the real script's own top-of-file imports; the names each block
# actually uses at module scope (`ctypes`, `time`) are supplied here
# exactly as the real script imports them -- nothing else is added.
exec(compile(exceptions_block_text, "<pinned_exceptions>", "exec"), ns)
exec(compile("import ctypes\n" + probe_block_text, "<pinned_probe_helper>", "exec"), ns)
exec(compile("import time\n" + wrapper_block_text, "<pinned_wrapper_installer>", "exec"), ns)
exec(compile(fact_helpers_block_text, "<pinned_fact_helpers>", "exec"), ns)


class _FakeQtCoreModule(object):
    class QObject(object):
        pass


FAKE_QTCORE = _FakeQtCoreModule()
ns["QtCore"] = FAKE_QTCORE
exec(compile(instance_locator_block_text, "<pinned_instance_locator>", "exec"), ns)
exec(compile("import time\n" + guard_block_text, "<pinned_guard>", "exec"), ns)
exec(compile("import os\n" + workload_identity_block_text, "<pinned_workload_identity>", "exec"), ns)
exec(compile(verdict_block_text, "<pinned_verdict_block>", "exec"), ns)

probe_access = ns["probe_access"]
probe_matrix = ns["probe_matrix"]
matrix_is_fully_open = ns["matrix_is_fully_open"]
matrix_is_exactly_protected = ns["matrix_is_exactly_protected"]
matrix_all_probe_handles_closed = ns["matrix_all_probe_handles_closed"]
make_wrappers = ns["make_wrappers"]
locate_run_instance = ns["locate_run_instance"]
wrap_run_instance_native_rebuild = ns["wrap_run_instance_native_rebuild"]
make_run_target_transaction_guard = ns["make_run_target_transaction_guard"]
install_run_target_transaction_guard = ns["install_run_target_transaction_guard"]
resolve_unique_shot = ns["resolve_unique_shot"]
normalize_path_for_comparison = ns["normalize_path_for_comparison"]
path_matches_baseline = ns["path_matches_baseline"]
resolve_fixture_basename = ns["resolve_fixture_basename"]
canonical_single_shot_match = ns["canonical_single_shot_match"]
work_inventory_matches_single_target = ns["work_inventory_matches_single_target"]
production_log_scope_confirmed = ns["production_log_scope_confirmed"]
production_log_single_target_transaction = ns["production_log_single_target_transaction"]
production_log_single_native_rebuild = ns["production_log_single_native_rebuild"]
validate_event_order = ns["validate_event_order"]
find_protected_master_sha256_ok = ns["find_protected_master_sha256_ok"]
classify_j_verdict = ns["classify_j_verdict"]
CheckpointJInstrumentationNotReadyError = ns["CheckpointJInstrumentationNotReadyError"]
ERROR_SHARING_VIOLATION = ns["ERROR_SHARING_VIOLATION"]
PROBE_GENERIC_READ = ns["PROBE_GENERIC_READ"]
PROBE_GENERIC_WRITE = ns["PROBE_GENERIC_WRITE"]
PROBE_FILE_SHARE_READ = ns["PROBE_FILE_SHARE_READ"]
PROBE_OPEN_EXISTING = ns["PROBE_OPEN_EXISTING"]
PROBE_FILE_ATTRIBUTE_NORMAL = ns["PROBE_FILE_ATTRIBUTE_NORMAL"]
b_name = ns["b_name"]
b_native_ptr = ns["b_native_ptr"]

expect(ERROR_SHARING_VIOLATION == 32, "identity.error_sharing_violation_constant", ERROR_SHARING_VIOLATION)


# ---------------------------------------------------------------------------
# 1. Disposable-file Win32 share-matrix tests (real CreateFileW behavior,
#    never the live Master), including the CloseHandle-result tracking
#    and derived handle-hygiene gate.
# ---------------------------------------------------------------------------

_tmp_fd, _tmp_path = tempfile.mkstemp(prefix="sfm_checkpoint_j_dryrun_", suffix=".tmp")
os.close(_tmp_fd)
with open(_tmp_path, "wb") as f:
    f.write(b"disposable checkpoint J fixture content\n")

try:
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _open_protection_handle = _kernel32.CreateFileW
    _open_protection_handle.argtypes = [
        ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
        ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
    ]
    _open_protection_handle.restype = ctypes.c_void_p
    _close_handle = _kernel32.CloseHandle
    _close_handle.argtypes = [ctypes.c_void_p]
    _close_handle.restype = ctypes.c_int
    _get_process_handle_count = _kernel32.GetProcessHandleCount
    _get_process_handle_count.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    _get_process_handle_count.restype = ctypes.c_int

    def current_process_handle_count():
        count = ctypes.c_ulong(0)
        ok = _get_process_handle_count(_kernel32.GetCurrentProcess(), ctypes.byref(count))
        if not ok:
            return None
        return count.value

    # --- Matrix 1: no restrictive handle -> READ/WRITE/DELETE all succeed,
    #     and every successful probe's OWN CloseHandle call also
    #     succeeded (recorded, never assumed). ---
    m1 = probe_matrix(_tmp_path)
    expect(m1["read"]["success"] is True, "share_matrix.no_handle_read_succeeds", m1["read"])
    expect(m1["write"]["success"] is True, "share_matrix.no_handle_write_succeeds", m1["write"])
    expect(m1["delete"]["success"] is True, "share_matrix.no_handle_delete_succeeds", m1["delete"])
    expect(matrix_is_fully_open(m1) is True, "share_matrix.no_handle_matrix_is_fully_open")
    expect(matrix_is_exactly_protected(m1) is False, "share_matrix.no_handle_matrix_is_not_protected")
    expect(m1["read"]["close_attempted"] is True and m1["read"]["close_succeeded"] is True,
           "share_matrix.no_handle_read_probe_close_recorded_as_succeeded", m1["read"])
    expect(matrix_all_probe_handles_closed(m1) is True, "share_matrix.no_handle_matrix_all_probe_handles_closed")

    # --- Matrix 2: production's own exact protection handle shape
    #     (GENERIC_READ, FILE_SHARE_READ only, OPEN_EXISTING) held ->
    #     READ succeeds, WRITE/DELETE fail with EXACT sharing violation;
    #     failed probes never attempted CloseHandle at all. ---
    protection_handle = _open_protection_handle(
        _tmp_path, PROBE_GENERIC_READ, PROBE_FILE_SHARE_READ, None,
        PROBE_OPEN_EXISTING, PROBE_FILE_ATTRIBUTE_NORMAL, None,
    )
    expect(protection_handle not in (None, ctypes.c_void_p(-1).value), "share_matrix.protection_handle_opened")

    m2 = probe_matrix(_tmp_path)
    expect(m2["read"]["success"] is True, "share_matrix.protected_read_succeeds", m2["read"])
    expect(m2["write"]["success"] is False, "share_matrix.protected_write_fails", m2["write"])
    expect(m2["write"]["win_error"] == ERROR_SHARING_VIOLATION, "share_matrix.protected_write_fails_with_exact_sharing_violation", m2["write"]["win_error"])
    expect(m2["write"]["close_attempted"] is False and m2["write"]["close_succeeded"] is None,
           "share_matrix.protected_write_failure_never_attempted_close", m2["write"])
    expect(m2["delete"]["success"] is False, "share_matrix.protected_delete_fails", m2["delete"])
    expect(m2["delete"]["win_error"] == ERROR_SHARING_VIOLATION, "share_matrix.protected_delete_fails_with_exact_sharing_violation", m2["delete"]["win_error"])
    expect(matrix_is_exactly_protected(m2) is True, "share_matrix.protected_matrix_classified_exactly_protected")
    expect(matrix_is_fully_open(m2) is False, "share_matrix.protected_matrix_is_not_fully_open")
    expect(matrix_all_probe_handles_closed(m2) is True,
           "share_matrix.protected_matrix_all_probe_handles_closed_read_only_success_case", m2)

    # --- Close the protection handle -> Matrix 3: READ/WRITE/DELETE all
    #     succeed again. ---
    _close_handle(protection_handle)
    m3 = probe_matrix(_tmp_path)
    expect(matrix_is_fully_open(m3) is True, "share_matrix.after_release_matrix_is_fully_open_again", m3)
    expect(matrix_is_exactly_protected(m3) is False, "share_matrix.after_release_matrix_is_not_protected")
    expect(matrix_all_probe_handles_closed(m3) is True, "share_matrix.after_release_matrix_all_probe_handles_closed")

    # --- Ambiguous-denial discrimination: a matrix reporting a
    #     NON-sharing-violation denial must NOT be classified protected. ---
    ambiguous_matrix = {
        "read": {"success": True, "win_error": None, "close_attempted": True, "close_succeeded": True, "close_error": None},
        "write": {"success": False, "win_error": 5, "close_attempted": False, "close_succeeded": None, "close_error": None},  # ERROR_ACCESS_DENIED
        "delete": {"success": False, "win_error": 5, "close_attempted": False, "close_succeeded": None, "close_error": None},
    }
    expect(matrix_is_exactly_protected(ambiguous_matrix) is False, "share_matrix.ambiguous_access_denied_not_counted_as_protected")

    # --- Handle-hygiene gate is DERIVED, never a hard-coded literal:
    #     synthesize a matrix whose read probe opened successfully but
    #     whose CloseHandle call itself failed, and prove
    #     matrix_all_probe_handles_closed() correctly flags it, and that
    #     an absent/falsy matrix is never silently treated as clean. ---
    leak_matrix = {
        "read": {"success": True, "win_error": None, "close_attempted": True, "close_succeeded": False, "close_error": 6},  # ERROR_INVALID_HANDLE
        "write": {"success": False, "win_error": 32, "close_attempted": False, "close_succeeded": None, "close_error": None},
        "delete": {"success": False, "win_error": 32, "close_attempted": False, "close_succeeded": None, "close_error": None},
    }
    expect(matrix_all_probe_handles_closed(leak_matrix) is False,
           "share_matrix.synthetic_close_handle_failure_is_detected_as_a_leak", leak_matrix)
    expect(matrix_all_probe_handles_closed(None) is False, "share_matrix.missing_matrix_never_silently_passes_hygiene_gate")
    expect(matrix_all_probe_handles_closed({}) is False, "share_matrix.empty_matrix_never_silently_passes_hygiene_gate")

    # --- Specifically: a J1 BASELINE matrix containing a successful-
    #     open/failed-close result must be rejected by the same hygiene
    #     gate the real script requires ("j1.baseline_handles_all_closed")
    #     before it will ever exec() production -- proving the pre-
    #     production gate's own underlying condition actually fires for
    #     exactly the scenario it exists to catch (a leaked baseline
    #     probe handle that could conflict with production's own
    #     subsequent protection handle). ---
    j1_leak_matrix = {
        "read": {"success": True, "win_error": None, "close_attempted": True, "close_succeeded": True, "close_error": None},
        "write": {"success": True, "win_error": None, "close_attempted": True, "close_succeeded": False, "close_error": 6},
        "delete": {"success": True, "win_error": None, "close_attempted": True, "close_succeeded": True, "close_error": None},
    }
    expect(matrix_all_probe_handles_closed(j1_leak_matrix) is False,
           "j1_baseline_hygiene.leaked_baseline_probe_handle_is_rejected_at_the_pre_production_gate", j1_leak_matrix)

    # --- Force a REAL synthetic CloseHandle failure through probe_access
    #     itself (not just a hand-built dict): monkeypatch this pinned
    #     namespace's own _probe_close_handle to fail exactly once, and
    #     confirm probe_access faithfully records close_succeeded=False
    #     with a real captured error code, and that the resulting matrix
    #     correctly fails matrix_all_probe_handles_closed(). ---
    _real_probe_close_handle = ns["_probe_close_handle"]
    _force_close_failure = [True]

    def _failing_close_handle(handle):
        if _force_close_failure[0]:
            _force_close_failure[0] = False
            ctypes.set_last_error(6)  # ERROR_INVALID_HANDLE
            return 0
        return _real_probe_close_handle(handle)

    ns["_probe_close_handle"] = _failing_close_handle
    forced_close_failure_result = probe_access(_tmp_path, PROBE_GENERIC_READ)
    ns["_probe_close_handle"] = _real_probe_close_handle
    expect(forced_close_failure_result["success"] is True, "share_matrix.forced_close_failure_open_itself_still_succeeded", forced_close_failure_result)
    expect(forced_close_failure_result["close_succeeded"] is False, "share_matrix.forced_close_failure_recorded_as_failed", forced_close_failure_result)
    expect(forced_close_failure_result["close_error"] == 6, "share_matrix.forced_close_failure_records_real_error_code", forced_close_failure_result["close_error"])
    forced_leak_matrix = {"read": forced_close_failure_result, "write": {"success": False, "win_error": 32, "close_attempted": False, "close_succeeded": None, "close_error": None}, "delete": {"success": False, "win_error": 32, "close_attempted": False, "close_succeeded": None, "close_error": None}}
    expect(matrix_all_probe_handles_closed(forced_leak_matrix) is False,
           "share_matrix.forced_close_failure_fails_the_hygiene_gate_end_to_end", forced_leak_matrix)

    # --- No file content, timestamp, or existence mutation occurred. ---
    with open(_tmp_path, "rb") as f:
        _content_after = f.read()
    expect(_content_after == b"disposable checkpoint J fixture content\n", "share_matrix.disposable_fixture_content_unchanged")

    # --- Every successful probe handle is actually closed: run a burst of
    #     successful probes and confirm the process handle count does not
    #     grow (a leak would grow it by roughly one per unclosed handle). ---
    handle_count_before = current_process_handle_count()
    for _ in range(2000):
        probe_access(_tmp_path, PROBE_GENERIC_READ)
    handle_count_after = current_process_handle_count()
    if handle_count_before is not None and handle_count_after is not None:
        delta = handle_count_after - handle_count_before
        expect(delta < 50, "share_matrix.no_handle_leak_across_2000_successful_probes", delta)
    else:
        expect(False, "share_matrix.no_handle_leak_across_2000_successful_probes (GetProcessHandleCount unavailable)")

    # --- Failed probes never grow the handle count either. ---
    protection_handle_2 = _open_protection_handle(
        _tmp_path, PROBE_GENERIC_READ, PROBE_FILE_SHARE_READ, None,
        PROBE_OPEN_EXISTING, PROBE_FILE_ATTRIBUTE_NORMAL, None,
    )
    handle_count_before_fail = current_process_handle_count()
    for _ in range(2000):
        probe_access(_tmp_path, PROBE_GENERIC_WRITE)
    handle_count_after_fail = current_process_handle_count()
    _close_handle(protection_handle_2)
    if handle_count_before_fail is not None and handle_count_after_fail is not None:
        delta_fail = handle_count_after_fail - handle_count_before_fail
        expect(delta_fail < 50, "share_matrix.no_handle_leak_across_2000_failed_probes", delta_fail)
    else:
        expect(False, "share_matrix.no_handle_leak_across_2000_failed_probes (GetProcessHandleCount unavailable)")

finally:
    try:
        os.remove(_tmp_path)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 2a. Historical-bug reproduction: reproduces the exact Checkpoint O2
#     defect (documented in checkpoint_o2_r1/O2_R1_NATIVE_TIMING_
#     CORRECTION.md) -- a late CLASS-level prepare_native_callback patch,
#     installed AFTER a synthetic source's own module-level code has
#     already synchronously constructed a run instance and assigned its
#     self.rebuild (exactly mirroring real production's own
#     StartRebuildControlGroups() -> derive_paths() ->
#     prepare_native_callback() chain, which completes before exec()
#     returns) -- gets ZERO interceptions. Then demonstrates that the
#     ACTUAL, deployed locate_run_instance()/wrap_run_instance_native_
#     rebuild() functions (extracted verbatim above), applied to that
#     SAME already-constructed instance, get exactly ONE interception
#     while preserving argument and return-value identity.
# ---------------------------------------------------------------------------


class FakeMainWindow(object):
    def __init__(self, children):
        self._children = list(children)

    def findChildren(self, cls):
        return list(self._children)


HISTORICAL_BUG_SOURCE = """
RUN_LOCK_NAME = "checkpoint_j_test_run_lock"


def native_rebuild_native_impl(aset_ptr):
    return ("NATIVE_ORIGINAL", aset_ptr)


class RebuildControlGroupsProductionRun(object):
    def objectName(self):
        return RUN_LOCK_NAME

    def prepare_native_callback(self):
        self.rebuild = native_rebuild_native_impl
        return "PREPARED"


# Simulates production's own top-level StartRebuildControlGroups(): the
# run instance is constructed and prepare_native_callback() is called
# SYNCHRONOUSLY, during this module's own exec() -- exactly like the real
# Normalizer -- so self.rebuild is already a plain INSTANCE attribute
# before this exec() call ever returns.
_the_run_instance = RebuildControlGroupsProductionRun()
_the_run_instance.prepare_native_callback()
"""

hist_ns = {}
exec(compile(HISTORICAL_BUG_SOURCE, "<historical_bug_repro>", "exec"), hist_ns)

# --- Reproduce the OLD (buggy, rejected) mechanism: patch
#     prepare_native_callback at the CLASS level AFTER exec() has already
#     returned. ---
RunClassHist = hist_ns["RebuildControlGroupsProductionRun"]
original_prepare_hist = RunClassHist.prepare_native_callback
buggy_call_count = [0]


def buggy_wrapped_prepare(self, *a, **kw):
    result = original_prepare_hist(self, *a, **kw)
    original_rebuild = self.rebuild

    def observed(aset_ptr):
        buggy_call_count[0] += 1
        return original_rebuild(aset_ptr)

    self.rebuild = observed
    return result


RunClassHist.prepare_native_callback = buggy_wrapped_prepare

_hist_call_result = hist_ns["_the_run_instance"].rebuild(0xAAAA)
expect(buggy_call_count[0] == 0,
       "historical_bug.late_class_level_patch_gets_zero_interceptions", buggy_call_count[0])
expect(_hist_call_result == ("NATIVE_ORIGINAL", 0xAAAA),
       "historical_bug.instance_still_calls_real_native_impl_unintercepted", _hist_call_result)

# --- Now apply the ACTUAL, deployed instance-level mechanism against the
#     SAME already-constructed instance. ---
fake_main_window_hist = FakeMainWindow([hist_ns["_the_run_instance"]])
located = locate_run_instance(fake_main_window_hist, hist_ns["RUN_LOCK_NAME"])
expect(located is hist_ns["_the_run_instance"], "historical_bug.locate_run_instance_finds_the_already_constructed_instance")

fix_events = []
fix_state = {"protection_active": False, "protected_path": None, "native_rebuild_wrapper_call_count": 0}
fix_wrap_ok = wrap_run_instance_native_rebuild(located, fix_events, fix_state)
expect(fix_wrap_ok is True, "historical_bug.instance_level_wrap_installs_successfully")

_fix_call_result = located.rebuild(0xBBBB)
expect(fix_state["native_rebuild_wrapper_call_count"] == 1,
       "historical_bug.instance_level_wrap_gets_exactly_one_interception", fix_state["native_rebuild_wrapper_call_count"])
expect(_fix_call_result == ("NATIVE_ORIGINAL", 0xBBBB),
       "historical_bug.instance_level_wrap_preserves_argument_and_return_value_identity", _fix_call_result)

expect(locate_run_instance(FakeMainWindow([]), "checkpoint_j_test_run_lock") is None,
       "locate_run_instance.zero_matches_returns_none")
expect(locate_run_instance(FakeMainWindow([hist_ns["_the_run_instance"], hist_ns["_the_run_instance"]]), "checkpoint_j_test_run_lock") is None,
       "locate_run_instance.ambiguous_multiple_matches_returns_none")
expect(locate_run_instance(fake_main_window_hist, None) is None,
       "locate_run_instance.none_run_lock_name_returns_none")
expect(wrap_run_instance_native_rebuild(None, [], dict(fix_state)) is False,
       "wrap_run_instance_native_rebuild.none_instance_returns_false")


class _InstanceWithoutRebuild(object):
    pass


expect(wrap_run_instance_native_rebuild(_InstanceWithoutRebuild(), [], dict(fix_state, native_rebuild_wrapper_call_count=0)) is False,
       "wrap_run_instance_native_rebuild.instance_missing_rebuild_attribute_returns_false")


# ---------------------------------------------------------------------------
# 2b. run_target_transaction fail-closed guard regression: setup-succeeds
#     path (original called exactly once, argument/return identity
#     preserved) and setup-fails path (original called zero times, the
#     guard raises instead).
# ---------------------------------------------------------------------------

GUARD_FAKE_SOURCE = """
class RebuildControlGroupsProductionRun(object):
    def __init__(self):
        self.transaction_calls = []

    def run_target_transaction(self, shot_record, target):
        self.transaction_calls.append((shot_record, target))
        return ("TRANSACTION_RESULT", shot_record, target)
"""

guard_ns = {}
exec(compile(GUARD_FAKE_SOURCE, "<guard_fake_production>", "exec"), guard_ns)

# --- Setup FAILS: instrumentation_ready stays False -- the guard must
#     raise and the ORIGINAL method must never be called at all. ---
guard_events_fail = []
guard_state_fail = {"instrumentation_ready": False}
guard_installed_fail = install_run_target_transaction_guard(guard_ns, guard_events_fail, guard_state_fail)
expect(guard_installed_fail is True, "guard.installs_successfully_against_the_real_class")

instance_fail = guard_ns["RebuildControlGroupsProductionRun"]()
_raised = False
try:
    instance_fail.run_target_transaction({"name": u"shot9"}, {"name": u"krystalv21"})
except CheckpointJInstrumentationNotReadyError:
    _raised = True
expect(_raised is True, "guard.setup_failed_path_raises_instrumentation_not_ready")
expect(instance_fail.transaction_calls == [], "guard.setup_failed_path_original_method_never_called", instance_fail.transaction_calls)
expect(guard_state_fail.get("blocked_call_count") == 1, "guard.setup_failed_path_increments_blocked_call_count", guard_state_fail.get("blocked_call_count"))
blocked_events = [e for e in guard_events_fail if e["kind"] == "target_transaction_blocked_not_ready"]
expect(len(blocked_events) == 1, "guard.setup_failed_path_records_exactly_one_blocked_event")

# A second attempt while still not ready must ALSO be blocked (never
# "only blocks once").
_raised_again = False
try:
    instance_fail.run_target_transaction({"name": u"shot9"}, {"name": u"krystalv21"})
except CheckpointJInstrumentationNotReadyError:
    _raised_again = True
expect(_raised_again is True, "guard.remains_blocked_on_every_call_while_not_ready")
expect(guard_state_fail.get("blocked_call_count") == 2, "guard.blocked_call_count_increments_on_every_blocked_attempt", guard_state_fail.get("blocked_call_count"))

# --- Setup SUCCEEDS: instrumentation_ready True -- the guard forwards to
#     the ORIGINAL method exactly once, with identical arguments, and
#     returns its exact result. ---
guard_events_ok = []
guard_state_ok = {"instrumentation_ready": True}
guard_ns_ok = {}
exec(compile(GUARD_FAKE_SOURCE, "<guard_fake_production_ok>", "exec"), guard_ns_ok)
guard_installed_ok = install_run_target_transaction_guard(guard_ns_ok, guard_events_ok, guard_state_ok)
expect(guard_installed_ok is True, "guard.installs_successfully_second_instance")

instance_ok = guard_ns_ok["RebuildControlGroupsProductionRun"]()
shot_record_arg = {"name": u"shot9"}
target_arg = {"name": u"krystalv21"}
result_ok = instance_ok.run_target_transaction(shot_record_arg, target_arg)
expect(result_ok == ("TRANSACTION_RESULT", shot_record_arg, target_arg),
       "guard.setup_ready_path_forwards_identical_arguments_and_returns_exact_result", result_ok)
expect(instance_ok.transaction_calls == [(shot_record_arg, target_arg)],
       "guard.setup_ready_path_original_method_called_exactly_once", instance_ok.transaction_calls)
expect(guard_state_ok.get("blocked_call_count", 0) == 0, "guard.setup_ready_path_never_blocks")
expect(guard_state_ok.get("target_transaction_call_count") == 1, "guard.setup_ready_path_records_exactly_one_call_count")
call_events_ok = [e for e in guard_events_ok if e["kind"] == "target_transaction_call"]
expect(len(call_events_ok) == 1 and call_events_ok[0]["shot_name"] == u"shot9" and call_events_ok[0]["target_name"] == u"krystalv21",
       "guard.setup_ready_path_records_exact_shot_and_target_identity", call_events_ok)

expect(install_run_target_transaction_guard({}, [], {}) is False,
       "guard.missing_run_class_fails_to_install")
_ns_no_method = {"RebuildControlGroupsProductionRun": type("Empty", (object,), {})}
expect(install_run_target_transaction_guard(_ns_no_method, [], {}) is False,
       "guard.class_without_run_target_transaction_fails_to_install")


# ---------------------------------------------------------------------------
# 2c. Full wrapper / event-order regression against a SYNTHETIC
#     fake-production module (never the real Normalizer), reusing the SAME
#     real disposable temp-file mechanics as section 1 so the
#     protected-matrix probes inside the wrappers observe REAL Windows
#     sharing semantics, not a mock. The fake module auto-constructs its
#     own run instance at module level (mirroring real production's
#     synchronous construction), located and wrapped via the SAME
#     locate_run_instance()/wrap_run_instance_native_rebuild() functions
#     exercised in 2a, and the fail-closed guard from 2b is installed and
#     driven through the full happy path together with the other four
#     wraps.
# ---------------------------------------------------------------------------

_tmp_fd2, _fake_master_path = tempfile.mkstemp(prefix="sfm_checkpoint_j_dryrun_fakemaster_", suffix=".tmp")
os.close(_tmp_fd2)
with open(_fake_master_path, "wb") as f:
    f.write(b"fake master fixture\n")

FAKE_PRODUCTION_SOURCE = """
import ctypes

RUN_LOCK_NAME = "checkpoint_j_test_run_lock_2c"

_GENERIC_READ = 0x80000000
_FILE_SHARE_READ = 0x00000001
_OPEN_EXISTING = 3
_FILE_ATTRIBUTE_NORMAL = 0x00000080

_fake_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_fake_create_file_w = _fake_kernel32.CreateFileW
_fake_create_file_w.argtypes = [
    ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
    ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
]
_fake_create_file_w.restype = ctypes.c_void_p
_fake_close_handle = _fake_kernel32.CloseHandle
_fake_close_handle.argtypes = [ctypes.c_void_p]
_fake_close_handle.restype = ctypes.c_int

sha256_stream_calls = []
composer_calls = []


def native_master_protect_acquire(path):
    handle = _fake_create_file_w(
        path, _GENERIC_READ, _FILE_SHARE_READ, None,
        _OPEN_EXISTING, _FILE_ATTRIBUTE_NORMAL, None,
    )
    if handle is None or handle == ctypes.c_void_p(-1).value:
        return None
    return handle


def native_master_protect_release(handle):
    if handle is None:
        return
    _fake_close_handle(handle)


def sha256_stream(path):
    sha256_stream_calls.append(path)
    return "deadbeef"


def production_generic_composer(a, b):
    composer_calls.append((a, b))
    return "COMPOSER_RESULT"


class RebuildControlGroupsProductionRun(object):
    def objectName(self):
        return RUN_LOCK_NAME

    def prepare_native_callback(self):
        def native_rebuild(aset_ptr):
            return "NATIVE_RESULT:%r" % (aset_ptr,)
        self.rebuild = native_rebuild
        return "PREPARED"

    def run_target_transaction(self, shot_record, target):
        return ("TRANSACTION_RESULT", shot_record, target)


# Synchronous construction, exactly like real production's own
# StartRebuildControlGroups() -- completes before this exec() returns.
_run_instance = RebuildControlGroupsProductionRun()
_run_instance.prepare_native_callback()
"""

fake_ns = {}
exec(compile(FAKE_PRODUCTION_SOURCE, "<fake_production_j>", "exec"), fake_ns)

events = []
state = {
    "protection_active": False,
    "protected_path": None,
    "acquire_call_count": 0,
    "release_call_count": 0,
    "native_rebuild_wrapper_call_count": 0,
    "native_rebuild_original_present": False,
    "instrumentation_ready": False,
}

fake_main_window_2c = FakeMainWindow([fake_ns["_run_instance"]])

# Guard installed FIRST, per the mandated ordering, while not ready.
guard_installed_2c = install_run_target_transaction_guard(fake_ns, events, state)
expect(guard_installed_2c is True, "wrapper_regression.guard_installed_first")

# Attempting the transaction BEFORE the rest of setup completes must be
# blocked -- proving the guard is armed from the very first post-exec
# instant, not merely "eventually".
_blocked_before_ready = False
try:
    fake_ns["_run_instance"].run_target_transaction({"name": u"shot9"}, {"name": u"krystalv21"})
except CheckpointJInstrumentationNotReadyError:
    _blocked_before_ready = True
expect(_blocked_before_ready is True, "wrapper_regression.transaction_blocked_before_rest_of_setup_completes")

run_instance_2c = locate_run_instance(fake_main_window_2c, fake_ns.get("RUN_LOCK_NAME"))
expect(run_instance_2c is fake_ns["_run_instance"], "wrapper_regression.locate_run_instance_finds_the_synthetic_run_instance")
native_wrap_ok_2c = wrap_run_instance_native_rebuild(run_instance_2c, events, state)
expect(native_wrap_ok_2c is True, "wrapper_regression.native_rebuild_instance_wrap_installed")
expect(state["native_rebuild_original_present"] is True, "wrapper_regression.native_rebuild_original_callable_was_present_before_wrap")

missing = make_wrappers(fake_ns, events, state)
expect(missing == [], "wrapper_regression.all_four_module_level_wrap_points_installed", missing)

# NOW flip instrumentation_ready -- exactly mirroring the real script's
# own ordering (guard, instance wrap, workload gates, module wraps, THEN
# instrumentation_ready = True).
state["instrumentation_ready"] = True

original_acquire_before_call_count = state["acquire_call_count"]
handle = fake_ns["native_master_protect_acquire"](_fake_master_path)
expect(handle is not None, "wrapper_regression.acquire_wrapper_returns_real_handle_unmodified")
expect(state["acquire_call_count"] == original_acquire_before_call_count + 1, "wrapper_regression.acquire_call_count_incremented_exactly_once")
expect(state["protection_active"] is True, "wrapper_regression.protection_active_set_after_real_acquire_success")
expect(state["protected_path"] == _fake_master_path, "wrapper_regression.protected_path_recorded_from_real_acquire_arg")

sha_result = fake_ns["sha256_stream"](_fake_master_path)
expect(sha_result == "deadbeef", "wrapper_regression.sha256_stream_wrapper_returns_original_value_unmodified")
sha_events = [e for e in events if e["kind"] == "sha256_stream_call"]
expect(len(sha_events) == 1 and sha_events[0]["protection_active"] is True and sha_events[0]["is_protected_path"] is True,
       "wrapper_regression.sha256_stream_event_recorded_while_protected_on_protected_path", sha_events)

_test_aset_ptr = 0xDEADBEEF
rebuild_result = run_instance_2c.rebuild(_test_aset_ptr)
expect(rebuild_result == ("NATIVE_RESULT:%r" % (_test_aset_ptr,)), "wrapper_regression.rebuild_wrapper_calls_real_native_rebuild_and_returns_its_value", rebuild_result)
expect(state["native_rebuild_wrapper_call_count"] == 1, "wrapper_regression.native_rebuild_wrapper_call_count_is_exactly_one", state["native_rebuild_wrapper_call_count"])

native_enter = [e for e in events if e["kind"] == "native_rebuild_enter"]
native_return = [e for e in events if e["kind"] == "native_rebuild_return"]
expect(len(native_enter) == 1 and len(native_return) == 1, "wrapper_regression.exactly_one_native_rebuild_enter_and_return_event")
expect(matrix_is_exactly_protected(native_enter[0]["matrix"]) is True,
       "wrapper_regression.native_rebuild_enter_matrix_shows_real_protected_state", native_enter[0]["matrix"])
expect(native_return[0].get("protection_active") is True,
       "wrapper_regression.native_rebuild_return_observed_while_protection_active", native_return[0])

# Protected-Master-SHA gate: the sha256_stream_call above sits, by event-
# list ordinal position, strictly between protect_acquire and
# native_rebuild_enter -- find_protected_master_sha256_ok() must confirm
# this using ACTUAL recorded events, not a hand-built fixture.
expect(find_protected_master_sha256_ok(events, _fake_master_path) is True,
       "wrapper_regression.protected_master_sha256_confirmed_from_real_events")

composer_result = fake_ns["production_generic_composer"]("A", "B")
expect(composer_result == "COMPOSER_RESULT", "wrapper_regression.composer_wrapper_returns_original_value")
expect(fake_ns["composer_calls"] == [("A", "B")], "wrapper_regression.composer_wrapper_forwards_same_args_unmodified")
composer_enter = [e for e in events if e["kind"] == "composer_enter"]
composer_return = [e for e in events if e["kind"] == "composer_return"]
expect(len(composer_enter) == 1 and len(composer_return) == 1, "wrapper_regression.exactly_one_composer_enter_and_return_event")
expect(matrix_is_exactly_protected(composer_enter[0]["matrix"]) is True,
       "wrapper_regression.composer_enter_matrix_shows_real_protected_state", composer_enter[0]["matrix"])

with open(_fake_master_path, "rb") as f:
    _fake_master_before_release = f.read()

fake_ns["native_master_protect_release"](handle)
expect(state["release_call_count"] == 1, "wrapper_regression.release_call_count_incremented_exactly_once")
expect(state["protection_active"] is False, "wrapper_regression.protection_active_cleared_after_real_release")

post_release_events = [e for e in events if e["kind"] == "post_release_probe_matrix"]
expect(len(post_release_events) == 1, "wrapper_regression.exactly_one_post_release_probe_matrix_event")
expect(matrix_is_fully_open(post_release_events[0]["matrix"]) is True,
       "wrapper_regression.post_release_matrix_shows_real_fully_open_state", post_release_events[0]["matrix"])
expect(matrix_all_probe_handles_closed(post_release_events[0]["matrix"]) is True,
       "wrapper_regression.post_release_matrix_all_probe_handles_closed")

with open(_fake_master_path, "rb") as f:
    _fake_master_after_release = f.read()
expect(_fake_master_before_release == _fake_master_after_release == b"fake master fixture\n",
       "wrapper_regression.harness_never_wrote_to_the_fixture_master_file")

expect(validate_event_order(events) is True, "wrapper_regression.full_happy_path_event_order_valid", [e["kind"] for e in events])

# Now that instrumentation was ready, the SAME transaction call from
# before must succeed (guard forwards, does not re-block).
transaction_result_after_ready = run_instance_2c.run_target_transaction({"name": u"shot9"}, {"name": u"krystalv21"})
expect(transaction_result_after_ready[0] == "TRANSACTION_RESULT", "wrapper_regression.transaction_succeeds_once_instrumentation_ready")
expect(state.get("blocked_call_count", 0) == 1, "wrapper_regression.exactly_one_blocked_call_total_from_the_earlier_premature_attempt", state.get("blocked_call_count"))

happy_context = {
    "baseline_matrix": {"read": {"success": True, "win_error": None, "close_attempted": True, "close_succeeded": True, "close_error": None},
                        "write": {"success": True, "win_error": None, "close_attempted": True, "close_succeeded": True, "close_error": None},
                        "delete": {"success": True, "win_error": None, "close_attempted": True, "close_succeeded": True, "close_error": None}},
    "acquire_call_count": state["acquire_call_count"],
    "acquire_succeeded": True,
    "native_rebuild_wrapper_installed": native_wrap_ok_2c,
    "native_rebuild_wrapper_call_count": state["native_rebuild_wrapper_call_count"],
    "native_rebuild_protection_active_at_return": bool(native_return[0].get("protection_active")),
    "protected_master_sha256_confirmed": find_protected_master_sha256_ok(events, _fake_master_path),
    "protected_path_is_canonical_master": True,
    "native_rebuild_matrix": native_enter[0]["matrix"],
    "native_rebuild_returned_pass": True,
    "composer_matrix": composer_enter[0]["matrix"],
    "composer_returned_pass": True,
    "release_call_count": state["release_call_count"],
    "post_release_matrix": post_release_events[0]["matrix"],
    "master_sha_before": "same",
    "master_sha_after": "same",
    "master_size_before": 100,
    "master_size_after": 100,
    "production_command_pass": True,
    "open_handle_leak_detected": False,
    "harness_master_write_detected": False,
    "event_order_valid": True,
    "actual_runtime_api_version_matches": True,
    "actual_runtime_build_id_matches": True,
    "authority_canonical": True,
    "authority_state_ready": True,
    "workload_identity_confirmed": True,
    "production_log_scope_confirmed": True,
    "production_log_single_target_confirmed": True,
    "production_log_single_native_rebuild_confirmed": True,
    "instrumentation_blocked_any_call": False,
}
happy_verdict, happy_failed = classify_j_verdict(happy_context)
expect(happy_verdict == "J_PASS" and happy_failed == [], "wrapper_regression.happy_path_context_classifies_j_pass", (happy_verdict, happy_failed))

try:
    os.remove(_fake_master_path)
except Exception:
    pass


# ---------------------------------------------------------------------------
# 3. Workload-identity gate unit tests -- pure logic (resolve_unique_shot,
#    canonical_single_shot_match, work_inventory_matches_single_target,
#    the three production_log_* string checks) plus resolve_fixture_
#    basename() against a fake sfmApp/vs object model (same technique
#    Checkpoint G's own test suite already uses for its own fake
#    sfmApp/DME object model).
# ---------------------------------------------------------------------------


class _FakeShot(object):
    def __init__(self, name, ptr):
        self._name = name
        self.this = ptr

    def GetName(self):
        return self._name


shot9_fake = _FakeShot(u"shot9", 111)
shot6_fake = _FakeShot(u"shot6", 222)
shot9_fake_duplicate_name_different_ptr = _FakeShot(u"shot9", 333)

expect(resolve_unique_shot([shot9_fake, shot6_fake], u"shot9") == [shot9_fake], "workload_identity.resolve_unique_shot_finds_the_one_match")
expect(resolve_unique_shot([shot9_fake, shot9_fake_duplicate_name_different_ptr], u"shot9") == [shot9_fake, shot9_fake_duplicate_name_different_ptr],
       "workload_identity.resolve_unique_shot_returns_all_name_matches_even_if_ambiguous")
expect(resolve_unique_shot([shot6_fake], u"shot9") == [], "workload_identity.resolve_unique_shot_empty_when_absent")

expect(b_native_ptr(shot9_fake) == 111, "workload_identity.b_native_ptr_reads_this_attribute")
expect(b_native_ptr(None) is None, "workload_identity.b_native_ptr_none_for_none_object")

expect(canonical_single_shot_match([shot9_fake], 111) is True, "workload_identity.canonical_single_shot_match_true_for_matching_single_shot")
expect(canonical_single_shot_match([], 111) is False, "workload_identity.canonical_single_shot_match_false_for_zero_shots")
expect(canonical_single_shot_match([shot9_fake, shot6_fake], 111) is False, "workload_identity.canonical_single_shot_match_false_for_more_than_one_shot")
expect(canonical_single_shot_match([shot6_fake], 111) is False, "workload_identity.canonical_single_shot_match_false_for_wrong_shot")
expect(canonical_single_shot_match([shot9_fake_duplicate_name_different_ptr], 111) is False,
       "workload_identity.canonical_single_shot_match_rejects_same_name_different_pointer")
expect(canonical_single_shot_match([shot9_fake], None) is False, "workload_identity.canonical_single_shot_match_false_when_expected_ptr_is_none")

expect(work_inventory_matches_single_target(None, u"shot9", u"krystalv21") is False, "workload_identity.work_inventory_none_is_a_hard_failure_never_a_soft_pass")
expect(work_inventory_matches_single_target([], u"shot9", u"krystalv21") is False, "workload_identity.work_inventory_empty_is_a_hard_failure_never_a_soft_pass")
good_work = [{"name": u"shot9", "targets": [{"name": u"krystalv21"}]}]
expect(work_inventory_matches_single_target(good_work, u"shot9", u"krystalv21") is True, "workload_identity.work_inventory_exact_single_target_passes")
wrong_shot_work = [{"name": u"shot6", "targets": [{"name": u"krystalv21"}]}]
expect(work_inventory_matches_single_target(wrong_shot_work, u"shot9", u"krystalv21") is False, "workload_identity.work_inventory_wrong_shot_fails")
too_many_shots_work = [{"name": u"shot9", "targets": [{"name": u"krystalv21"}]}, {"name": u"shot6", "targets": [{"name": u"felicia1"}]}]
expect(work_inventory_matches_single_target(too_many_shots_work, u"shot9", u"krystalv21") is False, "workload_identity.work_inventory_more_than_one_shot_fails")
too_many_targets_work = [{"name": u"shot9", "targets": [{"name": u"krystalv21"}, {"name": u"other"}]}]
expect(work_inventory_matches_single_target(too_many_targets_work, u"shot9", u"krystalv21") is False, "workload_identity.work_inventory_more_than_one_target_fails")
wrong_target_work = [{"name": u"shot9", "targets": [{"name": u"someone_else"}]}]
expect(work_inventory_matches_single_target(wrong_target_work, u"shot9", u"krystalv21") is False, "workload_identity.work_inventory_wrong_target_fails")

SAMPLE_LOG_GOOD = (
    u"scope_mode=SELECTED_SHOTS scope_shots=1\n"
    u"CONTEXTUALIZER_SCOPE_SHOT_NAMES = [u'shot9']\n"
    u"PRODUCTION_PRE_CAPTURE_GATE = PASS target=(u'shot9', u'krystalv21') signature=(302, 1, 302)\n"
    u"NATIVE_REBUILD_RETURNED = PASS\n"
)
expect(production_log_scope_confirmed(SAMPLE_LOG_GOOD, u"shot9") is True, "workload_identity.production_log_scope_confirmed_on_good_log")
expect(production_log_single_target_transaction(SAMPLE_LOG_GOOD, u"shot9", u"krystalv21") is True, "workload_identity.production_log_single_target_confirmed_on_good_log")
expect(production_log_single_native_rebuild(SAMPLE_LOG_GOOD) is True, "workload_identity.production_log_single_native_rebuild_confirmed_on_good_log")

SAMPLE_LOG_WRONG_SCOPE = u"scope_mode=ALL_SHOTS scope_shots=15\nCONTEXTUALIZER_SCOPE_SHOT_NAMES = [u'shot1', u'shot2']\n"
expect(production_log_scope_confirmed(SAMPLE_LOG_WRONG_SCOPE, u"shot9") is False, "workload_identity.production_log_scope_confirmed_false_for_all_shots_log")

SAMPLE_LOG_TWO_TARGETS = SAMPLE_LOG_GOOD + u"PRODUCTION_PRE_CAPTURE_GATE = PASS target=(u'shot9', u'other_target') signature=(1, 1, 1)\n"
expect(production_log_single_target_transaction(SAMPLE_LOG_TWO_TARGETS, u"shot9", u"krystalv21") is False,
       "workload_identity.production_log_single_target_confirmed_false_when_a_second_target_appears")

SAMPLE_LOG_WRONG_TARGET_ONLY = u"PRODUCTION_PRE_CAPTURE_GATE = PASS target=(u'shot9', u'someone_else') signature=(1, 1, 1)\n"
expect(production_log_single_target_transaction(SAMPLE_LOG_WRONG_TARGET_ONLY, u"shot9", u"krystalv21") is False,
       "workload_identity.production_log_single_target_confirmed_false_for_wrong_target")

SAMPLE_LOG_TWO_NATIVE_REBUILDS = SAMPLE_LOG_GOOD + u"NATIVE_REBUILD_RETURNED = PASS\n"
expect(production_log_single_native_rebuild(SAMPLE_LOG_TWO_NATIVE_REBUILDS) is False,
       "workload_identity.production_log_single_native_rebuild_confirmed_false_when_it_appears_twice")

expect(production_log_scope_confirmed(u"", u"shot9") is False, "workload_identity.production_log_scope_confirmed_false_for_empty_log")
expect(production_log_single_target_transaction(u"", u"shot9", u"krystalv21") is False, "workload_identity.production_log_single_target_confirmed_false_for_empty_log")
expect(production_log_single_native_rebuild(u"") is False, "workload_identity.production_log_single_native_rebuild_confirmed_false_for_empty_log")


class _FakeDocumentRoot(object):
    def __init__(self, file_id):
        self._file_id = file_id

    def GetFileId(self):
        return self._file_id


class _FakeDataModel(object):
    def __init__(self, filenames_by_id):
        self._filenames_by_id = filenames_by_id

    def GetFileName(self, file_id):
        return self._filenames_by_id.get(file_id)


class _FakeVsModule(object):
    def __init__(self, data_model):
        self.g_pDataModel = data_model


class _FakeSfmAppModule(object):
    def __init__(self, document_root):
        self._document_root = document_root

    def GetDocumentRoot(self):
        return self._document_root


fixture_test_ns = dict(ns)
fixture_test_ns["sfmApp"] = _FakeSfmAppModule(_FakeDocumentRoot(7))
fixture_test_ns["vs"] = _FakeVsModule(_FakeDataModel({7: u"C:\\projects\\F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx"}))
exec(compile("import os\n" + workload_identity_block_text, "<pinned_workload_identity_fixture_test>", "exec"), fixture_test_ns)
expect(fixture_test_ns["resolve_fixture_basename"]() == u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx",
       "workload_identity.resolve_fixture_basename_extracts_correct_basename")

fixture_test_ns_forbidden = dict(ns)
fixture_test_ns_forbidden["sfmApp"] = _FakeSfmAppModule(_FakeDocumentRoot(9))
fixture_test_ns_forbidden["vs"] = _FakeVsModule(_FakeDataModel({9: u"C:\\projects\\testscripts.dmx"}))
exec(compile("import os\n" + workload_identity_block_text, "<pinned_workload_identity_fixture_test_forbidden>", "exec"), fixture_test_ns_forbidden)
expect(fixture_test_ns_forbidden["resolve_fixture_basename"]() == u"testscripts.dmx",
       "workload_identity.resolve_fixture_basename_correctly_identifies_forbidden_fixture")

fixture_test_ns_broken = dict(ns)
fixture_test_ns_broken["sfmApp"] = _FakeSfmAppModule(None)
exec(compile("import os\n" + workload_identity_block_text, "<pinned_workload_identity_fixture_test_broken>", "exec"), fixture_test_ns_broken)
expect(fixture_test_ns_broken["resolve_fixture_basename"]() == u"",
       "workload_identity.resolve_fixture_basename_returns_empty_string_on_failure_never_raises")

# --- normalize_path_for_comparison() / path_matches_baseline() -- binds
#     production's own protected path/generation to the canonical Master.
#     Reused verbatim from checkpoint_i_generation_replacement/
#     I_Generation_Helper.py's own already-qualified implementation. ---
expect(path_matches_baseline(r"C:\Game\usermod\cfg\sfm_defaultanimationgroups.txt", r"C:\Game\usermod\cfg\sfm_defaultanimationgroups.txt") is True,
       "path_binding.identical_paths_match")
expect(path_matches_baseline(r"C:\GAME\USERMOD\CFG\SFM_DEFAULTANIMATIONGROUPS.TXT", r"C:\Game\usermod\cfg\sfm_defaultanimationgroups.txt") is True,
       "path_binding.case_insensitive_match_ntfs_semantics")
expect(path_matches_baseline(r"C:\Game\usermod\cfg\..\cfg\sfm_defaultanimationgroups.txt", r"C:\Game\usermod\cfg\sfm_defaultanimationgroups.txt") is True,
       "path_binding.dot_dot_normalized_path_matches")
expect(path_matches_baseline(r"C:\Game\usermod\cfg\sfm_defaultanimationgroups.txt", r"C:\Other\usermod\cfg\sfm_defaultanimationgroups.txt") is False,
       "path_binding.wrong_path_does_not_match")
expect(path_matches_baseline(None, r"C:\Game\usermod\cfg\sfm_defaultanimationgroups.txt") is False,
       "path_binding.none_actual_path_never_matches")
expect(path_matches_baseline(r"C:\Game\usermod\cfg\sfm_defaultanimationgroups.txt", None) is False,
       "path_binding.none_baseline_path_never_matches")
expect(path_matches_baseline(u"", u"") is False, "path_binding.empty_strings_never_match")


# ---------------------------------------------------------------------------
# 4. find_protected_master_sha256_ok() direct ordinal-position tests
#    (synthetic event lists -- covers cases the wrapper-regression happy
#    path above cannot reach: wrong path, protection inactive, and the
#    sha check occurring OUTSIDE the acquire..native_rebuild_enter
#    window).
# ---------------------------------------------------------------------------

def _mk_event(kind, **fields):
    e = {"kind": kind}
    e.update(fields)
    return e


PROTECTED_PATH = u"C:\\fake\\master.txt"

GOOD_SHA_EVENTS = [
    _mk_event("protect_acquire", success=True),
    _mk_event("sha256_stream_call", path=PROTECTED_PATH, protection_active=True),
    _mk_event("native_rebuild_enter"),
]
expect(find_protected_master_sha256_ok(GOOD_SHA_EVENTS, PROTECTED_PATH) is True,
       "protected_sha256.confirmed_when_call_sits_between_acquire_and_native_enter")

NO_SHA_EVENTS = [
    _mk_event("protect_acquire", success=True),
    _mk_event("native_rebuild_enter"),
]
expect(find_protected_master_sha256_ok(NO_SHA_EVENTS, PROTECTED_PATH) is False,
       "protected_sha256.false_when_no_sha256_stream_call_exists_at_all")

WRONG_PATH_SHA_EVENTS = [
    _mk_event("protect_acquire", success=True),
    _mk_event("sha256_stream_call", path=u"C:\\some\\other\\file.txt", protection_active=True),
    _mk_event("native_rebuild_enter"),
]
expect(find_protected_master_sha256_ok(WRONG_PATH_SHA_EVENTS, PROTECTED_PATH) is False,
       "protected_sha256.false_when_the_call_is_for_a_different_path")

NOT_ACTIVE_SHA_EVENTS = [
    _mk_event("protect_acquire", success=True),
    _mk_event("sha256_stream_call", path=PROTECTED_PATH, protection_active=False),
    _mk_event("native_rebuild_enter"),
]
expect(find_protected_master_sha256_ok(NOT_ACTIVE_SHA_EVENTS, PROTECTED_PATH) is False,
       "protected_sha256.false_when_protection_was_not_active_at_call_time")

SHA_BEFORE_ACQUIRE_EVENTS = [
    _mk_event("sha256_stream_call", path=PROTECTED_PATH, protection_active=True),
    _mk_event("protect_acquire", success=True),
    _mk_event("native_rebuild_enter"),
]
expect(find_protected_master_sha256_ok(SHA_BEFORE_ACQUIRE_EVENTS, PROTECTED_PATH) is False,
       "protected_sha256.false_when_the_call_occurs_before_acquire_ordinally")

SHA_AFTER_NATIVE_ENTER_EVENTS = [
    _mk_event("protect_acquire", success=True),
    _mk_event("native_rebuild_enter"),
    _mk_event("sha256_stream_call", path=PROTECTED_PATH, protection_active=True),
]
expect(find_protected_master_sha256_ok(SHA_AFTER_NATIVE_ENTER_EVENTS, PROTECTED_PATH) is False,
       "protected_sha256.false_when_the_call_occurs_after_native_rebuild_enter_ordinally")

MULTIPLE_SHA_CALLS_ONE_QUALIFYING = [
    _mk_event("sha256_stream_call", path=u"C:\\unrelated.txt", protection_active=False),
    _mk_event("protect_acquire", success=True),
    _mk_event("sha256_stream_call", path=u"C:\\unrelated.txt", protection_active=False),
    _mk_event("sha256_stream_call", path=PROTECTED_PATH, protection_active=True),
    _mk_event("native_rebuild_enter"),
    _mk_event("sha256_stream_call", path=PROTECTED_PATH, protection_active=True),
]
expect(find_protected_master_sha256_ok(MULTIPLE_SHA_CALLS_ONE_QUALIFYING, PROTECTED_PATH) is True,
       "protected_sha256.confirmed_when_at_least_one_of_several_calls_qualifies")

expect(find_protected_master_sha256_ok(GOOD_SHA_EVENTS, None) is False, "protected_sha256.false_when_protected_path_is_falsy")
expect(find_protected_master_sha256_ok(GOOD_SHA_EVENTS, u"") is False, "protected_sha256.false_when_protected_path_is_empty_string")


# ---------------------------------------------------------------------------
# 5. classify_j_verdict() / validate_event_order() adversarial matrix --
#    each of the mechanical gates individually forced to fail, proving
#    none of them is silently skipped.
# ---------------------------------------------------------------------------

def _mutate(base, **overrides):
    d = dict(base)
    d.update(overrides)
    return d


FULLY_OPEN = {"read": {"success": True, "win_error": None, "close_attempted": True, "close_succeeded": True, "close_error": None},
              "write": {"success": True, "win_error": None, "close_attempted": True, "close_succeeded": True, "close_error": None},
              "delete": {"success": True, "win_error": None, "close_attempted": True, "close_succeeded": True, "close_error": None}}
EXACTLY_PROTECTED = {"read": {"success": True, "win_error": None, "close_attempted": True, "close_succeeded": True, "close_error": None},
                      "write": {"success": False, "win_error": 32, "close_attempted": False, "close_succeeded": None, "close_error": None},
                      "delete": {"success": False, "win_error": 32, "close_attempted": False, "close_succeeded": None, "close_error": None}}
AMBIGUOUS_DENIAL = {"read": {"success": True, "win_error": None, "close_attempted": True, "close_succeeded": True, "close_error": None},
                     "write": {"success": False, "win_error": 5, "close_attempted": False, "close_succeeded": None, "close_error": None},
                     "delete": {"success": False, "win_error": 5, "close_attempted": False, "close_succeeded": None, "close_error": None}}

BASE_CONTEXT = {
    "baseline_matrix": FULLY_OPEN,
    "acquire_call_count": 1,
    "acquire_succeeded": True,
    "native_rebuild_wrapper_installed": True,
    "native_rebuild_wrapper_call_count": 1,
    "native_rebuild_protection_active_at_return": True,
    "protected_master_sha256_confirmed": True,
    "protected_path_is_canonical_master": True,
    "native_rebuild_matrix": EXACTLY_PROTECTED,
    "native_rebuild_returned_pass": True,
    "composer_matrix": EXACTLY_PROTECTED,
    "composer_returned_pass": True,
    "release_call_count": 1,
    "post_release_matrix": FULLY_OPEN,
    "master_sha_before": "SAME",
    "master_sha_after": "SAME",
    "master_size_before": 10,
    "master_size_after": 10,
    "production_command_pass": True,
    "open_handle_leak_detected": False,
    "harness_master_write_detected": False,
    "event_order_valid": True,
    "actual_runtime_api_version_matches": True,
    "actual_runtime_build_id_matches": True,
    "authority_canonical": True,
    "authority_state_ready": True,
    "workload_identity_confirmed": True,
    "production_log_scope_confirmed": True,
    "production_log_single_target_confirmed": True,
    "production_log_single_native_rebuild_confirmed": True,
    "instrumentation_blocked_any_call": False,
}

base_verdict, base_failed = classify_j_verdict(BASE_CONTEXT)
expect(base_verdict == "J_PASS" and base_failed == [], "adversarial.base_context_is_j_pass", (base_verdict, base_failed))

ADVERSARIAL_CASES = [
    ("j1_baseline_probes_all_succeeded", _mutate(BASE_CONTEXT, baseline_matrix=AMBIGUOUS_DENIAL)),
    ("acquire_called_exactly_once", _mutate(BASE_CONTEXT, acquire_call_count=2)),
    ("acquire_called_exactly_once", _mutate(BASE_CONTEXT, acquire_call_count=0)),
    ("acquire_succeeded", _mutate(BASE_CONTEXT, acquire_succeeded=False)),
    ("native_rebuild_wrapper_installed", _mutate(BASE_CONTEXT, native_rebuild_wrapper_installed=False)),
    ("native_rebuild_wrapper_called_exactly_once", _mutate(BASE_CONTEXT, native_rebuild_wrapper_call_count=0)),
    ("native_rebuild_wrapper_called_exactly_once", _mutate(BASE_CONTEXT, native_rebuild_wrapper_call_count=2)),
    ("native_rebuild_observed_while_protected", _mutate(BASE_CONTEXT, native_rebuild_protection_active_at_return=False)),
    ("protected_master_sha256_confirmed", _mutate(BASE_CONTEXT, protected_master_sha256_confirmed=False)),
    ("protected_path_is_canonical_master", _mutate(BASE_CONTEXT, protected_path_is_canonical_master=False)),
    ("protected_matrix_at_native_rebuild_boundary", _mutate(BASE_CONTEXT, native_rebuild_matrix=AMBIGUOUS_DENIAL)),
    ("protected_matrix_at_native_rebuild_boundary", _mutate(BASE_CONTEXT, native_rebuild_matrix=FULLY_OPEN)),
    ("native_rebuild_returned_pass", _mutate(BASE_CONTEXT, native_rebuild_returned_pass=False)),
    ("protected_matrix_at_composer_boundary", _mutate(BASE_CONTEXT, composer_matrix=AMBIGUOUS_DENIAL)),
    ("composer_returned_pass", _mutate(BASE_CONTEXT, composer_returned_pass=False)),
    ("release_called_exactly_once", _mutate(BASE_CONTEXT, release_call_count=0)),
    ("release_called_exactly_once", _mutate(BASE_CONTEXT, release_call_count=2)),
    ("j3_post_release_probes_all_succeeded", _mutate(BASE_CONTEXT, post_release_matrix=EXACTLY_PROTECTED)),
    ("master_sha_unchanged", _mutate(BASE_CONTEXT, master_sha_after="DIFFERENT")),
    ("master_size_unchanged", _mutate(BASE_CONTEXT, master_size_after=999)),
    ("production_command_itself_pass", _mutate(BASE_CONTEXT, production_command_pass=False)),
    ("no_leaked_probe_or_protection_handles", _mutate(BASE_CONTEXT, open_handle_leak_detected=True)),
    ("harness_did_not_mutate_master", _mutate(BASE_CONTEXT, harness_master_write_detected=True)),
    ("required_event_order", _mutate(BASE_CONTEXT, event_order_valid=False)),
    ("actual_runtime_api_version_matches", _mutate(BASE_CONTEXT, actual_runtime_api_version_matches=False)),
    ("actual_runtime_build_id_matches", _mutate(BASE_CONTEXT, actual_runtime_build_id_matches=False)),
    ("authority_canonical", _mutate(BASE_CONTEXT, authority_canonical=False)),
    ("authority_state_ready", _mutate(BASE_CONTEXT, authority_state_ready=False)),
    ("workload_identity_confirmed", _mutate(BASE_CONTEXT, workload_identity_confirmed=False)),
    ("production_log_scope_confirmed", _mutate(BASE_CONTEXT, production_log_scope_confirmed=False)),
    ("production_log_single_target_confirmed", _mutate(BASE_CONTEXT, production_log_single_target_confirmed=False)),
    ("production_log_single_native_rebuild_confirmed", _mutate(BASE_CONTEXT, production_log_single_native_rebuild_confirmed=False)),
    ("fail_closed_guard_never_blocked_a_call", _mutate(BASE_CONTEXT, instrumentation_blocked_any_call=True)),
]

for expected_failed_gate, mutated_context in ADVERSARIAL_CASES:
    verdict, failed = classify_j_verdict(mutated_context)
    expect(
        verdict == "J_FAIL" and expected_failed_gate in failed,
        "adversarial.%s_forces_j_fail" % expected_failed_gate,
        (verdict, failed),
    )

_actual_gate_count = len(set(gate for gate, _ in ADVERSARIAL_CASES))
expect(_actual_gate_count == 29, "adversarial.exactly_29_distinct_named_gates_covered", _actual_gate_count)


def _mk_order_event(kind, **fields):
    e = {"kind": kind}
    e.update(fields)
    return e


HAPPY_EVENTS = [
    _mk_order_event("protect_acquire", start=1.0, end=1.1),
    _mk_order_event("native_rebuild_enter", at=1.2),
    _mk_order_event("native_rebuild_return", at=1.3),
    _mk_order_event("composer_enter", at=1.4),
    _mk_order_event("composer_return", at=1.5),
    _mk_order_event("protect_release", start=1.6, end=1.7),
    _mk_order_event("post_release_probe_matrix", at=1.8),
]
expect(validate_event_order(HAPPY_EVENTS) is True, "event_order.correctly_ordered_events_valid")

MISSING_KIND_EVENTS = [e for e in HAPPY_EVENTS if e["kind"] != "composer_return"]
expect(validate_event_order(MISSING_KIND_EVENTS) is False, "event_order.missing_required_kind_is_invalid")

# --- Ordinal (list-position), never wall-clock, determines the result:
#     swap two required events' actual LIST POSITIONS (not merely their
#     timestamp fields) -- composer_enter now appears, by list position,
#     BEFORE native_rebuild_enter/native_rebuild_return. ---
ORDINAL_OUT_OF_ORDER_EVENTS = [
    _mk_order_event("protect_acquire", start=1.0, end=1.1),
    _mk_order_event("composer_enter", at=1.2),
    _mk_order_event("native_rebuild_enter", at=1.3),
    _mk_order_event("native_rebuild_return", at=1.4),
    _mk_order_event("composer_return", at=1.5),
    _mk_order_event("protect_release", start=1.6, end=1.7),
    _mk_order_event("post_release_probe_matrix", at=1.8),
]
expect(validate_event_order(ORDINAL_OUT_OF_ORDER_EVENTS) is False, "event_order.ordinal_out_of_order_events_invalid")

# --- Deliberately misleading timestamps that contradict the (correct)
#     list/append order must NOT change the result -- ordinal position
#     alone determines it. ---
MISLEADING_TIMESTAMP_EVENTS = [
    _mk_order_event("protect_acquire", start=100.0, end=100.0),
    _mk_order_event("native_rebuild_enter", at=5.0),
    _mk_order_event("native_rebuild_return", at=4.0),
    _mk_order_event("composer_enter", at=3.0),
    _mk_order_event("composer_return", at=2.0),
    _mk_order_event("protect_release", start=1.0, end=1.0),
    _mk_order_event("post_release_probe_matrix", at=0.5),
]
expect(validate_event_order(MISLEADING_TIMESTAMP_EVENTS) is True,
       "event_order.ordinal_order_prevails_over_deliberately_misleading_timestamps")

# --- A required kind occurring MORE than once (e.g. a duplicate
#     native_rebuild_enter) is invalid -- never silently matched against
#     just the first occurrence. ---
DUPLICATE_REQUIRED_EVENT = list(HAPPY_EVENTS) + [_mk_order_event("native_rebuild_enter", at=99.0)]
expect(validate_event_order(DUPLICATE_REQUIRED_EVENT) is False, "event_order.duplicate_required_event_is_invalid")


sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
