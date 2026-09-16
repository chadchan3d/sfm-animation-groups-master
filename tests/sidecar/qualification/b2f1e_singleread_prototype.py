# -*- coding: utf-8 -*-
"""R3-B2F1E Section 5, Alternative A/C test-only prototype: measures how
much of Family C's peak is attributable to the DUPLICATE bounded-read
(selection.select_sidecar_candidate's own internal open+validate+close
pass, immediately discarded, followed by cohort's own separate
open_path call) by skipping the first (selection) pass entirely and
going straight to BoundedProvider.open_path with the artifact path
already known from the manifest. This is a TEST-ONLY bypass of
selection.py for diagnostic purposes only -- NOT a proposed change to
any frozen file, and NOT a weakening of source-generation validation
(open_path still fully validates source_sha256 + complete structural
validation; only the redundant SECOND full pass through selection's own
validate-then-discard step is skipped).
"""
import ctypes
import gc
import json
import sys
from ctypes import wintypes

B2A_DEPLOY_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r3_b2a_broker_deploy"
)
sys.path.insert(0, B2A_DEPLOY_DIR)

RUNTIME_CAP_BYTES = 16 * 1024 * 1024
REAL_LITERALS_FOR_PROJECTION = ["left", "right", "Left PupilDown", "Right PupilDown", "Left PupilGrow"]

MANIFEST_PATH = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\scratch_r3b2f\fixtures\fixture_manifest.json"
)
RESULTS_DIR = r"C:\Users\Public\Documents"
HARNESS_TEST_ID = "CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01"


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
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


def sample(name):
    c = PROCESS_MEMORY_COUNTERS_EX()
    c.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
    _psapi.GetProcessMemoryInfo(_self_handle, ctypes.byref(c), c.cb)
    print("%-6s private=%12d peak_pf=%12d" % (name, int(c.PrivateUsage), int(c.PeakPagefileUsage)))
    return int(c.PrivateUsage), int(c.PeakPagefileUsage)


def main():
    fixture_name = sys.argv[1]
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    m = next(x for x in manifest if x["name"] == fixture_name)
    import os
    stage_dir = os.path.join(RESULTS_DIR, "%s_stage_%s" % (HARNESS_TEST_ID, fixture_name))
    artifact_path = os.path.join(stage_dir, "%s.sfmsidecar" % fixture_name)

    sample("P0")

    from sfm_master_authority import sidecar_contract, projections
    sample("P1")

    sidecar_contract.ensure_loaded()
    sample("P1b")

    provider_mod = sidecar_contract._provider_module
    # SKIP selection.select_sidecar_candidate() entirely -- go straight to
    # the ONE bounded-read+validate+open, using the artifact path already
    # known from the manifest (a legitimate diagnostic bypass; source_sha256
    # is still fully verified by open_path itself).
    provider = provider_mod.BoundedProvider.open_path(
        artifact_path, m["source_sha256"], runtime_cap_bytes=RUNTIME_CAP_BYTES,
    )
    sample("P_single_open")

    builder_fn = projections.build_normalizer_like_projection(REAL_LITERALS_FOR_PROJECTION)
    payload, coverage, estimated_bytes = builder_fn(provider)
    priv_after_build, peak_after_build = sample("P_after_build")

    provider.close()
    sample("P_after_close")

    del payload, coverage, provider
    gc.collect()
    priv_final, peak_final = sample("P_final")

    print()
    print("estimated_bytes (payload):", estimated_bytes)
    print("PEAK with SINGLE read (no duplicate selection-pass):", peak_after_build)
    print("peak delta from P0:", peak_after_build)


if __name__ == "__main__":
    main()
