# -*- coding: utf-8 -*-
"""R3-B2E1 low-level abandoned-mutex probe -- CHILD process.

Bypasses win_named_mutex.py / mutex_publisher.py entirely. Uses raw
Win32 primitives directly:
  1. CreateMutexW(NULL, FALSE, name) -- create/open, not initially owned.
  2. WaitForSingleObject(handle, INFINITE) -- actually acquire ownership.
  3. Record PID, handle value, mutex name, wait return, GetLastError().
  4. Signal the parent via a SEPARATE named Event (never reuse the mutex
     itself for signaling -- that would confound the very thing under
     test) -- signaled ONLY after ownership is positively confirmed.
  5. Die WITHOUT calling ReleaseMutex -- via os._exit(unusual-code), or
     (for the TerminateProcess variant) just spin/sleep forever waiting
     to be killed externally by the parent.

Usage: python abandoned_mutex_child.py <mutex_name> <event_name> <mode>
  mode = "exit"      -> die via os._exit(66) after acquiring + signaling
  mode = "terminate" -> acquire + signal + sleep, awaiting external
                        TerminateProcess from the parent
"""
import ctypes
import json
import os
import sys
import time
from ctypes import wintypes

_kernel32 = ctypes.windll.kernel32
_kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.CreateMutexW.restype = wintypes.HANDLE
_kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_kernel32.WaitForSingleObject.restype = wintypes.DWORD
_kernel32.CreateEventW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
_kernel32.CreateEventW.restype = wintypes.HANDLE
_kernel32.SetEvent.argtypes = [wintypes.HANDLE]
_kernel32.SetEvent.restype = wintypes.BOOL

WAIT_OBJECT_0 = 0x0
WAIT_ABANDONED = 0x80
WAIT_TIMEOUT = 0x102
WAIT_FAILED = 0xFFFFFFFF
INFINITE = 0xFFFFFFFF
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

RESULT_LOG = os.environ.get("B2E1_CHILD_LOG")


def _log(record):
    if RESULT_LOG:
        with open(RESULT_LOG, "a") as f:
            f.write(json.dumps(record) + "\n")


def main():
    mutex_name = sys.argv[1]
    event_name = sys.argv[2]
    mode = sys.argv[3]

    pid = os.getpid()
    _log({"phase": "start", "pid": pid, "mutex_name": mutex_name, "mode": mode})

    handle = _kernel32.CreateMutexW(None, False, mutex_name)
    create_err = ctypes.GetLastError()
    if handle is None or handle == _INVALID_HANDLE_VALUE:
        _log({"phase": "create_failed", "pid": pid, "GetLastError": create_err})
        sys.exit(1)
    _log({"phase": "created", "pid": pid, "handle": int(handle), "GetLastError_after_create": create_err,
          "already_existed": (create_err == 183)})  # ERROR_ALREADY_EXISTS == 183

    wait_result = _kernel32.WaitForSingleObject(handle, INFINITE)
    wait_err = ctypes.GetLastError()
    _log({"phase": "waited", "pid": pid, "wait_result": wait_result, "GetLastError_after_wait": wait_err})

    if wait_result not in (WAIT_OBJECT_0, WAIT_ABANDONED):
        _log({"phase": "acquire_failed", "pid": pid, "wait_result": wait_result})
        sys.exit(2)

    # Ownership confirmed (WAIT_OBJECT_0 or, if this child itself received
    # an abandoned mutex from some earlier run, WAIT_ABANDONED still means
    # THIS thread now owns it) -- open/signal the event ONLY now.
    event_handle = _kernel32.CreateEventW(None, True, False, event_name)
    if event_handle is None or event_handle == _INVALID_HANDLE_VALUE:
        _log({"phase": "event_create_failed", "pid": pid, "GetLastError": ctypes.GetLastError()})
        sys.exit(3)
    ok = _kernel32.SetEvent(event_handle)
    _log({"phase": "signaled_ownership", "pid": pid, "set_event_ok": bool(ok)})

    if mode == "exit":
        _log({"phase": "about_to_os_exit", "pid": pid})
        os._exit(66)
    elif mode == "terminate":
        _log({"phase": "sleeping_for_external_termination", "pid": pid})
        time.sleep(60)  # parent will TerminateProcess us well before this elapses
        _log({"phase": "woke_up_unexpectedly", "pid": pid})
        sys.exit(4)
    else:
        _log({"phase": "unknown_mode", "pid": pid, "mode": mode})
        sys.exit(5)


if __name__ == "__main__":
    main()
