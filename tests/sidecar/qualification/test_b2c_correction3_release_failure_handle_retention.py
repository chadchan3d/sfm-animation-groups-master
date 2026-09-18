# -*- coding: utf-8 -*-
"""Independent-audit targeted correction -- BLOCKER C regression probe:
release-failure-handle-retention.

Exercises the ACTUAL candidate command's own teardown methods
(`_b2c_release_master_index_lease`, `final_report`'s lease-ownership
prefix, `release_run_lock`), extracted verbatim by exact line range and
bound as REAL methods on a minimal fake command object -- never an
extracted acquisition function paired with MANUAL out-of-band lease
cleanup (the independent audit's exact rejected pattern: "the existing
test then manually repairs the leaked lease from outside the real
command path -- that is not acceptable"). Retry/reconciliation here
means calling the candidate's OWN `_b2c_release_master_index_lease()`
again -- never anything invented by this test.

Astra Narrow Issue E: paths derived from `__file__`, never hardcoded.
"""
import os
import sys
import textwrap

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
CORRECTION3_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction3")
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
FIXROOT_AB = os.path.join(CORRECTION3_ROOT, "fixtures_ab")

for p in (CORRECTION3_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

NORMALIZER_CANDIDATE_PATH = os.path.join(
    _THIS_DIR, "candidate_b2c_correction3_normalizer",
    "Rebuild_Control_Groups_Normalizer_B2CB_correction3_candidate.py",
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


# Exact line ranges (re-verified via grep against THIS file before
# writing this test; re-verify against the actual file, not memory, if
# this candidate is ever edited again).
RELEASE_HELPER_SRC = textwrap.dedent(_extract(12700, 12745))
FINAL_REPORT_PREFIX_SRC = textwrap.dedent(_extract(12746, 12772))
RELEASE_RUN_LOCK_SRC = textwrap.dedent(_extract(9218, 9229))

check("extract.0 release-helper range starts with the expected def",
      RELEASE_HELPER_SRC.lstrip().startswith("def _b2c_release_master_index_lease("))
check("extract.1 final_report prefix range starts with the expected def",
      FINAL_REPORT_PREFIX_SRC.lstrip().startswith("def final_report("))
check("extract.2 final_report prefix ends at the lease-release call (deliberately "
      "truncated before the unrelated logging/reporting body)",
      FINAL_REPORT_PREFIX_SRC.strip().splitlines()[-1].strip() == "self._b2c_release_master_index_lease()")
check("extract.3 release_run_lock range starts with the expected def",
      RELEASE_RUN_LOCK_SRC.lstrip().startswith("def release_run_lock("))

BOOTSTRAP_SRC = "import sys\nimport os\n" + _extract(152, 226)


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


def fresh_bootstrap_namespace():
    for name in list(sys.modules.keys()):
        if name == "sfm_master_authority" or name.startswith("sfm_master_authority."):
            del sys.modules[name]
    return {"QtCore": _FakeQtCore}


ns = fresh_bootstrap_namespace()
ns["__file__"] = NORMALIZER_CANDIDATE_PATH  # the bootstrap resolves its sibling root via __file__
exec(BOOTSTRAP_SRC, ns)
exec(RELEASE_HELPER_SRC, ns)
exec(FINAL_REPORT_PREFIX_SRC, ns)
exec(RELEASE_RUN_LOCK_SRC, ns)
check("extract.4 all three real methods extracted OK",
      all(name in ns for name in ("_b2c_release_master_index_lease", "final_report", "release_run_lock")))
_runtime = ns["_b2c_authority_runtime"]
_broker = _runtime.get_broker()


class _FakeCommand(object):
    """A minimal stand-in for RebuildControlGroupsProductionRun -- ONLY
    the attributes the extracted REAL methods actually touch. The
    methods themselves are the REAL, unmodified candidate methods bound
    here as genuine instance methods (not re-implemented)."""
    _b2c_release_master_index_lease = ns["_b2c_release_master_index_lease"]
    final_report = ns["final_report"]
    release_run_lock = ns["release_run_lock"]

    def __init__(self, master_index, lease):
        self.finished = False
        self.master_index = master_index
        self._master_index_lease = lease
        self.master_index_cleanup_incomplete = False
        self.log_calls = []
        self.set_parent_calls = []
        self.delete_later_calls = 0

    def log(self, text):
        self.log_calls.append(text)

    def setParent(self, parent):
        self.set_parent_calls.append(parent)

    def deleteLater(self):
        self.delete_later_calls += 1


import hashlib  # noqa: E402
REAL_MASTER_PATH = os.path.join(FIXROOT_AB, "generation_a_master.txt")
if not os.path.isfile(REAL_MASTER_PATH):
    # Fixtures not yet built for this environment -- build them now
    # (idempotent, deterministic, Python 3 only).
    import subprocess
    subprocess.check_call([sys.executable, os.path.join(_THIS_DIR, "build_test_ab_fixtures_correction3.py")])

from sfm_master_authority_productionized import normalizer_compat_adapter as adapter  # noqa: E402


def acquire_real_lease():
    wanted = frozenset([b"left", b"right"])
    detached = _broker.acquire_or_reuse_views(
        REAL_MASTER_PATH, {"normalizer": (wanted, adapter.build_targeted_master_compatible_projection(wanted))},
        shipped_root=os.path.join(FIXROOT_AB, "shipped_both"),
    )
    lease = _broker.lease_view(detached["normalizer"])
    return detached["normalizer"].payload, lease


# --- Case 1: normal completion ---
payload1, lease1 = acquire_real_lease()
before_outstanding1 = _broker.outstanding_lease_count()
cmd1 = _FakeCommand(payload1, lease1)
cmd1.final_report(True)
check("case1.0 normal completion: finished becomes True", cmd1.finished is True)
check("case1.1 normal completion: master_index cleared", cmd1.master_index is None)
check("case1.2 normal completion: lease handle cleared on SUCCESS", cmd1._master_index_lease is None)
check("case1.3 normal completion: cleanup_incomplete stays False", cmd1.master_index_cleanup_incomplete is False)
check("case1.4 normal completion: real outstanding_lease_count dropped by exactly 1",
      _broker.outstanding_lease_count() == before_outstanding1 - 1)

# --- Case 2: cancellation (success=False, same lease-ownership path) ---
payload2, lease2 = acquire_real_lease()
before_outstanding2 = _broker.outstanding_lease_count()
cmd2 = _FakeCommand(payload2, lease2)
cmd2.final_report(False)
check("case2.0 cancellation path: lease handle cleared on success",
      cmd2._master_index_lease is None and cmd2.master_index_cleanup_incomplete is False)
check("case2.1 cancellation path: real lease count dropped by exactly 1",
      _broker.outstanding_lease_count() == before_outstanding2 - 1)

# --- Case 3: command failure after acquisition (same path again --
# final_report's lease-ownership prefix does not branch on `success`,
# by the real method's own design). ---
payload3, lease3 = acquire_real_lease()
cmd3 = _FakeCommand(payload3, lease3)
cmd3.final_report(False)
check("case3.0 command-failure-after-acquisition path: lease released and cleared",
      cmd3._master_index_lease is None)

# --- Case 4: release failure -- the handle must be RETAINED, never
# discarded, and cleanup must be marked incomplete. ---
payload4, lease4 = acquire_real_lease()
cmd4 = _FakeCommand(payload4, lease4)
_orig_release = _broker.release_view_lease


def _raising_release(_lease):
    raise RuntimeError("synthetic release failure")


_broker.release_view_lease = _raising_release
cmd4.final_report(True)
_broker.release_view_lease = _orig_release

check("case4.0 release failure: finished still becomes True (main teardown still ran)", cmd4.finished is True)
check("case4.1 release failure: master_index is STILL cleared (last-use-then-drop, independent "
      "of release outcome)", cmd4.master_index is None)
check("case4.2 release failure: lease handle is RETAINED, not discarded",
      cmd4._master_index_lease is lease4, cmd4._master_index_lease)
check("case4.3 release failure: cleanup marked incomplete", cmd4.master_index_cleanup_incomplete is True)
check("case4.4 release failure: logged, never silently swallowed", len(cmd4.log_calls) == 1, cmd4.log_calls)
check("case4.5 release failure: the broker STILL considers this lease live "
      "(no untracked leak, no double-release confusion)",
      _broker.outstanding_lease_count() > 0)

# --- Case 5: retry/reconciliation after release failure -- using the
# candidate's OWN _b2c_release_master_index_lease() again, NEVER a
# manual out-of-band repair (the independent audit's explicitly
# rejected pattern). ---
before_outstanding5 = _broker.outstanding_lease_count()
cmd4._b2c_release_master_index_lease()  # retry, using the SAME retained handle
check("case5.0 retry via the candidate's OWN method succeeds this time",
      cmd4._master_index_lease is None)
check("case5.1 retry clears cleanup_incomplete", cmd4.master_index_cleanup_incomplete is False)
check("case5.2 retry actually released the real lease (broker count dropped by 1)",
      _broker.outstanding_lease_count() == before_outstanding5 - 1)

# Retry-on-an-already-clean handle must be a safe no-op (never a
# double-release, never an error) -- proves the retry path itself is
# idempotent, not merely "happens to work once".
cmd4._b2c_release_master_index_lease()
check("case5.3 a further retry call after success is a safe no-op",
      cmd4._master_index_lease is None and cmd4.master_index_cleanup_incomplete is False)

# --- Case 6: deferred QObject deletion / final cleanup -- reachable
# regardless of lease-release outcome (release_run_lock lives in
# final_report's own unconditional `finally` clause, downstream of the
# lease-release call this test already exercised above). ---
payload6, lease6 = acquire_real_lease()
cmd6 = _FakeCommand(payload6, lease6)
_broker.release_view_lease = _raising_release
cmd6.final_report(True)  # lease release fails, handle retained
_broker.release_view_lease = _orig_release
check("case6.0 setup: release failed and the handle is retained (precondition for this case)",
      cmd6._master_index_lease is lease6)
cmd6.release_run_lock()  # the REAL deferred-deletion method, called exactly as final_report's own finally does
check("case6.1 deferred QObject deletion (release_run_lock) runs cleanly even after a failed "
      "lease release", cmd6.delete_later_calls == 1 and cmd6.set_parent_calls == [None])
check("case6.2 the retained lease handle survives the deferred-deletion call untouched "
      "(release_run_lock does not itself touch lease state)", cmd6._master_index_lease is lease6)
cmd6._b2c_release_master_index_lease()  # clean up this test's own real lease
check("case6.3 cleanup after the deferred-deletion case still succeeds via the real retry path",
      cmd6._master_index_lease is None)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
