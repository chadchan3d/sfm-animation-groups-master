# -*- coding: utf-8 -*-
"""Offline regression for Checkpoint D2's compact-manifest comparison
logic (per the governing D2 brief, Section 3): proves that comparing
Checkpoint D1's own data against itself through the compact D1
comparison manifest produces full parity, and that a deliberate
mutation is correctly detected -- both at the eligible-target level and
at the excluded-witness level.

Extracts `per_target_hash`, `compute_target_hashes`, `compare_hash_maps`,
and `stream_file_sha256` VERBATIM (exact line ranges, SHA-256 pinned
against the deployed D2 script) rather than reimplementing them.

Uses the REAL, already-accepted Checkpoint D1-3 artifact and its own
real compact manifest (both already on disk) -- not synthetic toy
data. Since D2's own comparison logic only ever needs D1's own
PER-TARGET HASHES (never D1's raw fingerprint dicts), this regression
simulates "integrated capture equals D1 capture" by computing fresh
per-target hashes from D1's own raw fingerprint data (read once, here,
offline -- this tool is not memory-constrained the way D2's own SFM
runtime is) and comparing them against the manifest's own stored
hashes, proving:

  1. PRE aggregate parity (D1's own pre_fingerprint_hash matches the
     manifest's own pinned value);
  2. POST aggregate parity (same, for post_fingerprint_hash);
  3. 85/85 eligible per-target parity (zero mismatching, zero missing
     in either direction);
  4. the exact 57-target changed set and exact 28-target unchanged set
     recomputed from D1's own PRE/POST per-target hashes match the
     manifest's own stored changed/unchanged sets exactly;
  5. 78/78 excluded-witness per-target parity;
  6. target-set-diff expectations are all empty (no additions/
     removals/reclassifications), matching the manifest's own stored
     expectations;
  7. a deliberate mutation of ONE semantic field in a COPIED eligible
     target is correctly detected as exactly one mismatching target,
     named precisely;
  8. a deliberate mutation of ONE field in a COPIED excluded witness
     row is correctly detected as exactly one mismatching excluded
     target, named precisely.

Run under real Python 2.7.5. Never launches SFM. Read-only with
respect to the deployed D2 script, the real D1-3 artifact, and the
real D1 comparison manifest.
"""
import hashlib
import json
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
EXPECTED_D1_ARTIFACT_SHA256 = (
    "55cd0447f3d215afaa4fa334b1daf2d905055363972ead524672da822ed6e85f"
)
EXPECTED_D1_MANIFEST_SHA256 = (
    "64917b46896ced079bfc68e777d7e7c250e3875230a477ece1cb9320b0d4e42f"
)

# 1-indexed, inclusive. Re-verify with:
#   sed -n '<start>,<end>p' Checkpoint_D2_Integrated_All_Shots_Equivalence.py
DUMPS_SORTED_RANGE = (557, 558)
PER_TARGET_HASH_RANGE = (582, 589)
COMPUTE_TARGET_HASHES_RANGE = (592, 598)
COMPARE_HASH_MAPS_RANGE = (614, 625)
STREAM_FILE_SHA256_RANGE = (628, 641)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


# Module-level (not inside a function): Python 2's `exec` statement is
# disallowed inside any function that also contains a nested `def`/class
# with free variables -- top-level placement sidesteps it, same as this
# project's other extraction-based harnesses.

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


_ns = {"json": json, "hashlib": hashlib, "open": open}

_src_dumps_sorted = _extract(*DUMPS_SORTED_RANGE)
check("source.dumps_sorted_range_ok", _src_dumps_sorted.strip().startswith("def dumps_sorted(value):"), _src_dumps_sorted.splitlines()[0])
exec(compile(_src_dumps_sorted, "<dumps_sorted_extract>", "exec"), _ns)

_src_per_target_hash = _extract(*PER_TARGET_HASH_RANGE)
check("source.per_target_hash_range_ok", _src_per_target_hash.strip().startswith("def per_target_hash(value):"), _src_per_target_hash.splitlines()[0])
exec(compile(_src_per_target_hash, "<per_target_hash_extract>", "exec"), _ns)

_src_compute_target_hashes = _extract(*COMPUTE_TARGET_HASHES_RANGE)
check("source.compute_target_hashes_range_ok", _src_compute_target_hashes.strip().startswith("def compute_target_hashes(fingerprint_dict):"), _src_compute_target_hashes.splitlines()[0])
exec(compile(_src_compute_target_hashes, "<compute_target_hashes_extract>", "exec"), _ns)

