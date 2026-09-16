# -*- coding: utf-8 -*-
# R3-B2F1F Stage F4 -- real-SFM preflight-refusal qualification for
# fixtureC_1p25x. TEST-ONLY: calls only the F3 same-handle preflight
# candidate (b2f1f_f3_same_handle_candidate.py), never production
# broker/Cohort acquisition. Never modifies any frozen file.
#
# Executes directly at module scope (no __main__ guard, no __file__
# dependency, no sibling-directory import resolution) -- same corrected
# launcher pattern as Runs 2-4 (B2F1A/B/C/D).
#
# RESTART SFM FIRST. Run this as the ONLY script this SFM session
# executes for this run. DO NOT SAVE any prior experimental scene state.
import ctypes
import gc
import imp
import json
import os
import sys
from ctypes import wintypes

try:
    unicode
except NameError:
    unicode = str

RUN_ID = "F4_PreflightRefusal_C1p25"
RESULTS_DIR = r"C:\Users\Public\Documents"
RESULT_JSON_PATH = os.path.join(RESULTS_DIR, "CGN_R3_B2F1F_F4_PreflightRefusal_C1p25_result.json")
LOG_PATH = os.path.join(RESULTS_DIR, "CGN_R3_B2F1F_F4_PreflightRefusal_C1p25_log.txt")
DONE_MARKER_PATH = os.path.join(RESULTS_DIR, "CGN_R3_B2F1F_F4_PreflightRefusal_C1p25_DONE.marker")

RUNTIME_CAP_BYTES = 16 * 1024 * 1024
RETAINED_GATE_BYTES = 16 * 1024 * 1024
TRANSIENT_GATE_BYTES = 32 * 1024 * 1024  # 33,554,432 bytes -- exactly 32 MiB

FIXTURE_NAME = "fixtureC_1p25x"
FIXTURE_ARTIFACT_PATH = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\scratch_r3b2f\fixtures\fixtureC_1p25x.sfmsidecar"
)
FIXTURE_SOURCE_SHA256 = "0b1fe4f17dfdfcca8a99767da49be8c7c971e6db571aaa36c470ba0eb837e4d0"
FIXTURE_SIDECAR_BYTES = 12179112

_KNOWN_GAME_ROOT_FALLBACK = r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game"


def _derive_game_root():
    try:
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    except Exception:
        exe_dir = None
    if exe_dir and os.path.isdir(os.path.join(exe_dir, "usermod", "scripts", "sfm", "mainmenu")):
        return exe_dir
    return _KNOWN_GAME_ROOT_FALLBACK


_GAME_ROOT = _derive_game_root()
_MAINMENU_DIR = os.path.join(_GAME_ROOT, "usermod", "scripts", "sfm", "mainmenu")
_QUAL_DIR = r"E:\SFM Animation Group Master\tests\sidecar\qualification"
_B2A_DEPLOY_DIR = os.path.join(
    _GAME_ROOT, "usermod", "scripts", "sfm", "gate_r3_b2a_broker_deploy",
)
_GATE_R2_DIR = os.path.join(
    _GAME_ROOT, "usermod", "scripts", "sfm", "gate_r2_formal_deploy",
)

_log_lines = []


def log(msg):
    line = msg if isinstance(msg, unicode) else (
        msg.decode("utf-8", "replace") if isinstance(msg, str) else unicode(msg)
    )
    _log_lines.append(u"[%.4f] %s" % (__import__("time").time(), line))
    print(line)


# ---------------------------------------------------------------------------
# External memory/VAS sampler -- REUSED VERBATIM from the same lineage as
# CGN_R2_R1D_W1_SIDECAR_PackedValidationHot_01.py / b2f1_campaign_core.py.
# Used here ONLY for SFM-side named checkpoints (S0-S5) -- SECONDARY
# telemetry. The AUTHORITATIVE transient result comes from the genuine
# separate-process gate2a_external_sampler.py, per this task's own
# instruction not to treat any in-process sampler as authoritative.
# ---------------------------------------------------------------------------

MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_FREE = 0x10000
VAS_CEILING_4GIB = 0xFFFFFFFF


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


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


_kernel32 = ctypes.windll.kernel32
_psapi = ctypes.windll.psapi
_kernel32.GetCurrentProcess.restype = wintypes.HANDLE
_psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
_psapi.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD,
]
_kernel32.VirtualQuery.restype = ctypes.c_size_t
_kernel32.VirtualQuery.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(MEMORY_BASIC_INFORMATION), ctypes.c_size_t,
]
_self_handle = _kernel32.GetCurrentProcess()


def _self_memory_counters():
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


def _self_vas_scan(ceiling=VAS_CEILING_4GIB):
    addr = 0
    committed = 0
    reserved = 0
    free = 0
    largest_free = 0
    region_count = 0
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
    return {
        "committed": committed, "reserved": reserved, "free": free,
        "largest_free_region": largest_free, "region_count": region_count,
    }


def sample(checkpoint_name, forced_gc=False):
    if forced_gc:
        gc.collect()
    mem = _self_memory_counters()
    vas = _self_vas_scan()
    row = {"checkpoint": checkpoint_name, "timestamp": __import__("time").time(), "memory": mem, "vas": vas}
    log(u"STAGE %-24s private=%r peak_pf=%r committed=%r free=%r largest_free=%r" % (
        checkpoint_name, mem["private_bytes"] if mem else None,
        mem["peak_pagefile_usage"] if mem else None, vas["committed"], vas["free"], vas["largest_free_region"],
    ))
    return row


