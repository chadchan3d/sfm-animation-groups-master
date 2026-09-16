# -*- coding: utf-8 -*-
# R3-B2F1: shared core for the targeted external-sampler boundary
# campaign. Imported (not auto-run) by five tiny per-fixture launcher
# scripts in this same directory -- this module performs NO work at
# import time (matches the mainmenu-safe-import convention already
# established by CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01.py).
#
# Purpose: separate ONE-TIME process-first-use cost (module import,
# dynamic compile/exec of the FINAL R3-A2B validator/provider via
# sfm_master_authority.sidecar_contract.ensure_loaded()) from the
# PER-OPERATION authority-acquisition cost, using the SAME external
# memory/VAS sampler already qualified in R2
# (CGN_R2_R1D_W1_SIDECAR_PackedValidationHot_01.py) and reused verbatim
# in the B2F harness -- reused verbatim here too, plus a background
# high-frequency poller (private/pagefile counters only, no VAS scan, to
# avoid the VAS walk's own overhead perturbing the very transient spike
# being measured) so a spike-and-release WITHIN one acquisition call is
# not missed by before/after checkpoints alone.
#
# Never modifies R1D, the FINAL R3-A2B validator/provider, the canonical
# Master, production Normalizer, or production Character Preset. Only
# calls existing, already-idempotent public entry points
# (sidecar_contract.ensure_loaded, broker.Broker, acquire_or_reuse_views).
import ctypes
import gc
import json
import os
import sys
import threading
import time
import traceback
from ctypes import wintypes

try:
    unicode
except NameError:
    unicode = str

RESULTS_DIR = r"C:\Users\Public\Documents"

B2A_DEPLOY_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r3_b2a_broker_deploy"
)
GATE_R2_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r2_formal_deploy"
)
MANIFEST_PATH = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\scratch_r3b2f\fixtures\fixture_manifest.json"
)
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
HARNESS_TEST_ID = "CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01"

GENEROUS_QUALIFICATION_CAP_BYTES = 64 * 1024 * 1024
BACKGROUND_POLL_INTERVAL_SECONDS = 0.05  # 20 Hz -- private/pagefile counters only

REAL_LITERALS_FOR_PROJECTION = ["left", "right", "Left PupilDown", "Right PupilDown", "Left PupilGrow"]
REAL_CSP_VOCAB_FOR_PROJECTION = ["Left PupilLeft", "Right PupilLeft", "Left PupilRight"]

# ---------------------------------------------------------------------------
# External memory/VAS sampler -- REUSED VERBATIM (same structures, same
# fields, same technique) from CGN_R2_R1D_W1_SIDECAR_PackedValidationHot_01.py
# and from CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01.py's own
# copy of it. Never sys.getsizeof(), never Python-only estimates.
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


def sample(checkpoint_name, forced_gc=False, log_fn=None):
    if forced_gc:
        gc.collect()
    mem = _self_memory_counters()
    vas = _self_vas_scan()
    row = {"checkpoint": checkpoint_name, "timestamp": time.time(), "memory": mem, "vas": vas}
    line = u"STAGE %-32s private_bytes=%r peak_pagefile=%r committed=%r free=%r" % (
        checkpoint_name, mem["private_bytes"] if mem else None,
        mem["peak_pagefile_usage"] if mem else None, vas["committed"], vas["free"],
    )
    if log_fn is not None:
        log_fn(line)
    else:
        print(line)
    return row


class BackgroundPoller(object):
    """High-frequency (20 Hz default), private/pagefile-only sampler --
    deliberately omits the VAS region walk (which itself costs real time
    and could perturb the very transient spike being measured) at this
    cadence. Runs in a daemon thread from start() to stop()."""

    def __init__(self, interval_seconds=BACKGROUND_POLL_INTERVAL_SECONDS):
        self._interval = interval_seconds
        self._rows = []
        self._stop_event = threading.Event()
        self._thread = None

    def _run(self):
        while not self._stop_event.is_set():
            mem = _self_memory_counters()
            self._rows.append({"timestamp": time.time(), "memory": mem})
            time.sleep(self._interval)

    def start(self):
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        return self._rows


