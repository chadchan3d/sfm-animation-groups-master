# -*- coding: utf-8 -*-
"""Package-Boundary Correction, Blocker A: decisive regression for
"leased orphan views escape generation invalidation" (Astra-reproduced
defect A, `docs/qualification/SFM_CGN_ASTRA_HOLISTIC_AUDIT_c0122762_2026-09-21.md`).

Root cause (confirmed by direct reading, not assumed): `ViewCache.
invalidate_generation()` iterated `self._entries` (the live cache dict)
only. A view displaced into `self._leased_orphans` by `_remove()` (which
happens when a same-cache-key admission retires a still-leased entry --
see `ViewCache.admit()`/`admit_batch()`) keeps its OWN `authorization`
token unless that exact token object is ALSO visited by `invalidate_
generation()`. Before this fix, a leased view of a just-superseded
generation, evicted into `_leased_orphans` moments earlier, remained
authorized (`is_stale() == False`) forever -- no other code path ever
invalidates an orphan's token.

Fix (`view_cache.py`, `invalidate_generation`): also iterate `self.
_leased_orphans.values()` and invalidate any matching-generation token
found there, using the SAME token-dedup set so a shared token is never
invalidated twice. Ownership/accounting for an orphan (its
`_leased_orphans` entry, its re-keyed ledger charge) is completely
untouched by this change -- only `LiveAuthorizationToken.invalidate()`
is called, which the required invariant explicitly separates from
ownership/release.

This test constructs `ViewCache`/`DetachedView`/`AggregateLedger`
directly (unit-level), matching the exact object graph the real broker/
cohort machinery builds, without needing a real compiled sidecar or
provider -- the defect and its fix live entirely in this in-memory
object graph, independent of I/O.

Never launches SFM. Read-only with respect to the frozen production
file and the canonical Master (neither is touched by this file at all).
"""
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CORRECTION6_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction6")
if os.path.abspath(CORRECTION6_ROOT) not in sys.path:
    sys.path.insert(0, os.path.abspath(CORRECTION6_ROOT))

from sfm_master_authority_productionized import descriptors  # noqa: E402
from sfm_master_authority_productionized import memory_accounting  # noqa: E402
from sfm_master_authority_productionized import view_cache as view_cache_mod  # noqa: E402
from sfm_master_authority_productionized import views  # noqa: E402

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)


def _make_view(master_sha256, token, consumer_kind, estimated_bytes, covered=()):
    semantic_generation = descriptors.SemanticGeneration(
        effective_master_path=u"<fixture>", master_sha256=master_sha256,
        master_byte_length=1000, authority_semantics_version=1, projection_contract_version=None,
    )
    artifact_identity = descriptors.ArtifactIdentity(
        sidecar_artifact_sha256=u"artifact-" + master_sha256, format_contract_version=1,
        authority_semantics_version=1, projection_contract_version=None,
        embedded_source_sha256=master_sha256, embedded_source_byte_length=1000,
    )
    coverage = views.CoverageDescriptor(dict((k, views.CoverageResult(views.KNOWN)) for k in covered))
    return views.DetachedView(
        semantic_generation=semantic_generation, artifact_identity=artifact_identity,
        coverage=coverage, projection_contract_version=None, admission_id=1,
        consumer_kind=consumer_kind, payload={"stub": True}, authorization=token,
        estimated_bytes=estimated_bytes,
    )


# ===========================================================================
# Primary decisive regression (governing prompt's 10-step sequence).
# ===========================================================================
print("\n=== Primary sequence: acquire A -> lease A -> displace A into orphans -> acquire B -> invalidate A ===")

ledger = memory_accounting.AggregateLedger()
cache = view_cache_mod.ViewCache(ledger)

