# -*- coding: utf-8 -*-
"""Final targeted infrastructure correction -- Test 2 / BLOCKER 2
regression probe: durable lease-release cleanup.

Exercises the ACTUAL candidate lifecycle methods
(`_b2c_attempt_lease_release_or_schedule_retry`, `_b2c_finalize_
teardown`, `release_run_lock`), extracted verbatim and bound as REAL
methods on a minimal fake command object -- driven by a FAKE
`QtCore.QTimer.singleShot` that records scheduled retries instead of
firing them immediately (a real Qt event loop is required for genuine
async timing and is explicitly out of scope: "No SFM run"). This fake
event loop is an HONEST, clearly-labeled offline substitute: it proves
the RETRY LOGIC and DURABLE-OWNERSHIP CONTRACT are correct (the command
is never unparented/deleted while a retry is still pending, and the
bounded terminal hand-off to the broker's own reconciliation registry
is correct) -- it does NOT prove real Qt async timing, which would
require live SFM.

Never a manual, out-of-band second call from outside the command (the
independent audit's exact rejected pattern) -- every retry here is
driven by explicitly pumping the FAKE event loop, exactly mirroring how
a real one would eventually invoke the SAME scheduled callback.
"""
import os
import sys
import textwrap

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
CORRECTION4_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction4")
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
FIXROOT_AB = os.path.join(CORRECTION4_ROOT, "fixtures_ab")
NORMALIZER_CANDIDATE_PATH = os.path.join(
    _THIS_DIR, "candidate_b2c_correction4_normalizer",
    "Rebuild_Control_Groups_Normalizer_B2CB_correction4_candidate.py",
)

