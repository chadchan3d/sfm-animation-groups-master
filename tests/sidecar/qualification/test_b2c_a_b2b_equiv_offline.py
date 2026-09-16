# -*- coding: utf-8 -*-
"""R3-B2C-A: B2B-equivalent offline qualification suite, run against the
PRODUCTIONIZED candidate sfm_master_authority package instead of the
frozen B2A deploy copy. Byte-identical assertions to test_b2b_offline.py
-- only the import root changed. Python 2.7 / 3 compatible (statically
reviewed for 2.7 compatibility here; real dual-interpreter execution
happens only inside actual SFM). Never launches SFM, never modifies
R1D/final-R3-A2B/Master/production consumer files, never modifies the
frozen B2A deploy copy."""
import os
import sys

# The frozen B2A deploy copy is deliberately NOT put on sys.path here --
# only the candidate copy, staged under a correctly-named
# "sfm_master_authority" folder, so `import sfm_master_authority...` can
# only resolve to the candidate.
PKG_PARENT = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\67454949-e69f-4280-93d9-87c1f4464330\scratchpad\candidate_b2c_test_root"
)
GATE_R2_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r2_formal_deploy"
)
FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
FIXROOT_B2B = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures_b2b"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"

for p in (PKG_PARENT, GATE_R2_DIR, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from sfm_master_authority import broker as broker_mod  # noqa: E402
from sfm_master_authority import cohort as cohort_mod  # noqa: E402
from sfm_master_authority import errors  # noqa: E402
from sfm_master_authority import memory_accounting  # noqa: E402
from sfm_master_authority import projections  # noqa: E402
from sfm_master_authority import sidecar_contract  # noqa: E402
from sfm_master_authority import view_cache as view_cache_mod  # noqa: E402
from sfm_master_authority import views  # noqa: E402

results = []


def check(name, condition, detail=None):
    results.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


import json
with open(os.path.join(FIXROOT_B2B, "identities.json")) as f:
    b2b_ids = json.load(f)

REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"  # read-only use only
REAL_MASTER_SHA = b2b_ids["real_master_sha256"]
SHIPPED_TWO_ARTIFACTS = b2b_ids["shipped_two_artifacts_root"]
ARTIFACT_A_SHA = b2b_ids["artifact_a_sha256"]
ARTIFACT_B_SHA = b2b_ids["artifact_b_sha256"]

REAL_LITERALS = ["left", "right", "Left PupilDown", "Right PupilDown", "Left PupilGrow"]
REAL_CSP_VOCAB = ["Left PupilLeft", "Right PupilLeft", "Left PupilRight"]
NONEXISTENT_LITERAL = "ThisControlDoesNotExistAnywhereInTheMaster_XYZ123"


def normalizer_builder():
    return projections.build_normalizer_like_projection(REAL_LITERALS + [NONEXISTENT_LITERAL])


def csp_builder():
    return projections.build_character_preset_like_projection(REAL_CSP_VOCAB)


# ===========================================================================
# SECTION: baseline re-verification
# ===========================================================================
print("=== Baseline ===")
check("baseline.1 real Master matches pinned SHA", REAL_MASTER_SHA == "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93")
check("baseline.2 real official Master file itself matches (read-only check)",
      __import__("hashlib").sha256(open(REAL_MASTER_PATH, "rb").read()).hexdigest() == REAL_MASTER_SHA)


def fresh_broker():
    return broker_mod.Broker(api_version="test-b2b")


# ===========================================================================
# SECTION: one-provider-at-a-time invariant
# ===========================================================================
print("=== One-provider-at-a-time invariant ===")

b = fresh_broker()

# sequential cohorts
for _ in range(3):
    b.acquire_cohort(REAL_MASTER_PATH, {"normalizer": normalizer_builder(), "csp": csp_builder()},
                      shipped_root=SHIPPED_TWO_ARTIFACTS)
counters = b.provider_counters()
check("invariant.1 sequential cohorts: peak_open_provider_count == 1", counters["peak_open_provider_count"] == 1, counters)
check("invariant.1b sequential cohorts: current_open_provider_count == 0 after all complete", counters["current_open_provider_count"] == 0, counters)
check("invariant.1c total closes == total opens after sequential cohorts", counters["total_provider_opens"] == counters["total_provider_closes"], counters)

# near-simultaneous / reentrant request -> AuthorityBusy, never provider #2
b2 = fresh_broker()


def _reentrant_normalizer_builder(provider):
    # Attempt a SECOND acquisition while this one's cohort is still OPEN
    # (the provider passed in here is still open) -- must be refused.
    try:
        b2.acquire_cohort(REAL_MASTER_PATH, {"x": (lambda p: ({}, views.CoverageDescriptor({}), 8))},
                          shipped_root=SHIPPED_TWO_ARTIFACTS)
        reentry_result["raised"] = False
    except errors.AuthorityBusy:
        reentry_result["raised"] = True
    return projections.build_normalizer_like_projection(REAL_LITERALS)(provider)


reentry_result = {}
b2.acquire_cohort(REAL_MASTER_PATH, {"normalizer": _reentrant_normalizer_builder}, shipped_root=SHIPPED_TWO_ARTIFACTS)
check("invariant.2 reentrant acquisition attempt while one is open raises AuthorityBusy", reentry_result.get("raised") is True)
counters2 = b2.provider_counters()
check("invariant.2b peak_open_provider_count still == 1 despite the reentrant attempt (never opened #2)",
      counters2["peak_open_provider_count"] == 1, counters2)

# failure during validation (nonexistent shipped root -> SidecarMissing, before any provider opens)
b3 = fresh_broker()
try:
    b3.acquire_cohort(REAL_MASTER_PATH, {"normalizer": normalizer_builder()}, shipped_root=os.path.join(FIXROOT_B2B, "does_not_exist"))
    check("invariant.3 failure during validation/selection -> SidecarMissing", False, "did not raise")
except errors.SidecarMissing:
    check("invariant.3 failure during validation/selection -> SidecarMissing", True)
counters3 = b3.provider_counters()
check("invariant.3b no provider was ever opened for a selection-time failure", counters3["total_provider_opens"] == 0, counters3)

# failure during projection (a builder_fn that raises) -> provider still closes deterministically
b4 = fresh_broker()


def _failing_builder(provider):
    raise RuntimeError("simulated projection-builder failure")


try:
    b4.acquire_cohort(REAL_MASTER_PATH, {"boom": _failing_builder}, shipped_root=SHIPPED_TWO_ARTIFACTS)
    check("invariant.4 failure during projection building propagates", False, "did not raise")
except RuntimeError:
    check("invariant.4 failure during projection building propagates", True)
counters4 = b4.provider_counters()
check("invariant.4b provider opened exactly once and closed exactly once despite the projection failure",
      counters4["total_provider_opens"] == 1 and counters4["total_provider_closes"] == 1, counters4)
check("invariant.4c current_open_provider_count == 0 after a projection-time failure", counters4["current_open_provider_count"] == 0, counters4)

# H0/H1 instability -- reuse the B2A-proven stub technique (mutate a real,
# freely-mutable fixture Master between the cohort's own h0 capture and its
# h1 recheck), confirming the SAME real detection logic at the cohort level.
h01_dir = os.path.join(FIXROOT_B2A, "h01")
h01_master = os.path.join(h01_dir, "master_b2b.txt")
with open(h01_master, "wb") as f:
    f.write(b"B2B_ORIGINAL_CONTENT")


def _write_master(content_bytes):
    with open(h01_master, "wb") as f:
        f.write(content_bytes)


_flip_state = {"calls": 0}


def _make_flip_once_builder():
    def _b(provider):
        return ({}, views.CoverageDescriptor({}), 8)
    return _b


class _FakeArtifactIdentity(object):
    def __init__(self, embedded_source_sha256):
        self.embedded_source_sha256 = embedded_source_sha256
        self.authority_semantics_version = 1
        self.projection_contract_version = None
        self.sidecar_artifact_sha256 = "0" * 64


class _StubProvider(object):
    def close(self):
        pass


def _stub_open_provider_once(self):
    # Bypasses real file I/O entirely -- this test targets Cohort's OWN
    # H0/H1 comparison logic in build_projections(), not selection/
    # validation (already covered by invariant.3/3b and by B2A's own
    # selection tests). h0 is real (computed from the real, freely
    # mutable fixture Master); the "artifact" is a stub claiming to match
    # whatever h0 was just observed.
    _flip_state["calls"] += 1
    self.h0 = __import__("sfm_master_authority.observation", fromlist=["observe_master"]).observe_master(self.master_path)
    self.artifact_identity = _FakeArtifactIdentity(embedded_source_sha256=self.h0.sha256)
    self._provider = _StubProvider()
    if _flip_state["calls"] == 1:
        _write_master(b"B2B_MUTATED_DURING_VALIDATION")
    if self._broker is not None:
        self._broker._on_provider_opened(self.cohort_id)
    return self._provider


b5 = fresh_broker()
_orig_open_once = cohort_mod.Cohort._open_provider_once
cohort_mod.Cohort._open_provider_once = _stub_open_provider_once
try:
    b5.acquire_cohort(h01_master, {"x": _make_flip_once_builder()})
    h0h1_outcome = "succeeded_on_retry"
except errors.AuthorityChangedDuringAcquisition:
    h0h1_outcome = "failed_immediately"
finally:
    cohort_mod.Cohort._open_provider_once = _orig_open_once
check("invariant.5 H0/H1 instability at the cohort level -> retried once, succeeded on 2nd attempt",
      h0h1_outcome == "succeeded_on_retry", h0h1_outcome)
check("invariant.5b exactly 2 attempts made (1 retry total)", _flip_state["calls"] == 2, _flip_state)
counters5 = b5.provider_counters()
check("invariant.5c peak_open_provider_count == 1 even across the retried attempt (never 2 concurrently)",
      counters5["peak_open_provider_count"] == 1, counters5)

# local->shipped recovery path (from B2A), exercised through a real cohort.
with open(os.path.join(FIXROOT_B2A, "local_corrupt_test", "identities.json")) as f:
    lct_ids = json.load(f)
b6 = fresh_broker()
detached6 = b6.acquire_cohort(
    REAL_MASTER_PATH, {"normalizer": normalizer_builder()},
    allow_local_candidates=True, local_pointer_path=lct_ids["pointer_corrupt_path"],
    generated_root=lct_ids["generated_root"], shipped_root=os.path.join(FIXROOT_B2A, "shipped_root_valid"),
)
check("invariant.6 local-corrupt->shipped recovery succeeds through a real cohort", "normalizer" in detached6)
counters6 = b6.provider_counters()
check("invariant.6b exactly one provider opened for the recovered acquisition (never one for local + one for shipped)",
      counters6["total_provider_opens"] == 1, counters6)

# cancellation before publication
b7 = fresh_broker()
c7 = cohort_mod.Cohort(REAL_MASTER_PATH, shipped_root=SHIPPED_TWO_ARTIFACTS, broker=b7)
c7._open_provider_once()
check("invariant.7 cohort has an open provider before cancel", c7._provider is not None)
c7.cancel()
check("invariant.7b cancel() deterministically closes the provider", c7._provider is None)
check("invariant.7c cohort state is CANCELLED", c7.state == cohort_mod.Cohort.STATE_CANCELLED)
counters7 = b7.provider_counters()
check("invariant.7d counters reflect the cancel as a real close", counters7["total_provider_opens"] == 1 and counters7["total_provider_closes"] == 1, counters7)


# ===========================================================================
# SECTION: detached-view envelope + coverage semantics
# ===========================================================================
print("=== Detached-view envelope + coverage semantics ===")

b8 = fresh_broker()
detached8 = b8.acquire_cohort(REAL_MASTER_PATH, {"normalizer": normalizer_builder(), "csp": csp_builder()},
                               shipped_root=SHIPPED_TWO_ARTIFACTS)
norm_view = detached8["normalizer"]
csp_view = detached8["csp"]

check("envelope.1 view carries semantic_generation identity", norm_view.semantic_generation.master_sha256 == REAL_MASTER_SHA)
check("envelope.2 view carries artifact_identity separately", norm_view.artifact_identity is not None)
check("envelope.3 view carries a real (non-schema-only) coverage descriptor", len(norm_view.coverage) == len(REAL_LITERALS) + 1)
check("envelope.4 view carries projection_contract_version field", hasattr(norm_view, "projection_contract_version"))
check("envelope.5 view carries a creation/admission id", norm_view.admission_id is not None)
check("envelope.6 view carries memory/accounting metadata (estimated_bytes)", norm_view.estimated_bytes > 0, norm_view.estimated_bytes)
check("envelope.7 live authorization token is a DISTINCT object from the payload",
      norm_view.authorization is not norm_view.payload and not isinstance(norm_view.authorization, dict))
check("envelope.8 no provider/backing/handle attributes exist on the view (slots-checked)",
      set(views.DetachedView.__slots__).isdisjoint({"provider", "_provider", "buf", "_buf", "handle", "traceback"}))

# coverage semantics
covered_known = projections._ascii_fold(REAL_LITERALS[0])
covered_unknown_candidate = projections._ascii_fold(NONEXISTENT_LITERAL)
uncovered_key = projections._ascii_fold("SomeKeyNeverRequestedAtAll")

r_known = norm_view.coverage.lookup(covered_known)
r_unknown = norm_view.coverage.lookup(covered_unknown_candidate)
r_uncovered = norm_view.coverage.lookup(uncovered_key)

check("coverage.1 a real, existing literal resolves to Known", r_known.status == views.KNOWN, r_known)
check("coverage.2 a genuinely-nonexistent-but-REQUESTED literal resolves to MasterUnknown", r_unknown.status == views.MASTER_UNKNOWN, r_unknown)
check("coverage.3 a NEVER-requested key resolves to Uncovered, never conflated with MasterUnknown",
      r_uncovered.status == views.UNCOVERED, r_uncovered)
check("coverage.4 Uncovered and MasterUnknown are distinct statuses", views.UNCOVERED != views.MASTER_UNKNOWN)

# AuthorityUnavailable -- a property of an ACQUISITION ATTEMPT, not a view lookup.
try:
    fresh_broker().acquire_cohort(REAL_MASTER_PATH, {"x": normalizer_builder()}, shipped_root=os.path.join(FIXROOT_B2B, "does_not_exist"))
    check("coverage.5 AuthorityUnavailable-class failure (SidecarMissing) surfaces at ACQUISITION time, not as a view lookup result", False, "did not raise")
except errors.SidecarMissing:
    check("coverage.5 AuthorityUnavailable-class failure (SidecarMissing) surfaces at ACQUISITION time, not as a view lookup result", True)


# ===========================================================================
# SECTION: aggregate memory accounting
# ===========================================================================
print("=== Aggregate memory accounting ===")

ledger = memory_accounting.AggregateLedger()
ledger.charge(memory_accounting.CATEGORY_RETAINED_VIEWS, "v1", 1000)
ledger.charge(memory_accounting.CATEGORY_RETAINED_VIEWS, "v2", 2000)
check("memory.1 ledger sums per-category charges correctly", ledger.snapshot()[memory_accounting.CATEGORY_RETAINED_VIEWS] == 3000, ledger.snapshot())
ledger.release(memory_accounting.CATEGORY_RETAINED_VIEWS, "v1")
check("memory.2 releasing one entry reduces the category total correctly", ledger.snapshot()[memory_accounting.CATEGORY_RETAINED_VIEWS] == 2000)
check("memory.3 total_retained_bytes aggregates across categories (never a single per-tool quota)",
      ledger.total_retained_bytes() == 2000)
check("memory.4 would_exceed_retained_gate correctly compares against the 16 MiB gate",
      ledger.would_exceed_retained_gate(memory_accounting.RETAINED_PROMOTION_GATE_BYTES) is True)
check("memory.5 categories are independent (transient charge does not affect retained total)",
      ledger.total_transient_bytes() == 0)

b9 = fresh_broker()
detached9 = b9.acquire_cohort(REAL_MASTER_PATH, {"normalizer": normalizer_builder()}, shipped_root=SHIPPED_TWO_ARTIFACTS)
snap9 = b9.ledger_snapshot()
check("memory.6 a real acquisition's view is charged into CATEGORY_RETAINED_VIEWS",
      snap9[memory_accounting.CATEGORY_RETAINED_VIEWS] > 0, snap9)
check("memory.7 pending-projection charge is released after admission (transient, not left charged)",
      snap9[memory_accounting.CATEGORY_PENDING_PROJECTION] == 0, snap9)


# ===========================================================================
# SECTION: view admission / eviction policy
# ===========================================================================
print("=== View admission / eviction policy ===")

ledger2 = memory_accounting.AggregateLedger()
cache2 = view_cache_mod.ViewCache(ledger2)


def _make_fake_view(key_suffix, estimated_bytes, master_sha=REAL_MASTER_SHA):
    from sfm_master_authority import descriptors as descriptors_mod
    sg = descriptors_mod.SemanticGeneration(
        effective_master_path="fake", master_sha256=master_sha, master_byte_length=1,
        authority_semantics_version=1, projection_contract_version=None,
    )
    ai = descriptors_mod.ArtifactIdentity(
        sidecar_artifact_sha256="0" * 64, format_contract_version=1,
        authority_semantics_version=1, projection_contract_version=None,
        embedded_source_sha256=master_sha, embedded_source_byte_length=1,
    )
    cov = views.CoverageDescriptor({("k%s" % key_suffix).encode("ascii"): views.CoverageResult(views.KNOWN)})
    token = views.LiveAuthorizationToken(master_sha)
    return views.DetachedView(sg, ai, cov, None, key_suffix, "fake_consumer_%s" % key_suffix, {}, token, estimated_bytes)


big_view = _make_fake_view("big", memory_accounting.RETAINED_PROMOTION_GATE_BYTES - 100)
cache2.admit(big_view)
check("eviction.1 a view within the gate admits successfully", cache2.entry_count() == 1)

small_view = _make_fake_view("small", 1000)
try:
    cache2.admit(small_view)
    admitted_by_eviction = True
except errors.ViewAdmissionRefused:
    admitted_by_eviction = False
# big_view is unpinned and NOT stale -- admission must evict it (redundant/oldest) to make room.
check("eviction.2 admitting a new view under pressure evicts an unpinned old view rather than refusing outright",
      admitted_by_eviction and cache2.entry_count() == 1, (admitted_by_eviction, cache2.entry_count()))

ledger3 = memory_accounting.AggregateLedger()
cache3 = view_cache_mod.ViewCache(ledger3)
pinned_view = _make_fake_view("pinned", memory_accounting.RETAINED_PROMOTION_GATE_BYTES - 100)
pinned_view.pinned = True
cache3.admit(pinned_view)
too_big_view = _make_fake_view("toobig", 1000)
try:
    cache3.admit(too_big_view)
    check("eviction.3 a pinned view is NEVER evicted; admission refuses when only pinned views remain", False, "did not raise")
except errors.ViewAdmissionRefused:
    check("eviction.3 a pinned view is NEVER evicted; admission refuses when only pinned views remain", True)

ledger4 = memory_accounting.AggregateLedger()
cache4 = view_cache_mod.ViewCache(ledger4)
stale_view = _make_fake_view("stale", memory_accounting.RETAINED_PROMOTION_GATE_BYTES - 100)
cache4.admit(stale_view)
stale_view.authorization.invalidate()
fresh_view = _make_fake_view("fresh", 1000)
cache4.admit(fresh_view)
check("eviction.4 a stale (invalidated) view is preferentially evicted before an unpinned-but-live one",
      cache4.entry_count() == 1 and cache4.get(fresh_view.cache_key()) is not None)


# ===========================================================================
# SECTION: cache key / reuse
# ===========================================================================
print("=== Cache key / reuse ===")

view_norm = _make_fake_view("norm", 100)
view_norm.consumer_kind = "normalizer"
view_csp = _make_fake_view("norm", 100)  # same coverage-key-suffix, DIFFERENT consumer_kind
view_csp.consumer_kind = "character_preset"
check("cachekey.1 same generation/coverage but different consumer_kind -> DIFFERENT cache keys",
      view_norm.cache_key() != view_csp.cache_key())

view_a_gen = _make_fake_view("g", 100, master_sha=REAL_MASTER_SHA)
view_b_gen = _make_fake_view("g", 100, master_sha="0" * 64)
check("cachekey.2 different semantic generation (master_sha256) -> different cache key",
      view_a_gen.cache_key() != view_b_gen.cache_key())

view_same_1 = _make_fake_view("same", 100)
view_same_2 = _make_fake_view("same", 100)
check("cachekey.3 identical generation+coverage+consumer_kind -> IDENTICAL cache key (would collide/reuse)",
      view_same_1.cache_key() == view_same_2.cache_key())


# ===========================================================================
# SECTION: same-source / different-artifact (REAL fixture, not simulated)
# ===========================================================================
print("=== Same-source / different-artifact (real fixture) ===")

check("sameSource.0 fixture artifacts are genuinely byte-different", ARTIFACT_A_SHA != ARTIFACT_B_SHA)

b10 = fresh_broker()
detached10 = b10.acquire_cohort(REAL_MASTER_PATH, {"normalizer": normalizer_builder()},
                                 shipped_root=SHIPPED_TWO_ARTIFACTS)
view10 = detached10["normalizer"]
selected_artifact_sha = view10.artifact_identity.sidecar_artifact_sha256
check("sameSource.1 a real acquisition selected ONE of the two real, valid, byte-different shipped artifacts",
      selected_artifact_sha in (ARTIFACT_A_SHA, ARTIFACT_B_SHA), selected_artifact_sha)
check("sameSource.2 semantic generation still equals the real Master SHA regardless of which artifact was picked",
      view10.semantic_generation.master_sha256 == REAL_MASTER_SHA)

# Prove the cache/broker never conflates A and B: two views built directly
# against each real artifact (bypassing selection to force a specific one)
# must carry DISTINCT artifact identities while sharing ONE semantic
# generation.
identity_a = sidecar_contract.validate_selected_artifact(
    os.path.join(SHIPPED_TWO_ARTIFACTS, "artifact_a.sfmsidecar"), REAL_MASTER_SHA)
identity_b = sidecar_contract.validate_selected_artifact(
    os.path.join(SHIPPED_TWO_ARTIFACTS, "artifact_b.sfmsidecar"), REAL_MASTER_SHA)
check("sameSource.3 artifact A and B validate independently to their OWN distinct artifact SHAs",
      identity_a.sidecar_artifact_sha256 != identity_b.sidecar_artifact_sha256)
check("sameSource.4 both share the identical embedded_source_sha256 (same semantic generation)",
      identity_a.embedded_source_sha256 == identity_b.embedded_source_sha256 == REAL_MASTER_SHA)


# ===========================================================================
# SECTION: source-generation invalidation
# ===========================================================================
print("=== Source-generation invalidation ===")

b11 = fresh_broker()
detached_gen_a = b11.acquire_cohort(REAL_MASTER_PATH, {"normalizer": normalizer_builder()}, shipped_root=SHIPPED_TWO_ARTIFACTS)
view_gen_a = detached_gen_a["normalizer"]
check("invalidation.1 freshly-acquired view's authorization is valid", view_gen_a.authorization.is_valid())

# Simulate a later acquisition observing a DIFFERENT generation (fixture --
# never touches the real production Master) by directly invoking the
# broker's own invalidation sweep, exactly as acquire_cohort() would after
# observing a changed master_sha256.
b11._view_cache.invalidate_generation(REAL_MASTER_SHA)
check("invalidation.2 invalidate_generation() marks the cached view's authorization invalid",
      not view_gen_a.authorization.is_valid())
check("invalidation.3 the view's PAYLOAD remains readable for diagnosis after invalidation (bytes not freed)",
      view_gen_a.payload is not None and "lookup_results" in view_gen_a.payload)
try:
    view_gen_a.authorization.require_valid("a new mutation")
    check("invalidation.4 require_valid() raises ViewInvalidated for a new mutation attempt", False, "did not raise")
except errors.ViewInvalidated:
    check("invalidation.4 require_valid() raises ViewInvalidated for a new mutation attempt", True)
check("invalidation.5 cache.get() refuses to hand out the now-stale view",
      b11._view_cache.get(view_gen_a.cache_key()) is None)


# ===========================================================================
# SECTION: repeated view reuse does not reopen provider when coverage suffices
# ===========================================================================
print("=== Reuse without reopening provider ===")

b12 = fresh_broker()
folded_norm = frozenset(projections._ascii_fold(l) for l in REAL_LITERALS)
folded_csp = frozenset(projections._ascii_fold(l) for l in REAL_CSP_VOCAB)
specs = {
    "normalizer": (folded_norm, projections.build_normalizer_like_projection(REAL_LITERALS)),
    "csp": (folded_csp, projections.build_character_preset_like_projection(REAL_CSP_VOCAB)),
}
r1 = b12.acquire_or_reuse_views(REAL_MASTER_PATH, specs, shipped_root=SHIPPED_TWO_ARTIFACTS)
counters_r1 = b12.provider_counters()
check("reuse.1 first request opens exactly one provider", counters_r1["total_provider_opens"] == 1, counters_r1)

r2 = b12.acquire_or_reuse_views(REAL_MASTER_PATH, specs, shipped_root=SHIPPED_TWO_ARTIFACTS)
counters_r2 = b12.provider_counters()
check("reuse.2 identical second request reuses cached views WITHOUT opening a second provider",
      counters_r2["total_provider_opens"] == 1, counters_r2)
check("reuse.3 the reused views are the SAME objects as the first acquisition (true cache hit)",
      r2["normalizer"] is r1["normalizer"] and r2["csp"] is r1["csp"])

# Uncovered vocabulary -> a genuinely new cohort, provider opens (and closes) again.
new_literal = "Left PupilRound"  # real, but not in the original request set
specs_new = dict(specs)
specs_new["normalizer"] = (
    frozenset(projections._ascii_fold(l) for l in REAL_LITERALS + [new_literal]),
    projections.build_normalizer_like_projection(REAL_LITERALS + [new_literal]),
)
r3 = b12.acquire_or_reuse_views(REAL_MASTER_PATH, specs_new, shipped_root=SHIPPED_TWO_ARTIFACTS)
counters_r3 = b12.provider_counters()
check("reuse.4 newly-uncovered vocabulary triggers a fresh cohort (provider opens again)",
      counters_r3["total_provider_opens"] == 2, counters_r3)
check("reuse.5 provider closes again after the new cohort (current count back to 0)",
      counters_r3["current_open_provider_count"] == 0, counters_r3)
check("reuse.6 the csp view (still covered) was reused, not rebuilt, even within the new-vocabulary call",
      r3["csp"] is r1["csp"])


print()
failed = [n for n, ok in results if not ok]
print("RESULT: %d/%d %s" % (len(results) - len(failed), len(results), "ALL PASS" if not failed else "FAILED: %r" % (failed,)))
if failed:
    sys.exit(1)
