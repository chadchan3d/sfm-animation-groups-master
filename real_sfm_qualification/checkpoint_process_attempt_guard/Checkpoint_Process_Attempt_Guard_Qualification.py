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

Each run:
  1. Reads the CURRENTLY DEPLOYED production Normalizer script from its
     live install path and extracts ONLY a small, pinned set of pure-
     Python/Qt definitions verbatim, by exact source line range (never
     a whole-file exec(): production's own module body performs real
     `import sfmApp` / `import sfmClipEditor` / `import vs` statements
     that only succeed inside a real running SFM process, and this
     checkpoint never references production's own trailing
     StartRebuildControlGroups() invocation at all, so it can never
     trigger a real run) -- reusing the exact SAME
     _read_process_scope_state / _find_named_process_marker /
     _find_existing_run / marker names / OUTPUT_PATH the real, deployed
     production script uses, so this checkpoint's own read is guaranteed
     to observe production's actual state semantics, never a hand-copied
     approximation that could drift.
  2. Uses those extracted, real functions against the REAL live
     main_window to record the process's own current scope-state
     classification (UNUSED / SELECTED_USED / FULL_SCOPE_STARTED, or an
     explicit unreadable/legacy/conflicting error) and whether the
     temporary run-lock is currently present.
  3. Fingerprints the real production log file (existence/size/mtime/
     sha256) to later prove a refused invocation never truncates it.
  4. Appends one snapshot record (auto-numbered) to a small persisted
     JSON history and rewrites a human-readable summary. Uses lightweight
     counters/logging only -- no whole-session semantic capture, no
     scene/DME traversal of any kind.

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

STATE_PATH = (
    "C:\\Users\\Public\\Documents\\"
    "sfm_checkpoint_process_attempt_guard_state.json"
)
RESULT_PATH = (
    "C:\\Users\\Public\\Documents\\"
    "sfm_checkpoint_process_attempt_guard_result.json"
)
SUMMARY_PATH = (
    "C:\\Users\\Public\\Documents\\"
    "sfm_checkpoint_process_attempt_guard_summary.txt"
)


class CheckpointProcessAttemptGuardError(Exception):
    pass


def write_json_atomic(path, obj):
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


def write_text_atomic(path, text_bytes):
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


def read_state():
    if not os.path.exists(STATE_PATH):
        return {"snapshots": []}
    try:
        fp = open(STATE_PATH, "rb")
        try:
            raw = fp.read()
        finally:
            fp.close()
        parsed = json.loads(raw.decode("utf-8"))
        if not isinstance(parsed, dict) or "snapshots" not in parsed:
            raise CheckpointProcessAttemptGuardError(
                "state file is present but does not contain the "
                "expected 'snapshots' structure -- refusing to guess."
            )
        return parsed
    except CheckpointProcessAttemptGuardError:
        raise
    except Exception as exc:
        raise CheckpointProcessAttemptGuardError(
            "state file is present but could not be read/parsed: %r"
            % (exc,)
        )


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
    }


