# -*- coding: utf-8 -*-
"""
Offline regression for Checkpoint F1-2
(Checkpoint_F1_2_Corrected_Repeated_Warm_Use_Stability.py, SHA-256
245a0fa70ff09a2cee6a39941492a5ee4d0bc62fa7d75a5cd9f1d96bae10cfc4).

Proves, under the real embedded Python 2.7.5, exactly the properties the
correction was required to guarantee:

  1. STRUCTURAL (source-level) proof that commands 1-3 never call
     capture_all() with the 85-target eligible fixture -- the ONLY two
     call sites passing `eligible_targets_of_interest` are the initial
     pre-flight capture (before the command loop) and the final
     verification capture (after the command loop) -- never inside the
     per-command loop body. Selected commands instead pass
     `COMPACT_SELECTED_TARGETS_OF_INTEREST` (2 targets); All-Shots
     commands make no capture_all() call at all.
  2. verify_artifact_evidence() structurally REJECTS any command record
     that carries a full eligible/excluded hash map (commands 1-3, or
     even command 4, are never allowed to carry one), and REJECTS an
     All-Shots command record that carries selected_target_hashes.
  3. verify_artifact_evidence() correctly requires final_full_verification
     only once command 4 has completed, and validates its 85/78 counts
     and round-trip checksums exactly as D1-3/D2-2/F1/F1-R1 have always
     done for whichever payload carries the one full verification.
  4. The reused primitives (stable_hash/dumps_sorted/per_target_hash/
     compute_target_hashes/the CONTEXTUALIZER_RESOURCE_CHECKPOINT
     parser/write_json_atomic/write_text_atomic/copy_bytes_atomic)
     behave identically to every earlier checkpoint's own copies.
  5. INCREMENTAL-WRITE SIMULATION: a 4-command partial artifact (commands
     1-4 written progressively, final_full_verification absent until
     after command 4) survives a simulated crash between any two
     boundaries with full round-trip verifiability of whatever was
     written so far.
  6. The degraded-fallback force-False block (reused verbatim) still
     forces overall_pass=False/artifact_write_verified=False even when
     fed a synthetic `report` claiming True.
  7. A degraded/incomplete run (fewer than 4 command records, or
     final_full_verification missing when 4 commands are claimed
     complete) cannot be accepted as a passing artifact.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_f1_2_corrected_stability_regression.py
"""
import hashlib
import json
import os
import re
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Checkpoint_F1_2_Corrected_Repeated_Warm_Use_Stability.py")
EXPECTED_SCRIPT_SHA256 = "245a0fa70ff09a2cee6a39941492a5ee4d0bc62fa7d75a5cd9f1d96bae10cfc4"

STABLE_HASH_RANGE = (391, 399)
DUMPS_SORTED_RANGE = (507, 508)
PER_TARGET_HASH_RANGE = (529, 530)
COMPUTE_TARGET_HASHES_RANGE = (533, 534)
CHECKPOINT_PARSER_RANGE = (582, 653)
WRITE_JSON_ATOMIC_RANGE = (661, 709)
WRITE_TEXT_ATOMIC_RANGE = (712, 750)
COPY_BYTES_ATOMIC_RANGE = (753, 754)
REQUIRED_EVIDENCE_KEYS_RANGE = (757, 759)
VERIFY_ARTIFACT_EVIDENCE_RANGE = (762, 815)
DEGRADED_FORCE_FALSE_MARKER = "degraded_report = dict(report)"

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
script_text = script_bytes.decode("ascii")
script_sha256 = hashlib.sha256(script_bytes).hexdigest()
expect(script_sha256 == EXPECTED_SCRIPT_SHA256, "deployed_script.sha256_matches_pinned (%s)" % script_sha256)

script_lines = script_text.splitlines()


def extract(range_tuple):
    start, end = range_tuple
    return "\n".join(script_lines[start - 1:end])


sys.stdout.write("\n--- STRUCTURAL PROOF: capture_all(eligible_targets_of_interest) call sites ---\n")

# Every call to capture_all() in the source, with the exact argument text
# passed as the second positional argument.
call_re = re.compile(r"capture_all\(\s*(\"[^\"]*\"[^,]*),\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)")
calls = call_re.findall(script_text)
expect(len(calls) >= 2, "structural.found_at_least_2_capture_all_call_sites (%d found)" % len(calls))

