# -*- coding: utf-8 -*-
"""GATE 2A TEMPORARY EXTERNAL MONITOR (Python 3, runs on the host machine,
never inside SFM). Samples a target process's memory counters at a bounded
cadence and periodically scans its virtual address space, correlating with
the in-SFM probe's stage-marker log and DONE marker. Test-only; not part of
any production module.

Usage: python gate2a_external_sampler.py <PID> <done_marker_path> <output_csv_path> <vas_output_path> [max_seconds]
"""

import ctypes
import json
import sys
import time
from ctypes import wintypes

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_FREE = 0x10000


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
        ("PartitionId", wintypes.WORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
psapi.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD,
]
kernel32.VirtualQueryEx.restype = ctypes.c_size_t
kernel32.VirtualQueryEx.argtypes = [
    wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(MEMORY_BASIC_INFORMATION), ctypes.c_size_t,
]


def open_target(pid):
    h = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        raise OSError("OpenProcess failed for PID %d (err=%d)" % (pid, ctypes.get_last_error()))
    return h


def sample_memory(h):
    counters = PROCESS_MEMORY_COUNTERS_EX()
    counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
    ok = psapi.GetProcessMemoryInfo(h, ctypes.byref(counters), counters.cb)
    if not ok:
        return None
    return {
        "WorkingSetSize": int(counters.WorkingSetSize),
        "PeakWorkingSetSize": int(counters.PeakWorkingSetSize),
        "PagefileUsage": int(counters.PagefileUsage),
        "PeakPagefileUsage": int(counters.PeakPagefileUsage),
        "PrivateUsage": int(counters.PrivateUsage),
    }


def scan_vas(h, ceiling):
    """Walk the target's address space from 0 up to `ceiling`, tallying
    committed/reserved/free bytes and the largest free region. Bounded --
    stops at `ceiling` (the process's own effective VA limit), not an
    unbounded 64-bit scan."""
    addr = 0
    committed = 0
    reserved = 0
    free = 0
    largest_free = 0
    region_count = 0
    mbi = MEMORY_BASIC_INFORMATION()
    mbi_size = ctypes.sizeof(MEMORY_BASIC_INFORMATION)
    while addr < ceiling:
        ret = kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), mbi_size)
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
            addr += 0x1000  # safety: never infinite-loop on a zero-size report
    return {
        "committed": committed,
        "reserved": reserved,
        "free": free,
        "largest_free_region": largest_free,
        "region_count": region_count,
        "scanned_up_to": addr,
    }


def is_done(done_marker_path):
    """True iff the DONE marker file can be opened. Same detection
    semantics as the original inline `try: open(...): ... except OSError`
    check, factored out so it can be swapped for a deterministic fake in
    offline tests (see test_gate2a_vas_coverage.py)."""
    try:
        with open(done_marker_path, "rb"):
            return True
    except OSError:
        return False


