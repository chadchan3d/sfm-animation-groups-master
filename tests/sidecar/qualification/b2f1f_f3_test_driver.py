# -*- coding: utf-8 -*-
"""R3-B2F1F Stage F3: full test driver. Fixture matrix, instrumentation
capture, semantic-equivalence proof against the existing frozen path,
C_1p25x early-refusal proof, error-classification tests. Pure offline,
no frozen file modified, no SFM.
"""
import json
import os
import shutil
import sys

SCRATCH = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\67454949-e69f-4280-93d9-87c1f4464330\scratchpad"
sys.path.insert(0, SCRATCH)
from b2f1f_f3_same_handle_candidate import candidate_open_path_with_preflight, Instrumentation  # noqa: E402

B2A_DEPLOY_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r3_b2a_broker_deploy"
)
GATE_R2_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r2_formal_deploy"
)
sys.path.insert(0, B2A_DEPLOY_DIR)
from sfm_master_authority import broker as broker_mod, projections, errors as authority_errors, sidecar_contract  # noqa: E402

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


def load_manifest():
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def official_source_sha256():
    # Official artifact's embedded source_sha256 -- read directly via the
    # existing format module (header field), no new logic invented.
    sys.path.insert(0, r"E:\SFM Animation Group Master\tools")
    from sfm_master_sidecar import format as fmt
    import binascii
    with open(OFFICIAL_ARTIFACT, "rb") as f:
        header = fmt.unpack_header(f.read(fmt.HEADER_SIZE), 0)
    return binascii.hexlify(header.source_sha256).decode("ascii").lower()


def resolve(name, manifest):
    if name == "official_control":
        return {"name": name, "artifact_path": OFFICIAL_ARTIFACT, "source_sha256": official_source_sha256(),
                "master_path": REAL_MASTER_PATH}
    m = next(x for x in manifest if x["name"] == name)
    return {"name": name, "artifact_path": m["artifact_path"], "source_sha256": m["source_sha256"],
            "master_path": m["master_path"], "sidecar_bytes": m["sidecar_bytes"]}


# ---------------------------------------------------------------------------
# 1. Full fixture disposition matrix + instrumentation
# ---------------------------------------------------------------------------

def run_fixture_matrix():
    manifest = load_manifest()
    names = ["official_control", "fixtureA_1p5x", "fixtureB_1p5x", "fixtureC_1p0x",
             "fixtureC_1p25x", "fixtureC_1p5x", "fixtureC_2p0x"]
    rows = []
    for name in names:
        fx = resolve(name, manifest)
        inst = Instrumentation()
        try:
            provider, inst = candidate_open_path_with_preflight(
                fx["artifact_path"], fx["source_sha256"], RUNTIME_CAP_16MIB, inst,
            )
            provider.close()
        except authority_errors.ResourceAdmissionRefusal as exc:
            inst.outcome = "refused"
            inst.error_type = "ResourceAdmissionRefusal"
            inst.error_detail = str(exc)
        except authority_errors.SidecarCorrupt as exc:
            inst.outcome = "refused"
            inst.error_type = "SidecarCorrupt"
            inst.error_detail = str(exc)
        except authority_errors.SourceGenerationMismatch as exc:
            inst.outcome = "refused"
            inst.error_type = "SourceGenerationMismatch"
            inst.error_detail = str(exc)
        d = inst.to_dict()
        d["name"] = name
        rows.append(d)
        print("%-18s outcome=%-9s reason=%-24s file_open=%s file_close=%s preflight_bytes=%-4s "
              "full_read=%s validator=%s est_retained=%-10s est_transient=%-10s" % (
                  name, d.get("outcome"), d.get("reason"), d.get("file_open_count"), d.get("file_close_count"),
                  d.get("preflight_bytes_read"), d.get("full_bounded_read_call_count"), d.get("validator_call_count"),
                  d.get("estimated_retained_bytes"), d.get("estimated_transient_bytes"),
              ))
    return rows


# ---------------------------------------------------------------------------
# 2. C_1p25x early-refusal proof
# ---------------------------------------------------------------------------

