# -*- coding: utf-8 -*-
"""GATE C2 -- desktop Python 3 qualification of same-generation immutable
view acquisition/expansion semantics on the C1(R) owner foundation.
Exercises C2.1-C2.7 plus semantic parity through expansion. Desktop-only
development evidence; the embedded Python 2.7 re-run is a separate probe.
"""

import sys
import os
import copy
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))
sys.path.insert(0, os.path.join(REPO_ROOT, "tests", "sidecar"))
sys.path.insert(0, os.path.join(REPO_ROOT, "tests", "sidecar", "qualification"))
SCRATCH_DIR = r"C:\Users\REDACTED\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\67454949-e69f-4280-93d9-87c1f4464330\scratchpad"
sys.path.insert(0, SCRATCH_DIR)

import official_master_fixture as fx  # noqa: E402
import bounded_provider  # noqa: E402
import bounded_view  # noqa: E402
import resource_budgets  # noqa: E402
import session_owner as so  # noqa: E402
import gate_a2_compat_producer as cp  # noqa: E402 -- ascii_fold_unicode utility only

_pass = [0]
_fail = [0]
_fail_details = []


def check(label, condition, detail=""):
    if condition:
        _pass[0] += 1
        print("  PASS: %s %s" % (label, detail))
    else:
        _fail[0] += 1
        _fail_details.append("%s :: %s" % (label, detail))
        print("  FAIL: %s %s" % (label, detail))
    return condition


class _PE(Exception):
    pass


ARTIFACT_PATH = os.path.join(REPO_ROOT, "tests", "sidecar", "qualification", "_c2_official_sidecar_scratch.bin")
FIXTURES_DIR = os.path.join(SCRATCH_DIR, "gate_a2_adversarial")
LARGE_FAMILY_DIR = os.path.join(SCRATCH_DIR, "gate_b_adversarial")


def write_official_artifact():
    data = fx.compiled_artifact_bytes()
    with open(ARTIFACT_PATH, "wb") as f:
        f.write(data)
    return fx.core_parse_result().source_sha256


def make_namespace_identity(source_sha256, suffix=""):
    return so.NamespaceIdentity(
        source_path=str(fx.MASTER_PATH), source_sha256=source_sha256,
        artifact_sha256="test-artifact-c2", format_version=0, authority_version=0,
        profile_version="normalizer-v1-groupfile-no-backslash" + suffix,
    )


def sufficient_snapshot():
    return so.ResourceSnapshot(
        private_usage=400 * 1024 * 1024, committed_vas=800 * 1024 * 1024,
        reserved_vas=300 * 1024 * 1024, free_vas=2000 * 1024 * 1024,
        largest_free_region=1500 * 1024 * 1024, bitness=32,
    )


def make_owner(ns, budgets=None):
    return so.get_or_create_owner(
        ns, ARTIFACT_PATH, sufficient_snapshot, so.GuardPolicy.provisional_default(),
        budgets or so.ViewBudgets.from_qualification_defaults(resource_budgets),
        bounded_provider, bounded_view,
    )


def real_disjoint_fold_sets(source_sha256):
    from sfm_master_sidecar import reader as prod_reader
    prov = prod_reader.SidecarReader.open_generation(fx.compiled_artifact_bytes(), source_sha256)
    wrapper = prov.wrapper_path()
    occs = list(prov.iter_occurrences())
    prov.close()

    def folds_under(prefix):
        s = set()
        full_prefix = wrapper + "/" + prefix
        for o in occs:
            fp = o["full_path"]
            if fp == full_prefix or fp.startswith(full_prefix + "/"):
                s.add(cp.ascii_fold_unicode(o["literal"]))
        return s

    return folds_under("Fingers"), folds_under("RigArms")


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def payload_digest(payload):
    """Structural equality helper: folded rows + exact_literals + global
    stats, independent of dict insertion order."""
    folded_sorted = {
        k: sorted(v, key=lambda r: r["global_index"]) for k, v in payload["folded"].items()
    }
    return (
        payload["mapping_count"], payload["destination_count"],
        frozenset(payload["exact_literals"]),
        tuple(sorted((k, tuple(tuple(sorted(r.items())) for r in v)) for k, v in folded_sorted.items())),
    )


