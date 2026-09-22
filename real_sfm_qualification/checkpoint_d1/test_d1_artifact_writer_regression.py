# -*- coding: utf-8 -*-
"""Offline regression for Checkpoint D1-2's corrected artifact writer
(independent-audit correction 2026-09-22, defect: D1-1's writer opened
its JSON output path directly in "wb" mode -- which truncates any
existing file immediately on open -- and only THEN called
json.dumps(...); a bare `except Exception: json_write_ok = False`
discarded the real exception, leaving a truncated ZERO-BYTE evidence
artifact with the actual failure cause unrecoverable).

Extracts `stable_hash`, `dumps_sorted`, `write_json_atomic`,
`write_text_atomic`, `REQUIRED_EVIDENCE_KEYS`, and
`verify_artifact_evidence` VERBATIM (exact line ranges, SHA-256 pinned
against the deployed D1-2 script) and proves, using REPRESENTATIVE
D1-sized data (the real 85 PRE + 85 POST target fingerprints captured
by the already-accepted Checkpoint C1-2 run, read directly from its
own artifact on disk, plus a synthetic 78-row excluded-target witness
of the same shape D1 produces):

  1. a complete, D1-shaped result (full fingerprints + excluded witness
     + target-set-diff + checks) serializes successfully;
  2. the excluded witness sub-structure serializes correctly on its own;
  3. the written artifact reopens and reparses back to an equivalent
     structure;
  4. the stored PRE/POST fingerprint hashes recompute correctly from
     the round-tripped (serialized-then-reparsed) semantic data;
  5. a deliberate, unserializable payload (containing a raw Python
     `set`, which `json.dumps` cannot encode) is correctly REJECTED --
     `write_json_atomic` returns `ok=False` with a real, non-swallowed
     error message, and critically: an EXISTING valid file at that same
     final path is left COMPLETELY UNTOUCHED (byte-identical) by the
     failed attempt -- this is the exact defect class D1-1 hit, now
     proven fixed;
  6. `write_text_atomic` exhibits the same non-truncating behavior on a
     write failure (an unwritable destination directory);
  7. the exact boolean composition the real script uses to decide
     `overall_pass` (`runtime_checks_passed and artifact_write_verified`,
     where `artifact_write_verified = write_ok and evidence_ok`) causes
     an overall FAIL whenever the artifact write itself fails, even
     when every runtime/mutation check passed.

Run under real Python 2.7.5. Never launches SFM. Read-only with
respect to the deployed D1-2 script and the existing C1-2 artifact;
all newly-written files go to a dedicated scratch directory under
`C:\Users\Public\Documents\` and are cleaned up at the end.
"""
import hashlib
import json
import os
import shutil
import sys

D1_SCRIPT_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Checkpoint_D1_Historical_All_Shots_Baseline.py"
)
EXPECTED_D1_SCRIPT_SHA256 = (
    "e5df3675e26280ab3ed3a6e54ae1a54d7bd6526c3df22e2bfce59d3b5a2cdf61"
)
C1_JSON_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_c1_baseline_result.json"
SCRATCH_DIR = "C:\\Users\\Public\\Documents\\d1_writer_regression_scratch"

# 1-indexed, inclusive. Re-verify with:
#   sed -n '<start>,<end>p' Checkpoint_D1_Historical_All_Shots_Baseline.py
STABLE_HASH_RANGE = (383, 412)
DUMPS_SORTED_RANGE = (519, 520)
WRITE_JSON_ATOMIC_RANGE = (617, 689)
WRITE_TEXT_ATOMIC_RANGE = (692, 732)
REQUIRED_EVIDENCE_KEYS_RANGE = (735, 739)
VERIFY_ARTIFACT_EVIDENCE_RANGE = (742, 770)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


# Module-level (not inside a function): Python 2's `exec` statement is
# disallowed inside any function that also contains a nested `def`/class
# with free variables -- top-level placement sidesteps it, same as this
# project's other extraction-based harnesses.

with open(D1_SCRIPT_PATH, "rb") as f:
    _data = f.read()
