# -*- coding: utf-8 -*-
"""
Checkpoint: Process-Lifetime SCOPE-AWARE Admission Guard Qualification
(real-SFM).

Prepared, per the Astra-authorized, subsequently CORRECTED implementation
contract (2026-09-24), following F2-R1-R3's real-SFM FAIL result
("LEGITIMATE SAME-PROCESS REINVOCATION IS NOT RELIABLY SUSTAINABLE"). The
original broad one-attempt-per-process guard (commit
f3efd132ad5456a583df5917ef85576db0690c60) has been SUPERSEDED by a scope-
aware guard: Selected Shot(s) over any proper subset of project shots (1,
2, 5, 10, any number) remains normal, repeatedly-usable functionality
within one process; only a full-scope request (All Shots, or a Selected
Shot(s) request whose resolved shot set exactly equals the complete
project shot set) is gated. **This script has NOT been run against real
SFM** -- it is prepared for the operator to run.

This is a pure READ-ONLY SNAPSHOT UTILITY, not a Normalizer invocation.
It never calls StartRebuildControlGroups(), never opens a scope dialog,
performs zero scene traversal, zero provider/broker acquisition, and zero
native Rebuild work. Every real invocation of the actual "Rebuild Control
Groups" command during this checkpoint's own operator sequence is
performed manually by the operator through the real SFM menu -- this
script only observes and records state before/after each of those real
invocations.

EVIDENCE-FILE DISCIPLINE (2026-09-24 revision): the operator must NEVER
manually rename/copy files between steps, and no evidence file may ever be
overwritten. Every invocation of this script:
  1. Reads the CURRENTLY DEPLOYED production Normalizer script and
     extracts ONLY a small, pinned set of pure-Python/Qt definitions
     verbatim, by exact source line range (never a whole-file exec():
     production's own module body performs real `import sfmApp` /
     `import sfmClipEditor` / `import vs` statements that only succeed
     inside a real running SFM process) -- reusing the exact SAME
     _read_process_scope_state / _find_named_process_marker /
     _find_existing_run / marker names / OUTPUT_PATH the real, deployed
     production script uses.
  2. Captures the process's own current scope-state classification and
     run-lock presence, plus a fingerprint (exists/size/mtime/sha256) of
     the real production log.
  3. Writes this capture to a NEW, UNIQUELY NUMBERED, IMMUTABLE snapshot
     file pair: `sfm_scope_guard_snapshot_NN_<operation>.json` / `.txt`.
     Refuses (raises, does not silently overwrite) if that exact filename
     already exists -- this should never happen given the auto-
     incrementing counter, but is checked explicitly as well as relying
     on Windows' own os.rename() refusing an existing destination.
  4. If the production log's own sha256 differs from the last one this
     checkpoint itself observed (i.e. a new real Normalizer command
     completed since the previous invocation), copies the CURRENT log's
     exact byte content into a NEW, UNIQUELY NAMED, IMMUTABLE preserved-
     log file from a FIXED, PREDETERMINED 8-entry label schedule matching
     INSTRUCTIONS.md's own operator sequence
     (`sfm_scope_guard_run_NN_<label>.txt`) -- the operator never
     manually copies sfm_rebuild_control_groups.txt themselves.
  5. Also writes an immutable, uniquely-numbered cumulative-history
     snapshot (`sfm_scope_guard_history_through_NN.json`) indexing every
     evidence file captured so far.
  6. Updates a small, explicitly non-evidentiary CONTINUATION-STATE
     pointer file (freely overwritten every invocation -- this is
     bookkeeping, not evidence) that carries the next snapshot/run
     ordinal and the last-observed log sha256 across real SFM restarts
     (evidence files themselves already live in a persistent location and
     need no special restart handling).
  7. Rewrites `sfm_scope_guard_final_result.json` / `_final_summary.txt`
     -- a freely-overwritten ROLLUP/INDEX (not itself evidence; the
     individual snapshot/run files are the evidence) of every unique
     snapshot and preserved log captured so far, each with filename,
     SHA-256, step/ordinal, PID, wall time, operation/scope, expected
     state, and observed state. By the operator's final invocation this
     is the complete, correct final index.

See INSTRUCTIONS.md for exactly when to run this script relative to the
operator's own manual, real "Rebuild Control Groups" invocations.
"""
import hashlib
import json
import os
import sys
import time

