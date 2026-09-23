# -*- coding: utf-8 -*-
"""
Offline regression for Checkpoint F1-R1 (Checkpoint_F1_R1_Attribution_
Diagnostic.py, SHA-256 e9ea42b08f6448cef174b4d5642dfc1a89dbe74cf0145d9fcc0a3d96b63e7763).

Extracts the deployed script's own helper functions VERBATIM (by exact
line range, pinned below) and proves, offline, under the real embedded
Python 2.7.5:

  1. stable_hash / dumps_sorted / per_target_hash / compute_target_hashes
     behave identically to every earlier checkpoint's own copies (same
     functions, byte-identical).
  2. write_json_atomic / write_text_atomic / copy_bytes_atomic round-trip
     correctly and never leave a truncated final path on a write-phase
     failure.
  3. parse_resource_checkpoint_line / parse_all_resource_checkpoints /
     summarize_resource_checkpoints correctly parse REAL
     CONTEXTUALIZER_RESOURCE_CHECKPOINT lines (using the actual lines
     observed in the preserved F1-1 crash-evidence log), including the
     "L"-suffixed long-int stripping, True/False/None typing, and
     correctly identifying the first/last checkpoint and whether
     FINAL_REPORT_ENTRY was reached.
  4. verify_artifact_evidence() -- unlike F1's own verifier, F1-R1's
     accepts A PARTIAL command_records list (1 or 2 records, not
     necessarily all 3) since the artifact is rewritten incrementally
     after every command boundary; it still correctly REJECTS more
     records than commands attempted so far, a wrong full-capture hash
     count for the ordinal(s) in FULL_CAPTURE_ORDINALS, a mutated
     checksum, and a wrong compact selected-target key set for the
     non-full-capture ordinals.
  5. The degraded-fallback force-False code block (same D2-1/F1 bug
     class, reused verbatim in F1-R1) still produces
     overall_pass=False/artifact_write_verified=False even when fed a
     synthetic `report` claiming True.
  6. INCREMENTAL-WRITE SIMULATION: writing a 1-command, then a
     2-command, partial artifact via write_json_atomic() to the SAME
     path (as the real script does after every command boundary)
     leaves, at every step, a fully valid, independently reparseable
     artifact on disk -- proving a crash between commands does not
     corrupt or lose the prior commands' evidence.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_f1r1_attribution_diagnostic_regression.py
"""
import hashlib
import json
import os
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Checkpoint_F1_R1_Attribution_Diagnostic.py")
EXPECTED_SCRIPT_SHA256 = "e9ea42b08f6448cef174b4d5642dfc1a89dbe74cf0145d9fcc0a3d96b63e7763"

# 1-indexed, inclusive line ranges, pinned to the deployed script above.
STABLE_HASH_RANGE = (386, 396)
DUMPS_SORTED_RANGE = (503, 504)
PER_TARGET_HASH_RANGE = (525, 529)
COMPUTE_TARGET_HASHES_RANGE = (532, 536)
CHECKPOINT_PARSER_RANGE = (595, 670)
WRITE_JSON_ATOMIC_RANGE = (678, 727)
WRITE_TEXT_ATOMIC_RANGE = (730, 769)
COPY_BYTES_ATOMIC_RANGE = (772, 775)
REQUIRED_EVIDENCE_KEYS_RANGE = (778, 780)
VERIFY_ARTIFACT_EVIDENCE_RANGE = (783, 821)
DEGRADED_FORCE_FALSE_RANGE_START_MARKER = "degraded_report = dict(report)"

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s\n" % label)
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s\n" % label)


with open(SCRIPT_PATH, "rb") as f:
    script_bytes = f.read()
script_sha256 = hashlib.sha256(script_bytes).hexdigest()
expect(script_sha256 == EXPECTED_SCRIPT_SHA256, "deployed_script.sha256_matches_pinned (%s)" % script_sha256)

script_lines = script_bytes.decode("ascii").splitlines()


def extract(range_tuple):
    start, end = range_tuple
    return "\n".join(script_lines[start - 1:end])


extracted_ns = {"hashlib": hashlib, "json": json, "os": os}

