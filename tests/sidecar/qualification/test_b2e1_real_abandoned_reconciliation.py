# -*- coding: utf-8 -*-
"""R3-B2E1 Section 5: exercise abandoned-state reconciliation through a
REAL, non-mocked abandoned mutex inside a real mutex_publisher.publish()
call. Uses isolated temporary generated-root/pointer fixtures only.
"""
import ctypes
import json
import os
import shutil
import subprocess
import sys
import uuid
from ctypes import wintypes

sys.path.insert(0, r"E:\SFM Animation Group Master\tools")
from sfm_master_sidecar import mutex_publisher, manifest as manifest_module, win_named_mutex

_kernel32 = ctypes.windll.kernel32
_kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.CreateMutexW.restype = wintypes.HANDLE
_kernel32.CreateEventW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.CreateEventW.restype = wintypes.HANDLE
_kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_kernel32.WaitForSingleObject.restype = wintypes.DWORD
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
WAIT_OBJECT_0 = 0x0

PY3 = sys.executable
CHILD_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "real_wrapper_child.py")

REAL_MASTER = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
CUSTOM_MASTER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_master_fixture")
os.makedirs(CUSTOM_MASTER_DIR, exist_ok=True)
CUSTOM_MASTER = os.path.join(CUSTOM_MASTER_DIR, "custom_master.txt")
with open(CUSTOM_MASTER, "wb") as f:
    f.write(b'"RigLegs"\n{\n\t"control"\t\t"CustomFixtureControl"\n}\n')

SCRATCH_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recon_out")
if os.path.isdir(SCRATCH_ROOT):
    shutil.rmtree(SCRATCH_ROOT)
os.makedirs(SCRATCH_ROOT)

results = []


def check(name, condition, detail=None):
    results.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


def fresh_dir(name):
    d = os.path.join(SCRATCH_ROOT, name)
    os.makedirs(d, exist_ok=True)
    return d


class RealAbandonedMutexArranger(object):
    """Arranges a genuinely real (never mocked) abandoned mutex for the
    EXACT mutex name `mutex_publisher.publish()` will independently
    compute for a given slot identity, using the persistent-parent-handle
    technique proven necessary in Section 1-2. `__enter__` returns once
    the mutex is confirmed abandoned-and-ready; `__exit__` releases the
    parent's own persistent handle."""

    def __init__(self, slot_identity):
        self.slot_identity = slot_identity
        self.mutex_name = win_named_mutex.build_mutex_name(slot_identity)
        self._persistent_handle = None

    def __enter__(self):
        token = uuid.uuid4().hex[:10]
        event_name = r"Global\SFM_B2E1_ReconEvent_%s" % token
        child_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recon_child_log_%s.jsonl" % token)

        self._persistent_handle = _kernel32.CreateMutexW(None, False, self.mutex_name)
        if self._persistent_handle is None or self._persistent_handle == _INVALID_HANDLE_VALUE:
            raise RuntimeError("failed to pre-create persistent handle for %r" % self.mutex_name)

        env = dict(os.environ)
        env["B2E1_CHILD_LOG"] = child_log
        proc = subprocess.Popen([PY3, CHILD_SCRIPT, self.mutex_name, event_name], env=env)

        event_handle = _kernel32.CreateEventW(None, True, False, event_name)
        ev_wait = _kernel32.WaitForSingleObject(event_handle, 10000)
        _kernel32.CloseHandle(event_handle)
        if ev_wait != WAIT_OBJECT_0:
            raise RuntimeError("child never signaled ownership")
        exit_code = proc.wait(timeout=15)
        if exit_code != 66:
            raise RuntimeError("child did not exit as expected (code=%r)" % exit_code)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._persistent_handle is not None:
            _kernel32.CloseHandle(self._persistent_handle)
            self._persistent_handle = None
        return False


# ===========================================================================
# Scenario 1: primary valid / backup valid -- abandoned recovery proceeds normally
# ===========================================================================
print("=== Scenario 1: primary valid, backup valid ===")
out1 = fresh_dir("scenario1_valid_valid")
slot1 = "recon-scenario1-%s" % uuid.uuid4().hex[:8]

