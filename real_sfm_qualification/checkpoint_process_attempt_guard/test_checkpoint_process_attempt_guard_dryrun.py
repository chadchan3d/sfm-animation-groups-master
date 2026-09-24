# -*- coding: utf-8 -*-
"""
Offline dry-run for Checkpoint_Process_Attempt_Guard_Qualification.py
itself (the read-only real-SFM snapshot utility, not the production
guard -- see test_process_attempt_guard_regression.py for that).

Proves, under the real embedded Python 2.7.5 with a fake sfmApp and a
real QtCore.QObject main_window, that this checkpoint script:
  - never references production's own trailing
    StartRebuildControlGroups() invocation, its scope-dialog machinery,
    or any substantial-traversal/native-work identifier anywhere in its
    own source (the one thing this script must never do, since it is
    meant to be pure read-only observation);
  - correctly extracts, by exact pinned line range, and calls the real,
    guard-added _find_process_attempt_marker / _find_existing_run from
    the pinned production candidate's own source, without exec'ing
    production's own module body (which performs real `import sfmApp` /
    `import sfmClipEditor` / `import vs` statements that only succeed
    inside a real running SFM process);
  - produces a snapshot whose fields match what a truly fresh process
    (no marker, no run lock) should report;
  - persists and re-reads state via its own atomic-write helpers.

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
EXPECTED_PRODUCTION_SHA256 = "6170d2a248845281b5f5d38dfea4b9f2decf908b8e3b79e80f4ada18d2f54625"

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
# Kept as a plain byte str (not decoded to unicode) for compile() --
# Python 2 rejects a "# -*- coding: -*-" declaration inside a unicode
# string passed to compile(), but accepts it fine in a byte str, which
# is how the interpreter would normally load this file from disk anyway.
checkpoint_text = checkpoint_bytes

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


tmp_dir = tempfile.mkdtemp(prefix="process_attempt_guard_checkpoint_dryrun_")
try:
    ns = {
        "sfmApp": _FakeSfmApp(_FakeMainWindow()),
        "QtCore": QtCore,
    }
    exec(compile(definitions_only_text, "<checkpoint_defs>", "exec"), ns)

    # Point the extracted definitions at the pinned production candidate
    # (the repo's own guard-added file) and a scratch state/result/
    # summary location, instead of the real live-install/Public
    # Documents paths, for a fully offline, side-effect-contained dry run.
    ns["PRODUCTION_INSTALLED_PATH"] = PRODUCTION_CANDIDATE_PATH
    ns["EXPECTED_PRODUCTION_SHA256"] = EXPECTED_PRODUCTION_SHA256
    ns["STATE_PATH"] = os.path.join(tmp_dir, "state.json")
    ns["RESULT_PATH"] = os.path.join(tmp_dir, "result.json")
    ns["SUMMARY_PATH"] = os.path.join(tmp_dir, "summary.txt")

    load_production_definitions = ns["load_production_definitions"]
    take_snapshot = ns["take_snapshot"]
    read_state = ns["read_state"]
    write_json_atomic = ns["write_json_atomic"]

    prod_ns, prod_sha256, prod_text = load_production_definitions()
    expect(
        prod_sha256 == EXPECTED_PRODUCTION_SHA256,
        "load_production_definitions.reads_and_hashes_the_pinned_candidate_correctly",
    )
    expect(
        "_find_process_attempt_marker" in prod_ns
        and "_find_existing_run" in prod_ns
        and "OUTPUT_PATH" in prod_ns
        and "RUN_LOCK_NAME" in prod_ns
        and "NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME" in prod_ns
        and "NormalizerProcessAttemptMarkerError" in prod_ns
        and "to_unicode" in prod_ns,
        "load_production_definitions.extracts_all_seven_expected_real_definitions",
    )
    expect(
        "sfmApp" not in prod_ns
        and "sfmClipEditor" not in prod_ns
        and "vs" not in prod_ns,
        "load_production_definitions.never_imports_the_real_SFM_only_modules",
    )

    snapshot = take_snapshot()
    expect(
        snapshot["main_window_available"] is True,
        "take_snapshot.reports_main_window_available",
    )
    expect(
        snapshot["production_sha256_matches_expected"] is True,
        "take_snapshot.confirms_pinned_production_sha256",
    )
    expect(
        snapshot["process_attempt_marker_present"] is False,
        "take_snapshot.fresh_QObject_main_window_has_no_marker",
    )
    expect(
        snapshot["run_lock_present"] is False,
        "take_snapshot.fresh_QObject_main_window_has_no_run_lock",
    )
    expect(
        snapshot["marker_name_observed"]
        == u"__SFM_REBUILD_CONTROL_GROUPS_PROCESS_ATTEMPT_CONSUMED__",
        "take_snapshot.observes_the_real_marker_name_from_production",
    )

    main_fn = ns["main"]
    main_fn()
    persisted_state = read_state()
    expect(
        len(persisted_state["snapshots"]) == 1
        and persisted_state["snapshots"][0]["snapshot_index"] == 1,
        "main.persists_exactly_one_auto_numbered_snapshot_on_first_run",
    )
    expect(
        os.path.exists(ns["RESULT_PATH"]) and os.path.exists(ns["SUMMARY_PATH"]),
        "main.writes_result_and_summary_files",
    )

    main_fn()
    persisted_state_2 = read_state()
    expect(
        len(persisted_state_2["snapshots"]) == 2
        and persisted_state_2["snapshots"][1]["snapshot_index"] == 2,
        "main.second_run_appends_snapshot_index_two_never_overwrites_history",
    )
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))

if FAIL_COUNT[0]:
    sys.exit(1)