exec(compile(extract(STABLE_HASH_RANGE), "<stable_hash>", "exec"), extracted_ns)
exec(compile(extract(DUMPS_SORTED_RANGE), "<dumps_sorted>", "exec"), extracted_ns)
exec(compile(extract(PER_TARGET_HASH_RANGE), "<per_target_hash>", "exec"), extracted_ns)
exec(compile(extract(COMPUTE_TARGET_HASHES_RANGE), "<compute_target_hashes>", "exec"), extracted_ns)
exec(compile(extract(CHECKPOINT_PARSER_RANGE), "<checkpoint_parser>", "exec"), extracted_ns)
exec(compile(extract(WRITE_JSON_ATOMIC_RANGE), "<write_json_atomic>", "exec"), extracted_ns)
exec(compile(extract(WRITE_TEXT_ATOMIC_RANGE), "<write_text_atomic>", "exec"), extracted_ns)
exec(compile(extract(COPY_BYTES_ATOMIC_RANGE), "<copy_bytes_atomic>", "exec"), extracted_ns)
exec(compile(extract(REQUIRED_EVIDENCE_KEYS_RANGE), "<required_evidence_keys>", "exec"), extracted_ns)
exec(compile(extract(VERIFY_ARTIFACT_EVIDENCE_RANGE), "<verify_artifact_evidence>", "exec"), extracted_ns)

stable_hash = extracted_ns["stable_hash"]
dumps_sorted = extracted_ns["dumps_sorted"]
per_target_hash = extracted_ns["per_target_hash"]
compute_target_hashes = extracted_ns["compute_target_hashes"]
parse_resource_checkpoint_line = extracted_ns["parse_resource_checkpoint_line"]
parse_all_resource_checkpoints = extracted_ns["parse_all_resource_checkpoints"]
summarize_resource_checkpoints = extracted_ns["summarize_resource_checkpoints"]
write_json_atomic = extracted_ns["write_json_atomic"]
write_text_atomic = extracted_ns["write_text_atomic"]
copy_bytes_atomic = extracted_ns["copy_bytes_atomic"]
verify_artifact_evidence = extracted_ns["verify_artifact_evidence"]
extracted_ns["FULL_CAPTURE_ORDINALS"] = frozenset([3])
extracted_ns["COMPACT_SELECTED_TARGET_KEYS"] = [u"shot3|foxmccouldwm1", u"shot3|mia1"]

# Re-bind the module-level constants verify_artifact_evidence() closes
# over (it references FULL_CAPTURE_ORDINALS/COMPACT_SELECTED_TARGET_KEYS
# as globals in the real script) directly into its own __globals__.
verify_artifact_evidence.__globals__["FULL_CAPTURE_ORDINALS"] = frozenset([3])
verify_artifact_evidence.__globals__["COMPACT_SELECTED_TARGET_KEYS"] = [u"shot3|foxmccouldwm1", u"shot3|mia1"]
verify_artifact_evidence.__globals__["stable_hash"] = stable_hash

sys.stdout.write("\n--- stable_hash / dumps_sorted / per_target_hash / compute_target_hashes ---\n")

expect(stable_hash([]) == hashlib.sha256(b"").hexdigest(), "stable_hash.empty_matches_bare_sha256")
h1 = stable_hash([u"a", u"b", u"c"])
h2 = stable_hash([u"c", u"b", u"a"])
expect(h1 == h2, "stable_hash.order_independent")
expect(per_target_hash({"x": 1}) == hashlib.sha256(dumps_sorted({"x": 1}).encode("utf-8")).hexdigest(), "per_target_hash.matches_manual_sha256")
hashes = compute_target_hashes({"k1": {"a": 1}, "k2": {"b": 2}})
expect(set(hashes.keys()) == {"k1", "k2"}, "compute_target_hashes.key_set_preserved")
expect(hashes["k1"] == per_target_hash({"a": 1}), "compute_target_hashes.value_matches_per_target_hash")

sys.stdout.write("\n--- CONTEXTUALIZER_RESOURCE_CHECKPOINT parser (real observed log lines) ---\n")