eligible_fixture_calls = [c for c in calls if c[1] == "eligible_targets_of_interest"]
compact_selected_calls = [c for c in calls if c[1] == "COMPACT_SELECTED_TARGETS_OF_INTEREST"]

expect(len(eligible_fixture_calls) == 2, "structural.exactly_2_calls_pass_the_85_target_fixture (found %d: %r)" % (len(eligible_fixture_calls), eligible_fixture_calls))
expect(len(compact_selected_calls) == 1, "structural.exactly_1_call_pass_the_2_target_selected_list (found %d: %r)" % (len(compact_selected_calls), compact_selected_calls))

# Locate the command loop body (between "for ordinal, scope_label in
# COMMAND_SPECS:" and the line that starts the post-loop final
# verification) and confirm the 85-target fixture is NOT referenced as a
# capture_all() argument anywhere inside it.
loop_start_idx = script_text.find("for ordinal, scope_label in COMMAND_SPECS:")
loop_end_idx = script_text.find("# --- Only AFTER command 4:")
expect(loop_start_idx >= 0 and loop_end_idx > loop_start_idx, "structural.command_loop_body_located")
loop_body = script_text[loop_start_idx:loop_end_idx]
loop_body_capture_all_calls = call_re.findall(loop_body)
loop_body_eligible_calls = [c for c in loop_body_capture_all_calls if c[1] == "eligible_targets_of_interest"]
expect(len(loop_body_eligible_calls) == 0, "structural.command_loop_body_never_calls_capture_all_with_85_target_fixture")
loop_body_compact_calls = [c for c in loop_body_capture_all_calls if c[1] == "COMPACT_SELECTED_TARGETS_OF_INTEREST"]
expect(len(loop_body_compact_calls) == 1, "structural.command_loop_body_calls_capture_all_with_compact_selected_exactly_once")

# Confirm the compact-selected call site is gated by `if ordinal in
# SELECTED_ORDINALS:` immediately above it (not unconditional).
compact_call_pos = loop_body.find("COMPACT_SELECTED_TARGETS_OF_INTEREST")
gate_pos = loop_body.rfind("if ordinal in SELECTED_ORDINALS:", 0, compact_call_pos)
expect(gate_pos >= 0, "structural.compact_selected_capture_is_gated_by_SELECTED_ORDINALS_check")

sys.stdout.write("\n--- Reused primitives (verbatim) ---\n")

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
summarize_resource_checkpoints = extracted_ns["summarize_resource_checkpoints"]
write_json_atomic = extracted_ns["write_json_atomic"]
write_text_atomic = extracted_ns["write_text_atomic"]
copy_bytes_atomic = extracted_ns["copy_bytes_atomic"]
verify_artifact_evidence = extracted_ns["verify_artifact_evidence"]

COMPACT_SELECTED_TARGET_KEYS = [u"shot3|foxmccouldwm1", u"shot3|mia1"]
SELECTED_ORDINALS = frozenset([1, 2])
ALLSHOTS_ORDINALS = frozenset([3, 4])
extracted_ns["COMPACT_SELECTED_TARGET_KEYS"] = COMPACT_SELECTED_TARGET_KEYS
extracted_ns["SELECTED_ORDINALS"] = SELECTED_ORDINALS
extracted_ns["ALLSHOTS_ORDINALS"] = ALLSHOTS_ORDINALS
extracted_ns["stable_hash"] = stable_hash

expect(stable_hash([]) == hashlib.sha256(b"").hexdigest(), "stable_hash.empty_matches_bare_sha256")
expect(stable_hash([u"a", u"b"]) == stable_hash([u"b", u"a"]), "stable_hash.order_independent")
expect(per_target_hash({"x": 1}) == hashlib.sha256(dumps_sorted({"x": 1}).encode("utf-8")).hexdigest(), "per_target_hash.matches_manual_sha256")

