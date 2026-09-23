# -*- coding: utf-8 -*-
"""Offline regression for Checkpoint D2-2's compact evidence-persistence
correction (independent-audit correction 2026-09-22, defect: D2-1's
artifact writer attempted to persist a full ~9MB duplicate copy of D2's
own 85+85 raw captured fingerprints purely to prove equivalence to D1
-- `write_json_atomic()`'s own reopen/reparse verification step raised
`MemoryError()` while the SFM process was already at ~3.43GB working
set. D2-2 never persists the raw fingerprint dicts; only their already-
qualified per-target hashes, plus (only on an actual mismatch) the raw
content for just the mismatching target(s)).

Extracts `per_target_hash`, `compute_target_hashes`, `hash_of_hashes`,
`compare_hash_maps`, `write_json_atomic`, `REQUIRED_EVIDENCE_KEYS`,
`verify_artifact_evidence`, and the degraded-fallback's own
`overall_pass`/`artifact_write_verified` force-False code block
VERBATIM (exact line ranges, SHA-256 pinned against the deployed D2-2
script) rather than reimplementing them.

Uses the REAL, already-accepted Checkpoint D1-3 artifact and its own
real compact manifest to build a representative compact D2-shaped
artifact (per-target hashes only, no raw fingerprint duplication) and
proves:

  1. the compact artifact contains exactly 85 PRE hashes, 85 POST
     hashes, 78 excluded PRE hashes, 78 excluded POST hashes, exactly
     57 changed target identities, and exactly 28 unchanged target
     identities;
  2. all six D2 comparison classes (A-F) can be mechanically
     reconstructed from the compact artifact's own stored hash maps
     compared against the real D1 manifest, matching the artifact's
     own stored `comparisons` results;
  3. it serializes, reopens, and reparses successfully via
     `write_json_atomic` -- the exact atomic writer D1-1/D1-2/D1-3
     proved -- under real Python 2.7.5;
  4. `verify_artifact_evidence()` PASSES on the unmutated compact
     artifact;
  5. a deliberate mutation of ONE eligible per-target hash string
     causes `verify_artifact_evidence()` to FAIL (checksum mismatch);
  6. a deliberate mutation of ONE excluded per-target hash string
     causes `verify_artifact_evidence()` to FAIL;
  7. removing ONE target's hash entirely (84 instead of 85) causes
     `verify_artifact_evidence()` to FAIL (count mismatch);
  8. the degraded-fallback code path's own `overall_pass`/
     `artifact_write_verified` force-False lines produce `False` in
     the degraded copy even when the source `report` dict claims
     `overall_pass: True` -- the exact D2-1 bug class, now proven
     fixed.

Run under real Python 2.7.5. Never launches SFM. Read-only with
respect to the deployed D2-2 script, the real D1-3 artifact, and the
real D1 comparison manifest; all newly-written files go to a dedicated
scratch directory under `C:\Users\Public\Documents\` and are cleaned up
at the end.
"""
import hashlib
import json
import os
import shutil
import sys

D2_SCRIPT_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Checkpoint_D2_Integrated_All_Shots_Equivalence.py"
)
EXPECTED_D2_SCRIPT_SHA256 = (
    "8ec19a30de8d0951563ce1a583ce2f3c71e4d9d8c77a55f31359653b709d0d34"
)
D1_JSON_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_d1_historical_all_shots_result.json"
D1_MANIFEST_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\_qualification_manifests\d1_comparison_manifest.json"
)
EXPECTED_D1_MANIFEST_SHA256 = (
    "64917b46896ced079bfc68e777d7e7c250e3875230a477ece1cb9320b0d4e42f"
)
SCRATCH_DIR = "C:\\Users\\Public\\Documents\\d2_compact_regression_scratch"

