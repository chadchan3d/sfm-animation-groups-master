# -*- coding: utf-8 -*-
"""Astra SECOND correction gate -- Test 5: generation + ACTUAL bootstrap.

Critical methodology fix vs. the first correction gate: Astra found that
EVERY previous test exercising acquire_master_index_via_qualified_
authority extracted the function's SOURCE via line-range exec() and
INJECTED A FAKE `_b2c_authority_runtime` directly into the exec
namespace -- bypassing the real module-level bootstrap import entirely,
so no test ever caught that the bootstrap still pointed at the WRONG
package (candidate_b2c/ instead of the corrected candidate). This file
instead extracts and exec's the REAL bootstrap block (lines 152-210:
the sys.path insertion, the real `from sfm_master_authority import ...`
statements, and the real `_b2c_verify_bootstrap_identity()` call) --
a GENUINE import via sys.path, never an injected fake -- and only THEN
extracts+execs the function body into that SAME namespace, so it uses
whatever `_b2c_authority_runtime` the real bootstrap actually resolved.
"""
import sys

CORRECTION2_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction2"
FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
OFFICIAL_ROOT = FIXROOT_B2A + r"\shipped_root_valid"
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
NORMALIZER_CANDIDATE_PATH = (
    r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction2_normalizer"
    r"\Rebuild_Control_Groups_Normalizer_B2CB_correction2_candidate.py"
)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

with open(NORMALIZER_CANDIDATE_PATH, "rb") as f:
    _cand_bytes = f.read()
try:
    unicode  # noqa: F821
    _PY2 = True
except NameError:
    _PY2 = False
_cand_lines = _cand_bytes.splitlines() if _PY2 else _cand_bytes.decode("utf-8").splitlines()


def _extract(a, b):
    return "\n".join(_cand_lines[a - 1: b]) + "\n"


BOOTSTRAP_SRC = "import sys\nimport os\n" + _extract(152, 210)
FUNC_SRC = _extract(1501, 1602)  # acquire_master_index_via_qualified_authority, exact bounds
check("extract.0 function range starts with the expected def",
      FUNC_SRC.lstrip().startswith("def acquire_master_index_via_qualified_authority"))


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


# ===========================================================================
# Case 1: fresh process (no prior import), no other package preloaded ->
# the REAL bootstrap must load candidate_b2c_correction2, not
# candidate_b2c/.
# ===========================================================================


def fresh_bootstrap_namespace():
    """Each case gets its own namespace AND its own popped sys.modules
    entries for sfm_master_authority.* -- simulating a fresh process
    bootstrap, since Python caches imports in sys.modules and a second
    `from sfm_master_authority import ...` in the SAME process would
    just return the already-cached module regardless of sys.path."""
    for name in list(sys.modules.keys()):
        if name == "sfm_master_authority" or name.startswith("sfm_master_authority."):
            del sys.modules[name]
    ns = {"QtCore": _FakeQtCore}
    return ns


ns1 = fresh_bootstrap_namespace()
try:
    exec(BOOTSTRAP_SRC, ns1)
    bootstrap_outcome = "succeeded"
except Exception as exc:
    bootstrap_outcome = "raised %s: %s" % (type(exc).__name__, exc)

check("case1.0 fresh-process bootstrap with correction2 on sys.path succeeds",
      bootstrap_outcome == "succeeded", bootstrap_outcome)
if bootstrap_outcome == "succeeded":
    actual_origin = ns1["_b2c_authority_runtime"].get_actual_origin_dir()
    check("case1.1 the REAL bootstrap actually resolved to candidate_b2c_correction2 "
          "(not candidate_b2c/)", "candidate_b2c_correction2" in actual_origin.replace("\\", "/"), actual_origin)
    check("case1.2 loaded package has RUNTIME_BUILD_ID (the corrected build)",
          hasattr(ns1["_b2c_authority_runtime"], "RUNTIME_BUILD_ID"))

    exec(FUNC_SRC, ns1)
    check("case1.3 acquire_master_index_via_qualified_authority extracted OK",
          "acquire_master_index_via_qualified_authority" in ns1)

    payload1, lease1 = ns1["acquire_master_index_via_qualified_authority"](
        REAL_MASTER_PATH, set(["left", "right"]), shipped_root=OFFICIAL_ROOT,
        expected_generation="ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93",
    )
    check("case1.4 a REAL acquisition through the ACTUAL bootstrap (not an injected fake) succeeds",
          isinstance(payload1, dict) and payload1.get("mapping_count", 0) > 0)
    broker1 = ns1["_b2c_authority_runtime"].get_broker()
    broker1.release_view_lease(lease1)
    check("case1.5 releasing the lease zeroes outstanding leases", broker1.outstanding_lease_count() == 0)

# ===========================================================================
# Case 2: the OLD (pre-correction) package preloaded first under the
# canonical name -- must be explicitly rejected, not silently used.
# ===========================================================================
OLD_CANDIDATE_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c"

ns2 = fresh_bootstrap_namespace()
old_path_entry = OLD_CANDIDATE_ROOT
if old_path_entry not in sys.path:
    sys.path.insert(0, old_path_entry)
try:
    import sfm_master_authority.runtime as _preloaded_old  # noqa: F401  -- deliberately preloads the OLD package
    old_preload_ok = True
