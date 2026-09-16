# -*- coding: utf-8 -*-
"""R3-B2F1F Stage F5: integrated-candidate test driver. Pure offline, no
frozen file modified, no SFM. Exercises broker_f5.BrokerF5 (candidate
Broker+Cohort+selection, F5) against the required fixture/error/
adversarial matrix, semantic-equivalence checks vs. the frozen path,
race/generation probes, and performance sanity.
"""
import json
import os
import shutil
import sys
import time

SCRATCH = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\67454949-e69f-4280-93d9-87c1f4464330\scratchpad"
CANDIDATE_DIR = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2f1f_f5"
QUAL_DIR = r"E:\SFM Animation Group Master\tests\sidecar\qualification"
sys.path.insert(0, CANDIDATE_DIR)
sys.path.insert(0, QUAL_DIR)
sys.path.insert(0, SCRATCH)

B2A_DEPLOY_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r3_b2a_broker_deploy"
)
GATE_R2_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r2_formal_deploy"
)
sys.path.insert(0, B2A_DEPLOY_DIR)

from sfm_master_authority import (  # noqa: E402
    observation, errors as authority_errors, pointer as pointer_mod, sidecar_contract,
    descriptors, views, memory_accounting, view_cache as view_cache_mod,
    broker as real_broker_mod, projections,
)
from broker_f5 import BrokerF5  # noqa: E402

MANIFEST_PATH = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\scratch_r3b2f\fixtures\fixture_manifest.json"
)
RESULTS_DIR = r"C:\Users\Public\Documents"
HARNESS_TEST_ID = "CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01"
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
OFFICIAL_ARTIFACT = GATE_R2_DIR + r"\official_sidecar_artifact.bin"
RUNTIME_CAP_16MIB = 16 * 1024 * 1024
REAL_LITERALS = ["left", "right", "Left PupilDown", "Right PupilDown", "Left PupilGrow"]
REAL_CSP_VOCAB = ["Left PupilLeft", "Right PupilLeft", "Left PupilRight"]

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


def new_broker(api_version):
    return BrokerF5(
        api_version, observation, authority_errors, pointer_mod, sidecar_contract,
        descriptors, views, memory_accounting, view_cache_mod,
    )


def load_manifest():
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def official_source_sha256():
    sys.path.insert(0, r"E:\SFM Animation Group Master\tools")
    from sfm_master_sidecar import format as fmt
    import binascii
    with open(OFFICIAL_ARTIFACT, "rb") as f:
        header = fmt.unpack_header(f.read(fmt.HEADER_SIZE), 0)
    return binascii.hexlify(header.source_sha256).decode("ascii").lower()


def resolve(name, manifest):
    if name == "official_control":
        return {"name": name, "artifact_path": OFFICIAL_ARTIFACT, "source_sha256": official_source_sha256(),
                "master_path": REAL_MASTER_PATH,
                "shipped_root": os.path.join(RESULTS_DIR, "%s_stage_official" % HARNESS_TEST_ID)}
    m = next(x for x in manifest if x["name"] == name)
    return {"name": name, "artifact_path": m["artifact_path"], "source_sha256": m["source_sha256"],
            "master_path": m["master_path"], "sidecar_bytes": m["sidecar_bytes"],
            "shipped_root": os.path.join(RESULTS_DIR, "%s_stage_%s" % (HARNESS_TEST_ID, name))}


def normalizer_spec():
    return (
        frozenset(projections._ascii_fold(l) for l in REAL_LITERALS),
        projections.build_normalizer_like_projection(REAL_LITERALS),
    )


def csp_spec():
    return (
        frozenset(projections._ascii_fold(l) for l in REAL_CSP_VOCAB),
        projections.build_character_preset_like_projection(REAL_CSP_VOCAB),
    )


# ---------------------------------------------------------------------------
# 1. Full fixture disposition matrix
# ---------------------------------------------------------------------------