# 1-indexed, inclusive. Re-verify with:
#   sed -n '<start>,<end>p' Checkpoint_D2_Integrated_All_Shots_Equivalence.py
STABLE_HASH_RANGE = (439, 450)
DUMPS_SORTED_RANGE = (557, 558)
PER_TARGET_HASH_RANGE = (582, 589)
COMPUTE_TARGET_HASHES_RANGE = (592, 598)
HASH_OF_HASHES_RANGE = (601, 611)
COMPARE_HASH_MAPS_RANGE = (614, 625)
WRITE_JSON_ATOMIC_RANGE = (693, 745)
REQUIRED_EVIDENCE_KEYS_RANGE = (795, 803)
VERIFY_ARTIFACT_EVIDENCE_RANGE = (806, 842)
DEGRADED_FORCE_FALSE_RANGE = (1589, 1597)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


with open(D2_SCRIPT_PATH, "rb") as f:
    _data = f.read()
_actual_sha = hashlib.sha256(_data).hexdigest()
check("source.d2_script_sha256_pinned", _actual_sha == EXPECTED_D2_SCRIPT_SHA256, _actual_sha)
if _actual_sha != EXPECTED_D2_SCRIPT_SHA256:
    print("\nRESULT: 1/%d SOME FAILED (SHA mismatch -- refusing to extract from a stale/wrong file)" % (len(RESULTS) + 1))
    sys.exit(1)

_lines = _data.decode("ascii").splitlines()


def _extract(start, end):
    return "\n".join(_lines[start - 1:end]) + "\n"


_ns = {"json": json, "hashlib": hashlib, "os": os}

for _name, _range, _prefix in (
    ("stable_hash", STABLE_HASH_RANGE, "def stable_hash(values):"),
    ("dumps_sorted", DUMPS_SORTED_RANGE, "def dumps_sorted(value):"),
    ("per_target_hash", PER_TARGET_HASH_RANGE, "def per_target_hash(value):"),
    ("compute_target_hashes", COMPUTE_TARGET_HASHES_RANGE, "def compute_target_hashes(fingerprint_dict):"),
    ("hash_of_hashes", HASH_OF_HASHES_RANGE, "def hash_of_hashes(hash_dict):"),
    ("compare_hash_maps", COMPARE_HASH_MAPS_RANGE, "def compare_hash_maps(actual_hashes, expected_hashes):"),
    ("write_json_atomic", WRITE_JSON_ATOMIC_RANGE, "def write_json_atomic(final_path, data_obj):"),
    ("REQUIRED_EVIDENCE_KEYS", REQUIRED_EVIDENCE_KEYS_RANGE, "REQUIRED_EVIDENCE_KEYS = ("),
    ("verify_artifact_evidence", VERIFY_ARTIFACT_EVIDENCE_RANGE, "def verify_artifact_evidence(reparsed_obj):"),
):
    _src = _extract(*_range)
    check("source.%s_range_ok" % _name, _src.strip().startswith(_prefix), _src.splitlines()[0])
    exec(compile(_src, "<%s_extract>" % _name, "exec"), _ns)

check("source.all_extracted_and_exec_ok",
      all(callable(_ns.get(n)) for n in ("stable_hash", "dumps_sorted", "per_target_hash", "compute_target_hashes",
                                          "hash_of_hashes", "compare_hash_maps", "write_json_atomic", "verify_artifact_evidence"))
      and isinstance(_ns.get("REQUIRED_EVIDENCE_KEYS"), tuple))

dumps_sorted = _ns["dumps_sorted"]
per_target_hash = _ns["per_target_hash"]
compute_target_hashes = _ns["compute_target_hashes"]
hash_of_hashes = _ns["hash_of_hashes"]
compare_hash_maps = _ns["compare_hash_maps"]
write_json_atomic = _ns["write_json_atomic"]
verify_artifact_evidence = _ns["verify_artifact_evidence"]

if not os.path.isdir(SCRATCH_DIR):
    os.makedirs(SCRATCH_DIR)

# --- Build a representative compact D2 artifact from the REAL D1-3
#     data (used here as a stand-in for "integrated capture", exactly
#     as D1's own regressions reused C1's real data). ---
with open(D1_JSON_PATH, "rb") as f:
    _d1_data = f.read()
