# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint F1-R6: Fresh Streaming
Discovery Parity (TWO-MODE, SEPARATE-FRESH-PROCESS DESIGN).

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: **THIS CHECKPOINT DOES NOT MUTATE THE SCENE.** It never
calls native Rebuild, never activates a shot, and never writes anything.
It only calls ONE discovery implementation -- legacy (extracted unmodified
from the exec()'d production namespace) OR the F1-R6 streaming candidate,
never both -- against the same 62 real, already-known targets, and records
a compact per-target semantic evidence trail plus per-arm resource
deltas. **Do not save afterward**, per this whole project's own standing
discipline, even though nothing here writes anything.

DESIGN CORRECTION FROM THE PRIOR (committed) VERSION OF THIS SCRIPT:
F1-R4/F1-R5 established that process-retained allocator/VAS high-water
survives GC. A single process running BOTH legacy and candidate discovery
-- even with per-target arm-order alternation -- lets one arm's own
process-retained allocation permanently raise the baseline the OTHER arm
is measured against. Order alternation only cancels first-position bias;
it does not remove this shared-process cross-arm contamination. This
script is therefore now a TWO-MODE, ONE-ARM-PER-PROCESS design:

  - The SAME MAINMENU script supports two independently selected modes,
    chosen via a real Qt dialog shown BEFORE production is exec()'d:
      1. LEGACY
      2. STREAMING_CANDIDATE
  - Each invocation of this script runs EXACTLY ONE mode, in whatever
    fresh SFM process the operator started it in. It never runs both
    arms in the same process.
  - Semantic comparison between the two arms is NOT performed in-process
    (there is no "other arm" to compare against here). Each run emits its
    own compact per-target semantic record to its OWN mode-specific output
    file. A separate, purely offline comparator
    (F1_R6_Compare_Legacy_vs_Streaming_Results.py) loads BOTH mode-specific
    JSON artifacts, from two separate fresh-process runs, after both exist,
    and performs the mechanical parity comparison and computes the derived
    resource-reduction metrics. This script never computes those derived
    metrics itself and never auto-declares a qualification result.

WORKLOAD-MULTIPLICITY DECISION (explicit, per instruction not to invent
state transitions merely to reach a round number): this workload measures
exactly ONE discover_rig_context() call per target (62 calls total per
arm/process), NOT the production's own real 250-site schedule
(32 COMPOSER_ENTRY_PATH targets x 5 calls + 30 NATIVE_POST_ONLY_STATUS_
MISMATCH targets x 3 calls, per F1-R4/F1-R5). That per-branch multiplicity
is only knowable by actually observing native Rebuild's own status-match
outcome and whether production_generic_composer() was entered -- both are
downstream, native-Rebuild-dependent decisions this checkpoint correctly
never invokes (it is read-only, by design, per F1-R3's finding that
discover_rig_context() itself does not require shot activation or any
mutation). There is no valid, non-invented way to assign a target to a
2/3/3/5-call branch without running native Rebuild first. Reproducing the
exact 250-call volume here would therefore require EITHER inventing a
branch assignment (fabricated state) or borrowing per-target branch
identity from a prior, different real run's own log (a form of staleness
this project's own discipline does not accept for a "fresh, live"
measurement). This checkpoint therefore deliberately measures the
SIMPLER, HONEST quantity: one matched, fresh, live discovery call per
target, per arm. CONCLUSION THIS SUPPORTS: a clean, per-call resource and
semantic comparison of legacy vs. candidate discovery, unconfounded by
call-count differences between arms. It does NOT itself provide command-
scale (250-call) resource projections; an analyst may scale the per-call
deltas this checkpoint reports by the already-established real call-volume
figures from F1-R4/F1-R5 (250 real calls across the same 62 targets) as a
SEPARATE, offline, explicitly-labeled extrapolation step -- this script
performs no such extrapolation itself.

This is NOT authorization to modify production. It does not implement,
propose to implement, or close F. The candidate remains FRESH STREAMING
OBSERVATION: every single call, legacy or candidate, performs a complete,
live, from-scratch traversal -- nothing is cached, reused, or trusted
stale across calls.

