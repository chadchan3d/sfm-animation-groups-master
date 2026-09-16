# -*- coding: utf-8 -*-
"""R3-B2F1E Section 2/3: phase-isolation harness. Mirrors
sfm_master_authority.cohort.Cohort._open_provider_once /
build_projections EXACTLY -- calling the SAME underlying frozen
functions (observation.observe_master, sidecar_contract.ensure_loaded,
selection_mod.select_sidecar_candidate, BoundedProvider.open_path,
provider.close(), views.DetachedView, views.LiveAuthorizationToken,
descriptors.SemanticGeneration) in the SAME order cohort.py's own
methods do -- but inlined here so intermediate lifecycle boundaries
(read-acquired, validated, view-built, closed, retained-only) can be
sampled, which the bundled Cohort.build_projections() call cannot
expose without modifying the frozen file (not done). No production/
frozen file is modified by this script.

Honest limitation (documented, not hidden): BoundedProvider.open_path()
itself bundles the bounded read AND complete Section 20 A-J structural
validation into one atomic call (_read_path_bounded -> _validate_complete
-> object construction) -- there is no public seam between "read
acquired" and "validated" without editing the frozen provider. P2 and P3
are therefore reported as one measured boundary, explicitly labeled as
such below, rather than fabricating a false separation.

Usage: python b2f1e_phase_isolation_harness.py <fixture_name>
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
REAL_CSP_VOCAB_FOR_PROJECTION = ["Left PupilLeft", "Right PupilLeft", "Left PupilRight"]

MANIFEST_PATH = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\scratch_r3b2f\fixtures\fixture_manifest.json"
)
RESULTS_DIR = r"C:\Users\Public\Documents"
HARNESS_TEST_ID = "CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01"
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"


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

_phases = []


def sample(name, note=""):
    c = PROCESS_MEMORY_COUNTERS_EX()
    c.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
    _psapi.GetProcessMemoryInfo(_self_handle, ctypes.byref(c), c.cb)
    row = {
        "phase": name, "note": note,
        "private_bytes": int(c.PrivateUsage),
        "peak_pagefile_usage": int(c.PeakPagefileUsage),
        "working_set": int(c.WorkingSetSize),
        "peak_working_set": int(c.PeakWorkingSetSize),
    }
    _phases.append(row)
    print("%-6s private=%12d peak_pf=%12d  %s" % (name, row["private_bytes"], row["peak_pagefile_usage"], note))
    return row


def resolve_fixture(name):
    if name == "official_control":
        stage_dir = RESULTS_DIR + "\\%s_stage_official" % HARNESS_TEST_ID
        import os
        return {"master_path": REAL_MASTER_PATH, "shipped_root": stage_dir}
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    m = next(x for x in manifest if x["name"] == name)
    import os
    stage_dir = os.path.join(RESULTS_DIR, "%s_stage_%s" % (HARNESS_TEST_ID, name))
    return {"master_path": m["master_path"], "shipped_root": stage_dir, "sidecar_bytes": m["sidecar_bytes"]}


def main():
    fixture_name = sys.argv[1]

    sample("P0", "clean process baseline, before any authority import")

    from sfm_master_authority import (
        observation, sidecar_contract, selection as selection_mod,
        views, descriptors, projections, errors as authority_errors,
    )
    sample("P1", "infrastructure imported (authority package modules)")

    fx = resolve_fixture(fixture_name)

    # --- mirrors Cohort._open_provider_once(), inlined for phase visibility ---
    h0 = observation.observe_master(fx["master_path"])
    sidecar_contract.ensure_loaded()
    sample("P1b", "ensure_loaded() complete (FINAL R3-A2B validator/provider dynamic-loaded)")

    selection_result = selection_mod.select_sidecar_candidate(
        h0=h0, shipped_root=fx["shipped_root"], runtime_cap_bytes=RUNTIME_CAP_BYTES,
    )
    sample("P2", "selection.select_sidecar_candidate() complete -- this call performs its OWN "
                 "internal bounded-read+full-validate+close pass (via sidecar_contract.validate_"
                 "selected_artifact inside _find_matching_artifact) purely to resolve the artifact "
                 "path/identity; that buffer is already closed by the time this returns")

    provider_mod = sidecar_contract._provider_module
    provider = provider_mod.BoundedProvider.open_path(
        selection_result.artifact_path, h0.sha256, runtime_cap_bytes=RUNTIME_CAP_BYTES,
    )
    # HONEST LIMITATION: open_path() bundles the bounded read AND complete
    # Section 20 A-J structural validation atomically (_read_path_bounded ->
    # _validate_complete -> object construction) -- there is no public seam
    # between "read acquired" and "validated" without editing the frozen
    # provider. P2(cohort-level)/P3 are therefore ONE measured boundary.
    sample("P2_3", "cohort-level BoundedProvider.open_path() complete: SECOND bounded read + "
                   "complete structural validation, backing (_buf) now live, packed artifact "
                   "bytes strongly referenced via provider._buf; groups/metadata/child_index "
                   "still None (lazy, not yet decoded)")

    builder_fn = projections.build_normalizer_like_projection(REAL_LITERALS_FOR_PROJECTION)
    sample("P4", "about to call the Normalizer-like builder_fn(provider) -- projection "
                 "construction begins; provider._buf still live, decoded caches still None")

    payload, coverage, estimated_bytes = builder_fn(provider)
    sample("P5", "builder_fn(provider) returned -- detached projection payload now allocated "
                 "(estimated_bytes=%d); provider._buf and any lazily-decoded caches "
                 "(_groups/_metadata_rows/_child_index) it populated are STILL live "
                 "simultaneously with the new payload" % estimated_bytes)

    groups_decoded = provider._groups is not None
    metadata_decoded = provider._metadata_rows is not None
    child_index_decoded = provider._child_index is not None

    provider.close()
    sample("P6", "provider.close() complete -- _buf/_groups/_metadata_rows/_child_index all "
                 "released (set to None); only the detached payload remains live")

    h1 = observation.observe_master(fx["master_path"])
    semantic_generation = descriptors.SemanticGeneration(
        effective_master_path=fx["master_path"], master_sha256=h1.sha256,
        master_byte_length=h1.byte_length,
        authority_semantics_version=selection_result.artifact_identity.authority_semantics_version,
        projection_contract_version=selection_result.artifact_identity.projection_contract_version,
    )
    authorization = views.LiveAuthorizationToken(semantic_generation.master_sha256)
    detached_view = views.DetachedView(
        semantic_generation=semantic_generation, artifact_identity=selection_result.artifact_identity,
        coverage=coverage, projection_contract_version=selection_result.artifact_identity.projection_contract_version,
        admission_id=1, consumer_kind="normalizer", payload=payload, authorization=authorization,
        estimated_bytes=estimated_bytes,
    )
    sample("P7_8", "DetachedView constructed and held (mirrors broker cache publication + "
                   "consumer retaining the view only) -- packed backing already released at P6")

    del detached_view, payload, coverage, provider
    gc.collect()
    sample("P9", "released local references + gc.collect()")

    print()
    print("=== summary ===")
    print("fixture:", fixture_name)
    print("sidecar_bytes:", fx.get("sidecar_bytes"))
    print("estimated_bytes (projection payload, from builder_fn):", estimated_bytes)
    print("groups_decoded_during_builder:", groups_decoded)
    print("metadata_decoded_during_builder:", metadata_decoded)
    print("child_index_decoded_during_builder:", child_index_decoded)
    peak_overall = max(p["peak_pagefile_usage"] for p in _phases)
    peak_phase = next(p["phase"] for p in _phases if p["peak_pagefile_usage"] == peak_overall)
    print("overall peak_pagefile_usage:", peak_overall, "first reached at phase:", peak_phase)
    baseline = _phases[0]["peak_pagefile_usage"]
    print("peak delta from P0:", peak_overall - baseline, "bytes = %.4f MiB" % ((peak_overall - baseline) / 1048576.0))

    out_path = RESULTS_DIR + "\\b2f1e_phase_isolation_%s.json" % fixture_name
    with open(out_path, "w") as f:
        json.dump({
            "fixture": fixture_name, "sidecar_bytes": fx.get("sidecar_bytes"),
            "estimated_bytes": estimated_bytes,
            "groups_decoded_during_builder": groups_decoded,
            "metadata_decoded_during_builder": metadata_decoded,
            "child_index_decoded_during_builder": child_index_decoded,
            "phases": _phases,
            "peak_overall": peak_overall, "peak_phase": peak_phase,
            "peak_delta_from_p0": peak_overall - baseline,
        }, f, indent=2)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