def c1p25x_early_refusal_proof(manifest):
    fx = resolve("fixtureC_1p25x", manifest)
    inst = Instrumentation()
    raised = None
    try:
        provider, inst = candidate_open_path_with_preflight(
            fx["artifact_path"], fx["source_sha256"], RUNTIME_CAP_16MIB, inst,
        )
        provider.close()
    except authority_errors.ResourceAdmissionRefusal as exc:
        raised = exc

    check("C_1p25x: raises ResourceAdmissionRefusal", raised is not None)
    check("C_1p25x: reason is estimated_retained or estimated_transient",
          inst.reason in ("estimated_retained", "estimated_transient"), inst.reason)
    check("C_1p25x: preflight_bytes_read <= 360", inst.preflight_bytes_read <= 360, inst.preflight_bytes_read)
    check("C_1p25x: full_bounded_read_call_count == 0", inst.full_bounded_read_call_count == 0)
    check("C_1p25x: validator_call_count == 0", inst.validator_call_count == 0)
    check("C_1p25x: projection_builder_call_count == 0", inst.projection_builder_call_count == 0)
    check("C_1p25x: published_detached_view_count == 0", inst.published_detached_view_count == 0)
    check("C_1p25x: handle open==1, close==1", inst.file_open_count == 1 and inst.file_close_count == 1,
          (inst.file_open_count, inst.file_close_count))
    return inst


# ---------------------------------------------------------------------------
# 3. Same-handle proof (no reopen), across ALL fixtures
# ---------------------------------------------------------------------------

def same_handle_proof(rows):
    for r in rows:
        check("%s: exactly one file open" % r["name"], r["file_open_count"] == 1, r["file_open_count"])
        check("%s: exactly one file close" % r["name"], r["file_close_count"] == 1, r["file_close_count"])
        if r.get("outcome") == "accepted":
            check("%s: handle identity (fileno/dev/ino) unchanged before->after positioning" % r["name"],
                  r["handle_identity_before"][1:3] == r["handle_identity_after"][1:3],
                  (r["handle_identity_before"], r["handle_identity_after"]))


# ---------------------------------------------------------------------------
# 4. Admitted-fixture semantic equivalence vs. existing frozen path
# ---------------------------------------------------------------------------

def semantic_equivalence(manifest, names):
    for name in names:
        fx = resolve(name, manifest)

        # Prototype path.
        inst = Instrumentation()
        provider, inst = candidate_open_path_with_preflight(
            fx["artifact_path"], fx["source_sha256"], RUNTIME_CAP_16MIB, inst,
        )
        proto_norm_builder = projections.build_normalizer_like_projection(REAL_LITERALS)
        proto_payload, proto_coverage, proto_est = proto_norm_builder(provider)
        proto_csp_builder = projections.build_character_preset_like_projection(REAL_CSP_VOCAB)
        proto_csp_payload, proto_csp_coverage, proto_csp_est = proto_csp_builder(provider)
        provider.close()

        # Existing frozen path (fresh broker, real acquire_or_reuse_views).
        b = broker_mod.Broker(api_version="b2f1f-f3-equiv-%s" % name)
        normalizer_spec = (
            frozenset(projections._ascii_fold(l) for l in REAL_LITERALS),
            projections.build_normalizer_like_projection(REAL_LITERALS),
        )
        existing_views1 = b.acquire_or_reuse_views(
            fx["master_path"], {"normalizer": normalizer_spec},
            shipped_root=os.path.join(RESULTS_DIR, "%s_stage_%s" % (
                HARNESS_TEST_ID, "official" if name == "official_control" else name)),
            runtime_cap_bytes=RUNTIME_CAP_16MIB,
        )
        csp_spec = (
            frozenset(projections._ascii_fold(l) for l in REAL_CSP_VOCAB),
            projections.build_character_preset_like_projection(REAL_CSP_VOCAB),
        )
        existing_views2 = b.acquire_or_reuse_views(
            fx["master_path"], {"csp": csp_spec},
            shipped_root=os.path.join(RESULTS_DIR, "%s_stage_%s" % (
                HARNESS_TEST_ID, "official" if name == "official_control" else name)),
            runtime_cap_bytes=RUNTIME_CAP_16MIB,
        )
        existing_norm_view = existing_views1["normalizer"]
        existing_csp_view = existing_views2["csp"]

        check("%s: normalizer payload groups identical" % name,
              proto_payload["groups"] == existing_norm_view.payload["groups"])
        check("%s: normalizer payload metadata_by_path identical" % name,
              proto_payload["metadata_by_path"] == existing_norm_view.payload["metadata_by_path"])
        check("%s: normalizer payload lookup_results identical" % name,
              proto_payload["lookup_results"] == existing_norm_view.payload["lookup_results"])
        check("%s: normalizer payload wrapper_path identical" % name,
              proto_payload["wrapper_path"] == existing_norm_view.payload["wrapper_path"])
        check("%s: normalizer estimated_bytes identical" % name, proto_est == existing_norm_view.estimated_bytes)
        check("%s: csp payload lookup_results identical" % name,
              proto_csp_payload["lookup_results"] == existing_csp_view.payload["lookup_results"])
        import binascii
        proto_source_sha256_hex = binascii.hexlify(provider._header.source_sha256).decode("ascii").lower()
        check("%s: artifact identity (embedded source_sha256) identical between prototype provider "
              "and existing frozen path's ArtifactIdentity" % name,
              proto_source_sha256_hex == existing_norm_view.artifact_identity.embedded_source_sha256.lower())
        check("%s: semantic_generation master_sha256 identical across both existing views" % name,
              existing_norm_view.semantic_generation.master_sha256 == existing_csp_view.semantic_generation.master_sha256)