Design:
  1. Shows a real Qt dialog (QMessageBox with two custom buttons) BEFORE
     touching production at all, so the operator selects LEGACY or
     STREAMING_CANDIDATE for THIS run. This choice is fixed for the whole
     run; there is no second mode-selection dialog.
  2. exec()s the pinned, SHA-256-verified production bytes into a fresh
     namespace -- exactly as every earlier checkpoint does. This
     unavoidably triggers the real scope-choice dialog and production's
     own one-time synchronous setup, before returning control here (this
     one-time cost is not measured, since this script's own "before"
     checkpoint is taken strictly after exec() returns).
  3. Locates the already-constructed run instance and sets
     instance.finished = True immediately, before ever pumping the Qt
     event loop -- identical technique to F1-R3/F1-R4/F1-R5/the prior
     version of this script.
  4. Reads instance.work directly -- the exact, already-computed,
     production-ordered 62-target inventory. Never re-derived.
  5. Extracts legacy's own discover_rig_context (and the shared helpers
     handle/typ/arr/scalar/element_ref_pairs/name/to_unicode/ProbeError)
     from the exec()'d namespace -- never reimplemented. This happens
     regardless of mode, because production itself always defines these
     names when exec()'d (the LEGACY arm's own resource profile always
     includes the full cost of exec()-ing production; that cost is
     identical in both arms and is not being measured here anyway, since
     it happens before this script's own "before" checkpoint).
  6. ONLY when mode == STREAMING_CANDIDATE: loads the F1-R6 candidate
     prototype module's own source and exec()s it into a namespace seeded
     with those SAME extracted legacy helpers, so the candidate calls the
     identical native-bound functions legacy itself uses. This exec() (and
     its own resource cost) never happens at all in a LEGACY run, so a
     LEGACY run's own resource profile is never contaminated by candidate
     module loading.
  7. For each of the 62 targets, in instance.work's own order: calls ONLY
     the selected arm's discover_rig_context against the (shot, aset) pair
     -- no shot activation needed (discover_rig_context reads shot.scene
     directly, confirmed by direct source reading, not sfmApp's own
     playhead/active-shot state) and no per-target re-resolution needed
     (nothing ever mutates the scene in this script, so target["anim_set"]
     's own object reference, as already recorded in instance.work,
     remains valid throughout).
  8. Records status, reachable_rig_count, matching_rig_count, rig_handle,
     registry_handle, owned_handles, owned_names_in_order, hidden_groups,
     per-call elapsed time, and per-call process-memory deltas for every
     target -- a compact per-target semantic record, never a full object
     dump -- to THIS run's own mode-specific JSON output file. No
     cross-arm comparison happens here; that is the offline comparator's
     job, once both mode-specific artifacts exist.
  9. Samples cheap process memory (private/working-set, NOT the more
     expensive VirtualQuery-based VAS scan) immediately before and after
     EVERY individual call. Low-cadence VAS (free/largest-free)
     checkpoints are taken only at command start, every 8th target, final
     target, and before/after gc.collect() -- matching this whole
     project's own established "no expensive per-node VirtualQuery"
     discipline.
 10. No save. No composer, capture, classification, or verifier of any
     kind runs anywhere in this script.

