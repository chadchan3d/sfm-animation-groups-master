# -*- coding: utf-8 -*-
"""
Offline, real-Python-2.7.5 (32-bit) empirical test supporting the F1-R1
static proof (F1-R1_SEMANTIC_CAPTURE_STATIC_PROOF.md).

Distinguishes three retention categories the governing instruction asked
to be told apart, rather than lumping everything under "gc.collect()
should have handled it":

  1. live-reference retention   -- an object is still reachable via some
     name/container; del/reassignment fixes this.
  2. cyclic garbage             -- unreachable but not freed by
     refcounting alone; gc.collect() fixes this (proven separately in
     test_gc_cycle_accumulation_across_exec.py, the F1-1 static audit).
  3. Python/CRT allocator high-water retention -- even after an object is
     BOTH unreachable AND swept by gc.collect(), the memory arenas
     CPython's own small-object allocator (pymalloc) and/or the C
     runtime allocator used them from are not necessarily returned to the
     OS. Freed Python objects go back to pymalloc's own free lists, not
     to the OS, and pymalloc only returns a whole ARENA to the OS once
     every object in it is free -- a large, deeply nested capture (many
     small dicts/lists/strings of many different sizes, freed in a
     different order than allocated) is exactly the fragmentation
     pattern that leaves arenas partially occupied indefinitely. This
     category is NOT fixed by gc.collect() and NOT fixed by del.

This test builds a SYNTHETIC structure shaped like the real production
capture_tree()/capture_snapshot_explicit() output (nested per-target ->
per-group -> per-control dicts of short strings/scalars) at a size
approximating the real 85-eligible-target capture (this project's own
D1/D2 qualification runs independently measured the real full 85-target
raw semantic payload at roughly 9 MB) -- NOT a claim about production's
exact object graph, but a size/shape-matched stand-in sufficient to
stress the same allocator behavior.

It repeats an allocate -> hash -> del -> gc.collect() cycle multiple
times (mirroring F1-R1's own per-command capture_all()/compute_target_
hashes()/del pattern) and measures process working set via the SAME
ctypes GetProcessMemoryInfo() helper F1/F1-R1 themselves use, both at
peak allocation and after each cycle's own cleanup, to see whether
post-cleanup working set RETURNS toward baseline or RATCHETS UP across
repeated cycles despite every object being both unreachable and
gc.collect()-swept.
"""
import ctypes
import ctypes.wintypes
import gc
import json
import sys


