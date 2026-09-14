# -*- coding: utf-8 -*-
"""ROUND 3 -- desktop Python 3 qualification of the subtractive foundation
simplification/repair applied to `session_owner.py` after the Astra Round 3
holistic audit. This is the single focused Round 3 foundation harness
(brief section 13): it directly asserts every item on that checklist,
either with its own dedicated scenario (Repairs A, B, E, and the
cache-absence/repeated-lookup-correctness structural checks, which have no
prior coverage anywhere) or with one condensed confirming scenario for
items already covered in depth by the updated historical harnesses
(`desktop_session_owner_qualification.py` for the guard/init checks,
`desktop_view_expansion_qualification.py` for Repairs F/G/H/I and the
epoch-mismatch guard) -- so this file is a genuinely complete, self
-contained Round 3 PASS/FAIL record on its own, without silently
duplicating entire suites.

Desktop-only development evidence; the embedded Python 2.7 re-run is a
separate probe (brief section 14).
"""

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


ARTIFACT_PATH = os.path.join(REPO_ROOT, "tests", "sidecar", "qualification", "_round3_official_sidecar_scratch.bin")
FIXTURES_DIR = os.path.join(REPO_ROOT, "tests", "sidecar", "fixtures", "gate_a2_adversarial")


def write_official_artifact():
    data = fx.compiled_artifact_bytes()
    with open(ARTIFACT_PATH, "wb") as f:
        f.write(data)
    return fx.core_parse_result().source_sha256


def make_namespace_identity(source_sha256, suffix=""):
    return so.NamespaceIdentity(
        source_path=str(fx.MASTER_PATH), source_sha256=source_sha256,
        artifact_sha256="test-artifact-round3", format_version=0, authority_version=0,
        profile_version="normalizer-v1-groupfile-no-backslash" + suffix,
    )


def sufficient_snapshot():
    return so.ResourceSnapshot(
        private_usage=400 * 1024 * 1024, committed_vas=800 * 1024 * 1024,
        reserved_vas=300 * 1024 * 1024, free_vas=2000 * 1024 * 1024,
        largest_free_region=1500 * 1024 * 1024, bitness=32,
    )


