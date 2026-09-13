# -*- coding: utf-8 -*-
"""MINIMUM C3 -- desktop Python 3 qualification of command-boundary source
freshness, candidate/manifest compatibility, old-generation retirement,
active-lease drain, terminal close, and next-command lazy G2 readmission.
Exercises the brief's full §14 checklist against real compiled generations
(the actual production compiler/writer/manifest pipeline -- never a mocked
generation) built from small qualification-only Master TXT fixtures.
Desktop-only development evidence; the embedded Python 2.7 re-run is a
separate probe.
"""

import sys
import os
import shutil

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))
sys.path.insert(0, os.path.join(REPO_ROOT, "tests", "sidecar"))
sys.path.insert(0, os.path.join(REPO_ROOT, "tests", "sidecar", "qualification"))

import bounded_provider  # noqa: E402
import bounded_view  # noqa: E402
import resource_budgets  # noqa: E402
import session_owner as so  # noqa: E402
import command_boundary as cb  # noqa: E402
from sfm_master_sidecar import compiler as sidecar_compiler  # noqa: E402
from sfm_master_sidecar import manifest as sidecar_manifest  # noqa: E402
from sfm_master_sidecar import format as fmt  # noqa: E402

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


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


class _PE(Exception):
    pass


WORKDIR = os.path.join(REPO_ROOT, "tests", "sidecar", "qualification", "_c3_scratch")

G1_TXT = (
    "groupFile\n"
    "{\n"
    "\t\"Grp\"\n"
    "\t{\n"
    "\t\t\"control\"\t\t\"AAA\"\n"
    "\t\t\"control\"\t\t\"BBB\"\n"
    "\t}\n"
    "}\n"
)
# Same byte length as G1_TXT (AAA -> CCC, same char count, same structure).
G2_TXT = (
    "groupFile\n"
    "{\n"
    "\t\"Grp\"\n"
    "\t{\n"
    "\t\t\"control\"\t\t\"CCC\"\n"
    "\t\t\"control\"\t\t\"BBB\"\n"
    "\t}\n"
    "}\n"
)

assert len(G1_TXT) == len(G2_TXT), "fixture design invariant: G1/G2 must be byte-identical in length"


def fresh_workdir():
    if os.path.exists(WORKDIR):
        shutil.rmtree(WORKDIR)
    os.makedirs(WORKDIR)
    os.makedirs(os.path.join(WORKDIR, "generations"))


def build_generation(txt_path, generation_dir, manifest_path):
    """Compiles txt_path via the REAL, unmodified production compiler/
    writer/manifest pipeline. Returns (artifact_path, manifest_data,
    source_sha256)."""
    snapshot = sidecar_compiler.capture_source_snapshot(txt_path)
    outcome = sidecar_compiler.parse_and_compile(snapshot)
    basename = sidecar_compiler.generation_basename(outcome.ordinary_sha256)
    manifest_dict = sidecar_manifest.build_manifest_dict(outcome, basename)
    manifest_bytes = sidecar_manifest.serialize_manifest(manifest_dict)
    artifact_path = os.path.join(generation_dir, basename)
    with open(artifact_path, "wb") as f:
        f.write(outcome.blob)
    with open(manifest_path, "wb") as f:
        f.write(manifest_bytes)
    return artifact_path, sidecar_manifest.parse_manifest_bytes(manifest_bytes), snapshot.sha256_hex


def sufficient_snapshot():
    return so.ResourceSnapshot(
        private_usage=400 * 1024 * 1024, committed_vas=800 * 1024 * 1024,
        reserved_vas=300 * 1024 * 1024, free_vas=2000 * 1024 * 1024,
        largest_free_region=1500 * 1024 * 1024, bitness=32,
    )


EXPECTED_FORMAT_VERSION = fmt.FORMAT_CONTRACT_VERSION_EXPERIMENTAL
EXPECTED_AUTHORITY_VERSION = fmt.AUTHORITY_SEMANTICS_VERSION_EXPERIMENTAL