def run_sampling_loop(h, done_marker_path, max_seconds, sample_interval, vas_interval, vas_ceiling,
                       sample_memory_fn=sample_memory, scan_vas_fn=scan_vas,
                       time_fn=time.time, sleep_fn=time.sleep, is_done_fn=is_done,
                       trailing_grace_seconds=2.0, log_fn=print):
    """The sampler's full scheduling/shutdown control flow -- factored out
    of main() so it can be exercised offline with injected fakes (no real
    PID, no ctypes). Behavior is IDENTICAL to the original inline loop for
    every path except the DONE-observed shutdown sequence, which is
    corrected here (SFM_CGN_R2_W2_P03_VAS_Stream_Coverage_Correction,
    2026-09-15):

    Root cause of the original defect: the DONE-observed branch performed
    ONLY trailing memory sampling for `trailing_grace_seconds`, then
    `break`-ed out of the loop entirely -- it never reached the `if now -
    last_vas >= vas_interval: scan_vas(...)` check, which lives solely in
    the pre-DONE loop body. So once DONE was observed, NO further VAS scan
    could ever happen, regardless of cadence timing -- this is why memory
    sampling correctly continued for ~2s after DONE/RUN_COMPLETE while the
    VAS stream stopped up to `vas_interval` (2.0s) earlier than that, with
    no relationship to DONE detection cost, exception handling, or cadence
    ordering (all ruled out; the VAS-scan call site is simply absent from
    this branch).

    Correction: after the trailing memory-sampling grace period, perform
    exactly ONE final, unconditional VAS scan before returning. This
    guarantees at least one VAS record with a timestamp strictly later
    than the DONE observation timestamp (and therefore later than the
    formal BACKING_CLOSED stage, which always precedes DONE by
    construction) -- regardless of where in the `vas_interval` cadence
    DONE happened to occur."""
    samples = []
    vas_samples = []
    t_start = time_fn()
    last_vas = 0.0
    while True:
        now = time_fn()
        elapsed = now - t_start
        if elapsed > max_seconds:
            log_fn("max_seconds reached, stopping")
            return samples, vas_samples, "timeout"

        if is_done_fn(done_marker_path):
            done_observed_ts = now
            log_fn("DONE marker observed, sampling %.2fs longer for trailing data then stopping" % trailing_grace_seconds)
            extra_deadline = done_observed_ts + trailing_grace_seconds
            while time_fn() < extra_deadline:
                mem = sample_memory_fn(h)
                if mem is not None:
                    samples.append((time_fn(), mem))
                sleep_fn(sample_interval)
            # Final VAS scan -- unconditional, never gated by vas_interval
            # cadence -- guarantees VAS coverage through at least the DONE
            # observation instant, correcting the defect above.
            try:
                final_vas = scan_vas_fn(h, vas_ceiling)
                final_vas_ts = time_fn()
                vas_samples.append((final_vas_ts, final_vas))
                exit_reason = "done_with_final_vas"
            except Exception as exc:
                log_fn("final post-DONE VAS scan failed: %r" % (exc,))
                exit_reason = "done_final_vas_failed"
            return samples, vas_samples, exit_reason

        mem = sample_memory_fn(h)
        if mem is not None:
            samples.append((now, mem))
        else:
            log_fn("sample_memory failed at t=%.2f (process may have exited)" % elapsed)
            return samples, vas_samples, "process_exited"

        if now - last_vas >= vas_interval:
            try:
                vas = scan_vas_fn(h, vas_ceiling)
                vas_samples.append((now, vas))
            except Exception as exc:
                log_fn("VAS scan failed at t=%.2f: %r" % (elapsed, exc))
            last_vas = now

        sleep_fn(sample_interval)


def main():
    pid = int(sys.argv[1])
    done_marker_path = sys.argv[2]
    csv_path = sys.argv[3]
    vas_path = sys.argv[4]
    max_seconds = float(sys.argv[5]) if len(sys.argv) > 5 else 90.0
    vas_ceiling = int(sys.argv[6]) if len(sys.argv) > 6 else (4 * 1024 * 1024 * 1024)
    sample_interval = 0.15
    vas_interval = 2.0

    h = open_target(pid)
    print("opened PID %d, sampling for up to %.1fs (interval=%.2fs, VAS-scan interval=%.2fs, VAS ceiling=%d)" % (
        pid, max_seconds, sample_interval, vas_interval, vas_ceiling,
    ))

    samples, vas_samples, exit_reason = run_sampling_loop(
        h, done_marker_path, max_seconds, sample_interval, vas_interval, vas_ceiling)
    print("sampling loop exit reason: %s" % exit_reason)

    kernel32.CloseHandle(h)

    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("timestamp,WorkingSetSize,PeakWorkingSetSize,PagefileUsage,PeakPagefileUsage,PrivateUsage\n")
        for ts, mem in samples:
            f.write("%.4f,%d,%d,%d,%d,%d\n" % (
                ts, mem["WorkingSetSize"], mem["PeakWorkingSetSize"],
                mem["PagefileUsage"], mem["PeakPagefileUsage"], mem["PrivateUsage"],
            ))

    with open(vas_path, "w", encoding="utf-8") as f:
        json.dump([{"timestamp": ts, **vas} for ts, vas in vas_samples], f, indent=2)

    print("wrote %d memory samples to %s" % (len(samples), csv_path))
    print("wrote %d VAS scans to %s" % (len(vas_samples), vas_path))


if __name__ == "__main__":
    main()
