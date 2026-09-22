# -*- coding: utf-8 -*-
"""Production Normalizer Integration (2026-09-22), Section 9A: import/
bootstrap qualification for the module-level authority bootstrap block
this integration added to the frozen production Normalizer.

Extracts the bootstrap block VERBATIM (exact line range, SHA-256 pinned)
from the real, now-integrated frozen production Normalizer, and execs it
in a controlled, isolated environment that mimics the real SFM layout
this block expects: a fake `game/sfm.exe` plus `game/usermod/scripts/sfm/
mainmenu/ChadChan3D/sfm_master_authority_productionized/` containing a
REAL, byte-identical copy of the qualified package. The block itself
never touches sfmApp/sfmClipEditor/vs/PySide (confirmed by direct source
reading -- those are only referenced later, inside
RebuildControlGroupsProductionRun methods, not at bootstrap time), so it
can be exec'd standalone with no SFM-specific stubbing.

Proves:
  - the block imports the canonical installed package using only
    sys.executable-derived paths -- no __file__, no CWD dependency (run
    from an unrelated CWD, in a real separate subprocess, with PYTHONPATH
    cleared);
  - the pinned RUNTIME_API_VERSION/RUNTIME_BUILD_ID literals in the
    integration match the accepted package's real, current values;
  - a stale/wrong RUNTIME_BUILD_ID in the deployed copy is rejected by
    this integration's own _authority_verify_bootstrap_identity(), before
    any broker construction;
  - the block runs successfully under real Python 2.7.5 (matching the
    embedded SFM interpreter) in addition to Python 3.10.

Never launches SFM. Read-only with respect to the frozen production
Normalizer and the canonical Master (both are only hashed/read here).
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CORRECTION6_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction6")
REAL_AUTHORITY_PACKAGE_DIR = os.path.join(
    CORRECTION6_ROOT, "sfm_master_authority_productionized"
)
REAL_SIDECAR_PACKAGE_DIR = r"E:\SFM Animation Group Master\tools\sfm_master_sidecar"

FROZEN_NORMALIZER_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py"
)
EXPECTED_FROZEN_NORMALIZER_SHA256 = (
    "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"
)

# 1-indexed, inclusive. Re-verify with: sed -n '176,361p' Rebuild_Control_Groups_Normalizer.py
# (range widened by the fail-closed native-Master-protect correction,
# 2026-09-22 -- content through native_master_protect_release() changed,
# see test_normalizer_integration_native_protect.py for the functional
# proof of the new fail-closed behavior)
BOOTSTRAP_BLOCK_RANGE = (176, 361)
EXPECTED_BOOTSTRAP_BLOCK_SHA256 = (
    "7be3dae59f0c536fccf11fac0ab9eccd665a4359895c2b7bf4cee4c0714571cd"
)

RUNNER_TEMPLATE = u'''# -*- coding: utf-8 -*-
import os
import sys

sys.executable = %(fake_exe)r

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%%s] %%s%%s" %% ("PASS" if condition else "FAIL", name, ("" if condition else " -- %%r" %% (detail,))))


print("Interpreter: %%s" %% sys.version)
print("cwd: %%r" %% os.getcwd())
print("PYTHONPATH env: %%r" %% os.environ.get("PYTHONPATH"))

import ctypes

ns = {"os": os, "sys": sys, "ctypes": ctypes}
try:
    exec(compile(%(block_source)r, "<bootstrap_block_extract>", "exec"), ns)
    check("bootstrap.execs_without_exception", True)
except Exception as exc:
    check("bootstrap.execs_without_exception", False, exc)
    ns = None

if ns is not None:
    check(
        "bootstrap.mainmenu_dir_matches_fake_layout",
        ns.get("_AUTHORITY_MAINMENU_DIR") == %(expected_mainmenu_dir)r,
        ns.get("_AUTHORITY_MAINMENU_DIR"),
    )
    check(
        "bootstrap.no_repo_or_cwd_path_in_mainmenu_dir",
        "SFM Animation Group Master" not in (ns.get("_AUTHORITY_MAINMENU_DIR") or "")
        and os.getcwd() not in (ns.get("_AUTHORITY_MAINMENU_DIR") or ""),
    )
    authority_runtime = ns.get("authority_runtime")
    check("bootstrap.runtime_module_present", authority_runtime is not None)
    if authority_runtime is not None:
        check(
            "bootstrap.build_id_matches_expected",
            authority_runtime.RUNTIME_BUILD_ID == %(expected_build_id)r,
            authority_runtime.RUNTIME_BUILD_ID,
        )
        check(
            "bootstrap.api_version_matches_expected",
            authority_runtime.RUNTIME_API_VERSION == %(expected_api_version)r,
            authority_runtime.RUNTIME_API_VERSION,
        )
        check("bootstrap.is_canonical", authority_runtime.is_canonical())

print("\\nRESULT: %%d/%%d %%s" %% (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(c for _, c in RESULTS):
    sys.exit(1)
'''

RUNNER_TEMPLATE_NEGATIVE = u'''# -*- coding: utf-8 -*-
import ctypes
import os
import sys

sys.executable = %(fake_exe)r

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%%s] %%s%%s" %% ("PASS" if condition else "FAIL", name, ("" if condition else " -- %%r" %% (detail,))))


print("Interpreter: %%s" %% sys.version)

ns = {"os": os, "sys": sys, "ctypes": ctypes}
raised = None
try:
    exec(compile(%(block_source)r, "<bootstrap_block_extract>", "exec"), ns)
except Exception as exc:
    raised = exc

check("bootstrap.stale_build_id_rejected_with_exception", raised is not None, raised)
if raised is not None:
    message = str(raised)
    check(
        "bootstrap.rejection_names_both_build_ids",
        %(old_build_id)r in message and %(new_build_id)r in message,
        message,
    )
    # No separate "rejection is before broker use" check is meaningful here:
    # get_broker() is not part of this extracted block at all (it is only
    # ever called later, from inside a per-command method that this
    # bootstrap-only harness never execs) -- the raise above IS the whole
    # proof, structurally, not something a runtime assertion can add to.

print("\\nRESULT: %%d/%%d %%s" %% (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(c for _, c in RESULTS):
    sys.exit(1)
'''


def _read_and_verify_normalizer():
    with open(FROZEN_NORMALIZER_PATH, "rb") as f:
        data = f.read()
    actual = hashlib.sha256(data).hexdigest()
    if actual != EXPECTED_FROZEN_NORMALIZER_SHA256:
        raise AssertionError(
            "frozen Normalizer SHA-256 mismatch: expected %s, got %s"
            % (EXPECTED_FROZEN_NORMALIZER_SHA256, actual)
        )
    return data.decode("ascii")


def _extract_bootstrap_block(text):
    lines = text.splitlines()
    start, end = BOOTSTRAP_BLOCK_RANGE
    block = "\n".join(lines[start - 1:end]) + "\n"
    actual = hashlib.sha256(block.encode("ascii")).hexdigest()
    if actual != EXPECTED_BOOTSTRAP_BLOCK_SHA256:
        raise AssertionError(
            "bootstrap block SHA-256 mismatch: expected %s, got %s -- line range %r may be stale"
            % (EXPECTED_BOOTSTRAP_BLOCK_SHA256, actual, BOOTSTRAP_BLOCK_RANGE)
        )
    return block


def _build_fake_layout(root):
    game_dir = os.path.join(root, "game")
    mainmenu_dir = os.path.join(
        game_dir, "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D"
    )
    os.makedirs(mainmenu_dir)
    fake_exe = os.path.join(game_dir, "sfm.exe")
    with open(fake_exe, "wb") as f:
        f.write(b"not a real executable -- path identity only\n")
    shutil.copytree(
        REAL_AUTHORITY_PACKAGE_DIR,
        os.path.join(mainmenu_dir, "sfm_master_authority_productionized"),
        ignore=shutil.ignore_patterns("*.pyc", "__pycache__"),
    )
    # normalizer_compat_adapter.py imports resource_estimator.py, which
    # imports `from sfm_master_sidecar import format` at module level --
    # so this sibling package must also be on sys.path for the bootstrap
    # block's own imports to succeed, exactly as it would need to be in
    # a real installed deployment (see this integration's own report,
    # "exact package/bootstrap entry path used").
    shutil.copytree(
        REAL_SIDECAR_PACKAGE_DIR,
        os.path.join(mainmenu_dir, "sfm_master_sidecar"),
        ignore=shutil.ignore_patterns("*.pyc", "__pycache__"),
    )
    return fake_exe, mainmenu_dir


def _run_subprocess(python_exe, script_path, cwd):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    proc = subprocess.Popen(
        [python_exe, script_path],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    out, _ = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace")


def main():
    RESULTS = []

    def check(name, condition, detail=None):
        RESULTS.append((name, condition))
        print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))

    text = _read_and_verify_normalizer()
    check("source.frozen_normalizer_sha256_pinned", True)

    block = _extract_bootstrap_block(text)
    check("source.bootstrap_block_sha256_pinned", True)

    unrelated_cwd = tempfile.mkdtemp(prefix="pb_normalizer_bootstrap_cwd_")

    interpreters = [
        ("Python 3.10", "C:\\Users\\Eman\\AppData\\Local\\Programs\\Python\\Python310\\python.exe"),
        (
            "real Python 2.7.5",
            r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\sdktools\python\2.7\win32\python.exe",
        ),
    ]

    for label, python_exe in interpreters:
        print("\n=== Positive case: %s ===" % label)
        fake_root = tempfile.mkdtemp(prefix="pb_normalizer_bootstrap_")
        fake_exe, mainmenu_dir = _build_fake_layout(fake_root)

        script = RUNNER_TEMPLATE % {
            "fake_exe": fake_exe,
            "block_source": block,
            "expected_mainmenu_dir": mainmenu_dir,
            "expected_build_id": "package-boundary-corrected-2026-09-22",
            "expected_api_version": "1.0.0-b2a",
        }
        script_path = os.path.join(fake_root, "run_bootstrap_positive.py")
        with open(script_path, "w") as f:
            f.write(script)

        rc, out = _run_subprocess(python_exe, script_path, unrelated_cwd)
        print(out)
        check("%s: positive case exits 0" % label, rc == 0, rc)

        print("\n=== Negative case (stale RUNTIME_BUILD_ID): %s ===" % label)
        fake_root_neg = tempfile.mkdtemp(prefix="pb_normalizer_bootstrap_neg_")
        fake_exe_neg, mainmenu_dir_neg = _build_fake_layout(fake_root_neg)
        runtime_path = os.path.join(
            mainmenu_dir_neg, "sfm_master_authority_productionized", "runtime.py"
        )
        with open(runtime_path, "r") as f:
            runtime_src = f.read()
        old_build_id = "b2c-correction6-parsedeferred-floor-targeted-2026-09-18"
        new_build_id = "package-boundary-corrected-2026-09-22"
        stale_src = runtime_src.replace(
            'RUNTIME_BUILD_ID = "%s"' % new_build_id,
            'RUNTIME_BUILD_ID = "%s"' % old_build_id,
        )
        check(
            "%s: negative-case fixture actually mutated RUNTIME_BUILD_ID" % label,
            stale_src != runtime_src,
        )
        with open(runtime_path, "w") as f:
            f.write(stale_src)

        script_neg = RUNNER_TEMPLATE_NEGATIVE % {
            "fake_exe": fake_exe_neg,
            "block_source": block,
            "old_build_id": old_build_id,
            "new_build_id": new_build_id,
        }
        script_path_neg = os.path.join(fake_root_neg, "run_bootstrap_negative.py")
        with open(script_path_neg, "w") as f:
            f.write(script_neg)

        rc_neg, out_neg = _run_subprocess(python_exe, script_path_neg, unrelated_cwd)
        print(out_neg)
        check("%s: negative case exits 0 (its own assertions all passed)" % label, rc_neg == 0, rc_neg)

        shutil.rmtree(fake_root, ignore_errors=True)
        shutil.rmtree(fake_root_neg, ignore_errors=True)

    shutil.rmtree(unrelated_cwd, ignore_errors=True)

    print("\nOVERALL RESULT: %d/%d %s" % (
        sum(1 for _, c in RESULTS if c), len(RESULTS),
        "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
    ))
    if not all(c for _, c in RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