# 1. publish/acquire generation A.
# NOTE ON TOKEN IDENTITY: the real broker creates exactly ONE
# LiveAuthorizationToken PER COHORT/ACQUISITION (`cohort.py`: `
# authorization = views.LiveAuthorizationToken(self.semantic_generation.
# master_sha256)`, called once per `Cohort`, shared only by the views
# THAT cohort's own `build_projections` call emits). A1 (this
# acquisition) and A2 (a LATER, separate re-acquisition of the same
# content-identical generation A, below) are therefore two DIFFERENT
# token objects even though both report `master_sha256 == "sha-A"` --
# using the SAME token object for both would let A2's own (correct,
# entries-based) invalidation accidentally invalidate A1 "for free"
# through the shared token, masking the exact defect this test exists
# to catch (an orphan's OWN token, from ITS OWN cohort, must be visited
# directly).
token_a1 = views.LiveAuthorizationToken(u"sha-A")
view_a1 = _make_view(u"sha-A", token_a1, u"normalizer", 100, covered=(b"lit1",))
cache.admit(view_a1)
check("step1.A_admitted A's view is present in the cache after admission",
      cache.get(view_a1.cache_key()) is view_a1)

# 2. hold a lease to A.
lease_a = cache.acquire_lease(view_a1)
check("step2.A_leased a real lease was granted for A", lease_a is not None and not lease_a.is_released())

# 3. cause A's cached entry to be displaced into _leased_orphans (a
# same-cache-key admission, e.g. a fresh cohort re-publishing the exact
# same generation/coverage/consumer_kind while the old view is still
# leased -- this is a real, reachable path: `admit()`'s own same-key
# retirement branch). A2 gets its OWN token (token_a2), per the real
# per-cohort-token model above.
token_a2 = views.LiveAuthorizationToken(u"sha-A")
view_a2 = _make_view(u"sha-A", token_a2, u"normalizer", 110, covered=(b"lit1",))
assert view_a2.cache_key() == view_a1.cache_key(), "test setup: A2 must collide on A1's cache_key"
cache.admit(view_a2)
check("step3.A1_displaced_into_orphans A1 was moved to _leased_orphans (no longer the live cache "
      "entry, but still tracked) when A2 was admitted under the same cache_key while A1 was leased",
      id(view_a1) in cache._leased_orphans and cache.get(view_a1.cache_key()) is view_a2)
check("step3.A1_lease_still_live A1's lease remains valid immediately after displacement "
      "(displacement must not itself revoke or drop the lease)",
      not lease_a.is_released() and view_a1.has_live_leases())

# 4. publish/acquire generation B.
token_b = views.LiveAuthorizationToken(u"sha-B")
view_b = _make_view(u"sha-B", token_b, u"normalizer", 90, covered=(b"lit2",))
cache.admit(view_b)
check("step4.B_admitted B's view is present in the cache after admission", cache.get(view_b.cache_key()) is view_b)

# 5. invalidate A (the real call site: broker.acquire_cohort invalidates
# the PREVIOUS master_sha256 once a NEW one is observed -- reproduced
# directly here against the cache, matching that call exactly).
cache.invalidate_generation(u"sha-A")

# 6. prove the old A token/view (A1, the orphan) can no longer pass the
# current validity/authorization path.
check("step6.A1_orphan_now_stale A1 (the leased orphan) is now stale -- its OWN token (token_a1, "
      "never shared with A2) was revoked by invalidate_generation even though A1 was never in "
      "self._entries -- this is the exact defect: entries-only iteration would find A2 (a "
      "DIFFERENT token) and never touch token_a1 at all", view_a1.is_stale())
check("step6.A1_own_token_invalid A1's own token (token_a1) is now invalid",
      not token_a1.is_valid())
check("step6.A2_also_stale A2 (still the live cache entry for generation A, its own SEPARATE "
      "token_a2) is also correctly stale via the entries-based path", view_a2.is_stale())
check("step6.A2_own_token_invalid A2's own token (token_a2) is now invalid",
      not token_a2.is_valid())

# 7. prove the old lease can still be released deterministically (an
# invalidated/stale view must remain releasable -- revocation must never
# strand ownership/accounting).
before_release_orphans = dict(cache._leased_orphans)
cache.release_lease(lease_a)
check("step7.A1_lease_released_cleanly releasing the lease on a now-invalidated orphan raises no "
      "error and completes", lease_a.is_released())