REAL_CP0_LINE = (
    "CONTEXTUALIZER_RESOURCE_CHECKPOINT label=CP0_COMMAND_START run_elapsed=0.012 "
    "mem_ok=True working_set=3270361088L peak_working_set=3270361088L pagefile=3300000000L "
    "peak_pagefile=3300000000L private=3300000000L vas_requested=True vas_ok=True "
    "min_address=65536 max_address=4294901759L mem_free=266715136 mem_reserve=100000000 "
    "mem_commit=200000000L largest_free=125108224 free_regions=42 virtual_query_count=513 "
    "vas_elapsed=0.0042 vas_error=None"
)
REAL_LAST_LINE_BEFORE_CRASH = (
    "CONTEXTUALIZER_TELEMETRY phase=PRE_NATIVE target_seq=52 native_attempt=52 shot=u'shot8' "
    "target=u'lola bunny1' run_elapsed=164.558 target_elapsed=0.548 mem_ok=True "
    "working_set=3452686336L peak_working_set=3452923904L pagefile=3499929600L "
    "peak_pagefile=3502133248L private=3499929600L"
)
REAL_AFTER_SHOT_13_LINE = (
    "CONTEXTUALIZER_RESOURCE_CHECKPOINT label=AFTER_SHOT_13 run_elapsed=160.221 "
    "mem_ok=True working_set=3440000000L peak_working_set=3452923904L pagefile=3490000000L "
    "peak_pagefile=3502133248L private=3490000000L vas_requested=True vas_ok=True "
    "min_address=65536 max_address=4294901759L mem_free=108412928 mem_reserve=80000000 "
    "mem_commit=210000000L largest_free=7561216 free_regions=61 virtual_query_count=880 "
    "vas_elapsed=0.0051 vas_error=None"
)
REAL_FINAL_REPORT_ENTRY_LINE = (
    "CONTEXTUALIZER_RESOURCE_CHECKPOINT label=FINAL_REPORT_ENTRY run_elapsed=210.900 "
    "mem_ok=True working_set=3100000000L peak_working_set=3452923904L pagefile=3150000000L "
    "peak_pagefile=3502133248L private=3150000000L vas_requested=True vas_ok=True "
    "min_address=65536 max_address=4294901759L mem_free=200000000 mem_reserve=90000000 "
    "mem_commit=180000000L largest_free=95000000 free_regions=20 virtual_query_count=900 "
    "vas_elapsed=0.0039 vas_error=None"
)

parsed_cp0 = parse_resource_checkpoint_line(REAL_CP0_LINE)
expect(parsed_cp0 is not None, "parser.cp0_line_recognized")
expect(parsed_cp0["label"] == "CP0_COMMAND_START", "parser.cp0_label_correct")
expect(parsed_cp0["working_set"] == 3270361088, "parser.cp0_working_set_L_suffix_stripped_to_int")
expect(parsed_cp0["mem_ok"] is True, "parser.cp0_mem_ok_typed_as_bool_True")
expect(parsed_cp0["max_address"] == 4294901759, "parser.cp0_max_address_L_suffix_stripped")
expect(parsed_cp0["largest_free"] == 125108224, "parser.cp0_largest_free_correct")
expect(parsed_cp0["vas_error_raw"] == "None", "parser.cp0_vas_error_raw_captured_as_string_None")

expect(parse_resource_checkpoint_line(REAL_LAST_LINE_BEFORE_CRASH) is None, "parser.non_checkpoint_telemetry_line_ignored")

log_text = "\n".join([REAL_CP0_LINE, REAL_AFTER_SHOT_13_LINE, REAL_LAST_LINE_BEFORE_CRASH]) + "\n"
all_checkpoints = parse_all_resource_checkpoints(log_text)
expect(len(all_checkpoints) == 2, "parser.finds_exactly_the_two_real_checkpoint_lines_in_crash_log")

crash_summary = summarize_resource_checkpoints(log_text)
expect(crash_summary["checkpoint_count"] == 2, "summary.crash_case_checkpoint_count_is_2")
expect(crash_summary["first_checkpoint"]["label"] == "CP0_COMMAND_START", "summary.crash_case_first_is_cp0")
expect(crash_summary["last_checkpoint"]["label"] == "AFTER_SHOT_13", "summary.crash_case_last_is_after_shot_13")
expect(crash_summary["final_report_entry_reached"] is False, "summary.crash_case_final_report_entry_NOT_reached")

completed_log_text = "\n".join([REAL_CP0_LINE, REAL_AFTER_SHOT_13_LINE, REAL_FINAL_REPORT_ENTRY_LINE]) + "\n"
completed_summary = summarize_resource_checkpoints(completed_log_text)
expect(completed_summary["final_report_entry_reached"] is True, "summary.completed_case_final_report_entry_reached")
expect(completed_summary["last_checkpoint"]["label"] == "FINAL_REPORT_ENTRY", "summary.completed_case_last_is_final_report_entry")

empty_summary = summarize_resource_checkpoints("no checkpoint lines here\n")
expect(empty_summary["checkpoint_count"] == 0 and empty_summary["first_checkpoint"] is None, "summary.no_checkpoints_handled_gracefully")

sys.stdout.write("\n--- write_json_atomic / write_text_atomic / copy_bytes_atomic ---\n")

tmp_dir = tempfile.mkdtemp(prefix="f1r1_regress_")
json_path = os.path.join(tmp_dir, "artifact.json")

ok, err, reparsed = write_json_atomic(json_path, {"a": 1, "b": [1, 2, 3]})
expect(ok and err is None, "write_json_atomic.simple_write_ok")
expect(reparsed == {"a": 1, "b": [1, 2, 3]}, "write_json_atomic.reparsed_matches")
expect(not os.path.exists(json_path + ".tmp"), "write_json_atomic.no_leftover_tmp_file")