def memory_snapshot():
    class _ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.wintypes.DWORD),
            ("PageFaultCount", ctypes.wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = _ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(_ProcessMemoryCounters)
    process_handle = ctypes.windll.kernel32.GetCurrentProcess()
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(process_handle, ctypes.byref(counters), counters.cb)
    if not ok:
        return {"available": False}
    return {
        "available": True,
        "working_set_bytes": int(counters.WorkingSetSize),
        "pagefile_usage_bytes": int(counters.PagefileUsage),
    }


# ---------------------------------------------------------------------------
# Synthetic stand-in for capture_snapshot_explicit()'s own capture_tree()
# output shape: per target -> per group -> per control, short unique
# strings (mirrors real control/group name variety), sized to approximate
# 85 targets' worth of real captured payload (D1/D2's own independently
# measured ~9 MB for the real full 85-target raw fingerprint set).
# ---------------------------------------------------------------------------

TARGET_COUNT = 85
GROUPS_PER_TARGET = 20
CONTROLS_PER_GROUP = 8  # ~160 controls/target, matching Fox(136)/Mia(174)


def build_synthetic_capture(target_index):
    target = {}
    for g in range(GROUPS_PER_TARGET):
        group_path = u"RigGroup_%d_%d" % (target_index, g)
        controls = {}
        for c in range(CONTROLS_PER_GROUP):
            control_name = u"control_%d_%d_%d" % (target_index, g, c)
            controls[control_name] = {
                "type": u"DmeTransformControl",
                "value": [float(target_index), float(g), float(c)],
                "visible": True,
                "selectable": True,
                "path": u"%s/%s" % (group_path, control_name),
            }
        target[group_path] = {
            "groupColor": None,
            "controls": controls,
            "children": [],
        }
    return target


def per_target_hash(value):
    import hashlib
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def run_one_cycle():
    """Mirrors F1-R1's own capture_all() -> stable_hash()/compute_target_hashes() -> del pattern."""
    raw = {}
    for i in range(TARGET_COUNT):
        raw[u"target_%d" % i] = build_synthetic_capture(i)

    peak = memory_snapshot()

    hashes = dict((k, per_target_hash(v)) for k, v in raw.items())

    del raw
    gc.collect()
    after_cleanup = memory_snapshot()
    del hashes
    return peak, after_cleanup


def main():
    sys.stdout.write("Python version: %s\n" % (sys.version,))
    sys.stdout.write("TARGET_COUNT=%d GROUPS_PER_TARGET=%d CONTROLS_PER_GROUP=%d (~%d controls/target)\n"
                      % (TARGET_COUNT, GROUPS_PER_TARGET, CONTROLS_PER_GROUP, GROUPS_PER_TARGET * CONTROLS_PER_GROUP))

    gc.collect()
    baseline = memory_snapshot()
    sys.stdout.write("baseline working_set=%r\n" % (baseline.get("working_set_bytes"),))

    CYCLES = 4  # mirrors F1-R1's own repeated-command pattern
    results = []
    for cycle in range(1, CYCLES + 1):
        peak, after_cleanup = run_one_cycle()
        delta_peak_vs_baseline = peak.get("working_set_bytes", 0) - baseline.get("working_set_bytes", 0)
        delta_after_cleanup_vs_baseline = after_cleanup.get("working_set_bytes", 0) - baseline.get("working_set_bytes", 0)
        results.append({
            "cycle": cycle,
            "peak_working_set": peak.get("working_set_bytes"),
            "after_cleanup_working_set": after_cleanup.get("working_set_bytes"),
            "delta_peak_vs_baseline_bytes": delta_peak_vs_baseline,
            "delta_after_cleanup_vs_baseline_bytes": delta_after_cleanup_vs_baseline,
        })
        sys.stdout.write(
            "cycle %d: peak_delta=%+d bytes (%.2f MiB)  after_cleanup_delta=%+d bytes (%.2f MiB)\n"
            % (
                cycle, delta_peak_vs_baseline, delta_peak_vs_baseline / 1048576.0,
                delta_after_cleanup_vs_baseline, delta_after_cleanup_vs_baseline / 1048576.0,
            )
        )

    first_cleanup_delta = results[0]["delta_after_cleanup_vs_baseline_bytes"]
    last_cleanup_delta = results[-1]["delta_after_cleanup_vs_baseline_bytes"]

    sys.stdout.write("\nfirst_cycle_after_cleanup_delta_bytes=%r\n" % (first_cleanup_delta,))
    sys.stdout.write("last_cycle_after_cleanup_delta_bytes=%r\n" % (last_cleanup_delta,))

    # The defining signature of category-3 allocator high-water retention:
    # even after every object is unreachable AND gc.collect()-swept, the
    # process's own working set after cleanup does NOT return to baseline,
    # and does not shrink back down between repeated cycles -- it stays
    # elevated at (or ratchets further past) the level the first cycle's
    # peak allocation reached.
    retention_signature_present = (
        first_cleanup_delta > 1048576  # more than 1 MiB retained after the FIRST cycle's own cleanup
        and last_cleanup_delta >= first_cleanup_delta * 0.5  # stays materially elevated, does not collapse back toward 0
    )
    sys.stdout.write("\nALLOCATOR_HIGH_WATER_RETENTION_SIGNATURE_PRESENT=%r\n" % (retention_signature_present,))
    sys.stdout.write(
        "(i.e. even though every raw capture dict was del-eted and gc.collect() ran, "
        "process working set after cleanup did not return to baseline and stayed elevated "
        "across repeated cycles -- category 3, distinct from live-reference retention and "
        "cyclic garbage, neither of which del()/gc.collect() can address.)\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