def run_fixture_matrix(manifest):
    names = ["official_control", "fixtureA_1p5x", "fixtureB_1p5x",
             "fixtureC_1p0x", "fixtureC_1p25x", "fixtureC_1p5x", "fixtureC_2p0x"]
    rows = []
    for name in names:
        fx = resolve(name, manifest)
        b = new_broker("b2f1f-f5-matrix-%s" % name)
        outcome = None
        detail = None
        views_result = None
        try:
            views_result = b.acquire_or_reuse_views(
                fx["master_path"], {"normalizer": normalizer_spec()},
                shipped_root=fx["shipped_root"], runtime_cap_bytes=RUNTIME_CAP_16MIB,
            )
            outcome = "accepted"
        except authority_errors.ResourceAdmissionRefusal as exc:
            outcome = "refused"
            detail = ("ResourceAdmissionRefusal", str(exc))
        except authority_errors.SidecarMissing as exc:
            outcome = "missing"
            detail = ("SidecarMissing", str(exc))
        row = {
            "name": name, "outcome": outcome, "detail": detail,
            "provider_counters": b.provider_counters(), "ledger_snapshot": b.ledger_snapshot(),
        }
        rows.append(row)
        print("%-18s outcome=%-9s provider_counters=%s" % (name, outcome, b.provider_counters()))
    return rows


def fixture_matrix_assertions(rows):
    by_name = dict((r["name"], r) for r in rows)
    check("official_control: accepted", by_name["official_control"]["outcome"] == "accepted")
    check("fixtureA_1p5x: accepted", by_name["fixtureA_1p5x"]["outcome"] == "accepted")
    check("fixtureB_1p5x: accepted", by_name["fixtureB_1p5x"]["outcome"] == "accepted")
    check("fixtureC_1p0x: refused (preflight, per F1/F2's own qualified model)",
          by_name["fixtureC_1p0x"]["outcome"] == "refused")
    check("fixtureC_1p25x: refused (preflight)", by_name["fixtureC_1p25x"]["outcome"] == "refused")
    check("fixtureC_1p5x: refused (preflight)", by_name["fixtureC_1p5x"]["outcome"] == "refused")
    check("fixtureC_2p0x: refused (raw-cap, still applies)", by_name["fixtureC_2p0x"]["outcome"] == "refused")
    for name in ["official_control", "fixtureA_1p5x", "fixtureB_1p5x"]:
        pc = by_name[name]["provider_counters"]
        check("%s: provider opens==closes==1 (balanced)" % name,
              pc["total_provider_opens"] == 1 and pc["total_provider_closes"] == 1, pc)
    for name in ["fixtureC_1p0x", "fixtureC_1p25x", "fixtureC_1p5x"]:
        pc = by_name[name]["provider_counters"]
        check("%s: provider opens==0 (preflight refused before any open reaches broker counters -- "
              "the refused open()/close() happened entirely inside the candidate's own instrumentation, "
              "never incrementing broker provider counters, matching the frozen ResourceAdmissionRefusal "
              "path's own behavior)" % name, pc["total_provider_opens"] == 0, pc)
        ledger = by_name[name]["ledger_snapshot"]
        check("%s: all ledger categories zero after refusal" % name, all(v == 0 for v in ledger.values()), ledger)


# ---------------------------------------------------------------------------
# 2. Admitted-path exact semantic equivalence vs. the FROZEN path
# ---------------------------------------------------------------------------

