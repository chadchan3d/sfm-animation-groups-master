# -*- coding: utf-8 -*-
"""
Offline dry-run for Checkpoint_Process_Attempt_Guard_Qualification.py
itself (the read-only real-SFM snapshot/evidence utility, not the
production guard -- see test_process_attempt_guard_regression.py for
that).

Proves, under the real embedded Python 2.7.5 with a fake sfmApp/main
window and a fully controllable fake production-log fingerprint (so the
whole 15-snapshot/8-run schedule can be exercised deterministically
offline, without depending on or mutating the real
sfm_rebuild_control_groups.txt on this machine), that the independent-
review-corrected evidence-file discipline (2026-09-24) works correctly:
  - a pre-existing production log observed at snapshot 01 (baseline) is
    fingerprinted and seeds last_known_log_sha256, but is NEVER copied
    into a run-evidence file and never advances the run counter;
  - the first genuinely NEW log content observed at a later snapshot
    becomes run 01;
  - all 15 fixed-schedule snapshot names are used in order;
  - a snapshot taken immediately after a refused invocation captures no
    run, and its own recorded log sha256 exactly matches the immediately
    preceding snapshot's;
  - run indices remain contiguous 1..8 despite three refused invocations
    (snapshot 07, 12, 13) interleaved among them;
  - numbering (via the continuation-state pointer) survives a simulated
    restart;
  - write_evidence_json_once()/write_evidence_text_once() still refuse to
    overwrite an existing path;
  - the final rollup indexes all 15 snapshots, all 8 runs, and all three
    mechanically-computed refusal fingerprint-equality proofs, each
    correctly `equal: true`.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_checkpoint_process_attempt_guard_dryrun.py
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile

from PySide import QtCore

CHECKPOINT_SCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "Checkpoint_Process_Attempt_Guard_Qualification.py",
)
PRODUCTION_CANDIDATE_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..",
        "audit_external_runtime",
        "Rebuild_Control_Groups_Normalizer.py",
    )
)
EXPECTED_PRODUCTION_SHA256 = "1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7"

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s\n" % label)
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s\n" % label)


with open(CHECKPOINT_SCRIPT_PATH, "rb") as f:
    checkpoint_bytes = f.read()
checkpoint_text = checkpoint_bytes  # kept as bytes; compile() note below

trailing_call = "\nmain()\n"
idx = checkpoint_text.rfind(trailing_call)
expect(idx != -1, "checkpoint_script.trailing_main_call_located")
definitions_only_text = checkpoint_text[:idx]

expect(
    "\nStartRebuildControlGroups()\n" not in definitions_only_text,
    "checkpoint_script.never_contains_an_unguarded_real_invocation_call",
)
expect(
    "GetShots(" not in definitions_only_text
    and "RebuildScopeDialog" not in definitions_only_text,
    "checkpoint_script.never_references_scope_dialog_machinery",
)
expect(
    "collect_scope_master_wanted_folds" not in definitions_only_text
    and "acquire_master_index_via_qualified_authority" not in definitions_only_text
    and "NATIVE_REBUILD" not in definitions_only_text,
    "checkpoint_script.never_references_substantial_traversal_or_native_work",
)


class _FakeMainWindow(QtCore.QObject):
    pass


class _FakeSfmApp(object):
    def __init__(self, main_window):
        self._main_window = main_window

    def GetMainWindow(self):
        return self._main_window


def make_fake_log_fingerprint(fake_log_state):
    # fake_log_state: a shared, mutable {"bytes": <bytes-or-None>} dict,
    # deliberately OUTSIDE any single namespace so it persists across
    # simulated restarts (fresh_ns() calls) exactly like a real log file
    # on disk would, without touching the real
    # sfm_rebuild_control_groups.txt on this machine at all.
    def fake_log_fingerprint(output_path):
        raw = fake_log_state["bytes"]
        if raw is None:
            return {
                "exists": False,
                "size_bytes": None,
                "mtime": None,
                "sha256": None,
                "raw_bytes": None,
            }
        return {
            "exists": True,
            "size_bytes": len(raw),
            "mtime": 0.0,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "raw_bytes": raw,
        }

    return fake_log_fingerprint


def fresh_ns(tmp_dir, fake_log_state):
    ns = {
        "sfmApp": _FakeSfmApp(_FakeMainWindow()),
        "QtCore": QtCore,
    }
    exec(compile(definitions_only_text, "<checkpoint_defs>", "exec"), ns)

    ns["PRODUCTION_INSTALLED_PATH"] = PRODUCTION_CANDIDATE_PATH
    ns["EXPECTED_PRODUCTION_SHA256"] = EXPECTED_PRODUCTION_SHA256
    evidence_dir = tmp_dir + os.sep
    ns["EVIDENCE_DIR"] = evidence_dir
    ns["CONTINUATION_STATE_PATH"] = evidence_dir + "sfm_scope_guard_continuation_state.json"
    ns["FINAL_RESULT_PATH"] = evidence_dir + "sfm_scope_guard_final_result.json"
    ns["FINAL_SUMMARY_PATH"] = evidence_dir + "sfm_scope_guard_final_summary.txt"
    # Redirect the log-reading primitive to the controllable fake -- the
    # real OUTPUT_PATH is still extracted from the pinned production
    # candidate (proving that extraction works), but capture_current_
    # state() calls contextualizer_log_fingerprint(output_path) by name
    # at call time, so overriding it here redirects every call without
    # touching any real file.
    ns["contextualizer_log_fingerprint"] = make_fake_log_fingerprint(fake_log_state)
    return ns


tmp_dir = tempfile.mkdtemp(prefix="process_attempt_guard_checkpoint_dryrun_")
try:
    fake_log_state = {"bytes": None}

    ns = fresh_ns(tmp_dir, fake_log_state)

    load_production_definitions = ns["load_production_definitions"]
    read_continuation_state = ns["read_continuation_state"]
    write_evidence_json_once = ns["write_evidence_json_once"]
    write_evidence_text_once = ns["write_evidence_text_once"]
    CheckpointProcessAttemptGuardError = ns["CheckpointProcessAttemptGuardError"]
    RUN_LOG_LABELS = ns["RUN_LOG_LABELS"]
    SNAPSHOT_SCHEDULE = ns["SNAPSHOT_SCHEDULE"]
    REFUSAL_PROOF_PAIRS = ns["REFUSAL_PROOF_PAIRS"]

    prod_ns, prod_sha256, prod_text = load_production_definitions()
    expect(
        prod_sha256 == EXPECTED_PRODUCTION_SHA256,
        "load_production_definitions.reads_and_hashes_the_pinned_candidate_correctly",
    )
    expect(
        "_read_process_scope_state" in prod_ns and "OUTPUT_PATH" in prod_ns,
        "load_production_definitions.extracts_the_expected_real_definitions",
    )

    expect(len(RUN_LOG_LABELS) == 8, "schedule.exactly_eight_run_log_labels")
    expect(len(SNAPSHOT_SCHEDULE) == 15, "schedule.exactly_fifteen_snapshot_schedule_entries")
    expect(len(REFUSAL_PROOF_PAIRS) == 3, "schedule.exactly_three_refusal_proof_pairs")

    EXPECTED_SNAPSHOT_LABELS = [
        u"baseline", u"after_cancel", u"after_shot3", u"after_5shots", u"after_3shots",
        u"after_edit_repair", u"after_all_refusal", u"after_post_refusal_selected",
        u"after_reopen_selected", u"fresh_after_restart", u"after_all_shots",
        u"after_refused_selected", u"after_refused_all", u"reset_after_restart",
        u"final_after_restart_selected",
    ]
    expect(
        [op for (op, _st) in SNAPSHOT_SCHEDULE] == EXPECTED_SNAPSHOT_LABELS,
        "schedule.snapshot_operation_labels_match_the_exact_specified_order",
    )
    EXPECTED_STATES = [
        u"UNUSED", u"UNUSED", u"SELECTED_USED", u"SELECTED_USED", u"SELECTED_USED",
        u"SELECTED_USED", u"SELECTED_USED", u"SELECTED_USED", u"SELECTED_USED",
        u"UNUSED", u"FULL_SCOPE_STARTED", u"FULL_SCOPE_STARTED", u"FULL_SCOPE_STARTED",
        u"UNUSED", u"SELECTED_USED",
    ]
    expect(
        [st for (_op, st) in SNAPSHOT_SCHEDULE] == EXPECTED_STATES,
        "schedule.expected_states_match_the_exact_specified_order",
    )

    sys.stdout.write("\n--- write_evidence_*_once(): refuse-to-overwrite primitives ---\n")

    once_path = os.path.join(tmp_dir, "probe_evidence.json")
    write_evidence_json_once(once_path, {"a": 1})
    raised = False
    try:
        write_evidence_json_once(once_path, {"a": 2})
    except CheckpointProcessAttemptGuardError:
        raised = True
    expect(raised, "write_evidence_json_once.refuses_to_overwrite_an_existing_file")

    sys.stdout.write("\n--- Full 15-snapshot / 8-run walkthrough with a controllable fake log ---\n")

    main_fn = ns["main"]

    # Snapshot 01: baseline, with a NONEMPTY PRE-EXISTING log already on
    # "disk" (simulating leftover content from earlier qualification
    # work) -- must be seeded, never captured as a run.
    fake_log_state["bytes"] = b"PRE-EXISTING LOG FROM EARLIER WORK, NOT A REAL COMMAND"
    pre_existing_sha = hashlib.sha256(fake_log_state["bytes"]).hexdigest()
    main_fn()
    cont = read_continuation_state()
    expect(
        cont["captured_snapshots"][0]["operation"] == "baseline"
        and cont["captured_snapshots"][0]["baseline_seeded"] is True
        and cont["captured_snapshots"][0]["log_sha256"] == pre_existing_sha,
        "snap01.baseline_seeds_the_pre_existing_log_fingerprint",
    )
    expect(
        cont["last_known_log_sha256"] == pre_existing_sha,
        "snap01.continuation_state_last_known_log_sha256_seeded",
    )
    expect(
        cont["next_run_index"] == 1 and len(cont["captured_runs"]) == 0,
        "snap01.run_index_not_advanced_no_run_captured_for_pre_existing_log",
    )
    with open(os.path.join(tmp_dir, cont["captured_snapshots"][0]["filename"]), "rb") as f:
        snap01_content = json.loads(f.read().decode("utf-8"))
    expect(
        snap01_content.get("run_captured") is None
        and snap01_content.get("baseline_seeded") is True,
        "snap01.snapshot_json_itself_records_run_captured_none_and_baseline_seeded_true",
    )

    # Snapshot 02: after_cancel, log unchanged.
    main_fn()
    cont = read_continuation_state()
    expect(
        cont["captured_snapshots"][1]["operation"] == "after_cancel"
        and len(cont["captured_runs"]) == 0,
        "snap02.cancel_with_unchanged_log_captures_no_run",
    )

    def run_and_check(label, new_log_bytes, expected_operation, expected_run_label=None, expect_no_run=False):
        fake_log_state["bytes"] = new_log_bytes
        main_fn()
        c = read_continuation_state()
        latest = c["captured_snapshots"][-1]
        ok_op = latest["operation"] == expected_operation
        if expect_no_run:
            ok_run = latest.get("log_sha256") == (
                hashlib.sha256(new_log_bytes).hexdigest() if new_log_bytes is not None else None
            )
            run_unchanged = len(c["captured_runs"]) == run_and_check.prior_run_count[0]
            expect(ok_op and run_unchanged, "%s.operation_and_no_new_run_captured" % label)
        else:
            new_run = c["captured_runs"][-1] if c["captured_runs"] else None
            ok_run = (
                new_run is not None
                and new_run["label"] == expected_run_label
                and new_run["sha256"] == hashlib.sha256(new_log_bytes).hexdigest()
            )
            expect(ok_op and ok_run, "%s.operation_and_expected_run_captured" % label)
        run_and_check.prior_run_count[0] = len(c["captured_runs"])
        return c

    run_and_check.prior_run_count = [0]

    # Snapshot 03: after_shot3 -- first genuinely new log -> run 01.
    cont = run_and_check("snap03", b"LOG shot3 command output", "after_shot3", expected_run_label=u"selected_shot3")
    expect(cont["captured_runs"][0]["step_ordinal"] == 1, "snap03.run_captured_as_step_ordinal_one")

    # Snapshot 04-06: three more real commands.
    cont = run_and_check("snap04", b"LOG 5shots command output", "after_5shots", expected_run_label=u"selected_5shots")
    cont = run_and_check("snap05", b"LOG 3shots command output", "after_3shots", expected_run_label=u"selected_3shots")
    cont = run_and_check("snap06", b"LOG edit_repair command output", "after_edit_repair", expected_run_label=u"selected_edit_repair")
    snap06_sha = cont["captured_snapshots"][-1]["log_sha256"]

    # Snapshot 07: after_all_refusal -- REFUSED, log must be UNCHANGED
    # from snapshot 06, no new run.
    cont = run_and_check("snap07", b"LOG edit_repair command output", "after_all_refusal", expect_no_run=True)
    snap07_sha = cont["captured_snapshots"][-1]["log_sha256"]
    expect(snap07_sha == snap06_sha, "snap07.log_sha256_exactly_matches_snapshot06")

    # Snapshot 08: the real post-refusal Selected command -> run 05.
    cont = run_and_check("snap08", b"LOG after_all_refusal selected command output", "after_post_refusal_selected", expected_run_label=u"selected_after_all_refusal")
    expect(cont["captured_runs"][-1]["step_ordinal"] == 5, "snap08.run_captured_as_step_ordinal_five")

    # Snapshot 09: after_reopen_selected -> run 06.
    cont = run_and_check("snap09", b"LOG after_reopen selected command output", "after_reopen_selected", expected_run_label=u"selected_after_reopen")

    sys.stdout.write("\n--- Simulated restart (fresh namespace, same evidence dir + fake log state) ---\n")

    ns2 = fresh_ns(tmp_dir, fake_log_state)
    main_fn2 = ns2["main"]
    # Snapshot 10: fresh_after_restart -- log unchanged (still snapshot
    # 09's content, since nothing new has run yet in the "new process").
    main_fn2()
    cont = read_continuation_state()
    expect(
        cont["captured_snapshots"][9]["operation"] == "fresh_after_restart"
        and len(cont["captured_runs"]) == 6,
        "snap10.fresh_after_restart_log_unchanged_no_new_run",
    )

    def run_and_check2(main_fn_, label, new_log_bytes, expected_operation, expected_run_label=None, expect_no_run=False):
        fake_log_state["bytes"] = new_log_bytes
        main_fn_()
        c = read_continuation_state()
        latest = c["captured_snapshots"][-1]
        ok_op = latest["operation"] == expected_operation
        if expect_no_run:
            run_unchanged = len(c["captured_runs"]) == run_and_check2.prior_run_count[0]
            expect(ok_op and run_unchanged, "%s.operation_and_no_new_run_captured" % label)
        else:
            new_run = c["captured_runs"][-1] if c["captured_runs"] else None
            ok_run = (
                new_run is not None
                and new_run["label"] == expected_run_label
                and new_run["sha256"] == hashlib.sha256(new_log_bytes).hexdigest()
            )
            expect(ok_op and ok_run, "%s.operation_and_expected_run_captured" % label)
        run_and_check2.prior_run_count[0] = len(c["captured_runs"])
        return c

    run_and_check2.prior_run_count = [6]

    # Snapshot 11: after_all_shots -> run 07.
    cont = run_and_check2(main_fn2, "snap11", b"LOG all_shots command output", "after_all_shots", expected_run_label=u"all_shots")
    snap11_sha = cont["captured_snapshots"][-1]["log_sha256"]
    expect(cont["captured_runs"][-1]["step_ordinal"] == 7, "snap11.run_captured_as_step_ordinal_seven")

    # Snapshot 12: after_refused_selected -- REFUSED, log unchanged from 11.
    cont = run_and_check2(main_fn2, "snap12", b"LOG all_shots command output", "after_refused_selected", expect_no_run=True)
    snap12_sha = cont["captured_snapshots"][-1]["log_sha256"]
    expect(snap12_sha == snap11_sha, "snap12.log_sha256_exactly_matches_snapshot11")

    # Snapshot 13: after_refused_all -- REFUSED AGAIN, log unchanged from 11/12.
    cont = run_and_check2(main_fn2, "snap13", b"LOG all_shots command output", "after_refused_all", expect_no_run=True)
    snap13_sha = cont["captured_snapshots"][-1]["log_sha256"]
    expect(
        snap13_sha == snap11_sha and snap13_sha == snap12_sha,
        "snap13.log_sha256_exactly_matches_both_snapshot11_and_snapshot12",
    )

    with open(os.path.join(tmp_dir, "sfm_scope_guard_final_result.json"), "rb") as f:
        rollup_after_13 = json.loads(f.read().decode("utf-8"))
    proofs = rollup_after_13.get("refusal_proofs", [])
    expect(len(proofs) == 3, "rollup.all_three_refusal_proofs_present_after_snapshot_13")
    expect(
        all(p["equal"] is True for p in proofs),
        "rollup.all_three_refusal_proofs_report_equal_true",
    )

    sys.stdout.write("\n--- Second simulated restart ---\n")

    ns3 = fresh_ns(tmp_dir, fake_log_state)
    main_fn3 = ns3["main"]
    # Snapshot 14: reset_after_restart -- log unchanged (still snapshot 13's).
    main_fn3()
    cont = read_continuation_state()
    expect(
        cont["captured_snapshots"][13]["operation"] == "reset_after_restart"
        and len(cont["captured_runs"]) == 7,
        "snap14.reset_after_restart_log_unchanged_no_new_run",
    )

    # Snapshot 15: final_after_restart_selected -> run 08, the last one.
    fake_log_state["bytes"] = b"LOG final after_restart selected command output"
    main_fn3()
    cont = read_continuation_state()
    expect(
        cont["captured_snapshots"][14]["operation"] == "final_after_restart_selected"
        and len(cont["captured_runs"]) == 8
        and cont["captured_runs"][-1]["label"] == u"selected_after_restart"
        and cont["captured_runs"][-1]["step_ordinal"] == 8,
        "snap15.final_snapshot_captures_run_eight_selected_after_restart",
    )

    sys.stdout.write("\n--- Final rollup completeness ---\n")

    expect(
        len(cont["captured_snapshots"]) == 15,
        "final.exactly_fifteen_snapshots_captured",
    )
    expect(
        len(cont["captured_runs"]) == 8,
        "final.exactly_eight_runs_captured",
    )
    run_ordinals = [r["step_ordinal"] for r in cont["captured_runs"]]
    expect(
        run_ordinals == list(range(1, 9)),
        "final.run_indices_remain_contiguous_one_through_eight_despite_three_refusals",
    )
    expect(
        os.path.exists(os.path.join(tmp_dir, "sfm_scope_guard_snapshot_15_final_after_restart_selected.json")),
        "final.fifteenth_snapshot_evidence_file_exists_with_the_exact_expected_name",
    )
    expect(
        os.path.exists(os.path.join(tmp_dir, "sfm_scope_guard_run_08_selected_after_restart.txt")),
        "final.eighth_run_evidence_file_exists_with_the_exact_expected_name",
    )
    with open(os.path.join(tmp_dir, "sfm_scope_guard_final_result.json"), "rb") as f:
        final_rollup = json.loads(f.read().decode("utf-8"))
    expect(
        len(final_rollup["captured_snapshots"]) == 15 and len(final_rollup["captured_runs"]) == 8,
        "final.rollup_indexes_all_fifteen_snapshots_and_all_eight_runs_exactly",
    )
    expect(
        len(final_rollup["refusal_proofs"]) == 3
        and all(p["equal"] is True for p in final_rollup["refusal_proofs"]),
        "final.rollup_carries_all_three_refusal_proofs_all_equal_true",
    )
    # No evidence file was ever silently overwritten across the whole
    # 15-snapshot / 8-run walkthrough: every snapshot/run filename in the
    # final index must be unique.
    all_snapshot_filenames = [s["filename"] for s in final_rollup["captured_snapshots"]]
    all_run_filenames = [r["filename"] for r in final_rollup["captured_runs"]]
    expect(
        len(all_snapshot_filenames) == len(set(all_snapshot_filenames)),
        "final.all_fifteen_snapshot_filenames_are_unique",
    )
    expect(
        len(all_run_filenames) == len(set(all_run_filenames)),
        "final.all_eight_run_filenames_are_unique",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))

if FAIL_COUNT[0]:
    sys.exit(1)