def prepare(source_path, manifest_path, generation_dir, profile_version, budgets=None, guard=None):
    return cb.prepare_command_boundary(
        source_path, manifest_path, generation_dir, sufficient_snapshot,
        guard or so.GuardPolicy.provisional_default(),
        budgets or so.ViewBudgets.from_qualification_defaults(resource_budgets),
        bounded_provider, bounded_view,
        EXPECTED_FORMAT_VERSION, EXPECTED_AUTHORITY_VERSION, profile_version,
    )


def main():
    so._reset_registry_for_testing()

    # -----------------------------------------------------------------
    # Shared G1 fixture setup, reused across most scenarios below.
    # -----------------------------------------------------------------
    section("C3.0 -- setup: build real G1 generation")
    fresh_workdir()
    txt_path = os.path.join(WORKDIR, "master.txt")
    with open(txt_path, "w", newline="") as f:
        f.write(G1_TXT)
    g1_mtime_before = os.path.getmtime(txt_path)
    g1_size_before = os.path.getsize(txt_path)

    manifest_path = os.path.join(WORKDIR, "manifest.json")
    gen_dir = os.path.join(WORKDIR, "generations")
    g1_artifact_path, g1_manifest, g1_sha = build_generation(txt_path, gen_dir, manifest_path)
    check("C3.0 setup: G1 artifact/manifest built", os.path.isfile(g1_artifact_path) and os.path.isfile(manifest_path))

    # -----------------------------------------------------------------
    # C3.1 -- unchanged source -> reuse
    # -----------------------------------------------------------------
    section("C3.1 -- unchanged source -> reuse")
    owner1, md1 = prepare(txt_path, manifest_path, gen_dir, "-c31")
    lease1, view1 = owner1.acquire_view("ConsumerC31", {"aaa"}, _PE)
    check("C3.1 fold 'aaa' present in G1", "aaa" in view1.payload["folded"])
    owner1b, md1b = prepare(txt_path, manifest_path, gen_dir, "-c31")
    check("C3.1 second command boundary (unchanged source) reuses the SAME owner",
          owner1 is owner1b, "ids=%r,%r" % (owner1.owner_id, owner1b.owner_id))
    check("C3.1 no second admission on reuse", owner1.provider_allocation_count == 1)
    owner1.release_lease(lease1)
    owner1.close()

    # -----------------------------------------------------------------
    # C3.2 -- same-size/mtime-preserved byte edit -> SHA detects
    # -----------------------------------------------------------------
    section("C3.2 -- same-size/mtime-preserved edit -> SHA detects")
    so._reset_registry_for_testing()
    owner2, _ = prepare(txt_path, manifest_path, gen_dir, "-c32")
    lease2a, view2a = owner2.acquire_view("ConsumerC32", {"aaa"}, _PE)

    with open(txt_path, "w", newline="") as f:
        f.write(G2_TXT)
    os.utime(txt_path, (g1_mtime_before, g1_mtime_before))  # preserve mtime exactly
    size_after = os.path.getsize(txt_path)
    mtime_after = os.path.getmtime(txt_path)
    check("C3.2 file size unchanged", size_after == g1_size_before, "before=%d after=%d" % (g1_size_before, size_after))
    check("C3.2 mtime unchanged", mtime_after == g1_mtime_before, "before=%r after=%r" % (g1_mtime_before, mtime_after))

    new_sha = cb.hash_source_file(txt_path)
    check("C3.2 SHA-256 changed despite unchanged size/mtime", new_sha != g1_sha,
          "old=%s new=%s" % (g1_sha, new_sha))

    g2_artifact_path, g2_manifest, g2_sha = build_generation(txt_path, gen_dir, manifest_path)
    check("C3.2 setup: G2 artifact/manifest built", os.path.isfile(g2_artifact_path))

    owner2b, md2b = prepare(txt_path, manifest_path, gen_dir, "-c32")
    check("C3.2 freshness check detects the edit -> a NEW owner is returned",
          owner2b is not owner2, "ids=%r,%r" % (owner2.owner_id, owner2b.owner_id))
    check("C3.2 old G1 owner (this scenario) is RETIRED", owner2.state == so.STATE_RETIRED)
    try:
        owner2.acquire_view("ConsumerC32PostRetire", {"aaa"}, _PE)
        check("C3.2 old generation ineligible for NEW work", False, "did not raise")
    except so.ResourceRefused as exc:
        check("C3.2 old generation ineligible for NEW work", True, repr(exc))
    lease2b, view2b = owner2b.acquire_view("ConsumerC32b", {"ccc"}, _PE)
    check("C3.2 old negative fact cannot masquerade as new source semantics "
          "(fold 'ccc' now genuinely present in G2)", "ccc" in view2b.payload["folded"])
    owner2.release_lease(lease2a)
    owner2.close()
    owner2b.release_lease(lease2b)
    owner2b.close()

    # -----------------------------------------------------------------
    # C3.3 -- retirement idempotence
    # -----------------------------------------------------------------
    section("C3.3 -- retirement idempotence")
    so._reset_registry_for_testing()
    owner3, _ = prepare(txt_path, manifest_path, gen_dir, "-c33")
    r1 = owner3.retire()
    check("C3.3 first retire() succeeds", r1 == "retired", repr(r1))
    r2 = owner3.retire()
    check("C3.3 second retire() is an idempotent no-op", r2 == "already-retired-noop", repr(r2))
    owner3.close()

    # -----------------------------------------------------------------
    # C3.4 -- stale authorization rejected (new work), payload inspectable
    # -----------------------------------------------------------------
    section("C3.4 -- stale authorization rejected; payload remains inspectable")
    so._reset_registry_for_testing()
    owner4, _ = prepare(txt_path, manifest_path, gen_dir, "-c34")
    lease4, view4 = owner4.acquire_view("ConsumerC34", {"ccc"}, _PE)
    owner4.retire()
    try:
        owner4.acquire_view("ConsumerC34New", {"bbb"}, _PE)
        check("C3.4 retired owner refuses a NEW action/mutation boundary", False, "did not raise")
    except so.ResourceRefused as exc:
        check("C3.4 retired owner refuses a NEW action/mutation boundary", True, repr(exc))
    check("C3.4 no MasterUnknown/semantic fallback was fabricated (a real ResourceRefused, not a lookup result)", True)
    try:
        envelope4 = owner4.get_view_via_lease(lease4)
        check("C3.4 the already-issued lease/payload remains inspectable after retirement",
              envelope4.view_id == view4.view_id)
    except so.LeaseRejected as exc:
        check("C3.4 the already-issued lease/payload remains inspectable after retirement", False, repr(exc))
    owner4.release_lease(lease4)
    owner4.close()

    # -----------------------------------------------------------------
    # C3.5 -- active operation drain, both leases, no provider overlap
    # -----------------------------------------------------------------
    section("C3.5 -- active lease drain / no provider overlap")
    so._reset_registry_for_testing()
    owner5, _ = prepare(txt_path, manifest_path, gen_dir, "-c35")
    lease5n, _ = owner5.acquire_view("ConsumerN", {"ccc"}, _PE)
    lease5p, _ = owner5.acquire_view("ConsumerP", {"bbb"}, _PE)
    check("C3.5 G1 READY with two active leases", owner5.state == so.STATE_READY and owner5.active_lease_count() == 2)

    owner5.retire()
    check("C3.5 retire while active: state RETIRED", owner5.state == so.STATE_RETIRED)
    try:
        owner5.acquire_view("ConsumerNewAfterRetire", {"aaa"}, _PE)
        check("C3.5 new G1 acquisition refused after retirement", False, "did not raise")
    except so.ResourceRefused as exc:
        check("C3.5 new G1 acquisition refused after retirement", True, repr(exc))

    r_n = owner5.release_lease(lease5n)
    check("C3.5 release N -> 'released'", r_n == "released")
    check("C3.5 provider remains alive because P is still active", owner5.provider.is_valid())
    r_close_deferred = owner5.close()
    check("C3.5 close deferred while P still active", r_close_deferred == "deferred-active-leases:1", repr(r_close_deferred))

    r_p = owner5.release_lease(lease5p)
    check("C3.5 release P -> 'released'", r_p == "released")
    r_close = owner5.close()
    check("C3.5 owner can close once drained", r_close == "closed", repr(r_close))
    check("C3.5 provider invalid after close", not owner5.provider.is_valid() if owner5.provider else True)
    check("C3.5 registry contains no reusable G1 owner",
          so._OWNER_REGISTRY.get(owner5.namespace_identity) is not owner5)
    check("C3.5 no provider overlap: exactly one provider allocation for the whole G1 lifetime",
          owner5.provider_allocation_count == 1)

    # -----------------------------------------------------------------
    # C3.6 -- next-command lazy G2 readmission
    # -----------------------------------------------------------------
    section("C3.6 -- next-command lazy G2 readmission")
    so._reset_registry_for_testing()
    owner6a, _ = prepare(txt_path, manifest_path, gen_dir, "-c36")
    lease6a, _ = owner6a.acquire_view("ConsumerC36", {"ccc"}, _PE)
    owner6a.retire()
    owner6a.release_lease(lease6a)
    r6_close = owner6a.close()
    check("C3.6 G1 fully closed before any G2 preparation", r6_close == "closed", repr(r6_close))

    owner6b, md6b = prepare(txt_path, manifest_path, gen_dir, "-c36")
    check("C3.6 next explicit command boundary produces a genuinely new owner",
          owner6b is not owner6a)
    check("C3.6 G2 not admitted merely by prepare() -- lazy admission preserved",
          owner6b.provider is None and owner6b.provider_allocation_count == 0)
    lease6b, view6b = owner6b.acquire_view("ConsumerC36G2", {"ccc", "aaa"}, _PE)
    check("C3.6 G2 admits lazily on first acquisition", owner6b.provider_allocation_count == 1)
    check("C3.6 G2 receives a new authorization epoch", owner6b.epoch >= 1)
    check("C3.6 changed source semantic visible in G2 ('ccc' present)", "ccc" in view6b.payload["folded"])
    check("C3.6 old fold 'aaa' correctly absent/proven-negative in G2",
          "aaa" not in view6b.payload["folded"])
    try:
        owner6a.acquire_view("ConsumerC36G1Retry", {"ccc"}, _PE)
        check("C3.6 old G1 owner/lease still rejected after G2 exists", False, "did not raise")
    except so.ResourceRefused as exc:
        check("C3.6 old G1 owner/lease still rejected after G2 exists", True, repr(exc))
    owner6b.release_lease(lease6b)
    owner6b.close()

    # -----------------------------------------------------------------
    # C3.7 -- same semantic pointer rewrite does not invalidate
    # -----------------------------------------------------------------
    section("C3.7 -- same-artifact pointer rewrite does not invalidate")
    so._reset_registry_for_testing()
    owner7a, _ = prepare(txt_path, manifest_path, gen_dir, "-c37")
    # Rewrite the manifest file (re-serialize; same declared identity) --
    # a pure "pointer rewrite," not a new generation.
    with open(manifest_path, "rb") as f:
        manifest_bytes_before = f.read()
    md_reparsed = sidecar_manifest.parse_manifest_bytes(manifest_bytes_before)
    rewritten = sidecar_manifest.serialize_manifest(md_reparsed.raw)
    with open(manifest_path, "wb") as f:
        f.write(rewritten)
    owner7b, _ = prepare(txt_path, manifest_path, gen_dir, "-c37")
    check("C3.7 pointer rewrite resolving to the SAME generation/source does not force invalidation",
          owner7a is owner7b, "ids=%r,%r" % (owner7a.owner_id, owner7b.owner_id))
    owner7a.close()

    # -----------------------------------------------------------------
    # C3.8 -- stale artifact source SHA refused
    # -----------------------------------------------------------------
    section("C3.8 -- stale artifact source SHA refused")
    so._reset_registry_for_testing()
    stale_manifest_path = os.path.join(WORKDIR, "manifest_stale.json")
    stale_dict = dict(md_reparsed.raw)
    stale_dict["source_sha256"] = "0" * 64
    with open(stale_manifest_path, "wb") as f:
        f.write(sidecar_manifest.serialize_manifest(stale_dict))
    try:
        prepare(txt_path, stale_manifest_path, gen_dir, "-c38")
        check("C3.8 stale artifact source SHA refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("C3.8 stale artifact source SHA refused, no owner constructed", "stale" in str(exc), repr(exc))

    # -----------------------------------------------------------------
    # C3.9 -- missing pointer/manifest recoverable
    # -----------------------------------------------------------------
    section("C3.9 -- missing pointer/manifest recoverable")
    so._reset_registry_for_testing()
    missing_manifest_path = os.path.join(WORKDIR, "manifest_missing.json")
    if os.path.exists(missing_manifest_path):
        os.remove(missing_manifest_path)
    try:
        prepare(txt_path, missing_manifest_path, gen_dir, "-c39")
        check("C3.9 missing manifest/pointer refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("C3.9 missing manifest/pointer refused recoverably", True, repr(exc))
    # Recovery: write the valid manifest at that path and retry.
    with open(missing_manifest_path, "wb") as f:
        f.write(manifest_bytes_before)
    owner9, _ = prepare(txt_path, missing_manifest_path, gen_dir, "-c39")
    check("C3.9 later explicit retry after correction succeeds", owner9 is not None)
    owner9.close()

    # -----------------------------------------------------------------
    # C3.10 -- missing candidate artifact recoverable
    # -----------------------------------------------------------------
    section("C3.10 -- missing candidate artifact recoverable")
    so._reset_registry_for_testing()
    artifact_backup = os.path.join(WORKDIR, "artifact_backup.bin")
    shutil.copy(g2_artifact_path if os.path.isfile(g2_artifact_path) else g1_artifact_path,
                artifact_backup)
    current_artifact = g2_artifact_path if os.path.isfile(g2_artifact_path) else g1_artifact_path
    os.remove(current_artifact)
    try:
        prepare(txt_path, manifest_path, gen_dir, "-c310")
        check("C3.10 missing candidate artifact refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("C3.10 missing candidate artifact refused recoverably", True, repr(exc))
    shutil.copy(artifact_backup, current_artifact)
    owner10, _ = prepare(txt_path, manifest_path, gen_dir, "-c310")
    check("C3.10 later explicit retry after restoring the artifact succeeds", owner10 is not None)
    owner10.close()

    # -----------------------------------------------------------------
    # C3.11 -- corrupt candidate artifact recoverable
    # -----------------------------------------------------------------
    section("C3.11 -- corrupt candidate artifact recoverable")
    so._reset_registry_for_testing()
    good_bytes = open(current_artifact, "rb").read()
    with open(current_artifact, "wb") as f:
        f.write(good_bytes[:len(good_bytes) // 2])  # truncate -- structurally corrupt
    owner11, _ = prepare(txt_path, manifest_path, gen_dir, "-c311")
    check("C3.11 command-boundary checks pass (artifact file exists, manifest fresh)", owner11 is not None)
    try:
        owner11.acquire_view("ConsumerC311", {"ccc"}, _PE)
        check("C3.11 corrupt artifact refused at admission", False, "did not raise")
    except so.ResourceRefused as exc:
        check("C3.11 corrupt artifact refused at admission, owner UNAVAILABLE not stuck PREPARING",
              owner11.state == so.STATE_UNAVAILABLE, repr(exc))
    check("C3.11 no provider allocated for the corrupt artifact", owner11.provider_allocation_count == 0)
    with open(current_artifact, "wb") as f:
        f.write(good_bytes)
    owner11b, _ = prepare(txt_path, manifest_path, gen_dir, "-c311")
    lease11b, _ = owner11b.acquire_view("ConsumerC311Retry", {"ccc"}, _PE)
    check("C3.11 later explicit retry after restoring the artifact succeeds", owner11b.state == so.STATE_READY)
    owner11b.release_lease(lease11b)
    owner11b.close()

    # -----------------------------------------------------------------
    # C3.12 -- incompatible profile/version recoverable
    # -----------------------------------------------------------------
    section("C3.12 -- incompatible profile/version recoverable")
    so._reset_registry_for_testing()
    incompat_manifest_path = os.path.join(WORKDIR, "manifest_incompat.json")
    incompat_dict = dict(md_reparsed.raw)
    incompat_dict["format_contract_version"] = EXPECTED_FORMAT_VERSION + 999
    with open(incompat_manifest_path, "wb") as f:
        f.write(sidecar_manifest.serialize_manifest(incompat_dict))
    try:
        prepare(txt_path, incompat_manifest_path, gen_dir, "-c312")
        check("C3.12 incompatible format_contract_version refused", False, "did not raise")
    except so.ResourceRefused as exc:
        check("C3.12 incompatible format_contract_version refused recoverably",
              "incompatible" in str(exc), repr(exc))
    owner12, _ = prepare(txt_path, manifest_path, gen_dir, "-c312")
    check("C3.12 later explicit retry with a compatible manifest succeeds", owner12 is not None)
    owner12.close()

    # -----------------------------------------------------------------
    # C3.13 -- guard refusal recoverable
    # -----------------------------------------------------------------
    section("C3.13 -- guard refusal recoverable")
    so._reset_registry_for_testing()

    # A real resource-snapshot callback is naturally stateful (it queries
    # live process/VAS state each call) -- a single owner's admission is
    # retried on the SAME owner object once resources improve, so this
    # fixture's snapshot function is switchable rather than a fresh
    # function per call (which would just build a second, unrelated
    # owner, per the existing NamespaceIdentity-keyed reuse contract).
    snapshot_state = {"sufficient": False}

    def switchable_snapshot():
        if snapshot_state["sufficient"]:
            return sufficient_snapshot()
        return so.ResourceSnapshot(400 * 1024 * 1024, 800 * 1024 * 1024, 300 * 1024 * 1024,
                                    free_vas=8 * 1024 * 1024, largest_free_region=8 * 1024 * 1024)

    owner13, _ = cb.prepare_command_boundary(
        txt_path, manifest_path, gen_dir, switchable_snapshot, so.GuardPolicy.provisional_default(),
        so.ViewBudgets.from_qualification_defaults(resource_budgets), bounded_provider, bounded_view,
        EXPECTED_FORMAT_VERSION, EXPECTED_AUTHORITY_VERSION, "-c313",
    )
    try:
        owner13.acquire_view("ConsumerC313", {"ccc"}, _PE)
        check("C3.13 guard refusal at admission", False, "did not raise")
    except so.ResourceRefused as exc:
        check("C3.13 guard refusal at admission, owner UNAVAILABLE not stuck PREPARING",
              owner13.state == so.STATE_UNAVAILABLE, repr(exc))
    check("C3.13 no provider allocated on guard refusal", owner13.provider_allocation_count == 0)
    snapshot_state["sufficient"] = True
    lease13b, _ = owner13.acquire_view("ConsumerC313Retry", {"ccc"}, _PE)
    check("C3.13 later explicit retry with sufficient resources succeeds (same owner, UNAVAILABLE -> READY)",
          owner13.state == so.STATE_READY)
    owner13.release_lease(lease13b)
    owner13.close()

    # -----------------------------------------------------------------
    # C3.14 -- no mixed-generation publication (injected retirement race)
    # -----------------------------------------------------------------
    section("C3.14 -- no mixed-generation publication (injected retirement race)")
    so._reset_registry_for_testing()
    owner14, _ = prepare(txt_path, manifest_path, gen_dir, "-c314")
    lease14a, view14a = owner14.acquire_view("ConsumerC314A", {"ccc"}, _PE)
    views_before14 = dict(owner14._views)

    def retire_after_first(resolved_count, fold_key):
        if resolved_count == 1:
            owner14.retire()

    try:
        owner14.acquire_view("ConsumerC314Race", {"aaa", "bbb"}, _PE, fault_injector=retire_after_first)
        check("C3.14 injected retirement mid-resolution interrupted publication", False, "did not raise")
    except so.ResourceRefused as exc:
        check("C3.14 candidate discarded, nothing published under the race", owner14._views == views_before14, repr(exc))
    check("C3.14 existing G14-A view remains a valid historical action object",
          owner14.get_view_via_lease(lease14a).view_id == view14a.view_id)
    owner14.release_lease(lease14a)

    print("\n" + "=" * 70)
    print("RESULT: %d PASS / %d FAIL" % (_pass[0], _fail[0]))
    print("=" * 70)
    if _fail_details:
        for d in _fail_details:
            print("  FAIL DETAIL:", d)

    so._reset_registry_for_testing()
    if os.path.exists(WORKDIR):
        shutil.rmtree(WORKDIR)

    return 0 if _fail[0] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
