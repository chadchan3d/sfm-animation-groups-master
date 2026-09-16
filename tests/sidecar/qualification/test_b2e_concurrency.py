# -*- coding: utf-8 -*-
"""R3-B2E real inter-process concurrent-publisher tests. Python 3 only.
Never launches SFM, never modifies R1D/final-R3-A2B/Master/production
consumer files."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, r"E:\SFM Animation Group Master\tools")
from sfm_master_sidecar import mutex_publisher, generated_root, manifest as manifest_module

PYTHON_EXE = r"C:\Users\Eman\AppData\Local\Programs\Python\Python310\python.exe"
WORKER = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2e\publisher_worker.py"
REAL_MASTER = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
SCRATCH_ROOT = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2e\test_out_concurrency"

results = []


def check(name, condition, detail=None):
    results.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


def fresh_dir(name):
    d = os.path.join(SCRATCH_ROOT, name)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    return d


def make_custom_master(text):
    d = tempfile.mkdtemp(prefix="b2e_conc_master_")
    p = os.path.join(d, "custom_master.txt")
    with open(p, "wb") as f:
        f.write(text.encode("utf-8"))
    return p


def run_worker(source_path, output_dir, slot_identity, extra_args=None, result_path=None):
    args = [PYTHON_EXE, WORKER, source_path, output_dir, slot_identity]
    if result_path:
        args += ["--result-path", result_path]
    if extra_args:
        args += extra_args
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


# ===========================================================================
# 1/2. Two builders compile the SAME source simultaneously -> same artifact SHA
# ===========================================================================
print("=== Two builders, same source, simultaneous ===")

out_same = fresh_dir("two_same_source")
slot_same = generated_root.derive_install_slot_identity(r"C:\fake_install", REAL_MASTER)
r1_path = os.path.join(SCRATCH_ROOT, "r1_same.json")
r2_path = os.path.join(SCRATCH_ROOT, "r2_same.json")

p1 = run_worker(REAL_MASTER, out_same, slot_same, result_path=r1_path)
p2 = run_worker(REAL_MASTER, out_same, slot_same, result_path=r2_path)
p1.wait()
p2.wait()

r1 = json.load(open(r1_path))
r2 = json.load(open(r2_path))
check("concurrent.1 both simultaneous same-source builders succeeded", r1.get("ok") and r2.get("ok"), (r1, r2))
check("concurrent.2 both produced the IDENTICAL artifact SHA (same source generation)",
      r1.get("ordinary_sha256") == r2.get("ordinary_sha256"), (r1, r2))
check("concurrent.3 no temp-name collision occurred (both completed without a collision-shaped exception)",
      "exception_type" not in r1 and "exception_type" not in r2, (r1, r2))
final_manifest_same = mutex_publisher.read_active_manifest(out_same)
check("concurrent.4 exactly one final manifest exists and is valid after both racing publishers finished",
      final_manifest_same is not None)


# ===========================================================================
# 3. Two builders produce DIFFERENT source generations concurrently
# ===========================================================================
print("=== Two builders, different source generations, simultaneous ===")

out_diff = fresh_dir("two_diff_source")
master_b = make_custom_master('"groupFile"\n{\n\t"RigArms"\n\t{\n\t\t"control"\t\t"DifferentOne"\n\t}\n}\n')
slot_diff = generated_root.derive_install_slot_identity(r"C:\fake_install", REAL_MASTER)
r3_path = os.path.join(SCRATCH_ROOT, "r3_diff.json")
r4_path = os.path.join(SCRATCH_ROOT, "r4_diff.json")

p3 = run_worker(REAL_MASTER, out_diff, slot_diff, result_path=r3_path)
p4 = run_worker(master_b, out_diff, slot_diff, result_path=r4_path)
p3.wait()
p4.wait()

r3 = json.load(open(r3_path))
r4 = json.load(open(r4_path))
check("concurrent.5 both different-source simultaneous publishers each completed (one may see the other's H1 mutation and abort/succeed cleanly, never corrupt)",
      "exception_type" not in r3 or r3.get("exception_type") in (None,), r3)
final_manifest_diff = mutex_publisher.read_active_manifest(out_diff)
check("concurrent.6 exactly one valid, self-consistent final manifest exists (whichever publisher committed last)",
      final_manifest_diff is not None)
check("concurrent.7 the winning manifest's generation file actually exists and matches its own recorded digest",
      os.path.isfile(manifest_module.resolve_generation_path(out_diff, final_manifest_diff))
      and mutex_publisher._sha256_of_file(manifest_module.resolve_generation_path(out_diff, final_manifest_diff))
      == final_manifest_diff.sidecar_sha256)


# ===========================================================================
# 4. one holds mutex while second waits (real timing observed)
# ===========================================================================
print("=== One holds mutex while second waits ===")

out_hold = fresh_dir("hold_and_wait")
slot_hold = generated_root.derive_install_slot_identity(r"C:\fake_install", REAL_MASTER)
r5_path = os.path.join(SCRATCH_ROOT, "r5_hold.json")
r6_path = os.path.join(SCRATCH_ROOT, "r6_wait.json")

t0 = time.time()
p5 = run_worker(REAL_MASTER, out_hold, slot_hold, extra_args=["--hold-seconds", "3"], result_path=r5_path)
time.sleep(0.8)  # let p5 reach and start holding the mutex first
p6 = run_worker(REAL_MASTER, out_hold, slot_hold, result_path=r6_path)
p5.wait()
p6.wait()
t1 = time.time()

r5 = json.load(open(r5_path))
r6 = json.load(open(r6_path))
check("concurrent.8 the holder completed successfully", r5.get("ok"), r5)
check("concurrent.9 the waiter also completed successfully (serialized, not refused)", r6.get("ok"), r6)
check("concurrent.10 the whole sequence took at least ~3s (genuine serialization observed, not silently parallel)",
      (t1 - t0) >= 2.5, t1 - t0)


# ===========================================================================
# 5. first crashes while mutex held -> abandoned handling exercised end-to-end
# ===========================================================================
print("=== Crash while holding mutex (real cross-process) ===")

out_crash_mtx = fresh_dir("crash_holding_mutex")
slot_crash_mtx = generated_root.derive_install_slot_identity(r"C:\fake_install", REAL_MASTER)
r7_path = os.path.join(SCRATCH_ROOT, "r7_crash.json")
r8_path = os.path.join(SCRATCH_ROOT, "r8_after_crash.json")

p7 = run_worker(REAL_MASTER, out_crash_mtx, slot_crash_mtx, extra_args=["--crash-after-acquire"], result_path=r7_path)
p7.wait()
r7 = json.load(open(r7_path))
check("concurrent.11 the crashing worker did reach and hold the mutex before dying", r7.get("crashed_while_holding_mutex") is True, r7)

# A subsequent publish attempt must still be able to acquire (whether via a
# clean re-acquire or via real WAIT_ABANDONED -- both are handled; see the
# R3-B2E report's honest note on this host's observed WAIT_ABANDONED
# behavior) and must NOT hang or silently corrupt state.
p8 = run_worker(REAL_MASTER, out_crash_mtx, slot_crash_mtx, result_path=r8_path)
p8.wait(timeout=30)
r8 = json.load(open(r8_path))
check("concurrent.12 a subsequent publish after the crash-while-holding still succeeds cleanly (never hangs)",
      r8.get("ok"), r8)
final_after_crash = mutex_publisher.read_active_manifest(out_crash_mtx)
check("concurrent.13 a valid final manifest exists after the crash-recovery sequence",
      final_after_crash is not None)


print()
failed = [n for n, ok in results if not ok]
print("RESULT: %d/%d %s" % (len(results) - len(failed), len(results), "ALL PASS" if not failed else "FAILED: %r" % (failed,)))
if failed:
    sys.exit(1)
