# -*- coding: utf-8 -*-
"""Final targeted infrastructure correction -- Test 1 / BLOCKER 1
regression probe: offset-independent preflight memory.

Each directory-offset case runs in its OWN FRESH real-32-bit-Python-
2.7.5 subprocess (`_test1_offset_sweep_worker.py`), so PeakPagefileUsage/
PeakWorkingSetSize are genuine fresh-process peaks -- never inherited
from a prior, larger offset earlier in the sweep. PASS requires: the
maximum single preflight (header/directory) read request stays bounded
regardless of directory offset, and process memory growth from before
to after stays nearly constant across the whole offset sweep (never
scaling with the directory offset itself) -- the exact independently-
reproduced defect (~8 MiB offset -> ~16 MiB peak, ~15.9 MiB -> ~31.8 MiB)
must NOT reproduce here.

Astra Narrow Issue E: paths derived from `__file__`.
"""
import json
import os
import subprocess
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CORRECTION6_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction6")
FIXROOT = os.path.join(CORRECTION6_ROOT, "fixtures_offset_sweep")
WORKER = os.path.join(_THIS_DIR, "_test1_offset_sweep_worker_correction6.py")
REAL_PY27 = r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\sdktools\python\2.7\win32\python.exe"

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


with open(os.path.join(FIXROOT, "manifest.json")) as f:
    MANIFEST = json.load(f)

DUMMY_EXPECTED_SHA = "0" * 64  # irrelevant to this probe -- see worker docstring
SMALL_PREFLIGHT_CEILING = 108 + 65536  # HEADER_SIZE + _MAX_PREFLIGHT_REGION_BYTES

records = []
for label, entry in sorted(MANIFEST["offsets"].items(), key=lambda kv: kv[1]["directory_offset_bytes"]):
    artifact_path = os.path.join(FIXROOT, entry["artifact_relative_path"])
    proc = subprocess.Popen(
        [REAL_PY27, WORKER, artifact_path, DUMMY_EXPECTED_SHA],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    out, err = proc.communicate()
    out = out.decode("utf-8", "replace") if isinstance(out, bytes) else out
    try:
        record = json.loads([ln for ln in out.strip().splitlines() if ln.strip()][-1])
    except Exception as exc:
        record = {"outcome": "worker_error", "error": str(exc), "stdout": out,
                   "stderr": err.decode("utf-8", "replace") if isinstance(err, bytes) else err}
    record["label"] = label
    record["directory_offset_bytes"] = entry["directory_offset_bytes"]
    records.append(record)
    print("[offset %-9s] directory_offset=%10d %s" % (label, entry["directory_offset_bytes"], json.dumps(record, sort_keys=True)))

for r in records:
    label = r["label"]
    check("t1.%s worker completed (not a subprocess/interpreter error)" % label,
          r.get("outcome") not in (None, "worker_error", "wrong_interpreter"), r)
    if r.get("outcome") in (None, "worker_error", "wrong_interpreter"):
        continue
    check("t1.%s max single preflight (header/directory) read request stays bounded "
          "(<= %d bytes) regardless of an %s-byte directory offset" % (label, SMALL_PREFLIGHT_CEILING, r["directory_offset_bytes"]),
          r["max_single_preflight_read"] <= SMALL_PREFLIGHT_CEILING, r["max_single_preflight_read"])
    check("t1.%s total preflight bytes returned stays bounded (<= %d bytes)" % (label, SMALL_PREFLIGHT_CEILING),
          r["preflight_bytes_read"] <= SMALL_PREFLIGHT_CEILING, r["preflight_bytes_read"])

# ---------------------------------------------------------------------
# Decisive cross-case comparison: private-bytes delta must NOT scale
# with directory offset. Compare the smallest-offset case's delta
# against the largest-offset case's delta -- they must be close (never
# growing by anything close to the ~16 MiB/~31.8 MiB independently-
# reproduced defect magnitude).
# ---------------------------------------------------------------------
valid_records = [r for r in records if r.get("before") and r.get("after")]
if len(valid_records) >= 2:
    deltas = [(r["label"], r["directory_offset_bytes"], r["after"]["private_bytes"] - r["before"]["private_bytes"])
              for r in valid_records]
    print("\n[deltas] " + ", ".join("%s(offset=%d)=%d" % d for d in deltas))
    smallest_offset_delta = min(deltas, key=lambda d: d[1])[2]
    largest_offset_delta = max(deltas, key=lambda d: d[1])[2]
    growth = largest_offset_delta - smallest_offset_delta
    check("t1.decisive private-bytes delta growth from smallest to largest directory offset "
          "stays small (< 4 MiB) -- NOT offset-proportional (the independently-reproduced defect "
          "showed ~16-32 MiB growth across this same offset range)",
          growth < 4 * 1024 * 1024, growth)
    check("t1.decisive largest-offset (15.9 MiB) case's own private-bytes delta stays well under "
          "the ~31.8 MiB the independently-reproduced defect showed",
          largest_offset_delta < 8 * 1024 * 1024, largest_offset_delta)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