def _resolve_fixture(name):
    if name == "official_control":
        stage_dir = os.path.join(RESULTS_DIR, "%s_stage_official" % HARNESS_TEST_ID)
        artifact = os.path.join(stage_dir, "official.sfmsidecar")
        return {
            "name": "official_control", "master_path": REAL_MASTER_PATH,
            "shipped_root": stage_dir, "sidecar_bytes": os.path.getsize(artifact),
        }
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    m = next(x for x in manifest if x["name"] == name)
    stage_dir = os.path.join(RESULTS_DIR, "%s_stage_%s" % (HARNESS_TEST_ID, name))
    return {
        "name": name, "master_path": m["master_path"], "shipped_root": stage_dir,
        "sidecar_bytes": m["sidecar_bytes"],
    }


def _compute_summary(result):
    """Derives transient/retained deltas relative to the POST-INFRASTRUCTURE
    baseline (S3), per Section 6/7: the operation-only cost, not conflated
    with one-time process/module warm-up. Scans BOTH the discrete named
    stage samples AND the high-frequency background poll rows so a
    spike-and-release within one acquisition call is not missed."""
    stages = result["stages"]
    s3 = stages.get("S3_post_infrastructure_preload")
    if s3 is None or s3["memory"] is None:
        return {"error": "no S3 baseline available"}
    s3_priv = s3["memory"]["private_bytes"]
    s3_peak_pf = s3["memory"]["peak_pagefile_usage"]
    s3_ts = s3["timestamp"]

    last_stage_key = None
    for k in ("S6_release_evict", "S5_post_csp_acquire", "S4_post_normalizer_acquire_REFUSED",
              "S4_post_normalizer_acquire"):
        if k in stages:
            last_stage_key = k
            break
    last_ts = stages[last_stage_key]["timestamp"] if last_stage_key else s3_ts

    poll_rows = result.get("_background_poll_rows", [])
    window_rows = [r for r in poll_rows if s3_ts <= r["timestamp"] <= last_ts and r["memory"]]

    # Python 2.7.5 (SFM's shipped interpreter) does not support the
    # `default=` keyword on max()/min() (added in Python 3.4) -- build the
    # candidate list explicitly and only call max() when it is non-empty,
    # falling back to the S3 baseline itself otherwise. Same measurement
    # semantics as before, just 2.7-compatible.
    priv_candidates = [r["memory"]["private_bytes"] for r in window_rows]
    for k in stages:
        s = stages[k]
        if s.get("memory") and s3_ts <= s["timestamp"] <= last_ts:
            priv_candidates.append(s["memory"]["private_bytes"])
    max_priv_in_window = max(priv_candidates) if priv_candidates else s3_priv

    peak_pf_candidates = [
        r["memory"]["peak_pagefile_usage"] for r in window_rows if "peak_pagefile_usage" in r["memory"]
    ]
    for k in stages:
        s = stages[k]
        if s.get("memory") and s3_ts <= s["timestamp"] <= last_ts:
            peak_pf_candidates.append(s["memory"]["peak_pagefile_usage"])
    max_peak_pf_in_window = max(peak_pf_candidates) if peak_pf_candidates else s3_peak_pf

    retained_priv = None
    if "S5_post_csp_acquire" in stages:
        retained_priv = stages["S5_post_csp_acquire"]["memory"]["private_bytes"] - s3_priv
    elif "S4_post_normalizer_acquire" in stages:
        retained_priv = stages["S4_post_normalizer_acquire"]["memory"]["private_bytes"] - s3_priv

    return {
        "baseline_stage": "S3_post_infrastructure_preload",
        "baseline_private_bytes": s3_priv,
        "baseline_peak_pagefile_usage": s3_peak_pf,
        "transient_max_private_bytes_delta": max_priv_in_window - s3_priv,
        "transient_max_peak_pagefile_delta": max_peak_pf_in_window - s3_peak_pf,
        "retained_private_bytes_delta_at_last_full_stage": retained_priv,
        "background_poll_rows_in_window": len(window_rows),
    }


