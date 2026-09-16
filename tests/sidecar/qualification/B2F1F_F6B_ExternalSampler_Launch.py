# -*- coding: utf-8 -*-
r"""R3-B2F1F Stage F6B external-sampler launcher (fixtureC_1p25x, early-
refused integrated-candidate path). Run from an ordinary terminal
(PowerShell, Python 3.10), NEVER inside SFM.

Usage (PowerShell):
  & "C:\Users\Eman\AppData\Local\Programs\Python\Python310\python.exe" "<this file's absolute path>"
"""
import os
import subprocess
import sys

RUN_ID = "F6B_Refuse_C1p25"
RESULTS_DIR = r"C:\Users\Public\Documents"
DONE_MARKER_PATH = os.path.join(RESULTS_DIR, "CGN_R3_B2F1F_F6B_Refuse_C1p25_DONE.marker")
CSV_OUT = os.path.join(RESULTS_DIR, "B2F1F_F6B_Refuse_C1p25_mem.csv")
VAS_OUT = os.path.join(RESULTS_DIR, "B2F1F_F6B_Refuse_C1p25_vas.json")
MAX_SECONDS = "120"

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
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) >= 2:
            try:
                pids.append(int(parts[1]))
            except ValueError:
                pass
    return pids


def main():
    if not os.path.isfile(SAMPLER_SCRIPT):
        print("ERROR: gate2a_external_sampler.py not found next to this launcher at:")
        print("  %s" % SAMPLER_SCRIPT)
        sys.exit(1)

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
    print("Now go run CGN_R3_B2F1F_F6B_Refuse_C1p25.py from SFM's Main Menu.")

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