def make_owner(ns, artifact_path=ARTIFACT_PATH, budgets=None, guard_policy=None, snapshot_fn=None):
    return so.get_or_create_owner(
        ns, artifact_path, snapshot_fn or sufficient_snapshot,
        guard_policy or so.GuardPolicy.provisional_default(),
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


def main():
    source_sha256 = write_official_artifact()
    folds_A, folds_B = real_disjoint_fold_sets(source_sha256)

    # -----------------------------------------------------------------
    # 3 init call sites -> 1 owner; lazy admission (condensed confirming
    # check -- full detail already in desktop_session_owner_qualification.py
    # C1.1/C1.2, updated for Round3 Repair C).
    # -----------------------------------------------------------------
    section("Round3 -- 3 init call sites -> 1 owner; lazy admission")
    so._reset_registry_for_testing()
    ns_init = make_namespace_identity(source_sha256, "-init")
    owner_i1 = make_owner(ns_init)
    owner_i2 = make_owner(ns_init)
    owner_i3 = so.simulate_autoinit_call(
        ns_init, ARTIFACT_PATH, sufficient_snapshot, so.GuardPolicy.provisional_default(),
        so.ViewBudgets.from_qualification_defaults(resource_budgets), bounded_provider, bounded_view,
    )
    check("3 init call sites -> exactly 1 owner object", owner_i1 is owner_i2 is owner_i3,
          "owner_id=%r,%r,%r" % (owner_i1.owner_id, owner_i2.owner_id, owner_i3.owner_id))
    check("init_call_count == 3 (no simulated registration-install claim tracked)",
          owner_i1.init_call_count == 3, "count=%d" % owner_i1.init_call_count)
    check("lazy admission: no provider before first acquire_view", owner_i1.provider is None)
    lease_lazy, _ = owner_i1.acquire_view("ConsumerLazy", {sorted(folds_A)[0]}, _PE)
    check("lazy admission: provider allocated exactly once after first acquisition",
          owner_i1.provider_allocation_count == 1)
    owner_i1.release_lease(lease_lazy)

    # -----------------------------------------------------------------
    # Repair A -- foreign-owner lease confusion.
    # -----------------------------------------------------------------
    section("Round3 Repair A -- foreign-owner lease rejection")
    so._reset_registry_for_testing()
    ns_a1 = make_namespace_identity(source_sha256, "-foreignA")
    ns_a2 = make_namespace_identity(source_sha256, "-foreignB")
    owner_fa = make_owner(ns_a1)
    owner_fb = make_owner(ns_a2)

    lease_fa, view_fa = owner_fa.acquire_view("ConsumerFA", {sorted(folds_A)[0]}, _PE)
    lease_fb, view_fb = owner_fb.acquire_view("ConsumerFB", {sorted(folds_A)[0]}, _PE)
    check("owner A and owner B independently issued lease ID 1",
          lease_fa.lease_id == 1 and lease_fb.lease_id == 1, "A=%r B=%r" % (lease_fa.lease_id, lease_fb.lease_id))

    try:
        owner_fb.get_view_via_lease(lease_fa)
        check("A's lease cannot authorize B", False, "did not raise")
    except so.LeaseRejected as exc:
        check("A's lease cannot authorize B", True, repr(exc))

    try:
        owner_fb.release_lease(lease_fa)
        check("A's lease cannot release/mutate B's lease", False, "did not raise")
    except so.LeaseRejected as exc:
        check("A's lease cannot release/mutate B's lease", True, repr(exc))

    check("B's lease remains valid after both foreign attempts",
          owner_fb.get_view_via_lease(lease_fb).view_id == view_fb.view_id)
    check("same-owner lease continues to work (A's own lease still authorizes A)",
          owner_fa.get_view_via_lease(lease_fa).view_id == view_fa.view_id)

    owner_fa.release_lease(lease_fa)
    try:
        owner_fa.get_view_via_lease(lease_fa)
        check("released same-owner lease is rejected", False, "did not raise")
    except so.LeaseRejected as exc:
        check("released same-owner lease is rejected", True, repr(exc))
    owner_fb.release_lease(lease_fb)

    # -----------------------------------------------------------------
    # Repair B -- bounded lease lifetime, terminal cleanup, registry
    # removal.
    # -----------------------------------------------------------------
    section("Round3 Repair B -- release/close/registry cleanup")
    so._reset_registry_for_testing()
    ns_b = make_namespace_identity(source_sha256, "-repairb")
    owner_b = make_owner(ns_b)

    lease_b1, view_b1 = owner_b.acquire_view("ConsumerB1", {sorted(folds_A)[0]}, _PE)
    lease_b2, view_b2 = owner_b.acquire_view("ConsumerB2", {sorted(folds_B)[0]}, _PE)

    r_close_deferred = owner_b.close()
    check("close with active leases is deferred", r_close_deferred == "deferred-active-leases:2", repr(r_close_deferred))
    check("owner state unchanged while deferred", owner_b.state == so.STATE_READY)

    owner_b.release_lease(lease_b1)
    check("release removes the owner-held record (no tombstone)", lease_b1.lease_id not in owner_b._leases)
    leases_before_repeat = len(owner_b._leases)
    r_repeat = owner_b.release_lease(lease_b1)
    check("repeated release of the same lease is a documented no-op", r_repeat == "already-released-noop")
    check("repeated release grows no central history", len(owner_b._leases) == leases_before_repeat)

    owner_b.release_lease(lease_b2)
    r_close_ok = owner_b.close()
    check("terminal close succeeds once zero leases remain", r_close_ok == "closed")
    check("terminal close: lease registry empty", len(owner_b._leases) == 0)
    check("terminal close: view registry empty", len(owner_b._views) == 0)
    check("terminal close: owner removed from the process registry",
          so._OWNER_REGISTRY.get(ns_b) is not owner_b)

    # A fresh get_or_create_owner call for the SAME namespace after close
    # must create a genuinely new owner, never resurrect the closed one.
    owner_b_fresh = make_owner(ns_b)
    check("a closed owner is never discoverable via the normal registry lookup",
          owner_b_fresh is not owner_b and owner_b_fresh.provider is None)

    # -----------------------------------------------------------------
    # Repair E -- missing-artifact admission failure and recovery.
    # -----------------------------------------------------------------
    section("Round3 Repair E -- missing-artifact admission failure/recovery")
    so._reset_registry_for_testing()
    ns_e = make_namespace_identity(source_sha256, "-repaire")
    missing_path = os.path.join(REPO_ROOT, "tests", "sidecar", "qualification", "_round3_missing_artifact.bin")
    if os.path.exists(missing_path):
        os.remove(missing_path)
    owner_e = make_owner(ns_e, artifact_path=missing_path)

    raised = False
    try:
        owner_e.acquire_view("ConsumerMissing", {sorted(folds_A)[0]}, _PE)
    except so.ResourceRefused as exc:
        raised = True
        check("missing artifact: acquire_view raises ResourceRefused, not an uncaught OSError", True, repr(exc))
    check("missing artifact: acquire_view raised (setup sanity)", raised)
    check("missing artifact: owner ends in recoverable UNAVAILABLE, not stuck in PREPARING",
          owner_e.state == so.STATE_UNAVAILABLE, "state=%r" % owner_e.state)
    check("missing artifact: no provider allocated", owner_e.provider is None and owner_e.provider_allocation_count == 0)
    check("missing artifact: no partial lease/view published",
          len(owner_e._leases) == 0 and len(owner_e._views) == 0)

    # Restore the artifact and retry: must return through PREPARING and succeed.
    data = fx.compiled_artifact_bytes()
    with open(missing_path, "wb") as f:
        f.write(data)
    lease_e_retry, view_e_retry = owner_e.acquire_view("ConsumerRetry", {sorted(folds_A)[0]}, _PE)
    check("restored artifact: retry succeeds", owner_e.state == so.STATE_READY)
    check("restored artifact: exactly one successful admission (the retry)", owner_e.admission_success_count == 1)
    owner_e.release_lease(lease_e_retry)
    owner_e.close()
    os.remove(missing_path)

    # -----------------------------------------------------------------
    # Reusable family/negative cache absent (structural confirmation);
    # repeated action lookup remains correct without it.
    # -----------------------------------------------------------------
    section("Round3 Repair F -- reusable cross-action cache is structurally absent")
    so._reset_registry_for_testing()
    ns_f = make_namespace_identity(source_sha256, "-repairf")
    owner_f = make_owner(ns_f)
    check("owner object has no _coverage attribute (removed, not merely emptied)",
          not hasattr(owner_f, "_coverage"))
    check("session_owner module defines no _EpochCoverage class any more",
          not hasattr(so, "_EpochCoverage"))
    lease_f1, view_f1 = owner_f.acquire_view("ConsumerRepeat1", {sorted(folds_A)[0]}, _PE)
    lease_f2, view_f2 = owner_f.acquire_view("ConsumerRepeat2", {sorted(folds_A)[0]}, _PE)
    check("repeated action lookup for the same fold across separate calls remains correct",
          view_f1.payload["folded"][sorted(folds_A)[0]] == view_f2.payload["folded"][sorted(folds_A)[0]])
    owner_f.release_lease(lease_f1)
    owner_f.release_lease(lease_f2)

    # -----------------------------------------------------------------
    # Guard: physically consistent fixtures; redundant 4th criterion
    # removed (condensed confirming check -- full detail in the updated
    # desktop_session_owner_qualification.py Part 7).
    # -----------------------------------------------------------------
    section("Round3 Repair D -- guard has exactly 3 criteria, all physically consistent")
    guard_policy = so.GuardPolicy.provisional_default()
    check("GuardPolicy no longer exposes a committed-ceiling criterion",
          not hasattr(guard_policy, "min_committed_ceiling_reserve_bytes")
          and not hasattr(guard_policy, "assumed_address_space_ceiling_bytes"))
    snap = sufficient_snapshot()
    total = snap.private_usage + snap.committed_vas + snap.reserved_vas + snap.free_vas
    check("provisional guard-test snapshot is physically consistent (<= 4 GiB assumed ceiling)",
          total <= 4 * 1024 * 1024 * 1024, "total=%d" % total)
    ok, reason = guard_policy.evaluate(snap, 1024)
    check("guard evaluates a consistent, sufficient snapshot as OK", ok, reason)

    # -----------------------------------------------------------------
    # Epoch-mismatch prevents publication (condensed confirming check --
    # full detail in the updated desktop_view_expansion_qualification.py
    # C2.7).
    # -----------------------------------------------------------------
    section("Round3 -- epoch-mismatch prevents publication")
    so._reset_registry_for_testing()
    ns_epoch = make_namespace_identity(source_sha256, "-repairepoch")
    owner_epoch = make_owner(ns_epoch)
    lease_ep_a, view_ep_a = owner_epoch.acquire_view("ConsumerEpochA", {sorted(folds_A)[0]}, _PE)
    views_before_epoch = dict(owner_epoch._views)

    def bump_epoch_after_first(resolved_count, fold_key):
        if resolved_count == 1:
            owner_epoch.epoch += 1

    try:
        owner_epoch.acquire_view("ConsumerEpochB", {sorted(folds_B)[0]}, _PE, fault_injector=bump_epoch_after_first)
        check("epoch-mismatch candidate publication refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("epoch-mismatch candidate publication refused, nothing published",
              owner_epoch._views == views_before_epoch, repr(exc))
    owner_epoch.epoch -= 1  # qualification-only restore
    check("pre-existing lease/view remains valid after the refused epoch-mismatched request",
          owner_epoch.get_view_via_lease(lease_ep_a).view_id == view_ep_a.view_id)
    owner_epoch.release_lease(lease_ep_a)

    # -----------------------------------------------------------------
    # Semantic parity: representative HIT / alias / conflict / absent /
    # metadata-rank path through the repaired owner.
    # -----------------------------------------------------------------
    section("Round3 -- semantic parity (HIT / alias / conflict / absent / metadata)")
    so._reset_registry_for_testing()

    def owner_for_fixture(name, suffix):
        bin_path = os.path.join(FIXTURES_DIR, name + ".bin")
        data = open(bin_path, "rb").read()
        from sfm_master_sidecar import reader as prod_reader
        prov = prod_reader.SidecarReader.open_generation_unbound_bytes(data)
        sha_hex = prov.source_sha256_hex()
        prov.close()
        p = os.path.join(FIXTURES_DIR, name + "_round3_scratch.bin")
        with open(p, "wb") as f:
            f.write(data)
        ns = so.NamespaceIdentity(
            source_path=name, source_sha256=sha_hex, artifact_sha256="fixture-round3-" + name,
            format_version=0, authority_version=0, profile_version="normalizer-v1-round3-" + name + suffix,
        )
        owner = so.get_or_create_owner(
            ns, p, sufficient_snapshot, so.GuardPolicy.provisional_default(),
            so.ViewBudgets.from_qualification_defaults(resource_budgets), bounded_provider, bounded_view,
        )
        return owner, p

    owner_hit, p_hit = owner_for_fixture("same_destination_aliases", "-hit")
    lease_hit, view_hit = owner_hit.acquire_view("SemParity", {cp.ascii_fold_unicode("Foo")}, _PE)
    res_hit = bounded_view.compat_master_lookup(view_hit.payload, "Foo")
    check("HIT semantics unchanged via the repaired owner", res_hit["known"] is True and res_hit["mode"] == "EXACT", repr(res_hit))
    res_alias = bounded_view.compat_master_lookup(view_hit.payload, "fOo")
    check("ASCII-fold alias semantics unchanged", res_alias["known"] is True and res_alias["mode"] == "ASCII_CASEFOLD", repr(res_alias))
    check("metadata/path payload present (group_sibling_order non-empty)", len(view_hit.payload["group_sibling_order"]) > 0)
    res_absent = bounded_view.compat_master_lookup(view_hit.payload, "Totally_Absent_Round3_Sentinel")
    check("valid-absent semantics unchanged (known=False, not an exception)",
          res_absent["known"] is False and res_absent["mode"] == "NONE", repr(res_absent))
    owner_hit.release_lease(lease_hit)
    owner_hit.close()
    os.remove(p_hit)

    owner_conf, p_conf = owner_for_fixture("cross_destination_conflict", "-conf")
    lease_conf, view_conf = owner_conf.acquire_view("SemParity", {cp.ascii_fold_unicode("Bar")}, _PE)
    try:
        bounded_view.compat_master_lookup(view_conf.payload, "Bar")
        check("cross-destination conflict refusal unchanged", False, "did not raise")
    except ValueError as exc:
        check("cross-destination conflict refusal unchanged", True, repr(exc))
    owner_conf.release_lease(lease_conf)
    owner_conf.close()
    os.remove(p_conf)

    print("\n" + "=" * 70)
    print("RESULT: %d PASS / %d FAIL" % (_pass[0], _fail[0]))
    print("=" * 70)
    if _fail_details:
        for d in _fail_details:
            print("  FAIL DETAIL:", d)

    if os.path.exists(ARTIFACT_PATH):
        os.remove(ARTIFACT_PATH)

    return 0 if _fail[0] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
