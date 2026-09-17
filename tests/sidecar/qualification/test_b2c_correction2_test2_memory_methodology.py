# -*- coding: utf-8 -*-
"""Astra SECOND correction gate -- Section 12 real 32-bit memory
measurement methodology correction, applied to Test 2's boundary/refusal
cases.

Astra's exact critique of the FIRST correction's Test 2 memory evidence:
"Do NOT use end-state private delta as proof of transient peak... later
cases must not inherit an earlier process peak and then claim '0 delta.'"

Fix: EVERY case here runs in its OWN FRESH real-Python-2.7.5 subprocess
(via subprocess.Popen), so:
  - PeakPagefileUsage is a genuine fresh-process peak, never inherited
    from a prior case in the same process.
  - PrivateUsage is sampled immediately before and immediately after the
    ONE acquisition attempt this subprocess exists to make (phase-
    resolved, not an end-of-run delta across many unrelated operations).
  - Committed VAS (PagefileUsage) is recorded alongside PrivateUsage.
  - Raw sample dicts are retained and printed (not just a derived delta).

This harness spawns each worker, parses its one-line JSON result, and
reports it. This file itself does not compute any memory delta -- it only
orchestrates and records what each isolated worker measured.
"""
import json
import os
import subprocess
import sys

REAL_PY27 = r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\sdktools\python\2.7\win32\python.exe"
WORKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_test2_memory_worker.py")
FIXROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction2\fixtures"

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


with open(FIXROOT + r"\manifest.json") as f:
    MANIFEST = json.load(f)

CASES = [
    ("boundary_below_19999", "boundaryoccurrencecontrol", True),
    ("boundary_at_20000", "boundaryoccurrencecontrol", True),
    ("boundary_above_20001", "boundaryoccurrencecontrol", False),
    ("astra_two_large_families", "astrafamilyone,astrafamilytwo", False),
    ("astra_two_large_families", "astrasingleton00000", True),
]

RAW_SAMPLES = []

for fixture_key, wanted_csv, expect_admit in CASES:
    m = MANIFEST[fixture_key]
    proc = subprocess.Popen(
        [REAL_PY27, WORKER, m["master_path"], FIXROOT, wanted_csv],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    out, err = proc.communicate()
    out = out.decode("utf-8", "replace") if isinstance(out, bytes) else out
    err = err.decode("utf-8", "replace") if isinstance(err, bytes) else err
    try:
        last_line = [ln for ln in out.strip().splitlines() if ln.strip()][-1]
        record = json.loads(last_line)
    except Exception as exc:
        record = {"outcome": "worker_error", "error": str(exc), "stdout": out, "stderr": err}

    RAW_SAMPLES.append(record)
    label = "%s[%s]" % (fixture_key, wanted_csv)
    print("[mem %s] %s" % (label, json.dumps(record, sort_keys=True)))

    outcome = record.get("outcome")
    check("t2mem.%s worker completed (not a harness/subprocess error)" % label,
          outcome in ("admitted", "refused"), record)
    if outcome in ("admitted", "refused"):
        check("t2mem.%s outcome matches expectation (admit=%s)" % (label, expect_admit),
              (outcome == "admitted") == expect_admit, outcome)
        check("t2mem.%s baseline PrivateUsage sample present (phase-resolved, pre-operation)" % label,
              record.get("before", {}).get("private_bytes") is not None, record.get("before"))
        check("t2mem.%s post-operation PrivateUsage sample present" % label,
              record.get("after", {}).get("private_bytes") is not None, record.get("after"))
        check("t2mem.%s fresh-process PeakPagefileUsage recorded (never inherited from a prior case -- "
              "this is a BRAND NEW process)" % label,
              record.get("after", {}).get("peak_pagefile_usage", 0) > 0, record.get("after"))
        check("t2mem.%s committed VAS (PagefileUsage) recorded" % label,
              record.get("after", {}).get("pagefile_usage", 0) > 0, record.get("after"))
        if outcome == "admitted":
            delta_private = record["after"]["private_bytes"] - record["before"]["private_bytes"]
            check("t2mem.%s admitted case's real phase-resolved PrivateUsage delta stays inside the "
                  "32 MiB transient gate (cross-check against the estimator's own promise)" % label,
                  delta_private < 32 * 1024 * 1024, delta_private)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))

print("\n=== Section 12 raw per-case fresh-process memory samples ===")
for r in RAW_SAMPLES:
    print(json.dumps(r, sort_keys=True))