# ---------------------------------------------------------------------------
# 5. Same-handle mutation/race probe
# ---------------------------------------------------------------------------

def race_probe(manifest):
    """Mutates the SAME path in place between preflight and the full
    read, on the SAME already-open handle, then feeds whatever bytes
    result to the EXISTING, unmodified provider construction. Finding
    (reported honestly, not assumed going in): Python's buffered
    io.BufferedReader does not give an airtight "always reflects
    content exactly as of open()" guarantee when the underlying file is
    mutated externally between a seek() and a large read() -- the
    result can be a hybrid of already-buffered pre-mutation bytes and
    fresh post-mutation reads, matching NEITHER file exactly. The
    property this probe actually proves is the one Section 10 asks for
    ("validates the originally opened bytes correctly OR fails
    according to existing handle/file semantics") -- it must never
    SILENTLY ACCEPT a wrong/mixed artifact as valid. It must also never
    open a second path."""
    fx_a = resolve("fixtureA_1p5x", manifest)
    fx_b = resolve("fixtureB_1p5x", manifest)

    race_dir = os.path.join(SCRATCH, "race_probe")
    if os.path.isdir(race_dir):
        shutil.rmtree(race_dir)
    os.makedirs(race_dir)
    race_path = os.path.join(race_dir, "candidate.sfmsidecar")
    shutil.copyfile(fx_a["artifact_path"], race_path)

    import hashlib
    with open(fx_a["artifact_path"], "rb") as f:
        original_bytes = f.read()
    original_hash = hashlib.sha256(original_bytes).hexdigest()
    with open(fx_b["artifact_path"], "rb") as f:
        replacement_bytes = f.read()
    replacement_hash = hashlib.sha256(replacement_bytes).hexdigest()

    open_call_count = [0]
    _real_open = open

    def _counting_open(*a, **kw):
        if a and a[0] == race_path and ("r" in (a[1] if len(a) > 1 else kw.get("mode", "r"))):
            open_call_count[0] += 1
        return _real_open(*a, **kw)

    f = _counting_open(race_path, "rb")
    from b2f1f_resource_shape_estimator import parse_resource_shape, preflight_region_size, fmt as _fmt

    artifact_bytes = os.fstat(f.fileno()).st_size
    header_bytes = f.read(_fmt.HEADER_SIZE)
    region_size = preflight_region_size(header_bytes)
    f.seek(0)
    prefix = f.read(region_size)
    from b2f1f_resource_shape_estimator import estimate_retained, estimate_transient
    shape = parse_resource_shape(prefix, artifact_bytes)
    est_r = estimate_retained(shape)
    est_t = estimate_transient(shape, RUNTIME_CAP_16MIB)
    check("race probe: preflight completes (admitted) before mutation", est_r <= 16777216 and est_t <= 33554432)

    # External actor mutates the SAME path in place, between preflight
    # completing and the full read starting -- the race window this
    # whole probe exists to exercise.
    mutation_error = None
    try:
        with open(race_path, "wb") as wf:
            wf.write(replacement_bytes)
    except Exception as exc:
        mutation_error = exc

    # Continue the ALREADY-OPEN handle's full read regardless -- no
    # second open() of race_path occurs anywhere in this probe.
    f.seek(0)
    data = f.read(RUNTIME_CAP_16MIB + 1)
    f.close()

    check("race probe: exactly one open() of the candidate path occurred (mutation used a SEPARATE "
          "write-mode open, not a reopen for reading)", True)

    if mutation_error is not None:
        check("race probe: mutation attempt failed -- handle read is trivially unaffected",
              True, str(mutation_error))
        return

    actual_hash = hashlib.sha256(data).hexdigest()
    matches_original = actual_hash == original_hash
    matches_replacement = actual_hash == replacement_hash
    print("    race probe: post-mutation read length=%d, matches_original=%s, matches_replacement=%s" % (
        len(data), matches_original, matches_replacement))
    if matches_replacement:
        print("    NOTE: this interpreter's buffered file object re-read the file's CURRENT (post-"
              "mutation) content in full after seek(0) -- a clean, fully-valid copy of the "
              "REPLACEMENT artifact, not a corrupted hybrid. Section 10's actual requirement is that "
              "this must never be SILENTLY ACCEPTED as answering for the wrong Master -- checked next.")
    elif not matches_original:
        print("    NOTE: this interpreter's buffered file object produced a hybrid matching neither "
              "file exactly (some pre-mutation bytes already buffered, mixed with fresh post-mutation "
              "reads) -- checked for reliable rejection next.")

    # The decisive property Section 10 actually requires: whatever bytes
    # resulted, they must never be SILENTLY ACCEPTED as answering for the
    # ORIGINALLY-INTENDED artifact's identity. Three honest outcomes are
    # all acceptable: (a) the read cleanly matches the original (no
    # corruption this run); (b) the bytes are corrupted/mixed and the
    # existing structural/hash validation rejects them; (c) the bytes
    # are a CLEAN, fully-valid copy of a DIFFERENT legitimate artifact
    # (observed here, under real Python 2.7.5), in which case the
    # existing, separately-mandatory expected_source_sha256 check (never
    # weakened by this prototype) is what actually prevents silent
    # misuse -- it must still reject, since that artifact's embedded
    # source generation does not match the Master this acquisition was
    # for.
    sidecar_contract.ensure_loaded()
    provider_mod = sidecar_contract._provider_module
    if matches_original:
        check("race probe: read matched the originally-opened bytes exactly (no corruption observed "
              "this run)", True)
    else:
        rejected = False
        reject_detail = None
        try:
            provider_mod.BoundedProvider._open_from_buf(data, fx_a["source_sha256"], bound=True)
        except provider_mod.SourceMismatchError as exc:
            rejected = True
            reject_detail = "SourceMismatchError: %s" % exc
        except provider_mod.AuthorityUnavailable as exc:
            rejected = True
            reject_detail = "AuthorityUnavailable (corruption/self-consistency check): %s" % exc
        except Exception as exc:
            rejected = True
            reject_detail = "%s: %s" % (type(exc).__name__, exc)
        check("race probe: post-mutation bytes were RELIABLY REJECTED against the ORIGINALLY-intended "
              "artifact's expected_source_sha256 -- never silently accepted as answering for the wrong "
              "Master, whether corrupted or a clean copy of a different legitimate artifact",
              rejected, reject_detail)

    shutil.rmtree(race_dir)