check("step7.A1_orphan_entry_cleared releasing A1's last lease removes it from _leased_orphans "
      "(the deferred release finalized)", id(view_a1) not in cache._leased_orphans, cache._leased_orphans)
check("step7.orphans_before_release_included_A1 sanity: A1 really was tracked as an orphan "
      "immediately before this release call", id(view_a1) in before_release_orphans)

# 8. prove retained accounting reaches the correct final value: only B
# (90 bytes) and A2 (110 bytes, still the live -- if stale -- cache
# entry) remain charged; A1's re-keyed orphan charge (100 bytes) was
# released in step 7.
final_retained = ledger.total_retained_bytes()
check("step8.retained_accounting_correct final retained-bytes total reflects exactly A2 (110) + "
      "B (90) = 200, with A1's 100-byte orphan charge fully released",
      final_retained == 200, final_retained)

# 9. prove B remains valid (unaffected by A's invalidation).
check("step9.B_still_valid B's view was never touched by invalidating generation A",
      not view_b.is_stale())

# 10. prove no provider/backing leak: this object graph never opens a
# provider/file handle at all (DetachedView never holds one, by
# construction -- see views.py's own docstring), so "no leak" here means
# no dangling ledger entries anywhere outside the two live cache entries
# (A2, B) once every lease is accounted for.
outstanding = cache.outstanding_lease_count()
check("step10.no_outstanding_leases_left every granted lease (only lease_a) has been released",
      outstanding == 0, outstanding)
check("step10.no_stray_ledger_categories no accounting leaked into any OTHER ledger category "
      "(pending/transient/etc.) as a side effect of this sequence",
      ledger.snapshot()["retained_detached_views"] == 200 and
      all(v == 0 for k, v in ledger.snapshot().items() if k != "retained_detached_views"),
      ledger.snapshot())

# ===========================================================================
# Additional required coverage: invalidation BEFORE release (already
# exercised above, steps 5-7) vs release BEFORE invalidation; repeated
# invalidation idempotence.
# ===========================================================================
print("\n=== Ordering variant: release BEFORE invalidation ===")

ledger2 = memory_accounting.AggregateLedger()
cache2 = view_cache_mod.ViewCache(ledger2)
token_c = views.LiveAuthorizationToken(u"sha-C")
view_c1 = _make_view(u"sha-C", token_c, u"normalizer", 50, covered=(b"lit3",))
cache2.admit(view_c1)
lease_c = cache2.acquire_lease(view_c1)
view_c2 = _make_view(u"sha-C", token_c, u"normalizer", 55, covered=(b"lit3",))
cache2.admit(view_c2)  # displaces C1 into _leased_orphans
check("release_before_invalidate.displaced C1 is a leased orphan before release/invalidate",
      id(view_c1) in cache2._leased_orphans)

cache2.release_lease(lease_c)  # release FIRST
check("release_before_invalidate.orphan_cleared_by_release releasing C1's last lease before any "
      "invalidation call already clears the orphan entry (pre-existing, correct behavior)",
      id(view_c1) not in cache2._leased_orphans)

cache2.invalidate_generation(u"sha-C")  # invalidate AFTER release
check("release_before_invalidate.still_invalidated_after_release invalidate_generation still "
      "correctly marks the (now unleased, no-longer-orphaned) shared token stale even when called "
      "AFTER the lease that created the orphan was already released",
      view_c1.is_stale() and view_c2.is_stale() and not token_c.is_valid())

print("\n=== Repeated-invalidation idempotence ===")
cache2.invalidate_generation(u"sha-C")
cache2.invalidate_generation(u"sha-C")
check("repeated_invalidation.idempotent calling invalidate_generation twice more on an "
      "already-invalidated generation raises no error and leaves state correctly stale",
      view_c1.is_stale() and view_c2.is_stale())

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(condition for _, condition in RESULTS):
    sys.exit(1)
