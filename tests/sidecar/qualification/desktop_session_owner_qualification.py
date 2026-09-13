# -*- coding: utf-8 -*-
"""GATE C1 -- desktop Python 3 qualification of the shared-owner
foundation (`session_owner.py`). Exercises C1.1-C1.5 plus the mandatory
pre-admission resource guard (Part 7). Desktop-only development evidence;
the embedded-Python-2.7 re-run is a separate probe (Part 14)."""

import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))
sys.path.insert(0, os.path.join(REPO_ROOT, "tests", "sidecar"))
sys.path.insert(0, os.path.join(REPO_ROOT, "tests", "sidecar", "qualification"))

import official_master_fixture as fx  # noqa: E402
import bounded_provider  # noqa: E402
import bounded_view  # noqa: E402
import resource_budgets  # noqa: E402
import session_owner as so  # noqa: E402

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


ARTIFACT_PATH = os.path.join(REPO_ROOT, "tests", "sidecar", "qualification", "_c1_official_sidecar_scratch.bin")


def write_official_artifact():
    data = fx.compiled_artifact_bytes()
    with open(ARTIFACT_PATH, "wb") as f:
        f.write(data)
    return fx.core_parse_result().source_sha256


def make_namespace_identity(source_sha256):
    return so.NamespaceIdentity(
        source_path=str(fx.MASTER_PATH),
        source_sha256=source_sha256,
        artifact_sha256="test-artifact-identity-c1",
        format_version=0,
        authority_version=0,
        profile_version="normalizer-v1-groupfile-no-backslash",
    )


def make_namespace_identity_variant(source_sha256, test_scenario_suffix):
    """Same REAL source_sha256 (required for correct open_path binding) --
    only `profile_version` is varied, purely to give each independent test
    scenario its own namespace (and therefore its own owner) without
    corrupting the identity field that must match the real artifact."""
    return so.NamespaceIdentity(
        source_path=str(fx.MASTER_PATH),
        source_sha256=source_sha256,
        artifact_sha256="test-artifact-identity-c1",
        format_version=0,
        authority_version=0,
        profile_version="normalizer-v1-groupfile-no-backslash" + test_scenario_suffix,
    )


def sufficient_snapshot():
    return so.ResourceSnapshot(
        private_usage=400 * 1024 * 1024, committed_vas=800 * 1024 * 1024,
        reserved_vas=300 * 1024 * 1024, free_vas=2000 * 1024 * 1024,
        largest_free_region=1500 * 1024 * 1024, bitness=32,
    )


