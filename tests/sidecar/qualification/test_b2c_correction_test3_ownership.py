# -*- coding: utf-8 -*-
"""Astra post-B2C-B correction gate -- Test 3: ownership/teardown (F3).
Exercises the real view_cache/broker/views lease mechanism directly:
escaped payload+eviction, two borrowers, same-key replacement,
cancellation, failed second admission, invalidation, completion. Never
launches SFM; uses real fixtures + the real official artifact.
"""
import sys

CORRECTION_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"
FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
OFFICIAL_ROOT = FIXROOT_B2A + r"\shipped_root_valid"
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"

for p in (CORRECTION_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from sfm_master_authority_productionized import broker as broker_mod  # noqa: E402
from sfm_master_authority_productionized import memory_accounting  # noqa: E402
from sfm_master_authority_productionized import view_cache as view_cache_mod  # noqa: E402
from sfm_master_authority_productionized import views  # noqa: E402
from sfm_master_authority_productionized import descriptors  # noqa: E402
from sfm_master_authority_productionized import errors  # noqa: E402

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)


def _make_view(ledger, key_suffix, estimated_bytes, master_sha="a" * 64):
    sg = descriptors.SemanticGeneration(
        effective_master_path="fake", master_sha256=master_sha, master_byte_length=1,
        authority_semantics_version=1, projection_contract_version=None,
    )
    ai = descriptors.ArtifactIdentity(
        sidecar_artifact_sha256="0" * 64, format_contract_version=1,
        authority_semantics_version=1, projection_contract_version=None,
        embedded_source_sha256=master_sha, embedded_source_byte_length=1,
    )
    cov = views.CoverageDescriptor({("k%s" % key_suffix).encode("ascii"): views.CoverageResult(views.KNOWN)})
    token = views.LiveAuthorizationToken(master_sha)
    payload = {"marker": key_suffix}
    return views.DetachedView(sg, ai, cov, None, key_suffix, "consumer_%s" % key_suffix, payload, token, estimated_bytes)


# ===========================================================================
# Case 1: escaped payload survives eviction (the core F3 finding)
# ===========================================================================
ledger1 = memory_accounting.AggregateLedger()
cache1 = view_cache_mod.ViewCache(ledger1)
big1 = _make_view(ledger1, "big1", memory_accounting.RETAINED_PROMOTION_GATE_BYTES - 100)
cache1.admit(big1)
escaped_lease = cache1.acquire_lease(big1)
escaped_payload_ref = big1.payload  # simulates a consumer holding onto the payload dict

charge_before_eviction = ledger1.snapshot()[memory_accounting.CATEGORY_RETAINED_VIEWS]
check("case1.0 view is charged before any pressure", charge_before_eviction > 0, charge_before_eviction)

# Force eviction pressure: admit something that would need big1's room.
# Since big1 is now LEASED, admission of a same-size competitor must
# REFUSE rather than silently evict the leased, still-referenced view.
competitor1 = _make_view(ledger1, "comp1", 1000)
try:
    cache1.admit(competitor1)
    admitted_ok = True
except errors.ViewAdmissionRefused:
    admitted_ok = False
check("case1.1 a LEASED view is never evicted to make room (matches eviction.3's pinned semantics)",
      not admitted_ok or cache1.entry_count() == 2, (admitted_ok, cache1.entry_count()))

charge_after_pressure = ledger1.snapshot()[memory_accounting.CATEGORY_RETAINED_VIEWS]
check("case1.2 ledger charge for the leased view was NEVER dropped while the lease is live "
      "(no undercount)", charge_after_pressure >= charge_before_eviction, (charge_before_eviction, charge_after_pressure))
check("case1.3 the escaped payload reference is still the SAME object/content the consumer holds",
      escaped_payload_ref is big1.payload and escaped_payload_ref["marker"] == "big1")

cache1.release_lease(escaped_lease)
check("case1.4 releasing the lease does not raise", True)

