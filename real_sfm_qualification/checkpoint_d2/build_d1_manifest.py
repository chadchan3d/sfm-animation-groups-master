# -*- coding: utf-8 -*-
"""
Offline, non-SFM tool: builds Checkpoint D2's compact, immutable D1
comparison manifest from the actual accepted Checkpoint D1-3 JSON
artifact on disk (C:\\Users\\Public\\Documents\\
sfm_checkpoint_d1_historical_all_shots_result.json).

Never launches SFM. Mechanically derived from the real D1-3 artifact
bytes, not from conversation text. Run once, offline, before D2
deployment; the resulting manifest is committed to the repo and
deployed alongside the D2 MAINMENU script.

Purpose (per the governing D2 brief, Section 2): D2's own SFM-embedded
runtime must never `json.load()` the entire ~5.9MB D1-3 artifact merely
to compare runtime state against it -- that would defeat the whole
point of D1-3's own memory correction. Instead, D2 loads only this
compact manifest (SHA-256 pinned) at runtime, and separately verifies
the full D1-3 artifact's own identity via a STREAMING SHA-256 (never
parsed) if/when artifact-existence provenance is checked.

This tool itself runs OFFLINE (outside the 32-bit SFM process), so
parsing the full D1-3 artifact here is not memory-constrained the same
way D2's own runtime is -- there is no correctness reason to avoid a
full parse in THIS tool.
"""
import hashlib
import json
import sys
import time

D1_JSON_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_d1_historical_all_shots_result.json"
MANIFEST_OUTPUT_PATH = "d1_comparison_manifest.json"

EXPECTED_D1_ARTIFACT_SHA256 = (
    "55cd0447f3d215afaa4fa334b1daf2d905055363972ead524672da822ed6e85f"
)
EXPECTED_HISTORICAL_BASELINE_SHA256 = (
    "6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e"
)
EXPECTED_PRODUCTION_NORMALIZER_SHA256 = (
    "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"
)
EXPECTED_CANONICAL_MASTER_SHA256 = (
    "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
)
EXPECTED_PRE_HASH = (
    "eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0"
)
EXPECTED_POST_HASH = (
    "299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7"
)


def check(name, condition, detail=None):
    status = "PASS" if condition else "FAIL"
    print("[%s] %s%s" % (status, name, ("" if condition else " -- %r" % (detail,))))
    if not condition:
        raise SystemExit("Manifest build refused: %s failed (%r)" % (name, detail))


def dumps_sorted(value):
    return json.dumps(value, sort_keys=True)


def per_target_hash(value):
    """Canonical per-target structural hash: SHA-256 of the target's
    own sort_keys=True JSON serialization. Reproducible identically in
    Checkpoint D2's own runtime (same dumps_sorted() helper, same
    embedded Python 2.7.5 json module)."""
    return hashlib.sha256(dumps_sorted(value).encode("utf-8")).hexdigest()


with open(D1_JSON_PATH, "rb") as f:
    d1_bytes = f.read()
d1_artifact_sha256 = hashlib.sha256(d1_bytes).hexdigest()
check("d1_artifact.sha256_matches_expected_accepted_run", d1_artifact_sha256 == EXPECTED_D1_ARTIFACT_SHA256, d1_artifact_sha256)

d1_report = json.loads(d1_bytes.decode("utf-8"))

check("d1_report.overall_pass_is_true", d1_report.get("overall_pass") is True, d1_report.get("overall_pass"))
check("d1_report.artifact_write_verified_is_true", d1_report.get("artifact_write_verified") is True, d1_report.get("artifact_write_verified"))
check("d1_report.pre_fingerprint_hash_matches_pinned", d1_report.get("pre_fingerprint_hash") == EXPECTED_PRE_HASH, d1_report.get("pre_fingerprint_hash"))
check("d1_report.post_fingerprint_hash_matches_pinned", d1_report.get("post_fingerprint_hash") == EXPECTED_POST_HASH, d1_report.get("post_fingerprint_hash"))

pre_fingerprint = d1_report["pre_fingerprint"]
post_fingerprint = d1_report["post_fingerprint"]
check("d1_report.pre_fingerprint_has_85_targets", len(pre_fingerprint) == 85, len(pre_fingerprint))
check("d1_report.post_fingerprint_has_85_targets", len(post_fingerprint) == 85, len(post_fingerprint))
check("d1_report.pre_and_post_target_key_sets_match", set(pre_fingerprint.keys()) == set(post_fingerprint.keys()))

changed_target_keys = sorted(d1_report["semantically_changed_target_set"])
unchanged_target_keys = sorted(d1_report["semantically_unchanged_target_set"])
check("d1_report.changed_target_count_is_57", len(changed_target_keys) == 57, len(changed_target_keys))
check("d1_report.unchanged_target_count_is_28", len(unchanged_target_keys) == 28, len(unchanged_target_keys))
check("d1_report.changed_plus_unchanged_equals_85_with_no_overlap",
      len(changed_target_keys) + len(unchanged_target_keys) == 85
      and not (set(changed_target_keys) & set(unchanged_target_keys)))
check("d1_report.changed_union_unchanged_equals_eligible_key_set",
      set(changed_target_keys) | set(unchanged_target_keys) == set(pre_fingerprint.keys()))

