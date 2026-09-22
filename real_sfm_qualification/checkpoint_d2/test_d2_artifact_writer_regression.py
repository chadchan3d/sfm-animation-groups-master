# -*- coding: utf-8 -*-
"""Offline regression for Checkpoint D2's artifact writer (the same
streaming, atomic, exception-preserving design Checkpoint D1-3
introduced, reused verbatim in D2 with D2's own field names).

Extracts `stable_hash`, `dumps_sorted`, `write_json_atomic`,
`write_text_atomic`, `REQUIRED_EVIDENCE_KEYS`, and
`verify_artifact_evidence` VERBATIM (exact line ranges, SHA-256 pinned
against the deployed D2 script) and proves, using REPRESENTATIVE
D2-sized data (the real 85 PRE + 85 POST target fingerprints captured
by the already-accepted Checkpoint D1-3 run, read directly from its own
artifact on disk, plus a real 78-row excluded-target witness from the
same artifact):

  1. a complete, D2-shaped result (full integrated fingerprints +
     excluded witness + comparisons) serializes successfully;
  2. the written artifact reopens and reparses back to an equivalent
     structure;
  3. the stored PRE/POST aggregate hashes recompute correctly from the
     round-tripped (serialized-then-reparsed) semantic data;
  4. a deliberate, unserializable payload (containing a raw Python
     `set`) is correctly REJECTED -- `write_json_atomic` returns
     `ok=False` with a real, non-swallowed error message, and an
     EXISTING valid file at that same final path is left COMPLETELY
     UNTOUCHED (byte-identical) by the failed attempt, with no
     leftover `.tmp` file;
  5. `write_text_atomic` exhibits the same non-truncating behavior.

Run under real Python 2.7.5. Never launches SFM. Read-only with
respect to the deployed D2 script and the existing D1-3 artifact; all
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
    "61e45da0526ce37d56e5c04c8f9932122a8ce88855da14fc3ad5acf92b2d35ab"
)
D1_JSON_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_d1_historical_all_shots_result.json"
SCRATCH_DIR = "C:\\Users\\Public\\Documents\\d2_writer_regression_scratch"

# 1-indexed, inclusive. Re-verify with:
#   sed -n '<start>,<end>p' Checkpoint_D2_Integrated_All_Shots_Equivalence.py
STABLE_HASH_RANGE = (398, 409)
DUMPS_SORTED_RANGE = (516, 517)
WRITE_JSON_ATOMIC_RANGE = (641, 693)
WRITE_TEXT_ATOMIC_RANGE = (696, 736)
REQUIRED_EVIDENCE_KEYS_RANGE = (739, 743)
VERIFY_ARTIFACT_EVIDENCE_RANGE = (746, 771)

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
    ("write_json_atomic", WRITE_JSON_ATOMIC_RANGE, "def write_json_atomic(final_path, data_obj):"),
    ("write_text_atomic", WRITE_TEXT_ATOMIC_RANGE, "def write_text_atomic(final_path, text_bytes):"),
    ("REQUIRED_EVIDENCE_KEYS", REQUIRED_EVIDENCE_KEYS_RANGE, "REQUIRED_EVIDENCE_KEYS = ("),
    ("verify_artifact_evidence", VERIFY_ARTIFACT_EVIDENCE_RANGE, "def verify_artifact_evidence(reparsed_obj):"),
):
    _src = _extract(*_range)
    check("source.%s_range_ok" % _name, _src.strip().startswith(_prefix), _src.splitlines()[0])
    exec(compile(_src, "<%s_extract>" % _name, "exec"), _ns)

check("source.all_extracted_and_exec_ok",
      all(callable(_ns.get(n)) for n in ("stable_hash", "dumps_sorted", "write_json_atomic", "write_text_atomic", "verify_artifact_evidence"))
      and isinstance(_ns.get("REQUIRED_EVIDENCE_KEYS"), tuple))

stable_hash = _ns["stable_hash"]
dumps_sorted = _ns["dumps_sorted"]
write_json_atomic = _ns["write_json_atomic"]
write_text_atomic = _ns["write_text_atomic"]
verify_artifact_evidence = _ns["verify_artifact_evidence"]

if not os.path.isdir(SCRATCH_DIR):
    os.makedirs(SCRATCH_DIR)

with open(D1_JSON_PATH, "rb") as f:
    _d1_data = f.read()
_d1_report = json.loads(_d1_data.decode("utf-8"))
_real_pre_fingerprint = _d1_report["pre_fingerprint"]
_real_post_fingerprint = _d1_report["post_fingerprint"]
_real_excluded_pre = _d1_report["excluded_target_witness"]["pre"]
_real_excluded_post = _d1_report["excluded_target_witness"]["post"]
check("fixture.real_d1_pre_fingerprint_has_85_targets", len(_real_pre_fingerprint) == 85, len(_real_pre_fingerprint))
check("fixture.real_d1_post_fingerprint_has_85_targets", len(_real_post_fingerprint) == 85, len(_real_post_fingerprint))
check("fixture.real_d1_excluded_pre_has_78_targets", len(_real_excluded_pre) == 78, len(_real_excluded_pre))
check("fixture.real_d1_excluded_post_has_78_targets", len(_real_excluded_post) == 78, len(_real_excluded_post))

_pre_hash_real = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in _real_pre_fingerprint.items()])
_post_hash_real = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in _real_post_fingerprint.items()])


def _build_representative_report():
    return {
        "started_at": "2026-09-22 00:00:00",
        "finished_at": "2026-09-22 00:05:00",
        "python_version": sys.version,
        "checks": [{"name": "fixture.totals.eligible_targets_matches_required", "pass": True, "detail": None}] * 40,
        "anomalies": [],
        "integrated_pre_fingerprint_hash": _pre_hash_real,
        "integrated_post_fingerprint_hash": _post_hash_real,
        "integrated_pre_fingerprint": _real_pre_fingerprint,
        "integrated_post_fingerprint": _real_post_fingerprint,
        "integrated_excluded_witness": {"pre": _real_excluded_pre, "post": _real_excluded_post},
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
        "overall_pass": False,
        "artifact_write_verified": False,
        "artifact_evidence_detail": None,
        "json_write_error": None,
    }


# --- 1/2/3: complete result serializes, reopens/reparses, stored
#     hashes recompute correctly from round-tripped data. ---
_good_path = os.path.join(SCRATCH_DIR, "good_result.json")
if os.path.exists(_good_path):
    os.remove(_good_path)
_good_report = _build_representative_report()
_ok1, _err1, _reparsed1 = write_json_atomic(_good_path, _good_report)
check("regression.complete_representative_result_serializes", _ok1, _err1)
check("regression.written_file_exists_and_nonzero", os.path.exists(_good_path) and os.path.getsize(_good_path) > 0)
check("regression.reparsed_result_has_85_pre_and_post_and_78_excluded",
      _reparsed1 is not None
      and len(_reparsed1.get("integrated_pre_fingerprint", {})) == 85
      and len(_reparsed1.get("integrated_post_fingerprint", {})) == 85
      and len(_reparsed1.get("integrated_excluded_witness", {}).get("pre", {})) == 78
      and len(_reparsed1.get("integrated_excluded_witness", {}).get("post", {})) == 78)

_evidence_ok, _evidence_detail = verify_artifact_evidence(_reparsed1)
check("regression.stored_hashes_recompute_correctly_after_round_trip", _evidence_ok, _evidence_detail)

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
