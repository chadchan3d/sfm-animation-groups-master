# -*- coding: utf-8 -*-
"""Offline regression for Checkpoint F1's compact, multi-command
evidence artifact (per-command per-target hashes only, never raw
fingerprint dicts -- the same D1-3/D2-2 discipline applied across four
commands instead of one).

Extracts `stable_hash`, `dumps_sorted`, `per_target_hash`,
`compute_target_hashes`, `write_json_atomic`, `REQUIRED_EVIDENCE_KEYS`,
`verify_artifact_evidence`, and the degraded-fallback's own
`overall_pass`/`artifact_write_verified` force-False code block
VERBATIM (exact line ranges, SHA-256 pinned against the deployed F1
script) rather than reimplementing them.

Uses the REAL, already-accepted Checkpoint D1-3 artifact's own 85
eligible + 78 excluded target fingerprints (read once, here, offline)
to build FOUR representative command records (simulating a 4-command
F1 run) and proves:

  1. a complete, F1-shaped compact artifact (initial_state + 4
     command_records, per-target hashes only) serializes, reopens, and
     reparses successfully and stays well under 2MB;
  2. `verify_artifact_evidence()` PASSES on the unmutated artifact;
  3. exactly 4 command_records are required -- 3 or 5 records both
     correctly FAIL verification;
  4. a wrong per-command eligible/excluded hash COUNT (84 instead of
     85, or 77 instead of 78) correctly FAILS verification;
  5. a deliberate mutation of one command's own `eligible_hashes_
     checksum` (breaking round-trip fidelity) correctly FAILS
     verification;
  6. the degraded-fallback code path's own `overall_pass`/
     `artifact_write_verified` force-False lines produce `False` in
     the degraded copy even when the source `report` dict claims
     `overall_pass: True` -- the same D2-1 bug class D2-2 fixed,
     reused verbatim in F1, now proven fixed here too.

Run under real Python 2.7.5. Never launches SFM. Read-only with
respect to the deployed F1 script and the real D1-3 artifact; all
newly-written files go to a dedicated scratch directory under
`C:\Users\Public\Documents\` and are cleaned up at the end.
"""
import hashlib
import json
import os
import shutil
import sys

F1_SCRIPT_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Checkpoint_F1_Repeated_Warm_Use_Stability.py"
)
EXPECTED_F1_SCRIPT_SHA256 = (
    "d2af8cc6ac6eb2ed69fc5fae886ab715be8b79f3860274cd7f836aa874cd4ec6"
)
D1_JSON_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_d1_historical_all_shots_result.json"
SCRATCH_DIR = "C:\\Users\\Public\\Documents\\f1_compact_regression_scratch"

# 1-indexed, inclusive. Re-verify with:
#   sed -n '<start>,<end>p' Checkpoint_F1_Repeated_Warm_Use_Stability.py
STABLE_HASH_RANGE = (396, 406)
DUMPS_SORTED_RANGE = (513, 514)
PER_TARGET_HASH_RANGE = (538, 542)
COMPUTE_TARGET_HASHES_RANGE = (545, 549)
WRITE_JSON_ATOMIC_RANGE = (597, 646)
REQUIRED_EVIDENCE_KEYS_RANGE = (692, 694)
VERIFY_ARTIFACT_EVIDENCE_RANGE = (697, 726)
DEGRADED_FORCE_FALSE_RANGE = (1253, 1264)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


with open(F1_SCRIPT_PATH, "rb") as f:
    _data = f.read()
_actual_sha = hashlib.sha256(_data).hexdigest()
check("source.f1_script_sha256_pinned", _actual_sha == EXPECTED_F1_SCRIPT_SHA256, _actual_sha)
if _actual_sha != EXPECTED_F1_SCRIPT_SHA256:
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
    ("write_json_atomic", WRITE_JSON_ATOMIC_RANGE, "def write_json_atomic(final_path, data_obj):"),
    ("REQUIRED_EVIDENCE_KEYS", REQUIRED_EVIDENCE_KEYS_RANGE, "REQUIRED_EVIDENCE_KEYS = ("),
    ("verify_artifact_evidence", VERIFY_ARTIFACT_EVIDENCE_RANGE, "def verify_artifact_evidence(reparsed_obj):"),
):
    _src = _extract(*_range)
    check("source.%s_range_ok" % _name, _src.strip().startswith(_prefix), _src.splitlines()[0])
    exec(compile(_src, "<%s_extract>" % _name, "exec"), _ns)

check("source.all_extracted_and_exec_ok",
      all(callable(_ns.get(n)) for n in ("stable_hash", "dumps_sorted", "per_target_hash", "compute_target_hashes",
                                          "write_json_atomic", "verify_artifact_evidence"))
      and isinstance(_ns.get("REQUIRED_EVIDENCE_KEYS"), tuple))