from PySide import QtCore

PRODUCTION_INSTALLED_PATH = (
    "E:\\SteamLibrary\\steamapps\\common\\SourceFilmmaker\\game\\usermod"
    "\\scripts\\sfm\\mainmenu\\ChadChan3D\\Rebuild_Control_Groups_Normalizer.py"
)
EXPECTED_PRODUCTION_SHA256 = (
    "2c0edbb8a95f96147e6310fe1c039da7ee053f5e985f11bb3535dda8aa5ec23d"
)

# Exact source line ranges (1-indexed, inclusive) for the small handful
# of pure-Python/Qt definitions this checkpoint needs from production --
# verified directly against the pinned SHA-256 above via grep/Read
# immediately before writing this script. Deliberately NOT a whole-file
# exec(): production's own module body does `import sfmApp`,
# `import sfmClipEditor`, `import vs` as real import statements (not
# merely referencing pre-seeded globals), which only succeed inside a
# real running SFM process -- exec'ing the whole file would make this
# checkpoint's own logic untestable offline and would needlessly exec
# thousands of unrelated lines just to reach a handful of definitions.
RUN_LOCK_NAME_RANGE = (158, 160)
CONSTANTS_MARKER_NAMES_RANGE = (196, 212)
OUTPUT_PATH_RANGE = (214, 217)
MARKER_ERROR_CLASS_RANGE = (847, 857)
TO_UNICODE_RANGE = (899, 909)
FIND_EXISTING_RUN_RANGE = (5654, 5673)
FIND_NAMED_MARKER_RANGE = (5676, 5718)
PROCESS_STATE_CONSTANTS_RANGE = (5775, 5780)
READ_PROCESS_SCOPE_STATE_RANGE = (5783, 5825)

EVIDENCE_DIR = "C:\\Users\\Public\\Documents\\"

# Explicitly NON-EVIDENTIARY operational bookkeeping -- freely
# overwritten every invocation. Carries checkpoint numbering and the
# last-observed production-log sha256 across real SFM restarts.
CONTINUATION_STATE_PATH = EVIDENCE_DIR + "sfm_scope_guard_continuation_state.json"

# Freely-overwritten ROLLUP/INDEX of the evidence captured so far -- not
# itself evidence (the individual snapshot/run files are).
FINAL_RESULT_PATH = EVIDENCE_DIR + "sfm_scope_guard_final_result.json"
FINAL_SUMMARY_PATH = EVIDENCE_DIR + "sfm_scope_guard_final_summary.txt"

# Fixed, predetermined label schedule for the 8 real Normalizer commands
# INSTRUCTIONS.md's own operator sequence expects, in order. A production-
# log sha256 change beyond this many entries raises rather than guessing
# a label.
RUN_LOG_LABELS = [
    u"selected_shot3",
    u"selected_5shots",
    u"selected_3shots",
    u"selected_edit_repair",
    u"selected_after_all_refusal",
    u"selected_after_reopen",
    u"all_shots",
    u"selected_after_restart",
]

# Fixed, predetermined operation label and expected process_scope_state
# for each of INSTRUCTIONS.md's own 13 snapshot points, in order. Purely
# descriptive/expectation metadata for the rollup index -- never used to
# alter what is actually observed and recorded.
SNAPSHOT_SCHEDULE = [
    (u"baseline", u"UNUSED"),
    (u"after_cancel", u"UNUSED"),
    (u"after_shot3", u"SELECTED_USED"),
    (u"after_5shots", u"SELECTED_USED"),
    (u"after_3shots", u"SELECTED_USED"),
    (u"after_edit_repair", u"SELECTED_USED"),
    (u"after_post_refusal_selected", u"SELECTED_USED"),
    (u"after_reopen_selected", u"SELECTED_USED"),
    (u"fresh_after_restart", u"UNUSED"),
    (u"after_all_shots", u"FULL_SCOPE_STARTED"),
    (u"after_refusals", u"FULL_SCOPE_STARTED"),
    (u"reset_after_restart", u"UNUSED"),
    (u"final_after_restart_selected", u"SELECTED_USED"),
]


class CheckpointProcessAttemptGuardError(Exception):
    pass


