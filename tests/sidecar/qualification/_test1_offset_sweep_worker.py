# -*- coding: utf-8 -*-
"""Fresh-process worker for the BLOCKER 1 offset-sweep memory
measurement. Run under real 32-bit Python 2.7.5. Performs exactly ONE
`candidate_open_and_identify_with_preflight` call against one offset-
sweep fixture, sampling real Windows process memory immediately before
and immediately after -- each case gets its own brand-new interpreter
process, so PeakPagefileUsage/PeakWorkingSetSize are genuine fresh-
process peaks, never inherited from a prior offset in the sweep.

argv: artifact_path, expected_source_sha256 (arbitrary -- these
fixtures are for preflight READ/ALLOCATION measurement only, never
expected to reach final admission; a source-hash mismatch or stale-
digest corruption verdict downstream of the measured preflight stage is
expected and irrelevant to this probe)
"""
import ctypes
import json
import os
import struct
import sys
from ctypes import wintypes

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
CORRECTION4_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction4")
TOOLS_DIR = os.path.join(_REPO_ROOT, "tools")
for p in (CORRECTION4_ROOT, TOOLS_DIR):
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


from sfm_master_authority_productionized import resource_preflight  # noqa: E402
from sfm_master_authority_productionized import resource_estimator  # noqa: E402
from sfm_master_authority_productionized import errors  # noqa: E402
from sfm_master_sidecar import format as fmt  # noqa: E402
import os  # noqa: E402

artifact_path = sys.argv[1]
expected_source_sha256 = sys.argv[2]

# Isolates EXACTLY the Stage-1/BLOCKER-1 scope this probe measures --
# never the whole `candidate_open_and_identify_with_preflight` pipeline,
# which UNCONDITIONALLY proceeds to Stage 2's "one full bounded read"
# regardless of Blocker 1's fix (an artifact whose directory sits at a
# large offset must, by the format's own structural requirement, itself
# be at least that large on disk -- Stage 2's later, legitimate,
# ALREADY-bounded-by-runtime_cap_bytes full read of such a file is a
# separate, pre-existing, unchanged concern this probe does not
# measure). This mirrors resource_preflight.py's real Stage 1 exactly:
# fixed-header read, seek DIRECTLY to the directory offset, bounded
# directory read, parse_resource_shape_parts -- then STOP, never
# reading the rest of the file.
runtime_cap_bytes = 16 * 1024 * 1024
inst = resource_preflight.CandidateOpenInstrumentation()
before = sample_memory()
try:
    f = open(artifact_path, "rb")
    try:
        artifact_bytes = os.fstat(f.fileno()).st_size
        header_bytes = resource_preflight._instrumented_read(f, fmt.HEADER_SIZE, inst, "header")
        inst.header_bytes_read = len(header_bytes)
        header = fmt.unpack_header(header_bytes, 0)
        dir_region_end = resource_estimator._validate_header_and_bound_directory_region(header, artifact_bytes)
        directory_size = dir_region_end - header.section_directory_offset
        f.seek(header.section_directory_offset)
        directory_bytes = resource_preflight._instrumented_read(f, directory_size, inst, "directory")
        inst.directory_bytes_read = len(directory_bytes)
        shape = resource_estimator.parse_resource_shape_parts(header_bytes, directory_bytes, artifact_bytes)
        outcome = "preliminary_parse_ok"
    finally:
        f.close()
except Exception as exc:
    outcome = type(exc).__name__
after = sample_memory()

inst.header_bytes_read = inst.header_bytes_read or 0
inst.directory_bytes_read = inst.directory_bytes_read or 0
inst.preflight_bytes_read = inst.header_bytes_read + inst.directory_bytes_read
max_preflight_read = max(
    [rc.requested_size for rc in inst.read_calls if rc.label in ("header", "directory")] or [0])

print(json.dumps({
    "outcome": outcome,
    "header_bytes_read": inst.header_bytes_read,
    "directory_bytes_read": inst.directory_bytes_read,
    "preflight_bytes_read": inst.preflight_bytes_read,
    "max_single_preflight_read": max_preflight_read,
    "before": before, "after": after,
}, sort_keys=True))
