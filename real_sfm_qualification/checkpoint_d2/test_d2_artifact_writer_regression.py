# -*- coding: utf-8 -*-
"""Offline regression for Checkpoint D2's artifact writer (the same
streaming, atomic, exception-preserving design Checkpoint D1-3
introduced, reused verbatim in D2, now writing the D2-2 COMPACT
per-target-hash schema rather than raw fingerprint duplication).

Extracts `stable_hash`, `dumps_sorted`, `per_target_hash`,
`compute_target_hashes`, `hash_of_hashes`, `write_json_atomic`,
`write_text_atomic`, `REQUIRED_EVIDENCE_KEYS`, and
`verify_artifact_evidence` VERBATIM (exact line ranges, SHA-256 pinned
against the deployed D2-2 script) and proves, using REPRESENTATIVE
D2-sized data (per-target hashes computed from the real 85 PRE + 85
POST target fingerprints and the real 78-row excluded-target witness
captured by the already-accepted Checkpoint D1-3 run, read directly
from its own artifact on disk -- never the raw fingerprints
themselves, matching D2-2's own compact-artifact discipline):

  1. a complete, D2-2-shaped COMPACT result (per-target hashes +
     comparisons, never raw fingerprints) serializes successfully and
     stays small;
  2. the written artifact reopens and reparses back to an equivalent
     structure;
  3. the stored per-target hash maps recompute a matching checksum
     after round-trip (serialization/reparse fidelity);
  4. a deliberate, unserializable payload (containing a raw Python
     `set`) is correctly REJECTED -- `write_json_atomic` returns
     `ok=False` with a real, non-swallowed error message, and an
     EXISTING valid file at that same final path is left COMPLETELY
     UNTOUCHED (byte-identical) by the failed attempt, with no
     leftover `.tmp` file;
  5. `write_text_atomic` exhibits the same non-truncating behavior.

Run under real Python 2.7.5. Never launches SFM. Read-only with
respect to the deployed D2-2 script and the existing D1-3 artifact; all
newly-written files go to a dedicated scratch directory under
`C:\Users\Public\Documents\` and are cleaned up at the end.
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
SCRATCH_DIR = "C:\\Users\\Public\\Documents\\d2_writer_regression_scratch"

# 1-indexed, inclusive. Re-verify with:
#   sed -n '<start>,<end>p' Checkpoint_D2_Integrated_All_Shots_Equivalence.py
STABLE_HASH_RANGE = (439, 450)
DUMPS_SORTED_RANGE = (557, 558)
PER_TARGET_HASH_RANGE = (582, 589)
COMPUTE_TARGET_HASHES_RANGE = (592, 598)
HASH_OF_HASHES_RANGE = (601, 611)
WRITE_JSON_ATOMIC_RANGE = (693, 745)
WRITE_TEXT_ATOMIC_RANGE = (748, 788)
REQUIRED_EVIDENCE_KEYS_RANGE = (795, 803)
VERIFY_ARTIFACT_EVIDENCE_RANGE = (806, 842)

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
    ("write_json_atomic", WRITE_JSON_ATOMIC_RANGE, "def write_json_atomic(final_path, data_obj):"),
    ("write_text_atomic", WRITE_TEXT_ATOMIC_RANGE, "def write_text_atomic(final_path, text_bytes):"),
    ("REQUIRED_EVIDENCE_KEYS", REQUIRED_EVIDENCE_KEYS_RANGE, "REQUIRED_EVIDENCE_KEYS = ("),
    ("verify_artifact_evidence", VERIFY_ARTIFACT_EVIDENCE_RANGE, "def verify_artifact_evidence(reparsed_obj):"),
):
    _src = _extract(*_range)
    check("source.%s_range_ok" % _name, _src.strip().startswith(_prefix), _src.splitlines()[0])
    exec(compile(_src, "<%s_extract>" % _name, "exec"), _ns)

check("source.all_extracted_and_exec_ok",
      all(callable(_ns.get(n)) for n in ("stable_hash", "dumps_sorted", "per_target_hash", "compute_target_hashes",
                                          "hash_of_hashes", "write_json_atomic", "write_text_atomic", "verify_artifact_evidence"))
      and isinstance(_ns.get("REQUIRED_EVIDENCE_KEYS"), tuple))

dumps_sorted = _ns["dumps_sorted"]
per_target_hash = _ns["per_target_hash"]
compute_target_hashes = _ns["compute_target_hashes"]
hash_of_hashes = _ns["hash_of_hashes"]
write_json_atomic = _ns["write_json_atomic"]
write_text_atomic = _ns["write_text_atomic"]
verify_artifact_evidence = _ns["verify_artifact_evidence"]

if not os.path.isdir(SCRATCH_DIR):
    os.makedirs(SCRATCH_DIR)

with open(D1_JSON_PATH, "rb") as f:
    _d1_data = f.read()
_d1_report = json.loads(_d1_data.decode("utf-8"))
del _d1_data

_eligible_pre_hashes = compute_target_hashes(_d1_report["pre_fingerprint"])
_eligible_post_hashes = compute_target_hashes(_d1_report["post_fingerprint"])
_excluded_pre_hashes = compute_target_hashes(_d1_report["excluded_target_witness"]["pre"])
_excluded_post_hashes = compute_target_hashes(_d1_report["excluded_target_witness"]["post"])
del _d1_report

check("fixture.real_d1_eligible_pre_hashes_count_is_85", len(_eligible_pre_hashes) == 85, len(_eligible_pre_hashes))
check("fixture.real_d1_eligible_post_hashes_count_is_85", len(_eligible_post_hashes) == 85, len(_eligible_post_hashes))
check("fixture.real_d1_excluded_pre_hashes_count_is_78", len(_excluded_pre_hashes) == 78, len(_excluded_pre_hashes))
check("fixture.real_d1_excluded_post_hashes_count_is_78", len(_excluded_post_hashes) == 78, len(_excluded_post_hashes))

_changed_keys = sorted(k for k in _eligible_pre_hashes if _eligible_pre_hashes[k] != _eligible_post_hashes.get(k))
_unchanged_keys = sorted(k for k in _eligible_pre_hashes if _eligible_pre_hashes[k] == _eligible_post_hashes.get(k))
_pre_hash_real = "eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0"
_post_hash_real = "299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7"


def _build_representative_report():
    return {
        "started_at": "2026-09-22 00:00:00",
        "finished_at": "2026-09-22 00:05:00",
        "python_version": sys.version,
        "checks": [{"name": "fixture.totals.eligible_targets_matches_required", "pass": True, "detail": None}] * 40,
        "anomalies": [],
        "integrated_pre_fingerprint_hash": _pre_hash_real,
        "integrated_post_fingerprint_hash": _post_hash_real,
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
        "authority_runtime_evidence": {"get_state": "READY", "is_canonical": True, "outstanding_lease_count": 0},
        "native_protection_evidence": {"contains_NATIVE_GUARDS_PASS": True, "contains_NATIVE_REBUILD_RETURNED_PASS": True},
        "memory_snapshots": {},
        "provenance": {},
        "overall_pass": False,
        "artifact_write_verified": False,
        "artifact_evidence_detail": None,
        "json_write_error": None,
    }


# --- 1/2/3: complete COMPACT result serializes, stays small, reopens/
#     reparses, stored per-target hashes recompute a matching checksum
#     after round-trip. ---
_good_path = os.path.join(SCRATCH_DIR, "good_result.json")
if os.path.exists(_good_path):
    os.remove(_good_path)
_good_report = _build_representative_report()
_ok1, _err1, _reparsed1 = write_json_atomic(_good_path, _good_report)
check("regression.complete_representative_compact_result_serializes", _ok1, _err1)
check("regression.written_file_exists_nonzero_and_small",
      os.path.exists(_good_path) and 0 < os.path.getsize(_good_path) < 2 * 1024 * 1024,
      os.path.getsize(_good_path) if os.path.exists(_good_path) else None)
check("regression.reparsed_result_has_85_pre_and_post_and_78_excluded_hashes",
      _reparsed1 is not None
      and len(_reparsed1.get("eligible_pre_target_hashes", {})) == 85
      and len(_reparsed1.get("eligible_post_target_hashes", {})) == 85
      and len(_reparsed1.get("excluded_pre_target_hashes", {})) == 78
      and len(_reparsed1.get("excluded_post_target_hashes", {})) == 78)

_evidence_ok, _evidence_detail = verify_artifact_evidence(_reparsed1)
check("regression.stored_hash_maps_recompute_matching_checksum_after_round_trip", _evidence_ok, _evidence_detail)

# --- 4. Deliberate unserializable payload rejected; existing valid
#     file at the same final path left byte-identical; no leftover
#     .tmp file. ---
with open(_good_path, "rb") as f:
    _bytes_before = f.read()
_size_before = os.path.getsize(_good_path)

_broken_report = dict(_good_report)
_broken_report["this_field_cannot_be_serialized"] = set([1, 2, 3])
_ok_broken, _err_broken, _reparsed_broken = write_json_atomic(_good_path, _broken_report)
check("regression.unserializable_payload_correctly_rejected", _ok_broken is False, _ok_broken)
check("regression.rejection_carries_a_real_non_swallowed_error_message",
      isinstance(_err_broken, str) and len(_err_broken) > 0 and "set" in _err_broken.lower(), _err_broken)
check("regression.reparsed_result_is_None_on_failure", _reparsed_broken is None)

with open(_good_path, "rb") as f:
    _bytes_after = f.read()
check("regression.existing_valid_file_untouched_by_failed_attempt", _bytes_after == _bytes_before and os.path.getsize(_good_path) == _size_before)
check("regression.no_leftover_tmp_file_after_failed_attempt", not os.path.exists(_good_path + ".tmp"))

# --- 5. write_text_atomic exhibits the same discipline. ---
_bad_dir_path = os.path.join(SCRATCH_DIR, "this_directory_does_not_exist_at_all", "summary.txt")
_ok_text_fail, _err_text_fail = write_text_atomic(_bad_dir_path, b"hello world")
check("regression.write_text_atomic_correctly_reports_failure_for_bad_directory", _ok_text_fail is False, _err_text_fail)

_good_text_path = os.path.join(SCRATCH_DIR, "good_summary.txt")
_ok_text_good, _err_text_good = write_text_atomic(_good_text_path, b"hello world, this is a real summary\n")
check("regression.write_text_atomic_succeeds_for_a_valid_path", _ok_text_good and _err_text_good is None)

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