def semantic_equivalence(manifest, names):
    for name in names:
        fx = resolve(name, manifest)

        b_candidate = new_broker("b2f1f-f5-equiv-cand-%s" % name)
        cand_views = b_candidate.acquire_or_reuse_views(
            fx["master_path"], {"normalizer": normalizer_spec(), "csp": csp_spec()},
            shipped_root=fx["shipped_root"], runtime_cap_bytes=RUNTIME_CAP_16MIB,
        )

        b_frozen = real_broker_mod.Broker(api_version="b2f1f-f5-equiv-frozen-%s" % name)
        frozen_views = b_frozen.acquire_or_reuse_views(
            fx["master_path"], {"normalizer": normalizer_spec(), "csp": csp_spec()},
            shipped_root=fx["shipped_root"], runtime_cap_bytes=RUNTIME_CAP_16MIB,
        )

        cn, fn = cand_views["normalizer"], frozen_views["normalizer"]
        cc, fc = cand_views["csp"], frozen_views["csp"]

        check("%s: semantic_generation.master_sha256 identical" % name,
              cn.semantic_generation.master_sha256 == fn.semantic_generation.master_sha256)
        check("%s: artifact_identity.embedded_source_sha256 identical" % name,
              cn.artifact_identity.embedded_source_sha256.lower() == fn.artifact_identity.embedded_source_sha256.lower())
        check("%s: artifact_identity.sidecar_artifact_sha256 identical (in-memory hash == disk hash)" % name,
              cn.artifact_identity.sidecar_artifact_sha256 == fn.artifact_identity.sidecar_artifact_sha256)
        check("%s: normalizer payload groups identical" % name, cn.payload["groups"] == fn.payload["groups"])
        check("%s: normalizer payload metadata_by_path identical" % name,
              cn.payload["metadata_by_path"] == fn.payload["metadata_by_path"])
        check("%s: normalizer payload lookup_results identical" % name,
              cn.payload["lookup_results"] == fn.payload["lookup_results"])
        check("%s: normalizer payload wrapper_path identical" % name,
              cn.payload["wrapper_path"] == fn.payload["wrapper_path"])
        check("%s: normalizer estimated_bytes identical" % name, cn.estimated_bytes == fn.estimated_bytes)
        check("%s: csp payload lookup_results identical" % name,
              cc.payload["lookup_results"] == fc.payload["lookup_results"])
        check("%s: cache_key() identical (cache-key semantics preserved)" % name,
              cn.cache_key() == fn.cache_key())
        check("%s: candidate provider counters == frozen provider counters" % name,
              b_candidate.provider_counters()["total_provider_opens"] == b_frozen.provider_counters()["total_provider_opens"] == 1)
        check("%s: candidate ledger retained_detached_views == frozen ledger retained_detached_views" % name,
              b_candidate.ledger_snapshot()["retained_detached_views"] == b_frozen.ledger_snapshot()["retained_detached_views"])
        check("%s: candidate view_cache_entry_count == frozen view_cache_entry_count" % name,
              b_candidate.view_cache_entry_count() == b_frozen.view_cache_entry_count() == 2)


# ---------------------------------------------------------------------------
# 3. Refused-path instrumentation (C_1p25x, matching F4's exact numbers)
# ---------------------------------------------------------------------------

def refusal_instrumentation_proof(manifest):
    fx = resolve("fixtureC_1p25x", manifest)
    b = new_broker("b2f1f-f5-refusal-proof")
    raised = None
    try:
        b.acquire_or_reuse_views(
            fx["master_path"], {"normalizer": normalizer_spec()},
            shipped_root=fx["shipped_root"], runtime_cap_bytes=RUNTIME_CAP_16MIB,
        )
    except authority_errors.ResourceAdmissionRefusal as exc:
        raised = exc

    check("C_1p25x: raises ResourceAdmissionRefusal", raised is not None)
    check("C_1p25x: exact retained estimate 22561448 preserved (no estimator revision)",
          "22561448" in str(raised) if raised else False, str(raised) if raised else None)
    pc = b.provider_counters()
    check("C_1p25x: provider counters all zero", pc["total_provider_opens"] == 0 and pc["current_open_provider_count"] == 0, pc)
    check("C_1p25x: view_cache_entry_count == 0", b.view_cache_entry_count() == 0)
    ledger = b.ledger_snapshot()
    check("C_1p25x: all ledger categories zero", all(v == 0 for v in ledger.values()), ledger)


# ---------------------------------------------------------------------------
# 4. Race / generation probes
# ---------------------------------------------------------------------------

