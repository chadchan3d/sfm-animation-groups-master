# -*- coding: utf-8 -*-
# CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01 -- the ONE
# runtime harness authorized by
# SFM_CGN_R3_B2F_Custom_Sidecar_Runtime_Resource_Qualification Sections
# 6-17.
#
# IMPORTANT -- THIS SCRIPT DOES NOT AUTO-RUN. Being discovered/imported by
# SFM's mainmenu loader at startup executes ONLY the function/class
# definitions below -- there is deliberately NO QTimer/schedule() call at
# module scope. The actual harness runs ONLY when this file is executed
# directly (SFM Script Editor "Run" action, which sets
# __name__ == "__main__" per standard Python convention -- the same
# mechanism already qualified for the B2B runtime probe).
#
# DIAGNOSTIC / QUALIFICATION ONLY. Never modifies R1D, the final R3-A2B
# candidate, the Master, production Normalizer, or production Character
# Preset. Never alters production pointer selection. Uses the REAL
# canonical sfm_master_authority broker/provider path (B2A/B2B,
# unmodified) against a set of isolated qualification fixture artifacts
# (never the production generated-root/pointer locations).

import ctypes
import gc
import json
import os
import sys
import time
import traceback
from ctypes import wintypes

try:
    unicode
except NameError:
    unicode = str

TEST_ID = "CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01"

RESULTS_DIR = r"C:\Users\Public\Documents"
RESULT_JSON_PATH = os.path.join(RESULTS_DIR, "%s_result.json" % TEST_ID)
ERROR_LOG_PATH = os.path.join(RESULTS_DIR, "%s_error.log" % TEST_ID)
DONE_MARKER_PATH = os.path.join(RESULTS_DIR, "%s_DONE.marker" % TEST_ID)

B2A_DEPLOY_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r3_b2a_broker_deploy"
)
GATE_R2_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r2_formal_deploy"
)
FIXTURE_ROOT = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\scratch_r3b2f\fixtures"
)
MANIFEST_PATH = os.path.join(FIXTURE_ROOT, "fixture_manifest.json")

REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
REAL_MASTER_SHA = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
REAL_OFFICIAL_ARTIFACT = os.path.join(GATE_R2_DIR, "official_sidecar_artifact.bin")

DEFAULT_EXPERIMENTAL_CAP_BYTES = 16 * 1024 * 1024
GENEROUS_QUALIFICATION_CAP_BYTES = 64 * 1024 * 1024  # test-mode override ONLY, to measure real behavior above 16 MiB
REPEATED_CYCLES_PER_FIXTURE = 5

REAL_LITERALS_FOR_PROJECTION = ["left", "right", "Left PupilDown", "Right PupilDown", "Left PupilGrow"]
REAL_CSP_VOCAB_FOR_PROJECTION = ["Left PupilLeft", "Right PupilLeft", "Left PupilRight"]

_log_lines = []


def log(msg):
    line = msg if isinstance(msg, unicode) else (
        msg.decode("utf-8", "replace") if isinstance(msg, str) else unicode(msg)
    )
    _log_lines.append(u"[%.4f] %s" % (time.time(), line))
    print(line)


