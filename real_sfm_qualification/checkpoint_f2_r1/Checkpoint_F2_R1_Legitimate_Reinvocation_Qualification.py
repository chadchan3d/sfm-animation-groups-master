# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint F2-R1: Legitimate
Same-Process Reinvocation Qualification.

RUN TYPE: MAIN MENU SCRIPT, MUTATING, INVOKED MULTIPLE TIMES ACROSS ONE
CONTINUOUS SFM PROCESS (Stage 1, then Stage 2), then ONE MORE TIME after a
deliberate restart (Final Verification).

PURPOSE: this is NOT part of the F1 optimization search (that search is
concluded -- see F1_OPTIMIZATION_INVESTIGATION_SUMMARY.md -- and is not
reopened by this checkpoint). This is the ONE narrow real-SFM confirmation
F1_REPEAT_HISTORY_AUDIT.md identified as still missing before F's own
final disposition can be decided: whether a LEGITIMATE supported workflow
-- production All Shots completes, the user returns to ordinary editing,
makes one real, small, predetermined control-group-affecting edit that
genuinely warrants renormalization, then invokes All Shots again in the
SAME unrestarted process -- actually works. This is explicitly NOT an
immediate unchanged All->All stress test, NOT a repetition-count test, and
NOT an optimization benchmark. Undo is NOT a requirement anywhere in this
checkpoint.

THE CONTROLLED EDIT (already-qualified, not invented -- see
F2_R1_CONTROLLED_EDIT_JUSTIFICATION.md for the full evidence trail,
CORRECTED 2026-09-24: the operator cannot freely drag a control into an
arbitrary existing group in SFM; the actual supported relocation
mechanism is the real, first-party SFM DAG-view right-click command
"move_to_hidden group" (platform/scripts/sfm/dag/exact/count1/move_to_
hidden group .py -> Hide_SelectedDag()), which moves the selected
control into a group literally named "Hidden" -- created via
rootGroup.CreateControlGroup("Hidden") with SetVisible(False) if it does
not already exist):
  shot=shot3, target=foxmccouldwm1, control=rig_hand_L.
  Qualified state (confirmed directly from the real, preserved F1-2
  command-1 production log, PRODUCTION_DESTINATION_DIRECT_ORDER_
  AUTHORITIES row for RigArms/LeftArm, authority=EXACT_MASTER_
  DESTINATION_TOTAL_ORDER): rig_hand_L is a direct member of
  "RigArms/LeftArm", ordered (rig_collar_L, rig_elbow_L, rig_hand_L).
  Operator mutation (the real SFM DAG "move to hidden group" command, ONE
  control, no inventory change, same existing model/vocabulary): move
  rig_hand_L out of "RigArms/LeftArm" into the (real, invisible-by-design)
  "Hidden" group.
  Expected post-command-2 state: rig_hand_L back in "RigArms/LeftArm",
  with RigArms/LeftArm's own direct-control order restored to exactly
  (rig_collar_L, rig_elbow_L, rig_hand_L).

  Verified directly against production source (see
  F2_R1_CONTROLLED_EDIT_JUSTIFICATION.md for exact line citations) that a
  hidden rig-owned control is NOT excluded from Master-driven
  reconciliation: composer's own destination computation
  (_active_rig_counterpart_destination) is IDENTICAL whether the control
  is currently hidden or visible. A hidden rig-owned DmeTransformControl
  is additionally gated by a "PRE-hidden Master-active repair" safety
  rule (its own destination's active root, e.g. RigArms, must be visible,
  and at least 2 OTHER visible rig-owned peers must independently map to
  the exact same destination) -- rig_hand_L's own real siblings
  (rig_collar_L, rig_elbow_L), untouched by this edit, satisfy that gate.
  This changes the LOGGED authority label for this one control
  (PRE_HIDDEN_MASTER_ACTIVE+... instead of MASTER_PLUS_ACTIVE_RIG_
  COUNTERPART) but not the computed destination itself.

STAGED DESIGN (why ONE script, invoked multiple times, is sufficient):
Ordinary SFM editing must happen BETWEEN the two production commands, so
no single script invocation can span it. Cross-invocation continuity
within the SAME process is proven throughout this project (the
RUN_LOCK_NAME QObject-child-of-main_window technique, reused unmodified
here) -- a small marker QObject parented to main_window survives across
separate top-level script executions in the same process but is absent
after a real restart, which is exactly the signal needed to detect a
protocol violation (SFM restarted between Stage 1 and Stage 2, invalidating
the same-process claim) versus a legitimate mode transition. Combined with
a small persisted JSON state file (survives restarts, unlike the marker),
the script deterministically classifies every invocation into exactly one
of STAGE_1 / STAGE_2 / FINAL_VERIFICATION / a clearly-reported protocol
violation, and FAILS CLOSED (aborts before invoking production, or before
proceeding at all) on any state it cannot unambiguously classify.