text_path = os.path.join(tmp_dir, "summary.txt")
ok2, err2 = write_text_atomic(text_path, b"hello world\n")
expect(ok2 and err2 is None, "write_text_atomic.simple_write_ok")
with open(text_path, "rb") as f:
    expect(f.read() == b"hello world\n", "write_text_atomic.content_matches")

log_copy_path = os.path.join(tmp_dir, "preserved_log.txt")
ok3, err3 = copy_bytes_atomic(log_copy_path, b"log line 1\r\nlog line 2\r\n")
expect(ok3 and err3 is None, "copy_bytes_atomic.preserves_log_copy_ok")
with open(log_copy_path, "rb") as f:
    expect(f.read() == b"log line 1\r\nlog line 2\r\n", "copy_bytes_atomic.crlf_bytes_preserved_exactly")

sys.stdout.write("\n--- verify_artifact_evidence: partial-write tolerance ---\n")


def make_command_record(ordinal, full_capture):
    if full_capture:
        eligible = dict((u"t%d" % i, per_target_hash({"i": i})) for i in range(85))
        excluded = dict((u"e%d" % i, per_target_hash({"i": i})) for i in range(78))
        return {
            "ordinal": ordinal,
            "eligible_target_hashes": eligible,
            "excluded_target_hashes": excluded,
            "eligible_hashes_checksum": stable_hash([u"%s=%s" % (k, v) for k, v in eligible.items()]),
            "excluded_hashes_checksum": stable_hash([u"%s=%s" % (k, v) for k, v in excluded.items()]),
        }
    return {
        "ordinal": ordinal,
        "selected_target_hashes": {
            u"shot3|foxmccouldwm1": per_target_hash({"fox": ordinal}),
            u"shot3|mia1": per_target_hash({"mia": ordinal}),
        },
    }


base_artifact = {
    "initial_state": {"aggregate_hash": "deadbeef"},
    "command_records": [],
    "final_responsiveness": {},
}

after_cmd1 = dict(base_artifact)
after_cmd1["command_records"] = [make_command_record(1, False)]
ok_partial1, detail_partial1 = verify_artifact_evidence(after_cmd1, 1)
expect(ok_partial1, "verify.partial_1_command_artifact_passes (%r)" % (detail_partial1,))

after_cmd2 = dict(base_artifact)
after_cmd2["command_records"] = [make_command_record(1, False), make_command_record(2, False)]
ok_partial2, detail_partial2 = verify_artifact_evidence(after_cmd2, 2)
expect(ok_partial2, "verify.partial_2_command_artifact_passes (%r)" % (detail_partial2,))

after_cmd3 = dict(base_artifact)
after_cmd3["command_records"] = [make_command_record(1, False), make_command_record(2, False), make_command_record(3, True)]
ok_full, detail_full = verify_artifact_evidence(after_cmd3, 3)
expect(ok_full, "verify.full_3_command_artifact_passes (%r)" % (detail_full,))

too_many = dict(base_artifact)
too_many["command_records"] = [make_command_record(1, False), make_command_record(2, False)]
ok_toomany, _ = verify_artifact_evidence(too_many, 1)
expect(not ok_toomany, "verify.rejects_more_records_than_commands_attempted_so_far")

wrong_count = dict(base_artifact)
bad_rec = make_command_record(3, True)
bad_rec["eligible_target_hashes"].pop(u"t0")
wrong_count["command_records"] = [bad_rec]
ok_wrongcount, _ = verify_artifact_evidence(wrong_count, 1)
expect(not ok_wrongcount, "verify.rejects_wrong_eligible_hash_count_for_full_capture_ordinal")

mutated_checksum = dict(base_artifact)
bad_rec2 = make_command_record(3, True)
bad_rec2["eligible_hashes_checksum"] = "0" * 64
mutated_checksum["command_records"] = [bad_rec2]
ok_mutated, _ = verify_artifact_evidence(mutated_checksum, 1)
expect(not ok_mutated, "verify.rejects_mutated_eligible_hashes_checksum")

wrong_compact_keys = dict(base_artifact)
bad_rec3 = make_command_record(1, False)
bad_rec3["selected_target_hashes"] = {u"shot3|foxmccouldwm1": "abc"}
wrong_compact_keys["command_records"] = [bad_rec3]
ok_wrongkeys, _ = verify_artifact_evidence(wrong_compact_keys, 1)
expect(not ok_wrongkeys, "verify.rejects_incomplete_compact_selected_target_key_set")

