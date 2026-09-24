# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- F2-R1 Marker Persistence Probe.

RUN TYPE: MAIN MENU SCRIPT, NON-MUTATING, READ-ONLY, TINY.

PURPOSE: F2-R1's own design assumed that a QObject marker parented to
`main_window` (installed in one MAINMENU script invocation) survives
separate, LATER invocations of the same script within one continuous SFM
process, and is absent after a real restart -- exactly the same
cross-invocation-continuity mechanism this project's own `RUN_LOCK_NAME`
technique appears to use. A real F2-R1 run showed a fresh-looking
invocation, 35 minutes after a genuine Stage 1 completion, immediately
reporting `stage1_complete` with no marker found -- and on inspection,
`RUN_LOCK_NAME` has NEVER actually been checked across two SEPARATE
MAINMENU script invocations anywhere in this project; every existing use
checks it only within the SAME invocation's own wait loop, for a
production run started by that SAME exec(). Cross-invocation marker
persistence in this project is therefore an UNPROVEN assumption, not a
reused, already-validated mechanism. This probe tests it directly, in
isolation, with no Normalizer, no scene traversal, and no fixture
dependency.

No production code is invoked. No scene is read or mutated. Negligible
memory. This is a diagnostic, not part of F1 optimization, not part of F2
release qualification -- its ONLY job is to empirically prove or disprove
whether the F2-R1 marker mechanism can work at all.