WHY THIS HARNESS IS MATERIALLY LIGHTER THAN F1-1/F1-2: no whole-85-target
semantic capture and no whole-session external verification anywhere in
this script. The only DME read this script performs beyond production's
own execution is `capture_tree(aset.GetRootControlGroup())` -- production's
own, verbatim-reused, per-TARGET tree walker -- applied to exactly ONE
target's own root control group (foxmccouldwm1's own tree, on the order of
~200 controls / ~25 groups per its own real PRE signature), never the
whole scene and never all 62 eligible targets. This is the same function
production itself already uses internally for target-level before/after
membership comparison (confirmed by direct source reading).

WHY THE PRECONDITION/POSTCONDITION CHECKS ARE SAFE FROM A RACE: exec()-ing
the pinned production bytes triggers the real scope-choice dialog and
production's own one-time synchronous setup (building instance.work), but
NOT any actual per-target native processing -- that is only scheduled via
QTimer.singleShot() and does not fire until the Qt event loop is pumped
(confirmed by direct source reading, the same finding every earlier
checkpoint in this project's exec()-and-locate technique relies on). This
script performs its own read of instance.work and its own
precondition/postcondition control-membership check strictly BEFORE the
first QtCore.QCoreApplication.processEvents() call in the wait loop, so no
native Rebuild call for ANY target (including foxmccouldwm1, which is
shot3's own target and shot3 is frequently production's own first-processed
shot) can have run yet when the precondition check executes.

RESOURCE TELEMETRY: reuses the SAME extracted production functions
(contextualizer_process_memory_sample, contextualizer_virtual_address_
sample) every earlier real-SFM checkpoint in this project already uses,
sampled immediately before and after each command. No new resource-
admission threshold is invented; raw deltas are reported, not judged.

Do NOT run this against the original testscripts.dmx fixture, and do NOT
run Stage 1/Stage 2 against anything other than the accepted normalized
qualification fixture -- this script structurally refuses to proceed
otherwise. Final Verification mode instead requires the disposable saved
result file specifically (never the original fixture).
"""
import gc
import hashlib
import json
import os
import sys
import time
import traceback

from PySide import QtCore

# ---------------------------------------------------------------------------
# Pinned identities.
# ---------------------------------------------------------------------------

EXPECTED_PRODUCTION_NORMALIZER_SHA256 = (
    "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"
)
EXPECTED_CANONICAL_MASTER_SHA256 = (
    "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
)
STAGE_FIXTURE_FILENAME = u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx"
FINAL_VERIFICATION_FIXTURE_FILENAME = u"F2_R1_DISPOSABLE_REINVOCATION_RESULT.dmx"
FORBIDDEN_ORIGINAL_FIXTURE_FILENAME = u"testscripts.dmx"

# --- The controlled edit (see module docstring + F2_R1_CONTROLLED_EDIT_
#     JUSTIFICATION.md for the full evidence trail). ---
TARGET_SHOT_NAME = u"shot3"
TARGET_ANIMSET_NAME = u"foxmccouldwm1"
CONTROLLED_CONTROL_NAME = u"rig_hand_L"
QUALIFIED_GROUP_PATH = u"RigArms/LeftArm"
OPERATOR_EDIT_DESTINATION_GROUP_PATH = u"Hidden"
EXPECTED_RIGARMS_LEFTARM_ORDER = [u"rig_collar_L", u"rig_elbow_L", u"rig_hand_L"]

STAGE1_MARKER_NAME = u"SFM_F2_R1_STAGE1_COMPLETE_MARKER"
STAGE2_MARKER_NAME = u"SFM_F2_R1_STAGE2_COMPLETE_MARKER"

STATE_FILE_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f2_r1_state.json"
STAGE1_RESULT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f2_r1_stage1_result.json"
STAGE1_SUMMARY_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f2_r1_stage1_summary.txt"
STAGE2_RESULT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f2_r1_stage2_result.json"
STAGE2_SUMMARY_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f2_r1_stage2_summary.txt"
FINAL_VERIFICATION_RESULT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f2_r1_final_verification_result.json"
FINAL_VERIFICATION_SUMMARY_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f2_r1_final_verification_summary.txt"

NORMALIZER_LOG_PATH = "C:\\Users\\Public\\Documents\\sfm_rebuild_control_groups.txt"
STAGE1_PRODUCTION_LOG_PRESERVE_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f2_r1_stage1_production_log.txt"
STAGE2_PRODUCTION_LOG_PRESERVE_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f2_r1_stage2_production_log.txt"

MAX_WAIT_SECONDS = 1800  # generous operator/native timing, matching F1-2's own proven value

PRODUCTION_NORMALIZER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
    "Rebuild_Control_Groups_Normalizer.py",
)
CANONICAL_MASTER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "cfg", "sfm_defaultanimationgroups.txt",
)


class CheckpointF2R1Error(Exception):
    pass


ANOMALIES = []


def anomaly(message):
    ANOMALIES.append(message)
    try:
        sys.stdout.write("ANOMALY: %s\n" % message)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Shared helpers (verbatim, same copies every earlier checkpoint uses).
# ---------------------------------------------------------------------------

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

    def _cleanup_tmp():
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

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
    except Exception as exc:
        _cleanup_tmp()
        return False, "json.dump()/write to temp file (%r) failed: %r" % (tmp_path, exc), None
    try:
        temp_size = os.path.getsize(tmp_path)
    except Exception as exc:
        _cleanup_tmp()
        return False, "could not stat temp file (%r): %r" % (tmp_path, exc), None
    if temp_size <= 0:
        _cleanup_tmp()
        return False, "temp file is zero bytes after write (size=%r)" % (temp_size,), None
    try:
        with open(tmp_path, "rb") as f:
            reparsed_obj = json.load(f)
    except Exception as exc:
        _cleanup_tmp()
        return False, "temp file reopen/reparse verification failed: %r" % (exc,), None
    try:
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(tmp_path, final_path)
    except Exception as exc:
        return False, "promoting temp file to final path failed: %r" % (exc,), None
    return True, None, reparsed_obj


def write_text_atomic(final_path, text_bytes):
    tmp_path = final_path + ".tmp"

    def _cleanup_tmp():
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

    try:
        f = open(tmp_path, "wb")
        try:
            f.write(text_bytes)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        finally:
            f.close()
    except Exception as exc:
        _cleanup_tmp()
        return False, "temp file write (%r) failed: %r" % (tmp_path, exc)
    try:
        temp_size = os.path.getsize(tmp_path)
    except Exception as exc:
        _cleanup_tmp()
        return False, "could not stat temp file (%r): %r" % (tmp_path, exc)
    if temp_size <= 0:
        _cleanup_tmp()
        return False, "temp file is zero bytes after write (size=%r)" % (temp_size,)
    try:
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(tmp_path, final_path)
    except Exception as exc:
        return False, "promoting temp file to final path failed: %r" % (exc,)
    return True, None


def read_state_file():
    if not os.path.exists(STATE_FILE_PATH):
        return None
    try:
        with open(STATE_FILE_PATH, "rb") as f:
            return json.load(f)
    except Exception as exc:
        raise CheckpointF2R1Error("State file exists but could not be read/parsed: %r -- STOP, do not guess." % (exc,))


def marker_present(main_window, marker_name):
    if main_window is None:
        return False
    try:
        for child in main_window.findChildren(QtCore.QObject):
            try:
                if b_to_unicode(child.objectName()) == marker_name:
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def set_marker(main_window, marker_name):
    marker = QtCore.QObject(main_window)
    marker.setObjectName(marker_name)
    return marker


def capture_forensic_pre_classification_snapshot(main_window):
    """F2-R1-R2 forensic addition: captures the exact pre-classification
    disk/process state, BEFORE any state write and BEFORE classify_
    invocation_mode() is even called. Read-only; never writes STATE_FILE_
    PATH or anything else. This is the evidence needed to distinguish a
    genuine same-process marker-persistence defect from an operator-side
    "SFM was actually restarted" misunderstanding, after a real run showed
    a fresh-looking invocation unexpectedly classify as stage1_complete
    with no marker present."""
    snapshot = {
        "state_path": STATE_FILE_PATH,
        "state_path_abspath": os.path.abspath(STATE_FILE_PATH),
        "state_file_exists": False,
        "state_file_raw_contents": None,
        "state_file_size_bytes": None,
        "state_file_mtime": None,
        "current_pid": None,
        "stage1_marker_name": STAGE1_MARKER_NAME,
        "stage2_marker_name": STAGE2_MARKER_NAME,
        "stage1_marker_present": None,
        "stage2_marker_present": None,
        "all_marker_like_child_object_names": [],
    }
    try:
        snapshot["current_pid"] = os.getpid()
    except Exception as exc:
        snapshot["current_pid_error"] = repr(exc)

    try:
        snapshot["state_file_exists"] = os.path.exists(STATE_FILE_PATH)
        if snapshot["state_file_exists"]:
            st = os.stat(STATE_FILE_PATH)
            snapshot["state_file_size_bytes"] = st.st_size
            snapshot["state_file_mtime"] = st.st_mtime
            with open(STATE_FILE_PATH, "rb") as f:
                raw = f.read()
            try:
                snapshot["state_file_raw_contents"] = raw.decode("ascii", "replace")
            except Exception:
                snapshot["state_file_raw_contents"] = repr(raw)
    except Exception as exc:
        snapshot["state_file_read_error"] = repr(exc)

    try:
        snapshot["stage1_marker_present"] = marker_present(main_window, STAGE1_MARKER_NAME)
        snapshot["stage2_marker_present"] = marker_present(main_window, STAGE2_MARKER_NAME)
    except Exception as exc:
        snapshot["marker_check_error"] = repr(exc)

    try:
        if main_window is not None:
            for child in main_window.findChildren(QtCore.QObject):
                try:
                    child_name = b_to_unicode(child.objectName())
                except Exception:
                    continue
                if child_name and (u"MARKER" in child_name.upper() or u"F2_R1" in child_name.upper() or u"RUN_LOCK" in child_name.upper()):
                    snapshot["all_marker_like_child_object_names"].append(child_name)
    except Exception as exc:
        snapshot["child_enumeration_error"] = repr(exc)

    return snapshot


def assert_legal_classification_or_raise(state, stage1_marker, stage2_marker, mode):
    """F2-R1-R2 forensic addition: an explicit, redundant safety net,
    independent of classify_invocation_mode()'s own internal logic. If the
    invocation enters with state file absent AND both markers absent, the
    ONLY legal classification is STAGE_1 -- anything else observed here is
    itself a harness defect, not a normal protocol-violation STOP, and must
    be reported as such rather than silently passing through."""
    entered_with_no_state_and_no_markers = (state is None) and (not stage1_marker) and (not stage2_marker)
    if entered_with_no_state_and_no_markers and mode != "STAGE_1":
        raise CheckpointF2R1Error(
            "HARNESS DEFECT (not a normal protocol violation): entered with state file "
            "absent and both markers absent, which can only legally classify as STAGE_1, "
            "but classify_invocation_mode() returned %r instead. STOP -- this indicates a "
            "bug in classify_invocation_mode() itself, not a legitimate stale-state "
            "rejection." % (mode,)
        )


def classify_invocation_mode(state, stage1_marker, stage2_marker):
    """Pure decision function (offline-testable): returns (mode, reason)
    where mode is one of 'STAGE_1'/'STAGE_2'/'FINAL_VERIFICATION'/None
    (None means: STOP, protocol violation, reason explains why)."""
    if state is None:
        if stage1_marker or stage2_marker:
            return None, "No state file exists, but an in-process marker from a prior run of this script was found -- unexpected/inconsistent state. STOP."
        return "STAGE_1", "No prior state -- fresh Stage 1."
    if state.get("stage2_complete"):
        if stage1_marker or stage2_marker:
            return None, "Stage 2 already completed IN THIS PROCESS. Final Verification requires a fresh SFM restart, not a same-process re-run. STOP."
        return "FINAL_VERIFICATION", "Stage 2 already completed (per state file); no in-process marker present -- this is a fresh process, consistent with a post-restart Final Verification invocation."
    if state.get("stage1_complete"):
        if stage1_marker:
            return "STAGE_2", "Stage 1 completed in this exact process (marker present) -- proceeding to Stage 2."
        return None, "Stage 1 was completed in a DIFFERENT SFM process (state file says stage1_complete, but no in-process marker was found in THIS process). This test requires Stage 2 to run in the SAME continuous process as Stage 1. Restart the whole test from Stage 1. STOP."
    return None, "State file exists but is in an unrecognized/corrupt state (neither stage1_complete nor stage2_complete is True). STOP, do not guess."


# ---------------------------------------------------------------------------
# Control-membership check (uses production's own capture_tree/
# one_membership, extracted verbatim, applied to ONE target's own root
# control group only -- never a whole-session capture).
# ---------------------------------------------------------------------------

def get_control_membership(capture_tree_fn, one_membership_fn, aset, control_name):
    root_group = aset.GetRootControlGroup()
    if root_group is None:
        raise CheckpointF2R1Error("aset.GetRootControlGroup() returned None for the target's own animation set.")
    tree = capture_tree_fn(root_group)
    path = one_membership_fn(tree, control_name)
    return path, tree


def find_target_aset(work, shot_name, target_name):
    for shot_record in work:
        if b_to_unicode(shot_record["name"]) != shot_name:
            continue
        for target in shot_record["targets"]:
            if b_to_unicode(target["name"]) == target_name:
                return target["anim_set"]
    return None


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

report = {
    "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "python_version": sys.version,
    "checks": [],
    "anomalies": ANOMALIES,
    "provenance": {},
    "mode": None,
    "in_progress": True,
}


def check(name, condition, detail=None):
    report["checks"].append({"name": name, "pass": bool(condition), "detail": repr(detail) if detail is not None else None})
    try:
        sys.stdout.write("[%s] %s%s\n" % ("PASS" if condition else "FAIL", name, ("" if detail is None else " -- %r" % (detail,))))
    except Exception:
        pass


result_json_path = None
result_summary_path = None
main_window = None
instance = None
mode = None

try:
    # F2-R1-R2 forensic addition: capture the EXACT pre-classification
    # disk/process state FIRST, before read_state_file() is even called
    # for classification purposes and strictly before any state write.
    main_window = sfmApp.GetMainWindow()
    forensic_snapshot = capture_forensic_pre_classification_snapshot(main_window)
    report["forensic_pre_classification_snapshot"] = forensic_snapshot
    ok, err, _r = write_json_atomic(
        "C:\\Users\\Public\\Documents\\sfm_checkpoint_f2_r1_forensic_snapshot.json", forensic_snapshot
    )
    if not ok:
        anomaly("Forensic snapshot write failed (run continues): %s" % (err,))
    sys.stdout.write("F2-R1 forensic pre-classification snapshot: %r\n" % (forensic_snapshot,))

    state = read_state_file()
    stage1_marker = forensic_snapshot.get("stage1_marker_present")
    stage2_marker = forensic_snapshot.get("stage2_marker_present")
    mode, mode_reason = classify_invocation_mode(state, stage1_marker, stage2_marker)
    assert_legal_classification_or_raise(state, stage1_marker, stage2_marker, mode)
    if mode is None:
        raise CheckpointF2R1Error("Mode classification failed: %s" % mode_reason)
    report["mode"] = mode
    report["mode_reason"] = mode_reason
    check("mode.classified", mode in ("STAGE_1", "STAGE_2", "FINAL_VERIFICATION"), mode)
    sys.stdout.write("F2-R1 mode: %s (%s)\n" % (mode, mode_reason))

    if mode == "STAGE_1":
        result_json_path, result_summary_path = STAGE1_RESULT_PATH, STAGE1_SUMMARY_PATH
    elif mode == "STAGE_2":
        result_json_path, result_summary_path = STAGE2_RESULT_PATH, STAGE2_SUMMARY_PATH
    else:
        result_json_path, result_summary_path = FINAL_VERIFICATION_RESULT_PATH, FINAL_VERIFICATION_SUMMARY_PATH

    def write_rolling_evidence():
        ok, err, _r = write_json_atomic(result_json_path, report)
        if not ok:
            anomaly("Rolling evidence write failed (run continues): %s" % (err,))
        return ok

    write_rolling_evidence()

    with open(PRODUCTION_NORMALIZER_PATH, "rb") as f:
        production_bytes = f.read()
    production_sha = hashlib.sha256(production_bytes).hexdigest()
    check("production_normalizer.sha256_matches_accepted_integration", production_sha == EXPECTED_PRODUCTION_NORMALIZER_SHA256, production_sha)

    with open(CANONICAL_MASTER_PATH, "rb") as f:
        master_bytes = f.read()
    master_sha = hashlib.sha256(master_bytes).hexdigest()
    check("canonical_master.sha256_unchanged", master_sha == EXPECTED_CANONICAL_MASTER_SHA256, master_sha)

    if not (production_sha == EXPECTED_PRODUCTION_NORMALIZER_SHA256 and master_sha == EXPECTED_CANONICAL_MASTER_SHA256):
        raise CheckpointF2R1Error("Pre-flight SHA-256 check failed -- refusing to proceed.")
    report["provenance"]["production_normalizer_sha256"] = production_sha
    report["provenance"]["canonical_master_sha256"] = master_sha

    if not bool(sfmApp.HasDocument()):
        raise CheckpointF2R1Error("No SFM document is open.")

    root_for_filename = sfmApp.GetDocumentRoot()
    if root_for_filename is None:
        raise CheckpointF2R1Error("sfmApp.GetDocumentRoot() returned None.")
    open_file_id = root_for_filename.GetFileId()
    open_path = vs.g_pDataModel.GetFileName(open_file_id)
    open_basename = os.path.basename(b_to_unicode(open_path)) if open_path else u""

    expected_filename = STAGE_FIXTURE_FILENAME if mode in ("STAGE_1", "STAGE_2") else FINAL_VERIFICATION_FIXTURE_FILENAME
    check("fixture.refuses_original_fixture_filename", open_basename.lower() != FORBIDDEN_ORIGINAL_FIXTURE_FILENAME.lower(), open_basename)
    check("fixture.matches_expected_filename_for_mode", open_basename.lower() == expected_filename.lower(), (open_basename, expected_filename))
    if open_basename.lower() == FORBIDDEN_ORIGINAL_FIXTURE_FILENAME.lower():
        raise CheckpointF2R1Error("REFUSING TO RUN against the original disposable qualification fixture (%r)." % (open_basename,))
    if open_basename.lower() != expected_filename.lower():
        raise CheckpointF2R1Error("Open document (%r) does not match the expected filename for mode %s (%r)." % (open_basename, mode, expected_filename))

    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointF2R1Error("Starting-state fixture gate failed -- aborting before any production invocation.")

    check("f2r1.main_window_available", main_window is not None)
    write_rolling_evidence()

    # -----------------------------------------------------------------
    # FINAL_VERIFICATION mode: read-only, no production invocation.
    # -----------------------------------------------------------------
    if mode == "FINAL_VERIFICATION":
        prod_ns = {}
        exec(compile(production_bytes, "<installed_production_normalizer_f2r1_fv>", "exec"), prod_ns)
        capture_tree_fn = prod_ns.get("capture_tree")
        one_membership_fn = prod_ns.get("one_membership")
        to_unicode_fn = prod_ns.get("to_unicode")
        run_lock_name = prod_ns.get("RUN_LOCK_NAME")
        for required_name, required_value in (("capture_tree", capture_tree_fn), ("one_membership", one_membership_fn), ("to_unicode", to_unicode_fn), ("RUN_LOCK_NAME", run_lock_name)):
            if required_value is None:
                raise CheckpointF2R1Error("Required production name not found in exec'd namespace: %s" % required_name)

        for child in main_window.findChildren(QtCore.QObject):
            try:
                if b_to_unicode(child.objectName()) == run_lock_name:
                    instance = child
                    break
            except Exception:
                continue
        check("f2r1.run_instance_located", instance is not None)
        if instance is None:
            raise CheckpointF2R1Error("Could not locate the already-constructed run instance immediately after exec() in Final Verification mode.")
        instance.finished = True  # neutralize immediately; this mode never pumps events for production's own sake
        check("f2r1.instance_neutralized_readonly_mode", bool(instance.finished))

        work = instance.work
        aset = find_target_aset(work, TARGET_SHOT_NAME, TARGET_ANIMSET_NAME)
        check("f2r1.target_aset_resolved", aset is not None, (TARGET_SHOT_NAME, TARGET_ANIMSET_NAME))
        if aset is None:
            raise CheckpointF2R1Error("Could not resolve target aset for %s/%s in Final Verification mode." % (TARGET_SHOT_NAME, TARGET_ANIMSET_NAME))

        final_path, final_tree = get_control_membership(capture_tree_fn, one_membership_fn, aset, CONTROLLED_CONTROL_NAME)
        report["final_verification"] = {
            "control_current_path": final_path,
            "expected_path": QUALIFIED_GROUP_PATH,
            "rigarms_leftarm_order": (final_tree.get("groups", {}).get(QUALIFIED_GROUP_PATH, {}) or {}).get("direct_control_names_in_order"),
        }
        check("f2r1.final_verification.control_in_expected_group", final_path == QUALIFIED_GROUP_PATH, final_path)
        check(
            "f2r1.final_verification.rigarms_leftarm_order_matches_expected",
            report["final_verification"]["rigarms_leftarm_order"] == EXPECTED_RIGARMS_LEFTARM_ORDER,
            report["final_verification"]["rigarms_leftarm_order"],
        )
        write_rolling_evidence()

    # -----------------------------------------------------------------
    # STAGE_1 / STAGE_2: invoke production for real, wait for completion.
    # -----------------------------------------------------------------
    else:
        before_memory = None
        before_vas = None
        prod_ns = {}
        try:
            exec(compile(production_bytes, "<installed_production_normalizer_f2r1_%s>" % mode.lower(), "exec"), prod_ns)
        except Exception as exc:
            anomaly("Production Normalizer execution raised: %r" % (exc,))
            anomaly(traceback.format_exc())

        capture_tree_fn = prod_ns.get("capture_tree")
        one_membership_fn = prod_ns.get("one_membership")
        contextualizer_process_memory_sample = prod_ns.get("contextualizer_process_memory_sample")
        contextualizer_virtual_address_sample = prod_ns.get("contextualizer_virtual_address_sample")
        run_lock_name = prod_ns.get("RUN_LOCK_NAME")

        for required_name, required_value in (
            ("capture_tree", capture_tree_fn), ("one_membership", one_membership_fn),
            ("contextualizer_process_memory_sample", contextualizer_process_memory_sample),
            ("contextualizer_virtual_address_sample", contextualizer_virtual_address_sample),
            ("RUN_LOCK_NAME", run_lock_name),
        ):
            if required_value is None:
                raise CheckpointF2R1Error("Required production name not found in exec'd namespace: %s" % required_name)

        for child in main_window.findChildren(QtCore.QObject):
            try:
                if b_to_unicode(child.objectName()) == run_lock_name:
                    instance = child
                    break
            except Exception:
                continue
        check("f2r1.run_instance_located", instance is not None)
        if instance is None:
            raise CheckpointF2R1Error("Could not locate the already-constructed run instance immediately after exec().")

        # --- Safe window: instance.work is populated, but NO native
        #     processing has occurred yet (only QTimer-scheduled, requires
        #     an event pump we have not performed). Read the target and do
        #     the precondition check here, before any processEvents(). ---
        work = instance.work
        aset = find_target_aset(work, TARGET_SHOT_NAME, TARGET_ANIMSET_NAME)
        check("f2r1.target_aset_resolved", aset is not None, (TARGET_SHOT_NAME, TARGET_ANIMSET_NAME))
        if aset is None:
            raise CheckpointF2R1Error("Could not resolve target aset for %s/%s." % (TARGET_SHOT_NAME, TARGET_ANIMSET_NAME))

        pre_path, pre_tree = get_control_membership(capture_tree_fn, one_membership_fn, aset, CONTROLLED_CONTROL_NAME)
        report["precondition"] = {"control_current_path": pre_path}
        write_rolling_evidence()

        if mode == "STAGE_2":
            check("f2r1.stage2.precondition_edit_is_present", pre_path == OPERATOR_EDIT_DESTINATION_GROUP_PATH, pre_path)
            if pre_path != OPERATOR_EDIT_DESTINATION_GROUP_PATH:
                raise CheckpointF2R1Error(
                    "Stage 2 precondition failed: expected %r to currently be a member of %r (the specified "
                    "operator edit), but found %r instead. The controlled edit was not detected as applied -- "
                    "STOP, do not run production. Re-check the operator instructions and try Stage 2 again "
                    "WITHOUT restarting SFM." % (CONTROLLED_CONTROL_NAME, OPERATOR_EDIT_DESTINATION_GROUP_PATH, pre_path)
                )
        else:
            check("f2r1.stage1.control_already_in_qualified_group", pre_path == QUALIFIED_GROUP_PATH, pre_path)

        before_memory = contextualizer_process_memory_sample()
        before_vas = contextualizer_virtual_address_sample()
        report["memory_snapshots"] = {"before": {"memory": before_memory, "vas": before_vas}}
        write_rolling_evidence()

        def normalizer_run_is_active():
            if run_lock_name is None or main_window is None:
                return False
            try:
                for child in main_window.findChildren(QtCore.QObject):
                    try:
                        if b_to_unicode(child.objectName()) == run_lock_name:
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
            return False

        run_started = normalizer_run_is_active()
        run_completed_cleanly = False
        command_start_time = time.time()
        if run_started:
            sys.stdout.write("Command detected as active; waiting for completion (up to %d seconds)...\n" % MAX_WAIT_SECONDS)
            wait_start = time.time()
            while normalizer_run_is_active():
                QtCore.QCoreApplication.processEvents()
                time.sleep(0.05)
                if time.time() - wait_start > MAX_WAIT_SECONDS:
                    anomaly("Command did not complete within %d seconds -- aborting wait." % MAX_WAIT_SECONDS)
                    break
            else:
                run_completed_cleanly = True
            settle_start = time.time()
            while time.time() - settle_start < 1.0:
                QtCore.QCoreApplication.processEvents()
                time.sleep(0.05)
        else:
            anomaly("No run-lock was ever observed active after executing the production Normalizer source -- this most likely means the operator cancelled the scope dialog.")

        command_duration_seconds = time.time() - command_start_time
        check("f2r1.command.run_was_started", run_started)
        check("f2r1.command.run_completed_within_timeout", run_completed_cleanly if run_started else False)
        check("f2r1.command.total_shots_processed_nonzero", getattr(instance, "total_shots_processed", 0) > 0, getattr(instance, "total_shots_processed", None))

        native_evidence = {}
        preserve_path = STAGE1_PRODUCTION_LOG_PRESERVE_PATH if mode == "STAGE_1" else STAGE2_PRODUCTION_LOG_PRESERVE_PATH
        try:
            with open(NORMALIZER_LOG_PATH, "rb") as f:
                log_bytes = f.read()
            log_text = log_bytes.decode("ascii", "replace")
            native_evidence["log_size_bytes"] = len(log_bytes)
            native_evidence["contains_NATIVE_GUARDS_PASS"] = ("NATIVE_GUARDS = PASS" in log_text)
            native_evidence["contains_NATIVE_REBUILD_RETURNED_PASS"] = ("NATIVE_REBUILD_RETURNED = PASS" in log_text)
            native_evidence["contains_FINAL_REPORT_ENTRY"] = ("FINAL_REPORT_ENTRY" in log_text)
            preserve_ok, preserve_err = write_text_atomic(preserve_path, log_bytes)
            if not preserve_ok:
                anomaly("Could not preserve production log: %s" % preserve_err)
            del log_bytes, log_text
        except Exception as exc:
            native_evidence["log_read_ok"] = False
            native_evidence["log_read_error"] = repr(exc)
            anomaly("Could not read production Normalizer log for evidence: %r" % (exc,))

        check("f2r1.command.native_guards_pass", native_evidence.get("contains_NATIVE_GUARDS_PASS") is True, native_evidence.get("contains_NATIVE_GUARDS_PASS"))
        check("f2r1.command.native_rebuild_returned_pass", native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS") is True, native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS"))
        check("f2r1.command.final_report_entry_reached", native_evidence.get("contains_FINAL_REPORT_ENTRY") is True, native_evidence.get("contains_FINAL_REPORT_ENTRY"))

        post_path, post_tree = get_control_membership(capture_tree_fn, one_membership_fn, aset, CONTROLLED_CONTROL_NAME)
        rigarms_leftarm_order = (post_tree.get("groups", {}).get(QUALIFIED_GROUP_PATH, {}) or {}).get("direct_control_names_in_order")
        report["postcondition"] = {
            "control_current_path": post_path,
            "rigarms_leftarm_order": rigarms_leftarm_order,
        }
        check("f2r1.command.control_ends_in_qualified_group", post_path == QUALIFIED_GROUP_PATH, post_path)
        if mode == "STAGE_2":
            check("f2r1.stage2.rigarms_leftarm_order_restored", rigarms_leftarm_order == EXPECTED_RIGARMS_LEFTARM_ORDER, rigarms_leftarm_order)

        after_memory = contextualizer_process_memory_sample()
        after_vas = contextualizer_virtual_address_sample()
        gc.collect()
        postgc_memory = contextualizer_process_memory_sample()
        postgc_vas = contextualizer_virtual_address_sample()

        def _delta(a, b, key):
            try:
                return a[key] - b[key]
            except Exception:
                return None

        report["memory_snapshots"]["after"] = {"memory": after_memory, "vas": after_vas}
        report["memory_snapshots"]["after_gc"] = {"memory": postgc_memory, "vas": postgc_vas}
        report["resource_deltas"] = {
            "private_delta": _delta(after_memory, before_memory, "private"),
            "working_set_delta": _delta(after_memory, before_memory, "working_set"),
            "free_vas_delta": _delta(after_vas, before_vas, "free"),
            "largest_free_delta": _delta(after_vas, before_vas, "largest_free"),
        }
        report["command_record"] = {
            "mode": mode,
            "duration_seconds": command_duration_seconds,
            "run_started": run_started,
            "run_completed_cleanly": run_completed_cleanly,
            "native_evidence": native_evidence,
            "total_shots_processed": getattr(instance, "total_shots_processed", None),
        }
        write_rolling_evidence()

        # --- Persist minimal cross-invocation state + set the in-process
        #     marker, ONLY if this command's own checks all passed so far. ---
        stage_checks_passed = all(c["pass"] for c in report["checks"])
        if stage_checks_passed:
            current_pid = None
            try:
                current_pid = os.getpid()
            except Exception:
                pass
            if mode == "STAGE_1":
                set_marker(main_window, STAGE1_MARKER_NAME)
                new_state = {
                    "stage1_complete": True, "stage2_complete": False,
                    "stage1_completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "stage1_pid": current_pid,
                }
            else:
                set_marker(main_window, STAGE2_MARKER_NAME)
                new_state = dict(state or {})
                new_state["stage2_complete"] = True
                new_state["stage2_completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                new_state["stage2_pid"] = current_pid
            state_write_ok, state_write_err, _r = write_json_atomic(STATE_FILE_PATH, new_state)
            check("f2r1.state_persisted", state_write_ok, state_write_err)
        else:
            anomaly("One or more checks failed -- NOT persisting stage-complete state or marker, so a retry does not silently skip this stage.")

except CheckpointF2R1Error as gate_exc:
    anomaly("GATE FAILURE (orderly abort): %s" % gate_exc)
    report["gate_failure"] = True
except Exception as top_exc:
    anomaly("UNHANDLED TOP-LEVEL EXCEPTION: %s" % repr(top_exc))
    anomaly(traceback.format_exc())
    report["gate_failure"] = False

# ---------------------------------------------------------------------------
# Finalize / write output.
# ---------------------------------------------------------------------------

report["in_progress"] = False
report["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

all_checks_passed = all(c["pass"] for c in report["checks"]) if report["checks"] else False
completed_without_exception = not any(a.startswith("UNHANDLED TOP-LEVEL EXCEPTION") for a in ANOMALIES)
report["overall_pass"] = bool(all_checks_passed and completed_without_exception and not report.get("gate_failure"))

if result_json_path is None:
    result_json_path = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f2_r1_mode_classification_failed_result.json"
    result_summary_path = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f2_r1_mode_classification_failed_summary.txt"

json_write_ok, json_write_error, _r = write_json_atomic(result_json_path, report)
if not json_write_ok:
    anomaly("Final JSON write failed: %s" % json_write_error)

summary_lines = []
summary_lines.append("SFM CHECKPOINT F2-R1 -- LEGITIMATE SAME-PROCESS REINVOCATION QUALIFICATION (mode=%s)" % (mode,))
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
if report.get("gate_failure"):
    summary_lines.append("*** GATE FAILURE ***")
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
for key in ("precondition", "postcondition", "final_verification", "command_record", "resource_deltas"):
    if key in report:
        summary_lines.append("%s=%r" % (key, report[key]))
summary_lines.append("")
summary_lines.append("OVERALL_PASS=%r" % report["overall_pass"])
summary_lines.append("")
summary_lines.append("--- ANOMALIES (%d) ---" % len(ANOMALIES))
for a in ANOMALIES:
    summary_lines.append("- %s" % a)
if not ANOMALIES:
    summary_lines.append("(none)")
summary_lines.append("")
summary_lines.append("json_output_path=%s (write_ok=%r)" % (result_json_path, json_write_ok))

summary_text = u"\n".join(summary_lines) + u"\n"
summary_write_ok, summary_write_error = write_text_atomic(result_summary_path, summary_text.encode("ascii", "replace"))

try:
    sys.stdout.write(summary_text.encode("ascii", "replace"))
    sys.stdout.write("\nCheckpoint F2-R1 (mode=%s) reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n" % (mode, result_json_path, json_write_ok, result_summary_path, summary_write_ok))
    if mode == "STAGE_1":
        sys.stdout.write("\nReturn fully to normal SFM editing now. Perform the specified controlled edit, then run this SAME checkpoint again for Stage 2.\n")
    elif mode == "STAGE_2":
        sys.stdout.write("\nReturn fully to normal SFM editing now. Confirm ordinary selection/posing/editing works, then Save As the disposable result filename, then restart SFM and run this SAME checkpoint again for Final Verification.\n")
    else:
        sys.stdout.write("\nFinal Verification complete. Restart SFM afterward.\n")
except Exception:
    pass