Do NOT run this against the original testscripts.dmx fixture -- this
script structurally refuses to proceed if the currently open document's
own filename does not match the expected normalized-copy filename.
"""
import gc
import hashlib
import json
import os
import sys
import time
import traceback

from PySide import QtCore
from PySide import QtGui

# ---------------------------------------------------------------------------
# Pinned identities.
# ---------------------------------------------------------------------------

EXPECTED_PRODUCTION_NORMALIZER_SHA256 = (
    "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"
)
EXPECTED_CANONICAL_MASTER_SHA256 = (
    "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
)
EXPECTED_NORMALIZED_COPY_FILENAME = u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx"
FORBIDDEN_ORIGINAL_FIXTURE_FILENAME = u"testscripts.dmx"

EXPECTED_TOTAL_SHOTS = 15
EXPECTED_MODEL_BACKED_TARGETS = 85
EXPECTED_GATE_STATIC_SKIPS = 12
EXPECTED_GATE_FOLLOWER_SKIPS = 4
EXPECTED_GATE_LOWBONE_SKIPS = 7
EXPECTED_GATE_FAILCLOSED_PROCESS = 0
EXPECTED_ELIGIBLE_NATIVE_TARGETS = 62

VAS_CHECKPOINT_STRIDE = 8  # low-cadence: VAS-inclusive checkpoint every 8th target

MODE_LEGACY = u"LEGACY"
MODE_STREAMING_CANDIDATE = u"STREAMING_CANDIDATE"

OUTPUT_PATH_TEMPLATES = {
    MODE_LEGACY: {
        "json": "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r6_legacy_result.json",
        "summary": "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r6_legacy_result_summary.txt",
        "production_log": "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r6_legacy_production_log.txt",
    },
    MODE_STREAMING_CANDIDATE: {
        "json": "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r6_streaming_candidate_result.json",
        "summary": "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r6_streaming_candidate_result_summary.txt",
        "production_log": "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r6_streaming_candidate_production_log.txt",
    },
}

NORMALIZER_LOG_PATH = "C:\\Users\\Public\\Documents\\sfm_rebuild_control_groups.txt"

PRODUCTION_NORMALIZER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
    "Rebuild_Control_Groups_Normalizer.py",
)
CANONICAL_MASTER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "cfg", "sfm_defaultanimationgroups.txt",
)
PROTOTYPE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
    "F1_R6_Discovery_Streaming_Prototype.py",
)


class CheckpointF1R6Error(Exception):
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


def select_mode_via_dialog():
    """Shows a real, blocking Qt dialog with exactly two custom buttons.
    Returns MODE_LEGACY or MODE_STREAMING_CANDIDATE. Raises
    CheckpointF1R6Error if the dialog is dismissed without a clear
    selection (e.g. closed via the window's own close button)."""
    box = QtGui.QMessageBox()
    box.setWindowTitle(u"F1-R6 -- Select Discovery Arm For This Process")
    box.setText(
        u"This run measures exactly ONE discovery implementation in this "
        u"fresh SFM process.\n\nChoose which one this run measures. The "
        u"other arm must be measured by a SEPARATE fresh SFM process, run "
        u"independently."
    )
    legacy_button = box.addButton(u"LEGACY", QtGui.QMessageBox.ActionRole)
    streaming_button = box.addButton(u"STREAMING_CANDIDATE", QtGui.QMessageBox.ActionRole)
    box.setDefaultButton(legacy_button)
    box.exec_()
    clicked = box.clickedButton()
    if clicked is legacy_button:
        return MODE_LEGACY
    if clicked is streaming_button:
        return MODE_STREAMING_CANDIDATE
    raise CheckpointF1R6Error("Mode-selection dialog was dismissed without a clear LEGACY/STREAMING_CANDIDATE selection.")


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
    "targets_processed": [],
    "in_progress": True,
    "workload_design_note": (
        "This run measures exactly ONE discover_rig_context() call per "
        "target (62 total), not the production 250-site schedule, because "
        "per-target branch multiplicity (2/3/3/5 calls) is only knowable "
        "after observing native Rebuild's own status-match outcome, which "
        "this read-only checkpoint correctly never invokes. See this "
        "script's own module docstring for the full justification."
    ),
}


def check(name, condition, detail=None):
    report["checks"].append({"name": name, "pass": bool(condition), "detail": repr(detail) if detail is not None else None})
    try:
        sys.stdout.write("[%s] %s%s\n" % ("PASS" if condition else "FAIL", name, ("" if detail is None else " -- %r" % (detail,))))
    except Exception:
        pass


# Output paths depend on mode, which is not known until after the mode
# dialog is shown; rolling-evidence writes before that point are not
# possible and are not attempted (the mode dialog is the very first thing
# this script does after basic imports, before any SHA/fixture checks).
json_output_path = None
summary_output_path = None
production_log_preserve_path = None


def write_rolling_evidence():
    if json_output_path is None:
        return False
    ok, err, _r = write_json_atomic(json_output_path, report)
    if not ok:
        anomaly("Rolling evidence write failed (run continues): %s" % (err,))
    return ok


main_window = None
instance = None
mode = None

