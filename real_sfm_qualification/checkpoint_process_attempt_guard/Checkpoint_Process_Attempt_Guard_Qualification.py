# -*- coding: utf-8 -*-
"""
Checkpoint: Process-Lifetime Attempt Guard Qualification (real-SFM).

Prepared, per the Astra-authorized implementation contract (2026-09-24),
following F2-R1-R3's real-SFM FAIL result ("LEGITIMATE SAME-PROCESS
REINVOCATION IS NOT RELIABLY SUSTAINABLE"). This script has NOT been run
against real SFM -- it is prepared for the operator to run.

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
     _find_process_attempt_marker / _find_existing_run / marker-name /
     OUTPUT_PATH the real, deployed production script uses, so this
     checkpoint's own read is guaranteed to observe production's actual
     marker semantics, never a hand-copied approximation that could
     drift.
  2. Uses those extracted, real functions against the REAL live
     main_window to record whether the process-attempt marker and the
     temporary run-lock are currently present.
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
    "6170d2a248845281b5f5d38dfea4b9f2decf908b8e3b79e80f4ada18d2f54625"
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
# thousands of unrelated lines just to reach seven small definitions.
RUN_LOCK_NAME_RANGE = (158, 160)
NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME_RANGE = (170, 172)
OUTPUT_PATH_RANGE = (174, 177)
MARKER_ERROR_CLASS_RANGE = (807, 812)
TO_UNICODE_RANGE = (854, 864)
FIND_EXISTING_RUN_RANGE = (5609, 5628)
FIND_PROCESS_ATTEMPT_MARKER_RANGE = (5631, 5662)

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
        NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME_RANGE,
        OUTPUT_PATH_RANGE,
        MARKER_ERROR_CLASS_RANGE,
        TO_UNICODE_RANGE,
        FIND_EXISTING_RUN_RANGE,
        FIND_PROCESS_ATTEMPT_MARKER_RANGE,
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
        "NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME",
        "OUTPUT_PATH",
        "NormalizerProcessAttemptMarkerError",
        "to_unicode",
        "_find_existing_run",
        "_find_process_attempt_marker",
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
        try:
            found_marker = ns["_find_process_attempt_marker"](main_window)
            snapshot["process_attempt_marker_present"] = (
                found_marker is not None
            )
            snapshot["process_attempt_marker_lookup_error"] = None
        except Exception as exc:
            snapshot["process_attempt_marker_present"] = None
            snapshot["process_attempt_marker_lookup_error"] = u"%r" % (exc,)

        try:
            found_run_lock = ns["_find_existing_run"](main_window)
            snapshot["run_lock_present"] = found_run_lock is not None
        except Exception as exc:
            snapshot["run_lock_present"] = None
            snapshot["run_lock_lookup_error"] = u"%r" % (exc,)

        snapshot["marker_name_observed"] = ns.get(
            "NORMALIZER_PROCESS_ATTEMPT_MARKER_NAME"
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
        snapshot["process_attempt_marker_present"] = None
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
        "PROCESS ATTEMPT GUARD CHECKPOINT -- SNAPSHOT #%d"
        % snapshot["snapshot_index"]
    )
    lines.append("wall_time = %s" % snapshot["wall_time"])
    lines.append("current_pid = %s" % snapshot["current_pid"])
    lines.append(
        "production_sha256_matches_expected = %s"
        % snapshot.get("production_sha256_matches_expected")
    )
    lines.append(
        "process_attempt_marker_present = %s"
        % snapshot.get("process_attempt_marker_present")
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
            "  #%d pid=%s marker_present=%s run_lock_present=%s "
            "log_sha256=%s"
            % (
                s.get("snapshot_index"),
                s.get("current_pid"),
                s.get("process_attempt_marker_present"),
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