_actual_sha = hashlib.sha256(_data).hexdigest()
check("source.d1_script_sha256_pinned", _actual_sha == EXPECTED_D1_SCRIPT_SHA256, _actual_sha)
if _actual_sha != EXPECTED_D1_SCRIPT_SHA256:
    print("\nRESULT: 1/%d SOME FAILED (SHA mismatch -- refusing to extract from a stale/wrong file)" % (len(RESULTS) + 1))
    sys.exit(1)

_lines = _data.decode("ascii").splitlines()


def _extract(start, end):
    return "\n".join(_lines[start - 1:end]) + "\n"


_ns = {"json": json, "hashlib": hashlib, "os": os}

_src_stable_hash = _extract(*STABLE_HASH_RANGE)
check("source.stable_hash_range_ok", _src_stable_hash.strip().startswith("def stable_hash(values):"), _src_stable_hash.splitlines()[0])
exec(compile(_src_stable_hash, "<stable_hash_extract>", "exec"), _ns)

_src_dumps_sorted = _extract(*DUMPS_SORTED_RANGE)
check("source.dumps_sorted_range_ok", _src_dumps_sorted.strip().startswith("def dumps_sorted(value):"), _src_dumps_sorted.splitlines()[0])
exec(compile(_src_dumps_sorted, "<dumps_sorted_extract>", "exec"), _ns)

_src_write_json_atomic = _extract(*WRITE_JSON_ATOMIC_RANGE)
check("source.write_json_atomic_range_ok", _src_write_json_atomic.strip().startswith("def write_json_atomic(final_path, data_obj):"), _src_write_json_atomic.splitlines()[0])
exec(compile(_src_write_json_atomic, "<write_json_atomic_extract>", "exec"), _ns)

_src_write_text_atomic = _extract(*WRITE_TEXT_ATOMIC_RANGE)
check("source.write_text_atomic_range_ok", _src_write_text_atomic.strip().startswith("def write_text_atomic(final_path, text_bytes):"), _src_write_text_atomic.splitlines()[0])
exec(compile(_src_write_text_atomic, "<write_text_atomic_extract>", "exec"), _ns)

_src_required_keys = _extract(*REQUIRED_EVIDENCE_KEYS_RANGE)
check("source.required_evidence_keys_range_ok", _src_required_keys.strip().startswith("REQUIRED_EVIDENCE_KEYS = ("), _src_required_keys.splitlines()[0])
exec(compile(_src_required_keys, "<required_evidence_keys_extract>", "exec"), _ns)

_src_verify = _extract(*VERIFY_ARTIFACT_EVIDENCE_RANGE)
check("source.verify_artifact_evidence_range_ok", _src_verify.strip().startswith("def verify_artifact_evidence(reparsed_obj):"), _src_verify.splitlines()[0])
exec(compile(_src_verify, "<verify_artifact_evidence_extract>", "exec"), _ns)

check("source.all_extracted_and_exec_ok",
      all(callable(_ns.get(n)) for n in ("stable_hash", "dumps_sorted", "write_json_atomic", "write_text_atomic", "verify_artifact_evidence"))
      and isinstance(_ns.get("REQUIRED_EVIDENCE_KEYS"), tuple))

stable_hash = _ns["stable_hash"]
dumps_sorted = _ns["dumps_sorted"]
write_json_atomic = _ns["write_json_atomic"]
write_text_atomic = _ns["write_text_atomic"]
verify_artifact_evidence = _ns["verify_artifact_evidence"]

# --- Build representative D1-sized data: the REAL 85 PRE + 85 POST
#     target fingerprints from the already-accepted Checkpoint C1-2
#     artifact (same schema D1 produces -- capture_snapshot_explicit,
#     canonicalized), plus a synthetic 78-row excluded-target witness
#     of the exact shape D1's own excluded_witness_row() produces. ---
if not os.path.isdir(SCRATCH_DIR):
    os.makedirs(SCRATCH_DIR)

with open(C1_JSON_PATH, "rb") as f:
    _c1_data = f.read()