stable_hash = _ns["stable_hash"]
dumps_sorted = _ns["dumps_sorted"]
per_target_hash = _ns["per_target_hash"]
compute_target_hashes = _ns["compute_target_hashes"]
write_json_atomic = _ns["write_json_atomic"]
verify_artifact_evidence = _ns["verify_artifact_evidence"]

if not os.path.isdir(SCRATCH_DIR):
    os.makedirs(SCRATCH_DIR)

with open(D1_JSON_PATH, "rb") as f:
    _d1_data = f.read()
_d1_report = json.loads(_d1_data.decode("utf-8"))
del _d1_data

_eligible_hashes_base = compute_target_hashes(_d1_report["pre_fingerprint"])
_excluded_hashes_base = compute_target_hashes(_d1_report["excluded_target_witness"]["pre"])
del _d1_report
check("fixture.real_d1_eligible_hashes_count_is_85", len(_eligible_hashes_base) == 85, len(_eligible_hashes_base))
check("fixture.real_d1_excluded_hashes_count_is_78", len(_excluded_hashes_base) == 78, len(_excluded_hashes_base))


def _hash_of_hashes(hash_dict):
    return stable_hash([u"%s=%s" % (k, v) for k, v in hash_dict.items()])


def _build_command_record(ordinal, scope_label):
    return {
        "ordinal": ordinal,
        "scope_requested": scope_label,
        "duration_seconds": 12.5 + ordinal,
        "run_started": True,
        "run_completed_cleanly": True,
        "aggregate_hash": "d7b3bacb757253e126823db4e1445b57e4278d972c9be8b23920fc88cf1b5938",
        "expected_aggregate_hash": "d7b3bacb757253e126823db4e1445b57e4278d972c9be8b23920fc88cf1b5938",
        "aggregate_hash_matches_expected": True,
        "eligible_target_hashes": dict(_eligible_hashes_base),
        "excluded_target_hashes": dict(_excluded_hashes_base),
        "eligible_hashes_checksum": _hash_of_hashes(_eligible_hashes_base),
        "excluded_hashes_checksum": _hash_of_hashes(_excluded_hashes_base),
        "changed_target_keys_from_previous": [],
        "unchanged_target_keys_from_previous": sorted(_eligible_hashes_base.keys()),
        "excluded_changed_keys_from_previous": [],
        "target_set_diff_vs_initial": {
            "missing_targets_entirely": [], "new_targets_entirely": [],
            "reclassified_eligible_to_excluded": [], "reclassified_excluded_to_eligible": [],
        },
        "authority_lifecycle": {
            "get_state": "READY", "is_canonical": True, "outstanding_lease_count": 0,
            "provider_counters": {"current_open_provider_count": 0, "active_cohort_id": None,
                                   "total_provider_opens": ordinal, "total_provider_closes": ordinal},
            "provider_opens_delta_this_command": 1, "provider_closes_delta_this_command": 1,
        },
        "native_protection": {"contains_NATIVE_GUARDS_PASS": True, "contains_NATIVE_REBUILD_RETURNED_PASS": True},
        "memory_after_cleanup": {"available": True, "working_set_bytes": 3000000000 + ordinal * 1000000},
    }


def _build_compact_report(num_commands=4):
    return {
        "started_at": "2026-09-22 00:00:00",
        "finished_at": "2026-09-22 00:10:00",
        "python_version": sys.version,
        "checks": [{"name": "fixture.totals.eligible_targets_matches_required", "pass": True, "detail": None}] * 60,
        "anomalies": [],
        "provenance": {"production_normalizer_sha256": "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"},
        "initial_state": {
            "aggregate_hash": "eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0",
            "eligible_target_hashes": dict(_eligible_hashes_base),
            "excluded_target_hashes": dict(_excluded_hashes_base),
            "eligible_target_keys": sorted(_eligible_hashes_base.keys()),
            "excluded_target_keys": sorted(_excluded_hashes_base.keys()),
        },
        "command_records": [
            _build_command_record(i, u"Selected Shots" if i <= 2 else u"All Shots")
            for i in range(1, num_commands + 1)
        ],
        "final_responsiveness": {"main_window_available": True, "document_still_accessible": True, "events_processed_ok": True},
        "memory_snapshots": {},
        "overall_pass": True,
        "artifact_write_verified": True,
    }


# --- 1. Complete artifact serializes, reopens, reparses, stays small. ---
_good_path = os.path.join(SCRATCH_DIR, "good_f1_result.json")
if os.path.exists(_good_path):
    os.remove(_good_path)