Three invocations, auto-detected from a tiny persisted state file plus a
live marker scan (same technique as F2-R1 itself, deliberately, so this
probe tests the EXACT mechanism F2-R1 relies on, not a different one):

  Invocation A (fresh SFM process, first run): proves no marker is
    present, installs a durable marker (a QObject child of main_window
    whose objectName encodes this process's own PID), records that PID,
    and returns.

  Invocation B (SAME SFM process, run again without restarting): proves
    the marker installed by A is still present and still encodes A's own
    PID (i.e. this really is the same OS process, not merely the same
    "session" in some looser sense).

  Invocation C (run AFTER a real SFM restart): proves the marker is now
    absent, and that the current process's own PID differs from the PID
    recorded during A -- confirming this genuinely is a fresh process,
    not a scan bug producing a false negative.

OUTPUT: C:\\Users\\Public\\Documents\\sfm_marker_persistence_probe_result.json
        C:\\Users\\Public\\Documents\\sfm_marker_persistence_probe_summary.txt
        C:\\Users\\Public\\Documents\\sfm_marker_persistence_probe_state.json (small, persisted)

Do NOT run another F2-R1 attempt until this probe's own A/B/C sequence has
been run for real and returned a clear PASS or FAIL for marker
persistence.
"""
import json
import os
import sys
import time

from PySide import QtCore

MARKER_NAME_PREFIX = u"F2R1_MARKER_PROBE_INSTALLED_BY_PID_"

STATE_PATH = "C:\\Users\\Public\\Documents\\sfm_marker_persistence_probe_state.json"
RESULT_PATH = "C:\\Users\\Public\\Documents\\sfm_marker_persistence_probe_result.json"
SUMMARY_PATH = "C:\\Users\\Public\\Documents\\sfm_marker_persistence_probe_summary.txt"


class MarkerProbeError(Exception):
    pass


def b_to_unicode(value):
    if isinstance(value, unicode):
        return value
    try:
        return value.decode("utf-8")
    except Exception:
        try:
            return value.decode("latin-1")
        except Exception:
            return unicode(value)


def write_json_atomic(final_path, data_obj):
    tmp_path = final_path + ".tmp"
    try:
        f = open(tmp_path, "wb")
        try:
            json.dump(data_obj, f)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        finally:
            f.close()
        with open(tmp_path, "rb") as f:
            reparsed_obj = json.load(f)
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(tmp_path, final_path)
        return True, None, reparsed_obj
    except Exception as exc:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return False, repr(exc), None


def write_text_atomic(final_path, text_bytes):
    tmp_path = final_path + ".tmp"
    try:
        f = open(tmp_path, "wb")
        try:
            f.write(text_bytes)
            f.flush()
        finally:
            f.close()
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(tmp_path, final_path)
        return True, None
    except Exception as exc:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return False, repr(exc)


def read_state():
    if not os.path.exists(STATE_PATH):
        return None
    try:
        with open(STATE_PATH, "rb") as f:
            return json.load(f)
    except Exception as exc:
        raise MarkerProbeError("State file exists but could not be parsed: %r" % (exc,))


def find_probe_marker(main_window):
    if main_window is None:
        return None
    for child in main_window.findChildren(QtCore.QObject):
        try:
            nm = b_to_unicode(child.objectName())
        except Exception:
            continue
        if nm.startswith(MARKER_NAME_PREFIX):
            return nm
    return None


def install_probe_marker(main_window, pid):
    marker = QtCore.QObject(main_window)
    marker.setObjectName(u"%s%d" % (MARKER_NAME_PREFIX, pid))
    return marker


def extract_pid_from_marker_name(marker_name):
    if marker_name is None or not marker_name.startswith(MARKER_NAME_PREFIX):
        return None
    tail = marker_name[len(MARKER_NAME_PREFIX):]
    try:
        return int(tail)
    except Exception:
        return None


def classify_probe_invocation(state, found_marker_name):
    """Pure decision function (offline-testable)."""
    if state is None:
        if found_marker_name is not None:
            return None, "State absent but a marker was found -- inconsistent, STOP."
        return "A_INSTALL", "No prior state, no marker -- fresh install."
    if found_marker_name is not None:
        return "B_SAME_PROCESS_CHECK", "Prior state exists and the marker is still present."
    return "C_POST_RESTART_CHECK", "Prior state exists but no marker is present -- expected after a real restart."


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

report = {"started_at": time.strftime("%Y-%m-%d %H:%M:%S"), "checks": [], "anomalies": []}


def check(name, condition, detail=None):
    report["checks"].append({"name": name, "pass": bool(condition), "detail": repr(detail) if detail is not None else None})
    try:
        sys.stdout.write("[%s] %s%s\n" % ("PASS" if condition else "FAIL", name, "" if detail is None else " -- %r" % (detail,)))
    except Exception:
        pass


def anomaly(message):
    report["anomalies"].append(message)
    try:
        sys.stdout.write("ANOMALY: %s\n" % message)
    except Exception:
        pass


try:
    main_window = sfmApp.GetMainWindow()
    current_pid = os.getpid()
    state = read_state()
    found_marker_name = find_probe_marker(main_window)
    found_marker_pid = extract_pid_from_marker_name(found_marker_name)

    report["current_pid"] = current_pid
    report["state_before"] = state
    report["found_marker_name"] = found_marker_name
    report["found_marker_pid"] = found_marker_pid

    invocation, reason = classify_probe_invocation(state, found_marker_name)
    report["invocation"] = invocation
    report["reason"] = reason
    check("invocation.classified", invocation is not None, invocation)
    if invocation is None:
        raise MarkerProbeError(reason)

    sys.stdout.write("Marker probe invocation: %s (%s), current_pid=%d\n" % (invocation, reason, current_pid))

    if invocation == "A_INSTALL":
        check("A.no_marker_present_before_install", found_marker_name is None, found_marker_name)
        install_probe_marker(main_window, current_pid)
        new_state = {"installed": True, "install_pid": current_pid, "installed_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        ok, err, _r = write_json_atomic(STATE_PATH, new_state)
        check("A.state_persisted", ok, err)

    elif invocation == "B_SAME_PROCESS_CHECK":
        check("B.marker_still_present", found_marker_name is not None, found_marker_name)
        check("B.marker_encodes_the_original_install_pid", found_marker_pid == state.get("install_pid"), (found_marker_pid, state.get("install_pid")))
        check("B.current_pid_matches_original_install_pid", current_pid == state.get("install_pid"), (current_pid, state.get("install_pid")))

    else:  # C_POST_RESTART_CHECK
        check("C.marker_absent_after_restart", found_marker_name is None, found_marker_name)
        check("C.current_pid_differs_from_original_install_pid", current_pid != state.get("install_pid"), (current_pid, state.get("install_pid")))

except MarkerProbeError as exc:
    anomaly("GATE FAILURE: %s" % exc)
except Exception as exc:
    anomaly("UNHANDLED EXCEPTION: %r" % (exc,))
    import traceback
    anomaly(traceback.format_exc())

report["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
report["overall_pass"] = bool(report["checks"]) and all(c["pass"] for c in report["checks"]) and not report["anomalies"]

json_ok, json_err, _r = write_json_atomic(RESULT_PATH, report)

summary_lines = ["SFM MARKER PERSISTENCE PROBE"]
summary_lines.append("invocation=%s  current_pid=%s" % (report.get("invocation"), report.get("current_pid")))
summary_lines.append("")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
summary_lines.append("OVERALL_PASS=%r" % report["overall_pass"])
summary_lines.append("")
summary_lines.append("--- ANOMALIES (%d) ---" % len(report["anomalies"]))
for a in report["anomalies"]:
    summary_lines.append("- %s" % a)
if not report["anomalies"]:
    summary_lines.append("(none)")

summary_text = u"\n".join(summary_lines) + u"\n"
write_text_atomic(SUMMARY_PATH, summary_text.encode("ascii", "replace"))

try:
    sys.stdout.write(summary_text.encode("ascii", "replace"))
    sys.stdout.write("\nResult: %s\nSummary: %s\n" % (RESULT_PATH, SUMMARY_PATH))
    if report.get("invocation") == "A_INSTALL":
        sys.stdout.write("\nNow run this SAME script again, in the SAME SFM process (do not restart), for check B.\n")
    elif report.get("invocation") == "B_SAME_PROCESS_CHECK":
        sys.stdout.write("\nNow fully restart SFM and run this SAME script again for check C.\n")
    else:
        sys.stdout.write("\nProbe sequence complete.\n")
except Exception:
    pass