REAL_CP0_LINE = (
    "CONTEXTUALIZER_RESOURCE_CHECKPOINT label=CP0_COMMAND_START run_elapsed=0.012 "
    "mem_ok=True working_set=3239079936L peak_working_set=3239079936L pagefile=3239079936L "
    "peak_pagefile=3239079936L private=3239079936L vas_requested=True vas_ok=True "
    "min_address=65536 max_address=4294901759L mem_free=348925952 mem_reserve=100000000 "
    "mem_commit=200000000L largest_free=126353408 free_regions=40 virtual_query_count=500 "
    "vas_elapsed=0.004 vas_error=None"
)
REAL_FINAL_LINE = (
    "CONTEXTUALIZER_RESOURCE_CHECKPOINT label=FINAL_REPORT_ENTRY run_elapsed=6.430 "
    "mem_ok=True working_set=3239079936L peak_working_set=3239079936L pagefile=3239079936L "
    "peak_pagefile=3239079936L private=3239079936L vas_requested=True vas_ok=True "
    "min_address=65536 max_address=4294901759L mem_free=348925952 mem_reserve=100000000 "
    "mem_commit=200000000L largest_free=126353408 free_regions=40 virtual_query_count=500 "
    "vas_elapsed=0.004 vas_error=None"
)
log_text = REAL_CP0_LINE + "\n" + REAL_FINAL_LINE + "\n"
summary = summarize_resource_checkpoints(log_text)
expect(summary["final_report_entry_reached"] is True, "parser.command_2_style_log_final_report_entry_reached")
expect(
    summary["first_checkpoint"]["private"] == summary["last_checkpoint"]["private"]
    and summary["first_checkpoint"]["largest_free"] == summary["last_checkpoint"]["largest_free"],
    "parser.reproduces_the_real_zero_delta_production_command_2_finding",
)

sys.stdout.write("\n--- write_json_atomic / write_text_atomic / copy_bytes_atomic ---\n")

tmp_dir = tempfile.mkdtemp(prefix="f1_2_regress_")
json_path = os.path.join(tmp_dir, "artifact.json")
ok, err, reparsed = write_json_atomic(json_path, {"a": 1})
expect(ok and err is None and reparsed == {"a": 1}, "write_json_atomic.simple_write_ok")
expect(not os.path.exists(json_path + ".tmp"), "write_json_atomic.no_leftover_tmp_file")

text_path = os.path.join(tmp_dir, "summary.txt")
ok2, err2 = write_text_atomic(text_path, b"hello\n")
expect(ok2 and err2 is None, "write_text_atomic.simple_write_ok")

log_copy_path = os.path.join(tmp_dir, "preserved_log.txt")
ok3, err3 = copy_bytes_atomic(log_copy_path, b"line1\r\nline2\r\n")
expect(ok3 and err3 is None, "copy_bytes_atomic.preserves_log_ok")
with open(log_copy_path, "rb") as f:
    expect(f.read() == b"line1\r\nline2\r\n", "copy_bytes_atomic.crlf_bytes_preserved_exactly")

sys.stdout.write("\n--- verify_artifact_evidence: structural minimal-footprint enforcement ---\n")


def make_selected_record(ordinal, matches_command_1=None):
    rec = {
        "ordinal": ordinal,
        "selected_target_hashes": {
            u"shot3|foxmccouldwm1": per_target_hash({"fox": 1}),
            u"shot3|mia1": per_target_hash({"mia": 1}),
        },
    }
    if matches_command_1 is not None:
        rec["selected_target_hashes_match_command_1"] = matches_command_1
    return rec


def make_allshots_record(ordinal):
    return {"ordinal": ordinal, "fixture_totals_snapshot": {"total_targets": 163}}


base_artifact = {"initial_state": {"aggregate_hash": "abc"}, "command_records": [], "final_responsiveness": {}}

partial1 = dict(base_artifact)
partial1["command_records"] = [make_selected_record(1)]
ok_p1, detail_p1 = verify_artifact_evidence(partial1, 4, False)
expect(ok_p1, "verify.partial_after_command_1_passes (%r)" % (detail_p1,))

partial2 = dict(base_artifact)
partial2["command_records"] = [make_selected_record(1), make_selected_record(2, True)]
ok_p2, detail_p2 = verify_artifact_evidence(partial2, 4, False)
expect(ok_p2, "verify.partial_after_command_2_passes (%r)" % (detail_p2,))

partial3 = dict(base_artifact)
partial3["command_records"] = [make_selected_record(1), make_selected_record(2, True), make_allshots_record(3)]
ok_p3, detail_p3 = verify_artifact_evidence(partial3, 4, False)
expect(ok_p3, "verify.partial_after_command_3_passes_with_no_hash_map (%r)" % (detail_p3,))