def take_snapshot():
    snapshot = {
        "wall_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "epoch": time.time(),
        "current_pid": os.getpid(),
    }

    try:
        main_window = sfmApp.GetMainWindow()
    except Exception as exc:
        snapshot["main_window_error"] = u"%r" % (exc,)
        main_window = None

    snapshot["main_window_available"] = main_window is not None

    try:
        ns, production_sha256, production_text = load_production_definitions()
        snapshot["production_sha256"] = production_sha256
        snapshot["production_sha256_matches_expected"] = (
            production_sha256 == EXPECTED_PRODUCTION_SHA256
        )
        snapshot["production_definitions_load_error"] = None
    except Exception as exc:
        snapshot["production_sha256"] = None
        snapshot["production_sha256_matches_expected"] = False
        snapshot["production_definitions_load_error"] = u"%r" % (exc,)
        ns = None

    if ns is not None and main_window is not None:
        NormalizerProcessAttemptMarkerError = ns[
            "NormalizerProcessAttemptMarkerError"
        ]
        try:
            snapshot["process_scope_state"] = ns[
                "_read_process_scope_state"
            ](main_window)
            snapshot["process_scope_state_error"] = None
        except NormalizerProcessAttemptMarkerError as exc:
            snapshot["process_scope_state"] = None
            snapshot["process_scope_state_error"] = u"%r" % (exc,)
        except Exception as exc:
            snapshot["process_scope_state"] = None
            snapshot["process_scope_state_error"] = (
                u"UNEXPECTED: %r" % (exc,)
            )

        try:
            found_run_lock = ns["_find_existing_run"](main_window)
            snapshot["run_lock_present"] = found_run_lock is not None
        except Exception as exc:
            snapshot["run_lock_present"] = None
            snapshot["run_lock_lookup_error"] = u"%r" % (exc,)

        snapshot["selected_used_marker_name_observed"] = ns.get(
            "NORMALIZER_PROCESS_STATE_SELECTED_USED_MARKER_NAME"
        )
        snapshot["full_scope_started_marker_name_observed"] = ns.get(
            "NORMALIZER_PROCESS_STATE_FULL_SCOPE_STARTED_MARKER_NAME"
        )
        snapshot["legacy_marker_name_observed"] = ns.get(
            "NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME_LEGACY"
        )
        snapshot["run_lock_name_observed"] = ns.get("RUN_LOCK_NAME")

        try:
            output_path = ns["OUTPUT_PATH"]
            snapshot["production_log_path"] = output_path
            snapshot["production_log_fingerprint"] = (
                contextualizer_log_fingerprint(output_path)
            )
        except Exception as exc:
            snapshot["production_log_fingerprint_error"] = u"%r" % (exc,)
    else:
        snapshot["process_scope_state"] = None
        snapshot["run_lock_present"] = None

    return snapshot


def main():
    state = read_state()
    snapshot = take_snapshot()
    snapshot["snapshot_index"] = len(state["snapshots"]) + 1
    state["snapshots"].append(snapshot)

    ok, err, _reparsed = write_json_atomic(STATE_PATH, state)
    if not ok:
        raise CheckpointProcessAttemptGuardError(
            "Failed to persist state atomically: %s" % err
        )

    ok2, err2, _reparsed2 = write_json_atomic(
        RESULT_PATH, {"snapshots": state["snapshots"]}
    )
    if not ok2:
        raise CheckpointProcessAttemptGuardError(
            "Failed to write result atomically: %s" % err2
        )

    lines = []
    lines.append(
        "PROCESS SCOPE-STATE GUARD CHECKPOINT -- SNAPSHOT #%d"
        % snapshot["snapshot_index"]
    )
    lines.append("wall_time = %s" % snapshot["wall_time"])
    lines.append("current_pid = %s" % snapshot["current_pid"])
    lines.append(
        "production_sha256_matches_expected = %s"
        % snapshot.get("production_sha256_matches_expected")
    )
    lines.append(
        "process_scope_state = %s"
        % snapshot.get("process_scope_state")
    )
    lines.append(
        "process_scope_state_error = %s"
        % snapshot.get("process_scope_state_error")
    )
    lines.append("run_lock_present = %s" % snapshot.get("run_lock_present"))
    fp_info = snapshot.get("production_log_fingerprint")
    if fp_info:
        lines.append(
            "production_log: exists=%s size_bytes=%s sha256=%s"
            % (
                fp_info.get("exists"),
                fp_info.get("size_bytes"),
                fp_info.get("sha256"),
            )
        )
    lines.append("")
    lines.append(
        "Full snapshot history (%d total):" % len(state["snapshots"])
    )
    for s in state["snapshots"]:
        lines.append(
            "  #%d pid=%s scope_state=%s state_error=%s "
            "run_lock_present=%s log_sha256=%s"
            % (
                s.get("snapshot_index"),
                s.get("current_pid"),
                s.get("process_scope_state"),
                s.get("process_scope_state_error"),
                s.get("run_lock_present"),
                (s.get("production_log_fingerprint") or {}).get("sha256"),
            )
        )

    summary_text = u"\n".join(lines) + u"\n"
    ok3, err3 = write_text_atomic(
        SUMMARY_PATH, summary_text.encode("utf-8")
    )
    if not ok3:
        raise CheckpointProcessAttemptGuardError(
            "Failed to write summary atomically: %s" % err3
        )

    try:
        sys.stdout.write(summary_text)
    except Exception:
        pass


main()
