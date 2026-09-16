# -*- coding: utf-8 -*-
"""R3-B2E1 low-level probe v2 -- tests the HYPOTHESIS that WAIT_ABANDONED
is only observable if some handle to the SAME mutex kernel object remains
open (elsewhere) at the moment the owning process dies. If the crashing
process is the ONLY handle-holder, Windows destroys the kernel object
outright on process death (refcount to zero) -- the next CreateMutexW
with the same name then creates a brand-new, non-abandoned object.

This version has the PARENT open its OWN handle to the mutex (via
CreateMutexW, non-owning -- it does NOT call WaitForSingleObject on it
yet) BEFORE spawning the child, and keeps that handle open across the
child's entire lifetime. Only AFTER the child has confirmed ownership
and then died does the parent call WaitForSingleObject on its
ALREADY-OPEN handle.
"""
import ctypes
import json
import os
import subprocess
import sys
import time
import uuid
from ctypes import wintypes

_kernel32 = ctypes.windll.kernel32
_kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.CreateMutexW.restype = wintypes.HANDLE
_kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_kernel32.WaitForSingleObject.restype = wintypes.DWORD
_kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]
_kernel32.ReleaseMutex.restype = wintypes.BOOL
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.CreateEventW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.CreateEventW.restype = wintypes.HANDLE
_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.OpenProcess.restype = wintypes.HANDLE
_kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
_kernel32.TerminateProcess.restype = wintypes.BOOL

WAIT_OBJECT_0 = 0x0
WAIT_ABANDONED = 0x80
WAIT_TIMEOUT = 0x102
WAIT_FAILED = 0xFFFFFFFF
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
PROCESS_TERMINATE = 0x0001
ERROR_ALREADY_EXISTS = 183

_RESULT_NAMES = {WAIT_OBJECT_0: "WAIT_OBJECT_0", WAIT_ABANDONED: "WAIT_ABANDONED", WAIT_TIMEOUT: "WAIT_TIMEOUT", WAIT_FAILED: "WAIT_FAILED"}

PY3 = sys.executable
CHILD_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "abandoned_mutex_child.py")


def run_one_trial(mode):
    token = uuid.uuid4().hex[:12]
    mutex_name = r"Global\SFM_B2E1_ProbeV2_%s_%s" % (mode, token)
    event_name = r"Global\SFM_B2E1_ProbeV2Event_%s_%s" % (mode, token)
    child_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "child_log_v2_%s_%s.jsonl" % (mode, token))

    env = dict(os.environ)
    env["B2E1_CHILD_LOG"] = child_log

    print("=== v2 trial mode=%s mutex_name=%r ===" % (mode, mutex_name))

    # PARENT pre-opens its own handle to the mutex FIRST, before the child
    # even exists, and NEVER closes it until after this trial's final
    # wait. This handle keeps the kernel object alive regardless of what
    # happens to the child's own handle.
    parent_handle = _kernel32.CreateMutexW(None, False, mutex_name)
    parent_create_err = ctypes.GetLastError()
    if parent_handle is None or parent_handle == _INVALID_HANDLE_VALUE:
        return {"mode": mode, "error": "parent CreateMutexW (pre-open) failed, GetLastError=%d" % ctypes.GetLastError()}
    print("  parent pre-opened its own handle to the mutex (GetLastError=%d, i.e. %s)" % (
        parent_create_err, "ALREADY_EXISTS (unexpected this early)" if parent_create_err == ERROR_ALREADY_EXISTS else "created fresh, as expected"))

    event_handle = _kernel32.CreateEventW(None, True, False, event_name)
    if event_handle is None or event_handle == _INVALID_HANDLE_VALUE:
        return {"mode": mode, "error": "parent CreateEventW failed"}

    proc = subprocess.Popen([PY3, CHILD_SCRIPT, mutex_name, event_name, mode], env=env)

    ev_wait = _kernel32.WaitForSingleObject(event_handle, 10000)
    if ev_wait != WAIT_OBJECT_0:
        return {"mode": mode, "error": "child never signaled ownership (event wait=%r)" % ev_wait}
    _kernel32.CloseHandle(event_handle)
    print("  child confirmed mutex ownership (pid=%d)" % proc.pid)

    if mode == "terminate":
        time.sleep(0.3)
        h_proc = _kernel32.OpenProcess(PROCESS_TERMINATE, False, proc.pid)
        ok = _kernel32.TerminateProcess(h_proc, 0xDEAD)
        _kernel32.CloseHandle(h_proc)
        print("  TerminateProcess ok=%r" % bool(ok))

    exit_code = proc.wait(timeout=15)
    print("  child process confirmed terminated, exit_code=%r" % exit_code)

    # Now wait on the PARENT'S OWN, ALREADY-OPEN handle -- never a fresh
    # CreateMutexW call this time, since the whole point is that this
    # handle has been open continuously since before the child started.
    parent_result = _kernel32.WaitForSingleObject(parent_handle, 10000)
    parent_wait_err = ctypes.GetLastError()
    print("  parent WaitForSingleObject (on its PRE-EXISTING handle) result=%r (%s) GetLastError=%d" % (
        parent_result, _RESULT_NAMES.get(parent_result, "UNKNOWN"), parent_wait_err))

    if parent_result in (WAIT_OBJECT_0, WAIT_ABANDONED):
        _kernel32.ReleaseMutex(parent_handle)
    _kernel32.CloseHandle(parent_handle)

    child_events = []
    if os.path.isfile(child_log):
        with open(child_log) as f:
            for line in f:
                line = line.strip()
                if line:
                    child_events.append(json.loads(line))

    return {
        "mode": mode,
        "mutex_name": mutex_name,
        "child_pid": proc.pid,
        "child_exit_code": exit_code,
        "parent_precreate_GetLastError": parent_create_err,
        "parent_wait_result": parent_result,
        "parent_wait_result_name": _RESULT_NAMES.get(parent_result, "UNKNOWN(0x%x)" % parent_result),
        "parent_wait_GetLastError": parent_wait_err,
        "child_events": child_events,
    }


def main():
    results = {}
    results["exit"] = run_one_trial("exit")
    print()
    results["terminate"] = run_one_trial("terminate")
    print()
    print(json.dumps(results, indent=2))
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "abandoned_mutex_probe_v2_result.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print("\nwrote", out_path)


if __name__ == "__main__":
    main()
