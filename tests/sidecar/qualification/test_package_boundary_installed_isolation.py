# -*- coding: utf-8 -*-
"""Package-Boundary Correction, Section 8: installed-package isolation
proof.

Copies ONLY the real package files (`sfm_master_authority_
productionized/`, `sfm_master_sidecar/`, `sfm_master_core.py` -- no
qualification/candidate scaffolding, no test helpers) into a fresh temp
"installed" directory, publishes a synthetic Master into a SEPARATE
temp "published" directory via the real public compiler/publisher, then
runs the actual acquisition proof as a SEPARATE, REAL Python 2.7.5
SUBPROCESS whose:

  - `sys.path` is built from scratch (stdlib + ONLY the isolated
    installed-package directory -- the repository root, every
    `candidate_*` directory, and `tools/` are never added);
  - working directory is an unrelated temp directory (never the
    repository, never the installed/published directories themselves);
  - environment has `PYTHONPATH` cleared (no leakage from this
    orchestrating process's own environment).

This proves: canonical package/import owner resolution, duplicate-
ownership protection (`runtime.py`'s `is_canonical()`), and real broker
acquisition from the canonical installed publication all work with ZERO
repository-path or `__file__`-on-the-entry-script dependency -- matching
the real SFM MAINMENU constraint (`__file__` not assumed to exist,
`docs/qualification/CPM_ASTRA_AUTHORITY_CONSUMER_DOSSIER.md`).

Honest scope limit (per the governing prompt's own instruction: "If this
cannot be honestly proven without live SFM, separate what is proven
offline from the one small check that must move to real-SFM
qualification"): this proves the package/import/acquisition boundary is
independent of repository paths and CWD, using a real, separate Python
2.7.5 process. It does NOT prove the exact SFM MAINMENU exec/import
mechanics themselves (e.g. `execfile()` semantics, Qt main-thread
identity, or `sys.executable` actually pointing at a real `sfm.exe`) --
those require real SFM and are explicitly deferred to real-SFM
qualification, not fabricated here.

Never launches SFM. Never modifies the frozen production Normalizer or
the canonical Master.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.abspath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir, "tools"))
CORRECTION6_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction6")
PY27 = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\sdktools\python\2.7\win32\python.exe"
)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter (orchestrator): %s" % sys.version)

ISOLATED_ROOT = tempfile.mkdtemp(prefix="sfm_pkg_isolation_")
INSTALLED_PACKAGE_DIR = os.path.join(ISOLATED_ROOT, "installed_package")
PUBLISHED_DIR = os.path.join(ISOLATED_ROOT, "published")
UNRELATED_CWD = os.path.join(ISOLATED_ROOT, "unrelated_cwd")
INNER_SCRIPT_PATH = os.path.join(ISOLATED_ROOT, "_inner_isolated_check.py")
MASTER_TXT_PATH = os.path.join(ISOLATED_ROOT, "isolation_master.txt")

os.makedirs(INSTALLED_PACKAGE_DIR)
os.makedirs(PUBLISHED_DIR)
os.makedirs(UNRELATED_CWD)

# --- 1. Copy ONLY the real package files -- no qualification/candidate
#        scaffolding, no repo test helpers. ---
shutil.copytree(
    os.path.join(CORRECTION6_ROOT, "sfm_master_authority_productionized"),
    os.path.join(INSTALLED_PACKAGE_DIR, "sfm_master_authority_productionized"),
    ignore=shutil.ignore_patterns("*.pyc", "__pycache__"),
)
shutil.copytree(
    os.path.join(TOOLS_DIR, "sfm_master_sidecar"),
    os.path.join(INSTALLED_PACKAGE_DIR, "sfm_master_sidecar"),
    ignore=shutil.ignore_patterns("*.pyc", "__pycache__"),
)
shutil.copy2(os.path.join(TOOLS_DIR, "sfm_master_core.py"), INSTALLED_PACKAGE_DIR)
check("setup.package_files_copied the isolated installed_package directory contains exactly the "
      "real package files (no qualification scaffolding)",
      sorted(os.listdir(INSTALLED_PACKAGE_DIR)) ==
      ["sfm_master_authority_productionized", "sfm_master_core.py", "sfm_master_sidecar"])

# --- 2. Publish a synthetic Master via the real public compiler/
#        publisher into a directory SEPARATE from the installed package
#        code (a real install would keep code and published data apart
#        -- see bootstrap.py's own two distinct constants). ---
MASTER_TXT_BODY = (
    u'"groupFile"\n{\n"RigArms"\n{\n\t"control"\t\t"isolation_control"\n}\n}\n'
)
with open(MASTER_TXT_PATH, "wb") as f:
    f.write(MASTER_TXT_BODY.encode("utf-8"))

sys.path.insert(0, TOOLS_DIR)
from sfm_master_sidecar import publisher  # noqa: E402

publish_result = publisher.publish(MASTER_TXT_PATH, PUBLISHED_DIR)
check("setup.published_into_separate_dir the synthetic Master was published (via the real "
      "public compiler/publisher) into a directory separate from the installed package code",
      os.path.isfile(str(publish_result.generation_path)))
real_master_sha = hashlib.sha256(MASTER_TXT_BODY.encode("utf-8")).hexdigest()

# --- 3. Write the inner isolated-acquisition script. Built from scratch
#        with NO reference to this repository's own directory layout --
#        only stdlib imports plus the two isolated paths passed in via
#        argv. ---
_INNER_SCRIPT = u'''# -*- coding: utf-8 -*-
import os
import sys

installed_package_dir = sys.argv[1]
published_dir = sys.argv[2]
expected_master_sha = sys.argv[3]
master_txt_path = sys.argv[4]

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


check("isolated.cwd_is_unrelated the current working directory is the deliberately unrelated "
      "temp directory, never the repository or the installed/published directories",
      os.getcwd().rstrip(os.sep).endswith("unrelated_cwd"), os.getcwd())
check("isolated.pythonpath_env_cleared PYTHONPATH is not set in this process environment",
      "PYTHONPATH" not in os.environ, os.environ.get("PYTHONPATH"))
check("isolated.sys_path_has_no_repo_or_candidate_dirs sys.path (before this script inserts "
      "anything) contains no path mentioning this repository or any qualification/candidate "
      "directory", not any(("SFM Animation Group Master" in p or "candidate_" in p) for p in sys.path),
      sys.path)

sys.path.insert(0, installed_package_dir)

import sfm_master_authority_productionized.runtime as rt  # noqa: E402
check("isolated.runtime_imports_successfully importing sfm_master_authority_productionized.runtime "
      "succeeds from the isolated installed_package directory alone", True)
check("isolated.runtime_is_canonical the freshly-imported runtime module reports itself as the "
      "canonical owner (duplicate-ownership protection intact)", rt.is_canonical())

broker = rt.get_broker(is_main_thread_fn=lambda: True)
check("isolated.broker_ready get_broker() returns a real, READY broker", rt.get_state() == "READY")
broker2 = rt.get_broker()
check("isolated.get_broker_idempotent a second get_broker() call returns the SAME broker object "
      "(no silent second construction)", broker is broker2)

from sfm_master_authority_productionized import normalizer_compat_adapter as adapter  # noqa: E402

wanted = frozenset([b"isolation_control"])
request_specs = {"normalizer": (wanted, adapter.build_targeted_master_compatible_projection(wanted))}
detached = broker.acquire_or_reuse_views(
    master_txt_path, request_specs, shipped_root=published_dir, expected_generation=expected_master_sha,
)
check("isolated.acquisition_succeeds_from_installed_publication acquiring authority from the "
      "isolated installed publication succeeds (shipped_root points ONLY at the isolated "
      "published_dir, never a repository fixture path)", "normalizer" in detached)
view = detached["normalizer"]
check("isolated.no_fallback_to_repo_fixtures the acquired view's source generation matches the "
      "ISOLATION-SPECIFIC Master content, not any repository fixture's Master content",
      view.semantic_generation.master_sha256 == expected_master_sha)
entries = view.payload["folded"].get(b"isolation_control", [])
check("isolated.semantic_content_is_the_isolated_masters the resolved destination comes from the "
      "isolated Master TXT (RigArms), proving no repo/candidate fixture was silently substituted",
      len(entries) > 0 and entries[0]["destination"] in (u"RigArms", "RigArms"), entries)

lease = broker.lease_view(view)
broker.release_view_lease(lease)
check("isolated.lease_lifecycle_clean lease acquired and released with no error, zero open "
      "providers afterward", broker.provider_counters()["current_open_provider_count"] == 0)

print("\\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(condition for _, condition in RESULTS):
    sys.exit(1)
'''

with open(INNER_SCRIPT_PATH, "wb") as f:
    f.write(_INNER_SCRIPT.encode("utf-8"))

# --- 4. Run the inner script as a SEPARATE, real Python 2.7.5 process,
#        with a scrubbed environment and an unrelated CWD. ---
env = dict(os.environ)
env.pop("PYTHONPATH", None)
proc = subprocess.Popen(
    [PY27, INNER_SCRIPT_PATH, INSTALLED_PACKAGE_DIR, PUBLISHED_DIR, real_master_sha, MASTER_TXT_PATH],
    cwd=UNRELATED_CWD, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
)
out, _ = proc.communicate()
out_text = out.decode("utf-8", "replace")
print("\n--- isolated subprocess output ---")
print(out_text)
print("--- end isolated subprocess output ---\n")

check("orchestrator.isolated_subprocess_exit_zero the isolated Python 2.7.5 subprocess exited 0 "
      "(every inner check passed)", proc.returncode == 0, proc.returncode)
for line in out_text.splitlines():
    if line.startswith("[PASS]") or line.startswith("[FAIL]"):
        RESULTS.append((line, line.startswith("[PASS]")))

shutil.rmtree(ISOLATED_ROOT, ignore_errors=True)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(condition for _, condition in RESULTS):
    sys.exit(1)