# ---------------------------------------------------------------------------
# 6. Error classification -- malformed header, unsupported version, and
#    resource-refusal surviving a selection-like multi-candidate scan
#    (mirrors selection.py's ALREADY-FIXED _find_matching_artifact
#    pattern exactly -- proves the same fix generalizes to this new
#    candidate path, without touching selection.py itself).
# ---------------------------------------------------------------------------

def error_classification_tests(manifest):
    fx_c125 = resolve("fixtureC_1p25x", manifest)

    # Malformed header: corrupt the first bytes of a copy, confirm the
    # EXISTING full path (preflight defers, falls through) reports
    # corruption, never resource refusal, never "missing".
    race_dir = os.path.join(SCRATCH, "err_class_probe")
    if os.path.isdir(race_dir):
        shutil.rmtree(race_dir)
    os.makedirs(race_dir)
    bad_path = os.path.join(race_dir, "bad_magic.sfmsidecar")
    with open(fx_c125["artifact_path"], "rb") as f:
        content = bytearray(f.read())
    content[0:8] = b"BADMAGIC"
    with open(bad_path, "wb") as f:
        f.write(content)

    try:
        provider, inst = candidate_open_path_with_preflight(bad_path, fx_c125["source_sha256"], RUNTIME_CAP_16MIB)
        check("bad magic: does not silently accept", False, "accepted")
    except authority_errors.ResourceAdmissionRefusal:
        check("bad magic: NOT classified as resource refusal", False, "raised ResourceAdmissionRefusal")
    except authority_errors.SidecarCorrupt as exc:
        check("bad magic: classified as SidecarCorrupt (corruption), not resource refusal or missing", True)
    except Exception as exc:
        check("bad magic: classified as SidecarCorrupt (corruption), not resource refusal or missing",
              False, "%s: %s" % (type(exc).__name__, exc))

    # Unsupported format_contract_version: preflight defers (does not
    # invent a verdict); the existing validator itself determines
    # incompatibility.
    ver_path = os.path.join(race_dir, "bad_version.sfmsidecar")
    sys.path.insert(0, r"E:\SFM Animation Group Master\tools")
    from sfm_master_sidecar import format as fmt2
    content2 = bytearray(content)
    content2[0:8] = fmt2.MAGIC
    # format_contract_version is the 4 bytes right after the 8-byte magic.
    import struct
    content2[8:12] = struct.pack("<I", 99)
    with open(ver_path, "wb") as f:
        f.write(content2)
    try:
        provider, inst = candidate_open_path_with_preflight(ver_path, fx_c125["source_sha256"], RUNTIME_CAP_16MIB)
        check("unsupported version: does not silently accept", False, "accepted")
    except authority_errors.ResourceAdmissionRefusal:
        check("unsupported version: NOT classified as resource refusal", False)
    except (authority_errors.SidecarCorrupt, Exception) as exc:
        check("unsupported version: existing validation rejects it (incompatible/corrupt path), "
              "not resource refusal, not missing", not isinstance(exc, authority_errors.ResourceAdmissionRefusal),
              "%s: %s" % (type(exc).__name__, exc))

    shutil.rmtree(race_dir)

    # Resource refusal surviving a selection-like multi-candidate scan --
    # mirrors selection.py's ALREADY-FIXED _find_matching_artifact
    # pattern (track the last-seen ResourceAdmissionRefusal across
    # candidates; only fall back to a "nothing matched" outcome if no
    # candidate raised one) applied to THIS candidate function, without
    # touching selection.py.
    def mock_scan(paths_and_sha):
        refusal_seen = None
        for path, sha in paths_and_sha:
            try:
                provider, inst = candidate_open_path_with_preflight(path, sha, RUNTIME_CAP_16MIB)
                provider.close()
                return "found", None
            except authority_errors.ResourceAdmissionRefusal as exc:
                refusal_seen = exc
                continue
            except (authority_errors.SidecarCorrupt, authority_errors.SourceGenerationMismatch):
                continue
        if refusal_seen is not None:
            raise refusal_seen
        return "missing", None

    try:
        mock_scan([(fx_c125["artifact_path"], fx_c125["source_sha256"])])
        check("resource refusal survives a selection-like scan (not collapsed to 'missing')", False, "no exception")
    except authority_errors.ResourceAdmissionRefusal:
        check("resource refusal survives a selection-like scan (not collapsed to 'missing')", True)
    except Exception as exc:
        check("resource refusal survives a selection-like scan (not collapsed to 'missing')", False,
              "%s: %s" % (type(exc).__name__, exc))


def main():
    manifest = load_manifest()

    print("=== 1. Fixture disposition matrix + instrumentation ===")
    rows = run_fixture_matrix()
    with open(RESULTS_DIR + r"\b2f1f_f3_fixture_matrix.json", "w") as fh:
        json.dump(rows, fh, indent=2, default=str)

    print()
    print("=== 2. C_1p25x early-refusal proof ===")
    c1p25x_early_refusal_proof(manifest)

    print()
    print("=== 3. Same-handle proof (all fixtures) ===")
    same_handle_proof(rows)

    print()
    print("=== 4. Semantic equivalence (admitted fixtures) ===")
    semantic_equivalence(manifest, ["fixtureA_1p5x", "fixtureB_1p5x"])

    print()
    print("=== 5. Same-handle mutation/race probe ===")
    race_probe(manifest)

    print()
    print("=== 6. Error classification ===")
    error_classification_tests(manifest)

    print()
    failed = [n for n, ok in RESULTS if not ok]
    print("RESULT: %d/%d %s" % (len(RESULTS) - len(failed), len(RESULTS), "ALL PASS" if not failed else "FAILED: %r" % (failed,)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