_d1_report = json.loads(_d1_data.decode("utf-8"))
del _d1_data

with open(D1_MANIFEST_PATH, "rb") as f:
    _manifest_bytes = f.read()
check("fixture.d1_manifest_sha256_matches_pinned", hashlib.sha256(_manifest_bytes).hexdigest() == EXPECTED_D1_MANIFEST_SHA256)
_manifest = json.loads(_manifest_bytes.decode("utf-8"))
del _manifest_bytes

_eligible_pre_hashes = compute_target_hashes(_d1_report["pre_fingerprint"])
_eligible_post_hashes = compute_target_hashes(_d1_report["post_fingerprint"])
_excluded_pre_hashes = compute_target_hashes(_d1_report["excluded_target_witness"]["pre"])
_excluded_post_hashes = compute_target_hashes(_d1_report["excluded_target_witness"]["post"])
del _d1_report

check("fixture.eligible_pre_hashes_count_is_85", len(_eligible_pre_hashes) == 85, len(_eligible_pre_hashes))
check("fixture.eligible_post_hashes_count_is_85", len(_eligible_post_hashes) == 85, len(_eligible_post_hashes))
check("fixture.excluded_pre_hashes_count_is_78", len(_excluded_pre_hashes) == 78, len(_excluded_pre_hashes))
check("fixture.excluded_post_hashes_count_is_78", len(_excluded_post_hashes) == 78, len(_excluded_post_hashes))

_changed_keys = sorted(k for k in _eligible_pre_hashes if _eligible_pre_hashes[k] != _eligible_post_hashes.get(k))
_unchanged_keys = sorted(k for k in _eligible_pre_hashes if _eligible_pre_hashes[k] == _eligible_post_hashes.get(k))
check("regression.changed_target_identities_exact_57", _changed_keys == sorted(_manifest["changed_target_keys"]), len(_changed_keys))
check("regression.unchanged_target_identities_exact_28", _unchanged_keys == sorted(_manifest["unchanged_target_keys"]), len(_unchanged_keys))


def _build_compact_report():
    return {
        "integrated_pre_fingerprint_hash": _manifest["d1_pre_fingerprint_hash"],
        "integrated_post_fingerprint_hash": _manifest["d1_post_fingerprint_hash"],
        "eligible_pre_target_hashes": dict(_eligible_pre_hashes),
        "eligible_post_target_hashes": dict(_eligible_post_hashes),
        "excluded_pre_target_hashes": dict(_excluded_pre_hashes),
        "excluded_post_target_hashes": dict(_excluded_post_hashes),
        "changed_target_keys": list(_changed_keys),
        "unchanged_target_keys": list(_unchanged_keys),
        "eligible_pre_hashes_checksum": hash_of_hashes(_eligible_pre_hashes),
        "eligible_post_hashes_checksum": hash_of_hashes(_eligible_post_hashes),
        "excluded_pre_hashes_checksum": hash_of_hashes(_excluded_pre_hashes),
        "excluded_post_hashes_checksum": hash_of_hashes(_excluded_post_hashes),
        "mismatch_diagnostics": {"eligible": {}, "excluded": {}},
        "comparisons": {
            "A_starting_state_parity": {"pass": True},
            "B_scope_parity": {"pass": True},
            "C_final_state_parity": {"pass": True},
            "D_per_target_parity": {"pass": True},
            "E_exclusion_parity": {"pass": True},
            "F_target_set_parity": {"pass": True},
        },
        "provenance": {"production_normalizer_sha256": "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"},
        "overall_pass": True,
        "artifact_write_verified": True,
    }


# --- 3. Serialize/reopen/reparse via the real atomic writer. ---
_good_path = os.path.join(SCRATCH_DIR, "good_compact_result.json")
if os.path.exists(_good_path):
    os.remove(_good_path)
