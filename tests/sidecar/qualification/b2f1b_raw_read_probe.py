# -*- coding: utf-8 -*-
"""R3-B2F1B Section 3: isolated, no-broker/no-validation probe of raw
file.read(size) allocation behavior under real Python 2.7.5, comparing
requested-read-size vs actual-bytes-returned peak memory cost. Each case
(A/B/C) MUST be run as its own fresh process (invoked separately) for
true isolation -- pass the case letter as argv[1].

Usage: python b2f1b_raw_read_probe.py A|B|C <path_to_fixtureA_1p5x.sfmsidecar>
"""
import ctypes
import json
import os
import sys
from ctypes import wintypes


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


_kernel32 = ctypes.windll.kernel32
_psapi = ctypes.windll.psapi
_kernel32.GetCurrentProcess.restype = wintypes.HANDLE
_psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
_psapi.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD,
]
_self_handle = _kernel32.GetCurrentProcess()


def counters():
    c = PROCESS_MEMORY_COUNTERS_EX()
    c.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
    ok = _psapi.GetProcessMemoryInfo(_self_handle, ctypes.byref(c), c.cb)
    if not ok:
        return None
    return {
        "working_set": int(c.WorkingSetSize),
        "peak_working_set": int(c.PeakWorkingSetSize),
        "pagefile_usage": int(c.PagefileUsage),
        "peak_pagefile_usage": int(c.PeakPagefileUsage),
        "private_bytes": int(c.PrivateUsage),
    }


def main():
    case = sys.argv[1]
    path = sys.argv[2]
    actual_size = os.path.getsize(path)

    if case == "A":
        read_size = 16 * 1024 * 1024 + 1
    elif case == "B":
        read_size = 64 * 1024 * 1024 + 1
    elif case == "C":
        read_size = actual_size + 1
    else:
        raise ValueError("case must be A, B, or C")

    before = counters()

    f = open(path, "rb")
    try:
        data = f.read(read_size)
    finally:
        f.close()
    returned_len = len(data)
    del data

    after = counters()

    result = {
        "case": case,
        "path": path,
        "actual_file_size": actual_size,
        "requested_read_size": read_size,
        "returned_len": returned_len,
        "before": before,
        "after": after,
        "peak_pagefile_delta": after["peak_pagefile_usage"] - before["peak_pagefile_usage"],
        "peak_working_set_delta": after["peak_working_set"] - before["peak_working_set"],
        "private_bytes_delta_after_close": after["private_bytes"] - before["private_bytes"],
        "python_version": sys.version,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