def _flush_log(text):
    if not os.path.isdir(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    f = open(ERROR_LOG_PATH, "wb")
    try:
        f.write(text.encode("utf-8", "replace"))
    finally:
        f.close()


def _write_done(status):
    if not os.path.isdir(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    f = open(DONE_MARKER_PATH, "wb")
    try:
        f.write(status.encode("ascii", "replace"))
    finally:
        f.close()


def _save_json(path, data):
    if not os.path.isdir(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    f = open(path, "wb")
    try:
        f.write(json.dumps(data, indent=2, sort_keys=True).encode("utf-8", "replace"))
    finally:
        f.close()


# ---------------------------------------------------------------------------
# External memory/VAS sampler -- REUSED VERBATIM from the established,
# already-real-SFM-qualified R2 methodology
# (CGN_R2_R1D_W1_SIDECAR_PackedValidationHot_01.py), never Python-only
# estimates, never sys.getsizeof().
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
    row = {"checkpoint": checkpoint_name, "timestamp": time.time(), "memory": mem, "vas": vas}
    log(u"SAMPLE %-28s private_bytes=%r committed=%r free=%r" % (
        checkpoint_name, mem["private_bytes"] if mem else None, vas["committed"], vas["free"],
    ))
    return row


# ---------------------------------------------------------------------------
# Per-fixture phase runner
# ---------------------------------------------------------------------------


def run_fixture_phases(broker, projections_mod, errors_mod, fixture, runtime_cap_bytes, cycle_index):
    """Runs P0-P5 for one fixture, one cycle, against the REAL canonical
    broker path. Returns a dict of {phase: sample_row} plus outcome info.
    """
    result = {"fixture": fixture["name"], "cycle": cycle_index, "runtime_cap_bytes": runtime_cap_bytes}

    result["P0_baseline"] = sample("P0_baseline_%s_c%d" % (fixture["name"], cycle_index))

    specs = {
        "normalizer": (
            frozenset(projections_mod._ascii_fold(l) for l in REAL_LITERALS_FOR_PROJECTION),
            projections_mod.build_normalizer_like_projection(REAL_LITERALS_FOR_PROJECTION),
        ),
    }

    t0 = time.time()
    try:
        views1 = broker.acquire_or_reuse_views(
            fixture["master_path"],
            {"normalizer": specs["normalizer"]},
            shipped_root=fixture["shipped_root"],
            runtime_cap_bytes=runtime_cap_bytes,
        )
        result["P1_P2_open_validate_and_normalizer_projection"] = sample(
            "P1P2_open_validate_normalizer_%s_c%d" % (fixture["name"], cycle_index)
        )
        result["admission_outcome"] = "accepted"
    except errors_mod.BrokerError as exc:
        result["admission_outcome"] = "refused"
        result["admission_error_type"] = type(exc).__name__
        result["admission_error_detail"] = str(exc)
        result["P1_P2_open_validate_and_normalizer_projection"] = sample(
            "P1P2_refused_%s_c%d" % (fixture["name"], cycle_index)
        )
        result["phase_duration_seconds"] = time.time() - t0
        result["provider_counters_after"] = broker.provider_counters()
        return result
    result["p1_p2_duration_seconds"] = time.time() - t0

    t1 = time.time()
    csp_spec = (
        frozenset(projections_mod._ascii_fold(l) for l in REAL_CSP_VOCAB_FOR_PROJECTION),
        projections_mod.build_character_preset_like_projection(REAL_CSP_VOCAB_FOR_PROJECTION),
    )
    views2 = broker.acquire_or_reuse_views(
        fixture["master_path"],
        {"csp": csp_spec},
        shipped_root=fixture["shipped_root"],
        runtime_cap_bytes=runtime_cap_bytes,
    )
    result["P3_second_consumer_projection"] = sample(
        "P3_csp_projection_%s_c%d" % (fixture["name"], cycle_index)
    )
    result["p3_duration_seconds"] = time.time() - t1

    # P4: provider is ALREADY closed here (Cohort closes it internally the
    # instant build_projections() returns) -- both views remain retained
    # in the broker's aggregate ledger/cache. This IS the retained
    # aggregate authority state the phase is defined to capture.
    result["P4_provider_closed_views_retained"] = sample(
        "P4_retained_%s_c%d" % (fixture["name"], cycle_index)
    )
    result["ledger_snapshot_at_P4"] = broker.ledger_snapshot()
    result["view_cache_entry_count_at_P4"] = broker.view_cache_entry_count()
    result["provider_counters_at_P4"] = broker.provider_counters()

    # P5: release/evict -- drop our own references and force a cache
    # eviction pass by admitting a tiny throwaway view, then GC.
    del views1
    del views2
    gc.collect()
    result["P5_release_evict"] = sample("P5_release_%s_c%d" % (fixture["name"], cycle_index), forced_gc=True)
    result["view_cache_entry_count_at_P5"] = broker.view_cache_entry_count()

    return result


def main():
    results = {"fixtures": [], "cap_refusal_tests": [], "repeated_cycle_stability": []}

    if B2A_DEPLOY_DIR not in sys.path:
        sys.path.insert(0, B2A_DEPLOY_DIR)
    if GATE_R2_DIR not in sys.path:
        sys.path.insert(0, GATE_R2_DIR)

    import sfm_master_authority.runtime as authority_runtime
    from sfm_master_authority import broker as broker_mod, projections, errors as authority_errors

    broker = authority_runtime.get_broker(is_main_thread_fn=lambda: True)
    log(u"canonical broker acquired: %r" % (broker,))

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    # Stage each fixture's artifact under a per-fixture shipped_root
    # directory with a `.sfmsidecar` extension (selection scans by
    # extension) -- an ISOLATED qualification location, never the
    # production generated-root/pointer path.
    fixtures = []
    for m in manifest:
        stage_dir = os.path.join(RESULTS_DIR, "%s_stage_%s" % (TEST_ID, m["name"]))
        if not os.path.isdir(stage_dir):
            os.makedirs(stage_dir)
        staged_artifact = os.path.join(stage_dir, "%s.sfmsidecar" % m["name"])
        if not os.path.isfile(staged_artifact):
            with open(m["artifact_path"], "rb") as src, open(staged_artifact, "wb") as dst:
                dst.write(src.read())
        fixtures.append({
            "name": m["name"], "family": m["family"], "target_ratio": m["target_ratio"],
            "sidecar_bytes": m["sidecar_bytes"], "shipped_root": stage_dir, "is_official": False,
            # Each synthetic fixture's OWN Master path -- its artifact's
            # embedded source_sha256 matches THIS file's hash, never the
            # real official Master's hash (a real, harness-breaking bug
            # found during dry-run: selection correctly refused every
            # synthetic fixture with SidecarMissing when the real Master
            # path was passed instead).
            "master_path": m["master_path"],
        })

    # Official control fixture.
    official_stage_dir = os.path.join(RESULTS_DIR, "%s_stage_official" % TEST_ID)
    if not os.path.isdir(official_stage_dir):
        os.makedirs(official_stage_dir)
    official_staged = os.path.join(official_stage_dir, "official.sfmsidecar")
    if not os.path.isfile(official_staged):
        with open(REAL_OFFICIAL_ARTIFACT, "rb") as src, open(official_staged, "wb") as dst:
            dst.write(src.read())
    fixtures.insert(0, {
        "name": "official_control", "family": "official", "target_ratio": "1.0x",
        "sidecar_bytes": os.path.getsize(official_staged), "shipped_root": official_stage_dir,
        "is_official": True, "master_path": REAL_MASTER_PATH,
    })

    # --- Main pass: full P0-P5 phases per fixture, generous qualification
    #     cap (this task's own authorized override, to MEASURE real
    #     behavior above the 16 MiB experimental default before deciding
    #     what the production cap should be).
    #
    #     A FRESH Broker instance is used PER FIXTURE (bypassing the
    #     canonical singleton deliberately, for this isolated measurement
    #     only): every synthetic fixture in this harness shares the SAME
    #     real REAL_MASTER_SHA (only `shipped_root` differs, to swap which
    #     candidate artifact answers that Master) -- reusing one broker's
    #     cache across fixtures would let fixture N's view silently be
    #     served from fixture 1's cached entry (same master_sha256 +
    #     same requested literals + same consumer_kind = same cache key),
    #     never actually opening/measuring fixture N's own artifact. A
    #     fresh broker's empty cache guarantees each fixture is genuinely,
    #     independently measured. ---
    for fixture in fixtures:
        log(u"=== fixture %s (%s, %s, %d bytes) ===" % (
            fixture["name"], fixture["family"], fixture["target_ratio"], fixture["sidecar_bytes"]))
        fixture_broker = broker_mod.Broker(api_version="b2f-main-pass-%s" % fixture["name"])
        try:
            r = run_fixture_phases(fixture_broker, projections, authority_errors, fixture,
                                    GENEROUS_QUALIFICATION_CAP_BYTES, cycle_index=0)
            r["provider_counters_final_for_fixture"] = fixture_broker.provider_counters()
            results["fixtures"].append(r)
        except Exception:
            tb = traceback.format_exc()
            log(u"EXCEPTION during fixture %s: %s" % (fixture["name"], tb))
            results["fixtures"].append({"fixture": fixture["name"], "exception": tb})

    # --- Cap-refusal test: DEFAULT 16 MiB experimental cap against every
    #     fixture whose real sidecar_bytes exceeds it -- must refuse
    #     cleanly with ResourceAdmissionRefusal, never corruption/format/
    #     source-mismatch. ---
    for fixture in fixtures:
        if fixture["sidecar_bytes"] <= DEFAULT_EXPERIMENTAL_CAP_BYTES:
            continue
        log(u"=== cap-refusal test: %s (%d bytes > 16 MiB default) ===" % (fixture["name"], fixture["sidecar_bytes"]))
        # Deliberately a FRESH, isolated broker instance (bypassing the
        # canonical singleton) for this specific check -- the shared
        # `broker` above already cached a normalizer view keyed by
        # (master_sha256, None, folded_keys, "normalizer") from the main
        # pass, and since every fixture here reuses the SAME real
        # REAL_MASTER_SHA (only `shipped_root` differs, a test-harness-only
        # pattern to swap which candidate artifact answers a given Master),
        # reusing the shared broker would silently return that ALREADY-
        # CACHED view instead of attempting a genuinely fresh acquisition
        # under the smaller cap -- exactly the real risk R3-B2F Section 15
        # asks to be proven safe against. A fresh broker's empty cache
        # guarantees this check exercises a real, uncached acquisition.
        cap_test_broker = broker_mod.Broker(api_version="b2f-cap-refusal-test-%s" % fixture["name"])
        try:
            cap_test_broker.acquire_or_reuse_views(
                fixture["master_path"],
                {"normalizer": (
                    frozenset(projections._ascii_fold(l) for l in REAL_LITERALS_FOR_PROJECTION),
                    projections.build_normalizer_like_projection(REAL_LITERALS_FOR_PROJECTION),
                )},
                shipped_root=fixture["shipped_root"],
                runtime_cap_bytes=DEFAULT_EXPERIMENTAL_CAP_BYTES,
            )
            results["cap_refusal_tests"].append({
                "fixture": fixture["name"], "sidecar_bytes": fixture["sidecar_bytes"],
                "outcome": "UNEXPECTEDLY_ACCEPTED",
            })
        except authority_errors.ResourceAdmissionRefusal as exc:
            results["cap_refusal_tests"].append({
                "fixture": fixture["name"], "sidecar_bytes": fixture["sidecar_bytes"],
                "outcome": "correctly_refused_as_ResourceAdmissionRefusal", "detail": str(exc),
            })
        except authority_errors.BrokerError as exc:
            results["cap_refusal_tests"].append({
                "fixture": fixture["name"], "sidecar_bytes": fixture["sidecar_bytes"],
                "outcome": "refused_but_WRONG_CATEGORY", "wrong_category": type(exc).__name__, "detail": str(exc),
            })

    # --- Repeated-acquisition stability: pick the largest fixture that
    #     was ACCEPTED under the generous cap, run several more cycles on
    #     a SINGLE DEDICATED broker (intentional reuse this time -- the
    #     whole point of this section is to observe whether THAT ONE
    #     broker's cache/ledger plateaus across repeated cycles of the
    #     SAME fixture, which is correct/expected reuse, not the cross-
    #     fixture cache confusion the main pass above had to avoid).
    #     Confirm provider count returns to zero and cache/view counts
    #     plateau rather than growing monotonically. ---
    accepted = [f for f in results["fixtures"] if f.get("admission_outcome") == "accepted"]
    if accepted:
        largest = max(accepted, key=lambda r: next(
            (fx["sidecar_bytes"] for fx in fixtures if fx["name"] == r["fixture"]), 0))
        stability_fixture = next(fx for fx in fixtures if fx["name"] == largest["fixture"])
        log(u"=== repeated-cycle stability: %s, %d cycles ===" % (
            stability_fixture["name"], REPEATED_CYCLES_PER_FIXTURE))
        stability_broker = broker_mod.Broker(api_version="b2f-stability-%s" % stability_fixture["name"])
        for cycle in range(1, REPEATED_CYCLES_PER_FIXTURE + 1):
            r = run_fixture_phases(stability_broker, projections, authority_errors, stability_fixture,
                                    GENEROUS_QUALIFICATION_CAP_BYTES, cycle_index=cycle)
            r["view_cache_entry_count_at_end_of_cycle"] = stability_broker.view_cache_entry_count()
            r["provider_counters_at_end_of_cycle"] = stability_broker.provider_counters()
            results["repeated_cycle_stability"].append(r)
        results["stability_broker_final_provider_counters"] = stability_broker.provider_counters()
        results["stability_broker_final_ledger_snapshot"] = stability_broker.ledger_snapshot()

    results["final_provider_counters"] = broker.provider_counters()
    results["final_ledger_snapshot"] = broker.ledger_snapshot()
    results["final_view_cache_entry_count"] = broker.view_cache_entry_count()
    results["fixtures_processed"] = len(fixtures)
    return results


def _guarded_run():
    try:
        results = main()
        _save_json(RESULT_JSON_PATH, results)
        _flush_log(u"\n".join(_log_lines))
        log(u"DONE -- results written to %s" % RESULT_JSON_PATH)
        _write_done("done")
    except Exception:
        tb = traceback.format_exc()
        log(u"UNCAUGHT EXCEPTION:\n%s" % tb)
        try:
            _flush_log(u"\n".join(_log_lines))
        except Exception:
            pass
        _write_done("done-with-exception")


if __name__ == "__main__":
    _guarded_run()
else:
    print(u"%s loaded (import only) -- run this file directly via SFM's "
          u"Script Editor to execute the harness. It does NOT auto-run." % TEST_ID)