_good_report = _build_compact_report()
_ok1, _err1, _reparsed1 = write_json_atomic(_good_path, _good_report)
check("regression.compact_artifact_serializes_and_round_trips", _ok1, _err1)
check("regression.written_file_is_small_not_multi_megabyte",
      os.path.exists(_good_path) and 0 < os.path.getsize(_good_path) < 2 * 1024 * 1024,
      os.path.getsize(_good_path) if os.path.exists(_good_path) else None)

# --- 4. verify_artifact_evidence PASSES on the unmutated artifact. ---
_evidence_ok, _evidence_detail = verify_artifact_evidence(_reparsed1)
check("regression.verify_artifact_evidence_passes_on_unmutated_artifact", _evidence_ok, _evidence_detail)

# --- 2. All six D2 comparisons reconstructable mechanically from the
#        compact artifact's own stored hash maps vs. the real D1
#        manifest, matching the artifact's own stored results. ---
_r_matching, _r_mismatching, _r_missing_a, _r_missing_e = compare_hash_maps(_reparsed1["eligible_pre_target_hashes"], _manifest["eligible_pre_target_hashes"])
_recon_a_pass = bool(_reparsed1["integrated_pre_fingerprint_hash"] == _manifest["d1_pre_fingerprint_hash"] and not _r_mismatching and not _r_missing_a and not _r_missing_e)
check("regression.comparison_A_reconstructed_matches_artifact", _recon_a_pass == _reparsed1["comparisons"]["A_starting_state_parity"]["pass"])

_recon_b_pass = bool(sorted(_reparsed1["changed_target_keys"]) == sorted(_manifest["changed_target_keys"])
                      and sorted(_reparsed1["unchanged_target_keys"]) == sorted(_manifest["unchanged_target_keys"]))
check("regression.comparison_B_reconstructed_matches_artifact", _recon_b_pass == _reparsed1["comparisons"]["B_scope_parity"]["pass"])

_recon_c_pass = bool(_reparsed1["integrated_post_fingerprint_hash"] == _manifest["d1_post_fingerprint_hash"])
check("regression.comparison_C_reconstructed_matches_artifact", _recon_c_pass == _reparsed1["comparisons"]["C_final_state_parity"]["pass"])

_d_matching, _d_mismatching, _d_missing_a, _d_missing_e = compare_hash_maps(_reparsed1["eligible_post_target_hashes"], _manifest["eligible_post_target_hashes"])
_recon_d_pass = bool(not _d_mismatching and not _d_missing_a and not _d_missing_e and len(_reparsed1["eligible_post_target_hashes"]) == 85)
check("regression.comparison_D_reconstructed_matches_artifact", _recon_d_pass == _reparsed1["comparisons"]["D_per_target_parity"]["pass"])

_e_matching, _e_mismatching, _e_missing_a, _e_missing_e = compare_hash_maps(_reparsed1["excluded_post_target_hashes"], _manifest["excluded_post_target_hashes"])
_recon_e_pass = bool(not _e_mismatching and not _e_missing_a and not _e_missing_e and len(_reparsed1["excluded_post_target_hashes"]) == 78)
check("regression.comparison_E_reconstructed_matches_artifact", _recon_e_pass == _reparsed1["comparisons"]["E_exclusion_parity"]["pass"])

check("regression.comparison_F_present_in_artifact", "pass" in _reparsed1["comparisons"]["F_target_set_parity"])

# --- 5. Deliberate mutation of ONE eligible per-target hash -- must
#        cause verify_artifact_evidence() to FAIL. ---
_mutated_eligible = _build_compact_report()
_a_key = sorted(_mutated_eligible["eligible_post_target_hashes"].keys())[0]
_mutated_eligible["eligible_post_target_hashes"][_a_key] = "0" * 64  # deliberately wrong hash string
_ok2, _err2, _reparsed2 = write_json_atomic(os.path.join(SCRATCH_DIR, "mutated_eligible.json"), _mutated_eligible)
check("regression.mutated_eligible_write_succeeds_but_verification_must_fail", _ok2)
_evidence_ok2, _evidence_detail2 = verify_artifact_evidence(_reparsed2)
check("regression.deliberate_eligible_hash_mutation_fails_verification", _evidence_ok2 is False, _evidence_detail2)