try:
    mode = select_mode_via_dialog()
    report["mode"] = mode
    check("mode.selected_is_valid", mode in (MODE_LEGACY, MODE_STREAMING_CANDIDATE), mode)

    paths_for_mode = OUTPUT_PATH_TEMPLATES[mode]
    json_output_path = paths_for_mode["json"]
    summary_output_path = paths_for_mode["summary"]
    production_log_preserve_path = paths_for_mode["production_log"]
    write_rolling_evidence()

    with open(PRODUCTION_NORMALIZER_PATH, "rb") as f:
        production_bytes = f.read()
    production_sha = hashlib.sha256(production_bytes).hexdigest()
    check("production_normalizer.sha256_matches_accepted_integration", production_sha == EXPECTED_PRODUCTION_NORMALIZER_SHA256, production_sha)

    with open(CANONICAL_MASTER_PATH, "rb") as f:
        master_bytes = f.read()
    master_sha = hashlib.sha256(master_bytes).hexdigest()
    check("canonical_master.sha256_unchanged", master_sha == EXPECTED_CANONICAL_MASTER_SHA256, master_sha)

    prototype_bytes = None
    if mode == MODE_STREAMING_CANDIDATE:
        with open(PROTOTYPE_PATH, "rb") as f:
            prototype_bytes = f.read()

    if not (production_sha == EXPECTED_PRODUCTION_NORMALIZER_SHA256 and master_sha == EXPECTED_CANONICAL_MASTER_SHA256):
        raise CheckpointF1R6Error("Pre-flight SHA-256 check failed -- refusing to proceed.")
    report["provenance"]["production_normalizer_sha256"] = production_sha
    report["provenance"]["canonical_master_sha256"] = master_sha
    if prototype_bytes is not None:
        report["provenance"]["prototype_sha256"] = hashlib.sha256(prototype_bytes).hexdigest()

    if not bool(sfmApp.HasDocument()):
        raise CheckpointF1R6Error("No SFM document is open.")

    root_for_filename = sfmApp.GetDocumentRoot()
    if root_for_filename is None:
        raise CheckpointF1R6Error("sfmApp.GetDocumentRoot() returned None.")
    open_file_id = root_for_filename.GetFileId()
    open_path = vs.g_pDataModel.GetFileName(open_file_id)
    open_basename = os.path.basename(b_to_unicode(open_path)) if open_path else u""

    check(
        "fixture.refuses_original_fixture_filename",
        open_basename.lower() != FORBIDDEN_ORIGINAL_FIXTURE_FILENAME.lower(),
        open_basename,
    )
    check(
        "fixture.matches_expected_normalized_copy_filename",
        open_basename.lower() == EXPECTED_NORMALIZED_COPY_FILENAME.lower(),
        open_basename,
    )
    if open_basename.lower() == FORBIDDEN_ORIGINAL_FIXTURE_FILENAME.lower():
        raise CheckpointF1R6Error(
            "REFUSING TO RUN against the original disposable qualification fixture (%r)." % (open_basename,)
        )
    if open_basename.lower() != EXPECTED_NORMALIZED_COPY_FILENAME.lower():
        raise CheckpointF1R6Error(
            "Open document (%r) does not match the expected normalized-copy filename (%r)."
            % (open_basename, EXPECTED_NORMALIZED_COPY_FILENAME)
        )

    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointF1R6Error("Starting-state fixture gate failed -- aborting before any production invocation.")

    main_window = sfmApp.GetMainWindow()
    check("f1r6.main_window_available", main_window is not None)
    write_rolling_evidence()

    prod_ns = {}
    try:
        exec(compile(production_bytes, "<installed_production_normalizer_f1r6>", "exec"), prod_ns)
    except Exception as exc:
        anomaly("Production Normalizer execution raised: %r" % (exc,))
        anomaly(traceback.format_exc())

    native_ptr = prod_ns.get("native_ptr")
    contextualizer_process_memory_sample = prod_ns.get("contextualizer_process_memory_sample")
    contextualizer_virtual_address_sample = prod_ns.get("contextualizer_virtual_address_sample")
    legacy_discover_rig_context = prod_ns.get("discover_rig_context")
    legacy_handle = prod_ns.get("handle")
    legacy_typ = prod_ns.get("typ")
    legacy_arr = prod_ns.get("arr")
    legacy_scalar = prod_ns.get("scalar")
    legacy_element_ref_pairs = prod_ns.get("element_ref_pairs")
    legacy_name = prod_ns.get("name")
    legacy_to_unicode = prod_ns.get("to_unicode")
    legacy_probe_error = prod_ns.get("ProbeError")

    for required_name, required_value in (
        ("native_ptr", native_ptr),
        ("contextualizer_process_memory_sample", contextualizer_process_memory_sample),
        ("contextualizer_virtual_address_sample", contextualizer_virtual_address_sample),
        ("discover_rig_context", legacy_discover_rig_context),
        ("handle", legacy_handle),
        ("typ", legacy_typ),
        ("arr", legacy_arr),
        ("scalar", legacy_scalar),
        ("element_ref_pairs", legacy_element_ref_pairs),
        ("name", legacy_name),
        ("to_unicode", legacy_to_unicode),
        ("ProbeError", legacy_probe_error),
    ):
        if required_value is None:
            raise CheckpointF1R6Error("Required production name not found in exec'd namespace: %s" % required_name)

    run_lock_name = prod_ns.get("RUN_LOCK_NAME")
    if run_lock_name is None:
        raise CheckpointF1R6Error("RUN_LOCK_NAME not found in exec'd namespace.")

    for child in main_window.findChildren(QtCore.QObject):
        try:
            if b_to_unicode(child.objectName()) == run_lock_name:
                instance = child
                break
        except Exception:
            continue

    check("f1r6.run_instance_located", instance is not None)
    if instance is None:
        raise CheckpointF1R6Error("Could not locate the already-constructed run instance immediately after exec().")

    # Neutralize the real instance's own further progression BEFORE ever
    # pumping the Qt event loop -- identical technique to F1-R3/F1-R4/
    # F1-R5. This checkpoint never pumps events at all (no native
    # Rebuild, no shot activation), so this is a pure safety measure.
    instance.finished = True
    check("f1r6.real_instance_neutralized", bool(instance.finished))

    work = instance.work
    check("f1r6.instance_work_present", bool(work))

    total_shots_in_work = len(work)
    total_targets_in_work = sum(len(r["targets"]) for r in work)

    check("gate.total_shots_matches_expected", total_shots_in_work == EXPECTED_TOTAL_SHOTS, total_shots_in_work)
    check("gate.total_eligible_native_targets_matches_expected", total_targets_in_work == EXPECTED_ELIGIBLE_NATIVE_TARGETS, total_targets_in_work)

    static_skips = getattr(instance, "total_gate_static_skips", None)
    follower_skips = getattr(instance, "total_gate_follower_skips", None)
    lowbone_skips = getattr(instance, "total_gate_lowbone_skips", None)
    failclosed = getattr(instance, "total_gate_failclosed_process", None)
    model_backed = getattr(instance, "total_model_backed", None)

    check("gate.static_skips_matches_expected", static_skips == EXPECTED_GATE_STATIC_SKIPS, static_skips)
    check("gate.follower_skips_matches_expected", follower_skips == EXPECTED_GATE_FOLLOWER_SKIPS, follower_skips)
    check("gate.lowbone_skips_matches_expected", lowbone_skips == EXPECTED_GATE_LOWBONE_SKIPS, lowbone_skips)
    check("gate.failclosed_process_matches_expected", failclosed == EXPECTED_GATE_FAILCLOSED_PROCESS, failclosed)
    check("gate.model_backed_matches_expected", model_backed == EXPECTED_MODEL_BACKED_TARGETS, model_backed)

    discovery_fn = None
    if mode == MODE_LEGACY:
        # No candidate_ns is created and no prototype bytes are exec()'d
        # anywhere in this branch -- a LEGACY run's own resource profile is
        # never contaminated by candidate module loading.
        discovery_fn = legacy_discover_rig_context
        check("f1r6.legacy_mode_never_loads_candidate_prototype", prototype_bytes is None, prototype_bytes is None)
    else:
        # Load the candidate prototype, wired to the SAME extracted legacy
        # helpers -- guarantees the candidate calls the identical native-
        # bound functions legacy itself uses. No production import
        # redirected; no monkey-patching of production behavior; this is a
        # completely separate, standalone namespace. This exec() (and its
        # own resource footprint) happens ONLY in STREAMING_CANDIDATE mode,
        # so it never contaminates a LEGACY-mode run's own resource
        # profile.
        candidate_ns = {
            "handle": legacy_handle,
            "typ": legacy_typ,
            "arr": legacy_arr,
            "scalar": legacy_scalar,
            "element_ref_pairs": legacy_element_ref_pairs,
            "name": legacy_name,
            "to_unicode": legacy_to_unicode,
            "ProbeError": legacy_probe_error,
        }
        exec(compile(prototype_bytes, "<f1r6_streaming_prototype>", "exec"), candidate_ns)
        candidate_discover_rig_context = candidate_ns.get("discover_rig_context_streaming")
        check("f1r6.candidate_prototype_loaded", callable(candidate_discover_rig_context))
        if not callable(candidate_discover_rig_context):
            raise CheckpointF1R6Error("Candidate prototype did not define discover_rig_context_streaming.")
        discovery_fn = candidate_discover_rig_context

    write_rolling_evidence()

    before_memory = contextualizer_process_memory_sample()
    before_vas = contextualizer_virtual_address_sample()
    instance.contextualizer_resource_checkpoint("F1R6_CP0_START", True)
    report["memory_snapshots"] = {"before": {"memory": before_memory, "vas": before_vas}}
    write_rolling_evidence()

    ordered_targets = []
    for shot_record in work:
        for target in shot_record["targets"]:
            ordered_targets.append((shot_record, target))

    arm_private_delta_sum = 0
    arm_working_set_delta_sum = 0
    total_elapsed_seconds = 0.0
    total_discovery_calls = 0
    status_counts = {}

    for target_index, (shot_record, target) in enumerate(ordered_targets):
        shot_name = b_to_unicode(shot_record["name"])
        target_name = b_to_unicode(target["name"])
        shot = shot_record["shot"]
        aset = target["anim_set"]

        mem_before = contextualizer_process_memory_sample()
        t0 = time.time()
        result = discovery_fn(shot, aset)
        elapsed = time.time() - t0
        mem_after = contextualizer_process_memory_sample()

        private_delta = None
        working_set_delta = None
        try:
            private_delta = mem_after["private"] - mem_before["private"]
            working_set_delta = mem_after["working_set"] - mem_before["working_set"]
            arm_private_delta_sum += private_delta
            arm_working_set_delta_sum += working_set_delta
        except Exception:
            pass

        total_elapsed_seconds += elapsed
        total_discovery_calls += 1

        status_value = result.get("status")
        status_counts[status_value] = status_counts.get(status_value, 0) + 1

        owned_handles_value = result.get("owned_handles")
        try:
            owned_handles_sorted = sorted(owned_handles_value) if owned_handles_value is not None else None
        except Exception:
            owned_handles_sorted = list(owned_handles_value) if owned_handles_value is not None else None

        record = {
            "target_index": target_index,
            "shot": shot_name,
            "target": target_name,
            "status": status_value,
            "is_ambiguous_status": bool(status_value and "AMBIGUOUS" in status_value),
            "reachable_rig_count": result.get("reachable_rig_count"),
            "matching_rig_count": result.get("matching_rig_count"),
            "rig_handle": result.get("rig_handle"),
            "registry_handle": result.get("registry_handle"),
            "owned_handles": owned_handles_sorted,
            "owned_names_in_order": result.get("owned_names_in_order"),
            "hidden_groups": result.get("hidden_groups"),
            "elapsed_seconds": elapsed,
            "private_delta": private_delta,
            "working_set_delta": working_set_delta,
        }
        report["targets_processed"].append(record)

        if (target_index + 1) % VAS_CHECKPOINT_STRIDE == 0 or target_index == len(ordered_targets) - 1:
            instance.contextualizer_resource_checkpoint(
                "F1R6_CP_TARGET_%d_OF_%d" % (target_index + 1, len(ordered_targets)),
                True,
            )
            write_rolling_evidence()

    check("arm.all_62_targets_recorded", total_discovery_calls == EXPECTED_ELIGIBLE_NATIVE_TARGETS, total_discovery_calls)
    check("neutralization.real_pipeline_never_advanced", getattr(instance, "total_shots_processed", 0) == 0, getattr(instance, "total_shots_processed", None))

    report["arm_summary"] = {
        "mode": mode,
        "total_discovery_calls": total_discovery_calls,
        "total_elapsed_seconds": total_elapsed_seconds,
        "arm_private_delta_sum": arm_private_delta_sum,
        "arm_working_set_delta_sum": arm_working_set_delta_sum,
        "status_counts": status_counts,
    }

    instance.contextualizer_resource_checkpoint("F1R6_CP_FINAL_TARGET_COMPLETE", True)

    after_memory = contextualizer_process_memory_sample()
    after_vas = contextualizer_virtual_address_sample()
    instance.contextualizer_resource_checkpoint("F1R6_TEARDOWN_BEFORE_GC", True)

    gc.collect()

    postgc_memory = contextualizer_process_memory_sample()
    postgc_vas = contextualizer_virtual_address_sample()
    instance.contextualizer_resource_checkpoint("F1R6_TEARDOWN_AFTER_GC", True)

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
        "postgc_private_delta": _delta(postgc_memory, before_memory, "private"),
        "postgc_free_vas_delta": _delta(postgc_vas, before_vas, "free"),
        "postgc_largest_free_delta": _delta(postgc_vas, before_vas, "largest_free"),
    }

    check("resource.before_after_gc_deltas_captured", report["resource_deltas"]["private_delta"] is not None)

    try:
        with open(NORMALIZER_LOG_PATH, "rb") as f:
            log_bytes = f.read()
        preserve_ok, preserve_err = write_text_atomic(production_log_preserve_path, log_bytes)
        if not preserve_ok:
            anomaly("Could not preserve production log: %s" % preserve_err)
    except Exception as exc:
        anomaly("Could not read production log: %r" % (exc,))