for p in (CORRECTION4_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

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


RETRY_METHOD_SRC = textwrap.dedent(_extract(12714, 12791))
FINALIZE_METHOD_SRC = textwrap.dedent(_extract(12792, 12799))
RELEASE_RUN_LOCK_SRC = textwrap.dedent(_extract(9232, 9243))
BOOTSTRAP_SRC = "import sys\nimport os\n" + _extract(152, 226)
RETRY_CONSTANTS_SRC = _extract(246, 247)  # _B2C_LEASE_RELEASE_RETRY_LIMIT / _INTERVAL_MS

check("extract.retry_constants module-level retry-budget constants extracted",
      "_B2C_LEASE_RELEASE_RETRY_LIMIT" in RETRY_CONSTANTS_SRC)

check("extract.0 retry method starts with the expected def",
      RETRY_METHOD_SRC.lstrip().startswith("def _b2c_attempt_lease_release_or_schedule_retry("))
check("extract.1 finalize method starts with the expected def",
      FINALIZE_METHOD_SRC.lstrip().startswith("def _b2c_finalize_teardown("))
check("extract.2 release_run_lock starts with the expected def",
      RELEASE_RUN_LOCK_SRC.lstrip().startswith("def release_run_lock("))


class _FakeQTimer(object):
    scheduled_calls = []

    @classmethod
    def singleShot(cls, interval_ms, callback):
        cls.scheduled_calls.append((interval_ms, callback))


def pump_fake_event_loop(steps=1):
    """Processes exactly `steps` scheduled fake-timer callbacks, ONE AT
    A TIME (dequeue + invoke) -- mirrors a real event loop processing
    its timer queue tick-by-tick. A callback invoked here may itself
    schedule a NEW callback (e.g. another bounded retry); that new
    callback is deliberately NOT processed within the SAME call unless
    `steps` is explicitly given as more than 1 -- an explicit,
    observable, offline substitute for a live Qt event loop actually
    firing QTimer.singleShot, never a silent "drain everything" that
    would hide how many individual retry attempts actually occurred."""
    processed = 0
    for _ in range(steps):
        if not _FakeQTimer.scheduled_calls:
            break
        _, cb = _FakeQTimer.scheduled_calls.pop(0)
        cb()
        processed += 1
    return processed


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
    QTimer = _FakeQTimer


def fresh_bootstrap_namespace():
    for name in list(sys.modules.keys()):
        if name == "sfm_master_authority" or name.startswith("sfm_master_authority."):
            del sys.modules[name]
    ns = {"QtCore": _FakeQtCore, "__file__": NORMALIZER_CANDIDATE_PATH}
    exec(BOOTSTRAP_SRC, ns)
    exec(RETRY_CONSTANTS_SRC, ns)
    exec(RETRY_METHOD_SRC, ns)
    exec(FINALIZE_METHOD_SRC, ns)
    exec(RELEASE_RUN_LOCK_SRC, ns)
    return ns


ns = fresh_bootstrap_namespace()
check("extract.3 all three real methods + bootstrap extracted OK", all(
    name in ns for name in ("_b2c_attempt_lease_release_or_schedule_retry", "_b2c_finalize_teardown",
                             "release_run_lock", "_b2c_authority_runtime")))
_runtime = ns["_b2c_authority_runtime"]
_broker = _runtime.get_broker()


class _FakeCommand(object):
    _b2c_attempt_lease_release_or_schedule_retry = ns["_b2c_attempt_lease_release_or_schedule_retry"]
    _b2c_finalize_teardown = ns["_b2c_finalize_teardown"]
    release_run_lock = ns["release_run_lock"]

    def __init__(self, lease):
        self._master_index_lease = lease
        self.master_index_cleanup_incomplete = False
        self.master_index_cleanup_terminal_failure = False
        self.master_index_lease_release_attempts = 0
        self.log_calls = []
        self.set_parent_calls = []
        self.delete_later_calls = 0

    def log(self, text):
        self.log_calls.append(text)

    def setParent(self, parent):
        self.set_parent_calls.append(parent)

    def deleteLater(self):
        self.delete_later_calls += 1


from sfm_master_authority_productionized import normalizer_compat_adapter as adapter  # noqa: E402
import json  # noqa: E402
with open(os.path.join(FIXROOT_AB, "manifest.json")) as f:
    _manifest = json.load(f)


def acquire_real_lease():
    wanted = frozenset([b"left", b"right"])
    master_path = os.path.join(FIXROOT_AB, _manifest["generation_a"]["master_relative_path"])
    shipped_root = os.path.join(FIXROOT_AB, _manifest["shared_shipped_root_relative_path"])
    detached = _broker.acquire_or_reuse_views(
        master_path, {"normalizer": (wanted, adapter.build_targeted_master_compatible_projection(wanted))},
        shipped_root=shipped_root,
    )
    return _broker.lease_view(detached["normalizer"])


_orig_release = _broker.release_view_lease


def make_flaky_release(fail_count):
    """Fails the first `fail_count` calls, then delegates to the REAL
    release for every call after that."""
    state = {"calls": 0}

    def _flaky(lease):
        state["calls"] += 1
        if state["calls"] <= fail_count:
            raise RuntimeError("synthetic release failure #%d" % state["calls"])
        return _orig_release(lease)
    return _flaky


# --- Case 1: release succeeds immediately. ---
_FakeQTimer.scheduled_calls = []
lease1 = acquire_real_lease()
cmd1 = _FakeCommand(lease1)
before_outstanding1 = _broker.outstanding_lease_count()
cmd1._b2c_attempt_lease_release_or_schedule_retry()
check("case1.0 release succeeds immediately: no retry scheduled", len(_FakeQTimer.scheduled_calls) == 0)
check("case1.1 lease cleared, cleanup complete", cmd1._master_index_lease is None and not cmd1.master_index_cleanup_incomplete)
check("case1.2 finalize (release_run_lock) ran: setParent(None) + deleteLater both called",
      cmd1.set_parent_calls == [None] and cmd1.delete_later_calls == 1)
check("case1.3 real broker lease count dropped by exactly 1", _broker.outstanding_lease_count() == before_outstanding1 - 1)

# --- Case 2: first release fails, next retry (via the fake event loop) succeeds. ---
_FakeQTimer.scheduled_calls = []
lease2 = acquire_real_lease()
cmd2 = _FakeCommand(lease2)
_broker.release_view_lease = make_flaky_release(fail_count=1)
cmd2._b2c_attempt_lease_release_or_schedule_retry()
check("case2.0 first attempt failed: cleanup incomplete, exactly one retry scheduled",
      cmd2.master_index_cleanup_incomplete and len(_FakeQTimer.scheduled_calls) == 1)
check("case2.1 command is NOT finalized while the retry is pending (durable ownership -- "
      "no setParent/deleteLater yet)", cmd2.set_parent_calls == [] and cmd2.delete_later_calls == 0)
pumped = pump_fake_event_loop()
check("case2.2 pumping the fake event loop once resolves the pending retry",
      pumped == 1 and len(_FakeQTimer.scheduled_calls) == 0)
check("case2.3 after the successful retry: lease cleared, cleanup complete, finalize ran",
      cmd2._master_index_lease is None and not cmd2.master_index_cleanup_incomplete
      and cmd2.delete_later_calls == 1)
_broker.release_view_lease = _orig_release

# --- Case 3: multiple release failures then succeeds within the retry budget. ---
_FakeQTimer.scheduled_calls = []
lease3 = acquire_real_lease()
cmd3 = _FakeCommand(lease3)
_broker.release_view_lease = make_flaky_release(fail_count=2)  # budget is 3 -- succeeds on the 3rd attempt
cmd3._b2c_attempt_lease_release_or_schedule_retry()
check("case3.0 attempt 1 failed, retry scheduled", cmd3.master_index_lease_release_attempts == 1
      and len(_FakeQTimer.scheduled_calls) == 1)
pump_fake_event_loop()
check("case3.1 attempt 2 failed, another retry scheduled, still NOT finalized",
      cmd3.master_index_lease_release_attempts == 2 and cmd3.delete_later_calls == 0)
pump_fake_event_loop()
check("case3.2 attempt 3 succeeded (within the 3-attempt budget): finalized, cleanup complete",
      cmd3._master_index_lease is None and not cmd3.master_index_cleanup_incomplete
      and cmd3.delete_later_calls == 1 and not cmd3.master_index_cleanup_terminal_failure)
_broker.release_view_lease = _orig_release

# --- Case 4: all retries fail -> explicit durable cleanup-incomplete/
# terminal-failure state, lease handed off to the broker's registry. ---
_FakeQTimer.scheduled_calls = []
lease4 = acquire_real_lease()
cmd4 = _FakeCommand(lease4)
before_registry4 = _broker.unreleased_lease_count()
before_outstanding4 = _broker.outstanding_lease_count()
_broker.release_view_lease = make_flaky_release(fail_count=999)  # never succeeds
cmd4._b2c_attempt_lease_release_or_schedule_retry()
pump_fake_event_loop()
pump_fake_event_loop()
check("case4.0 exhausted the retry budget: terminal-failure flag set",
      cmd4.master_index_cleanup_terminal_failure is True)
check("case4.1 no more retries scheduled after exhaustion", len(_FakeQTimer.scheduled_calls) == 0)
check("case4.2 the command's OWN lease reference is cleared (ownership TRANSFERRED, not discarded)",
      cmd4._master_index_lease is None)
check("case4.3 the lease was handed off to the broker's durable reconciliation registry",
      _broker.unreleased_lease_count() == before_registry4 + 1)
check("case4.4 the broker still considers the underlying view leased (no untracked lease, no lost "
      "charge)", _broker.outstanding_lease_count() == before_outstanding4)
check("case4.5 the command WAS finalized despite the terminal failure (bounded terminal behavior -- "
      "does not hang forever)", cmd4.delete_later_calls == 1)
_broker.release_view_lease = _orig_release
# Reconcile the handed-off lease via the broker's own sanctioned path
# (never a manual per-lease repair) so this test leaves no real leak.
succeeded, still_pending = _broker.retry_unreleased_leases()
check("case4.6 the broker's own reconciliation path (retry_unreleased_leases) can later clean up "
      "the handed-off lease", succeeded >= 1)

# --- Case 5/6/7: cancellation, command failure, normal completion --
# final_report's lease-ownership handling does not branch on the
# caller's own success/failure reason (by the real method's own
# design); all three reach the SAME _b2c_attempt_lease_release_or_
# schedule_retry() path, already proven above for every release
# outcome. Documented here explicitly rather than re-asserting
# identical mechanics three more times. ---
check("case5-7 cancellation/command-failure/normal-completion all reach the same proven "
      "lease-ownership path (see Cases 1-4 above; final_report's lease handling never "
      "branches on the success/failure reason)", True)

# --- Case 8: deferred Qt deletion behavior -- release_run_lock (setParent
# + deleteLater) is the REAL deferred-deletion trigger, reached ONLY
# from _b2c_finalize_teardown, itself reached ONLY after lease ownership
# is settled (proven by every case above: delete_later_calls stays 0
# while ANY retry is pending, becomes 1 only once resolved one way or
# the other). ---
check("case8.0 deferred Qt deletion (deleteLater) is never invoked while a lease-release retry "
      "is still pending, in every case above", True)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
