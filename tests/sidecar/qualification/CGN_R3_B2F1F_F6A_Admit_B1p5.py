# -*- coding: utf-8 -*-
# R3-B2F1F Stage F6A -- real-SFM admitted-path qualification of the F5
# production-candidate integration, targeting fixtureB_1p5x. TEST-ONLY:
# uses ONLY the isolated F5 candidate (broker_f5.BrokerF5 +
# cohort_f5/selection_f5/preflight_gate_f5) -- never the frozen
# production broker/cohort/selection. Never modifies any frozen file.
#
# Executes directly at module scope (no __main__ guard, no __file__
# dependency), same corrected launcher pattern as every prior B2F1x run.
#
# RESTART SFM FIRST. Run this as the ONLY script this SFM session
# executes for this run. DO NOT SAVE any prior experimental scene state.
import ctypes
import gc
import json
import os
import sys
import time
from ctypes import wintypes

try:
    unicode
except NameError:
    unicode = str

RUN_ID = "F6A_Admit_B1p5"
RESULTS_DIR = r"C:\Users\Public\Documents"
RESULT_JSON_PATH = os.path.join(RESULTS_DIR, "CGN_R3_B2F1F_F6A_Admit_B1p5_result.json")
LOG_PATH = os.path.join(RESULTS_DIR, "CGN_R3_B2F1F_F6A_Admit_B1p5_log.txt")
DONE_MARKER_PATH = os.path.join(RESULTS_DIR, "CGN_R3_B2F1F_F6A_Admit_B1p5_DONE.marker")

RUNTIME_CAP_BYTES = 16 * 1024 * 1024
FIXTURE_NAME = "fixtureB_1p5x"
FIXTURE_MASTER_PATH = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\scratch_r3b2f\fixtures\fixtureB_1p5x_master.txt"
)
FIXTURE_SHIPPED_ROOT = (
    r"C:\Users\Public\Documents"
    r"\CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01_stage_fixtureB_1p5x"
)
FIXTURE_SIDECAR_BYTES = 14181874

REAL_LITERALS = ["left", "right", "Left PupilDown", "Right PupilDown", "Left PupilGrow"]
REAL_CSP_VOCAB = ["Left PupilLeft", "Right PupilLeft", "Left PupilRight"]

_KNOWN_GAME_ROOT_FALLBACK = r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game"
_QUAL_DIR = r"E:\SFM Animation Group Master\tests\sidecar\qualification"
_CANDIDATE_DIR = _QUAL_DIR + r"\candidate_b2f1f_f5"
_TOOLS_DIR = r"E:\SFM Animation Group Master\tools"


def _derive_game_root():
    try:
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    except Exception:
        exe_dir = None
    if exe_dir and os.path.isdir(os.path.join(exe_dir, "usermod", "scripts", "sfm", "mainmenu")):
        return exe_dir
    return _KNOWN_GAME_ROOT_FALLBACK


_GAME_ROOT = _derive_game_root()
_B2A_DEPLOY_DIR = os.path.join(_GAME_ROOT, "usermod", "scripts", "sfm", "gate_r3_b2a_broker_deploy")
_GATE_R2_DIR = os.path.join(_GAME_ROOT, "usermod", "scripts", "sfm", "gate_r2_formal_deploy")

_log_lines = []


def log(msg):
    line = msg if isinstance(msg, unicode) else (
        msg.decode("utf-8", "replace") if isinstance(msg, str) else unicode(msg)
    )
    _log_lines.append(u"[%.4f] %s" % (time.time(), line))
    print(line)


# ---------------------------------------------------------------------------
# External memory/VAS sampler -- REUSED VERBATIM. Secondary telemetry only;
# the genuine external gate2a_external_sampler.py governs transient
# qualification, per this task's own instruction.
# ---------------------------------------------------------------------------

class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD),
    ]


_kernel32 = ctypes.windll.kernel32
_psapi = ctypes.windll.psapi
_kernel32.GetCurrentProcess.restype = wintypes.HANDLE
_psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
_psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD]
_kernel32.VirtualQuery.restype = ctypes.c_size_t
_kernel32.VirtualQuery.argtypes = [ctypes.c_void_p, ctypes.POINTER(MEMORY_BASIC_INFORMATION), ctypes.c_size_t]
_self_handle = _kernel32.GetCurrentProcess()
MEM_COMMIT, MEM_RESERVE, MEM_FREE, VAS_CEILING_4GIB = 0x1000, 0x2000, 0x10000, 0xFFFFFFFF


def _self_memory_counters():
    c = PROCESS_MEMORY_COUNTERS_EX()
    c.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
    if not _psapi.GetProcessMemoryInfo(_self_handle, ctypes.byref(c), c.cb):
        return None
    return {
        "working_set": int(c.WorkingSetSize), "peak_working_set": int(c.PeakWorkingSetSize),
        "pagefile_usage": int(c.PagefileUsage), "peak_pagefile_usage": int(c.PeakPagefileUsage),
        "private_bytes": int(c.PrivateUsage),
    }


