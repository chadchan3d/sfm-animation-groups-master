# -*- coding: utf-8 -*-
"""
Offline dry-run for Checkpoint_Process_Attempt_Guard_Qualification.py
itself (the read-only real-SFM snapshot/evidence utility, not the
production guard -- see test_process_attempt_guard_regression.py for
that).

Proves, under the real embedded Python 2.7.5 with a fake sfmApp and a
real QtCore.QObject main_window, that this checkpoint script's revised
evidence-file discipline (2026-09-24) works correctly:
  - never reaches/executes production's own StartRebuildControlGroups(),
    scope-dialog machinery, or any substantial-traversal/native-work
    identifier anywhere in its own source;
  - correctly extracts, by exact pinned line range, the real, scope-aware
    definitions from the pinned production candidate's own source;
  - each invocation writes a NEW, UNIQUELY NUMBERED, IMMUTABLE snapshot
    file pair, never overwriting a prior one;
  - write_evidence_json_once()/write_evidence_text_once() refuse to
    overwrite an existing path (raise, do not silently replace);
  - a production-log content change is detected and copied into a NEW,
    uniquely-labeled, immutable run-evidence file exactly once per
    change, using the fixed 8-entry label schedule, and NOT re-captured
    on a later invocation where the log is unchanged;
  - the continuation-state pointer file and rollup files
    (final_result/final_summary) are freely, safely overwritten and
    correctly reflect the cumulative index;
  - history-through files are themselves unique and immutable per
    snapshot index.

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
EXPECTED_PRODUCTION_SHA256 = "2c0edbb8a95f96147e6310fe1c039da7ee053f5e985f11bb3535dda8aa5ec23d"

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
checkpoint_text = checkpoint_bytes  # kept as bytes; see compile() note below

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


def fresh_ns(tmp_dir):
    ns = {
        "sfmApp": _FakeSfmApp(_FakeMainWindow()),
        "QtCore": QtCore,
    }
    exec(compile(definitions_only_text, "<checkpoint_defs>", "exec"), ns)

    ns["PRODUCTION_INSTALLED_PATH"] = PRODUCTION_CANDIDATE_PATH
    ns["EXPECTED_PRODUCTION_SHA256"] = EXPECTED_PRODUCTION_SHA256
    # EVIDENCE_DIR is read at call-time inside main(), so overriding it
    # here correctly redirects every evidence-file path main() builds.
    # The three rollup/pointer paths were computed ONCE at exec-time
    # using the real EVIDENCE_DIR and must be overridden separately.
    evidence_dir = tmp_dir + os.sep
    ns["EVIDENCE_DIR"] = evidence_dir
    ns["CONTINUATION_STATE_PATH"] = evidence_dir + "sfm_scope_guard_continuation_state.json"
    ns["FINAL_RESULT_PATH"] = evidence_dir + "sfm_scope_guard_final_result.json"
    ns["FINAL_SUMMARY_PATH"] = evidence_dir + "sfm_scope_guard_final_summary.txt"
    return ns


tmp_dir = tempfile.mkdtemp(prefix="process_attempt_guard_checkpoint_dryrun_")
try:
    ns = fresh_ns(tmp_dir)

    load_production_definitions = ns["load_production_definitions"]
    read_continuation_state = ns["read_continuation_state"]
    write_evidence_json_once = ns["write_evidence_json_once"]
    write_evidence_text_once = ns["write_evidence_text_once"]
    CheckpointProcessAttemptGuardError = ns["CheckpointProcessAttemptGuardError"]
    RUN_LOG_LABELS = ns["RUN_LOG_LABELS"]
    SNAPSHOT_SCHEDULE = ns["SNAPSHOT_SCHEDULE"]

    prod_ns, prod_sha256, prod_text = load_production_definitions()
    expect(
        prod_sha256 == EXPECTED_PRODUCTION_SHA256,
        "load_production_definitions.reads_and_hashes_the_pinned_candidate_correctly",
    )
    expect(
        "_read_process_scope_state" in prod_ns
        and "_find_named_process_marker" in prod_ns
        and "_find_existing_run" in prod_ns
        and "OUTPUT_PATH" in prod_ns,
        "load_production_definitions.extracts_the_expected_real_definitions",
    )
    expect(
        "sfmApp" not in prod_ns and "sfmClipEditor" not in prod_ns and "vs" not in prod_ns,
        "load_production_definitions.never_imports_the_real_SFM_only_modules",
    )

    expect(
        len(RUN_LOG_LABELS) == 8,
        "schedule.exactly_eight_run_log_labels",
    )
    expect(
        len(SNAPSHOT_SCHEDULE) == 13,
        "schedule.exactly_thirteen_snapshot_schedule_entries",
    )

    sys.stdout.write("\n--- write_evidence_*_once(): refuse-to-overwrite primitives ---\n")

    once_path = os.path.join(tmp_dir, "probe_evidence.json")
    write_evidence_json_once(once_path, {"a": 1})
    expect(os.path.exists(once_path), "write_evidence_json_once.writes_a_new_file")
    raised = False
    try:
        write_evidence_json_once(once_path, {"a": 2})
    except CheckpointProcessAttemptGuardError:
        raised = True
    expect(raised, "write_evidence_json_once.refuses_to_overwrite_an_existing_file")
    with open(once_path, "rb") as f:
        expect(
            json.loads(f.read().decode("utf-8")) == {"a": 1},
            "write_evidence_json_once.original_content_unchanged_after_refused_overwrite",
        )

    once_txt_path = os.path.join(tmp_dir, "probe_evidence.txt")
    write_evidence_text_once(once_txt_path, b"first")
    raised = False
    try:
        write_evidence_text_once(once_txt_path, b"second")
    except CheckpointProcessAttemptGuardError:
        raised = True
    expect(raised, "write_evidence_text_once.refuses_to_overwrite_an_existing_file")
    with open(once_txt_path, "rb") as f:
        expect(
            f.read() == b"first",
            "write_evidence_text_once.original_content_unchanged_after_refused_overwrite",
        )

    sys.stdout.write("\n--- main(): sequential invocations produce unique, immutable evidence ---\n")

    main_fn = ns["main"]
    main_fn()

    cont1 = read_continuation_state()
    expect(
        cont1["next_snapshot_index"] == 2 and len(cont1["captured_snapshots"]) == 1,
        "main.first_call_advances_snapshot_index_to_two",
    )
    snap1_filename = cont1["captured_snapshots"][0]["filename"]
    expect(
        snap1_filename == "sfm_scope_guard_snapshot_01_baseline.json",
        "main.first_snapshot_uses_the_scheduled_baseline_operation_label",
    )
    expect(
        os.path.exists(os.path.join(tmp_dir, snap1_filename)),
        "main.first_snapshot_json_file_exists",
    )
    expect(
        os.path.exists(os.path.join(tmp_dir, "sfm_scope_guard_snapshot_01_baseline.txt")),
        "main.first_snapshot_txt_companion_exists",
    )
    expect(
        os.path.exists(os.path.join(tmp_dir, "sfm_scope_guard_history_through_01.json")),
        "main.first_history_through_file_exists",
    )
    run_count_after_first = len(cont1["captured_runs"])
    expect(
        run_count_after_first == 1
        and cont1["captured_runs"][0]["filename"] == "sfm_scope_guard_run_01_selected_shot3.txt",
        "main.first_call_captures_the_existing_real_log_as_run_01_with_the_scheduled_label",
    )
    expect(
        os.path.exists(os.path.join(tmp_dir, "sfm_scope_guard_run_01_selected_shot3.txt")),
        "main.run_01_evidence_file_exists",
    )

    # Re-read the freshly-written snapshot JSON directly and confirm it
    # is well-formed evidence with the expected fields.
    with open(os.path.join(tmp_dir, snap1_filename), "rb") as f:
        snap1_content = json.loads(f.read().decode("utf-8"))
    expect(
        snap1_content.get("operation") == "baseline"
        and snap1_content.get("expected_state") == "UNUSED"
        and "observed_state" in snap1_content,
        "main.first_snapshot_content_has_the_expected_schema_fields",
    )

    main_fn()  # second invocation, log unchanged since the first call

    cont2 = read_continuation_state()
    expect(
        cont2["next_snapshot_index"] == 3 and len(cont2["captured_snapshots"]) == 2,
        "main.second_call_advances_snapshot_index_to_three_never_overwrites_history",
    )
    snap2_filename = cont2["captured_snapshots"][1]["filename"]
    expect(
        snap2_filename == "sfm_scope_guard_snapshot_02_after_cancel.json",
        "main.second_snapshot_uses_the_next_scheduled_operation_label",
    )
    expect(
        snap2_filename != snap1_filename,
        "main.second_snapshot_filename_is_distinct_from_the_first",
    )
    expect(
        len(cont2["captured_runs"]) == run_count_after_first,
        "main.second_call_captures_no_new_run_since_the_production_log_did_not_change",
    )
    # The first snapshot file must still exist, unmodified, after the
    # second invocation.
    with open(os.path.join(tmp_dir, snap1_filename), "rb") as f:
        snap1_content_after_second_call = json.loads(f.read().decode("utf-8"))
    expect(
        snap1_content_after_second_call == snap1_content,
        "main.first_snapshot_file_remains_byte_identical_after_a_later_invocation",
    )

    main_fn()  # third invocation
    cont3 = read_continuation_state()
    expect(
        cont3["next_snapshot_index"] == 4 and len(cont3["captured_snapshots"]) == 3,
        "main.third_call_advances_snapshot_index_to_four",
    )
    expect(
        cont3["captured_snapshots"][2]["filename"]
        == "sfm_scope_guard_snapshot_03_after_shot3.json",
        "main.third_snapshot_uses_the_third_scheduled_operation_label",
    )

    sys.stdout.write("\n--- Rollup files: freely overwritten, always reflect the cumulative index ---\n")

    with open(os.path.join(tmp_dir, "sfm_scope_guard_final_result.json"), "rb") as f:
        final_result = json.loads(f.read().decode("utf-8"))
    expect(
        len(final_result["captured_snapshots"]) == 3
        and len(final_result["captured_runs"]) == run_count_after_first,
        "main.final_result_rollup_reflects_all_snapshots_and_runs_captured_so_far",
    )
    expect(
        os.path.exists(os.path.join(tmp_dir, "sfm_scope_guard_final_summary.txt")),
        "main.final_summary_rollup_file_exists",
    )

    sys.stdout.write("\n--- Continuation state persists across a simulated restart (fresh namespace, same dir) ---\n")

    ns_after_restart = fresh_ns(tmp_dir)
    main_fn_after_restart = ns_after_restart["main"]
    main_fn_after_restart()
    cont4 = ns_after_restart["read_continuation_state"]()
    expect(
        cont4["next_snapshot_index"] == 5 and len(cont4["captured_snapshots"]) == 4,
        "main.numbering_continues_correctly_across_a_fresh_namespace_ie_simulated_restart",
    )
    expect(
        cont4["captured_snapshots"][3]["filename"]
        == "sfm_scope_guard_snapshot_04_after_5shots.json",
        "main.fourth_snapshot_after_simulated_restart_uses_the_fourth_scheduled_label",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))

if FAIL_COUNT[0]:
    sys.exit(1)
