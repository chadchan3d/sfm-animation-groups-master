# -*- coding: utf-8 -*-
"""R3-B2E1 low-level abandoned-mutex probe -- PARENT process.

Spawns abandoned_mutex_child.py as a real separate process, waits for it
to positively confirm mutex ownership via a named Event (never via a
timing guess), confirms the child has actually terminated, then opens
the SAME named mutex and calls WaitForSingleObject with a bounded
timeout, recording the exact return code.

Two independent runs: `os._exit` death and parent-driven
`TerminateProcess` death.
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
_kernel32.OpenMutexW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.OpenMutexW.restype = wintypes.HANDLE
_kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_kernel32.WaitForSingleObject.restype = wintypes.DWORD
_kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]
_kernel32.ReleaseMutex.restype = wintypes.BOOL
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.CreateEventW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.CreateEventW.restype = wintypes.HANDLE
_kernel32.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.OpenEventW.restype = wintypes.HANDLE
_kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
_kernel32.TerminateProcess.restype = wintypes.BOOL
_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.OpenProcess.restype = wintypes.HANDLE

WAIT_OBJECT_0 = 0x0
WAIT_ABANDONED = 0x80
WAIT_TIMEOUT = 0x102
WAIT_FAILED = 0xFFFFFFFF
INFINITE = 0xFFFFFFFF
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
EVENT_ALL_ACCESS = 0x1F0003
SYNCHRONIZE = 0x00100000
PROCESS_TERMINATE = 0x0001

_RESULT_NAMES = {WAIT_OBJECT_0: "WAIT_OBJECT_0", WAIT_ABANDONED: "WAIT_ABANDONED", WAIT_TIMEOUT: "WAIT_TIMEOUT", WAIT_FAILED: "WAIT_FAILED"}

PY3 = sys.executable
CHILD_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "abandoned_mutex_child.py")


def run_one_trial(mode):
    token = uuid.uuid4().hex[:12]
    mutex_name = r"Global\SFM_B2E1_Probe_%s_%s" % (mode, token)
    event_name = r"Global\SFM_B2E1_ProbeEvent_%s_%s" % (mode, token)
    child_log = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "child_log_%s_%s.jsonl" % (mode, token)
    )
    if os.path.isfile(child_log):
        os.remove(child_log)

    env = dict(os.environ)
    env["B2E1_CHILD_LOG"] = child_log

    print("=== trial mode=%s mutex_name=%r ===" % (mode, mutex_name))

    # BUG FIX (found via this exact probe, see report): the PARENT must
    # create the named Event BEFORE spawning the child and keep its own
    # handle open throughout. If only the child ever held a handle to the
    # event, `os._exit()` (which drops ALL of that process's handles) can
    # destroy the kernel object itself before the parent gets a chance to
    # open it -- a real race, lost almost every time in "exit" mode since
    # the child signals-then-immediately-exits with no delay. Keeping the
    # parent's own handle open the whole time keeps the object alive
    # regardless of what the child does to its own handle.
    event_handle = _kernel32.CreateEventW(None, True, False, event_name)
    if event_handle is None or event_handle == _INVALID_HANDLE_VALUE:
        return {"mode": mode, "error": "parent CreateEventW failed, GetLastError=%d" % ctypes.GetLastError()}

    proc = subprocess.Popen([PY3, CHILD_SCRIPT, mutex_name, event_name, mode], env=env)

    ev_wait = _kernel32.WaitForSingleObject(event_handle, 10000)
    if ev_wait != WAIT_OBJECT_0:
        return {"mode": mode, "error": "child never signaled ownership (event wait=%r)" % ev_wait}
    _kernel32.CloseHandle(event_handle)
    print("  child confirmed mutex ownership (pid=%d)" % proc.pid)

    if mode == "terminate":
        # Give the child a moment to actually enter its sleep (it signaled
        # the event just before sleeping) then kill it externally, hard,
        # via TerminateProcess -- not Python's own .kill()/.terminate()
        # wrapper indirection, to match the prompt's exact requirement.
        time.sleep(0.3)
        h_proc = _kernel32.OpenProcess(PROCESS_TERMINATE, False, proc.pid)
        if h_proc is None or h_proc == _INVALID_HANDLE_VALUE:
            return {"mode": mode, "error": "OpenProcess(PROCESS_TERMINATE) failed, GetLastError=%d" % ctypes.GetLastError()}
        ok = _kernel32.TerminateProcess(h_proc, 0xDEAD)
        terminate_err = ctypes.GetLastError()
        _kernel32.CloseHandle(h_proc)
        print("  TerminateProcess ok=%r GetLastError=%d" % (bool(ok), terminate_err))

    # Confirm the child process has actually terminated (wait on its
    # process handle via subprocess, which is the parent-owned handle from
    # Popen -- this IS a real Win32 process handle under the hood).
    exit_code = proc.wait(timeout=15)
    print("  child process confirmed terminated, exit_code=%r" % exit_code)

    # Now: open the SAME named mutex and wait on it with a bounded timeout.
    handle2 = _kernel32.CreateMutexW(None, False, mutex_name)
    create2_err = ctypes.GetLastError()
    if handle2 is None or handle2 == _INVALID_HANDLE_VALUE:
        return {"mode": mode, "error": "parent CreateMutexW failed, GetLastError=%d" % ctypes.GetLastError()}

    parent_result = _kernel32.WaitForSingleObject(handle2, 10000)
    parent_wait_err = ctypes.GetLastError()
    print("  parent WaitForSingleObject result=%r (%s) GetLastError=%d" % (
        parent_result, _RESULT_NAMES.get(parent_result, "UNKNOWN"), parent_wait_err))

    if parent_result in (WAIT_OBJECT_0, WAIT_ABANDONED):
        _kernel32.ReleaseMutex(handle2)
    _kernel32.CloseHandle(handle2)

    # Read the child's own structured log for corroboration.
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
        "already_existed_at_create2": (create2_err == 183),
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
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "abandoned_mutex_probe_result.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print("\nwrote", out_path)


if __name__ == "__main__":
    main()