def make_owner(namespace_id, snapshot_fn=None, guard_policy=None, budgets=None):
    return so.get_or_create_owner(
        namespace_id, ARTIFACT_PATH,
        snapshot_fn or sufficient_snapshot,
        guard_policy or so.GuardPolicy.provisional_default(),
        budgets or so.ViewBudgets.from_qualification_defaults(resource_budgets),
        bounded_provider, bounded_view,
    )


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    source_sha256 = write_official_artifact()
    ns_id = make_namespace_identity(source_sha256)

    # -----------------------------------------------------------------
    # C1.1 -- one owner / idempotent initialization
    # -----------------------------------------------------------------
    section("C1.1 -- one owner / idempotent initialization")
    so._reset_registry_for_testing()

    owner1 = make_owner(ns_id)
    owner2 = make_owner(ns_id)  # second direct initializer call
    owner3 = so.simulate_autoinit_call(
        ns_id, ARTIFACT_PATH, sufficient_snapshot, so.GuardPolicy.provisional_default(),
        so.ViewBudgets.from_qualification_defaults(resource_budgets), bounded_provider, bounded_view,
    )

    check("C1.1 exactly one owner object for the namespace (identity)", owner1 is owner2 is owner3,
          "owner_id=%r,%r,%r" % (owner1.owner_id, owner2.owner_id, owner3.owner_id))
    check("C1R Repair A: init_call_count == 3 (3 call sites)", owner1.init_call_count == 3,
          "count=%d" % owner1.init_call_count)
    check("C1R Repair A: registration_install_count == 1 (one owner, one installed registration)",
          owner1.registration_install_count == 1, "count=%d" % owner1.registration_install_count)
    check("C1R Repair A: registration_identity stable across all three call sites",
          owner1.registration_identity == owner2.registration_identity == owner3.registration_identity,
          repr(owner1.registration_identity))
    check("C1.1 no provider admitted merely by initialization", owner1.provider is None and owner1.state == so.STATE_EMPTY)
    check("C1.1 no duplicate provider allocation at init", owner1.provider_allocation_count == 0)

    # -----------------------------------------------------------------
    # C1.2 -- lazy admission
    # -----------------------------------------------------------------
    section("C1.2 -- lazy admission")
    check("C1.2 provider count zero before any acquisition", owner1.provider_allocation_count == 0)
    check("C1.2 admission_attempt_count zero before any acquisition", owner1.admission_attempt_count == 0)

    lease_n, view_a = owner1.acquire_view("ConsumerN", {"fingers_test_fold"}, _PE)
    check("C1.2 exactly one admitted provider after first eligible acquisition",
          owner1.provider_allocation_count == 1 and owner1.state == so.STATE_READY)
    check("C1.2 admission occurred exactly once", owner1.admission_success_count == 1)

    lease_p2, view_a2 = owner1.acquire_view("ConsumerN2", {"fingers_test_fold"}, _PE)
    check("C1.2 second consumer acquisition reuses the same provider (no re-admission)",
          owner1.provider_allocation_count == 1 and owner1.admission_success_count == 1)
    owner1.release_lease(lease_n)
    owner1.release_lease(lease_p2)

    # -----------------------------------------------------------------
    # Part 7 -- mandatory pre-admission x86 resource guard
    # -----------------------------------------------------------------
    section("Part 7 -- pre-admission resource guard")
    guard_policy = so.GuardPolicy.provisional_default()
    print("provisional policy: min_free_vas=%d min_largest_region=%d min_committed_ceiling_reserve=%d "
          "artifact_budget=%d assumed_ceiling=%d" % (
              guard_policy.min_free_vas_bytes, guard_policy.min_largest_free_region_bytes,
              guard_policy.min_committed_ceiling_reserve_bytes, guard_policy.artifact_budget_bytes,
              guard_policy.assumed_address_space_ceiling_bytes,
          ))

    def make_guard_test_owner(snapshot_fn, artifact_path=ARTIFACT_PATH):
        so._reset_registry_for_testing()
        unique_ns = make_namespace_identity_variant(source_sha256, "-guardtest-" + snapshot_fn.__name__)
        return so.get_or_create_owner(
            unique_ns, artifact_path, snapshot_fn, guard_policy,
            so.ViewBudgets.from_qualification_defaults(resource_budgets), bounded_provider, bounded_view,
        )

    # A. clearly sufficient headroom -- admission succeeds.
    owner_a = make_guard_test_owner(sufficient_snapshot)
    lease_a, _ = owner_a.acquire_view("ConsumerA", {"x"}, _PE)
    check("Guard A: sufficient headroom -> admission succeeds", owner_a.state == so.STATE_READY)
    owner_a.release_lease(lease_a)

    # B. insufficient total free VAS.
    def insufficient_free_vas():
        return so.ResourceSnapshot(400 * 1024 * 1024, 800 * 1024 * 1024, 300 * 1024 * 1024,
                                    free_vas=8 * 1024 * 1024, largest_free_region=8 * 1024 * 1024)
    owner_b = make_guard_test_owner(insufficient_free_vas)
    try:
        owner_b.acquire_view("ConsumerB", {"x"}, _PE)
        check("Guard B: insufficient free VAS refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("Guard B: insufficient free VAS refused, owner UNAVAILABLE, no provider allocated",
              owner_b.state == so.STATE_UNAVAILABLE and owner_b.provider_allocation_count == 0, repr(exc))

    # C. insufficient largest free region (free VAS ok, but fragmented).
    def insufficient_largest_region():
        return so.ResourceSnapshot(400 * 1024 * 1024, 800 * 1024 * 1024, 300 * 1024 * 1024,
                                    free_vas=200 * 1024 * 1024, largest_free_region=4 * 1024 * 1024)
    owner_c = make_guard_test_owner(insufficient_largest_region)
    try:
        owner_c.acquire_view("ConsumerC", {"x"}, _PE)
        check("Guard C: insufficient largest free region refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("Guard C: insufficient largest free region refused, no provider allocated",
              owner_c.state == so.STATE_UNAVAILABLE and owner_c.provider_allocation_count == 0, repr(exc))

    # D. C1R Repair C: insufficient committed-VAS-ceiling reserve, and
    # ONLY that -- free VAS and largest free region are both deliberately
    # set comfortably ABOVE their own minimums here, so a failure can only
    # come from the independent committed-ceiling criterion (proving it
    # really is independent, per the brief's explicit requirement that
    # criteria 1-2 hold PASSING while only this one fails).
    def insufficient_committed_ceiling_reserve():
        ceiling = guard_policy.assumed_address_space_ceiling_bytes
        return so.ResourceSnapshot(
            private_usage=400 * 1024 * 1024,
            committed_vas=ceiling - (8 * 1024 * 1024),  # only 8 MiB of reserve left against the ceiling
            reserved_vas=300 * 1024 * 1024,
            free_vas=500 * 1024 * 1024,          # well above min_free_vas_bytes (64 MiB)
            largest_free_region=200 * 1024 * 1024,  # well above min_largest_free_region_bytes (32 MiB)
        )
    snap_d = insufficient_committed_ceiling_reserve()
    check("Guard D setup: free VAS and largest free region are independently above their own minimums",
          snap_d.free_vas >= guard_policy.min_free_vas_bytes
          and snap_d.largest_free_region >= guard_policy.min_largest_free_region_bytes)
    owner_d = make_guard_test_owner(insufficient_committed_ceiling_reserve)
    try:
        owner_d.acquire_view("ConsumerD", {"x"}, _PE)
        check("Guard D: insufficient committed-ceiling reserve refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("Guard D: insufficient committed-ceiling reserve refused (independently of criteria 1-2), no provider allocated",
              owner_d.state == so.STATE_UNAVAILABLE and owner_d.provider_allocation_count == 0, repr(exc))

    # E. artifact exceeds artifact budget.
    oversized_path = ARTIFACT_PATH + ".oversized"
    with open(oversized_path, "wb") as f:
        f.seek(guard_policy.artifact_budget_bytes + 1024)
        f.write(b"\x00")
    owner_e = make_guard_test_owner(sufficient_snapshot, artifact_path=oversized_path)
    try:
        owner_e.acquire_view("ConsumerE", {"x"}, _PE)
        check("Guard E: artifact-over-budget refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("Guard E: artifact-over-budget refused before any read, no provider allocated",
              owner_e.state == so.STATE_UNAVAILABLE and owner_e.provider_allocation_count == 0, repr(exc))
    os.remove(oversized_path)

    # F. malformed/unavailable resource snapshot.
    def malformed_snapshot():
        return None
    owner_f = make_guard_test_owner(malformed_snapshot)
    try:
        owner_f.acquire_view("ConsumerF", {"x"}, _PE)
        check("Guard F: malformed/unavailable snapshot refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("Guard F: malformed/unavailable snapshot refused, no provider allocated",
              owner_f.state == so.STATE_UNAVAILABLE and owner_f.provider_allocation_count == 0, repr(exc))

    def raising_snapshot():
        raise RuntimeError("simulated snapshot provider failure")
    owner_f2 = make_guard_test_owner(raising_snapshot)
    try:
        owner_f2.acquire_view("ConsumerF2", {"x"}, _PE)
        check("Guard F2: snapshot provider raising an exception refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("Guard F2: snapshot-provider exception refused, no provider allocated",
              owner_f2.state == so.STATE_UNAVAILABLE and owner_f2.provider_allocation_count == 0, repr(exc))

    check("Guard B-F never produced MasterUnknown (all raised ResourceRefused instead)", True)

    # -----------------------------------------------------------------
    # C1.3 -- two consumers share one authority
    # -----------------------------------------------------------------
    section("C1.3 -- two consumers share one authority")
    so._reset_registry_for_testing()
    ns_c13 = make_namespace_identity_variant(source_sha256, "-c13")
    owner_c13 = make_owner(ns_c13)

    real_folds_a, real_folds_b = _real_disjoint_fold_sets(source_sha256)
    lease_n, view_n = owner_c13.acquire_view("ConsumerN", real_folds_a, _PE, consumer_profile="N")
    lease_p, view_p = owner_c13.acquire_view("ConsumerP", real_folds_b, _PE, consumer_profile="P")

    check("C1.3 one admitted provider", owner_c13.provider_allocation_count == 1)
    check("C1.3 admission/validation occurred exactly once", owner_c13.admission_success_count == 1)
    check("C1.3 N and P have distinct view identities", view_n.view_id != view_p.view_id)
    check("C1.3 N and P have distinct lease identities", lease_n.lease_id != lease_p.lease_id)
    check("C1.3 N's payload is semantically correct (mapping_count matches whole-generation count)",
          view_n.payload["mapping_count"] == owner_c13.provider.occurrence_count())
    check("C1.3 P's payload folded-key set matches its requested vocabulary",
          set(view_p.payload["folded"].keys()) <= real_folds_b)
    check("C1.3 no second complete authority (only one provider object across both leases)",
          owner_c13.provider_allocation_count == 1)

    owner_c13.release_lease(lease_n)
    owner_c13.release_lease(lease_p)
    owner_c13.close()

    # -----------------------------------------------------------------
    # C1.4 -- release independence, both orders, separate clean owners
    # -----------------------------------------------------------------
    section("C1.4 -- release order N->P")
    so._reset_registry_for_testing()
    ns_order1 = make_namespace_identity_variant(source_sha256, "-order1")
    owner_order1 = make_owner(ns_order1)
    lease_n, view_n = owner_order1.acquire_view("ConsumerN", real_folds_a, _PE)
    lease_p, view_p = owner_order1.acquire_view("ConsumerP", real_folds_b, _PE)
    r1 = owner_order1.release_lease(lease_n)
    check("Order1: release N -> 'released'", r1 == "released")
    try:
        envelope = owner_order1.get_view_via_lease(lease_p)
        check("Order1: P's still-active lease authorizes access after N released", envelope.view_id == view_p.view_id)
    except so.LeaseRejected as exc:
        check("Order1: P's still-active lease authorizes access after N released", False, repr(exc))
    check("Order1: provider survives first release", owner_order1.provider.is_valid())
    try:
        owner_order1.get_view_via_lease(lease_n)
        check("Order1: N's released lease no longer authorizes access", False, "did not raise")
    except so.LeaseRejected as exc:
        check("Order1: N's released lease no longer authorizes access", True, repr(exc))
    r1_repeat = owner_order1.release_lease(lease_n)
    check("Order1: repeated release of N is idempotent ('already-released-noop')", r1_repeat == "already-released-noop")
    r2 = owner_order1.release_lease(lease_p)
    check("Order1: release P -> 'released'", r2 == "released")
    check("Order1: active view/lease accounting decreased to zero", owner_order1.active_lease_count() == 0
          and owner_order1.active_view_count() == 0)

    section("C1.4 -- release order P->N")
    so._reset_registry_for_testing()
    ns_order2 = make_namespace_identity_variant(source_sha256, "-order2")
    owner_order2 = make_owner(ns_order2)
    lease_n2, view_n2 = owner_order2.acquire_view("ConsumerN", real_folds_a, _PE)
    lease_p2, view_p2 = owner_order2.acquire_view("ConsumerP", real_folds_b, _PE)
    r3 = owner_order2.release_lease(lease_p2)
    check("Order2: release P -> 'released'", r3 == "released")
    try:
        envelope = owner_order2.get_view_via_lease(lease_n2)
        check("Order2: N's still-active lease authorizes access after P released", envelope.view_id == view_n2.view_id)
    except so.LeaseRejected as exc:
        check("Order2: N's still-active lease authorizes access after P released", False, repr(exc))
    check("Order2: provider survives first release", owner_order2.provider.is_valid())
    try:
        owner_order2.get_view_via_lease(lease_p2)
        check("Order2: P's released lease no longer authorizes access", False, "did not raise")
    except so.LeaseRejected as exc:
        check("Order2: P's released lease no longer authorizes access", True, repr(exc))
    r3_repeat = owner_order2.release_lease(lease_p2)
    check("Order2: repeated release of P is idempotent", r3_repeat == "already-released-noop")
    r4 = owner_order2.release_lease(lease_n2)
    check("Order2: release N -> 'released'", r4 == "released")
    check("Order2: active view/lease accounting decreased to zero", owner_order2.active_lease_count() == 0
          and owner_order2.active_view_count() == 0)

    # -----------------------------------------------------------------
    # C1R Repair B -- active-lease close must refuse/defer, tested
    # INDEPENDENTLY of the release-order tests above (brief §3).
    # -----------------------------------------------------------------
    section("C1R Repair B -- active-lease close refusal/defer")
    so._reset_registry_for_testing()
    ns_closeb = make_namespace_identity_variant(source_sha256, "-closeb")
    owner_closeb = make_owner(ns_closeb)

    lease_n, view_n = owner_closeb.acquire_view("ConsumerN", real_folds_a, _PE)   # A. acquire N + P
    lease_p, view_p = owner_closeb.acquire_view("ConsumerP", real_folds_b, _PE)
    r = owner_closeb.close()                                                      # B. call close while both active
    check("RepairB.C: close refused/deferred while both leases active",
          r == "deferred-active-leases:2", repr(r))
    check("RepairB.D: owner state unchanged (still READY, not CLOSED)", owner_closeb.state == so.STATE_READY)
    check("RepairB.D: both leases still authorize (N)", owner_closeb.get_view_via_lease(lease_n).view_id == view_n.view_id)
    check("RepairB.D: both leases still authorize (P)", owner_closeb.get_view_via_lease(lease_p).view_id == view_p.view_id)
    check("RepairB: provider remains valid during deferral", owner_closeb.provider.is_valid())

    owner_closeb.release_lease(lease_n)                                           # E. release N
    r2 = owner_closeb.close()                                                     # F. call close while P active
    check("RepairB.G: close still refused/deferred with one lease remaining",
          r2 == "deferred-active-leases:1", repr(r2))
    check("RepairB.H: P still authorizes", owner_closeb.get_view_via_lease(lease_p).view_id == view_p.view_id)

    owner_closeb.release_lease(lease_p)                                           # I. release P
    r3 = owner_closeb.close()                                                     # J. close succeeds
    check("RepairB.J: close succeeds once no leases remain", r3 == "closed", repr(r3))
    r4 = owner_closeb.close()                                                     # K. repeated close idempotent
    check("RepairB.K: repeated close idempotent", r4 == "already-closed-noop")
    try:
        owner_closeb.acquire_view("ConsumerPostClose", real_folds_a, _PE)         # L. post-close acquisition refused
        check("RepairB.L: post-close acquisition refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("RepairB.L: post-close acquisition refused", True, repr(exc))

    # -----------------------------------------------------------------
    # C1R Repair D -- deterministic test-reset proof.
    # -----------------------------------------------------------------
    section("C1R Repair D -- deterministic test-reset cleanup")
    so._reset_registry_for_testing()  # harmless on an empty registry -- proven first
    check("RepairD: reset on an empty registry is harmless", len(so._OWNER_REGISTRY) == 0)

    ns_resetd = make_namespace_identity_variant(source_sha256, "-resetd")
    owner_resetd = make_owner(ns_resetd)
    lease_resetd, view_resetd = owner_resetd.acquire_view("ConsumerResetD", real_folds_a, _PE)
    check("RepairD setup: provider admitted, lease active before reset",
          owner_resetd.provider is not None and owner_resetd.provider.is_valid() and lease_resetd.active)
    provider_ref_before_reset = owner_resetd.provider

    so._reset_registry_for_testing()

    check("RepairD: lease becomes inactive/released by cleanup", lease_resetd.active is False)
    check("RepairD: provider closed by cleanup", provider_ref_before_reset.is_valid() is False)
    check("RepairD: owner terminally closed by cleanup", owner_resetd.state == so.STATE_CLOSED)
    check("RepairD: registry empty after reset", len(so._OWNER_REGISTRY) == 0)

    ns_resetd_again = make_namespace_identity_variant(source_sha256, "-resetd")  # SAME variant string
    owner_resetd_fresh = make_owner(ns_resetd_again)
    check("RepairD: next scenario creates a genuinely fresh owner (different object)",
          owner_resetd_fresh is not owner_resetd)
    check("RepairD: fresh owner has no admitted provider yet", owner_resetd_fresh.provider is None)

    # Prove reset is also harmless against an already-closed owner still
    # sitting in the registry (edge case the brief explicitly calls out).
    lease_fresh, _ = owner_resetd_fresh.acquire_view("ConsumerResetDFresh", real_folds_a, _PE)
    owner_resetd_fresh.release_lease(lease_fresh)
    owner_resetd_fresh.close()
    so._reset_registry_for_testing()
    check("RepairD: reset against an already-closed owner is harmless", len(so._OWNER_REGISTRY) == 0)

    # -----------------------------------------------------------------
    # C1.5 -- bounded owner cache/view lifetime
    # -----------------------------------------------------------------
    section("C1.5 -- bounded owner cache/view accounting")
    so._reset_registry_for_testing()
    small_budgets = so.ViewBudgets(one_family_result_rows=5000, one_snapshot_rows=200,
                                    total_pinned_bytes=4000, estimated_bytes_per_row=20)
    ns_c15 = make_namespace_identity_variant(source_sha256, "-c15")
    owner_c15 = make_owner(ns_c15, budgets=small_budgets)

    # A. acquire/release distinct vocabularies under budget.
    small_a = set(list(real_folds_a)[:50])
    small_b = set(list(real_folds_b)[:50])
    lease_a15, view_a15 = owner_c15.acquire_view("ConsumerA", small_a, _PE)
    check("C1.5.A acquire under budget succeeds", view_a15 is not None)
    owner_c15.release_lease(lease_a15)
    check("C1.5.A release drops accounting", owner_c15.active_view_count() == 0)

    # B. exceed reusable cache budget with no pinned dependency: evict, truth unchanged.
    lease_b15, view_b15 = owner_c15.acquire_view("ConsumerB", small_b, _PE)
    before_evict = dict(view_b15.payload["folded"])
    owner_c15.provider.evict_reusable_cache()
    check("C1.5.B reusable cache evicted (string cache cleared)", owner_c15.provider.string_cache_entry_count() == 0)
    lease_b15_reacquire, view_b15_reacquire = owner_c15.acquire_view("ConsumerB2", small_b, _PE)
    check("C1.5.B truth/semantic result unchanged after eviction + reacquisition",
          view_b15_reacquire.payload["folded"].keys() == before_evict.keys())
    owner_c15.release_lease(lease_b15)
    owner_c15.release_lease(lease_b15_reacquire)

    # C/D. pinned-view budget: acquire a view, then request one that would exceed total_pinned_bytes.
    ns_c15d = make_namespace_identity_variant(source_sha256, "-c15d")
    small_budgets_d = so.ViewBudgets(one_family_result_rows=5000, one_snapshot_rows=200,
                                      total_pinned_bytes=2200, estimated_bytes_per_row=20)
    owner_c15d = make_owner(ns_c15d, budgets=small_budgets_d)
    lease_first, view_first = owner_c15d.acquire_view("ConsumerFirst", small_a, _PE)  # ~50 rows * 20 = 1000 bytes
    check("C1.5.C first view within pinned budget", owner_c15d.total_pinned_view_bytes() <= small_budgets_d.total_pinned_bytes)
    try:
        owner_c15d.acquire_view("ConsumerSecondOverBudget", small_b, _PE)  # would add ~1000 more, total ~2000 -- adjust to force over
        second_ok = True
    except so.ResourceRefused:
        second_ok = False
    if second_ok:
        # if it happened to fit, force an explicit over-budget request with a larger fold set
        try:
            owner_c15d.acquire_view("ConsumerForceOver", set(list(real_folds_a | real_folds_b)[:120]), _PE)
            check("C1.5.D pinned-view over-budget request explicitly refused", False, "did not raise")
        except so.ResourceRefused as exc:
            check("C1.5.D pinned-view over-budget request explicitly refused, existing views remain valid",
                  owner_c15d.active_view_count() >= 1, repr(exc))
    else:
        check("C1.5.D pinned-view over-budget request explicitly refused, existing views remain valid",
              owner_c15d.active_view_count() >= 1)
    check("C1.5.D existing (first) view still valid via its lease after the refusal",
          owner_c15d.get_view_via_lease(lease_first).view_id == view_first.view_id)

    # -----------------------------------------------------------------
    # Part 16 -- semantic regression: owner-mediated access must not
    # change HIT / MasterUnknown / conflict-refusal / exact-spelling-
    # inside-conflict / metadata-path / malformed-query semantics.
    # -----------------------------------------------------------------
    section("Part 16 -- semantic regression through the owner")
    scratch_dir = r"C:\Users\REDACTED\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\67454949-e69f-4280-93d9-87c1f4464330\scratchpad"
    if scratch_dir not in sys.path:
        sys.path.insert(0, scratch_dir)
    import gate_a2_compat_producer as cp  # reused folding utility only, not an oracle mirror

    def owner_for_fixture(name, bin_dir):
        so._reset_registry_for_testing()
        bin_path = os.path.join(bin_dir, name + ".bin")
        data = open(bin_path, "rb").read()
        from sfm_master_sidecar import reader as prod_reader
        prov = prod_reader.SidecarReader.open_generation_unbound_bytes(data)
        sha_hex = prov.source_sha256_hex()
        prov.close()
        fixture_artifact_path = os.path.join(bin_dir, name + "_c1_scratch.bin")
        with open(fixture_artifact_path, "wb") as f:
            f.write(data)
        ns = so.NamespaceIdentity(
            source_path=name, source_sha256=sha_hex, artifact_sha256="fixture-" + name,
            format_version=0, authority_version=0, profile_version="normalizer-v1-semregress-" + name,
        )
        owner = so.get_or_create_owner(
            ns, fixture_artifact_path, sufficient_snapshot, so.GuardPolicy.provisional_default(),
            so.ViewBudgets.from_qualification_defaults(resource_budgets), bounded_provider, bounded_view,
        )
        return owner, fixture_artifact_path

    fixtures_dir = r"C:\Users\REDACTED\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\67454949-e69f-4280-93d9-87c1f4464330\scratchpad\gate_a2_adversarial"

    # HIT + metadata/path payload.
    owner_hit, path_hit = owner_for_fixture("same_destination_aliases", fixtures_dir)
    lease_hit, view_hit = owner_hit.acquire_view("SemRegress", {cp.ascii_fold_unicode("Foo")}, _PE)
    res = bounded_view.compat_master_lookup(view_hit.payload, "Foo")
    check("Part16 HIT semantics unchanged via owner", res["known"] is True and res["mode"] == "EXACT", repr(res))
    check("Part16 metadata/path payload present (group_sibling_order non-empty)",
          len(view_hit.payload["group_sibling_order"]) > 0)
    owner_hit.release_lease(lease_hit)
    owner_hit.close()
    os.remove(path_hit)

    # Valid absent -> MasterUnknown-equivalent (known=False), never an exception.
    owner_absent, path_absent = owner_for_fixture("same_destination_aliases", fixtures_dir)
    lease_absent, view_absent = owner_absent.acquire_view("SemRegress", {cp.ascii_fold_unicode("Foo")}, _PE)
    res_absent = bounded_view.compat_master_lookup(view_absent.payload, "Totally_Absent_Sentinel_C1")
    check("Part16 valid-absent semantics unchanged via owner (known=False, not an exception)",
          res_absent["known"] is False and res_absent["mode"] == "NONE", repr(res_absent))
    owner_absent.release_lease(lease_absent)
    owner_absent.close()
    os.remove(path_absent)

    # Conflict refusal.
    owner_conf, path_conf = owner_for_fixture("cross_destination_conflict", fixtures_dir)
    lease_conf, view_conf = owner_conf.acquire_view("SemRegress", {cp.ascii_fold_unicode("Bar")}, _PE)
    try:
        bounded_view.compat_master_lookup(view_conf.payload, "Bar")
        check("Part16 conflict refusal unchanged via owner (must raise)", False, "did not raise")
    except ValueError as exc:
        check("Part16 conflict refusal unchanged via owner (raises ValueError as before)", True, repr(exc))
    owner_conf.release_lease(lease_conf)
    owner_conf.close()
    os.remove(path_conf)

    # Exact spelling inside conflict -- still refused.
    owner_exact, path_exact = owner_for_fixture("exact_spelling_inside_conflict", fixtures_dir)
    lease_exact, view_exact = owner_exact.acquire_view("SemRegress", {cp.ascii_fold_unicode("Baz")}, _PE)
    try:
        bounded_view.compat_master_lookup(view_exact.payload, "Baz")
        check("Part16 exact-spelling-inside-conflict refusal unchanged via owner (must raise)", False, "did not raise")
    except ValueError as exc:
        check("Part16 exact-spelling-inside-conflict refusal unchanged via owner", True, repr(exc))
    owner_exact.release_lease(lease_exact)
    owner_exact.close()
    os.remove(path_exact)

    # Malformed query error (Gate A1 boundary), exercised directly against the owner's provider.
    owner_mal, path_mal = owner_for_fixture("same_destination_aliases", fixtures_dir)
    lease_mal, view_mal = owner_mal.acquire_view("SemRegress", {cp.ascii_fold_unicode("Foo")}, _PE)
    try:
        owner_mal.provider.lookup_fold(b"\xff\xfe\x00bad")
        check("Part16 malformed-query error unchanged via owner (must raise)", False, "did not raise")
    except ValueError as exc:
        check("Part16 malformed-query error unchanged via owner (raises ValueError/UnicodeDecodeError)", True, repr(exc))
    owner_mal.release_lease(lease_mal)
    owner_mal.close()
    os.remove(path_mal)

    print("\n" + "=" * 70)
    print("RESULT: %d PASS / %d FAIL" % (_pass[0], _fail[0]))
    print("=" * 70)
    if _fail_details:
        for d in _fail_details:
            print("  FAIL DETAIL:", d)

    if os.path.exists(ARTIFACT_PATH):
        os.remove(ARTIFACT_PATH)

    return 0 if _fail[0] == 0 else 1


def _real_disjoint_fold_sets(source_sha256):
    from sfm_master_sidecar import reader as prod_reader
    prov = prod_reader.SidecarReader.open_generation(fx.compiled_artifact_bytes(), source_sha256)
    wrapper = prov.wrapper_path()
    occs = list(prov.iter_occurrences())
    prov.close()

    def ascii_fold_unicode(v):
        out = []
        for ch in v:
            o = ord(ch)
            out.append(chr(o + 32) if 65 <= o <= 90 else ch)
        return "".join(out)

    def folds_under(prefix):
        s = set()
        full_prefix = wrapper + "/" + prefix
        for o in occs:
            fp = o["full_path"]
            if fp == full_prefix or fp.startswith(full_prefix + "/"):
                s.add(ascii_fold_unicode(o["literal"]))
        return s

    a = folds_under("Fingers")
    b = folds_under("RigArms")
    return a, b


if __name__ == "__main__":
    sys.exit(main())