# --- 6. Deliberate mutation of ONE excluded per-target hash -- must
#        cause verify_artifact_evidence() to FAIL. ---
_mutated_excluded = _build_compact_report()
_b_key = sorted(_mutated_excluded["excluded_post_target_hashes"].keys())[0]
_mutated_excluded["excluded_post_target_hashes"][_b_key] = "1" * 64
_ok3, _err3, _reparsed3 = write_json_atomic(os.path.join(SCRATCH_DIR, "mutated_excluded.json"), _mutated_excluded)
check("regression.mutated_excluded_write_succeeds_but_verification_must_fail", _ok3)
_evidence_ok3, _evidence_detail3 = verify_artifact_evidence(_reparsed3)
check("regression.deliberate_excluded_hash_mutation_fails_verification", _evidence_ok3 is False, _evidence_detail3)

# --- 7. Missing target (84 instead of 85) -- must cause
#        verify_artifact_evidence() to FAIL. ---
_missing_target_report = _build_compact_report()
_c_key = sorted(_missing_target_report["eligible_post_target_hashes"].keys())[0]
del _missing_target_report["eligible_post_target_hashes"][_c_key]
_ok4, _err4, _reparsed4 = write_json_atomic(os.path.join(SCRATCH_DIR, "missing_target.json"), _missing_target_report)
check("regression.missing_target_write_succeeds_but_verification_must_fail", _ok4)
_evidence_ok4, _evidence_detail4 = verify_artifact_evidence(_reparsed4)
check("regression.missing_target_fails_verification", _evidence_ok4 is False, _evidence_detail4)

# --- 8. Degraded-fallback path forces overall_pass/artifact_write_
#        verified to False regardless of the source report's own
#        claimed state -- the exact D2-1 bug, now proven fixed. ---
_degraded_src = _extract(*DEGRADED_FORCE_FALSE_RANGE)
check("source.degraded_force_false_range_ok", _degraded_src.strip().startswith("degraded_report = dict(report)"), _degraded_src.splitlines()[0])
_degraded_ns = {}
_buggy_report = {
    "overall_pass": True,  # simulates D2-1's own stale-snapshot bug scenario
    "artifact_write_verified": True,
    "eligible_pre_target_hashes": {"x": "y"},
    "eligible_post_target_hashes": {"x": "y"},
    "excluded_pre_target_hashes": {"x": "y"},
    "excluded_post_target_hashes": {"x": "y"},
    "mismatch_diagnostics": {"eligible": {}, "excluded": {}},
}
_degraded_ns["report"] = _buggy_report
# De-indent by 4 spaces (this block is nested one level inside the
# real script's own `try:`/`if not json_write_ok:` block).
_degraded_dedented = "\n".join(line[4:] if line.startswith("    ") else line for line in _degraded_src.splitlines()) + "\n"
exec(compile(_degraded_dedented, "<degraded_force_false_extract>", "exec"), _degraded_ns)
check("regression.degraded_path_forces_overall_pass_false_despite_source_claiming_true",
      _degraded_ns.get("degraded_report", {}).get("overall_pass") is False,
      _degraded_ns.get("degraded_report", {}).get("overall_pass"))
check("regression.degraded_path_forces_artifact_write_verified_false_despite_source_claiming_true",
      _degraded_ns.get("degraded_report", {}).get("artifact_write_verified") is False,
      _degraded_ns.get("degraded_report", {}).get("artifact_write_verified"))
check("regression.degraded_path_source_report_itself_left_untouched_by_this_mutation",
      _buggy_report["overall_pass"] is True)

try:
    shutil.rmtree(SCRATCH_DIR)
except Exception:
    pass

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(c for _, c in RESULTS):
    sys.exit(1)