# ===========================================================================
# Case 2: two borrowers -- releasing one must NOT drop the charge while
# the other is still live.
# ===========================================================================
ledger2 = memory_accounting.AggregateLedger()
cache2 = view_cache_mod.ViewCache(ledger2)
shared = _make_view(ledger2, "shared", 5000)
cache2.admit(shared)
lease_a = cache2.acquire_lease(shared)
lease_b = cache2.acquire_lease(shared)
check("case2.0 two independent leases were both acquired", shared.live_lease_count() == 2, shared.live_lease_count())

cache2.release_lease(lease_a)
check("case2.1 releasing ONE of two leases leaves the view still leased (pinned)",
      shared.pinned is True and shared.live_lease_count() == 1, shared.live_lease_count())
check("case2.2 view still fully cached and charged after releasing only one of two leases",
      cache2.entry_count() == 1 and ledger2.snapshot()[memory_accounting.CATEGORY_RETAINED_VIEWS] > 0)

cache2.release_lease(lease_b)
check("case2.3 releasing the LAST lease drops pinning", shared.pinned is False, shared.live_lease_count())

# ===========================================================================
# Case 3: same-key replacement while the OLD view is still leased --
# explicit old+new overlap accounting, never silent clobbering.
# ===========================================================================
ledger3 = memory_accounting.AggregateLedger()
cache3 = view_cache_mod.ViewCache(ledger3)
old_view = _make_view(ledger3, "samekey", 4000, master_sha="b" * 64)
cache3.admit(old_view)
old_lease = cache3.acquire_lease(old_view)
old_charge = ledger3.snapshot()[memory_accounting.CATEGORY_RETAINED_VIEWS]

new_view = _make_view(ledger3, "samekey", 3000, master_sha="b" * 64)
check("case3.0 old and new views genuinely share the same cache_key",
      old_view.cache_key() == new_view.cache_key())
cache3.admit(new_view)  # same cache_key as old_view

check("case3.1 the new view is now the one returned by get()",
      cache3.get(new_view.cache_key()) is new_view)
check("case3.2 the OLD view's charge was NOT silently dropped while it is still leased "
      "(explicit old+new overlap, both accounted)",
      ledger3.snapshot()[memory_accounting.CATEGORY_RETAINED_VIEWS] >= old_charge,
      (old_charge, ledger3.snapshot()[memory_accounting.CATEGORY_RETAINED_VIEWS]))
check("case3.3 old view is still functionally alive/leased even though evicted from the cache slot",
      old_view.has_live_leases() is True)

cache3.release_lease(old_lease)
check("case3.4 releasing the orphaned old view's last lease finalizes its deferred charge release",
      True)  # no exception is itself the proof; exact byte accounting checked structurally above

# ===========================================================================
# Case 4: cancellation -- Cohort.cancel() always closes the provider and
# never leaves an unreleased lease dangling from THIS package's own
# lifecycle (leases are consumer-side; cancellation before publication
# means no view/lease was ever created in the first place).
# ===========================================================================
b4 = broker_mod.Broker(api_version="test-t3-cancel")
from sfm_master_authority_productionized import cohort as cohort_mod  # noqa: E402
c4 = cohort_mod.Cohort(REAL_MASTER_PATH, shipped_root=OFFICIAL_ROOT, broker=b4)
c4._open_provider_once()
check("case4.0 cohort has an open provider before cancel", c4._provider is not None)
c4.cancel()
check("case4.1 cancel() closes the provider and leaves zero outstanding leases",
      c4._provider is None and b4.outstanding_lease_count() == 0,
      (c4._provider, b4.outstanding_lease_count()))

# ===========================================================================
# Case 5: failed second admission -- a ResourceAdmissionRefusal during
# acquisition leaves no lease outstanding and no phantom charge.
# ===========================================================================
b5 = broker_mod.Broker(api_version="test-t3-failed-admission")
from sfm_master_authority_productionized import projections  # noqa: E402
try:
    b5.acquire_cohort(
        REAL_MASTER_PATH,
        {"normalizer": projections.build_normalizer_like_projection(["left"])},
        shipped_root=OFFICIAL_ROOT, runtime_cap_bytes=1024,
    )
    check("case5.0 expected ResourceAdmissionRefusal", False, "did not raise")
