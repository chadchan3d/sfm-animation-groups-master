# -*- coding: utf-8 -*-
"""B2C-C Targeted Audit Correction, Section 4: proves the exit-status
hardening added to the four RESULTS-accumulating B2C-C qualification
scripts (`test_b2c_c_plan_layer_equivalence.py`, `test_b2c_c_execution_
layer_equivalence.py`, `test_b2c_c_broker_mediated_authority_sanity.py`,
`test_b2c_c_fake_dme_addchild_regression.py`) actually works, in both
directions:

1. A synthetic script mirroring the EXACT hardening pattern each of the
   four files now ends with (`if not all(condition for _, condition in
   RESULTS): sys.exit(1)`), with one check deliberately forced to fail,
   is run as a REAL subprocess under the SAME real Python 2.7.5
   interpreter this whole project uses -- its process exit code must be
   non-zero.
2. The SAME synthetic script with every check passing must exit zero --
   proving the hardening does not always fail regardless of content.
3. One of the four REAL, already-hardened files is run as a real
   subprocess (its current, genuinely-passing state) and must exit
   zero -- direct evidence the hardening is live in production files,
   not just in this isolated synthetic mirror.

Never launches SFM. Read-only with respect to the frozen production
file and the qualified Correction6 candidate.
"""
import os
import subprocess
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PY27 = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\sdktools\python\2.7\win32\python.exe"
)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

_SYNTHETIC_TEMPLATE = """# -*- coding: utf-8 -*-
import sys
RESULTS = []
def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%%s] %%s" %% ("PASS" if condition else "FAIL", name))
check("synthetic.always_true", True)
check("synthetic.forced", %(forced)s)
print("RESULT: %%d/%%d" %% (sum(1 for _, c in RESULTS if c), len(RESULTS)))
if not all(condition for _, condition in RESULTS):
    sys.exit(1)
"""

_scratch_dir = os.path.join(_THIS_DIR, "_exit_status_self_test_scratch")
if not os.path.isdir(_scratch_dir):
    os.makedirs(_scratch_dir)

passing_path = os.path.join(_scratch_dir, "_synthetic_passing.py")
failing_path = os.path.join(_scratch_dir, "_synthetic_failing.py")
with open(passing_path, "w") as f:
    f.write(_SYNTHETIC_TEMPLATE % {"forced": "True"})
with open(failing_path, "w") as f:
    f.write(_SYNTHETIC_TEMPLATE % {"forced": "False"})

try:
    passing_proc = subprocess.Popen([PY27, passing_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    passing_out, passing_err = passing_proc.communicate()
    check("synthetic_all_pass.exit_code_zero a synthetic script with every RESULTS check passing "
          "exits 0 under the real Python 2.7.5 interpreter", passing_proc.returncode == 0,
          (passing_proc.returncode, passing_out, passing_err))

    failing_proc = subprocess.Popen([PY27, failing_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    failing_out, failing_err = failing_proc.communicate()
    check("synthetic_forced_failure.exit_code_nonzero a synthetic script with ONE RESULTS check "
          "deliberately forced to fail exits NON-ZERO under the real Python 2.7.5 interpreter "
          "(the exact hardening pattern added to all four real B2C-C harnesses)",
          failing_proc.returncode != 0, (failing_proc.returncode, failing_out, failing_err))
finally:
    for p in (passing_path, failing_path):
        if os.path.isfile(p):
            os.remove(p)
    try:
        os.rmdir(_scratch_dir)
    except OSError:
        pass

# Direct evidence on a REAL, already-hardened file: its current,
# genuinely-passing state must exit 0 as a real subprocess.
real_target = os.path.join(_THIS_DIR, "test_b2c_c_fake_dme_addchild_regression.py")
real_proc = subprocess.Popen([PY27, real_target], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
real_out, real_err = real_proc.communicate()
check("real_hardened_file.exit_code_zero_when_passing the REAL, already-hardened "
      "test_b2c_c_fake_dme_addchild_regression.py exits 0 as a subprocess in its current, "
      "genuinely-passing state", real_proc.returncode == 0, real_proc.returncode)
check("real_hardened_file.contains_exit_guard the real file's source literally contains the "
      "sys.exit(1) hardening guard",
      b"sys.exit(1)" in open(real_target, "rb").read())

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(condition for _, condition in RESULTS):
    sys.exit(1)