_good_report = _build_compact_report()
_ok1, _err1, _reparsed1 = write_json_atomic(_good_path, _good_report)
check("regression.compact_f1_artifact_serializes_and_round_trips", _ok1, _err1)
check("regression.written_file_is_small_not_multi_megabyte",
      os.path.exists(_good_path) and 0 < os.path.getsize(_good_path) < 2 * 1024 * 1024,
      os.path.getsize(_good_path) if os.path.exists(_good_path) else None)

# --- 2. verify_artifact_evidence PASSES on the unmutated artifact. ---
_evidence_ok, _evidence_detail = verify_artifact_evidence(_reparsed1)
check("regression.verify_artifact_evidence_passes_on_unmutated_artifact", _evidence_ok, _evidence_detail)

# --- 3. Exactly 4 command_records required. ---
_report_3_cmds = _build_compact_report(num_commands=3)
_ok2, _err2, _reparsed2 = write_json_atomic(os.path.join(SCRATCH_DIR, "three_commands.json"), _report_3_cmds)
check("regression.three_command_records_write_succeeds", _ok2)
_evidence_ok2, _evidence_detail2 = verify_artifact_evidence(_reparsed2)
check("regression.three_command_records_fails_verification", _evidence_ok2 is False, _evidence_detail2)

_report_5_cmds = _build_compact_report(num_commands=5)
_ok3, _err3, _reparsed3 = write_json_atomic(os.path.join(SCRATCH_DIR, "five_commands.json"), _report_5_cmds)
check("regression.five_command_records_write_succeeds", _ok3)
_evidence_ok3, _evidence_detail3 = verify_artifact_evidence(_reparsed3)
check("regression.five_command_records_fails_verification", _evidence_ok3 is False, _evidence_detail3)

# --- 4. Wrong per-command hash counts fail. ---
_report_bad_count = _build_compact_report()
_a_key = sorted(_report_bad_count["command_records"][1]["eligible_target_hashes"].keys())[0]
del _report_bad_count["command_records"][1]["eligible_target_hashes"][_a_key]
_ok4, _err4, _reparsed4 = write_json_atomic(os.path.join(SCRATCH_DIR, "bad_eligible_count.json"), _report_bad_count)
check("regression.bad_eligible_count_write_succeeds", _ok4)
_evidence_ok4, _evidence_detail4 = verify_artifact_evidence(_reparsed4)
check("regression.command_with_84_eligible_hashes_fails_verification", _evidence_ok4 is False, _evidence_detail4)

_report_bad_excl_count = _build_compact_report()
_b_key = sorted(_report_bad_excl_count["command_records"][2]["excluded_target_hashes"].keys())[0]
del _report_bad_excl_count["command_records"][2]["excluded_target_hashes"][_b_key]
_ok5, _err5, _reparsed5 = write_json_atomic(os.path.join(SCRATCH_DIR, "bad_excluded_count.json"), _report_bad_excl_count)
check("regression.bad_excluded_count_write_succeeds", _ok5)
_evidence_ok5, _evidence_detail5 = verify_artifact_evidence(_reparsed5)
check("regression.command_with_77_excluded_hashes_fails_verification", _evidence_ok5 is False, _evidence_detail5)

# --- 5. Broken round-trip checksum (mutated checksum, not the hash map
#        itself) fails. ---
_report_bad_checksum = _build_compact_report()
_report_bad_checksum["command_records"][3]["eligible_hashes_checksum"] = "0" * 64
_ok6, _err6, _reparsed6 = write_json_atomic(os.path.join(SCRATCH_DIR, "bad_checksum.json"), _report_bad_checksum)
check("regression.bad_checksum_write_succeeds", _ok6)
_evidence_ok6, _evidence_detail6 = verify_artifact_evidence(_reparsed6)
check("regression.mutated_checksum_fails_verification", _evidence_ok6 is False, _evidence_detail6)

# --- 6. Degraded-fallback path forces overall_pass/artifact_write_
#        verified to False regardless of the source report's own
#        claimed state -- the same D2-1 bug class, reused verbatim in
#        F1, now proven fixed here too. ---
_degraded_src = _extract(*DEGRADED_FORCE_FALSE_RANGE)
check("source.degraded_force_false_range_ok", _degraded_src.strip().startswith("degraded_report = dict(report)"), _degraded_src.splitlines()[0])
_degraded_ns = {}
_buggy_report = _build_compact_report()
_buggy_report["overall_pass"] = True  # simulates the D2-1-class stale-snapshot bug scenario
_buggy_report["artifact_write_verified"] = True
_buggy_report["json_write_error"] = "simulated failure for this test"
_degraded_ns["report"] = _buggy_report
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
check("regression.degraded_path_command_records_still_present_but_hash_maps_dropped",
      len(_degraded_ns.get("degraded_report", {}).get("command_records", [])) == 4
      and "eligible_target_hashes" not in _degraded_ns["degraded_report"]["command_records"][0])

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