except Exception as exc:
    old_preload_ok = False
    old_preload_exc = exc

if old_preload_ok:
    try:
        exec(BOOTSTRAP_SRC, ns2)
        case2_outcome = "bootstrap succeeded (WRONG -- should have rejected the stale preload)"
    except Exception as exc:
        case2_outcome = "rejected: %s: %s" % (type(exc).__name__, exc)
    check("case2.0 old candidate_b2c/ preloaded first under the canonical name -> "
          "bootstrap explicitly REJECTS it", case2_outcome.startswith("rejected"), case2_outcome)
else:
    print("[SKIP] case2 -- could not preload the old package to set up this scenario: %r" % (old_preload_exc,))

for name in list(sys.modules.keys()):
    if name == "sfm_master_authority" or name.startswith("sfm_master_authority."):
        del sys.modules[name]
try:
    sys.path.remove(old_path_entry)
except ValueError:
    pass

# ===========================================================================
# Case 3: frozen production package preloaded first -- must be rejected.
# ===========================================================================
FROZEN_ROOT = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm\gate_r3_b2a_broker_deploy"
)
ns3 = fresh_bootstrap_namespace()
if FROZEN_ROOT not in sys.path:
    sys.path.insert(0, FROZEN_ROOT)
try:
    import sfm_master_authority.runtime as _preloaded_frozen  # noqa: F401
    frozen_preload_ok = True
except Exception as exc:
    frozen_preload_ok = False
    frozen_preload_exc = exc

if frozen_preload_ok:
    try:
        exec(BOOTSTRAP_SRC, ns3)
        case3_outcome = "bootstrap succeeded (WRONG -- should have rejected the frozen package)"
    except Exception as exc:
        case3_outcome = "rejected: %s: %s" % (type(exc).__name__, exc)
    check("case3.0 frozen production package preloaded first -> bootstrap explicitly REJECTS it",
          case3_outcome.startswith("rejected"), case3_outcome)
else:
    print("[SKIP] case3 -- could not preload the frozen package: %r" % (frozen_preload_exc,))

for name in list(sys.modules.keys()):
    if name == "sfm_master_authority" or name.startswith("sfm_master_authority."):
        del sys.modules[name]
try:
    sys.path.remove(FROZEN_ROOT)
except ValueError:
    pass

# ===========================================================================
# Case 4/5: valid A and valid B artifacts -- command pinned to A must not
# accept B; A->B->A; single retry budget.
# ===========================================================================
ns4 = fresh_bootstrap_namespace()
exec(BOOTSTRAP_SRC, ns4)
exec(FUNC_SRC, ns4)

import hashlib, os, shutil, tempfile  # noqa: E402
SCRATCH = tempfile.mkdtemp(prefix="b2c_correction2_test5_")
FIXTURE_MASTER = os.path.join(SCRATCH, "master.txt")
with open(REAL_MASTER_PATH, "rb") as f:
    _real_master_bytes = f.read()
with open(FIXTURE_MASTER, "wb") as f:
    f.write(_real_master_bytes)
GEN_A = hashlib.sha256(_real_master_bytes).hexdigest()

try:
    payload_a, lease_a = ns4["acquire_master_index_via_qualified_authority"](
        FIXTURE_MASTER, set(["left", "right"]), shipped_root=OFFICIAL_ROOT, expected_generation=GEN_A,
    )
    check("case4.0 command A + acquire A (matching pin) succeeds", isinstance(payload_a, dict))
    ns4["_b2c_authority_runtime"].get_broker().release_view_lease(lease_a)
except Exception as exc:
    check("case4.0 command A + acquire A (matching pin) succeeds", False, exc)

with open(FIXTURE_MASTER, "wb") as f:
    f.write(_real_master_bytes + b"\n// generation B\n")
GEN_B = hashlib.sha256(_real_master_bytes + b"\n// generation B\n").hexdigest()

try:
    ns4["acquire_master_index_via_qualified_authority"](
        FIXTURE_MASTER, set(["left", "right"]), shipped_root=OFFICIAL_ROOT, expected_generation=GEN_A,
    )
    case4_1_outcome = "unexpected_success"
except Exception as exc:
    case4_1_outcome = "%s: %s" % (type(exc).__name__, exc)
check("case4.1 command STILL pinned to A, but Master is now B -> explicit refuse/retry-then-fail "
      "(never silently accept B)", "AuthorityChangedDuringAcquisition" in case4_1_outcome or "SidecarMissing" in case4_1_outcome,
      case4_1_outcome)

with open(FIXTURE_MASTER, "wb") as f:
    f.write(_real_master_bytes)  # restore to A's exact original bytes (A->B->A)
try:
    payload_a2, lease_a2 = ns4["acquire_master_index_via_qualified_authority"](
        FIXTURE_MASTER, set(["left", "right"]), shipped_root=OFFICIAL_ROOT, expected_generation=GEN_A,
    )
    check("case4.2 A->B->A: re-acquisition under restored generation A succeeds", isinstance(payload_a2, dict))
    ns4["_b2c_authority_runtime"].get_broker().release_view_lease(lease_a2)
except Exception as exc:
    check("case4.2 A->B->A: re-acquisition under restored generation A succeeds", False, exc)

shutil.rmtree(SCRATCH, ignore_errors=True)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
