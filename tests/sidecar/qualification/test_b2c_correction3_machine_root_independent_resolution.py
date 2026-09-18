# -*- coding: utf-8 -*-
"""Independent-audit targeted correction -- NARROW ISSUE E regression
probe: machine-root-independent bootstrap/fixture resolution.

Proves the candidate no longer depends on the original `E:\\SFM
Animation Group Master\\...` checkout path: copies `tools/`,
`candidate_b2c_correction3/`, and `candidate_b2c_correction3_normalizer/`
(preserving their RELATIVE layout under tests/sidecar/qualification/)
into a FRESH temporary root at an entirely different absolute path
(simulating a fresh checkout or an extracted archive root -- see the
independent-audit archive workflow this project already uses), then
runs the REAL Normalizer candidate's bootstrap and a REAL acquisition
FROM that copied location, confirming everything resolves correctly
relative to itself, never to the original machine path.
"""
import json
import os
import shutil
import sys
import tempfile

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
CORRECTION3_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction3")
CORRECTION3_NORMALIZER_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction3_normalizer")
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

# ===========================================================================
# Build a fresh, differently-rooted copy -- a completely different
# absolute path from E:\SFM Animation Group Master\..., with the SAME
# relative layout (tools/, tests/sidecar/qualification/candidate_b2c_
# correction3(_normalizer)/) a real fresh checkout or archive extraction
# would have.
# ===========================================================================
FRESH_ROOT = tempfile.mkdtemp(prefix="b2c_correction3_freshroot_")
check("setup.0 fresh root is NOT under the original repo path",
      not FRESH_ROOT.lower().startswith(REPO_ROOT.lower()), (FRESH_ROOT, REPO_ROOT))

fresh_tools = os.path.join(FRESH_ROOT, "tools")
fresh_qual_dir = os.path.join(FRESH_ROOT, "tests", "sidecar", "qualification")
os.makedirs(fresh_qual_dir)
shutil.copytree(TOOLS_DIR, fresh_tools, ignore=shutil.ignore_patterns("__pycache__"))
shutil.copytree(
    CORRECTION3_ROOT, os.path.join(fresh_qual_dir, "candidate_b2c_correction3"),
    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
)
shutil.copytree(
    CORRECTION3_NORMALIZER_ROOT, os.path.join(fresh_qual_dir, "candidate_b2c_correction3_normalizer"),
    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
)
check("setup.1 fresh copy contains the candidate authority package",
      os.path.isdir(os.path.join(fresh_qual_dir, "candidate_b2c_correction3", "sfm_master_authority")))
check("setup.2 fresh copy contains the Normalizer candidate file",
      os.path.isfile(os.path.join(
          fresh_qual_dir, "candidate_b2c_correction3_normalizer",
          "Rebuild_Control_Groups_Normalizer_B2CB_correction3_candidate.py")))

fresh_normalizer_path = os.path.join(
    fresh_qual_dir, "candidate_b2c_correction3_normalizer",
    "Rebuild_Control_Groups_Normalizer_B2CB_correction3_candidate.py",
)

# ===========================================================================
# Run the REAL bootstrap block FROM the copied file's location, with
# __file__ pointing at the COPY (never the original), confirming the
# resolved authority root is the COPIED candidate_b2c_correction3, not
# the original E:\SFM Animation Group Master\... path.
# ===========================================================================
with open(fresh_normalizer_path, "rb") as f:
    _cand_bytes = f.read()
try:
    unicode  # noqa: F821
    _PY2 = True
except NameError:
    _PY2 = False
_cand_lines = _cand_bytes.splitlines() if _PY2 else _cand_bytes.decode("utf-8").splitlines()


def _extract(a, b):
    return "\n".join(_cand_lines[a - 1: b]) + "\n"


BOOTSTRAP_SRC = "import sys\nimport os\n" + _extract(152, 226)
FUNC_SRC = _extract(1517, 1617)  # acquire_master_index_via_qualified_authority


class _FakeQThread(object):
    @staticmethod
    def currentThread():
        return "main"


class _FakeQCoreApplication(object):
    @staticmethod
    def instance():
        return None


class _FakeQtCore(object):
    QThread = _FakeQThread
    QCoreApplication = _FakeQCoreApplication


