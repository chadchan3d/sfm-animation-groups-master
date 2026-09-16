# -*- coding: utf-8 -*-
"""R3-B2F1A external-sampler launcher for Run 2 (fixtureA_1p5x).

Run this from an ordinary terminal on the host machine (Python 3), NEVER
inside SFM, AFTER SFM has been restarted and BEFORE you run
CGN_R3_B2F1A_ExternalSampler_Run2_fixtureA_1p5x.py from SFM's Main Menu.

What it does:
  1. Finds the one running sfm.exe process (fails loudly, does not guess,
     if zero or more than one is found).
  2. Launches gate2a_external_sampler.py (the already-qualified, genuinely
     separate-process R2 external sampler -- reused verbatim, never
     reimplemented) targeting that PID.
  3. Waits for CGN_R3_B2F1_ExternalSampler_Run2_fixtureA_1p5x_DONE.marker
     to appear (written by the in-SFM script when it finishes) plus a
     short trailing grace period, then stops automatically.
  4. Writes this run's own memory CSV and VAS JSON, uniquely named, next
     to the in-SFM script's own result files in
     C:\\Users\\Public\\Documents -- nothing overwrites Run 1's evidence
     or the in-SFM JSON result.

Does NOT launch SFM itself. Does NOT modify anything inside SFM.
"""
import os
import subprocess
import sys
import time

RUN_ID = "Run2_fixtureA_1p5x"
RESULTS_DIR = r"C:\Users\Public\Documents"
DONE_MARKER_PATH = os.path.join(RESULTS_DIR, "CGN_R3_B2F1_ExternalSampler_%s_DONE.marker" % RUN_ID)
CSV_OUT = os.path.join(RESULTS_DIR, "B2F1A_ExternalSampler_%s_mem.csv" % RUN_ID)
VAS_OUT = os.path.join(RESULTS_DIR, "B2F1A_ExternalSampler_%s_vas.json" % RUN_ID)
MAX_SECONDS = "120"  # generous -- Run 1 completed in ~7s inside real SFM

SAMPLER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate2a_external_sampler.py")


def find_sfm_pid():
    out = subprocess.check_output(
        ["tasklist", "/FI", "IMAGENAME eq sfm.exe", "/FO", "CSV", "/NH"],
        universal_newlines=True,
    )
    pids = []
    for line in out.splitlines():
        line = line.strip()
        if not line or line.upper().startswith("INFO:"):
            continue
        # CSV row: "sfm.exe","1234","Console","1","500,000 K"
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) >= 2:
            try:
                pids.append(int(parts[1]))
            except ValueError:
                pass
    return pids


def main():
    if os.path.isfile(DONE_MARKER_PATH):
        print("WARNING: a stale DONE marker from a previous run already exists at:")
        print("  %s" % DONE_MARKER_PATH)
        print("Delete it before proceeding, or this sampler will stop immediately.")
        sys.exit(1)

    pids = find_sfm_pid()
    if len(pids) == 0:
        print("No running sfm.exe process found. Start/restart SFM first, then re-run this launcher.")
        sys.exit(1)
    if len(pids) > 1:
        print("Multiple sfm.exe processes found (%r) -- refusing to guess which one to sample. "
              "Close the extra instance(s) and re-run this launcher." % (pids,))
        sys.exit(1)

    pid = pids[0]
    print("Found sfm.exe PID %d." % pid)
    print("Starting external sampler -- leave this window open.")
    print("Now go run CGN_R3_B2F1A_ExternalSampler_Run2_fixtureA_1p5x.py from SFM's Main Menu.")

    rc = subprocess.call([
        sys.executable, SAMPLER_SCRIPT,
        str(pid), DONE_MARKER_PATH, CSV_OUT, VAS_OUT, MAX_SECONDS,
    ])
    if rc != 0:
        print("External sampler exited with code %d." % rc)
        sys.exit(rc)

    print("External sampler finished.")
    print("Memory samples: %s" % CSV_OUT)
    print("VAS samples:    %s" % VAS_OUT)


if __name__ == "__main__":
    main()
