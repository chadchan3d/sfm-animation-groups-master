# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint J: Native Protected-Handle
Qualification.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: mutates the scene (one ordinary Selected Shot(s) command,
on one already-qualified fixture, transacting exactly one eligible target).
Do not save afterward.

Purpose:
  Prove, in real SFM, the actual Windows sharing semantics of production's
  existing Master-protection handle (native_master_protect_acquire /
  native_master_protect_release, Rebuild_Control_Groups_Normalizer.py
  lines ~356-413): a short-lived CreateFileW handle opened with
  GENERIC_READ / FILE_SHARE_READ ONLY (never FILE_SHARE_WRITE, never
  FILE_SHARE_DELETE) / OPEN_EXISTING, held across the protected Master
  hash check (assert_master_stable -> sha256_stream), native Rebuild
  (self.rebuild), and contextual reconciliation (production_generic_
  composer), released in run_target_transaction's own finally
  (Rebuild_Control_Groups_Normalizer.py lines ~11837-12465).

  This checkpoint does NOT modify production. It exec()s the pinned,
  SHA-256-verified production bytes into a fresh namespace (the same
  technique every earlier checkpoint in this project already uses -- see
  Checkpoint O2/Checkpoint I) and monkey-patches five call points in that
  IN-MEMORY namespace only:
    1. native_master_protect_acquire(path)      -- module function
    2. native_master_protect_release(handle)    -- module function
    3. sha256_stream(path)                      -- module function
       (its evidence is a REAL verdict gate -- see "Protected Master SHA
       gate" below, not merely event-ordering decoration)
    4. production_generic_composer(...)         -- module function
    5. <run_instance>.rebuild                   -- INSTANCE-attribute patch

  Correction (round 1, see checkpoint_o2_r1/O2_R1_NATIVE_TIMING_
  CORRECTION.md): executing the production file's bytes does not merely
  define classes/functions -- its own top-level code synchronously
  constructs the run instance and performs one-time command-level setup,
  including the real self.rebuild assignment (prepare_native_callback,
  called from derive_paths()), and this ALL completes BEFORE exec()
  itself returns; only the PER-TARGET processing loop that follows is
  Qt-deferred. A class-level patch of prepare_native_callback installed
  AFTER exec() returns is therefore always too late -- self.rebuild is
  already a plain INSTANCE attribute by then, which takes precedence over
  any class-level definition by ordinary Python attribute-lookup rules,
  and prepare_native_callback is never called again for this run. Wrap #5
  above therefore locates the ALREADY-CONSTRUCTED run instance immediately
  after exec() returns -- via the same main_window.findChildren(QtCore.
  QObject) + objectName() == RUN_LOCK_NAME technique every earlier
  checkpoint's own wait-loop already uses -- and patches THAT INSTANCE's
  own self.rebuild attribute directly. The remaining four module-level
  wraps (1-4) are unaffected by this timing issue -- they are looked up by
  unqualified name from the exec()'d namespace's own globals at CALL time,
  which only happens later, inside the Qt-deferred per-target loop this
  wrap correctly precedes.

  Correction (round 2, source review): a raised CheckpointJError in THIS
  script's own outer control flow, after exec() has already returned, is
  NOT itself a safety mechanism -- by that point production has already
  constructed the run and scheduled its Qt-deferred target callback via
  the ambient SFM Qt event loop, which this script does not control and
  cannot stop merely by raising in its own frame. The real prevention
  mechanism is install_run_target_transaction_guard() below: a class-level
  wrap of RebuildControlGroupsProductionRun.run_target_transaction,
  installed as the FIRST post-exec instrumentation action (before any
  operation that can itself fail), which RAISES INSIDE production's own
  real call chain -- never calling the original method at all -- for as
  long as state["instrumentation_ready"] is not True. instrumentation_
  ready only becomes True after run-instance discovery, self.rebuild
  instance wrap installation, all four module-level wraps, AND the exact
  workload-identity gates below have all succeeded. This is what actually
  prevents an uninstrumented native-protection window, independent of
  whatever this script's own outer flow does afterward.

  Every wrapper calls the ORIGINAL function/method with the SAME
  arguments and returns its SAME, unmodified return value -- only
  recording timing/matrix metadata around the call. No capture is
  skipped, no native Rebuild call is bypassed, no composer call is
  bypassed, and no authority-lifecycle behavior is touched.

  A harness-side `state["protection_active"]` flag is set to True ONLY
  after the REAL production acquire call returns a non-None handle, and
  cleared ONLY after the REAL production release call has actually
  executed -- the harness never substitutes its own handle for
  production's.

Independent Win32 access probe (probe_access / probe_matrix below):
  Calls CreateFileW directly against the exact live Master path, for one
  desired-access class at a time (GENERIC_READ, GENERIC_WRITE, or DELETE),
  requesting maximally permissive sharing on the PROBE'S OWN side
  (FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE) so the result
  reflects compatibility with whatever handle production currently holds,
  never a conflict the probe itself introduces. OPEN_EXISTING only -- no
  truncation, no write, no rename, no delete is ever performed. Every
  successfully opened probe handle is closed immediately, and the ACTUAL
  CloseHandle result (success/failure/error code) is recorded and
  mechanically required by matrix_all_probe_handles_closed() -- never a
  hard-coded assumption. A failed probe handle (None / INVALID_HANDLE_
  VALUE) is NEVER passed to CloseHandle at all.

Protected Master SHA gate: sha256_stream's own wrapper records every call
  (path, whether protection was active, whether the path is the protected
  Master). find_protected_master_sha256_ok() below requires AT LEAST ONE
  such call whose recorded path equals the protected Master path,
  protection_active is True, and whose position in the (append-ordered)
  events list falls strictly between the successful protect_acquire event
  and the first native_rebuild_enter event -- i.e. mechanically proving
  the protected Master hash check genuinely happened inside the protected
  interval, not merely that a wrapper exists.

Workload (intentionally ONE target -- this checkpoint tests the
protection INTERVAL, not scope, generation switching, repeated use, or
vocabulary behavior). Mechanically pinned, never assumed, at three
independent layers:
  1. PRE-PRODUCTION (before exec()): fixture basename independently
     resolved via sfmApp.GetDocumentRoot().GetFileId() ->
     vs.g_pDataModel.GetFileName() (never testscripts.dmx), exactly 15
     project shots, shot9 resolves uniquely, its sole animation set is
     exactly krystalv21, and sfmClipEditor.GetSelectedShots() shows
     exactly one selected shot that canonically (native-pointer-identity)
     matches the resolved shot9.
  2. POST-EXEC, on the already-constructed run instance, before
     instrumentation_ready can become True: run_instance.scope_mode ==
     u"SELECTED_SHOTS"; exactly one run_instance.scope_shots entry,
     canonically matching the preflight shot9; and (if available)
     run_instance.work is exactly one shot record (shot9) with exactly
     one target (krystalv21).
  3. POST-RUN, from production's own completed log: exact
     "scope_mode=SELECTED_SHOTS scope_shots=1" and exact
     "CONTEXTUALIZER_SCOPE_SHOT_NAMES = [u'shot9']"; exactly one
     PRODUCTION_PRE_CAPTURE_GATE line, for exactly shot9/krystalv21; and
     exactly one NATIVE_REBUILD_RETURNED = PASS line.
  A correct protection matrix on any other workload cannot reach J_PASS:
  layer 1 failure aborts before exec(); layer 2 failure leaves
  instrumentation_ready False, so the fail-closed guard blocks the real
  transaction; layer 3 failure is its own hard verdict gate.

Required event ordering (see validate_event_order() below; event-list
ORDINAL position is used in preference to wall-clock timestamps wherever
practical, since the event list itself is append-ordered):
  baseline probes (J1, before production ever runs)
  < protect_acquire < protected_master_sha256 (see above; proven
  separately by find_protected_master_sha256_ok(), not by
  validate_event_order() itself, since sha256_stream may legitimately be
  called more than once and not every call need be inside the protected
  window) < native_rebuild_enter < native_rebuild_return < composer_enter
  < composer_return < protect_release < post_release_probe_matrix
  The protected-access matrix (READ succeeds; WRITE/DELETE fail with
  EXACTLY ERROR_SHARING_VIOLATION=32) is captured INSIDE the
  native_rebuild_enter and composer_enter events, i.e. strictly between
  each boundary's own enter/return pair.

Output (written incrementally):
  C:\\Users\\Public\\Documents\\sfm_checkpoint_j_result.json
  C:\\Users\\Public\\Documents\\sfm_checkpoint_j_result_summary.txt
  C:\\Users\\Public\\Documents\\sfm_checkpoint_j_production_log.txt

Do NOT save the SFM project after running this script.
"""
import ctypes
import hashlib
import json
import os
import sys
import time
import traceback

from PySide import QtCore

# ---------------------------------------------------------------------------
# Pinned identities.
# ---------------------------------------------------------------------------

EXPECTED_PRODUCTION_NORMALIZER_SHA256 = (
    "1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7"
)
EXPECTED_CANONICAL_MASTER_SHA256 = (
    "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
)
EXPECTED_RUNTIME_API_VERSION = "1.0.0-b2a"
EXPECTED_RUNTIME_BUILD_ID = "package-boundary-corrected-2026-09-22"
EXPECTED_SELECTED_SHOT_NAME = u"shot9"
EXPECTED_SELECTED_TARGET_NAME = u"krystalv21"
EXPECTED_PROJECT_SHOT_COUNT = 15
EXPECTED_FIXTURE_BASENAME = u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx"
FORBIDDEN_FIXTURE_BASENAME = u"testscripts.dmx"

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_j_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_j_result_summary.txt"
PRODUCTION_LOG_PRESERVE_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_j_production_log.txt"
NORMALIZER_LOG_PATH = "C:\\Users\\Public\\Documents\\sfm_rebuild_control_groups.txt"

PRODUCTION_NORMALIZER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
    "Rebuild_Control_Groups_Normalizer.py",
)
CANONICAL_MASTER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "cfg", "sfm_defaultanimationgroups.txt",
)


class CheckpointJError(Exception):
    pass


class CheckpointJInstrumentationNotReadyError(Exception):
    """
    Raised INSIDE production's own real call chain, by the
    run_target_transaction fail-closed guard, when a real per-target
    transaction was about to begin while this checkpoint's own
    instrumentation/workload-identity gates were not yet (or never)
    fully satisfied. This prevents the call from ever reaching native
    protection acquisition or native Rebuild uninstrumented, regardless
    of what this script's own outer control flow does afterward. Because
    PySide's Qt event-loop dispatch does not generally propagate a Python
    exception raised from inside a Qt-deferred callback back into this
    script's own stack frame, this script does not rely on CATCHING this
    exception for safety -- only on the fact that raising it, inside the
    guard, prevents the original method from ever being called. The
    outer except-clause for this exception (see the bottom of this file)
    exists only to handle the case where it DOES propagate.
    """
    pass


ANOMALIES = []


def anomaly(message):
    ANOMALIES.append(message)
    try:
        sys.stdout.write("ANOMALY: %s\n" % message)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Checkpoint-B-style fact helpers (verbatim, same copies every earlier
# checkpoint in this project uses).
# ---------------------------------------------------------------------------

def b_to_unicode(value):
    if isinstance(value, unicode):
        return value
    try:
        return value.decode("utf-8")
    except Exception:
        try:
            return value.decode("latin-1")
        except Exception:
            return unicode(value)


def b_name(obj):
    try:
        return b_to_unicode(obj.GetName())
    except Exception:
        return u"<UNNAMED>"


def b_native_ptr(obj):
    if obj is None:
        return None
    try:
        return long(obj.this)
    except Exception:
        try:
            return int(obj.this)
        except Exception:
            return None


# ---------------------------------------------------------------------------
# BEGIN PINNED BLOCK: Win32 access-probe helper.
# (Offline-extracted verbatim by exact line range -- see
#  test_checkpoint_j_native_protected_handle_dryrun.py -- and exercised
#  against a disposable temp file, never the live Master, before this
#  checkpoint was ever authorized to run in real SFM.)
# ---------------------------------------------------------------------------

PROBE_GENERIC_READ = 0x80000000
PROBE_GENERIC_WRITE = 0x40000000
PROBE_DELETE = 0x00010000
PROBE_FILE_SHARE_READ = 0x00000001
PROBE_FILE_SHARE_WRITE = 0x00000002
PROBE_FILE_SHARE_DELETE = 0x00000004
PROBE_OPEN_EXISTING = 3
PROBE_FILE_ATTRIBUTE_NORMAL = 0x00000080
PROBE_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
ERROR_SHARING_VIOLATION = 32

_probe_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_probe_create_file_w = _probe_kernel32.CreateFileW
_probe_create_file_w.argtypes = [
    ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
    ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
]
_probe_create_file_w.restype = ctypes.c_void_p
_probe_close_handle = _probe_kernel32.CloseHandle
_probe_close_handle.argtypes = [ctypes.c_void_p]
_probe_close_handle.restype = ctypes.c_int


def probe_access(path, desired_access):
    """
    Independent CreateFileW probe against `path` for exactly ONE desired-
    access class, using maximally permissive sharing on the probe's own
    side (FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE) so the
    result reflects compatibility with whatever handle production may
    currently hold, never a conflict this probe itself introduces.
    OPEN_EXISTING only. On success, the handle is closed immediately and
    no read/write/rename/delete/truncation of any kind is performed; the
    ACTUAL CloseHandle result is recorded, never assumed. On failure, the
    failed value is NEVER passed to CloseHandle at all.

    Returns {"success": bool, "win_error": int or None,
             "close_attempted": bool,
             "close_succeeded": bool or None,
             "close_error": int or None}.
    close_attempted/close_succeeded/close_error are only meaningful when
    success is True; a failed open never attempts CloseHandle, so those
    three fields are False/None/None in that case.
    """
    ctypes.set_last_error(0)
    share_mode = (
        PROBE_FILE_SHARE_READ | PROBE_FILE_SHARE_WRITE | PROBE_FILE_SHARE_DELETE
    )
    handle = _probe_create_file_w(
        path,
        desired_access,
        share_mode,
        None,
        PROBE_OPEN_EXISTING,
        PROBE_FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if handle is None or handle == PROBE_INVALID_HANDLE_VALUE:
        return {
            "success": False,
            "win_error": ctypes.get_last_error(),
            "close_attempted": False,
            "close_succeeded": None,
            "close_error": None,
        }
    ctypes.set_last_error(0)
    close_ok = bool(_probe_close_handle(handle))
    close_error = None if close_ok else ctypes.get_last_error()
    return {
        "success": True,
        "win_error": None,
        "close_attempted": True,
        "close_succeeded": close_ok,
        "close_error": close_error,
    }


def probe_matrix(path):
    """Independent READ/WRITE/DELETE probe triple against `path`."""
    return {
        "read": probe_access(path, PROBE_GENERIC_READ),
        "write": probe_access(path, PROBE_GENERIC_WRITE),
        "delete": probe_access(path, PROBE_DELETE),
    }


def matrix_is_fully_open(matrix):
    return bool(
        matrix
        and matrix["read"]["success"]
        and matrix["write"]["success"]
        and matrix["delete"]["success"]
    )


def matrix_is_exactly_protected(matrix):
    """READ succeeds; WRITE and DELETE fail with EXACTLY
    ERROR_SHARING_VIOLATION (32) -- never an arbitrary/ambiguous denial
    counted as equivalent."""
    if not matrix:
        return False
    return bool(
        matrix["read"]["success"]
        and (not matrix["write"]["success"])
        and matrix["write"]["win_error"] == ERROR_SHARING_VIOLATION
        and (not matrix["delete"]["success"])
        and matrix["delete"]["win_error"] == ERROR_SHARING_VIOLATION
    )


def matrix_all_probe_handles_closed(matrix):
    """
    Requires that every successfully-opened probe in `matrix` (read,
    write, delete) was ALSO successfully closed (close_succeeded is
    exactly True). A probe that never opened (success is False) is
    exempt -- it must never have attempted CloseHandle at all (see
    probe_access), which is proven separately, statically. Returns False
    (never True) for a missing/falsy matrix, so an absent matrix can
    never silently satisfy this gate.
    """
    if not matrix:
        return False
    for key in ("read", "write", "delete"):
        entry = matrix.get(key) or {}
        if entry.get("success") and entry.get("close_succeeded") is not True:
            return False
    return True

# ---------------------------------------------------------------------------
# END PINNED BLOCK: Win32 access-probe helper.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# BEGIN PINNED BLOCK: observational wrapper installer.
# ---------------------------------------------------------------------------

def make_wrappers(prod_ns, events, state):
    """
    Builds and installs the FOUR module-level observational wrappers this
    checkpoint relies on (module functions patched via reassignment in the
    exec()'d namespace dict). These four are unaffected by the
    synchronous-construction timing issue documented above and in
    checkpoint_o2_r1/O2_R1_NATIVE_TIMING_CORRECTION.md: each is looked up
    by unqualified name from the exec()'d namespace's own globals only at
    CALL time, which happens later, inside the Qt-deferred per-target
    loop -- installing them here, after exec() returns, remains correct.
    The fifth wrap point (self.rebuild) is NOT installed by this function;
    see wrap_run_instance_native_rebuild() below, which must be called
    separately against the already-constructed run instance. Every
    wrapper calls the ORIGINAL function with the SAME arguments and
    returns its SAME, unmodified return value.

    `events` is a flat, time-ordered (append-ordered) list this function
    appends dicts to. `state` is a dict with keys "protection_active",
    "protected_path", "acquire_call_count", "release_call_count" that
    this function reads and mutates as the real production acquire/
    release calls occur.

    Returns a list of the names of any wrap points that could not be
    installed (empty list means all four installed successfully).
    """
    missing = []

    original_acquire = prod_ns.get("native_master_protect_acquire")
    if original_acquire is not None:
        def wrapped_acquire(path):
            t0 = time.time()
            handle = original_acquire(path)
            t1 = time.time()
            success = handle is not None
            state["acquire_call_count"] += 1
            if success:
                state["protection_active"] = True
                state["protected_path"] = path
            events.append({
                "kind": "protect_acquire",
                "path": path,
                "success": success,
                "start": t0,
                "end": t1,
            })
            return handle
        prod_ns["native_master_protect_acquire"] = wrapped_acquire
    else:
        missing.append("native_master_protect_acquire")

    original_release = prod_ns.get("native_master_protect_release")
    if original_release is not None:
        def wrapped_release(handle):
            t0 = time.time()
            original_release(handle)
            t1 = time.time()
            state["release_call_count"] += 1
            state["protection_active"] = False
            events.append({
                "kind": "protect_release",
                "start": t0,
                "end": t1,
            })
            protected_path = state.get("protected_path")
            post_matrix = probe_matrix(protected_path) if protected_path else None
            events.append({
                "kind": "post_release_probe_matrix",
                "matrix": post_matrix,
                "at": time.time(),
            })
            return None
        prod_ns["native_master_protect_release"] = wrapped_release
    else:
        missing.append("native_master_protect_release")

    original_sha256_stream = prod_ns.get("sha256_stream")
    if original_sha256_stream is not None:
        def wrapped_sha256_stream(path):
            result = original_sha256_stream(path)
            events.append({
                "kind": "sha256_stream_call",
                "path": path,
                "protection_active": state.get("protection_active"),
                "is_protected_path": (path == state.get("protected_path")),
                "at": time.time(),
            })
            return result
        prod_ns["sha256_stream"] = wrapped_sha256_stream
    else:
        missing.append("sha256_stream")

    original_composer = prod_ns.get("production_generic_composer")
    if original_composer is not None:
        def wrapped_composer(*args, **kwargs):
            protected_path = state.get("protected_path")
            active = state.get("protection_active")
            enter_matrix = (
                probe_matrix(protected_path) if (protected_path and active) else None
            )
            events.append({
                "kind": "composer_enter",
                "protection_active": active,
                "matrix": enter_matrix,
                "at": time.time(),
            })
            result = original_composer(*args, **kwargs)
            events.append({
                "kind": "composer_return",
                "at": time.time(),
            })
            return result
        prod_ns["production_generic_composer"] = wrapped_composer
    else:
        missing.append("production_generic_composer")

    return missing

# ---------------------------------------------------------------------------
# END PINNED BLOCK: observational wrapper installer.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# BEGIN PINNED BLOCK: run-instance locator and native-rebuild instance wrap.
#
# Executing the production file's bytes does not merely define classes/
# functions -- its own top-level code SYNCHRONOUSLY constructs the run
# instance and performs one-time command-level setup, including the real
# self.rebuild assignment (prepare_native_callback, called from
# derive_paths()), and this ALL completes BEFORE exec() itself returns;
# only the per-target processing loop that follows is Qt-deferred. A
# class-level patch of prepare_native_callback installed AFTER exec()
# returns is therefore always too late -- self.rebuild is already a plain
# INSTANCE attribute by then, which takes precedence over any class-level
# definition by ordinary Python attribute-lookup rules, and prepare_
# native_callback is never called again for this run. This is the exact
# defect documented in checkpoint_o2_r1/O2_R1_NATIVE_TIMING_CORRECTION.md
# for Checkpoint O2's own original native-Rebuild wrap. The functions
# below locate the ALREADY-CONSTRUCTED run instance immediately after
# exec() returns -- via the same main_window.findChildren(QtCore.QObject)
# + objectName() == RUN_LOCK_NAME technique every earlier checkpoint's own
# wait-loop already uses -- and patch THAT INSTANCE's own self.rebuild
# attribute directly (a plain instance-attribute reassignment).
# ---------------------------------------------------------------------------

def locate_run_instance(main_window, run_lock_name):
    """
    Returns the single QObject child of `main_window` whose objectName()
    equals `run_lock_name`, or None if zero or more than one is found, or
    if either argument is None. Identical technique to every earlier
    checkpoint's own run-lock wait-loop (main_window.findChildren(
    QtCore.QObject) + objectName() comparison) -- reused here to locate
    the run instance itself immediately after exec() returns, not merely
    to detect that a run is active.
    """
    if run_lock_name is None or main_window is None:
        return None
    matches = []
    try:
        for child in main_window.findChildren(QtCore.QObject):
            try:
                if b_to_unicode(child.objectName()) == run_lock_name:
                    matches.append(child)
            except Exception:
                continue
    except Exception:
        return None
    if len(matches) != 1:
        return None
    return matches[0]


def wrap_run_instance_native_rebuild(run_instance, events, state):
    """
    Wraps the ALREADY-CONSTRUCTED `run_instance`'s own self.rebuild
    attribute directly (instance-attribute reassignment, never a
    class-level patch). Requires run_instance to be non-None and its
    current self.rebuild to be non-None (i.e. prepare_native_callback has
    already run, which it always has by the time exec() returns -- see
    the module docstring). The wrapper calls the ORIGINAL callable with
    the SAME argument and returns its SAME, unmodified return value;
    increments state["native_rebuild_wrapper_call_count"]; records a
    protected-matrix probe (if protection is active) at
    "native_rebuild_enter", and records state["protection_active"] again
    at "native_rebuild_return" so a real run's evidence directly shows
    protection was still held when the native call actually returned.

    Returns True if the wrap was installed, False otherwise (run_instance
    missing, or its self.rebuild not yet present).
    """
    if run_instance is None:
        state["native_rebuild_original_present"] = False
        return False
    original_rebuild = getattr(run_instance, "rebuild", None)
    state["native_rebuild_original_present"] = (original_rebuild is not None)
    if original_rebuild is None:
        return False

    def observed_rebuild(aset_ptr_arg):
        protected_path = state.get("protected_path")
        active = state.get("protection_active")
        enter_matrix = (
            probe_matrix(protected_path) if (protected_path and active) else None
        )
        events.append({
            "kind": "native_rebuild_enter",
            "protection_active": active,
            "matrix": enter_matrix,
            "at": time.time(),
        })
        ret = original_rebuild(aset_ptr_arg)
        state["native_rebuild_wrapper_call_count"] += 1
        events.append({
            "kind": "native_rebuild_return",
            "protection_active": state.get("protection_active"),
            "at": time.time(),
        })
        return ret

    run_instance.rebuild = observed_rebuild
    return True

# ---------------------------------------------------------------------------
# END PINNED BLOCK: run-instance locator and native-rebuild instance wrap.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# BEGIN PINNED BLOCK: run_target_transaction fail-closed instrumentation
# guard.
#
# A raised CheckpointJError in this script's OWN outer control flow, after
# exec() has already returned, does not itself prevent anything: by that
# point production has already constructed the run and scheduled its
# Qt-deferred target callback via the ambient SFM Qt event loop, which
# this script neither owns nor can stop merely by raising in its own
# frame. The REAL prevention mechanism is this class-level wrap of
# run_target_transaction itself, installed as the FIRST post-exec
# instrumentation action (before any operation that can itself fail): for
# as long as state["instrumentation_ready"] is not True, it raises INSIDE
# production's own real call chain and NEVER calls the original method --
# the scheduled callback can never enter native protection/native Rebuild
# uninstrumented, regardless of what this script's own outer flow does.
# ---------------------------------------------------------------------------

def make_run_target_transaction_guard(original_method, events, state):
    def wrapped(self, shot_record, target):
        if not state.get("instrumentation_ready"):
            state["blocked_call_count"] = state.get("blocked_call_count", 0) + 1
            events.append({
                "kind": "target_transaction_blocked_not_ready",
                "at": time.time(),
            })
            raise CheckpointJInstrumentationNotReadyError(
                "run_target_transaction invoked before Checkpoint J instrumentation "
                "was fully installed and workload identity was confirmed -- refusing "
                "to allow an uninstrumented native-protection window."
            )
        shot_name = None
        target_name = None
        try:
            shot_name = shot_record.get("name") if isinstance(shot_record, dict) else None
        except Exception:
            pass
        try:
            target_name = target.get("name") if isinstance(target, dict) else None
        except Exception:
            pass
        state["target_transaction_call_count"] = state.get("target_transaction_call_count", 0) + 1
        events.append({
            "kind": "target_transaction_call",
            "shot_name": shot_name,
            "target_name": target_name,
            "at": time.time(),
        })
        return original_method(self, shot_record, target)
    return wrapped


def install_run_target_transaction_guard(prod_ns, events, state):
    """
    Locates RebuildControlGroupsProductionRun in `prod_ns` and installs
    the fail-closed guard above at the CLASS level (unaffected by the
    synchronous-self.rebuild-assignment timing issue -- run_target_
    transaction itself is only ever called later, from inside the
    Qt-deferred per-target loop). Returns True if installed, False if the
    class or its run_target_transaction method could not be found (in
    which case instrumentation_ready can never legitimately become True
    either).
    """
    RunClass = prod_ns.get("RebuildControlGroupsProductionRun")
    original_method = (
        getattr(RunClass, "run_target_transaction", None)
        if RunClass is not None else None
    )
    if RunClass is None or original_method is None:
        return False
    RunClass.run_target_transaction = make_run_target_transaction_guard(original_method, events, state)
    return True

# ---------------------------------------------------------------------------
# END PINNED BLOCK: run_target_transaction fail-closed instrumentation
# guard.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# BEGIN PINNED BLOCK: workload-identity gates.
# ---------------------------------------------------------------------------

def resolve_unique_shot(all_shots, shot_name):
    return [s for s in all_shots if b_name(s) == shot_name]


def normalize_path_for_comparison(path):
    """
    Normalized absolute Windows path comparison (case-insensitive,
    separator-normalized -- NTFS/Win32 paths are case-insensitive).
    Identical technique to checkpoint_i_generation_replacement/
    I_Generation_Helper.py's own already-qualified
    normalize_path_for_comparison(), reused verbatim here to bind
    production's own protected path/generation to the canonical Master.
    """
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def path_matches_baseline(actual_path, baseline_path):
    if not actual_path or not baseline_path:
        return False
    return normalize_path_for_comparison(actual_path) == normalize_path_for_comparison(baseline_path)


def resolve_fixture_basename():
    """
    Independently resolves the currently-open document's basename via
    sfmApp.GetDocumentRoot().GetFileId() -> vs.g_pDataModel.GetFileName(),
    the same established technique checkpoint_g/checkpoint_i already use
    -- never assumed from shot names alone. Returns u"" on any failure.
    """
    try:
        root_for_filename = sfmApp.GetDocumentRoot()
        file_id = root_for_filename.GetFileId()
        open_path = vs.g_pDataModel.GetFileName(file_id)
        return os.path.basename(b_to_unicode(open_path)) if open_path else u""
    except Exception:
        return u""


def canonical_single_shot_match(shots, expected_ptr):
    """
    Returns True iff `shots` (any iterable of shot-like objects) contains
    EXACTLY ONE element, and that element's b_native_ptr() equals
    expected_ptr exactly -- never a name-only comparison, and never true
    for zero or more than one candidate.
    """
    items = list(shots)
    if len(items) != 1:
        return False
    if expected_ptr is None:
        return False
    return b_native_ptr(items[0]) == expected_ptr


def work_inventory_matches_single_target(work, shot_name, target_name):
    """
    Requires `work` to be EXACTLY one shot record matching `shot_name`
    with EXACTLY one target matching `target_name`. Empty/absent `work`
    is a FAILURE, never a soft pass: for this exact one-target J
    workload, production's own start() always constructs self.work =
    self.snapshot_work() synchronously, before exec() returns (see the
    module docstring), so it is always genuinely available by the time
    this check runs -- an empty/missing work inventory here is itself
    evidence something is wrong, not merely "not yet available".
    """
    if not work:
        return False
    if len(work) != 1:
        return False
    shot_record = work[0]
    try:
        if b_to_unicode(shot_record.get("name")) != shot_name:
            return False
        targets = shot_record.get("targets") or []
    except Exception:
        return False
    if len(targets) != 1:
        return False
    try:
        return b_to_unicode(targets[0].get("name")) == target_name
    except Exception:
        return False


def production_log_scope_confirmed(log_text, expected_shot_name):
    """
    Requires production's own completed log to contain BOTH the exact
    scope-summary line and the exact scope-shot-names line, matching
    production's own literal logging format (Rebuild_Control_Groups_
    Normalizer.py lines ~13879-13894):
      "scope_mode=SELECTED_SHOTS scope_shots=1"
      "CONTEXTUALIZER_SCOPE_SHOT_NAMES = [u'<expected_shot_name>']"
    """
    expected_names_line = "CONTEXTUALIZER_SCOPE_SHOT_NAMES = [u'%s']" % expected_shot_name
    return bool(
        log_text
        and ("scope_mode=SELECTED_SHOTS scope_shots=1" in log_text)
        and (expected_names_line in log_text)
    )


def production_log_single_target_transaction(log_text, shot_name, target_name):
    """
    Requires EXACTLY ONE "PRODUCTION_PRE_CAPTURE_GATE = PASS target=..."
    line in the whole log (proving no OTHER target was ever transacted),
    and that the one occurrence is exactly for (shot_name, target_name).
    """
    if not log_text:
        return False
    marker = "PRODUCTION_PRE_CAPTURE_GATE = PASS target="
    exact_marker = "%s(u'%s', u'%s')" % (marker, shot_name, target_name)
    return log_text.count(marker) == 1 and log_text.count(exact_marker) == 1


def production_log_single_native_rebuild(log_text):
    """Requires EXACTLY ONE "NATIVE_REBUILD_RETURNED = PASS" line."""
    if not log_text:
        return False
    return log_text.count("NATIVE_REBUILD_RETURNED = PASS") == 1

# ---------------------------------------------------------------------------
# END PINNED BLOCK: workload-identity gates.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# BEGIN PINNED BLOCK: event-order validator and mechanical verdict.
# ---------------------------------------------------------------------------

_REQUIRED_EVENT_ORDER_KINDS = [
    "protect_acquire",
    "native_rebuild_enter",
    "native_rebuild_return",
    "composer_enter",
    "composer_return",
    "protect_release",
    "post_release_probe_matrix",
]


def validate_event_order(events):
    """
    Confirms the required real-execution ordering for the seven kinds
    that must occur EXACTLY once each in a correct run, using PURELY
    ORDINAL (list-index) positions within the append-ordered `events`
    list itself -- never wall-clock timestamps, which could tie at clock
    resolution or be misleading even when the underlying append order is
    correct:
      protect_acquire < native_rebuild_enter < native_rebuild_return
      < composer_enter < composer_return < protect_release
      < post_release_probe_matrix
    (Baseline probes (J1) are, by construction, recorded before production
    ever executes at all -- checked separately by the caller, not via this
    event list. The protected Master SHA check -- protect_acquire <
    protected_master_sha256 < native_rebuild_enter -- is proven separately
    by find_protected_master_sha256_ok() below, using the SAME ordinal-
    index technique, since sha256_stream may legitimately be called more
    than once and not every call need fall inside the protected window,
    which would break the exactly-once assumption this function relies on
    for its own seven kinds.) Returns False if any required kind is
    entirely absent, or occurs MORE than once (never silently matched
    against just the first occurrence), or if the resulting indexes are
    not strictly increasing.
    """
    indexes = []
    for kind in _REQUIRED_EVENT_ORDER_KINDS:
        matching_indexes = [i for i, e in enumerate(events) if e["kind"] == kind]
        if len(matching_indexes) != 1:
            return False
        indexes.append(matching_indexes[0])
    for i in range(len(indexes) - 1):
        if not (indexes[i] < indexes[i + 1]):
            return False
    return True


def find_protected_master_sha256_ok(events, protected_path):
    """
    Requires AT LEAST ONE sha256_stream_call event satisfying:
      - its recorded path equals `protected_path` (the exact live Master
        path production's own real acquire call succeeded against);
      - protection_active is True at the moment of that call;
      - it occurs, by EVENT-LIST ORDINAL POSITION (never wall-clock
        timestamp), strictly after the first successful protect_acquire
        event and strictly before the first native_rebuild_enter event.
    Returns False if protected_path is falsy, or if no protect_acquire/
    native_rebuild_enter event exists to bound the window, or if no
    qualifying sha256_stream_call event is found in that window.
    """
    if not protected_path:
        return False
    acquire_idx = None
    native_enter_idx = None
    for i, e in enumerate(events):
        if acquire_idx is None and e["kind"] == "protect_acquire" and e.get("success"):
            acquire_idx = i
        if native_enter_idx is None and e["kind"] == "native_rebuild_enter":
            native_enter_idx = i
    if acquire_idx is None or native_enter_idx is None:
        return False
    for i, e in enumerate(events):
        if e["kind"] != "sha256_stream_call":
            continue
        if not (acquire_idx < i < native_enter_idx):
            continue
        if e.get("path") == protected_path and e.get("protection_active") is True:
            return True
    return False


def classify_j_verdict(context):
    """
    Evaluates the mechanical PASS criteria against the assembled evidence
    in `context` (a plain dict; see call site for its exact construction,
    and see the offline dryrun suite for synthetic-context coverage of
    every individual failure mode). Returns (verdict, failed_checks)
    where verdict is "J_PASS" or "J_FAIL" and failed_checks is a list of
    the specific named gates that failed (empty list iff verdict ==
    "J_PASS").

    Includes: the instance-level native-rebuild-wrap gates (a wrapper
    that was never installed, or installed but never actually called
    exactly once, or called while protection was not observed active,
    forces J_FAIL -- a zero-call wrapper is never treated as merely
    "incomplete evidence"); the protected-Master-SHA gate; the actual
    (not merely expected) authority runtime identity gates; the derived
    (never hard-coded) handle-hygiene gate; the three-layer workload-
    identity gates; and the fail-closed-guard-never-fired gate.
    """
    failed = []

    if not matrix_is_fully_open(context.get("baseline_matrix")):
        failed.append("j1_baseline_probes_all_succeeded")

    if context.get("acquire_call_count") != 1:
        failed.append("acquire_called_exactly_once")
    if not context.get("acquire_succeeded"):
        failed.append("acquire_succeeded")

    if not context.get("native_rebuild_wrapper_installed"):
        failed.append("native_rebuild_wrapper_installed")
    if context.get("native_rebuild_wrapper_call_count") != 1:
        failed.append("native_rebuild_wrapper_called_exactly_once")
    if not context.get("native_rebuild_protection_active_at_return"):
        failed.append("native_rebuild_observed_while_protected")

    if not context.get("protected_master_sha256_confirmed"):
        failed.append("protected_master_sha256_confirmed")

    if not context.get("protected_path_is_canonical_master"):
        failed.append("protected_path_is_canonical_master")

    if not matrix_is_exactly_protected(context.get("native_rebuild_matrix")):
        failed.append("protected_matrix_at_native_rebuild_boundary")
    if not context.get("native_rebuild_returned_pass"):
        failed.append("native_rebuild_returned_pass")

    if not matrix_is_exactly_protected(context.get("composer_matrix")):
        failed.append("protected_matrix_at_composer_boundary")
    if not context.get("composer_returned_pass"):
        failed.append("composer_returned_pass")

    if context.get("release_call_count") != 1:
        failed.append("release_called_exactly_once")

    if not matrix_is_fully_open(context.get("post_release_matrix")):
        failed.append("j3_post_release_probes_all_succeeded")

    if context.get("master_sha_before") != context.get("master_sha_after"):
        failed.append("master_sha_unchanged")
    if context.get("master_size_before") != context.get("master_size_after"):
        failed.append("master_size_unchanged")

    if not context.get("production_command_pass"):
        failed.append("production_command_itself_pass")

    if context.get("open_handle_leak_detected"):
        failed.append("no_leaked_probe_or_protection_handles")

    if context.get("harness_master_write_detected"):
        failed.append("harness_did_not_mutate_master")

    if not context.get("event_order_valid"):
        failed.append("required_event_order")

    if not context.get("actual_runtime_api_version_matches"):
        failed.append("actual_runtime_api_version_matches")
    if not context.get("actual_runtime_build_id_matches"):
        failed.append("actual_runtime_build_id_matches")
    if not context.get("authority_canonical"):
        failed.append("authority_canonical")
    if not context.get("authority_state_ready"):
        failed.append("authority_state_ready")

    if not context.get("workload_identity_confirmed"):
        failed.append("workload_identity_confirmed")
    if not context.get("production_log_scope_confirmed"):
        failed.append("production_log_scope_confirmed")
    if not context.get("production_log_single_target_confirmed"):
        failed.append("production_log_single_target_confirmed")
    if not context.get("production_log_single_native_rebuild_confirmed"):
        failed.append("production_log_single_native_rebuild_confirmed")

    if context.get("instrumentation_blocked_any_call"):
        failed.append("fail_closed_guard_never_blocked_a_call")

    verdict = "J_PASS" if not failed else "J_FAIL"
    return verdict, failed

# ---------------------------------------------------------------------------
# END PINNED BLOCK: event-order validator and mechanical verdict.
# ---------------------------------------------------------------------------


def write_json_atomic(final_path, data_obj):
    tmp_path = final_path + ".tmp"

    def _cleanup_tmp():
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

    try:
        f = open(tmp_path, "wb")
        try:
            json.dump(data_obj, f)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        finally:
            f.close()
    except Exception as exc:
        _cleanup_tmp()
        return False, "json.dump()/write to temp file (%r) failed: %r" % (tmp_path, exc), None
    try:
        temp_size = os.path.getsize(tmp_path)
    except Exception as exc:
        _cleanup_tmp()
        return False, "could not stat temp file (%r): %r" % (tmp_path, exc), None
    if temp_size <= 0:
        _cleanup_tmp()
        return False, "temp file is zero bytes after write (size=%r)" % (temp_size,), None
    try:
        with open(tmp_path, "rb") as f:
            reparsed_obj = json.load(f)
    except Exception as exc:
        _cleanup_tmp()
        return False, "temp file reopen/reparse verification failed: %r" % (exc,), None
    try:
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(tmp_path, final_path)
    except Exception as exc:
        return False, "promoting temp file to final path failed: %r" % (exc,), None
    return True, None, reparsed_obj


def write_text_atomic(final_path, text_bytes):
    tmp_path = final_path + ".tmp"

    def _cleanup_tmp():
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

    try:
        f = open(tmp_path, "wb")
        try:
            f.write(text_bytes)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        finally:
            f.close()
    except Exception as exc:
        _cleanup_tmp()
        return False, "temp file write (%r) failed: %r" % (tmp_path, exc)
    try:
        temp_size = os.path.getsize(tmp_path)
    except Exception as exc:
        _cleanup_tmp()
        return False, "could not stat temp file (%r): %r" % (tmp_path, exc)
    if temp_size <= 0:
        _cleanup_tmp()
        return False, "temp file is zero bytes after write (size=%r)" % (temp_size,)
    try:
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(tmp_path, final_path)
    except Exception as exc:
        return False, "promoting temp file to final path failed: %r" % (exc,)
    return True, None


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

report = {
    "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "python_version": sys.version,
    "checks": [],
    "anomalies": ANOMALIES,
    "provenance": {},
    "failure_phase": None,
    "in_progress": True,
}


def check(name, condition, detail=None):
    report["checks"].append({
        "name": name,
        "pass": bool(condition),
        "detail": repr(detail) if detail is not None else None,
    })
    try:
        sys.stdout.write(
            "[%s] %s%s\n"
            % ("PASS" if condition else "FAIL", name, ("" if detail is None else " -- %r" % (detail,)))
        )
    except Exception:
        pass


def write_rolling_evidence():
    ok, err, _r = write_json_atomic(JSON_OUTPUT_PATH, report)
    if not ok:
        anomaly("Rolling evidence write failed (run continues): %s" % (err,))
    return ok


main_window = None
production_bytes = None

# Bound into report["events"]/report["state"] IMMEDIATELY, as the SAME
# mutable objects -- not copies -- so any later mutation (including
# mutation that happens after an exception is raised elsewhere in this
# script) remains visible in the evidence artifact, rather than only
# being captured near a successful final-assembly point.
events = []
state = {
    "protection_active": False,
    "protected_path": None,
    "acquire_call_count": 0,
    "release_call_count": 0,
    "native_rebuild_wrapper_call_count": 0,
    "native_rebuild_original_present": False,
    "instrumentation_ready": False,
    "target_transaction_call_count": 0,
    "blocked_call_count": 0,
}
report["events"] = events
report["state"] = state

try:
    with open(PRODUCTION_NORMALIZER_PATH, "rb") as f:
        production_bytes = f.read()
    production_sha = hashlib.sha256(production_bytes).hexdigest()
    check("production_normalizer.sha256_matches_accepted", production_sha == EXPECTED_PRODUCTION_NORMALIZER_SHA256, production_sha)

    with open(CANONICAL_MASTER_PATH, "rb") as f:
        master_bytes_before = f.read()
    master_sha_before = hashlib.sha256(master_bytes_before).hexdigest()
    master_size_before = len(master_bytes_before)
    check("canonical_master.sha256_matches_baseline", master_sha_before == EXPECTED_CANONICAL_MASTER_SHA256, master_sha_before)

    if not (production_sha == EXPECTED_PRODUCTION_NORMALIZER_SHA256 and master_sha_before == EXPECTED_CANONICAL_MASTER_SHA256):
        report["failure_phase"] = "PRE_PRODUCTION_GATE"
        raise CheckpointJError("Pre-flight SHA-256 check failed -- refusing to proceed.")
    report["provenance"]["production_normalizer_sha256"] = production_sha
    report["provenance"]["canonical_master_sha256_before"] = master_sha_before
    report["provenance"]["canonical_master_size_before"] = master_size_before

    if not bool(sfmApp.HasDocument()):
        report["failure_phase"] = "PRE_PRODUCTION_GATE"
        raise CheckpointJError("No SFM document is open.")

    # -------------------------------------------------------------
    # Layer 1 (pre-production) workload-identity gates: fixture
    # basename, project shot count, shot9 uniqueness/animation-set
    # identity, and the real Clip Editor selection -- all independently
    # resolved, never assumed from shot names alone.
    # -------------------------------------------------------------
    open_basename = resolve_fixture_basename()
    report["provenance"]["fixture_open_basename"] = open_basename
    check("fixture.matches_expected_normalized_copy", open_basename.lower() == EXPECTED_FIXTURE_BASENAME.lower(), open_basename)
    check("fixture.is_not_forbidden_original", open_basename.lower() != FORBIDDEN_FIXTURE_BASENAME.lower(), open_basename)

    all_shots = list(sfmApp.GetShots())
    check("fixture.project_shot_count_matches_established_size", len(all_shots) == EXPECTED_PROJECT_SHOT_COUNT, len(all_shots))

    shot9_matches = resolve_unique_shot(all_shots, EXPECTED_SELECTED_SHOT_NAME)
    check("fixture.shot9_resolves_uniquely", len(shot9_matches) == 1, len(shot9_matches))
    if len(shot9_matches) != 1:
        report["failure_phase"] = "PRE_PRODUCTION_GATE"
        raise CheckpointJError("shot9 did not resolve uniquely in the open document -- wrong fixture/state?")
    shot9 = shot9_matches[0]
    shot9_ptr = b_native_ptr(shot9)

    asets = list(shot9.animationSets)
    aset_names = [b_name(a) for a in asets]
    check("fixture.shot9_single_animation_set", len(asets) == 1, aset_names)
    check("fixture.shot9_target_identity", aset_names == [EXPECTED_SELECTED_TARGET_NAME], aset_names)

    clip_editor_selected = []
    try:
        clip_editor_selected = list(sfmClipEditor.GetSelectedShots())
    except Exception as exc:
        anomaly("sfmClipEditor.GetSelectedShots() raised: %r" % (exc,))
    check(
        "fixture.clip_editor_selection_is_exactly_shot9",
        canonical_single_shot_match(clip_editor_selected, shot9_ptr),
        [b_name(s) for s in clip_editor_selected],
    )

    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        report["failure_phase"] = "PRE_PRODUCTION_GATE"
        raise CheckpointJError("Starting-state fixture gate failed -- aborting before any Master probe or production invocation.")

    # -------------------------------------------------------------
    # J1 -- unprotected baseline probe, strictly BEFORE production
    # ever executes (module-level exec has not happened yet).
    # -------------------------------------------------------------
    baseline_matrix = probe_matrix(CANONICAL_MASTER_PATH)
    check("j1.baseline_read_succeeds", baseline_matrix["read"]["success"], baseline_matrix["read"])
    check("j1.baseline_write_succeeds", baseline_matrix["write"]["success"], baseline_matrix["write"])
    check("j1.baseline_delete_succeeds", baseline_matrix["delete"]["success"], baseline_matrix["delete"])
    # A leaked baseline probe handle (opened successfully but never
    # actually closed) could itself conflict with production's own
    # subsequent GENERIC_READ/FILE_SHARE_READ protection handle,
    # contaminating the experiment -- this is a HARD pre-production gate,
    # never merely informational.
    check("j1.baseline_handles_all_closed", matrix_all_probe_handles_closed(baseline_matrix), baseline_matrix)
    report["baseline_matrix"] = baseline_matrix

    main_window = sfmApp.GetMainWindow()
    check("j.main_window_available", main_window is not None)
    write_rolling_evidence()

    baseline_gate_passed = all(c["pass"] for c in report["checks"])
    if not baseline_gate_passed:
        report["failure_phase"] = "PRE_PRODUCTION_GATE"
        raise CheckpointJError(
            "J1 baseline probe gate failed (including handle hygiene) -- aborting before production "
            "invocation. Restart SFM before another attempt."
        )

    # -------------------------------------------------------------
    # Execute the pinned production bytes. This is NOT merely defining
    # classes/functions: production's own top-level code SYNCHRONOUSLY
    # shows the real scope dialog (the operator already selected shot9
    # in the Clip Editor beforehand, per the checked gate above; this
    # dialog itself only chooses Selected Shot(s) vs. All Shots),
    # constructs the run instance once the operator responds, and
    # performs one-time command-level setup (including the real
    # self.rebuild assignment) -- all of this completes before exec()
    # itself returns; only the per-target processing loop that follows
    # is Qt-deferred. See the module docstring and
    # checkpoint_o2_r1/O2_R1_NATIVE_TIMING_CORRECTION.md.
    # -------------------------------------------------------------
    prod_ns = {}
    try:
        exec(compile(production_bytes, "<installed_production_normalizer_checkpoint_j>", "exec"), prod_ns)
    except Exception as exc:
        anomaly("Production Normalizer execution raised: %r" % exc)
        anomaly(traceback.format_exc())

    # From this point on, production has ALREADY constructed the run and
    # scheduled its Qt-deferred target callback -- "no production
    # invocation occurred" no longer applies to anything that follows.
    report["failure_phase"] = "POST_EXEC_INSTRUMENTATION"

    # -------------------------------------------------------------
    # FIRST post-exec instrumentation action, before any operation that
    # can itself fail: install the fail-closed run_target_transaction
    # guard. This -- not a raised exception in this script's own outer
    # flow -- is what actually prevents an uninstrumented native-
    # protection window.
    # -------------------------------------------------------------
    guard_installed = install_run_target_transaction_guard(prod_ns, events, state)
    check("j.run_target_transaction_guard_installed", guard_installed)

    # Locate the ALREADY-CONSTRUCTED run instance and wrap its own
    # self.rebuild attribute directly (instance-level patch).
    run_lock_name_early = prod_ns.get("RUN_LOCK_NAME")
    run_instance = locate_run_instance(main_window, run_lock_name_early)
    native_rebuild_wrap_ok = wrap_run_instance_native_rebuild(run_instance, events, state)
    check("j.native_rebuild_instance_wrap_installed", native_rebuild_wrap_ok, run_instance)

    # -------------------------------------------------------------
    # Bind production's own protected path/generation to the canonical
    # Master directly on the already-constructed instance -- otherwise
    # the file this harness hashed and the file production actually
    # protects are only ASSUMED to be the same. Both are real instance
    # attributes, set synchronously inside derive_paths() before exec()
    # returns (Rebuild_Control_Groups_Normalizer.py lines ~9865-9886).
    # -------------------------------------------------------------
    actual_master_path = getattr(run_instance, "master_path", None)
    actual_master_hash = getattr(run_instance, "master_hash", None)
    master_path_matches_canonical = path_matches_baseline(actual_master_path, CANONICAL_MASTER_PATH)
    master_hash_matches_canonical = (actual_master_hash == EXPECTED_CANONICAL_MASTER_SHA256)
    check("j.run_instance_master_path_matches_canonical", master_path_matches_canonical, actual_master_path)
    check("j.run_instance_master_hash_matches_canonical", master_hash_matches_canonical, actual_master_hash)
    report["provenance"]["run_instance_master_path"] = actual_master_path
    report["provenance"]["run_instance_master_hash"] = actual_master_hash

    # -------------------------------------------------------------
    # Layer 2 (post-exec, on the already-constructed instance)
    # workload-identity gates -- checked, never assumed. A failure here
    # does not raise; it simply prevents instrumentation_ready from ever
    # becoming True, so the guard installed above blocks the real
    # transaction when the Qt-deferred callback eventually arrives.
    # -------------------------------------------------------------
    actual_scope_mode = getattr(run_instance, "scope_mode", None)
    scope_mode_ok = (actual_scope_mode == u"SELECTED_SHOTS")
    check("j.run_instance_scope_mode_is_selected_shots", scope_mode_ok, actual_scope_mode)

    scope_shots = list(getattr(run_instance, "scope_shots", None) or [])
    scope_shots_ok = canonical_single_shot_match(scope_shots, shot9_ptr)
    check("j.run_instance_scope_shots_is_exactly_shot9", scope_shots_ok, [b_name(s) for s in scope_shots])

    work_inventory = getattr(run_instance, "work", None)
    work_inventory_ok = work_inventory_matches_single_target(work_inventory, EXPECTED_SELECTED_SHOT_NAME, EXPECTED_SELECTED_TARGET_NAME)
    check("j.run_instance_work_inventory_is_exactly_one_target", work_inventory_ok, work_inventory)

    workload_identity_confirmed = bool(
        scope_mode_ok and scope_shots_ok and work_inventory_ok
        and master_path_matches_canonical and master_hash_matches_canonical
    )
    check("j.workload_identity_confirmed", workload_identity_confirmed)

    # Install the remaining four module-level wraps.
    missing = make_wrappers(prod_ns, events, state)
    for m in missing:
        anomaly("Could not install wrapper for %r -- instrumentation incomplete." % m)
    check("j.instrumentation_installed", not missing, missing)

    instrumentation_ready = bool(
        guard_installed
        and native_rebuild_wrap_ok
        and (not missing)
        and workload_identity_confirmed
    )
    state["instrumentation_ready"] = instrumentation_ready
    check("j.instrumentation_ready", instrumentation_ready)

    run_lock_name = run_lock_name_early
    run_started = False
    run_completed_cleanly = False

    def normalizer_run_is_active():
        if run_lock_name is None or main_window is None:
            return False
        try:
            for child in main_window.findChildren(QtCore.QObject):
                try:
                    if b_to_unicode(child.objectName()) == run_lock_name:
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    active_now = normalizer_run_is_active()
    if active_now:
        run_started = True
        wait_start = time.time()
        MAX_WAIT_SECONDS = 1800
        while normalizer_run_is_active():
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.05)
            if time.time() - wait_start > MAX_WAIT_SECONDS:
                anomaly("Command did not complete within %d seconds -- aborting wait." % MAX_WAIT_SECONDS)
                break
        else:
            run_completed_cleanly = True
        settle_start = time.time()
        while time.time() - settle_start < 1.0:
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.05)
    else:
        anomaly(
            "No run-lock was ever observed active immediately after exec() returned -- "
            "this most likely means the operator cancelled the scope dialog."
        )

    check("j.run_was_started", run_started)
    check("j.run_completed_within_timeout", run_completed_cleanly if run_started else False)
    check("j.fail_closed_guard_never_blocked_a_call", state.get("blocked_call_count", 0) == 0, state.get("blocked_call_count"))

    # -------------------------------------------------------------
    # Post-run: re-read the Master, production log evidence,
    # ACTUAL authority-lifecycle identity checks (not merely production's
    # own expectation constants, kept only as corroboration below).
    # -------------------------------------------------------------
    with open(CANONICAL_MASTER_PATH, "rb") as f:
        master_bytes_after = f.read()
    master_sha_after = hashlib.sha256(master_bytes_after).hexdigest()
    master_size_after = len(master_bytes_after)
    check("j4.master_sha_unchanged", master_sha_after == master_sha_before, master_sha_after)
    check("j4.master_size_unchanged", master_size_after == master_size_before, master_size_after)
    report["provenance"]["canonical_master_sha256_after"] = master_sha_after
    report["provenance"]["canonical_master_size_after"] = master_size_after

    native_evidence = {}
    log_text = u""
    try:
        with open(NORMALIZER_LOG_PATH, "rb") as f:
            log_bytes = f.read()
        log_text = log_bytes.decode("ascii", "replace")
        native_evidence["contains_NATIVE_GUARDS_PASS"] = ("NATIVE_GUARDS = PASS" in log_text)
        native_evidence["contains_NATIVE_REBUILD_RETURNED_PASS"] = ("NATIVE_REBUILD_RETURNED = PASS" in log_text)
        native_evidence["contains_PRODUCTION_REBUILD_CONTROL_GROUPS_PASS"] = ("PRODUCTION_REBUILD_CONTROL_GROUPS = PASS" in log_text)
        native_evidence["contains_production_fail"] = ("PRODUCTION_REBUILD_CONTROL_GROUPS = FAIL" in log_text)
        preserve_ok, preserve_err = write_text_atomic(PRODUCTION_LOG_PRESERVE_PATH, log_bytes)
        if not preserve_ok:
            anomaly("Could not preserve production log: %s" % preserve_err)
        del log_bytes
    except Exception as exc:
        native_evidence["log_read_error"] = repr(exc)
        anomaly("Could not read production log: %r" % exc)

    check("j.native_guards_pass", native_evidence.get("contains_NATIVE_GUARDS_PASS") is True, native_evidence.get("contains_NATIVE_GUARDS_PASS"))
    check("j.native_rebuild_returned_pass", native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS") is True, native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS"))
    production_command_pass = bool(
        native_evidence.get("contains_PRODUCTION_REBUILD_CONTROL_GROUPS_PASS") is True
        and not native_evidence.get("contains_production_fail")
    )
    check("j.production_command_pass", production_command_pass, native_evidence)

    # Layer 3 (post-run, from production's own completed log).
    log_scope_confirmed = production_log_scope_confirmed(log_text, EXPECTED_SELECTED_SHOT_NAME)
    check("j.production_log_scope_confirmed", log_scope_confirmed)
    log_single_target_ok = production_log_single_target_transaction(log_text, EXPECTED_SELECTED_SHOT_NAME, EXPECTED_SELECTED_TARGET_NAME)
    check("j.production_log_single_target_transaction_confirmed", log_single_target_ok)
    log_single_native_rebuild_ok = production_log_single_native_rebuild(log_text)
    check("j.production_log_single_native_rebuild_confirmed", log_single_native_rebuild_ok)

    authority_evidence = {}
    try:
        authority_runtime = prod_ns.get("authority_runtime")
        if authority_runtime is not None:
            try:
                authority_evidence["runtime_api_version"] = getattr(authority_runtime, "RUNTIME_API_VERSION", None)
            except Exception as exc:
                authority_evidence["runtime_api_version_error"] = repr(exc)
            try:
                authority_evidence["runtime_build_id"] = getattr(authority_runtime, "RUNTIME_BUILD_ID", None)
            except Exception as exc:
                authority_evidence["runtime_build_id_error"] = repr(exc)
            try:
                authority_evidence["is_canonical"] = bool(authority_runtime.is_canonical())
            except Exception as exc:
                authority_evidence["is_canonical_error"] = repr(exc)
            try:
                authority_evidence["get_state"] = authority_runtime.get_state()
            except Exception as exc:
                authority_evidence["get_state_error"] = repr(exc)
            try:
                broker = authority_runtime.get_broker(
                    expected_api_version=prod_ns.get("_AUTHORITY_EXPECTED_API_VERSION"),
                    expected_build_id=prod_ns.get("_AUTHORITY_EXPECTED_BUILD_ID"),
                    is_main_thread_fn=lambda: (
                        QtCore.QThread.currentThread() is QtCore.QCoreApplication.instance().thread()
                    ),
                )
                authority_evidence["outstanding_lease_count"] = broker.outstanding_lease_count()
            except Exception as exc:
                authority_evidence["broker_query_error"] = repr(exc)
    except Exception as exc:
        authority_evidence["capture_error"] = repr(exc)

    # ACTUAL loaded runtime identity -- the real hard gates.
    check("j4.actual_runtime_api_version_matches", authority_evidence.get("runtime_api_version") == EXPECTED_RUNTIME_API_VERSION, authority_evidence.get("runtime_api_version"))
    check("j4.actual_runtime_build_id_matches", authority_evidence.get("runtime_build_id") == EXPECTED_RUNTIME_BUILD_ID, authority_evidence.get("runtime_build_id"))
    check("j4.authority_canonical", authority_evidence.get("is_canonical") is True, authority_evidence.get("is_canonical"))
    check("j4.authority_state_ready", authority_evidence.get("get_state") == "READY", authority_evidence.get("get_state"))
    check("j4.zero_outstanding_leases", authority_evidence.get("outstanding_lease_count") == 0, authority_evidence.get("outstanding_lease_count"))
    # Production's own EXPECTATION constants: corroboration only, never a
    # substitute for the actual loaded identity checked immediately above.
    check("j4.production_expected_api_version_corroborates", prod_ns.get("_AUTHORITY_EXPECTED_API_VERSION") == EXPECTED_RUNTIME_API_VERSION, prod_ns.get("_AUTHORITY_EXPECTED_API_VERSION"))
    check("j4.production_expected_build_id_corroborates", prod_ns.get("_AUTHORITY_EXPECTED_BUILD_ID") == EXPECTED_RUNTIME_BUILD_ID, prod_ns.get("_AUTHORITY_EXPECTED_BUILD_ID"))

    # -------------------------------------------------------------
    # Assemble event-derived matrices and classify the final verdict.
    # -------------------------------------------------------------
    def find_event(kind):
        for e in events:
            if e["kind"] == kind:
                return e
        return None

    acquire_event = find_event("protect_acquire")
    native_enter_event = find_event("native_rebuild_enter")
    native_return_event = find_event("native_rebuild_return")
    composer_enter_event = find_event("composer_enter")
    post_release_event = find_event("post_release_probe_matrix")

    protected_master_sha256_confirmed = find_protected_master_sha256_ok(events, state.get("protected_path"))

    # Final mechanical evidence that the path production ACTUALLY
    # protected -- both the one successful protect_acquire event's own
    # path and the harness-side state["protected_path"] it derived from
    # that event -- is the SAME canonical Master this checkpoint hashed
    # and bound to the run instance above, not merely assumed to be.
    acquire_event_path_is_canonical = bool(
        acquire_event and path_matches_baseline(acquire_event.get("path"), CANONICAL_MASTER_PATH)
    )
    protected_path_state_is_canonical = path_matches_baseline(state.get("protected_path"), CANONICAL_MASTER_PATH)
    check("j.acquire_event_path_matches_canonical_master", acquire_event_path_is_canonical, acquire_event.get("path") if acquire_event else None)
    check("j.protected_path_state_matches_canonical_master", protected_path_state_is_canonical, state.get("protected_path"))

    protected_path_is_canonical_master = bool(
        master_path_matches_canonical
        and master_hash_matches_canonical
        and acquire_event_path_is_canonical
        and protected_path_state_is_canonical
    )

    native_rebuild_matrix = native_enter_event.get("matrix") if native_enter_event else None
    composer_matrix = composer_enter_event.get("matrix") if composer_enter_event else None
    post_release_matrix = post_release_event.get("matrix") if post_release_event else None

    matrices_to_check_for_hygiene = [
        m for m in (report.get("baseline_matrix"), native_rebuild_matrix, composer_matrix, post_release_matrix)
        if m
    ]
    handle_hygiene_ok = bool(
        matrices_to_check_for_hygiene
        and all(matrix_all_probe_handles_closed(m) for m in matrices_to_check_for_hygiene)
    )

    context = {
        "baseline_matrix": report.get("baseline_matrix"),
        "acquire_call_count": state["acquire_call_count"],
        "acquire_succeeded": bool(acquire_event and acquire_event.get("success")),
        "native_rebuild_wrapper_installed": native_rebuild_wrap_ok,
        "native_rebuild_wrapper_call_count": state["native_rebuild_wrapper_call_count"],
        "native_rebuild_protection_active_at_return": bool(native_return_event and native_return_event.get("protection_active")),
        "protected_master_sha256_confirmed": protected_master_sha256_confirmed,
        "protected_path_is_canonical_master": protected_path_is_canonical_master,
        "native_rebuild_matrix": native_rebuild_matrix,
        "native_rebuild_returned_pass": native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS") is True,
        "composer_matrix": composer_matrix,
        "composer_returned_pass": find_event("composer_return") is not None,
        "release_call_count": state["release_call_count"],
        "post_release_matrix": post_release_matrix,
        "master_sha_before": master_sha_before,
        "master_sha_after": master_sha_after,
        "master_size_before": master_size_before,
        "master_size_after": master_size_after,
        "production_command_pass": production_command_pass,
        "open_handle_leak_detected": not handle_hygiene_ok,
        "harness_master_write_detected": (master_sha_after != master_sha_before),
        "event_order_valid": validate_event_order(events),
        "actual_runtime_api_version_matches": authority_evidence.get("runtime_api_version") == EXPECTED_RUNTIME_API_VERSION,
        "actual_runtime_build_id_matches": authority_evidence.get("runtime_build_id") == EXPECTED_RUNTIME_BUILD_ID,
        "authority_canonical": authority_evidence.get("is_canonical") is True,
        "authority_state_ready": authority_evidence.get("get_state") == "READY",
        "workload_identity_confirmed": workload_identity_confirmed,
        "production_log_scope_confirmed": log_scope_confirmed,
        "production_log_single_target_confirmed": log_single_target_ok,
        "production_log_single_native_rebuild_confirmed": log_single_native_rebuild_ok,
        "instrumentation_blocked_any_call": state.get("blocked_call_count", 0) > 0,
    }

    verdict, failed_checks = classify_j_verdict(context)
    report["j_verdict"] = verdict
    report["j_failed_checks"] = failed_checks
    report["context"] = context

    check("j.final_verdict_pass", verdict == "J_PASS", failed_checks)

except CheckpointJInstrumentationNotReadyError as instr_exc:
    # See this exception's own class docstring: PySide generally does not
    # propagate a Python exception raised from inside a Qt-deferred
    # callback back into this frame, so this clause exists only to handle
    # the case where it DOES -- the real fail-closed effect already
    # happened inside the guard regardless (the original method was never
    # called), and is independently visible via state["blocked_call_count"]
    # / the "target_transaction_blocked_not_ready" event either way.
    anomaly("Instrumentation-not-ready guard propagated to the outer frame: %s" % instr_exc)
    report["gate_failure"] = True
except CheckpointJError as gate_exc:
    if report.get("failure_phase") is None:
        report["failure_phase"] = "PRE_PRODUCTION_GATE"
    anomaly("GATE FAILURE (%s): %s" % (report["failure_phase"], gate_exc))
    report["gate_failure"] = True
except Exception as top_exc:
    anomaly("UNHANDLED TOP-LEVEL EXCEPTION: %s" % repr(top_exc))
    anomaly(traceback.format_exc())
    report["gate_failure"] = False

# ---------------------------------------------------------------------------
# Finalize / write output.
# ---------------------------------------------------------------------------

report["in_progress"] = False
report["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

all_checks_passed = all(c["pass"] for c in report["checks"]) if report["checks"] else False
completed_without_exception = not any(a.startswith("UNHANDLED TOP-LEVEL EXCEPTION") for a in ANOMALIES)
report["overall_pass"] = bool(
    all_checks_passed
    and completed_without_exception
    and report.get("j_verdict") == "J_PASS"
)

json_write_ok, json_write_error, _r = write_json_atomic(JSON_OUTPUT_PATH, report)
if not json_write_ok:
    anomaly("Final JSON write failed: %s" % json_write_error)

summary_lines = []
summary_lines.append("SFM CHECKPOINT J -- NATIVE PROTECTED-HANDLE QUALIFICATION")
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
if report.get("failure_phase"):
    summary_lines.append("failure_phase=%s" % report["failure_phase"])
if report.get("gate_failure"):
    summary_lines.append("*** GATE FAILURE: aborted before completing the qualification. ***")
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
summary_lines.append("J_VERDICT=%s" % report.get("j_verdict"))
summary_lines.append("J_FAILED_CHECKS=%r" % report.get("j_failed_checks"))
summary_lines.append("OVERALL_PASS=%r" % report["overall_pass"])
summary_lines.append("")
summary_lines.append("--- ANOMALIES (%d) ---" % len(ANOMALIES))
for a in ANOMALIES:
    summary_lines.append("- %s" % a)
if not ANOMALIES:
    summary_lines.append("(none)")
summary_lines.append("")
summary_lines.append("json_output_path=%s (write_ok=%r)" % (JSON_OUTPUT_PATH, json_write_ok))

summary_text = u"\n".join(summary_lines) + u"\n"
summary_write_ok, summary_write_error = write_text_atomic(SUMMARY_OUTPUT_PATH, summary_text.encode("ascii", "replace"))

try:
    sys.stdout.write(summary_text.encode("ascii", "replace"))
    sys.stdout.write(
        "\nCheckpoint J reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok)
    )
    sys.stdout.write("\nDO NOT SAVE. Restart SFM to discard this mutation.\n")
except Exception:
    pass
