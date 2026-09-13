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
    # C2.1 -- repeated request, no owner-level cross-action cache
    # (Round 3 Repair F: the C2 `_EpochCoverage` reusable positive/
    # negative cache was REMOVED. A repeated identical request now always
    # re-resolves against the already-admitted provider -- intentionally
    # not optimized in this repair -- but must still produce a
    # semantically identical result, and must not cause a second
    # admission/provider allocation.)
    # -----------------------------------------------------------------
    section("C2.1 -- repeated request without an owner-level cache (Round3 Repair F)")
    so._reset_registry_for_testing()
    ns1 = make_namespace_identity(source_sha256, "-c21")
    owner1 = make_owner(ns1)

    t0 = time.perf_counter()
    lease_a1, view_a1 = owner1.acquire_view("ConsumerA", folds_A, _PE)
    t_first = time.perf_counter() - t0
    admissions_after_first = owner1.admission_success_count
    providers_after_first = owner1.provider_allocation_count

    owner1.release_lease(lease_a1)

    t0 = time.perf_counter()
    lease_a2, view_a2 = owner1.acquire_view("ConsumerA2", folds_A, _PE)
    t_second = time.perf_counter() - t0

    check("C2.1 provider allocation count unchanged (one provider still shared across requests)",
          owner1.provider_allocation_count == providers_after_first,
          "before=%d after=%d" % (providers_after_first, owner1.provider_allocation_count))
    check("C2.1 admission count unchanged (lazy admission still happens exactly once)",
          owner1.admission_success_count == admissions_after_first,
          "before=%d after=%d" % (admissions_after_first, owner1.admission_success_count))
    check("C2.1 repeated request produces a semantically identical payload (re-resolved, not cached)",
          payload_digest(view_a1.payload) == payload_digest(view_a2.payload))
    print("  (timing, informational only -- Repair F intentionally removed the reuse-hit "
          "fast path) first=%.5fs second=%.5fs" % (t_first, t_second))
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
    # C2.3 -- positive / proven-negative / uncovered distinction WITHIN
    # one action view (Round 3 Repair F coverage contract). There is no
    # owner-level cross-action cache any more, so "uncovered" is no
    # longer a cross-call cache state -- it is simply any fold not
    # included in THIS action's `wanted_folds`. A global negative is
    # never inferred from a fold's absence in some OTHER view.
    # -----------------------------------------------------------------
    section("C2.3 -- positive / proven-negative / uncovered within one view")
    so._reset_registry_for_testing()
    ns3 = make_namespace_identity(source_sha256, "-c23")
    owner3 = make_owner(ns3)
    sorted_folds_a = sorted(folds_A)
    POS = sorted_folds_a[0]
    UNREQUESTED = sorted_folds_a[1]  # a real fold, deliberately never requested by this action
    NEG1 = cp.ascii_fold_unicode("Gate_C2_Neg_Sentinel_One_999")

    lease3, view3 = owner3.acquire_view("ConsumerMixed", {POS, NEG1}, _PE)
    check("C2.3 requested positive fold appears in folded", POS in view3.payload["folded"])
    check("C2.3 requested proven-negative fold is in proven_negative_folds, never in folded (never a false positive)",
          NEG1 in view3.payload["proven_negative_folds"] and NEG1 not in view3.payload["folded"])
    check("C2.3 a fold this action never requested is in neither collection (no inferred global negative)",
          UNREQUESTED not in view3.payload["folded"] and UNREQUESTED not in view3.payload["proven_negative_folds"])
    owner3.release_lease(lease3)

    # Repeated identical negative request: re-resolved (no cache), but
    # must remain a true absence, never an invented positive.
    lease3b, view3b = owner3.acquire_view("ConsumerMixed2", {NEG1}, _PE)
    check("C2.3 repeated negative request remains a true absence (re-resolved against the provider, not cached)",
          NEG1 in view3b.payload["proven_negative_folds"] and NEG1 not in view3b.payload["folded"])
    owner3.release_lease(lease3b)

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
        check("C2.4.B too-small family budget refused before publishing, no partial view published",
              len(owner4b._views) == 0, repr(exc))

    # -----------------------------------------------------------------
    # C2.5 -- snapshot/pinned-view budget atomicity
    # -----------------------------------------------------------------
    section("C2.5 -- snapshot/pinned-view budget atomicity")
    so._reset_registry_for_testing()
    ns5 = make_namespace_identity(source_sha256, "-c25")
    # This test is about family-row/pinned-byte budgeting specifically
    # (Repair H's separate per-fold accounting overhead is exercised in
    # its own dedicated section), so the per-view/per-fold overhead is
    # explicitly zeroed to preserve this test's original row-based
    # calibration.
    small_budgets = so.ViewBudgets(one_family_result_rows=5000, one_snapshot_rows=1000,
                                    total_pinned_bytes=2500, estimated_bytes_per_row=20,
                                    per_view_fixed_overhead_bytes=0, per_requested_fold_overhead_bytes=0)
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
    # REMOVED (Round 3 Repair F): the "Cache eviction -- performance only,
    # never truth" section and the "Gate C2R -- enforced coverage-cache
    # bound (FIFO eviction)" section that used to appear here both tested
    # the owner-level `_EpochCoverage` cache, which no longer exists --
    # there is nothing left at the owner level to evict or bound. See
    # SFM_MASTER_SIDECAR_ROUND3_FOUNDATION_SIMPLIFICATION_REPAIR_AUDIT.md
    # for the removal rationale. The PROVIDER's own decode-cache bound
    # (a different mechanism, Repair G) is exercised in the new section
    # immediately below.
    # -----------------------------------------------------------------

    # -----------------------------------------------------------------
    # Round 3 Repair G -- provider decode-cache bound enforced on every
    # acquire_view path (ordinary, refused, injected-failure).
    # -----------------------------------------------------------------
    section("Round3 Repair G -- provider decode-cache bound enforced on every path")
    so._reset_registry_for_testing()
    ns8 = make_namespace_identity(source_sha256, "-c2decodebound")
    tiny_decode_budgets = so.ViewBudgets(
        one_family_result_rows=5000, one_snapshot_rows=5000, total_pinned_bytes=100_000_000,
        estimated_bytes_per_row=256, decode_cache_estimated_bytes_budget=64,  # deliberately tiny
    )
    owner8 = make_owner(ns8, budgets=tiny_decode_budgets)

    lease8a, view8a = owner8.acquire_view("ConsumerOrdinary", folds_A, _PE)
    check("Repair G: decode cache bound enforced after an ordinary request",
          owner8.provider.string_cache_estimated_bytes() <= tiny_decode_budgets.decode_cache_estimated_bytes_budget,
          "estimated=%d budget=%d" % (
              owner8.provider.string_cache_estimated_bytes(), tiny_decode_budgets.decode_cache_estimated_bytes_budget,
          ))
    digest_after_bound_enforced = payload_digest(view8a.payload)
    check("Repair G: held action view remains valid after decode-cache eviction",
          payload_digest(owner8.get_view_via_lease(lease8a).payload) == digest_after_bound_enforced)
    owner8.release_lease(lease8a)

    # Reuses the large-family fixture (500 occurrences for one fold, from
    # C2.4) rather than folds_A, so the family-row refusal is guaranteed
    # to trigger regardless of how many single-occurrence folds folds_A
    # happens to contain.
    ns8b = so.NamespaceIdentity(
        source_path="large_family_fixture", source_sha256=lf_meta["source_sha256"],
        artifact_sha256="test-lf-decodebound", format_version=0, authority_version=0,
        profile_version="normalizer-v1-groupfile-no-backslash-decodebound",
    )
    strict_family_budgets = so.ViewBudgets(
        one_family_result_rows=1, one_snapshot_rows=5000, total_pinned_bytes=100_000_000,
        estimated_bytes_per_row=256, decode_cache_estimated_bytes_budget=64,
    )
    owner8b = so.get_or_create_owner(
        ns8b, lf_artifact_path, sufficient_snapshot, so.GuardPolicy.provisional_default(),
        strict_family_budgets, bounded_provider, bounded_view,
    )
    try:
        owner8b.acquire_view("ConsumerRefused", {big_fold}, _PE)
        check("Repair G setup: refusal actually occurred", False, "did not raise")
    except so.ResourceRefused:
        check("Repair G: decode cache bound enforced after a refused (over-budget) request",
              owner8b.provider.string_cache_estimated_bytes() <= strict_family_budgets.decode_cache_estimated_bytes_budget,
              "estimated=%d" % owner8b.provider.string_cache_estimated_bytes())

    ns8c = make_namespace_identity(source_sha256, "-c2decodeboundfault")
    owner8c = make_owner(ns8c, budgets=tiny_decode_budgets)

    class _InjectedDecodeFault(Exception):
        pass

    def fault_after_first(resolved_count, fold_key):
        if resolved_count == 1:
            raise _InjectedDecodeFault("qualification-only injected failure")

    try:
        owner8c.acquire_view("ConsumerFaulted", folds_A, _PE, fault_injector=fault_after_first)
        check("Repair G setup: injected fault actually occurred", False, "did not raise")
    except _InjectedDecodeFault:
        check("Repair G: decode cache bound enforced after an injected candidate failure",
              owner8c.provider.string_cache_estimated_bytes() <= tiny_decode_budgets.decode_cache_estimated_bytes_budget,
              "estimated=%d" % owner8c.provider.string_cache_estimated_bytes())

    # -----------------------------------------------------------------
    # Round 3 Repair H -- action-view accounting must charge negative-only
    # views a nonzero amount, and must charge mixed positive+negative
    # views more than the equivalent positive-only content.
    # -----------------------------------------------------------------
    section("Round3 Repair H -- action-view accounting charges negative-only views")
    so._reset_registry_for_testing()
    ns9 = make_namespace_identity(source_sha256, "-c2negacct")
    owner9 = make_owner(ns9)
    NEGX = cp.ascii_fold_unicode("Gate_Round3_NegAcct_Sentinel")
    NEGY = cp.ascii_fold_unicode("Gate_Round3_NegAcct_Sentinel_2")
    pos_fold = sorted(folds_A)[0]

    lease9pos, view9pos = owner9.acquire_view("ConsumerPosOnly", {pos_fold}, _PE)
    positive_only_bytes = view9pos.accounted_bytes
    owner9.release_lease(lease9pos)

    lease9neg, view9neg = owner9.acquire_view("ConsumerNegOnly", {NEGX}, _PE)
    check("Repair H: negative-only view has nonzero accounted size", view9neg.accounted_bytes > 0,
          "accounted_bytes=%d" % view9neg.accounted_bytes)

    lease9mixed, view9mixed = owner9.acquire_view("ConsumerMixedAcct", {pos_fold, NEGY}, _PE)
    check("Repair H: mixed positive+negative accounting exceeds equivalent positive-only accounting",
          view9mixed.accounted_bytes > positive_only_bytes,
          "mixed=%d positive_only=%d" % (view9mixed.accounted_bytes, positive_only_bytes))

    before_release_pinned = owner9.total_pinned_view_bytes()
    owner9.release_lease(lease9neg)
    check("Repair H: release drops pinned accounting", owner9.total_pinned_view_bytes() < before_release_pinned)
    owner9.release_lease(lease9mixed)

    ns9b = make_namespace_identity(source_sha256, "-c2negacctrefuse")
    tiny_pinned_budgets = so.ViewBudgets(one_family_result_rows=5000, one_snapshot_rows=5000,
                                          total_pinned_bytes=1, estimated_bytes_per_row=256)
    owner9b = make_owner(ns9b, budgets=tiny_pinned_budgets)
    try:
        owner9b.acquire_view("ConsumerNegTinyBudget", {NEGX}, _PE)
        check("Repair H: negative-only view under a deliberately tiny budget is refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("Repair H: negative-only view under a deliberately tiny budget is refused", True, repr(exc))

    # -----------------------------------------------------------------
    # Round 3 Repair I -- detached action-view mutation isolation.
    # -----------------------------------------------------------------
    section("Round3 Repair I -- detached action-view mutation isolation")
    so._reset_registry_for_testing()
    ns10 = make_namespace_identity(source_sha256, "-c2detach")
    owner10 = make_owner(ns10)
    detach_fold = sorted(folds_A)[0]

    lease_a10, view_a10 = owner10.acquire_view("ConsumerDetachA", {detach_fold}, _PE)
    lease_b10, view_b10 = owner10.acquire_view("ConsumerDetachB", {detach_fold}, _PE)
    digest_b_before_mutation = payload_digest(view_b10.payload)

    view_a10.payload["folded"][detach_fold][0]["literal"] = "MUTATED_BY_TEST"
    view_a10.payload["folded"][detach_fold].append({
        "literal": "INJECTED", "destination": "x", "global_index": -1, "local_index": -1,
    })

    check("Repair I: mutating view A's rows does not affect view B",
          payload_digest(view_b10.payload) == digest_b_before_mutation)

    owner10.release_lease(lease_a10)
    lease_c10, view_c10 = owner10.acquire_view("ConsumerDetachC", {detach_fold}, _PE)
    check("Repair I: after releasing mutated A, reacquiring C returns authoritative unmutated data",
          payload_digest(view_c10.payload) == digest_b_before_mutation)
    owner10.release_lease(lease_b10)
    owner10.release_lease(lease_c10)

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
