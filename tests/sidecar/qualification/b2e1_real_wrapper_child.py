# -*- coding: utf-8 -*-
"""R3-B2E1 Section 4 -- child process that acquires the mutex through the
REAL PRODUCTION win_named_mutex.WindowsNamedMutex wrapper (not raw
ctypes), signals ownership via a named Event, then dies without
releasing. Usage: python real_wrapper_child.py <mutex_name> <event_name>
"""
import ctypes
import json
import os
import sys
from ctypes import wintypes

sys.path.insert(0, r"E:\SFM Animation Group Master\tools")
from sfm_master_sidecar import win_named_mutex

_kernel32 = ctypes.windll.kernel32
_kernel32.CreateEventW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.CreateEventW.restype = wintypes.HANDLE
_kernel32.SetEvent.argtypes = [wintypes.HANDLE]
_kernel32.SetEvent.restype = wintypes.BOOL

RESULT_LOG = os.environ.get("B2E1_CHILD_LOG")


def _log(record):
    if RESULT_LOG:
        with open(RESULT_LOG, "a") as f:
            f.write(json.dumps(record) + "\n")


def main():
    mutex_name = sys.argv[1]
    event_name = sys.argv[2]
    pid = os.getpid()
    _log({"phase": "start", "pid": pid, "mutex_name": mutex_name})

    mtx = win_named_mutex.WindowsNamedMutex(mutex_name)
    outcome = mtx.acquire(timeout_seconds=10.0)
    _log({"phase": "acquired_via_production_wrapper", "pid": pid, "outcome_kind": outcome.kind})

    event_handle = _kernel32.CreateEventW(None, True, False, event_name)
    _kernel32.SetEvent(event_handle)
    _log({"phase": "signaled_ownership", "pid": pid})

    os._exit(66)  # die without mtx.release()


if __name__ == "__main__":
    main()
