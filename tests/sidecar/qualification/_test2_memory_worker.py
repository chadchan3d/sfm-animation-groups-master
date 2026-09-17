# -*- coding: utf-8 -*-
"""Fresh-process worker for the Section 12 memory-methodology fix. Run
under real 32-bit Python 2.7.5. Performs exactly ONE broker acquisition
attempt, sampling real Windows process memory immediately before and
immediately after -- this process's own PeakPagefileUsage is therefore
guaranteed fresh (never inherited from any other case), since each case
gets its own brand-new interpreter process.

argv: master_path, shipped_root, comma_separated_wanted_folds
Prints exactly one JSON line (the last line of stdout) with the result.
"""
import ctypes
import json
import struct
import sys
from ctypes import wintypes

CORRECTION2_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction2"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"
for p in (CORRECTION2_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

_pointer_size = struct.calcsize("P")
if _pointer_size != 4:
    print(json.dumps({"outcome": "wrong_interpreter", "pointer_size": _pointer_size}))
    sys.exit(1)


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


def sample_memory():
    counters = PROCESS_MEMORY_COUNTERS_EX()
    counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
    ok = _psapi.GetProcessMemoryInfo(_self_handle, ctypes.byref(counters), counters.cb)
    if not ok:
        return None
    return {
        "working_set": int(counters.WorkingSetSize),
        "peak_working_set": int(counters.PeakWorkingSetSize),
        "pagefile_usage": int(counters.PagefileUsage),
        "peak_pagefile_usage": int(counters.PeakPagefileUsage),
        "private_bytes": int(counters.PrivateUsage),
    }


from sfm_master_authority_productionized import broker as broker_mod  # noqa: E402
from sfm_master_authority_productionized import normalizer_compat_adapter as adapter  # noqa: E402
from sfm_master_authority_productionized import errors  # noqa: E402

master_path = sys.argv[1]
shipped_root = sys.argv[2]
wanted_folds = frozenset(f.encode("utf-8") for f in sys.argv[3].split(","))

before = sample_memory()
b = broker_mod.Broker(api_version="test-t2mem-worker")
try:
    b.acquire_or_reuse_views(
        master_path, {"normalizer": (wanted_folds, adapter.build_targeted_master_compatible_projection(wanted_folds))},
        shipped_root=shipped_root, runtime_cap_bytes=4 * 1024 * 1024,
    )
    outcome = "admitted"
    reason = None
except errors.ResourceAdmissionRefusal as exc:
    outcome = "refused"
    reason = str(exc)
after = sample_memory()

print(json.dumps({
    "outcome": outcome, "reason": reason,
    "before": before, "after": after,
}, sort_keys=True))
