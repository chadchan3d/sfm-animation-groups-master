# -*- coding: utf-8 -*-
"""Astra SECOND correction gate -- Test 4: atomic ownership + REAL
teardown (F3/F4).

Part A (view_cache.py level, synthetic views -- pure in-memory
accounting logic, independent of the sidecar binary format): two
individually-admissible views whose SUM is not; second-view failure
leaves no partial state; same-key replacement with two borrowers;
lease attempt on an evicted returned view (a genuine remaining gap
found and fixed in THIS session -- see errors.EvictedViewLeaseRefused
and ViewCache.acquire_lease in view_cache.py).

Part B (the ACTUAL Normalizer candidate's real terminal paths): normal
completion, cancellation, command failure, and the deferred-deletion
path, each proven via reference/ledger probes against the REAL
`final_report()` teardown sequence -- not merely the isolated broker/
view_cache API surface.
"""
import sys

CORRECTION2_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction2"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"

for p in (CORRECTION2_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from sfm_master_authority_productionized import views  # noqa: E402
from sfm_master_authority_productionized import view_cache as view_cache_mod  # noqa: E402
from sfm_master_authority_productionized import memory_accounting  # noqa: E402
from sfm_master_authority_productionized import descriptors  # noqa: E402
from sfm_master_authority_productionized import errors  # noqa: E402

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)


def make_view(consumer_kind, estimated_bytes, master_sha="gen-A", covered_key=None):
    gen = descriptors.SemanticGeneration(
        effective_master_path="<synthetic>", master_sha256=master_sha, master_byte_length=1000,
        authority_semantics_version=1, projection_contract_version=None,
    )
    token = views.LiveAuthorizationToken(master_sha)
    covered_key = covered_key or (consumer_kind,)
    coverage = views.CoverageDescriptor({covered_key: views.CoverageResult(views.KNOWN, "SomeDest", [0])})
    return views.DetachedView(
        semantic_generation=gen, artifact_identity=None, coverage=coverage,
        projection_contract_version=None, admission_id=0, consumer_kind=consumer_kind,
        payload={"dummy": True}, authorization=token, estimated_bytes=estimated_bytes,
    )


# ===========================================================================
# Part A.1: two individually-admissible views whose SUM is not admissible.
# ===========================================================================
ledger1 = memory_accounting.AggregateLedger()
cache1 = view_cache_mod.ViewCache(ledger1)
v1 = make_view("normalizer", 10 * 1024 * 1024)   # 10 MiB alone: fine
v2 = make_view("character_preset", 10 * 1024 * 1024)  # 10 MiB alone: fine
# 20 MiB together > 16 MiB RETAINED_PROMOTION_GATE_BYTES.
try:
    cache1.admit_batch([v1, v2])
    outcome_a1 = "admitted"
except errors.ViewAdmissionRefused:
    outcome_a1 = "refused"
check("t4a.1 two individually-admissible (10MiB each) views whose SUM (20MiB) exceeds the "
      "16MiB gate are REFUSED as a whole batch", outcome_a1 == "refused", outcome_a1)
check("t4a.1 NEITHER view was published (no partial admission)", cache1.entry_count() == 0, cache1.entry_count())
check("t4a.1 the ledger reflects ZERO charge (nothing was partially charged either)",
      ledger1.total_retained_bytes() == 0, ledger1.total_retained_bytes())

# ===========================================================================
# Part A.2: "second-view failure" -- same shape, explicit proof that a
# batch failing on its cumulative total leaves the PRE-EXISTING cache
# state completely untouched (an unrelated view already cached survives
# unchanged).
# ===========================================================================
ledger2 = memory_accounting.AggregateLedger()
cache2 = view_cache_mod.ViewCache(ledger2)
pre_existing = make_view("pre_existing_consumer", 2 * 1024 * 1024)
cache2.admit(pre_existing)
before_entry_count = cache2.entry_count()
before_retained = ledger2.total_retained_bytes()

big1 = make_view("big_consumer_1", 9 * 1024 * 1024)
big2 = make_view("big_consumer_2", 9 * 1024 * 1024)  # 2+9+9 = 20MiB > 16MiB, and pre_existing is unpinned
try:
    cache2.admit_batch([big1, big2])
    outcome_a2 = "admitted"
except errors.ViewAdmissionRefused:
    outcome_a2 = "refused"
check("t4a.2 a batch that cannot fit even after evicting unrelated unpinned entries is REFUSED",
      outcome_a2 == "refused", outcome_a2)
check("t4a.2 pre-existing UNRELATED cache state is untouched by the failed batch "
      "(entry_count identical)", cache2.entry_count() == before_entry_count, cache2.entry_count())
check("t4a.2 pre-existing ledger charge is untouched by the failed batch",
      ledger2.total_retained_bytes() == before_retained, ledger2.total_retained_bytes())