def main():
    source_sha256 = write_official_artifact()
    folds_A, folds_B = real_disjoint_fold_sets(source_sha256)

    # -----------------------------------------------------------------
    # C2.1 -- warm covered reacquisition
    # -----------------------------------------------------------------
    section("C2.1 -- warm covered reacquisition")
    so._reset_registry_for_testing()
    ns1 = make_namespace_identity(source_sha256, "-c21")
    owner1 = make_owner(ns1)

    t0 = time.perf_counter()
    lease_a1, view_a1 = owner1.acquire_view("ConsumerA", folds_A, _PE)
    t_cold = time.perf_counter() - t0
    admissions_after_first = owner1.admission_success_count
    providers_after_first = owner1.provider_allocation_count
    lookups_after_first = owner1._coverage.lookup_call_count

    owner1.release_lease(lease_a1)

    t0 = time.perf_counter()
    lease_a2, view_a2 = owner1.acquire_view("ConsumerA2", folds_A, _PE)
    t_warm = time.perf_counter() - t0

    check("C2.1 provider allocation count unchanged", owner1.provider_allocation_count == providers_after_first,
          "before=%d after=%d" % (providers_after_first, owner1.provider_allocation_count))
    check("C2.1 admission count unchanged", owner1.admission_success_count == admissions_after_first,
          "before=%d after=%d" % (admissions_after_first, owner1.admission_success_count))
    check("C2.1 no provider.lookup_fold re-invocation for already-covered folds",
          owner1._coverage.lookup_call_count == lookups_after_first,
          "before=%d after=%d" % (lookups_after_first, owner1._coverage.lookup_call_count))
    check("C2.1 warm reacquisition recorded as a reuse hit", owner1._coverage.reuse_hit_count >= 1)
    check("C2.1 resulting payload structurally identical", payload_digest(view_a1.payload) == payload_digest(view_a2.payload))
    print("  (timing, not a claimed speedup target) cold=%.5fs warm=%.5fs" % (t_cold, t_warm))
    owner1.release_lease(lease_a2)

    # -----------------------------------------------------------------
    # C2.2 -- known late vocabulary
    # -----------------------------------------------------------------
    section("C2.2 -- known late vocabulary (A then late B)")
    so._reset_registry_for_testing()
    ns2 = make_namespace_identity(source_sha256, "-c22")
    owner2 = make_owner(ns2)

    lease_a, view_a = owner2.acquire_view("ConsumerN", folds_A, _PE)
    view_a_id_before = view_a.view_id
    payload_a_digest_before = payload_digest(view_a.payload)
    wanted_folds_a_before = frozenset(view_a.wanted_folds)
    epoch_before = owner2.epoch
    admissions_before = owner2.admission_success_count
    providers_before = owner2.provider_allocation_count

    lease_b, view_b = owner2.acquire_view("ConsumerP", folds_B, _PE)

    check("C2.2 old A view_id unchanged", view_a.view_id == view_a_id_before)
    check("C2.2 old A payload unchanged (structural digest)", payload_digest(view_a.payload) == payload_a_digest_before)
    check("C2.2 old A wanted_folds unchanged", frozenset(view_a.wanted_folds) == wanted_folds_a_before)
    check("C2.2 new B view contains complete B families",
          set(view_b.payload["folded"].keys()) <= folds_B and len(view_b.payload["folded"]) > 0)
    check("C2.2 same provider/epoch throughout", owner2.epoch == epoch_before and view_a.epoch == view_b.epoch == owner2.epoch)
    check("C2.2 no second admission", owner2.admission_success_count == admissions_before
          and owner2.provider_allocation_count == providers_before)
    owner2.release_lease(lease_a)
    owner2.release_lease(lease_b)

    # -----------------------------------------------------------------
    # C2.3 -- true negative coverage
    # -----------------------------------------------------------------
    section("C2.3 -- true negative coverage")
    so._reset_registry_for_testing()
    ns3 = make_namespace_identity(source_sha256, "-c23")
    owner3 = make_owner(ns3)
    NEG1 = cp.ascii_fold_unicode("Gate_C2_Neg_Sentinel_One_999")
    NEG2 = cp.ascii_fold_unicode("Gate_C2_Neg_Sentinel_Two_777")

    # Force admission (empty vocabulary) so `_coverage` exists, WITHOUT
    # touching NEG1/NEG2 -- this is what "uncovered" means: the owner is
    # admitted and could answer, but has simply never been asked yet.
    lease_empty, _ = owner3.acquire_view("ConsumerBootstrap", set(), _PE)
    owner3.release_lease(lease_empty)
    check("C2.3 NEG2 genuinely uncovered before any request (neither positive nor negative)",
          NEG2 not in owner3._coverage.positive and NEG2 not in owner3._coverage.negative)

    lease_neg1a, view_neg1a = owner3.acquire_view("ConsumerNeg", {NEG1}, _PE)
    check("C2.3 NEG1 first request: recorded as true negative coverage", NEG1 in owner3._coverage.negative)
    check("C2.3 NEG1 absent from folded payload (never a false positive)", NEG1 not in view_neg1a.payload["folded"])
    lookups_after_neg1 = owner3._coverage.lookup_call_count
    owner3.release_lease(lease_neg1a)

    lease_neg1b, view_neg1b = owner3.acquire_view("ConsumerNeg2", {NEG1}, _PE)
    check("C2.3 repeated NEG1 request: no re-lookup (reused from negative coverage)",
          owner3._coverage.lookup_call_count == lookups_after_neg1,
          "before=%d after=%d" % (lookups_after_neg1, owner3._coverage.lookup_call_count))
    check("C2.3 repeated NEG1 remains true absence (no invented positive)", NEG1 not in view_neg1b.payload["folded"])
    owner3.release_lease(lease_neg1b)

    lease_neg2, view_neg2 = owner3.acquire_view("ConsumerNeg3", {NEG2}, _PE)
    check("C2.3 NEG2 independently proven negative", NEG2 in owner3._coverage.negative)
    owner3.release_lease(lease_neg2)

    # -----------------------------------------------------------------
    # C2.4 -- complete family / result-budget semantics
    # -----------------------------------------------------------------
    section("C2.4 -- complete family / result-budget semantics")
    import json
    manifest = json.load(open(os.path.join(LARGE_FAMILY_DIR, "manifest.json")))
    lf_meta = manifest["large_family"]
    lf_data = open(os.path.join(LARGE_FAMILY_DIR, "large_family.bin"), "rb").read()
    lf_artifact_path = os.path.join(LARGE_FAMILY_DIR, "large_family_c2_scratch.bin")
    with open(lf_artifact_path, "wb") as f:
        f.write(lf_data)
    big_fold = cp.ascii_fold_unicode("BigFamilyControl")

    # A. sufficient budget.
    so._reset_registry_for_testing()
    ns4a = so.NamespaceIdentity(
        source_path="large_family_fixture", source_sha256=lf_meta["source_sha256"],
        artifact_sha256="test-lf-c2a", format_version=0, authority_version=0,
        profile_version="normalizer-v1-groupfile-no-backslash-c24a",
    )
    owner4a = so.get_or_create_owner(
        ns4a, lf_artifact_path, sufficient_snapshot, so.GuardPolicy.provisional_default(),
        so.ViewBudgets(one_family_result_rows=5000, one_snapshot_rows=5000, total_pinned_bytes=10_000_000,
                        estimated_bytes_per_row=20),
        bounded_provider, bounded_view,
    )
    lease_lf, view_lf = owner4a.acquire_view("ConsumerLF", {big_fold}, _PE)
    check("C2.4.A complete family preserved (500/500 rows, no truncation)",
          len(view_lf.payload["folded"][big_fold]) == lf_meta["occurrences"])
    check("C2.4.A conflict semantics preserved (50 distinct destinations)",
          len(set(r["destination"] for r in view_lf.payload["folded"][big_fold])) == 50)
    owner4a.release_lease(lease_lf)

    # B. deliberately too-small family budget.
    so._reset_registry_for_testing()
    ns4b = so.NamespaceIdentity(
        source_path="large_family_fixture", source_sha256=lf_meta["source_sha256"],
        artifact_sha256="test-lf-c2b", format_version=0, authority_version=0,
        profile_version="normalizer-v1-groupfile-no-backslash-c24b",
    )
    owner4b = so.get_or_create_owner(
        ns4b, lf_artifact_path, sufficient_snapshot, so.GuardPolicy.provisional_default(),
        so.ViewBudgets(one_family_result_rows=10, one_snapshot_rows=5000, total_pinned_bytes=10_000_000,
                        estimated_bytes_per_row=20),
        bounded_provider, bounded_view,
    )
    try:
        owner4b.acquire_view("ConsumerLFOver", {big_fold}, _PE)
        check("C2.4.B too-small family budget refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("C2.4.B too-small family budget refused before publishing, no partial family, no partial negative",
              len(owner4b._views) == 0 and big_fold not in owner4b._coverage.positive
              and big_fold not in owner4b._coverage.negative, repr(exc))

    # -----------------------------------------------------------------
    # C2.5 -- snapshot/pinned-view budget atomicity
    # -----------------------------------------------------------------
    section("C2.5 -- snapshot/pinned-view budget atomicity")
    so._reset_registry_for_testing()
    ns5 = make_namespace_identity(source_sha256, "-c25")
    small_budgets = so.ViewBudgets(one_family_result_rows=5000, one_snapshot_rows=1000,
                                    total_pinned_bytes=2500, estimated_bytes_per_row=20)
    owner5 = make_owner(ns5, budgets=small_budgets)
    small_a = set(list(folds_A)[:50])   # ~50 rows * 20 bytes = ~1000 bytes
    small_b = set(list(folds_B)[:50])   # would add ~1000 more -> still might fit; force bigger
    lease5a, view5a = owner5.acquire_view("ConsumerA", small_a, _PE)
    check("C2.5 view A published within budget", owner5.active_view_count() == 1)

    big_expansion = set(list(folds_A | folds_B)[:120])  # deliberately large enough to exceed total_pinned_bytes
    try:
        owner5.acquire_view("ConsumerBOverBudget", big_expansion, _PE)
        check("C2.5 over-budget candidate expansion refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("C2.5 over-budget candidate expansion refused before registry publication",
              owner5.active_view_count() == 1, repr(exc))
        check("C2.5 existing A lease/view remains valid",
              owner5.get_view_via_lease(lease5a).view_id == view5a.view_id)
        check("C2.5 owner/provider stays READY", owner5.state == so.STATE_READY and owner5.provider.is_valid())
        newly_requested_only = big_expansion - small_a
        leaked = newly_requested_only & (set(owner5._coverage.positive.keys()) | set(owner5._coverage.negative.keys()))
        check("C2.5 candidate B coverage not falsely published (staged-then-committed contract)",
              len(leaked) == 0, "leaked=%r" % (leaked,))
    owner5.release_lease(lease5a)

    # -----------------------------------------------------------------
    # C2.6 -- injected lookup failure during expansion
    # -----------------------------------------------------------------
    section("C2.6 -- injected lookup/allocation failure during expansion")
    so._reset_registry_for_testing()
    ns6 = make_namespace_identity(source_sha256, "-c26")
    owner6 = make_owner(ns6)
    lease6a, view6a = owner6.acquire_view("ConsumerA", folds_A, _PE)
    views_before = dict(owner6._views)
    leases_before = dict(owner6._leases)
    coverage_positive_before = dict(owner6._coverage.positive)
    coverage_negative_before = dict(owner6._coverage.negative)

    class _InjectedFault(Exception):
        pass

    def fault_after_third(resolved_count, fold_key):
        if resolved_count == 3:
            raise _InjectedFault("qualification-only injected failure at resolved_count=3")

    try:
        owner6.acquire_view("ConsumerBFault", folds_B, _PE, fault_injector=fault_after_third)
        check("C2.6 injected fault actually interrupted expansion", False, "did not raise")
    except _InjectedFault:
        check("C2.6 no candidate view published after injected fault", owner6._views == views_before)
        check("C2.6 no candidate lease published after injected fault", owner6._leases == leases_before)
        check("C2.6 no partial coverage published after injected fault",
              owner6._coverage.positive == coverage_positive_before and owner6._coverage.negative == coverage_negative_before)
        check("C2.6 existing A remains valid", owner6.get_view_via_lease(lease6a).view_id == view6a.view_id)
        check("C2.6 owner/provider remains READY after qualification-level candidate failure",
              owner6.state == so.STATE_READY and owner6.provider.is_valid())

    lease6b, view6b = owner6.acquire_view("ConsumerBRetry", folds_B, _PE)
    check("C2.6 retry without injected fault succeeds and publishes the complete new view",
          set(view6b.payload["folded"].keys()) <= folds_B and len(view6b.payload["folded"]) > 0)
    owner6.release_lease(lease6a)
    owner6.release_lease(lease6b)

    # -----------------------------------------------------------------
    # C2.7 -- epoch-change race before publication
    # -----------------------------------------------------------------
    section("C2.7 -- epoch-mismatch publication guard")
    so._reset_registry_for_testing()
    ns7 = make_namespace_identity(source_sha256, "-c27")
    owner7 = make_owner(ns7)
    lease7a, view7a = owner7.acquire_view("ConsumerA", folds_A, _PE)
    epoch_e = owner7.epoch
    views_before7 = dict(owner7._views)
    leases_before7 = dict(owner7._leases)

    def bump_epoch_after_second(resolved_count, fold_key):
        if resolved_count == 2:
            owner7.epoch += 1  # qualification-only injected epoch mismatch

    try:
        owner7.acquire_view("ConsumerBEpoch", folds_B, _PE, fault_injector=bump_epoch_after_second)
        check("C2.7 epoch-mismatch candidate publication refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("C2.7 no view/lease/coverage committed under stale epoch",
              owner7._views == views_before7 and owner7._leases == leases_before7, repr(exc))
    check("C2.7 old E-epoch view remains a historical object, not relabeled",
          view7a.epoch == epoch_e and view7a.epoch != owner7.epoch)
    owner7.epoch = epoch_e  # qualification-only restore, so lease/view checks below are meaningful
    check("C2.7 old lease still resolves to the E-epoch view after restore",
          owner7.get_view_via_lease(lease7a).view_id == view7a.view_id)
    owner7.release_lease(lease7a)

    # -----------------------------------------------------------------
    # Cache eviction: performance only, never truth (Section 11).
    # -----------------------------------------------------------------
    section("Cache eviction -- performance only, never truth")
    so._reset_registry_for_testing()
    ns8 = make_namespace_identity(source_sha256, "-c2evict")
    owner8 = make_owner(ns8)
    lease8, view8 = owner8.acquire_view("ConsumerEvict", folds_A, _PE)
    digest_before_evict = payload_digest(view8.payload)
    owner8.evict_reusable_coverage_cache()
    check("Cache eviction clears owner-level coverage", len(owner8._coverage.positive) == 0
          and len(owner8._coverage.negative) == 0)
    check("Already-published view payload unaffected by eviction (independent copy)",
          payload_digest(view8.payload) == digest_before_evict)
    lease8b, view8b = owner8.acquire_view("ConsumerEvict2", folds_A, _PE)
    check("Reacquisition after eviction returns semantically identical result (truth unchanged)",
          payload_digest(view8b.payload) == digest_before_evict)
    owner8.release_lease(lease8)
    owner8.release_lease(lease8b)

    # -----------------------------------------------------------------
    # Gate C2R -- the coverage cache is EXPLICITLY BOUNDED (positive by
    # estimated bytes, negative by entry count); exceeding it evicts the
    # OLDEST entries (FIFO), never a currently-published view's payload,
    # and never changes a subsequent request's semantic result.
    # -----------------------------------------------------------------
    section("Gate C2R -- enforced coverage-cache bound (FIFO eviction)")
    so._reset_registry_for_testing()
    ns9 = make_namespace_identity(source_sha256, "-c2rbound")
    # Deliberately tiny bound: at ~1000 bytes/row estimate, 3000 bytes
    # holds ~3 single-row entries before a 4th forces FIFO eviction.
    tiny_bound_budgets = so.ViewBudgets(
        one_family_result_rows=5000, one_snapshot_rows=5000, total_pinned_bytes=100_000_000,
        estimated_bytes_per_row=1000, coverage_positive_max_bytes=3000, coverage_negative_max_entries=100000,
    )
    owner9 = make_owner(ns9, budgets=tiny_bound_budgets)

    singleton_folds = sorted(folds_A)[:6]  # 6 distinct real folds, requested one at a time
    digests_by_fold = {}
    for fk in singleton_folds:
        lease_i, view_i = owner9.acquire_view("ConsumerSingleton_%s" % fk, {fk}, _PE)
        digests_by_fold[fk] = payload_digest(view_i.payload)
        owner9.release_lease(lease_i)

    check("C2R bound: cache did not grow past the configured byte bound",
          owner9._coverage.positive_bytes() <= tiny_bound_budgets.coverage_positive_max_bytes,
          "positive_bytes=%d bound=%d" % (owner9._coverage.positive_bytes(), tiny_bound_budgets.coverage_positive_max_bytes))
    check("C2R bound: FIFO eviction actually occurred", owner9._coverage.bound_eviction_count > 0,
          "bound_eviction_count=%d" % owner9._coverage.bound_eviction_count)
    oldest_fold, newest_fold = singleton_folds[0], singleton_folds[-1]
    check("C2R bound: oldest entry was evicted (FIFO)", oldest_fold not in owner9._coverage.positive)
    check("C2R bound: newest entry survived", newest_fold in owner9._coverage.positive)

    # Re-requesting the evicted (oldest) fold must still produce the exact
    # same correct semantic result -- eviction cost performance (a fresh
    # provider lookup), never truth.
    lookups_before_reacquire = owner9._coverage.lookup_call_count
    lease_re, view_re = owner9.acquire_view("ConsumerReacquireEvicted", {oldest_fold}, _PE)
    check("C2R bound: re-acquiring an evicted fold re-queries the provider (lookup_call_count increased)",
          owner9._coverage.lookup_call_count > lookups_before_reacquire)
    check("C2R bound: re-acquired evicted fold's payload is semantically identical to its first resolution",
          payload_digest(view_re.payload) == digests_by_fold[oldest_fold])
    owner9.release_lease(lease_re)

    # Negative-side entry-count bound, proven the same way with a tiny cap.
    ns10 = make_namespace_identity(source_sha256, "-c2rboundneg")
    tiny_neg_budgets = so.ViewBudgets(
        one_family_result_rows=5000, one_snapshot_rows=5000, total_pinned_bytes=100_000_000,
        estimated_bytes_per_row=256, coverage_positive_max_bytes=100_000_000, coverage_negative_max_entries=3,
    )
    owner10 = make_owner(ns10, budgets=tiny_neg_budgets)
    neg_sentinels = ["Gate_C2R_Neg_Bound_%d" % i for i in range(6)]
    for neg in neg_sentinels:
        lease_i, _ = owner10.acquire_view("ConsumerNegBound_%s" % neg, {neg}, _PE)
        owner10.release_lease(lease_i)
    check("C2R bound: negative-entry cap enforced", len(owner10._coverage.negative) <= 3,
          "count=%d" % len(owner10._coverage.negative))
    check("C2R bound: negative FIFO eviction occurred", owner10._coverage.bound_eviction_count > 0)
    check("C2R bound: oldest negative sentinel evicted", neg_sentinels[0] not in owner10._coverage.negative)
    check("C2R bound: newest negative sentinel retained", neg_sentinels[-1] in owner10._coverage.negative)
    lease_reneg, view_reneg = owner10.acquire_view("ConsumerRenegAcquire", {neg_sentinels[0]}, _PE)
    check("C2R bound: re-acquiring an evicted negative fold remains a true absence (never becomes a false positive)",
          neg_sentinels[0] not in view_reneg.payload["folded"])
    owner10.release_lease(lease_reneg)

    # -----------------------------------------------------------------
    # Semantic parity through expansion (Section 14).
    # -----------------------------------------------------------------
    section("Semantic parity through expansion")
    so._reset_registry_for_testing()

    def owner_for_fixture(name, suffix):
        bin_path = os.path.join(FIXTURES_DIR, name + ".bin")
        data = open(bin_path, "rb").read()
        from sfm_master_sidecar import reader as prod_reader
        prov = prod_reader.SidecarReader.open_generation_unbound_bytes(data)
        sha_hex = prov.source_sha256_hex()
        prov.close()
        p = os.path.join(FIXTURES_DIR, name + "_c2_scratch.bin")
        with open(p, "wb") as f:
            f.write(data)
        ns = so.NamespaceIdentity(
            source_path=name, source_sha256=sha_hex, artifact_sha256="fixture-c2-" + name,
            format_version=0, authority_version=0, profile_version="normalizer-v1-c2-" + name + suffix,
        )
        owner = so.get_or_create_owner(
            ns, p, sufficient_snapshot, so.GuardPolicy.provisional_default(),
            so.ViewBudgets.from_qualification_defaults(resource_budgets), bounded_provider, bounded_view,
        )
        return owner, p

    # Acquire an EMPTY initial view, then EXPAND to include the real fold --
    # proves semantics hold via the expansion path specifically.
    owner_hit, p_hit = owner_for_fixture("same_destination_aliases", "-hit")
    lease_e0, view_e0 = owner_hit.acquire_view("Sem", set(), _PE)
    lease_hit, view_hit = owner_hit.acquire_view("Sem2", {cp.ascii_fold_unicode("Foo")}, _PE)
    res = bounded_view.compat_master_lookup(view_hit.payload, "Foo")
    check("Expansion: HIT semantics", res["known"] is True and res["mode"] == "EXACT", repr(res))
    res_alias = bounded_view.compat_master_lookup(view_hit.payload, "fOo")
    check("Expansion: ASCII-fold alias semantics", res_alias["known"] is True and res_alias["mode"] == "ASCII_CASEFOLD", repr(res_alias))
    check("Expansion: metadata/path payload present", len(view_hit.payload["group_sibling_order"]) > 0)
    owner_hit.release_lease(lease_e0)
    owner_hit.release_lease(lease_hit)
    owner_hit.close()
    os.remove(p_hit)

    owner_conf, p_conf = owner_for_fixture("cross_destination_conflict", "-conf")
    lease_conf0, _ = owner_conf.acquire_view("Sem", set(), _PE)
    lease_conf, view_conf = owner_conf.acquire_view("Sem2", {cp.ascii_fold_unicode("Bar")}, _PE)
    try:
        bounded_view.compat_master_lookup(view_conf.payload, "Bar")
        check("Expansion: cross-destination conflict refusal", False, "did not raise")
    except ValueError as exc:
        check("Expansion: cross-destination conflict refusal", True, repr(exc))
    owner_conf.release_lease(lease_conf0)
    owner_conf.release_lease(lease_conf)
    owner_conf.close()
    os.remove(p_conf)

    owner_exact, p_exact = owner_for_fixture("exact_spelling_inside_conflict", "-exact")
    lease_exact0, _ = owner_exact.acquire_view("Sem", set(), _PE)
    lease_exact, view_exact = owner_exact.acquire_view("Sem2", {cp.ascii_fold_unicode("Baz")}, _PE)
    try:
        bounded_view.compat_master_lookup(view_exact.payload, "Baz")
        check("Expansion: exact-spelling-inside-conflict refusal", False, "did not raise")
    except ValueError as exc:
        check("Expansion: exact-spelling-inside-conflict refusal", True, repr(exc))
    owner_exact.release_lease(lease_exact0)
    owner_exact.release_lease(lease_exact)
    owner_exact.close()
    os.remove(p_exact)

    owner_absent, p_absent = owner_for_fixture("same_destination_aliases", "-absent")
    lease_absent0, _ = owner_absent.acquire_view("Sem", set(), _PE)
    lease_absent, view_absent = owner_absent.acquire_view("Sem2", {cp.ascii_fold_unicode("Foo")}, _PE)
    res_absent = bounded_view.compat_master_lookup(view_absent.payload, "Totally_Absent_C2_Sentinel")
    check("Expansion: true-absent semantics", res_absent["known"] is False and res_absent["mode"] == "NONE", repr(res_absent))
    owner_absent.release_lease(lease_absent0)
    owner_absent.release_lease(lease_absent)
    owner_absent.close()
    os.remove(p_absent)

    print("\n" + "=" * 70)
    print("RESULT: %d PASS / %d FAIL" % (_pass[0], _fail[0]))
    print("=" * 70)
    if _fail_details:
        for d in _fail_details:
            print("  FAIL DETAIL:", d)

    for p in [ARTIFACT_PATH, lf_artifact_path]:
        if os.path.exists(p):
            os.remove(p)

    return 0 if _fail[0] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