# First, a normal publish (no abandonment) to create a valid primary AND
# a valid backup (a second publish of a DIFFERENT source creates a .bak
# preserving the first).
mutex_publisher.publish(REAL_MASTER, out1, mutex_slot_identity=slot1)
mutex_publisher.publish(CUSTOM_MASTER, out1, mutex_slot_identity=slot1)
primary_before = mutex_publisher.read_active_manifest(out1)
check("scenario1.1 both a valid primary and a valid backup exist before the abandoned recovery",
      primary_before is not None and os.path.isfile(os.path.join(out1, mutex_publisher.BACKUP_MANIFEST_BASENAME)))

with RealAbandonedMutexArranger(slot1):
    result1 = mutex_publisher.publish(REAL_MASTER, out1, mutex_slot_identity=slot1)

check("scenario1.2 publish() reports a REAL (non-mocked) abandoned acquisition",
      result1.mutex_outcome_kind == win_named_mutex.OUTCOME_ACQUIRED_ABANDONED, result1.mutex_outcome_kind)
check("scenario1.3 reconciliation reports primary_valid=True, backup_valid=True",
      result1.abandoned_reconciliation["primary_valid"] is True
      and result1.abandoned_reconciliation["backup_valid"] is True, result1.abandoned_reconciliation)
check("scenario1.4 publish() completed successfully despite the real abandonment", result1.manifest_path.exists())


# ===========================================================================
# Scenario 2: primary corrupt / backup valid -- recovery still proceeds
# (a fresh, independently-validated commit is about to replace the corrupt
# primary anyway; the backup's validity is what matters for confidence)
# ===========================================================================
print("=== Scenario 2: primary corrupt, backup valid ===")
out2 = fresh_dir("scenario2_corrupt_valid")
slot2 = "recon-scenario2-%s" % uuid.uuid4().hex[:8]
mutex_publisher.publish(REAL_MASTER, out2, mutex_slot_identity=slot2)
mutex_publisher.publish(CUSTOM_MASTER, out2, mutex_slot_identity=slot2)  # creates a valid backup of the official gen
primary_path2 = os.path.join(out2, mutex_publisher.MANIFEST_BASENAME)
with open(primary_path2, "wb") as f:
    f.write(b"{not valid json")

with RealAbandonedMutexArranger(slot2):
    result2 = mutex_publisher.publish(REAL_MASTER, out2, mutex_slot_identity=slot2)

check("scenario2.1 publish() reports a REAL abandoned acquisition",
      result2.mutex_outcome_kind == win_named_mutex.OUTCOME_ACQUIRED_ABANDONED)
check("scenario2.2 reconciliation correctly reports primary_valid=False, backup_valid=True",
      result2.abandoned_reconciliation["primary_valid"] is False
      and result2.abandoned_reconciliation["backup_valid"] is True, result2.abandoned_reconciliation)
check("scenario2.3 publish() still completed (backup gave confidence prior state was recoverable)",
      result2.manifest_path.exists())


# ===========================================================================
# Scenario 3: primary references a missing/corrupt artifact / backup valid
# ===========================================================================
print("=== Scenario 3: primary references missing artifact, backup valid ===")
out3 = fresh_dir("scenario3_missingartifact_valid")
slot3 = "recon-scenario3-%s" % uuid.uuid4().hex[:8]
mutex_publisher.publish(REAL_MASTER, out3, mutex_slot_identity=slot3)
mutex_publisher.publish(CUSTOM_MASTER, out3, mutex_slot_identity=slot3)
primary_data3 = mutex_publisher.read_active_manifest(out3)
gen_path3 = manifest_module.resolve_generation_path(out3, primary_data3)
os.remove(gen_path3)  # primary's manifest now references a MISSING artifact

with RealAbandonedMutexArranger(slot3):
    result3 = mutex_publisher.publish(REAL_MASTER, out3, mutex_slot_identity=slot3)

check("scenario3.1 publish() reports a REAL abandoned acquisition",
      result3.mutex_outcome_kind == win_named_mutex.OUTCOME_ACQUIRED_ABANDONED)
