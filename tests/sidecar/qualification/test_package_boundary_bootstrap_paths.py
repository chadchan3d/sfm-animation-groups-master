# -*- coding: utf-8 -*-
"""Package-Boundary Targeted Correction (2026-09-22), Section 6: tiny,
pure unit test for `bootstrap.py`'s path-calculation functions.

Scope is deliberately narrow -- this proves the path ARITHMETIC only
(`game_root()`/`installed_authority_root()`/`bootstrap_import_path()`/
`ownership_report()` given a synthetic root), never a real MAINMENU
entry seam, a real `sys.executable`, or any real SFM process. See
`bootstrap.py`'s own docstring, "Exact scope", for what IS and is NOT
proven by this package's tests as a whole.

Never launches SFM. Read-only with respect to the frozen production
file and the canonical Master (neither is referenced by this file).
"""
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CORRECTION6_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction6")
for _p in (os.path.abspath(CORRECTION6_ROOT),):
    if _p not in sys.path:
        sys.path.insert(0, _p)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

from sfm_master_authority_productionized import bootstrap  # noqa: E402

FAKE_ROOT = os.path.join("Z:" + os.sep, "fake_sfm_install", "game")

# --- installed_authority_root(root=...) is a deterministic join under
#     the one documented relative path, never touching sys.executable
#     when an explicit root is given. ---
expected_authority = os.path.join(FAKE_ROOT, "usermod", "cfg", "sfm_shared_authority")
check("installed_authority_root.matches_documented_relative_path",
      bootstrap.installed_authority_root(root=FAKE_ROOT) == expected_authority,
      bootstrap.installed_authority_root(root=FAKE_ROOT))

# --- bootstrap_import_path() takes no root override in the current
#     API -- confirm that directly rather than assuming a signature it
#     doesn't have (package CODE location vs PUBLISHED SIDECAR location
#     are distinct directories, but only installed_authority_root()
#     accepts a test-only override). ---
check("bootstrap_import_path.takes_no_root_argument",
      "root" not in bootstrap.bootstrap_import_path.__code__.co_varnames[
          :bootstrap.bootstrap_import_path.__code__.co_argcount])

# --- game_root() and installed_authority_root()/bootstrap_import_path()
#     (real, sys.executable-derived) never raise, and are mutually
#     consistent: the authority root and the import path are both
#     computed relative to the SAME game_root(). ---
try:
    real_game_root = bootstrap.game_root()
    real_authority_root = bootstrap.installed_authority_root()
    real_import_path = bootstrap.bootstrap_import_path()
    check("real_paths.no_exception", True)
    check("real_authority_root.starts_with_game_root",
          real_authority_root.startswith(real_game_root), (real_authority_root, real_game_root))
    check("real_import_path.starts_with_game_root",
          real_import_path.startswith(real_game_root), (real_import_path, real_game_root))
    check("real_authority_root.ne.real_import_path",
          real_authority_root != real_import_path,
          "published-sidecar location and package-code location must remain distinct")
except Exception as exc:
    check("real_paths.no_exception", False, exc)

# --- ownership_report() never raises, and reports a dict with the
#     documented keys, regardless of whether the package happens to be
#     imported under its canonical name in this process. ---
try:
    report = bootstrap.ownership_report()
    expected_keys = {
        "game_root", "installed_authority_root", "bootstrap_import_path",
        "runtime_module_loaded", "runtime_is_canonical",
    }
    check("ownership_report.no_exception", True)
    check("ownership_report.has_documented_keys", set(report.keys()) == expected_keys, sorted(report.keys()))
except Exception as exc:
    check("ownership_report.no_exception", False, exc)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(condition for _, condition in RESULTS):
    sys.exit(1)