def write_json_rollup(path, obj):
    # Freely overwritten -- for CONTINUATION_STATE_PATH / FINAL_RESULT_PATH
    # only. Never used for evidence files.
    tmp_path = path + ".tmp"
    try:
        text = json.dumps(obj, indent=2, sort_keys=True)
        fp = open(tmp_path, "wb")
        try:
            fp.write(text.encode("utf-8"))
            fp.flush()
            os.fsync(fp.fileno())
        finally:
            fp.close()

        fp2 = open(tmp_path, "rb")
        try:
            reparsed = json.loads(fp2.read().decode("utf-8"))
        finally:
            fp2.close()

        if os.path.exists(path):
            os.remove(path)
        os.rename(tmp_path, path)
        return True, None, reparsed
    except Exception as exc:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return False, u"%r" % (exc,), None


def write_text_rollup(path, text_bytes):
    # Freely overwritten -- for FINAL_SUMMARY_PATH only.
    tmp_path = path + ".tmp"
    try:
        fp = open(tmp_path, "wb")
        try:
            fp.write(text_bytes)
            fp.flush()
            os.fsync(fp.fileno())
        finally:
            fp.close()
        if os.path.exists(path):
            os.remove(path)
        os.rename(tmp_path, path)
        return True, None
    except Exception as exc:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return False, u"%r" % (exc,)


def write_evidence_json_once(path, obj):
    # EVIDENCE. Refuses to overwrite: raises if the target already
    # exists, both via an explicit upfront check (for a clear error
    # message) and by relying on Windows' own os.rename() refusing an
    # existing destination (unlike POSIX rename, which silently
    # replaces) as a second, race-safe guarantee.
    if os.path.exists(path):
        raise CheckpointProcessAttemptGuardError(
            "Refusing to overwrite existing evidence file: %r" % (path,)
        )

    tmp_path = path + ".tmp"
    text = json.dumps(obj, indent=2, sort_keys=True)
    fp = open(tmp_path, "wb")
    try:
        fp.write(text.encode("utf-8"))
        fp.flush()
        os.fsync(fp.fileno())
    finally:
        fp.close()

    fp2 = open(tmp_path, "rb")
    try:
        reparsed = json.loads(fp2.read().decode("utf-8"))
    finally:
        fp2.close()

    try:
        os.rename(tmp_path, path)
    except Exception as exc:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise CheckpointProcessAttemptGuardError(
            "Refusing to overwrite existing evidence file (rename "
            "failed, target likely already exists): %r (%r)"
            % (path, exc)
        )

    return reparsed


def write_evidence_text_once(path, text_bytes):
    # EVIDENCE. Same refuse-to-overwrite discipline as
    # write_evidence_json_once().
    if os.path.exists(path):
        raise CheckpointProcessAttemptGuardError(
            "Refusing to overwrite existing evidence file: %r" % (path,)
        )

    tmp_path = path + ".tmp"
    fp = open(tmp_path, "wb")
    try:
        fp.write(text_bytes)
        fp.flush()
        os.fsync(fp.fileno())
    finally:
        fp.close()

    try:
        os.rename(tmp_path, path)
    except Exception as exc:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise CheckpointProcessAttemptGuardError(
            "Refusing to overwrite existing evidence file (rename "
            "failed, target likely already exists): %r (%r)"
            % (path, exc)
        )


def read_continuation_state():
    # NON-EVIDENTIARY bookkeeping only.
    if not os.path.exists(CONTINUATION_STATE_PATH):
        return {
            "next_snapshot_index": 1,
            "next_run_index": 1,
            "last_known_log_sha256": None,
            "captured_snapshots": [],
            "captured_runs": [],
        }
    fp = open(CONTINUATION_STATE_PATH, "rb")
    try:
        raw = fp.read()
    finally:
        fp.close()
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise CheckpointProcessAttemptGuardError(
            "continuation-state file is present but could not be "
            "parsed: %r -- refusing to guess." % (exc,)
        )
    for required_key in (
        "next_snapshot_index",
        "next_run_index",
        "last_known_log_sha256",
        "captured_snapshots",
        "captured_runs",
    ):
        if required_key not in parsed:
            raise CheckpointProcessAttemptGuardError(
                "continuation-state file is present but missing "
                "expected key %r -- refusing to guess." % (required_key,)
            )
    return parsed