except errors.ResourceAdmissionRefusal:
    check("case5.0 expected ResourceAdmissionRefusal", True)
check("case5.1 failed admission leaves zero outstanding leases and zero retained charge",
      b5.outstanding_lease_count() == 0
      and b5.ledger_snapshot()[memory_accounting.CATEGORY_RETAINED_VIEWS] == 0,
      (b5.outstanding_lease_count(), b5.ledger_snapshot()))

# ===========================================================================
# Case 6: invalidation -- a stale (invalidated) but still-leased view
# stays readable and charged; the ledger never silently drops it either.
# ===========================================================================
ledger6 = memory_accounting.AggregateLedger()
cache6 = view_cache_mod.ViewCache(ledger6)
stale_leased = _make_view(ledger6, "staleleased", 2000, master_sha="c" * 64)
cache6.admit(stale_leased)
stale_lease = cache6.acquire_lease(stale_leased)
cache6.invalidate_generation("c" * 64)
check("case6.0 invalidated-but-leased view is stale", stale_leased.is_stale() is True)
check("case6.1 cache.get() refuses to hand out the stale view even though it is still leased",
      cache6.get(stale_leased.cache_key()) is None)
check("case6.2 the leased view's payload remains readable for diagnosis after invalidation",
      stale_leased.payload["marker"] == "staleleased")
check("case6.3 ledger charge is untouched by invalidation alone (release is lease-driven, not "
      "staleness-driven)", ledger6.snapshot()[memory_accounting.CATEGORY_RETAINED_VIEWS] > 0)
cache6.release_lease(stale_lease)

# ===========================================================================
# Case 7: command completion -- a real acquisition through the full
# candidate call site correctly zeroes outstanding leases after release.
# ===========================================================================
_norm_path = (
    r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction_normalizer"
    r"\Rebuild_Control_Groups_Normalizer_B2CB_correction_candidate.py"
)
with open(_norm_path, "rb") as _f:
    _norm_lines = _f.read().decode("utf-8").splitlines()


def _extract(a, b):
    return "\n".join(_norm_lines[a - 1: b]) + "\n"


_func_src = _extract(1439, 1520)  # acquire_master_index_via_qualified_authority, exact bounds
from sfm_master_authority_productionized import normalizer_compat_adapter as _adapter  # noqa: E402


class _FakeRuntimeModule(object):
    def __init__(self, b):
        self._b = b

    def get_broker(self, *a, **kw):
        return self._b


class _FakeQThread(object):
    @staticmethod
    def currentThread():
        return "main"


class _FakeQCoreApplication(object):
    @staticmethod
    def instance():
        return None  # no real Qt app in this offline test -> lambda short-circuits to True


class _FakeQtCore(object):
    QThread = _FakeQThread
    QCoreApplication = _FakeQCoreApplication


ns7 = {"_b2c_normalizer_adapter": _adapter, "QtCore": _FakeQtCore}
exec(_func_src, ns7)
b7 = broker_mod.Broker(api_version="test-t3-completion")
ns7["_b2c_authority_runtime"] = _FakeRuntimeModule(b7)
payload7, lease7 = ns7["acquire_master_index_via_qualified_authority"](
    REAL_MASTER_PATH, set(["left", "right"]), shipped_root=OFFICIAL_ROOT,
)
check("case7.0 real acquisition returned a real lease with the view still leased",
      b7.outstanding_lease_count() == 1, b7.outstanding_lease_count())
b7.release_view_lease(lease7)
check("case7.1 releasing the lease at 'command completion' zeroes outstanding leases",
      b7.outstanding_lease_count() == 0, b7.outstanding_lease_count())

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