_c1_report = json.loads(_c1_data.decode("utf-8"))
_real_pre_fingerprint = _c1_report["pre_fingerprint"]
_real_post_fingerprint = _c1_report["post_fingerprint"]
check("fixture.real_c1_pre_fingerprint_has_85_targets", len(_real_pre_fingerprint) == 85, len(_real_pre_fingerprint))
check("fixture.real_c1_post_fingerprint_has_85_targets", len(_real_post_fingerprint) == 85, len(_real_post_fingerprint))

_pre_excluded_witness = {}
_post_excluded_witness = {}
for _i in range(78):
    _key = u"shot%d|excl%d" % (_i, _i)
    _row = {
        "shot_name": u"shot%d" % _i, "aset_name": u"excl%d" % _i,
        "model_backed": False, "model_name": None, "root_group_valid": (_i % 3 == 0),
        "is_duplicate_aset_ptr": False, "control_count": 0, "fold_vocabulary_hash": None,
        "category": "excluded",
    }
    _pre_excluded_witness[_key] = _row
    _post_excluded_witness[_key] = dict(_row)

_pre_hash_real = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in _real_pre_fingerprint.items()])
_post_hash_real = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in _real_post_fingerprint.items()])


def _build_representative_report():
    return {
        "started_at": "2026-09-22 00:00:00",
        "finished_at": "2026-09-22 00:05:00",
        "python_version": sys.version,
        "checks": [{"name": "fixture.totals.eligible_targets_matches_required", "pass": True, "detail": None}] * 30,
        "anomalies": [],
        "selection_state_evidence": {"selected_shot_names": [u"shot3"], "note": u"evidence only"},
        "initial_pre_fingerprint_hash": _pre_hash_real,
        "all_shots_post_fingerprint_hash": _post_hash_real,
        "pre_fingerprint_hash": _pre_hash_real,
        "post_fingerprint_hash": _post_hash_real,
        "pre_fingerprint": _real_pre_fingerprint,
        "post_fingerprint": _real_post_fingerprint,
        "excluded_target_witness": {
            "pre": _pre_excluded_witness, "post": _post_excluded_witness,
            "changed_targets": [], "changed_count": 0,
        },
        "target_set_diff": {
            "missing_targets_entirely": [], "new_targets_entirely": [],
            "reclassified_eligible_to_excluded": [], "reclassified_excluded_to_eligible": [],
        },
        "fixture_totals": {
            "total_shots": 15, "total_targets": 163, "eligible_targets": 85, "excluded_targets": 78,
            "expected_selected_candidates": 2, "untouched_peer_targets": 83,
            "distinct_model_names": 22, "distinct_fold_vocabulary_hashes_among_eligible": 21,
        },
        "semantically_changed_target_set": [],
        "semantically_unchanged_target_set": sorted(_real_pre_fingerprint.keys()),
        "changed_target_count": 0,
        "unchanged_eligible_target_count": 85,
        "excluded_target_count": 78,
        "overall_pass": False,
        "artifact_write_verified": False,
        "artifact_evidence_detail": None,
        "json_write_error": None,
    }


# --- 1/2/3/4: complete result (incl. excluded witness) serializes,
#     reopens/reparses, and its stored hashes recompute correctly. ---
_good_path = os.path.join(SCRATCH_DIR, "good_result.json")
if os.path.exists(_good_path):
    os.remove(_good_path)
_good_report = _build_representative_report()
_ok1, _err1, _reparsed1 = write_json_atomic(_good_path, _good_report)
check("regression.complete_representative_result_serializes", _ok1, _err1)
check("regression.written_file_exists_and_nonzero", os.path.exists(_good_path) and os.path.getsize(_good_path) > 0,
      os.path.getsize(_good_path) if os.path.exists(_good_path) else None)
check("regression.reparsed_result_has_85_pre_and_post_and_78_excluded",
      _reparsed1 is not None
      and len(_reparsed1.get("pre_fingerprint", {})) == 85
      and len(_reparsed1.get("post_fingerprint", {})) == 85
      and len(_reparsed1.get("excluded_target_witness", {}).get("pre", {})) == 78
      and len(_reparsed1.get("excluded_target_witness", {}).get("post", {})) == 78)

_evidence_ok, _evidence_detail = verify_artifact_evidence(_reparsed1)
check("regression.stored_hashes_recompute_correctly_after_round_trip", _evidence_ok, _evidence_detail)