def _extract_lines(raw_bytes, range_tuple):
    start, end = range_tuple
    # Kept as a plain byte str (not decoded to unicode) for compile() --
    # this never includes production's own line-1 "# -*- coding: -*-"
    # declaration (every extracted range starts well past it), so this
    # is purely a byte-string slice/join, matching this project's own
    # established verbatim-extraction convention used by every other
    # checkpoint's offline test.
    lines = raw_bytes.split("\n")
    return "\n".join(lines[start - 1:end])


def load_production_definitions():
    """Reads the currently-deployed production Normalizer and extracts
    ONLY the small set of pure-Python/Qt definitions this checkpoint
    needs, verbatim, by exact source line range -- never a whole-file
    exec() (production's own module body performs real `import sfmApp` /
    `import sfmClipEditor` / `import vs` statements that only succeed
    inside a real running SFM process, and never references its own
    trailing StartRebuildControlGroups() invocation at all, so this
    checkpoint can never trigger a real run). Returns
    (namespace, sha256, raw_text)."""
    fp = open(PRODUCTION_INSTALLED_PATH, "rb")
    try:
        raw_bytes = fp.read()
    finally:
        fp.close()

    sha256 = hashlib.sha256(raw_bytes).hexdigest()

    ns = {"QtCore": QtCore}
    for range_tuple in (
        RUN_LOCK_NAME_RANGE,
        CONSTANTS_MARKER_NAMES_RANGE,
        OUTPUT_PATH_RANGE,
        MARKER_ERROR_CLASS_RANGE,
        TO_UNICODE_RANGE,
        FIND_EXISTING_RUN_RANGE,
        FIND_NAMED_MARKER_RANGE,
        PROCESS_STATE_CONSTANTS_RANGE,
        READ_PROCESS_SCOPE_STATE_RANGE,
    ):
        exec(
            compile(
                _extract_lines(raw_bytes, range_tuple),
                "<production_definitions_readonly>",
                "exec",
            ),
            ns,
        )

    for required_name in (
        "RUN_LOCK_NAME",
        "NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME",
        "NORMALIZER_PROCESS_STATE_FULL_SCOPE_STARTED_MARKER_NAME",
        "NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME_LEGACY",
        "OUTPUT_PATH",
        "NormalizerProcessAttemptMarkerError",
        "to_unicode",
        "_find_existing_run",
        "_find_named_process_marker",
        "PROCESS_SCOPE_STATE_UNUSED",
        "PROCESS_SCOPE_STATE_SELECTED_USED",
        "PROCESS_SCOPE_STATE_FULL_SCOPE_STARTED",
        "_read_process_scope_state",
    ):
        if required_name not in ns:
            raise CheckpointProcessAttemptGuardError(
                "Extraction did not produce the expected definition "
                "%r -- the pinned line ranges may be stale for this "
                "production script version; refusing to proceed rather "
                "than guess." % (required_name,)
            )

    return ns, sha256, raw_bytes.decode("utf-8")


def contextualizer_log_fingerprint(output_path):
    if not os.path.exists(output_path):
        return {
            "exists": False,
            "size_bytes": None,
            "mtime": None,
            "sha256": None,
            "raw_bytes": None,
        }
    fp = open(output_path, "rb")
    try:
        raw = fp.read()
    finally:
        fp.close()
    st = os.stat(output_path)
    return {
        "exists": True,
        "size_bytes": len(raw),
        "mtime": st.st_mtime,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "raw_bytes": raw,
    }