def run_single_fixture_campaign(fixture_name, run_id, out_dir=RESULTS_DIR,
                                 runtime_cap_bytes=GENEROUS_QUALIFICATION_CAP_BYTES):
    """`runtime_cap_bytes` defaults to the original 64 MiB exploratory
    override (Runs 1-5's existing behavior, unchanged) -- R3-B2F1B added
    this parameter, additively, so a corrected run can pass the intended
    16 MiB production cap instead, without altering any prior run's
    already-recorded behavior. See R3_B2F1B_ReadCapPeak_Isolation_Report.md:
    the ~63-66 MiB one-time peak seen in Runs 1/2 was caused almost
    entirely by `_read_path_bounded`'s `f.read(runtime_cap_bytes + 1)`
    being sized off the 64 MiB exploratory cap, not by artifact content or
    broker/view construction -- confirmed by direct measurement."""
    log_lines = []

    def log(msg):
        line = msg if isinstance(msg, unicode) else (
            msg.decode("utf-8", "replace") if isinstance(msg, str) else unicode(msg)
        )
        log_lines.append(u"[%.4f] %s" % (time.time(), line))
        print(line)

    result_json_path = os.path.join(out_dir, "CGN_R3_B2F1_ExternalSampler_%s_result.json" % run_id)
    log_path = os.path.join(out_dir, "CGN_R3_B2F1_ExternalSampler_%s_log.txt" % run_id)
    done_marker_path = os.path.join(out_dir, "CGN_R3_B2F1_ExternalSampler_%s_DONE.marker" % run_id)

    result = {"run_id": run_id, "fixture_name": fixture_name, "stages": {}}
    poller = BackgroundPoller()
    poller.start()

    try:
        result["stages"]["S0_process_baseline"] = sample("S0_process_baseline_%s" % run_id, log_fn=log)

        if B2A_DEPLOY_DIR not in sys.path:
            sys.path.insert(0, B2A_DEPLOY_DIR)
        if GATE_R2_DIR not in sys.path:
            sys.path.insert(0, GATE_R2_DIR)

        import sfm_master_authority.runtime as authority_runtime  # noqa: F401
        from sfm_master_authority import broker as broker_mod, projections, errors as authority_errors
        from sfm_master_authority import sidecar_contract

        result["stages"]["S1_post_import"] = sample("S1_post_import_%s" % run_id, log_fn=log)

        fx = _resolve_fixture(fixture_name)
        result["fixture"] = fx
        log(u"targeting fixture %r (%d sidecar bytes)" % (fixture_name, fx["sidecar_bytes"]))

        fresh_broker = broker_mod.Broker(api_version="b2f1-campaign-%s" % run_id)
        result["stages"]["S2_post_broker_construct"] = sample("S2_post_broker_construct_%s" % run_id, log_fn=log)

        # Section 6 warm-import attribution subtest: trigger the FINAL
        # R3-A2B validator/provider dynamic compile+exec load (module-level,
        # idempotent, guarded -- fires exactly once per process regardless
        # of which fixture is acquired) HERE, in isolation, before opening
        # any provider or building any view.
        sidecar_contract.ensure_loaded()
        result["stages"]["S3_post_infrastructure_preload"] = sample(
            "S3_post_infra_preload_%s" % run_id, log_fn=log
        )

        normalizer_spec = (
            frozenset(projections._ascii_fold(l) for l in REAL_LITERALS_FOR_PROJECTION),
            projections.build_normalizer_like_projection(REAL_LITERALS_FOR_PROJECTION),
        )

        t0 = time.time()
        try:
            views1 = fresh_broker.acquire_or_reuse_views(
                fx["master_path"], {"normalizer": normalizer_spec},
                shipped_root=fx["shipped_root"], runtime_cap_bytes=runtime_cap_bytes,
            )
            result["stages"]["S4_post_normalizer_acquire"] = sample(
                "S4_post_normalizer_%s" % run_id, log_fn=log
            )
            result["admission_outcome"] = "accepted"
            result["p1p2_duration_seconds"] = time.time() - t0
        except authority_errors.BrokerError as exc:
            result["admission_outcome"] = "refused"
            result["admission_error_type"] = type(exc).__name__
            result["admission_error_detail"] = str(exc)
            result["stages"]["S4_post_normalizer_acquire_REFUSED"] = sample(
                "S4_refused_%s" % run_id, log_fn=log
            )
            result["p1p2_duration_seconds"] = time.time() - t0
            result["provider_counters_after_refusal"] = fresh_broker.provider_counters()
            result["ledger_snapshot_after_refusal"] = fresh_broker.ledger_snapshot()
            result["_background_poll_rows"] = poller.stop()
            result["summary"] = _compute_summary(result)
            _write_outputs(result, result_json_path, log_path, done_marker_path, log_lines)
            return result

        t1 = time.time()
        csp_spec = (
            frozenset(projections._ascii_fold(l) for l in REAL_CSP_VOCAB_FOR_PROJECTION),
            projections.build_character_preset_like_projection(REAL_CSP_VOCAB_FOR_PROJECTION),
        )
        views2 = fresh_broker.acquire_or_reuse_views(
            fx["master_path"], {"csp": csp_spec},
            shipped_root=fx["shipped_root"], runtime_cap_bytes=runtime_cap_bytes,
        )
        result["stages"]["S5_post_csp_acquire"] = sample("S5_post_csp_%s" % run_id, log_fn=log)
        result["p3_duration_seconds"] = time.time() - t1
        result["ledger_snapshot_at_S5"] = fresh_broker.ledger_snapshot()
        result["provider_counters_at_S5"] = fresh_broker.provider_counters()
        result["view_cache_entry_count_at_S5"] = fresh_broker.view_cache_entry_count()

        del views1
        del views2
        gc.collect()
        result["stages"]["S6_release_evict"] = sample("S6_release_%s" % run_id, forced_gc=True, log_fn=log)
        result["view_cache_entry_count_at_S6"] = fresh_broker.view_cache_entry_count()
        result["final_provider_counters"] = fresh_broker.provider_counters()

        result["_background_poll_rows"] = poller.stop()
        result["summary"] = _compute_summary(result)
        _write_outputs(result, result_json_path, log_path, done_marker_path, log_lines)
        return result
    except Exception:
        tb = traceback.format_exc()
        log(u"UNCAUGHT EXCEPTION:\n%s" % tb)
        result["exception"] = tb
        try:
            result["_background_poll_rows"] = poller.stop()
        except Exception:
            pass
        _write_outputs(result, result_json_path, log_path, done_marker_path, log_lines, status="done-with-exception")
        return result


def _write_outputs(result, result_json_path, log_path, done_marker_path, log_lines, status="done"):
    if not os.path.isdir(os.path.dirname(result_json_path)):
        os.makedirs(os.path.dirname(result_json_path))
    with open(result_json_path, "wb") as f:
        f.write(json.dumps(result, indent=2, sort_keys=True).encode("utf-8", "replace"))
    with open(log_path, "wb") as f:
        f.write(u"\n".join(log_lines).encode("utf-8", "replace"))
    with open(done_marker_path, "wb") as f:
        f.write(status.encode("ascii", "replace"))
    print(u"DONE (%s) -- results written to %s" % (status, result_json_path))