_src_compare_hash_maps = _extract(*COMPARE_HASH_MAPS_RANGE)
check("source.compare_hash_maps_range_ok", _src_compare_hash_maps.strip().startswith("def compare_hash_maps(actual_hashes, expected_hashes):"), _src_compare_hash_maps.splitlines()[0])
exec(compile(_src_compare_hash_maps, "<compare_hash_maps_extract>", "exec"), _ns)

_src_stream_file_sha256 = _extract(*STREAM_FILE_SHA256_RANGE)
check("source.stream_file_sha256_range_ok", _src_stream_file_sha256.strip().startswith("def stream_file_sha256(path, chunk_size=1048576):"), _src_stream_file_sha256.splitlines()[0])
exec(compile(_src_stream_file_sha256, "<stream_file_sha256_extract>", "exec"), _ns)

check("source.all_extracted_and_exec_ok",
      all(callable(_ns.get(n)) for n in ("dumps_sorted", "per_target_hash", "compute_target_hashes", "compare_hash_maps", "stream_file_sha256")))

dumps_sorted = _ns["dumps_sorted"]
per_target_hash = _ns["per_target_hash"]
compute_target_hashes = _ns["compute_target_hashes"]
compare_hash_maps = _ns["compare_hash_maps"]
stream_file_sha256 = _ns["stream_file_sha256"]

# --- stream_file_sha256 correctness: must match a plain full-file hash. ---
with open(D1_JSON_PATH, "rb") as f:
    _d1_full_bytes = f.read()
_d1_full_sha_plain = hashlib.sha256(_d1_full_bytes).hexdigest()
_d1_full_sha_streamed = stream_file_sha256(D1_JSON_PATH)
check("regression.stream_file_sha256.matches_plain_full_read_hash", _d1_full_sha_streamed == _d1_full_sha_plain, (_d1_full_sha_streamed, _d1_full_sha_plain))
check("regression.stream_file_sha256.matches_pinned_d1_artifact_sha256", _d1_full_sha_streamed == EXPECTED_D1_ARTIFACT_SHA256, _d1_full_sha_streamed)

_d1_report = json.loads(_d1_full_bytes.decode("utf-8"))
del _d1_full_bytes

with open(D1_MANIFEST_PATH, "rb") as f:
    _manifest_bytes = f.read()
_manifest_sha = hashlib.sha256(_manifest_bytes).hexdigest()
check("fixture.d1_manifest_sha256_matches_pinned", _manifest_sha == EXPECTED_D1_MANIFEST_SHA256, _manifest_sha)
_manifest = json.loads(_manifest_bytes.decode("utf-8"))
del _manifest_bytes

# --- 1/2. PRE and POST aggregate parity: the manifest's own pinned
#          values must match D1's own report fields exactly. ---
check("regression.pre_aggregate_parity", _manifest["d1_pre_fingerprint_hash"] == _d1_report["pre_fingerprint_hash"])
check("regression.post_aggregate_parity", _manifest["d1_post_fingerprint_hash"] == _d1_report["post_fingerprint_hash"])

# --- 3. 85/85 eligible per-target parity: fresh per-target hashes
#        computed from D1's own raw PRE/POST fingerprints must exactly
#        match the manifest's own stored per-target hashes. ---
_fresh_pre_hashes = compute_target_hashes(_d1_report["pre_fingerprint"])
_fresh_post_hashes = compute_target_hashes(_d1_report["post_fingerprint"])

_pre_matching, _pre_mismatching, _pre_missing_a, _pre_missing_e = compare_hash_maps(_fresh_pre_hashes, _manifest["eligible_pre_target_hashes"])
check("regression.pre_per_target_parity_85_of_85",
      len(_pre_matching) == 85 and not _pre_mismatching and not _pre_missing_a and not _pre_missing_e,
      (len(_pre_matching), _pre_mismatching, _pre_missing_a, _pre_missing_e))

_post_matching, _post_mismatching, _post_missing_a, _post_missing_e = compare_hash_maps(_fresh_post_hashes, _manifest["eligible_post_target_hashes"])
check("regression.post_per_target_parity_85_of_85",
      len(_post_matching) == 85 and not _post_mismatching and not _post_missing_a and not _post_missing_e,
      (len(_post_matching), _post_mismatching, _post_missing_a, _post_missing_e))

# --- 4. Exact 57-changed / 28-unchanged set, recomputed fresh from
#        D1's own PRE/POST hashes, matches the manifest exactly. ---
_recomputed_changed = sorted(k for k in _fresh_pre_hashes if _fresh_pre_hashes[k] != _fresh_post_hashes.get(k))
_recomputed_unchanged = sorted(k for k in _fresh_pre_hashes if _fresh_pre_hashes[k] == _fresh_post_hashes.get(k))
check("regression.changed_set_exact_57", _recomputed_changed == sorted(_manifest["changed_target_keys"]), len(_recomputed_changed))
check("regression.unchanged_set_exact_28", _recomputed_unchanged == sorted(_manifest["unchanged_target_keys"]), len(_recomputed_unchanged))