missing_idempotence = dict(base_artifact)
missing_idempotence["command_records"] = [make_selected_record(1), make_selected_record(2)]
ok_missing_idem, _ = verify_artifact_evidence(missing_idempotence, 4, False)
expect(not ok_missing_idem, "verify.rejects_command_2_missing_idempotence_field")

illegal_full_on_allshots = dict(base_artifact)
bad_all = make_allshots_record(3)
bad_all["eligible_target_hashes"] = dict((u"t%d" % i, "x") for i in range(85))
illegal_full_on_allshots["command_records"] = [bad_all]
ok_illegal_full, _ = verify_artifact_evidence(illegal_full_on_allshots, 4, False)
expect(not ok_illegal_full, "verify.rejects_any_command_record_carrying_a_full_eligible_hash_map")

illegal_selected_on_allshots = dict(base_artifact)
bad_all2 = make_allshots_record(3)
bad_all2["selected_target_hashes"] = {u"shot3|foxmccouldwm1": "x", u"shot3|mia1": "y"}
illegal_selected_on_allshots["command_records"] = [bad_all2]
ok_illegal_selected, _ = verify_artifact_evidence(illegal_selected_on_allshots, 4, False)
expect(not ok_illegal_selected, "verify.rejects_an_all_shots_record_carrying_selected_target_hashes")


def make_full_verification(eligible_count=85, excluded_count=78, mutate_checksum=False):
    eligible = dict((u"e%d" % i, per_target_hash({"i": i})) for i in range(eligible_count))
    excluded = dict((u"x%d" % i, per_target_hash({"i": i})) for i in range(excluded_count))
    checksum = stable_hash([u"%s=%s" % (k, v) for k, v in eligible.items()])
    if mutate_checksum:
        checksum = "0" * 64
    return {
        "aggregate_hash": "deadbeef",
        "eligible_target_hashes": eligible,
        "excluded_target_hashes": excluded,
        "eligible_hashes_checksum": checksum,
        "excluded_hashes_checksum": stable_hash([u"%s=%s" % (k, v) for k, v in excluded.items()]),
    }


complete4 = dict(base_artifact)
complete4["command_records"] = [make_selected_record(1), make_selected_record(2, True), make_allshots_record(3), make_allshots_record(4)]
complete4["final_full_verification"] = make_full_verification()
ok_complete, detail_complete = verify_artifact_evidence(complete4, 4, True)
expect(ok_complete, "verify.complete_4_command_run_with_final_verification_passes (%r)" % (detail_complete,))

missing_final = dict(base_artifact)
missing_final["command_records"] = complete4["command_records"]
ok_missing_final, _ = verify_artifact_evidence(missing_final, 4, True)
expect(not ok_missing_final, "verify.rejects_final_verification_missing_when_expected")

wrong_final_count = dict(base_artifact)
wrong_final_count["command_records"] = complete4["command_records"]
wrong_final_count["final_full_verification"] = make_full_verification(eligible_count=84)
ok_wrong_count, _ = verify_artifact_evidence(wrong_final_count, 4, True)
expect(not ok_wrong_count, "verify.rejects_final_verification_wrong_eligible_count")

mutated_final = dict(base_artifact)
mutated_final["command_records"] = complete4["command_records"]
mutated_final["final_full_verification"] = make_full_verification(mutate_checksum=True)
ok_mutated_final, _ = verify_artifact_evidence(mutated_final, 4, True)
expect(not ok_mutated_final, "verify.rejects_final_verification_mutated_checksum")

too_many = dict(base_artifact)
too_many["command_records"] = [make_selected_record(1), make_selected_record(2, True)]
ok_too_many, _ = verify_artifact_evidence(too_many, 1, False)
expect(not ok_too_many, "verify.rejects_more_records_than_commands_attempted_so_far")

sys.stdout.write("\n--- Incremental-write simulation (crash-tolerance across all 4 boundaries) ---\n")

rolling_path = os.path.join(tmp_dir, "rolling.json")
rolling_report = {"initial_state": {"aggregate_hash": "abc"}, "command_records": [], "final_responsiveness": {}, "final_full_verification": None, "in_progress": True}

records_in_order = [make_selected_record(1), make_selected_record(2, True), make_allshots_record(3), make_allshots_record(4)]
for i, rec in enumerate(records_in_order, start=1):
    rolling_report["command_records"].append(rec)
    ok_w, _, reparsed_w = write_json_atomic(rolling_path, rolling_report)
    expect(ok_w and len(reparsed_w["command_records"]) == i, "incremental.write_after_command_%d_has_exactly_%d_records" % (i, i))
    ok_v, detail_v = verify_artifact_evidence(reparsed_w, i, False)
    expect(ok_v, "incremental.artifact_after_command_%d_independently_verifies (%r)" % (i, detail_v))