def capture_current_state():
    state = {
        "wall_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "epoch": time.time(),
        "current_pid": os.getpid(),
    }

    try:
        main_window = sfmApp.GetMainWindow()
    except Exception as exc:
        state["main_window_error"] = u"%r" % (exc,)
        main_window = None

    state["main_window_available"] = main_window is not None

    try:
        ns, production_sha256, production_text = load_production_definitions()
        state["production_sha256"] = production_sha256
        state["production_sha256_matches_expected"] = (
            production_sha256 == EXPECTED_PRODUCTION_SHA256
        )
        state["production_definitions_load_error"] = None
    except Exception as exc:
        state["production_sha256"] = None
        state["production_sha256_matches_expected"] = False
        state["production_definitions_load_error"] = u"%r" % (exc,)
        ns = None

    log_fingerprint = None

    if ns is not None and main_window is not None:
        NormalizerProcessAttemptMarkerError = ns[
            "NormalizerProcessAttemptMarkerError"
        ]
        try:
            state["process_scope_state"] = ns[
                "_read_process_scope_state"
            ](main_window)
            state["process_scope_state_error"] = None
        except NormalizerProcessAttemptMarkerError as exc:
            state["process_scope_state"] = None
            state["process_scope_state_error"] = u"%r" % (exc,)
        except Exception as exc:
            state["process_scope_state"] = None
            state["process_scope_state_error"] = (
                u"UNEXPECTED: %r" % (exc,)
            )

        try:
            found_run_lock = ns["_find_existing_run"](main_window)
            state["run_lock_present"] = found_run_lock is not None
        except Exception as exc:
            state["run_lock_present"] = None
            state["run_lock_lookup_error"] = u"%r" % (exc,)

        state["selected_used_marker_name_observed"] = ns.get(
            "NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME"
        )
        state["full_scope_started_marker_name_observed"] = ns.get(
            "NORMALIZER_PROCESS_STATE_FULL_SCOPE_STARTED_MARKER_NAME"
        )
        state["legacy_marker_name_observed"] = ns.get(
            "NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME_LEGACY"
        )
        state["run_lock_name_observed"] = ns.get("RUN_LOCK_NAME")

        try:
            output_path = ns["OUTPUT_PATH"]
            state["production_log_path"] = output_path
            log_fingerprint = contextualizer_log_fingerprint(output_path)
            state["production_log_fingerprint"] = {
                "exists": log_fingerprint["exists"],
                "size_bytes": log_fingerprint["size_bytes"],
                "mtime": log_fingerprint["mtime"],
                "sha256": log_fingerprint["sha256"],
            }
        except Exception as exc:
            state["production_log_fingerprint_error"] = u"%r" % (exc,)
    else:
        state["process_scope_state"] = None
        state["run_lock_present"] = None

    return state, log_fingerprint