# --- 5. 78/78 excluded-witness parity. ---
_fresh_excluded_pre_hashes = compute_target_hashes(_d1_report["excluded_target_witness"]["pre"])
_fresh_excluded_post_hashes = compute_target_hashes(_d1_report["excluded_target_witness"]["post"])

_excl_pre_matching, _excl_pre_mismatching, _excl_pre_missing_a, _excl_pre_missing_e = compare_hash_maps(_fresh_excluded_pre_hashes, _manifest["excluded_pre_target_hashes"])
check("regression.excluded_pre_parity_78_of_78",
      len(_excl_pre_matching) == 78 and not _excl_pre_mismatching and not _excl_pre_missing_a and not _excl_pre_missing_e,
      (len(_excl_pre_matching), _excl_pre_mismatching))

_excl_post_matching, _excl_post_mismatching, _excl_post_missing_a, _excl_post_missing_e = compare_hash_maps(_fresh_excluded_post_hashes, _manifest["excluded_post_target_hashes"])
check("regression.excluded_post_parity_78_of_78",
      len(_excl_post_matching) == 78 and not _excl_post_mismatching and not _excl_post_missing_a and not _excl_post_missing_e,
      (len(_excl_post_matching), _excl_post_mismatching))

# --- 6. Zero additions/removals/reclassifications. ---
_tsd = _manifest["target_set_diff_expectations"]
check("regression.target_set_diff_all_empty",
      _tsd.get("missing_targets_entirely") == [] and _tsd.get("new_targets_entirely") == []
      and _tsd.get("reclassified_eligible_to_excluded") == [] and _tsd.get("reclassified_excluded_to_eligible") == [],
      _tsd)

# --- 7. Deliberate mutation of ONE semantic field in a COPIED eligible
#        target -- must be detected as exactly one mismatching target,
#        named precisely. ---
_mutated_post = dict(_d1_report["post_fingerprint"])  # shallow copy of the dict of targets
_a_key = sorted(_mutated_post.keys())[0]
_mutated_target = dict(_mutated_post[_a_key])  # copy the one target's own dict before mutating
_mutated_target["control_count"] = (_mutated_target.get("control_count") or 0) + 999
_mutated_post[_a_key] = _mutated_target

_mutated_post_hashes = compute_target_hashes(_mutated_post)
_mut_matching, _mut_mismatching, _mut_missing_a, _mut_missing_e = compare_hash_maps(_mutated_post_hashes, _manifest["eligible_post_target_hashes"])
check("regression.deliberate_eligible_mutation_detected_as_exactly_one_mismatch",
      _mut_mismatching == [_a_key] and len(_mut_matching) == 84, (_mut_mismatching, len(_mut_matching)))
# The original (unmutated) D1 data itself must remain untouched by this test.
check("regression.original_d1_post_fingerprint_not_mutated_by_this_test",
      per_target_hash(_d1_report["post_fingerprint"][_a_key]) == _manifest["eligible_post_target_hashes"][_a_key])

# --- 8. Deliberate mutation of ONE field in a COPIED excluded witness
#        row -- must be detected as exactly one mismatching excluded
#        target, named precisely. ---
_mutated_excluded_post = dict(_d1_report["excluded_target_witness"]["post"])
_b_key = sorted(_mutated_excluded_post.keys())[0]
_mutated_excluded_row = dict(_mutated_excluded_post[_b_key])
_mutated_excluded_row["control_count"] = (_mutated_excluded_row.get("control_count") or 0) + 777
_mutated_excluded_post[_b_key] = _mutated_excluded_row

_mutated_excluded_hashes = compute_target_hashes(_mutated_excluded_post)
_mut_excl_matching, _mut_excl_mismatching, _mut_excl_missing_a, _mut_excl_missing_e = compare_hash_maps(_mutated_excluded_hashes, _manifest["excluded_post_target_hashes"])
check("regression.deliberate_excluded_mutation_detected_as_exactly_one_mismatch",
      _mut_excl_mismatching == [_b_key] and len(_mut_excl_matching) == 77, (_mut_excl_mismatching, len(_mut_excl_matching)))
check("regression.original_d1_excluded_post_not_mutated_by_this_test",
      per_target_hash(_d1_report["excluded_target_witness"]["post"][_b_key]) == _manifest["excluded_post_target_hashes"][_b_key])

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(c for _, c in RESULTS):
    sys.exit(1)