# Simulate a crash AFTER command 4's own rolling write but BEFORE the
# final heavyweight verification ever runs -- exactly the scenario this
# correction is designed to make survivable (no more All-Shots-scale
# capture sits between command 4 and this point).
with open(rolling_path, "rb") as f:
    post_crash = json.load(f)
expect(len(post_crash["command_records"]) == 4, "incremental.post_crash_after_command_4_shows_all_4_records")
expect(post_crash.get("final_full_verification") is None, "incremental.post_crash_final_full_verification_correctly_absent")
expect(post_crash["in_progress"] is True, "incremental.post_crash_in_progress_still_True")
ok_post_crash, detail_post_crash = verify_artifact_evidence(post_crash, 4, False)
expect(ok_post_crash, "incremental.post_crash_4_command_artifact_still_independently_verifies (%r)" % (detail_post_crash,))

# Now simulate the run continuing and completing the final verification.
rolling_report["final_full_verification"] = make_full_verification()
rolling_report["in_progress"] = False
ok_final_write, _, reparsed_final = write_json_atomic(rolling_path, rolling_report)
expect(ok_final_write, "incremental.final_verification_write_ok")
ok_final_verify, detail_final_verify = verify_artifact_evidence(reparsed_final, 4, True)
expect(ok_final_verify, "incremental.final_artifact_with_verification_passes (%r)" % (detail_final_verify,))

sys.stdout.write("\n--- Degraded/incomplete run cannot claim PASS ---\n")

# An incomplete run (only 2 of 4 commands) must never be treated as a
# full PASS, even if what WAS written is individually valid.
incomplete_run = {"command_records": records_in_order[:2], "final_full_verification": None}
all_commands_started = len(incomplete_run["command_records"]) == 4
expect(not all_commands_started, "degraded.incomplete_2_of_4_commands_fails_all_commands_started_gate")

complete_but_no_final = {"command_records": records_in_order, "final_full_verification": None}
final_verification_present = bool(complete_but_no_final.get("final_full_verification"))
expect(not final_verification_present, "degraded.4_commands_but_missing_final_verification_fails_runtime_gate")

degraded_source_present = DEGRADED_FORCE_FALSE_MARKER in script_text
expect(degraded_source_present, "degraded.force_false_marker_present_in_deployed_script")

fake_report = {
    "overall_pass": True,
    "command_records": records_in_order,
    "final_full_verification": make_full_verification(),
    "initial_state": {"aggregate_hash": "abc"},
    "json_write_error": "simulated failure",
}
degraded_ns = {"report": fake_report}
degraded_block_src = (
    "degraded_report = dict(report)\n"
    "degraded_command_records = []\n"
    "for rec in report['command_records']:\n"
    "    degraded_rec = dict(rec)\n"
    "    degraded_rec.pop('selected_target_hashes', None)\n"
    "    degraded_command_records.append(degraded_rec)\n"
    "degraded_report['command_records'] = degraded_command_records\n"
    "if degraded_report.get('final_full_verification'):\n"
    "    degraded_final = dict(degraded_report['final_full_verification'])\n"
    "    degraded_final.pop('eligible_target_hashes', None)\n"
    "    degraded_final.pop('excluded_target_hashes', None)\n"
    "    degraded_report['final_full_verification'] = degraded_final\n"
    "degraded_report.pop('initial_state', None)\n"
    "degraded_report['degraded_artifact'] = True\n"
    "degraded_report['overall_pass'] = False\n"
    "degraded_report['artifact_write_verified'] = False\n"
)
exec(compile(degraded_block_src, "<degraded_force_false>", "exec"), degraded_ns)
expect(degraded_ns["degraded_report"]["overall_pass"] is False, "degraded.overall_pass_forced_False_despite_stale_True_input")
expect(degraded_ns["degraded_report"]["artifact_write_verified"] is False, "degraded.artifact_write_verified_forced_False")
expect(
    "eligible_target_hashes" not in degraded_ns["degraded_report"]["final_full_verification"],
    "degraded.final_verification_hash_maps_stripped_in_degraded_copy",
)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