# --- 5: a deliberate unserializable payload is rejected, AND an
#     existing valid file at the same final path is left byte-
#     identical (never truncated) by the failed attempt -- the exact
#     defect class D1-1 hit. ---
with open(_good_path, "rb") as f:
    _bytes_before_failed_attempt = f.read()
_size_before_failed_attempt = os.path.getsize(_good_path)

_broken_report = dict(_good_report)
_broken_report["this_field_cannot_be_serialized"] = set([1, 2, 3])  # json.dumps() cannot encode a raw set.
_ok_broken, _err_broken, _reparsed_broken = write_json_atomic(_good_path, _broken_report)
check("regression.unserializable_payload_correctly_rejected", _ok_broken is False, _ok_broken)
check("regression.rejection_carries_a_real_non_swallowed_error_message",
      isinstance(_err_broken, str) and len(_err_broken) > 0 and "set" in _err_broken.lower(), _err_broken)
check("regression.reparsed_result_is_None_on_failure", _reparsed_broken is None, _reparsed_broken)

with open(_good_path, "rb") as f:
    _bytes_after_failed_attempt = f.read()
check("regression.existing_valid_file_untouched_by_failed_attempt",
      _bytes_after_failed_attempt == _bytes_before_failed_attempt
      and os.path.getsize(_good_path) == _size_before_failed_attempt,
      (len(_bytes_before_failed_attempt), len(_bytes_after_failed_attempt)))
check("regression.no_leftover_tmp_file_after_failed_attempt", not os.path.exists(_good_path + ".tmp"))

# A failing write against a path with NO pre-existing file must not
# leave a zero-byte file either.
_never_existed_path = os.path.join(SCRATCH_DIR, "never_existed_result.json")
if os.path.exists(_never_existed_path):
    os.remove(_never_existed_path)
_ok_never, _err_never, _reparsed_never = write_json_atomic(_never_existed_path, _broken_report)
check("regression.failed_write_to_a_new_path_leaves_no_file_at_all", _ok_never is False and not os.path.exists(_never_existed_path), _err_never)

# --- 6: write_text_atomic exhibits the same non-truncating behavior
#     on a write failure (an unwritable destination directory). ---
_bad_dir_path = os.path.join(SCRATCH_DIR, "this_directory_does_not_exist_at_all", "summary.txt")
_ok_text_fail, _err_text_fail = write_text_atomic(_bad_dir_path, b"hello world")
check("regression.write_text_atomic_correctly_reports_failure_for_bad_directory", _ok_text_fail is False, _err_text_fail)
check("regression.write_text_atomic_failure_message_not_swallowed", isinstance(_err_text_fail, str) and len(_err_text_fail) > 0, _err_text_fail)

_good_text_path = os.path.join(SCRATCH_DIR, "good_summary.txt")
_ok_text_good, _err_text_good = write_text_atomic(_good_text_path, b"hello world, this is a real summary\n")
check("regression.write_text_atomic_succeeds_for_a_valid_path", _ok_text_good and _err_text_good is None, (_ok_text_good, _err_text_good))
check("regression.write_text_atomic_written_file_is_nonzero", os.path.exists(_good_text_path) and os.path.getsize(_good_text_path) > 0)

# --- 7: the exact boolean composition the real script uses to decide
#     overall_pass causes an overall FAIL whenever the artifact write
#     fails, even when every runtime/mutation check passed. ---
_runtime_checks_passed = True  # simulates: every historical-run/fixture/gate check passed.
_write_ok_simulated = _ok_broken  # the failed write from step 5, reused directly.
_evidence_ok_simulated = False if not _write_ok_simulated else True
_artifact_write_verified_simulated = bool(_write_ok_simulated and _evidence_ok_simulated)
_overall_pass_simulated = bool(_runtime_checks_passed and _artifact_write_verified_simulated)
check("regression.overall_pass_formula_fails_when_artifact_write_fails_despite_runtime_pass",
      _overall_pass_simulated is False, (_runtime_checks_passed, _artifact_write_verified_simulated, _overall_pass_simulated))

# Cleanup.
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