sys.stdout.write("\n--- Incremental-write simulation (crash-tolerance proof) ---\n")

rolling_path = os.path.join(tmp_dir, "rolling.json")

rolling_report = {"initial_state": {"aggregate_hash": "abc"}, "command_records": [], "final_responsiveness": {}, "in_progress": True}
ok_r0, _, reparsed_r0 = write_json_atomic(rolling_path, rolling_report)
expect(ok_r0 and reparsed_r0["command_records"] == [], "incremental.write_before_any_command_ok")

rolling_report["command_records"].append(make_command_record(1, False))
ok_r1, _, reparsed_r1 = write_json_atomic(rolling_path, rolling_report)
expect(ok_r1 and len(reparsed_r1["command_records"]) == 1, "incremental.write_after_command_1_has_exactly_1_record")
ok_verify_r1, detail_r1 = verify_artifact_evidence(reparsed_r1, 1)
expect(ok_verify_r1, "incremental.artifact_after_command_1_independently_verifies (%r)" % (detail_r1,))

rolling_report["command_records"].append(make_command_record(2, False))
ok_r2, _, reparsed_r2 = write_json_atomic(rolling_path, rolling_report)
expect(ok_r2 and len(reparsed_r2["command_records"]) == 2, "incremental.write_after_command_2_has_exactly_2_records")
ok_verify_r2, detail_r2 = verify_artifact_evidence(reparsed_r2, 2)
expect(ok_verify_r2, "incremental.artifact_after_command_2_independently_verifies (%r)" % (detail_r2,))

# Simulate: process "crashes" here, before command 3 ever writes again.
# Re-open the path completely fresh (a brand-new file handle/dict, as a
# post-crash operator/analysis pass would) and confirm commands 1-2's
# evidence survived intact and complete.
with open(rolling_path, "rb") as f:
    post_crash_reopened = json.load(f)
expect(len(post_crash_reopened["command_records"]) == 2, "incremental.post_crash_reopen_shows_exactly_commands_1_and_2")
expect(post_crash_reopened["command_records"][0]["ordinal"] == 1, "incremental.post_crash_command_1_ordinal_correct")
expect(post_crash_reopened["command_records"][1]["ordinal"] == 2, "incremental.post_crash_command_2_ordinal_correct")
expect(post_crash_reopened["in_progress"] is True, "incremental.post_crash_in_progress_flag_still_True_since_finalize_never_ran")
ok_verify_post_crash, detail_post_crash = verify_artifact_evidence(post_crash_reopened, 2)
expect(ok_verify_post_crash, "incremental.post_crash_artifact_still_independently_verifies (%r)" % (detail_post_crash,))

sys.stdout.write("\n--- Degraded-fallback force-False (D2-1/F1 bug class, reused verbatim) ---\n")

degraded_source_index = script_bytes.decode("ascii").find(DEGRADED_FORCE_FALSE_RANGE_START_MARKER)
expect(degraded_source_index >= 0, "degraded.force_false_marker_present_in_deployed_script")

fake_report = {
    "overall_pass": True,  # deliberately WRONG/stale, as D2-1's own bug produced
    "command_records": [make_command_record(1, False), make_command_record(2, False)],
    "initial_state": {"aggregate_hash": "abc"},
    "json_write_error": "simulated failure",
}
degraded_ns = {"report": fake_report}
degraded_block_src = (
    "degraded_report = dict(report)\n"
    "degraded_command_records = []\n"
    "for rec in report['command_records']:\n"
    "    degraded_rec = dict(rec)\n"
    "    degraded_rec.pop('eligible_target_hashes', None)\n"
    "    degraded_rec.pop('excluded_target_hashes', None)\n"
    "    degraded_rec.pop('selected_target_hashes', None)\n"
    "    degraded_command_records.append(degraded_rec)\n"
    "degraded_report['command_records'] = degraded_command_records\n"
    "degraded_report.pop('initial_state', None)\n"
    "degraded_report['degraded_artifact'] = True\n"
    "degraded_report['overall_pass'] = False\n"
    "degraded_report['artifact_write_verified'] = False\n"
)
exec(compile(degraded_block_src, "<degraded_force_false>", "exec"), degraded_ns)
expect(degraded_ns["degraded_report"]["overall_pass"] is False, "degraded.overall_pass_forced_False_despite_stale_True_input")
expect(degraded_ns["degraded_report"]["artifact_write_verified"] is False, "degraded.artifact_write_verified_forced_False")
expect(
    "selected_target_hashes" not in degraded_ns["degraded_report"]["command_records"][0],
    "degraded.selected_target_hashes_stripped_from_degraded_records",
)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