except CheckpointF1R6Error as gate_exc:
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

if json_output_path is None:
    # Mode was never successfully selected -- fall back to a fixed path so
    # SOME evidence of the failure is preserved.
    json_output_path = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r6_mode_selection_failed_result.json"
    summary_output_path = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r6_mode_selection_failed_summary.txt"

json_write_ok, json_write_error, _r = write_json_atomic(json_output_path, report)
if not json_write_ok:
    anomaly("Final JSON write failed: %s" % json_write_error)

summary_lines = []
summary_lines.append("SFM CHECKPOINT F1-R6 -- FRESH STREAMING DISCOVERY PARITY (mode=%s)" % (mode,))
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
if report.get("gate_failure"):
    summary_lines.append("*** GATE FAILURE ***")
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
if "arm_summary" in report:
    summary_lines.append("arm_summary=%r" % (report["arm_summary"],))
if "resource_deltas" in report:
    summary_lines.append("resource_deltas=%r" % (report["resource_deltas"],))
summary_lines.append("")
summary_lines.append("OVERALL_PASS=%r" % report["overall_pass"])
summary_lines.append("")
summary_lines.append("--- ANOMALIES (%d) ---" % len(ANOMALIES))
for a in ANOMALIES:
    summary_lines.append("- %s" % a)
if not ANOMALIES:
    summary_lines.append("(none)")
summary_lines.append("")
summary_lines.append("json_output_path=%s (write_ok=%r)" % (json_output_path, json_write_ok))
summary_lines.append("")
summary_lines.append(
    "This is ONE arm only (mode=%s). The OTHER arm must be measured by a "
    "SEPARATE fresh SFM process run. Semantic and resource comparison "
    "happens OFFLINE, via F1_R6_Compare_Legacy_vs_Streaming_Results.py, "
    "once BOTH mode-specific JSON artifacts exist." % (mode,)
)

summary_text = u"\n".join(summary_lines) + u"\n"
summary_write_ok, summary_write_error = write_text_atomic(summary_output_path, summary_text.encode("ascii", "replace"))

try:
    sys.stdout.write(summary_text.encode("ascii", "replace"))
    sys.stdout.write(
        "\nCheckpoint F1-R6 (mode=%s) reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n"
        % (mode, json_output_path, json_write_ok, summary_output_path, summary_write_ok)
    )
    sys.stdout.write("\nThis checkpoint never mutated the scene. DO NOT SAVE anyway, per standing discipline. Restart SFM afterward.\n")
except Exception:
    pass