check("scenario3.2 reconciliation correctly reports primary_valid=False (missing artifact) backup_valid=True",
      result3.abandoned_reconciliation["primary_valid"] is False
      and result3.abandoned_reconciliation["backup_valid"] is True, result3.abandoned_reconciliation)
check("scenario3.3 publish() still completed", result3.manifest_path.exists())


# ===========================================================================
# Scenario 4: both pointers unusable -> explicit failure (the NEW required gate)
# ===========================================================================
print("=== Scenario 4: both pointers unusable -> explicit failure ===")
out4 = fresh_dir("scenario4_both_unusable")
slot4 = "recon-scenario4-%s" % uuid.uuid4().hex[:8]
mutex_publisher.publish(REAL_MASTER, out4, mutex_slot_identity=slot4)
mutex_publisher.publish(CUSTOM_MASTER, out4, mutex_slot_identity=slot4)  # creates backup
primary_path4 = os.path.join(out4, mutex_publisher.MANIFEST_BASENAME)
backup_path4 = os.path.join(out4, mutex_publisher.BACKUP_MANIFEST_BASENAME)
with open(primary_path4, "wb") as f:
    f.write(b"{also not valid")
with open(backup_path4, "wb") as f:
    f.write(b"{also not valid either")

raised4 = False
detail4 = None
try:
    with RealAbandonedMutexArranger(slot4):
        mutex_publisher.publish(REAL_MASTER, out4, mutex_slot_identity=slot4)
except mutex_publisher.AbandonedStateUnrecoverableError as exc:
    raised4 = True
    detail4 = str(exc)
check("scenario4.1 publish() raises AbandonedStateUnrecoverableError when BOTH are unusable AND prior state existed",
      raised4, detail4)
# The generation file compiled for THIS failed attempt is expected to
# remain as a harmless orphan (no automatic GC) -- confirmed in Scenario 5.
check("scenario4.2 the pre-existing (corrupt) primary/backup files were left untouched, not silently replaced",
      open(primary_path4, "rb").read() == b"{also not valid"
      and open(backup_path4, "rb").read() == b"{also not valid either")


# ===========================================================================
# Scenario 5: already-published immutable artifact present after pre-pointer crash
# ===========================================================================
print("=== Scenario 5: immutable artifact survives a pre-pointer-commit crash (orphan, no GC) ===")
out5 = fresh_dir("scenario5_orphan_artifact")
slot5 = "recon-scenario5-%s" % uuid.uuid4().hex[:8]


def _crash_before_manifest_replace(stage):
    if stage == "before_manifest_replace":
        raise RuntimeError("simulated crash after generation publication, before pointer commit")


raised5 = False
try:
    mutex_publisher.publish(REAL_MASTER, out5, mutex_slot_identity=slot5, _fault_hook=_crash_before_manifest_replace)
except RuntimeError:
    raised5 = True
check("scenario5.1 the simulated crash propagated as expected", raised5)

check("scenario5.2 no manifest exists (pointer commit never happened)",
      mutex_publisher.read_active_manifest(out5) is None)

from sfm_master_sidecar import compiler as compiler_module
snapshot5 = compiler_module.capture_source_snapshot(REAL_MASTER)
outcome5 = compiler_module.parse_and_compile(snapshot5)
expected_basename5 = compiler_module.generation_basename(outcome5.ordinary_sha256)
expected_path5 = os.path.join(out5, expected_basename5)
check("scenario5.3 the immutable generation file DOES still exist on disk as an orphan (no automatic GC)",
      os.path.isfile(expected_path5), expected_path5)
check("scenario5.4 the orphaned artifact's content matches the real recompiled bytes exactly",
      open(expected_path5, "rb").read() == outcome5.blob)

# A subsequent, non-crashing publish must reuse this orphan rather than
# recompiling/re-publishing a duplicate.
result5b = mutex_publisher.publish(REAL_MASTER, out5, mutex_slot_identity=slot5)
check("scenario5.5 a later successful publish reuses the orphaned generation file (result.reused == True)",
      result5b.reused is True, result5b.reused)


print()
failed = [n for n, ok in results if not ok]
print("RESULT: %d/%d %s" % (len(results) - len(failed), len(results), "ALL PASS" if not failed else "FAILED: %r" % (failed,)))
if failed:
    sys.exit(1)
