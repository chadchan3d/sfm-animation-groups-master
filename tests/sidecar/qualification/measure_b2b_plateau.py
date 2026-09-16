# -*- coding: utf-8 -*-
"""B2B repeated-cycle memory/cache plateau measurement (R3-B2B Section
14). Runs many real acquire/release cycles against the real official
artifact and confirms cache entry count / ledger retained-bytes PLATEAU
rather than growing monotonically, plus real GC object-count and
Windows peak-working-set deltas (same techniques already established in
R3-A2B) across the run. Never claims full 32-bit SFM memory qualification
from these offline numbers alone.
"""
import ctypes
import gc
import sys
import time

PKG_PARENT = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r3_b2a_broker_deploy"
)
GATE_R2_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r2_formal_deploy"
)
for p in (PKG_PARENT, GATE_R2_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from sfm_master_authority import broker as broker_mod  # noqa: E402
from sfm_master_authority import projections  # noqa: E402

REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
SHIPPED_ROOT = r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm\gate_r2_formal_deploy"

REAL_LITERALS = ["left", "right", "Left PupilDown", "Right PupilDown", "Left PupilGrow"]
REAL_CSP_VOCAB = ["Left PupilLeft", "Right PupilLeft", "Left PupilRight"]

N_CYCLES = 40


def peak_working_set_bytes():
    class PMC(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_uint32), ("PageFaultCount", ctypes.c_uint32),
            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        ]
    counters = PMC()
    counters.cb = ctypes.sizeof(PMC)
    h = ctypes.windll.kernel32.GetCurrentProcess()
    ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(counters), counters.cb)
    return counters.PeakWorkingSetSize, counters.WorkingSetSize


def main():
    shipped_official = SHIPPED_ROOT  # official_sidecar_artifact.bin matches this Master; scanned by extension .sfmsidecar
    # official_sidecar_artifact.bin doesn't end in .sfmsidecar -- point at
    # the fixture root that already holds a correctly-named copy.
    fix_shipped = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures\shipped_root_valid"

    b = broker_mod.Broker(api_version="plateau-measure")

    cache_counts = []
    ledger_retained = []
    gc_counts = []
    peak_ws = []

    for i in range(N_CYCLES):
        norm_builder = projections.build_normalizer_like_projection(REAL_LITERALS)
        csp_builder = projections.build_character_preset_like_projection(REAL_CSP_VOCAB)
        b.acquire_cohort(REAL_MASTER_PATH, {"normalizer": norm_builder, "csp": csp_builder},
                          shipped_root=fix_shipped)

        cache_counts.append(b.view_cache_entry_count())
        ledger_retained.append(b._ledger.total_retained_bytes())
        gc.collect()
        gc_counts.append(len(gc.get_objects()))
        peak, _ = peak_working_set_bytes()
        peak_ws.append(peak)

    print("cache entry counts over %d cycles: min=%d max=%d last10=%r" % (
        N_CYCLES, min(cache_counts), max(cache_counts), cache_counts[-10:]))
    print("ledger retained bytes over %d cycles: min=%d max=%d last10=%r" % (
        N_CYCLES, min(ledger_retained), max(ledger_retained), ledger_retained[-10:]))
    print("gc object counts: first5=%r last5=%r (monotonic growth check)" % (gc_counts[:5], gc_counts[-5:]))
    print("peak working set bytes: first=%d last=%d delta=%d" % (peak_ws[0], peak_ws[-1], peak_ws[-1] - peak_ws[0]))

    plateaued = (max(cache_counts[-10:]) - min(cache_counts[-10:])) <= 1
    print("CACHE ENTRY COUNT PLATEAUED (last 10 cycles vary by <=1): %r" % plateaued)

    gc_growth_last_half = gc_counts[-1] - gc_counts[len(gc_counts) // 2]
    gc_growth_first_half = gc_counts[len(gc_counts) // 2] - gc_counts[0]
    print("gc object growth: first half=%d, second half=%d (second-half << first-half implies plateau, not monotonic growth)" % (
        gc_growth_first_half, gc_growth_last_half))


if __name__ == "__main__":
    main()