# ===========================================================================
# Part A.3: same-key replacement with two borrowers -- an old view leased
# by TWO consumers is replaced (same cache_key) by a fresh view; the old
# view's charge must survive (re-keyed as a leased orphan) until BOTH
# borrowers release, while the new view is charged/cached immediately.
# ===========================================================================
ledger3 = memory_accounting.AggregateLedger()
cache3 = view_cache_mod.ViewCache(ledger3)
old_view = make_view("shared_consumer", 3 * 1024 * 1024, covered_key=("shared_key",))
cache3.admit(old_view)
lease_x = cache3.acquire_lease(old_view)
lease_y = cache3.acquire_lease(old_view)
check("t4a.3 the old view has two live leases before replacement", old_view.live_lease_count() == 2)

new_view = make_view("shared_consumer", 4 * 1024 * 1024, covered_key=("shared_key",))
check("t4a.3 old and new views share the exact same cache_key (same-key replacement scenario)",
      old_view.cache_key() == new_view.cache_key())
cache3.admit_batch([new_view])
check("t4a.3 the NEW view is now the live cache entry at that key",
      cache3.get(new_view.cache_key()) is new_view)
check("t4a.3 the ledger reflects BOTH the new view's charge AND the old (still-leased) "
      "view's preserved charge simultaneously (old+new overlap, never silently clobbered)",
      ledger3.total_retained_bytes() == (3 + 4) * 1024 * 1024, ledger3.total_retained_bytes())

cache3.release_lease(lease_x)
check("t4a.3 releasing ONE of the two old borrowers does NOT yet release the old view's "
      "orphaned charge (the other borrower still holds it live)",
      ledger3.total_retained_bytes() == (3 + 4) * 1024 * 1024, ledger3.total_retained_bytes())
cache3.release_lease(lease_y)
check("t4a.3 releasing the LAST old borrower finally drops the old view's orphaned charge, "
      "leaving only the new view's charge",
      ledger3.total_retained_bytes() == 4 * 1024 * 1024, ledger3.total_retained_bytes())

# ===========================================================================
# Part A.4: lease attempt on an evicted returned view -- the fix built in
# THIS session (errors.EvictedViewLeaseRefused).
# ===========================================================================
ledger4 = memory_accounting.AggregateLedger()
cache4 = view_cache_mod.ViewCache(ledger4)
victim = make_view("victim_consumer", 5 * 1024 * 1024, covered_key=("victim_key",))
cache4.admit(victim)
check("t4a.4 the victim view starts out genuinely cached and charged",
      cache4.get(victim.cache_key()) is victim and ledger4.total_retained_bytes() == 5 * 1024 * 1024)

# Evict it via unrelated pressure -- a big batch that requires evicting
# the (unpinned, un-leased) victim to fit.
evictor = make_view("evictor_consumer", 14 * 1024 * 1024, covered_key=("evictor_key",))
cache4.admit_batch([evictor])
check("t4a.4 the victim view was genuinely evicted (no longer the cache's live entry)",
      cache4.get(victim.cache_key()) is None)
check("t4a.4 the victim's charge was fully released at eviction (it had ZERO live leases at "
      "that moment, so it never became a leased orphan)",
      ledger4.total_retained_bytes() == 14 * 1024 * 1024, ledger4.total_retained_bytes())

try:
    cache4.acquire_lease(victim)
    outcome_a4 = "lease_succeeded"
except errors.EvictedViewLeaseRefused:
    outcome_a4 = "lease_refused"
check("t4a.4 leasing the evicted (stale Python reference) view is EXPLICITLY REFUSED -- never "
      "silently succeeds with zero backing charge", outcome_a4 == "lease_refused", outcome_a4)
check("t4a.4 the refusal did not somehow charge anything either",
      ledger4.total_retained_bytes() == 14 * 1024 * 1024, ledger4.total_retained_bytes())

print("\n=== Part A (view_cache-level) RESULT so far: %d/%d ===" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS)))

# ===========================================================================
# Part B: the ACTUAL Normalizer candidate's real terminal path --
# `final_report()`'s teardown block (lines 12675-12720), extracted and
# exec'd verbatim (same non-bypassed-bootstrap technique as Test 5) so
# `_b2c_authority_runtime` is the REAL, genuinely-imported corrected
# package, never an injected fake. Exercises: normal completion,
# cancellation/failure (same code path, no branch on `success`),
# deferred re-invocation (idempotency -- simulates a deferred QObject
# deletion path or a caller race), acquisition-failure-before-lease-
# existed, and a non-fatal release failure that must still drop the
# reference.
# ===========================================================================
NORMALIZER_CANDIDATE_PATH = (
    r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction2_normalizer"
    r"\Rebuild_Control_Groups_Normalizer_B2CB_correction2_candidate.py"
)
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


import textwrap  # noqa: E402

BOOTSTRAP_SRC = "import sys\nimport os\n" + _extract(152, 210)
TEARDOWN_SRC = textwrap.dedent(_extract(12675, 12720))  # class-method indent -> module-level def
check("t4b.extract.0 teardown range starts with the expected def",
      TEARDOWN_SRC.lstrip().startswith("def final_report("))
check("t4b.extract.1 teardown range ends with the expected finally-clause line",
      "self._master_index_lease = None" in TEARDOWN_SRC.strip().splitlines()[-1])


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