excluded_witness = d1_report["excluded_target_witness"]
excluded_pre = excluded_witness["pre"]
excluded_post = excluded_witness["post"]
check("d1_report.excluded_pre_has_78_targets", len(excluded_pre) == 78, len(excluded_pre))
check("d1_report.excluded_post_has_78_targets", len(excluded_post) == 78, len(excluded_post))
check("d1_report.excluded_pre_and_post_key_sets_match", set(excluded_pre.keys()) == set(excluded_post.keys()))
excluded_changed_target_keys = sorted(excluded_witness["changed_targets"])
check("d1_report.excluded_changed_set_is_empty", excluded_changed_target_keys == [], excluded_changed_target_keys)

target_set_diff = d1_report["target_set_diff"]
check("d1_report.target_set_diff_is_fully_empty",
      target_set_diff.get("missing_targets_entirely") == []
      and target_set_diff.get("new_targets_entirely") == []
      and target_set_diff.get("reclassified_eligible_to_excluded") == []
      and target_set_diff.get("reclassified_excluded_to_eligible") == [],
      target_set_diff)

eligible_pre_target_hashes = dict((k, per_target_hash(v)) for k, v in pre_fingerprint.items())
eligible_post_target_hashes = dict((k, per_target_hash(v)) for k, v in post_fingerprint.items())
excluded_pre_target_hashes = dict((k, per_target_hash(v)) for k, v in excluded_pre.items())
excluded_post_target_hashes = dict((k, per_target_hash(v)) for k, v in excluded_post.items())

manifest = {
    "manifest_format": "sfm_d2_comparison_manifest_v1",
    "manifest_build_identity": {
        "built_from_d1_artifact_path": D1_JSON_PATH,
        "built_from_d1_artifact_sha256": d1_artifact_sha256,
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "builder_note": (
            "Offline, non-SFM tool (real_sfm_qualification/checkpoint_d2/"
            "build_d1_manifest.py). Mechanically derived from the real, "
            "accepted D1-3 JSON artifact bytes -- never retyped from "
            "conversation text. This tool runs outside the 32-bit SFM "
            "process, so a full parse of the D1-3 artifact here carries "
            "none of the memory risk a full parse inside SFM's own "
            "runtime would."
        ),
    },
    "d1_artifact_sha256": d1_artifact_sha256,
    "d1_overall_pass": d1_report["overall_pass"],
    "d1_pre_fingerprint_hash": d1_report["pre_fingerprint_hash"],
    "d1_post_fingerprint_hash": d1_report["post_fingerprint_hash"],
    "eligible_target_keys": sorted(pre_fingerprint.keys()),
    "changed_target_keys": changed_target_keys,
    "unchanged_target_keys": unchanged_target_keys,
    "eligible_pre_target_hashes": eligible_pre_target_hashes,
    "eligible_post_target_hashes": eligible_post_target_hashes,
    "excluded_target_keys": sorted(excluded_pre.keys()),
    "excluded_pre_target_hashes": excluded_pre_target_hashes,
    "excluded_post_target_hashes": excluded_post_target_hashes,
    "excluded_changed_target_keys": excluded_changed_target_keys,
    "target_set_diff_expectations": target_set_diff,
    "fixture_totals": d1_report["fixture_totals"],
    "source_identities": {
        "historical_baseline_sha256": EXPECTED_HISTORICAL_BASELINE_SHA256,
        "production_normalizer_sha256": EXPECTED_PRODUCTION_NORMALIZER_SHA256,
        "canonical_master_sha256": EXPECTED_CANONICAL_MASTER_SHA256,
    },
}

with open(MANIFEST_OUTPUT_PATH, "wb") as f:
    # explicit separators avoid Python 2's default trailing space after
    # each comma before the newline (a cosmetic-only difference, but one
    # that trips `git diff --check` on every array/dict entry).
    f.write(json.dumps(manifest, indent=2, sort_keys=True, separators=(",", ": ")).encode("utf-8"))

with open(MANIFEST_OUTPUT_PATH, "rb") as f:
    manifest_bytes = f.read()
manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()

# Independent reopen/reparse verification of the manifest itself.
with open(MANIFEST_OUTPUT_PATH, "rb") as f:
    reparsed_manifest = json.loads(f.read().decode("utf-8"))
check("manifest.reopens_and_reparses_ok", reparsed_manifest == manifest)
check("manifest.eligible_pre_hashes_count_is_85", len(reparsed_manifest["eligible_pre_target_hashes"]) == 85)
check("manifest.eligible_post_hashes_count_is_85", len(reparsed_manifest["eligible_post_target_hashes"]) == 85)
check("manifest.excluded_pre_hashes_count_is_78", len(reparsed_manifest["excluded_pre_target_hashes"]) == 78)
check("manifest.excluded_post_hashes_count_is_78", len(reparsed_manifest["excluded_post_target_hashes"]) == 78)

print("")
print("Manifest written to: %s" % MANIFEST_OUTPUT_PATH)
print("Manifest size bytes: %d" % len(manifest_bytes))
print("Manifest SHA-256: %s" % manifest_sha256)
print("")
print("D1 artifact SHA-256 (pin into D2 as EXPECTED_D1_ARTIFACT_SHA256): %s" % d1_artifact_sha256)
print("D1 manifest SHA-256 (pin into D2 as EXPECTED_D1_MANIFEST_SHA256): %s" % manifest_sha256)
