# -*- coding: utf-8 -*-
"""R3-B2F1B Section 4: provider-level isolation. Opens+validates
fixtureA_1p5x through sfm_master_authority.sidecar_contract.validate_selected_artifact
-- the REAL function Run 2's acquisition path calls (selection.py ->
sidecar_contract.validate_selected_artifact -> BoundedProvider.open_path)
-- with NO broker/cohort/view construction. Compares
runtime_cap_bytes=16MiB vs 64MiB. Each case must be run as its own fresh
process (pass the cap in MiB as argv[1]: 16 or 64).
"""
import ctypes
import json
import sys
from ctypes import wintypes

B2A_DEPLOY_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r3_b2a_broker_deploy"
)
sys.path.insert(0, B2A_DEPLOY_DIR)
from sfm_master_authority import sidecar_contract  # noqa: E402


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
    cap_mib = int(sys.argv[1])
    cap_bytes = cap_mib * 1024 * 1024

    with open(r"E:\SFM Animation Group Master\tests\sidecar\qualification\b2f_fixture_manifest.json") as f:
        manifest = json.load(f)
    fx = next(x for x in manifest if x["name"] == "fixtureA_1p5x")

    before = counters()

    sidecar_contract.ensure_loaded()
    after_load = counters()

    identity = sidecar_contract.validate_selected_artifact(
        fx["artifact_path"], fx["source_sha256"], runtime_cap_bytes=cap_bytes,
    )
    after_validate = counters()

    result = {
        "cap_mib": cap_mib,
        "cap_bytes": cap_bytes,
        "fixture_bytes": fx["sidecar_bytes"],
        "identity_repr": repr(identity),
        "before": before,
        "after_module_load": after_load,
        "after_validate_and_close": after_validate,
        "peak_pagefile_delta_before_to_validate": after_validate["peak_pagefile_usage"] - before["peak_pagefile_usage"],
        "peak_pagefile_delta_load_to_validate": after_validate["peak_pagefile_usage"] - after_load["peak_pagefile_usage"],
        "private_bytes_retained_after_close": after_validate["private_bytes"] - before["private_bytes"],
        "python_version": sys.version,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