for name in list(sys.modules.keys()):
    if name == "sfm_master_authority" or name.startswith("sfm_master_authority."):
        del sys.modules[name]

ns = {"QtCore": _FakeQtCore, "__file__": fresh_normalizer_path}
try:
    exec(BOOTSTRAP_SRC, ns)
    bootstrap_outcome = "succeeded"
except Exception as exc:
    bootstrap_outcome = "raised %s: %s" % (type(exc).__name__, exc)

check("bootstrap.0 the REAL bootstrap, run from the FRESH (differently-rooted) copy, succeeds",
      bootstrap_outcome == "succeeded", bootstrap_outcome)

if bootstrap_outcome == "succeeded":
    actual_origin = ns["_b2c_authority_runtime"].get_actual_origin_dir()
    check("bootstrap.1 the resolved authority origin is under the FRESH root (not the original "
          "E:\\SFM Animation Group Master\\... path)",
          actual_origin.lower().startswith(FRESH_ROOT.lower())
          and not actual_origin.lower().startswith(REPO_ROOT.lower()),
          actual_origin)
    check("bootstrap.2 the expected authority root constant itself resolved under the fresh root",
          ns["_B2C_QUALIFIED_AUTHORITY_ROOT"].lower().startswith(FRESH_ROOT.lower()),
          ns["_B2C_QUALIFIED_AUTHORITY_ROOT"])
    check("bootstrap.3 the tools root constant itself resolved under the fresh root",
          ns["_B2C_SIDECAR_TOOLS_ROOT"].lower().startswith(FRESH_ROOT.lower()),
          ns["_B2C_SIDECAR_TOOLS_ROOT"])

    exec(FUNC_SRC, ns)
    check("bootstrap.4 acquire_master_index_via_qualified_authority extracted OK",
          "acquire_master_index_via_qualified_authority" in ns)

    # ===================================================================
    # Now prove a REAL acquisition succeeds using fixtures ALSO copied
    # to the fresh root -- deterministic fixture roots must resolve
    # correctly from the new location too.
    # ===================================================================
    fresh_fixtures_ab = os.path.join(
        fresh_qual_dir, "candidate_b2c_correction3", "fixtures_ab",
    )
    if not os.path.isdir(fresh_fixtures_ab):
        # fixtures_ab is built by a separate script under the ORIGINAL
        # tree; copy it into the fresh root the same way a real archive/
        # checkout would carry its own fixtures along.
        original_fixtures_ab = os.path.join(CORRECTION3_ROOT, "fixtures_ab")
        shutil.copytree(original_fixtures_ab, fresh_fixtures_ab)
    with open(os.path.join(fresh_fixtures_ab, "manifest.json")) as f:
        fresh_manifest = json.load(f)
    # Manifest paths were recorded relative to the ORIGINAL tree at build
    # time -- rewrite them here to point at the FRESH copy, exactly as a
    # real consumer of a relocated archive would need to (re)point its
    # own fixture roots after extraction, never assuming the recorded
    # absolute path is still valid post-move.
    fresh_master_a = os.path.join(fresh_fixtures_ab, "generation_a_master.txt")
    fresh_shipped_root = os.path.join(fresh_fixtures_ab, "shipped_both")
    check("fixtures.0 fresh-root Master A fixture exists", os.path.isfile(fresh_master_a))
    check("fixtures.1 fresh-root shared shipped root exists", os.path.isdir(fresh_shipped_root))

    GEN_A = fresh_manifest["generation_a"]["master_sha256"]
    try:
        payload, lease = ns["acquire_master_index_via_qualified_authority"](
            fresh_master_a, set(["left", "right"]), shipped_root=fresh_shipped_root,
            expected_generation=GEN_A,
        )
        acquisition_outcome = "succeeded"
    except Exception as exc:
        acquisition_outcome = "raised %s: %s" % (type(exc).__name__, exc)
        payload, lease = None, None
    check("acquisition.0 a REAL acquisition, entirely from the fresh (differently-rooted) copy, "
          "using fixtures ALSO from the fresh copy, succeeds",
          acquisition_outcome == "succeeded", acquisition_outcome)
    if lease is not None:
        ns["_b2c_authority_runtime"].get_broker().release_view_lease(lease)

shutil.rmtree(FRESH_ROOT, ignore_errors=True)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