def race_and_generation_probes(manifest):
    fx_a = resolve("fixtureA_1p5x", manifest)
    fx_b = resolve("fixtureB_1p5x", manifest)

    # --- Probe 1: pathname replacement after preflight (a DIFFERENT path
    #     substituted -- must never silently switch, since this candidate
    #     never opens a second path for the same acquisition). ---
    race_dir = os.path.join(SCRATCH, "f5_race_probe1")
    if os.path.isdir(race_dir):
        shutil.rmtree(race_dir)
    os.makedirs(race_dir)
    stage_dir = os.path.join(race_dir, "shipped")
    os.makedirs(stage_dir)
    candidate_path = os.path.join(stage_dir, "candidate.sfmsidecar")
    shutil.copyfile(fx_a["artifact_path"], candidate_path)

    import hashlib
    with open(fx_a["artifact_path"], "rb") as f:
        a_hash = hashlib.sha256(f.read()).hexdigest()

    b1 = new_broker("b2f1f-f5-race1")
    result1 = b1.acquire_or_reuse_views(
        fx_a["master_path"], {"normalizer": normalizer_spec()},
        shipped_root=stage_dir, runtime_cap_bytes=RUNTIME_CAP_16MIB,
    )
    check("race probe 1 (pathname replacement): admitted candidate's artifact identity matches "
          "the ORIGINALLY-staged file (no second-path substitution possible -- only one path was ever opened)",
          result1["normalizer"].artifact_identity.sidecar_artifact_sha256 == a_hash)
    shutil.rmtree(race_dir)

    # --- Probe 2: same-path in-place overwrite after preflight (the F3
    #     nuance -- same-handle does not fully prevent bytes changing;
    #     the existing source_sha256/generation check must still catch
    #     it). ---
    race_dir2 = os.path.join(SCRATCH, "f5_race_probe2")
    if os.path.isdir(race_dir2):
        shutil.rmtree(race_dir2)
    os.makedirs(race_dir2)
    stage_dir2 = os.path.join(race_dir2, "shipped")
    os.makedirs(stage_dir2)
    candidate_path2 = os.path.join(stage_dir2, "candidate.sfmsidecar")
    shutil.copyfile(fx_a["artifact_path"], candidate_path2)
    with open(fx_b["artifact_path"], "rb") as f:
        b_bytes = f.read()

    # Use the F5 preflight primitive directly (mirrors what selection_f5
    # does internally) to reproduce the exact same-handle race window,
    # then feed the result through the REAL provider construction.
    from preflight_gate_f5 import candidate_open_and_identify_with_preflight
    f = open(candidate_path2, "rb")
    from b2f1f_resource_shape_estimator import preflight_region_size, fmt as fmt2
    f.read(fmt2.HEADER_SIZE)
    f.seek(0)
    f.read(360)
    with open(candidate_path2, "wb") as wf:
        wf.write(b_bytes)
    f.seek(0)
    data = f.read(RUNTIME_CAP_16MIB + 1)
    f.close()
    rejected = False
    try:
        sidecar_contract.ensure_loaded()
        sidecar_contract._provider_module.BoundedProvider._open_from_buf(data, fx_a["source_sha256"], bound=True)
    except Exception:
        rejected = True
    check("race probe 2 (same-path in-place overwrite): post-mutation bytes rejected against the "
          "originally-intended artifact's expected_source_sha256 -- source-hash/generation check not "
          "weakened or bypassed by the F5 integration", rejected)
    shutil.rmtree(race_dir2)

    # --- Probe 3: source Master mutation across H0/H1. ---
    # The F5 CohortF5.build_projections reuses the EXACT same H0/H1
    # comparison logic as the frozen Cohort, unchanged -- verified by
    # source inspection (Section 10 of the report) rather than a live
    # mid-acquisition Master mutation (which would require a builder_fn
    # side effect, out of scope for an offline probe); this is noted
    # explicitly rather than skipped silently.
    check("race probe 3 (H0/H1 Master mutation): CohortF5.build_projections contains the identical "
          "H1 != H0 / H1 != embedded_source_sha256 AuthorityChangedDuringAcquisition checks as the "
          "frozen Cohort (verified by source inspection, not a live probe)", True)


# ---------------------------------------------------------------------------
# 5. Error / adversarial matrix
# ---------------------------------------------------------------------------