def main():
    cont = read_continuation_state()
    current, log_fingerprint = capture_current_state()

    snapshot_index = cont["next_snapshot_index"]
    if snapshot_index - 1 < len(SNAPSHOT_SCHEDULE):
        operation_label, expected_state = SNAPSHOT_SCHEDULE[snapshot_index - 1]
    else:
        operation_label, expected_state = u"unscheduled_extra_snapshot", None

    run_capture_record = None

    if (
        log_fingerprint is not None
        and log_fingerprint["exists"]
        and log_fingerprint["sha256"] != cont["last_known_log_sha256"]
    ):
        run_index = cont["next_run_index"]
        if run_index > len(RUN_LOG_LABELS):
            raise CheckpointProcessAttemptGuardError(
                "Detected a production-log change beyond the fixed "
                "%d-entry run-evidence schedule (run_index=%d) -- "
                "refusing to guess a label. Check INSTRUCTIONS.md's "
                "own operator sequence for a mismatch."
                % (len(RUN_LOG_LABELS), run_index)
            )
        run_label = RUN_LOG_LABELS[run_index - 1]
        run_filename = "sfm_scope_guard_run_%02d_%s.txt" % (run_index, run_label)
        run_path = EVIDENCE_DIR + run_filename

        write_evidence_text_once(run_path, log_fingerprint["raw_bytes"])

        run_capture_record = {
            "filename": run_filename,
            "sha256": log_fingerprint["sha256"],
            "size_bytes": log_fingerprint["size_bytes"],
            "step_ordinal": run_index,
            "label": run_label,
            "pid": current["current_pid"],
            "wall_time": current["wall_time"],
            "captured_at_snapshot_index": snapshot_index,
        }
        cont["captured_runs"].append(run_capture_record)
        cont["next_run_index"] = run_index + 1
        cont["last_known_log_sha256"] = log_fingerprint["sha256"]

    snapshot_record = dict(current)
    snapshot_record["snapshot_index"] = snapshot_index
    snapshot_record["operation"] = operation_label
    snapshot_record["expected_state"] = expected_state
    snapshot_record["observed_state"] = current.get("process_scope_state")
    snapshot_record["run_captured"] = run_capture_record

    snapshot_json_filename = "sfm_scope_guard_snapshot_%02d_%s.json" % (
        snapshot_index,
        operation_label,
    )
    snapshot_txt_filename = "sfm_scope_guard_snapshot_%02d_%s.txt" % (
        snapshot_index,
        operation_label,
    )
    snapshot_json_path = EVIDENCE_DIR + snapshot_json_filename
    snapshot_txt_path = EVIDENCE_DIR + snapshot_txt_filename

    write_evidence_json_once(snapshot_json_path, snapshot_record)

    snapshot_txt_lines = [
        u"PROCESS SCOPE-STATE GUARD CHECKPOINT -- SNAPSHOT #%02d (%s)"
        % (snapshot_index, operation_label),
        u"wall_time = %s" % snapshot_record["wall_time"],
        u"current_pid = %s" % snapshot_record["current_pid"],
        u"production_sha256_matches_expected = %s"
        % snapshot_record.get("production_sha256_matches_expected"),
        u"expected_state = %s" % expected_state,
        u"observed_state = %s" % snapshot_record["observed_state"],
        u"process_scope_state_error = %s"
        % snapshot_record.get("process_scope_state_error"),
        u"run_lock_present = %s" % snapshot_record.get("run_lock_present"),
    ]
    fp_info = snapshot_record.get("production_log_fingerprint")
    if fp_info:
        snapshot_txt_lines.append(
            u"production_log: exists=%s size_bytes=%s sha256=%s"
            % (fp_info.get("exists"), fp_info.get("size_bytes"), fp_info.get("sha256"))
        )
    if run_capture_record:
        snapshot_txt_lines.append(
            u"run_captured: %s (sha256=%s)"
            % (run_capture_record["filename"], run_capture_record["sha256"])
        )
    else:
        snapshot_txt_lines.append(u"run_captured: none (production log unchanged)")

    write_evidence_text_once(
        snapshot_txt_path,
        (u"\n".join(snapshot_txt_lines) + u"\n").encode("utf-8"),
    )

    cont["captured_snapshots"].append(
        {
            "filename": snapshot_json_filename,
            "step_ordinal": snapshot_index,
            "pid": snapshot_record["current_pid"],
            "wall_time": snapshot_record["wall_time"],
            "operation": operation_label,
            "expected_state": expected_state,
            "observed_state": snapshot_record["observed_state"],
        }
    )
    cont["next_snapshot_index"] = snapshot_index + 1

    ok_cont, err_cont, _r = write_json_rollup(CONTINUATION_STATE_PATH, cont)
    if not ok_cont:
        raise CheckpointProcessAttemptGuardError(
            "Failed to persist continuation-state atomically: %s" % err_cont
        )

    history_index = {
        "captured_snapshots": cont["captured_snapshots"],
        "captured_runs": cont["captured_runs"],
    }
    history_path = EVIDENCE_DIR + (
        "sfm_scope_guard_history_through_%02d.json" % snapshot_index
    )
    write_evidence_json_once(history_path, history_index)

    ok_final, err_final, _r2 = write_json_rollup(FINAL_RESULT_PATH, history_index)
    if not ok_final:
        raise CheckpointProcessAttemptGuardError(
            "Failed to write final-result rollup atomically: %s" % err_final
        )

    summary_lines = [
        u"SCOPE-AWARE GUARD CHECKPOINT -- ROLLUP THROUGH SNAPSHOT #%02d"
        % snapshot_index,
        u"",
        u"Snapshots (%d total):" % len(cont["captured_snapshots"]),
    ]
    for s in cont["captured_snapshots"]:
        summary_lines.append(
            u"  #%02d [%s] pid=%s expected=%s observed=%s -> %s"
            % (
                s["step_ordinal"],
                s["operation"],
                s["pid"],
                s["expected_state"],
                s["observed_state"],
                s["filename"],
            )
        )
    summary_lines.append(u"")
    summary_lines.append(u"Preserved production-log runs (%d total):" % len(cont["captured_runs"]))
    for r in cont["captured_runs"]:
        summary_lines.append(
            u"  #%02d [%s] sha256=%s -> %s"
            % (r["step_ordinal"], r["label"], r["sha256"], r["filename"])
        )

    summary_text = u"\n".join(summary_lines) + u"\n"
    ok_summary, err_summary = write_text_rollup(
        FINAL_SUMMARY_PATH, summary_text.encode("utf-8")
    )
    if not ok_summary:
        raise CheckpointProcessAttemptGuardError(
            "Failed to write final-summary rollup atomically: %s" % err_summary
        )

    try:
        sys.stdout.write(u"\n".join(snapshot_txt_lines) + u"\n\n" + summary_text)
    except Exception:
        pass


main()