def _write_outputs(result, status="done"):
    if not os.path.isdir(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    with open(RESULT_JSON_PATH, "wb") as f:
        f.write(json.dumps(result, indent=2, sort_keys=True).encode("utf-8", "replace"))
    with open(LOG_PATH, "wb") as f:
        f.write(u"\n".join(_log_lines).encode("utf-8", "replace"))
    with open(DONE_MARKER_PATH, "wb") as f:
        f.write(status.encode("ascii", "replace"))
    print(u"DONE (%s) -- results written to %s" % (status, RESULT_JSON_PATH))


def _guarded_run():
    result = {
        "run_id": RUN_ID, "fixture_name": FIXTURE_NAME, "fixture_sidecar_bytes": FIXTURE_SIDECAR_BYTES,
        "runtime_cap_bytes": RUNTIME_CAP_BYTES, "retained_gate_bytes": RETAINED_GATE_BYTES,
        "transient_gate_bytes": TRANSIENT_GATE_BYTES, "stages": {}, "assertions": {},
    }
    try:
        result["stages"]["S0_process_baseline"] = sample("S0_process_baseline")

        if _B2A_DEPLOY_DIR not in sys.path:
            sys.path.insert(0, _B2A_DEPLOY_DIR)
        if _GATE_R2_DIR not in sys.path:
            sys.path.insert(0, _GATE_R2_DIR)
        from sfm_master_authority import broker as broker_mod, errors as authority_errors
        result["stages"]["S1_post_import"] = sample("S1_post_import")

        candidate_path = os.path.join(_QUAL_DIR, "b2f1f_f3_same_handle_candidate.py")
        with open(candidate_path, "rb") as f:
            import hashlib
            result["candidate_sha256"] = hashlib.sha256(f.read()).hexdigest()
        candidate = imp.load_source("b2f1f_f3_same_handle_candidate_%s" % RUN_ID, candidate_path)
        result["stages"]["S2_post_candidate_load"] = sample("S2_post_candidate_load")

        result["stages"]["S3_pre_acquisition"] = sample("S3_pre_acquisition")

        inst = candidate.Instrumentation()
        refusal_exc = None
        provider = None
        t0 = __import__("time").time()
        try:
            provider, inst = candidate.candidate_open_path_with_preflight(
                FIXTURE_ARTIFACT_PATH, FIXTURE_SOURCE_SHA256, RUNTIME_CAP_BYTES, inst,
            )
        except authority_errors.ResourceAdmissionRefusal as exc:
            refusal_exc = exc
        result["acquisition_duration_seconds"] = __import__("time").time() - t0

        result["stages"]["S4_post_refusal_handle_closed"] = sample("S4_post_refusal_handle_closed")

        if provider is not None:
            try:
                provider.close()
            except Exception:
                pass

        # Fresh, never-otherwise-touched broker, purely to report the
        # authoritative AggregateLedger/provider-counter state -- this
        # F3 candidate path never constructs a Broker/Cohort at all, so
        # this is the honest, direct way to confirm nothing authority-
        # side was ever touched by this refused acquisition.
        b = broker_mod.Broker(api_version="b2f1f-f4-%s" % RUN_ID)
        ledger = b.ledger_snapshot()
        provider_counters = b.provider_counters()
        view_cache_entry_count = b.view_cache_entry_count()

        result["instrumentation"] = inst.to_dict()
        result["error_type"] = type(refusal_exc).__name__ if refusal_exc is not None else None
        result["error_detail"] = str(refusal_exc) if refusal_exc is not None else None
        result["ledger_snapshot_after_refusal"] = ledger
        result["broker_provider_counters_after_refusal"] = provider_counters
        result["view_cache_entry_count_after_refusal"] = view_cache_entry_count

        gc.collect()
        result["stages"]["S5_final_settled"] = sample("S5_final_settled", forced_gc=True)

        # --- Section 6 explicit assertions -- a script that merely runs
        # to completion is NOT a PASS; every one of these must hold. ---
        a = result["assertions"]
        a["raw_artifact_check_passes"] = FIXTURE_SIDECAR_BYTES <= RUNTIME_CAP_BYTES
        a["resource_admission_refusal_raised"] = refusal_exc is not None
        a["error_class_is_ResourceAdmissionRefusal"] = type(refusal_exc).__name__ == "ResourceAdmissionRefusal" if refusal_exc else False
        a["candidate_file_opens_eq_1"] = inst.file_open_count == 1
        a["candidate_file_closes_eq_1"] = inst.file_close_count == 1
        a["preflight_bytes_read_le_360"] = (inst.preflight_bytes_read or 0) <= 360
        a["full_bounded_read_call_count_eq_0"] = inst.full_bounded_read_call_count == 0
        a["validator_call_count_eq_0"] = inst.validator_call_count == 0
        a["projection_builder_call_count_eq_0"] = inst.projection_builder_call_count == 0
        a["published_detached_view_count_eq_0"] = inst.published_detached_view_count == 0
        a["provider_left_open_eq_0"] = (provider is None) or (provider._state == "CLEANED")
        a["ledger_all_categories_zero"] = all(v == 0 for v in ledger.values())
        a["broker_provider_counters_all_zero"] = (
            provider_counters.get("total_provider_opens") == 0
            and provider_counters.get("total_provider_closes") == 0
            and provider_counters.get("current_open_provider_count") == 0
        )
        a["reason_identifies_retained_or_transient"] = inst.reason in ("estimated_retained", "estimated_transient")

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