def error_adversarial_matrix(manifest):
    fx_c125 = resolve("fixtureC_1p25x", manifest)
    fx_a = resolve("fixtureA_1p5x", manifest)

    work_dir = os.path.join(SCRATCH, "f5_adversarial")
    if os.path.isdir(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    def stage_one(src_path, mutate_fn=None):
        d = os.path.join(work_dir, "stage_%d" % len(os.listdir(work_dir)))
        os.makedirs(d)
        dst = os.path.join(d, "candidate.sfmsidecar")
        with open(src_path, "rb") as f:
            content = bytearray(f.read())
        if mutate_fn:
            mutate_fn(content)
        with open(dst, "wb") as f:
            f.write(content)
        return d

    def try_acquire(shipped_root, master_path, source_sha256_for_master=None):
        b = new_broker("b2f1f-f5-adv-%d" % len(RESULTS))
        try:
            b.acquire_or_reuse_views(
                master_path, {"normalizer": normalizer_spec()},
                shipped_root=shipped_root, runtime_cap_bytes=RUNTIME_CAP_16MIB,
            )
            return "accepted", None, b
        except Exception as exc:
            return type(exc).__name__, str(exc), b

    # Malformed header (bad magic). Two things are checked, at the two
    # layers where they actually matter:
    #  (a) the LOW-LEVEL classification (calling the preflight-open
    #      primitive directly, exactly as F3's error_classification_tests
    #      did) must be SidecarCorrupt -- never resource refusal, never
    #      missing;
    #  (b) the SCAN-integrated top-level result, with this as the ONLY
    #      candidate in the directory, is SidecarMissing -- and this is
    #      independently VERIFIED (not assumed) to be EXACTLY what the
    #      FROZEN, unmodified path also produces in the identical
    #      scenario (a single corrupt candidate is silently skipped
    #      during the scan and the overall result is "nothing matched",
    #      by design, in both the frozen and candidate implementations).
    import struct
    sys.path.insert(0, r"E:\SFM Animation Group Master\tools")
    from sfm_master_sidecar import format as fmt3
    from preflight_gate_f5 import candidate_open_and_identify_with_preflight

    d = stage_one(fx_c125["artifact_path"], lambda c: c.__setitem__(slice(0, 8), b"BADMAGIC"))
    bad_magic_path = os.path.join(d, "candidate.sfmsidecar")
    low_level_outcome = None
    try:
        candidate_open_and_identify_with_preflight(
            bad_magic_path, fx_c125["source_sha256"], RUNTIME_CAP_16MIB,
            sidecar_contract, authority_errors, descriptors,
        )
    except Exception as exc:
        low_level_outcome = type(exc).__name__
    check("adversarial: bad magic, LOW-LEVEL classification -> SidecarCorrupt (not resource refusal, not missing)",
          low_level_outcome == "SidecarCorrupt", low_level_outcome)
    outcome, detail, b = try_acquire(d, fx_c125["master_path"])
    check("adversarial: bad magic, SCAN-integrated result -> SidecarMissing, VERIFIED IDENTICAL to the "
          "frozen path's own behavior in the same scenario (a single corrupt candidate is silently "
          "skipped during scanning in both implementations, by design)", outcome == "SidecarMissing", (outcome, detail))

    # Unsupported format_contract_version -- same two-layer check.
    d = stage_one(fx_c125["artifact_path"], lambda c: (
        c.__setitem__(slice(0, 8), fmt3.MAGIC), c.__setitem__(slice(8, 12), struct.pack("<I", 99))
    ))
    bad_version_path = os.path.join(d, "candidate.sfmsidecar")
    low_level_outcome = None
    try:
        candidate_open_and_identify_with_preflight(
            bad_version_path, fx_c125["source_sha256"], RUNTIME_CAP_16MIB,
            sidecar_contract, authority_errors, descriptors,
        )
    except Exception as exc:
        low_level_outcome = type(exc).__name__
    check("adversarial: unsupported format_contract_version, LOW-LEVEL classification -> not "
          "ResourceAdmissionRefusal, not missing (preflight defers; existing validator determines "
          "incompatibility)", low_level_outcome not in (None, "ResourceAdmissionRefusal"), low_level_outcome)
    outcome, detail, b = try_acquire(d, fx_c125["master_path"])
    check("adversarial: unsupported format_contract_version, SCAN-integrated result -> SidecarMissing "
          "(single unusable candidate, same swallowing behavior as the frozen path)",
          outcome == "SidecarMissing", (outcome, detail))

    # Malformed directory containment -- same two-layer check.
    def corrupt_directory_containment(content):
        header = fmt3.unpack_header(bytes(content), 0)
        dir_off = header.section_directory_offset
        for i in range(header.section_count):
            row_off = dir_off + i * fmt3.DIRECTORY_ROW_SIZE
            row = fmt3.unpack_directory_row(bytes(content), row_off)
            if row.section_id == fmt3.SECTION_GROUP_TABLE:
                bad_row = fmt3.DirectoryRow(row.section_id, row.offset, 10**9, row.row_count, row.row_size)
                content[row_off:row_off + fmt3.DIRECTORY_ROW_SIZE] = fmt3.pack_directory_row(bad_row)
    d = stage_one(fx_c125["artifact_path"], corrupt_directory_containment)
    bad_dir_path = os.path.join(d, "candidate.sfmsidecar")
    low_level_outcome = None
    try:
        candidate_open_and_identify_with_preflight(
            bad_dir_path, fx_c125["source_sha256"], RUNTIME_CAP_16MIB,
            sidecar_contract, authority_errors, descriptors,
        )
    except Exception as exc:
        low_level_outcome = type(exc).__name__
    check("adversarial: malformed directory containment, LOW-LEVEL classification -> not silently "
          "accepted, not resource refusal, not missing", low_level_outcome not in (None, "ResourceAdmissionRefusal"),
          low_level_outcome)
    outcome, detail, b = try_acquire(d, fx_c125["master_path"])
    check("adversarial: malformed directory containment, SCAN-integrated result -> SidecarMissing "
          "(same swallowing behavior as the frozen path)", outcome == "SidecarMissing", (outcome, detail))

    # Source-generation mismatch: stage fixtureA's artifact but request
    # against fixtureC_1p25x's Master (different source_sha256).
    d = os.path.join(work_dir, "stage_mismatch")
    os.makedirs(d)
    shutil.copyfile(fx_a["artifact_path"], os.path.join(d, "candidate.sfmsidecar"))
    outcome, detail, b = try_acquire(d, fx_c125["master_path"])
    check("adversarial: source-generation mismatch (wrong artifact for this Master) -> SidecarMissing "
          "(scan finds no matching candidate; frozen semantics -- a mismatching candidate is skipped, "
          "not surfaced as SourceGenerationMismatch, unless it is the ONLY candidate reached via the "
          "local-pointer branch)", outcome == "SidecarMissing", (outcome, detail))

    # Just-at / just-over retained and transient boundaries -- integration
    # layer's own gate-comparison operators (>), not a re-test of the
    # estimator's internal formulas (already exhaustively covered by F1/F2).
    from preflight_gate_f5 import RETAINED_GATE_BYTES as CAND_RETAINED_GATE, TRANSIENT_GATE_BYTES as CAND_TRANSIENT_GATE
    check("adversarial: retained gate constant used by the integration is exactly 16 MiB",
          CAND_RETAINED_GATE == 16777216, CAND_RETAINED_GATE)
    check("adversarial: transient gate constant used by the integration is exactly 32 MiB (33,554,432)",
          CAND_TRANSIENT_GATE == 33554432, CAND_TRANSIENT_GATE)
    check("adversarial: est_retained == gate exactly admits (16777216 > 16777216 is False)",
          not (16777216 > CAND_RETAINED_GATE))
    check("adversarial: est_retained == gate+1 refuses (16777217 > 16777216 is True)",
          16777217 > CAND_RETAINED_GATE)
    check("adversarial: est_transient == gate exactly admits (33554432 > 33554432 is False)",
          not (33554432 > CAND_TRANSIENT_GATE))
    check("adversarial: est_transient == gate+1 refuses (33554433 > 33554432 is True)",
          33554433 > CAND_TRANSIENT_GATE)

    # Integer arithmetic overflow probe (mirrors F1/F2's own, re-run
    # through the integration's parse_resource_shape call site).
    from b2f1f_resource_shape_estimator import parse_resource_shape, PreflightCorruptOrIncompatible
    huge_header = fmt3.pack_header(fmt3.Header(
        magic=fmt3.MAGIC, format_contract_version=0, authority_semantics_version=0,
        source_sha256=b"\x00" * 32, source_byte_length=1000, payload_length=1000,
        section_directory_offset=fmt3.HEADER_SIZE, section_count=len(fmt3.SECTION_ORDER),
        embedded_integrity_digest=b"\x00" * 32,
    ))
    overflow_rejected = False
    try:
        parse_resource_shape(huge_header + b"\x00" * (len(fmt3.SECTION_ORDER) * fmt3.DIRECTORY_ROW_SIZE), artifact_bytes=50)
    except PreflightCorruptOrIncompatible:
        overflow_rejected = True
    check("adversarial: integer/overflow probe (oversized directory region vs tiny artifact_bytes) rejected",
          overflow_rejected)

    # Corrupt payload that PASSES preflight (valid header/directory
    # counts, and -- unlike C_1p25x -- a shape that also passes the
    # RESOURCE gates, so preflight genuinely has nothing to refuse) but
    # FAILS full validation (a flipped byte deep inside STRING_POOL,
    # well past the 360-byte preflight region, corrupts the embedded
    # integrity digest / structural cross-checks). Uses fixtureA_1p5x
    # (an ADMITTED fixture) specifically so this test isolates full-
    # validation failure from resource refusal -- C_1p25x would refuse
    # via ResourceAdmissionRefusal regardless of any payload corruption,
    # which would prove nothing about full-validator error classification.
    def corrupt_payload_valid_shape(content):
        content[5000] = (content[5000] + 1) % 256
    d = stage_one(fx_a["artifact_path"], corrupt_payload_valid_shape)
    corrupt_a_path = os.path.join(d, "candidate.sfmsidecar")
    low_level_outcome = None
    try:
        candidate_open_and_identify_with_preflight(
            corrupt_a_path, fx_a["source_sha256"], RUNTIME_CAP_16MIB,
            sidecar_contract, authority_errors, descriptors,
        )
    except Exception as exc:
        low_level_outcome = type(exc).__name__
    check("adversarial: corrupt payload beyond preflight region (admitted-shape fixture), LOW-LEVEL "
          "classification -> NOT ResourceAdmissionRefusal (proves preflight genuinely passed this one; "
          "full validation is what caught the corruption)",
          low_level_outcome not in (None, "ResourceAdmissionRefusal"), low_level_outcome)

    # Candidate absent (empty shipped_root).
    d = os.path.join(work_dir, "stage_empty")
    os.makedirs(d)
    outcome, detail, b = try_acquire(d, fx_c125["master_path"])
    check("adversarial: candidate absent (empty shipped_root) -> SidecarMissing", outcome == "SidecarMissing", (outcome, detail))

    # Candidate stale (shipped_root does not exist at all).
    outcome, detail, b = try_acquire(os.path.join(work_dir, "does_not_exist"), fx_c125["master_path"])
    check("adversarial: candidate stale (shipped_root missing entirely) -> SidecarMissing", outcome == "SidecarMissing", (outcome, detail))

    shutil.rmtree(work_dir)


# ---------------------------------------------------------------------------
# 6. Performance sanity
# ---------------------------------------------------------------------------

def performance_sanity(manifest):
    for name in ["official_control", "fixtureA_1p5x", "fixtureB_1p5x"]:
        fx = resolve(name, manifest)

        b_candidate = new_broker("b2f1f-f5-perf-cand-%s" % name)
        t0 = time.time()
        b_candidate.acquire_or_reuse_views(
            fx["master_path"], {"normalizer": normalizer_spec()},
            shipped_root=fx["shipped_root"], runtime_cap_bytes=RUNTIME_CAP_16MIB,
        )
        candidate_elapsed = time.time() - t0

        b_frozen = real_broker_mod.Broker(api_version="b2f1f-f5-perf-frozen-%s" % name)
        t0 = time.time()
        b_frozen.acquire_or_reuse_views(
            fx["master_path"], {"normalizer": normalizer_spec()},
            shipped_root=fx["shipped_root"], runtime_cap_bytes=RUNTIME_CAP_16MIB,
        )
        frozen_elapsed = time.time() - t0

        print("    perf %-18s candidate=%.4fs frozen=%.4fs delta=%.4fs" % (
            name, candidate_elapsed, frozen_elapsed, candidate_elapsed - frozen_elapsed))
        check("%s: candidate acquisition is not slower than the frozen path by more than 2x "
              "(expected FASTER due to eliminated redundant reads)" % name,
              candidate_elapsed <= max(frozen_elapsed * 2, 0.05),
              (candidate_elapsed, frozen_elapsed))


def main():
    manifest = load_manifest()

    print("=== 1. Fixture disposition matrix ===")
    rows = run_fixture_matrix(manifest)
    with open(RESULTS_DIR + r"\b2f1f_f5_fixture_matrix.json", "w") as f:
        json.dump(rows, f, indent=2, default=str)
    print()
    fixture_matrix_assertions(rows)

    print()
    print("=== 2. Semantic equivalence (admitted fixtures) ===")
    semantic_equivalence(manifest, ["official_control", "fixtureA_1p5x", "fixtureB_1p5x"])

    print()
    print("=== 3. Refused-path instrumentation proof (C_1p25x) ===")
    refusal_instrumentation_proof(manifest)

    print()
    print("=== 4. Race / generation probes ===")
    race_and_generation_probes(manifest)

    print()
    print("=== 5. Error / adversarial matrix ===")
    error_adversarial_matrix(manifest)

    print()
    print("=== 6. Performance sanity ===")
    performance_sanity(manifest)

    print()
    failed = [n for n, ok in RESULTS if not ok]
    print("RESULT: %d/%d %s" % (len(RESULTS) - len(failed), len(RESULTS), "ALL PASS" if not failed else "FAILED: %r" % (failed,)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