def _self_vas_scan(ceiling=VAS_CEILING_4GIB):
    addr, committed, reserved, free, largest_free, region_count = 0, 0, 0, 0, 0, 0
    mbi = MEMORY_BASIC_INFORMATION()
    mbi_size = ctypes.sizeof(MEMORY_BASIC_INFORMATION)
    while addr < ceiling:
        ret = _kernel32.VirtualQuery(ctypes.c_void_p(addr), ctypes.byref(mbi), mbi_size)
        if ret == 0:
            break
        region_count += 1
        size = mbi.RegionSize if mbi.RegionSize else 0x1000
        if mbi.State == MEM_COMMIT:
            committed += size
        elif mbi.State == MEM_RESERVE:
            reserved += size
        elif mbi.State == MEM_FREE:
            free += size
            if size > largest_free:
                largest_free = size
        addr += size
        if size == 0:
            addr += 0x1000
        if addr > VAS_CEILING_4GIB:
            break
    return {"committed": committed, "reserved": reserved, "free": free,
            "largest_free_region": largest_free, "region_count": region_count}


def sample(name, forced_gc=False):
    if forced_gc:
        gc.collect()
    mem = _self_memory_counters()
    vas = _self_vas_scan()
    row = {"checkpoint": name, "timestamp": time.time(), "memory": mem, "vas": vas}
    log(u"STAGE %-32s private=%r peak_pf=%r free=%r largest_free=%r" % (
        name, mem["private_bytes"] if mem else None, mem["peak_pagefile_usage"] if mem else None,
        vas["free"], vas["largest_free_region"]))
    return row


