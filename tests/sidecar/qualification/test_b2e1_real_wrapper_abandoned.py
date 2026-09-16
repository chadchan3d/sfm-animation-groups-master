# -*- coding: utf-8 -*-
"""R3-B2E1 Section 4: exercise the REAL production win_named_mutex
wrapper end to end with a genuinely real (not mocked) abandoned mutex.

Technique (proven correct via the low-level probe, Section 1-2): the
PARENT holds its OWN persistent, non-owning handle to the mutex open
BEFORE the child even starts, keeping the kernel object alive regardless
of what happens to the child's own handle. Without this, Windows destroys
the mutex object outright when its sole holder (the crashing child) dies,
and a subsequent CreateMutexW just creates a fresh, non-abandoned object
-- this was the root cause of the original non-trigger (see report).
"""
import ctypes
import json
import os
import subprocess
import sys
import time
import uuid
from ctypes import wintypes

sys.path.insert(0, r"E:\SFM Animation Group Master\tools")
from sfm_master_sidecar import win_named_mutex

_kernel32 = ctypes.windll.kernel32
_kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.CreateMutexW.restype = wintypes.HANDLE
_kernel32.CreateEventW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.CreateEventW.restype = wintypes.HANDLE
_kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_kernel32.WaitForSingleObject.restype = wintypes.DWORD
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]
_kernel32.ReleaseMutex.restype = wintypes.BOOL

_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
WAIT_OBJECT_0 = 0x0

PY3 = sys.executable
CHILD_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "real_wrapper_child.py")

results = []


def check(name, condition, detail=None):
    results.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


token = uuid.uuid4().hex[:12]
mutex_name = win_named_mutex.build_mutex_name("b2e1-real-wrapper-probe-%s" % token)
event_name = r"Global\SFM_B2E1_RealWrapperEvent_%s" % token
child_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "real_wrapper_child_log_%s.jsonl" % token)

print("mutex_name:", mutex_name)

# Parent's own persistent, non-owning handle -- created BEFORE the child,
# never released/closed until this script's own final cleanup.
parent_persistent_handle = _kernel32.CreateMutexW(None, False, mutex_name)
check("setup.1 parent's persistent handle created successfully",
      parent_persistent_handle is not None and parent_persistent_handle != _INVALID_HANDLE_VALUE)

env = dict(os.environ)
env["B2E1_CHILD_LOG"] = child_log

proc = subprocess.Popen([PY3, CHILD_SCRIPT, mutex_name, event_name], env=env)

event_handle = _kernel32.CreateEventW(None, True, False, event_name)
ev_wait = _kernel32.WaitForSingleObject(event_handle, 10000)
check("setup.2 child signaled ownership within 10s", ev_wait == WAIT_OBJECT_0, ev_wait)
_kernel32.CloseHandle(event_handle)

exit_code = proc.wait(timeout=15)
check("setup.3 child process terminated (exit_code=66, via os._exit)", exit_code == 66, exit_code)

# Now exercise the REAL PRODUCTION wrapper -- a SEPARATE
# WindowsNamedMutex instance, doing its own independent CreateMutexW +
# WaitForSingleObject internally, exactly as mutex_publisher.publish()
# would.
mtx = win_named_mutex.WindowsNamedMutex(mutex_name)
outcome = mtx.acquire(timeout_seconds=10.0)
check("wrapper.1 production wrapper reports OUTCOME_ACQUIRED_ABANDONED (real, not mocked)",
      outcome.kind == win_named_mutex.OUTCOME_ACQUIRED_ABANDONED, outcome.kind)
check("wrapper.2 the recovering wrapper instance now owns the mutex (handle set)",
      outcome.handle is not None)

# Release/close afterward is correct -- via the wrapper's own release().
mtx.release()
check("wrapper.3 release() completes without raising", True)

# Confirm the mutex is now genuinely free for a THIRD acquisition (proves
# release() actually worked, not just didn't crash).
mtx2 = win_named_mutex.WindowsNamedMutex(mutex_name)
outcome2 = mtx2.acquire(timeout_seconds=5.0)
check("wrapper.4 mutex is cleanly acquirable again after release() (kind == acquired, not abandoned/timeout)",
      outcome2.kind == win_named_mutex.OUTCOME_ACQUIRED, outcome2.kind)
mtx2.release()

_kernel32.CloseHandle(parent_persistent_handle)

child_events = []
if os.path.isfile(child_log):
    with open(child_log) as f:
        for line in f:
            line = line.strip()
            if line:
                child_events.append(json.loads(line))
print("child_events:", json.dumps(child_events, indent=2))
check("wrapper.5 child's own log confirms it acquired via the production wrapper before dying",
      any(e.get("phase") == "acquired_via_production_wrapper" and e.get("outcome_kind") == win_named_mutex.OUTCOME_ACQUIRED
          for e in child_events),
      child_events)

print()
failed = [n for n, ok in results if not ok]
print("RESULT: %d/%d %s" % (len(results) - len(failed), len(results), "ALL PASS" if not failed else "FAILED: %r" % (failed,)))
if failed:
    sys.exit(1)