ns_b = fresh_bootstrap_namespace()
exec(BOOTSTRAP_SRC, ns_b)
exec(TEARDOWN_SRC, ns_b)
check("t4b.extract.2 final_report extracted OK", "final_report" in ns_b)
_runtime = ns_b["_b2c_authority_runtime"]
_broker_b = _runtime.get_broker()


class _FakeCommand(object):
    """Minimal stand-in for RebuildControlGroupsProductionRun -- only the
    attributes the REAL final_report teardown block actually touches."""

    def __init__(self, master_index, lease):
        self.finished = False
        self.master_index = master_index
        self._master_index_lease = lease
        self.log_calls = []

    def log(self, text):
        self.log_calls.append(text)


def acquire_real_lease():
    from sfm_master_authority_productionized import normalizer_compat_adapter as adapter
    from sfm_master_authority_productionized import broker as broker_mod
    wanted = frozenset([b"left", b"right"])
    detached = _broker_b.acquire_or_reuse_views(
        r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt",
        {"normalizer": (wanted, adapter.build_targeted_master_compatible_projection(wanted))},
        shipped_root=r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures\shipped_root_valid",
    )
    lease = _broker_b.lease_view(detached["normalizer"])
    return detached["normalizer"].payload, lease


# --- Case B.1: normal completion ---
payload1, lease1 = acquire_real_lease()
before_outstanding = _broker_b.outstanding_lease_count()
cmd1 = _FakeCommand(payload1, lease1)
ns_b["final_report"](cmd1, True)
check("t4b.1 normal completion: self.finished becomes True", cmd1.finished is True)
check("t4b.1 normal completion: self.master_index is cleared (command drops its payload reference)",
      cmd1.master_index is None)
check("t4b.1 normal completion: self._master_index_lease is cleared", cmd1._master_index_lease is None)
check("t4b.1 normal completion: the REAL broker's outstanding_lease_count dropped by exactly 1",
      _broker_b.outstanding_lease_count() == before_outstanding - 1, _broker_b.outstanding_lease_count())

# --- Case B.2: cancellation / command failure (same code path, success=False) ---
payload2, lease2 = acquire_real_lease()
before_outstanding2 = _broker_b.outstanding_lease_count()
cmd2 = _FakeCommand(payload2, lease2)
ns_b["final_report"](cmd2, False)
check("t4b.2 cancellation/failure path: reference + lease both cleared identically",
      cmd2.master_index is None and cmd2._master_index_lease is None)
check("t4b.2 cancellation/failure path: real lease count dropped by exactly 1",
      _broker_b.outstanding_lease_count() == before_outstanding2 - 1, _broker_b.outstanding_lease_count())

# --- Case B.3: deferred re-invocation / idempotency (simulates a
# deferred QObject deletion callback, or any caller racing a second
# final_report call) -- must be a genuine no-op, never a double-release. ---
before_outstanding3 = _broker_b.outstanding_lease_count()
ns_b["final_report"](cmd1, True)  # cmd1 already finished -- second call
check("t4b.3 a SECOND final_report call on an already-finished command is a pure no-op "
      "(guarded by `if self.finished: return`)", _broker_b.outstanding_lease_count() == before_outstanding3)

# --- Case B.4: acquisition failure before the lease ever existed (no
# `_master_index_lease` attribute at all) -- must not crash. ---
cmd4 = _FakeCommand(None, None)
del cmd4._master_index_lease
try:
    ns_b["final_report"](cmd4, False)
    outcome_b4 = "ok"
except Exception as exc:
    outcome_b4 = "raised:%r" % (exc,)
check("t4b.4 final_report on a command that never got a lease at all (acquisition failed "
      "before build) does not crash (getattr default handles the missing attribute)",
      outcome_b4 == "ok", outcome_b4)
check("t4b.4 finished still becomes True", cmd4.finished is True)

# --- Case B.5: non-fatal release failure -- the reference is STILL
# dropped via `finally`, and the failure is logged, never silently
# swallowed. ---
payload5, lease5 = acquire_real_lease()
cmd5 = _FakeCommand(payload5, lease5)


def _raising_release(_lease):
    raise RuntimeError("synthetic non-fatal release failure")


_orig_release = _broker_b.release_view_lease
_broker_b.release_view_lease = _raising_release
try:
    ns_b["final_report"](cmd5, True)
finally:
    _broker_b.release_view_lease = _orig_release

check("t4b.5 a release failure is LOGGED, not silently swallowed", len(cmd5.log_calls) == 1, cmd5.log_calls)
check("t4b.5 despite the release failure, the lease reference is STILL dropped via `finally` "
      "(never left as a stale, un-recheckable live reference)", cmd5._master_index_lease is None)
check("t4b.5 the command's own master_index reference is cleared regardless of the release outcome",
      cmd5.master_index is None)
# Clean up the leaked real lease (the synthetic failure prevented the
# real broker from ever seeing release_view_lease called for it).
_broker_b.release_view_lease(lease5)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