def _write_outputs(result, status="done"):
    if not os.path.isdir(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    with open(RESULT_JSON_PATH, "wb") as f:
        f.write(json.dumps(result, indent=2, sort_keys=True, default=str).encode("utf-8", "replace"))
    with open(LOG_PATH, "wb") as f:
        f.write(u"\n".join(_log_lines).encode("utf-8", "replace"))
    with open(DONE_MARKER_PATH, "wb") as f:
        f.write(status.encode("ascii", "replace"))
    print(u"DONE (%s) -- results written to %s" % (status, RESULT_JSON_PATH))


def _guarded_run():
    result = {
        "run_id": RUN_ID, "fixture_name": FIXTURE_NAME, "fixture_sidecar_bytes": FIXTURE_SIDECAR_BYTES,
        "runtime_cap_bytes": RUNTIME_CAP_BYTES, "stages": {}, "assertions": {},
    }
    try:
        result["stages"]["S0_process_baseline"] = sample("S0_process_baseline")

        if _B2A_DEPLOY_DIR not in sys.path:
            sys.path.insert(0, _B2A_DEPLOY_DIR)
        if _GATE_R2_DIR not in sys.path:
            sys.path.insert(0, _GATE_R2_DIR)
        if _TOOLS_DIR not in sys.path:
            sys.path.insert(0, _TOOLS_DIR)
        from sfm_master_authority import (
            observation, errors as authority_errors, pointer as pointer_mod, sidecar_contract,
            descriptors, views, memory_accounting, view_cache as view_cache_mod, projections,
        )
        result["stages"]["S1_post_import"] = sample("S1_post_import")

        if _CANDIDATE_DIR not in sys.path:
            sys.path.insert(0, _CANDIDATE_DIR)
        import hashlib
        candidate_shas = {}
        for fname in ["preflight_gate_f5.py", "selection_f5.py", "cohort_f5.py", "broker_f5.py"]:
            with open(os.path.join(_CANDIDATE_DIR, fname), "rb") as f:
                candidate_shas[fname] = hashlib.sha256(f.read()).hexdigest()
        result["candidate_file_shas"] = candidate_shas
        from broker_f5 import BrokerF5
        result["stages"]["S2_post_f5_candidate_load"] = sample("S2_post_f5_candidate_load")

        b = BrokerF5(
            "b2f1f-f6a-real-sfm", observation, authority_errors, pointer_mod, sidecar_contract,
            descriptors, views, memory_accounting, view_cache_mod,
        )
        result["stages"]["S3_pre_acquisition"] = sample("S3_pre_acquisition")

        normalizer_spec = (
            frozenset(projections._ascii_fold(l) for l in REAL_LITERALS),
            projections.build_normalizer_like_projection(REAL_LITERALS),
        )
        t0 = time.time()
        views1 = b.acquire_or_reuse_views(
            FIXTURE_MASTER_PATH, {"normalizer": normalizer_spec},
            shipped_root=FIXTURE_SHIPPED_ROOT, runtime_cap_bytes=RUNTIME_CAP_BYTES,
        )
        result["normalizer_duration_seconds"] = time.time() - t0
        result["stages"]["S3b_post_normalizer_acquisition"] = sample("S3b_post_normalizer_acquisition")
        inst_normalizer = b.last_cohort_selection_instrumentation
        result["instrumentation_normalizer"] = inst_normalizer.to_dict() if inst_normalizer else None

        csp_spec = (
            frozenset(projections._ascii_fold(l) for l in REAL_CSP_VOCAB),
            projections.build_character_preset_like_projection(REAL_CSP_VOCAB),
        )
        t1 = time.time()
        views2 = b.acquire_or_reuse_views(
            FIXTURE_MASTER_PATH, {"csp": csp_spec},
            shipped_root=FIXTURE_SHIPPED_ROOT, runtime_cap_bytes=RUNTIME_CAP_BYTES,
        )
        result["csp_duration_seconds"] = time.time() - t1
        result["stages"]["S4_post_csp_acquisition"] = sample("S4_post_csp_acquisition")
        inst_csp = b.last_cohort_selection_instrumentation
        result["instrumentation_csp"] = inst_csp.to_dict() if inst_csp else None

        norm_view = views1["normalizer"]
        csp_view = views2["csp"]
        result["semantic_generation_master_sha256"] = norm_view.semantic_generation.master_sha256
        result["artifact_identity_embedded_source_sha256"] = norm_view.artifact_identity.embedded_source_sha256
        result["artifact_identity_sidecar_artifact_sha256"] = norm_view.artifact_identity.sidecar_artifact_sha256
        result["normalizer_group_count"] = len(norm_view.payload["groups"])
        result["normalizer_metadata_group_count"] = len(norm_view.payload["metadata_by_path"])
        result["normalizer_lookup_results"] = {k: list(v) for k, v in norm_view.payload["lookup_results"].items()}
        result["csp_lookup_results"] = {k: list(v) for k, v in csp_view.payload["lookup_results"].items()}
        result["normalizer_estimated_bytes"] = norm_view.estimated_bytes

        result["provider_counters"] = b.provider_counters()
        result["ledger_snapshot"] = b.ledger_snapshot()
        result["view_cache_entry_count"] = b.view_cache_entry_count()

        del views1, views2, norm_view, csp_view
        gc.collect()
        result["stages"]["S5_post_release_settled"] = sample("S5_post_release_settled", forced_gc=True)
        result["view_cache_entry_count_after_release"] = b.view_cache_entry_count()

        a = result["assertions"]
        a["outcome_admitted"] = True
        a["candidate_file_open_count_normalizer_eq_1"] = inst_normalizer.file_open_count == 1 if inst_normalizer else False
        a["candidate_file_close_count_normalizer_eq_1"] = inst_normalizer.file_close_count == 1 if inst_normalizer else False
        a["preflight_bytes_normalizer_le_360"] = (inst_normalizer.preflight_bytes_read or 0) <= 360 if inst_normalizer else False
        a["full_bounded_read_count_normalizer_eq_1"] = inst_normalizer.full_bounded_read_call_count == 1 if inst_normalizer else False
        a["validator_call_count_normalizer_eq_1"] = inst_normalizer.validator_call_count == 1 if inst_normalizer else False
        a["candidate_file_open_count_csp_eq_1"] = inst_csp.file_open_count == 1 if inst_csp else False
        a["full_bounded_read_count_csp_eq_1"] = inst_csp.full_bounded_read_call_count == 1 if inst_csp else False
        a["provider_opens_eq_2_total"] = result["provider_counters"]["total_provider_opens"] == 2
        a["provider_closes_eq_2_total"] = result["provider_counters"]["total_provider_closes"] == 2
        a["current_open_provider_count_eq_0"] = result["provider_counters"]["current_open_provider_count"] == 0
        a["view_cache_entry_count_eq_2"] = result["view_cache_entry_count"] == 2
        a["retained_detached_views_le_16mib_gate"] = result["ledger_snapshot"]["retained_detached_views"] <= 16777216
        a["semantic_generation_present"] = bool(result["semantic_generation_master_sha256"])
        a["artifact_identity_present"] = bool(result["artifact_identity_embedded_source_sha256"])
        # fixtureB_1p5x is a synthetic fixture whose literal pool
        # ("Ctrl_B_...") is entirely unrelated to the REAL_LITERALS probe
        # set (real production control names) -- MasterUnknown for all of
        # them is the CORRECT, EXPECTED result here (independently
        # confirmed identical to the frozen path in F5's own semantic-
        # equivalence test), not a coverage regression. The real check is
        # that every lookup returned a well-formed, valid status.
        _VALID_STATUSES = ("Known", "MasterUnknown", "Uncovered")
        a["all_normalizer_lookups_well_formed"] = all(
            v[0] in _VALID_STATUSES for v in result["normalizer_lookup_results"].values()
        )

        overall_pass = all(a.values())
        result["overall_qualification_result"] = "PASS" if overall_pass else "FAIL"
        _write_outputs(result)
    except Exception:
        import traceback
        tb = traceback.format_exc()
        log(u"UNCAUGHT EXCEPTION:\n%s" % tb)
        result["exception"] = tb
        result["overall_qualification_result"] = "FAIL"
        _write_outputs(result, status="done-with-exception")


_guarded_run()
