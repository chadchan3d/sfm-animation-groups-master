# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint F1-R2, Phase 1: Create
Normalized Diagnostic Copy.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: **THIS CHECKPOINT MUTATES THE SCENE AND SAVES A NEW FILE.**
This is an INTENTIONAL, EXPLICIT exception to this whole project's normal
"DO NOT SAVE" rule -- justified because Phase 2 of this diagnostic
requires a genuinely fresh SFM process loading an ALREADY-NORMALIZED
scene from disk, which is only possible if such a file exists.

**This script NEVER overwrites the original disposable qualification
fixture.** It saves to a NEW, clearly-named file
(`F1_R2_NORMALIZED_DIAGNOSTIC_COPY.sfm`, see SAVE_AS_TARGET_PATH below) via
an explicit Save-As-style call, never a plain re-save of the currently
open document.

Purpose:
  Checkpoint F1-2's own confirmed evidence showed production's All-Shots
  command 3 growing ~227.32 MiB private / losing ~222.44 MiB free VAS /
  ~105.88 MiB largest-contiguous-block WITHIN ITS OWN SINGLE RUN (CP0_
  COMMAND_START vs its own FINAL_REPORT_ENTRY) -- this is production-
  internal, not harness-caused (F1-2 had already eliminated the harness's
  own whole-85-target capture that F1-R1 identified). Command 4 then
  failed to produce any completed record at all, consistent with running
  out of the already-reduced headroom command 3 left behind.

  This diagnostic exists to separate two hypotheses (see
  `../checkpoint_f1_2/F1-2_PRODUCTION_INTERNAL_STATIC_AUDIT.md` for the
  accompanying static trace): (A) SCENE-RESIDENT structural growth -- the
  first All-Shots run legitimately makes the scene itself bigger/more
  complex, and this growth would already be represented in a saved,
  reloaded copy of the normalized scene; vs. (B) PER-RUN NATIVE/allocator
  retention -- growth that is an artifact of the Rebuild process itself
  and would recur on every run regardless of prior normalization state.

  Phase 1 (this script) creates the normalized copy needed to test this.
  Phase 2 (a separate script, run after a full SFM restart against ONLY
  this new copy) performs the actual comparison.

Sequence (this script):
  1. Confirm the original disposable qualification fixture is open (the
     operator must have opened it before running this script).
  2. Record idle/process memory/VAS (this harness's own ctypes sampler).
  3. Run production All Shots ONCE with the LIGHTEST possible harness:
     - no external whole-85 semantic capture before the run;
     - no D1/D2-scale verification of any kind;
     - only production resource checkpoints, authority lifecycle,
       provenance (SHA checks), and a bounded structural witness (totals/
       counts only, no rig-tree walk) are captured.
  4. Require production completion.
  5. Record FINAL_REPORT_ENTRY memory/VAS (parsed from production's own
     pre-existing log, same technique as F1-R1/F1-2).
  6. Save As a new file (never overwriting the original fixture).
  7. Record the saved file's path, size, and save success/failure.
  8. Write phase-1 evidence to disk BEFORE the operator restarts SFM for
     Phase 2 (this script's own finalize section, not deferred).

Do NOT run Phase 2 from this same SFM process. A full restart is required
between phases (this is Phase 2's own operator instruction).

Output:
  C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r2_phase1_result.json
  C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r2_phase1_result_summary.txt
  C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r2_phase1_production_log.txt
    (a byte-for-byte preserved copy of production's own log for this run)
"""
import gc
import hashlib
import json
import os
import sys
import time
import traceback

from PySide import QtCore
import vs

# ---------------------------------------------------------------------------
# Pinned identities.
# ---------------------------------------------------------------------------

EXPECTED_PRODUCTION_NORMALIZER_SHA256 = (
    "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"
)
EXPECTED_CANONICAL_MASTER_SHA256 = (
    "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
)
EXPECTED_TOTALS = {
    "total_shots": 15,
    "total_targets": 163,
    "eligible_targets": 85,
    "excluded_targets": 78,
    "distinct_model_names": 22,
    "distinct_fold_vocabulary_hashes_among_eligible": 21,
}

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r2_phase1_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r2_phase1_result_summary.txt"
PRODUCTION_LOG_PRESERVE_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r2_phase1_production_log.txt"

# The new diagnostic copy's save target. Never the original fixture path.
# A plain, unambiguous filename inside the same disposable-projects
# directory the operator's original fixture already lives in, so Phase 2
# can be pointed at it manually.
SAVE_AS_FILENAME = u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.sfm"

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


class CheckpointF1R2Phase1Error(Exception):
    pass


ANOMALIES = []


def anomaly(message):
    ANOMALIES.append(message)
    try:
        sys.stdout.write("ANOMALY: %s\n" % message)
    except Exception:
        pass


def b_native_ptr(obj):
    if obj is None:
        return None
    try:
        return long(obj.this)
    except Exception:
        try:
            return int(obj.this)
        except Exception:
            return None


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


def b_name(obj):
    try:
        return b_to_unicode(obj.GetName())
    except Exception:
        return u"<UNNAMED>"


def b_typ(obj):
    try:
        return b_to_unicode(obj.GetTypeString())
    except Exception:
        try:
            return b_to_unicode(obj.__class__.__name__)
        except Exception:
            return u"<UNKNOWN_TYPE>"


def b_attr(obj, attr_name):
    try:
        return obj.GetAttribute(attr_name)
    except Exception:
        return None


def b_scalar(obj, attr_name):
    a = b_attr(obj, attr_name)
    if a is not None:
        try:
            return a.GetValue()
        except Exception:
            pass
    try:
        return getattr(obj, attr_name)
    except Exception:
        return None


def b_arr(obj, attr_name):
    a = b_attr(obj, attr_name)
    if a is None:
        return []
    try:
        count = int(a.Count())
    except Exception:
        try:
            count = len(a)
        except Exception:
            return []
    out = []
    for i in xrange(count):
        try:
            out.append(a[i])
        except Exception:
            try:
                out.append(a.GetValue(i))
            except Exception:
                raise CheckpointF1R2Phase1Error(
                    "Cannot read %s[%d] on %r." % (attr_name, i, b_name(obj))
                )
    return out


def b_get_game_model(aset):
    try:
        if not aset.HasAttribute("gameModel"):
            return None
    except Exception:
        return None
    try:
        game_model = aset.gameModel
    except Exception:
        return None
    if game_model is None or not b_native_ptr(game_model):
        return None
    return game_model


def b_get_model_name(game_model):
    for attr_name in ("modelName", "modelPath", "fileName", "filename", "model"):
        value = b_scalar(game_model, attr_name)
        if value is None:
            continue
        text = b_to_unicode(value).strip()
        if text:
            return text
    return None


def b_get_root_group(aset):
    try:
        return aset.GetRootControlGroup()
    except Exception:
        return None


def build_bounded_witness_totals():
    """Bounded structural witness -- classification/counts ONLY, no
    rig-tree walk, no semantic fingerprinting. Deliberately does not
    reuse capture_snapshot_explicit() at all, per this phase's explicit
    'no external whole-85 semantic capture' constraint."""
    if not bool(sfmApp.HasDocument()):
        return None, "No SFM document is open."

    all_shots = list(sfmApp.GetShots())
    if not all_shots:
        return None, "sfmApp.GetShots() returned zero shots."

    global_aset_ptr_seen = set()
    total_targets = 0
    eligible = 0
    excluded = 0
    model_names = set()

    for shot in all_shots:
        try:
            animation_sets = list(shot.animationSets)
        except Exception:
            animation_sets = []
        for aset in animation_sets:
            total_targets += 1
            aset_ptr = b_native_ptr(aset)
            is_duplicate = aset_ptr is not None and aset_ptr in global_aset_ptr_seen
            if aset_ptr is not None:
                global_aset_ptr_seen.add(aset_ptr)
            game_model = b_get_game_model(aset)
            model_backed = game_model is not None
            model_name = b_get_model_name(game_model) if model_backed else None
            root_group = b_get_root_group(aset)
            root_valid = bool(root_group is not None and b_native_ptr(root_group))
            target_eligible = bool(model_backed and root_valid and not is_duplicate)
            if target_eligible:
                eligible += 1
                if model_name:
                    model_names.add(model_name)
            else:
                excluded += 1

    totals = {
        "total_shots": len(all_shots),
        "total_targets": total_targets,
        "eligible_targets": eligible,
        "excluded_targets": excluded,
        "distinct_model_names": len(model_names),
    }
    return totals, None


def memory_snapshot():
    try:
        import ctypes
        import ctypes.wintypes

        class _ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.wintypes.DWORD),
                ("PageFaultCount", ctypes.wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = _ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(_ProcessMemoryCounters)
        process_handle = ctypes.windll.kernel32.GetCurrentProcess()
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(process_handle, ctypes.byref(counters), counters.cb)
        if not ok:
            return {"available": False, "error": "GetProcessMemoryInfo returned FALSE"}
        return {
            "available": True,
            "working_set_bytes": int(counters.WorkingSetSize),
            "peak_working_set_bytes": int(counters.PeakWorkingSetSize),
            "pagefile_usage_bytes": int(counters.PagefileUsage),
            "peak_pagefile_usage_bytes": int(counters.PeakPagefileUsage),
        }
    except Exception as exc:
        return {"available": False, "error": repr(exc)}


_CHECKPOINT_MARKER = "CONTEXTUALIZER_RESOURCE_CHECKPOINT "


def _typed_checkpoint_value(raw):
    if raw == "None":
        return None
    if raw == "True":
        return True
    if raw == "False":
        return False
    v = raw
    if v.endswith("L") and v[:-1].lstrip("-").isdigit():
        v = v[:-1]
    try:
        return int(v)
    except Exception:
        pass
    try:
        return float(v)
    except Exception:
        pass
    return raw


def parse_resource_checkpoint_line(line):
    idx = line.find(_CHECKPOINT_MARKER)
    if idx < 0:
        return None
    body = line[idx + len(_CHECKPOINT_MARKER):].rstrip("\r\n")
    vas_error_idx = body.find("vas_error=")
    if vas_error_idx >= 0:
        head = body[:vas_error_idx]
        vas_error_raw = body[vas_error_idx + len("vas_error="):]
    else:
        head = body
        vas_error_raw = None
    fields = {}
    for token in head.split(" "):
        if not token or "=" not in token:
            continue
        k, _sep, v = token.partition("=")
        fields[k] = _typed_checkpoint_value(v)
    fields["vas_error_raw"] = vas_error_raw
    return fields


def parse_all_resource_checkpoints(log_text):
    out = []
    for line in log_text.splitlines():
        parsed = parse_resource_checkpoint_line(line)
        if parsed is not None:
            out.append(parsed)
    return out


def summarize_resource_checkpoints(log_text):
    checkpoints = parse_all_resource_checkpoints(log_text)
    if not checkpoints:
        return {
            "checkpoint_count": 0,
            "first_checkpoint": None,
            "last_checkpoint": None,
            "final_report_entry_reached": False,
        }
    return {
        "checkpoint_count": len(checkpoints),
        "first_checkpoint": checkpoints[0],
        "last_checkpoint": checkpoints[-1],
        "final_report_entry_reached": any(
            c.get("label") == "FINAL_REPORT_ENTRY" for c in checkpoints
        ),
    }


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


def save_normalized_diagnostic_copy(save_as_filename):
    """Saves the CURRENTLY OPEN document to a NEW path -- never the
    original fixture's own path. Uses the real, evidence-grounded SFM/
    Source-SDK DataModel Save-As API (confirmed via direct reading of
    the bundled vs/datamodel.py SWIG stub and real usage in
    sdktools/python/global/Scripts/cleanEmptyControls.py):

        root = sfmApp.GetDocumentRoot()
        file_id = root.GetFileId()
        original_path = vs.g_pDataModel.GetFileName(file_id)
        format_name = vs.g_pDataModel.GetFileFormat(file_id)
        vs.g_pDataModel.SaveToFile(new_path, None, "binary", format_name, root)

    `SaveToFile`'s first argument is an ARBITRARY target path, independent
    of the currently-open file's own path -- true Save-As semantics, not
    a re-save. The encoding ("binary") and format are copied from
    cleanEmptyControls.py's own real call site rather than guessed; the
    format string is derived from the ACTUAL currently-loaded file via
    `GetFileFormat(file_id)`, not hardcoded, so it matches whatever
    format this real .sfm project actually uses.

    Returns a dict describing the outcome. Never raises -- a failure is
    reported in the returned dict, not propagated."""
    result = {
        "ok": False,
        "original_path": None,
        "target_path": None,
        "target_differs_from_original": None,
        "target_exists_before_save": None,
        "target_size_after_save": None,
        "error": None,
    }
    try:
        root = sfmApp.GetDocumentRoot()
        if root is None:
            result["error"] = "sfmApp.GetDocumentRoot() returned None"
            return result
        file_id = root.GetFileId()
        original_path = vs.g_pDataModel.GetFileName(file_id)
        result["original_path"] = original_path
        format_name = vs.g_pDataModel.GetFileFormat(file_id)

        original_dir = os.path.dirname(os.path.abspath(original_path)) if original_path else None
        if not original_dir:
            result["error"] = "could not determine original file's directory from GetFileName()"
            return result
        target_path = os.path.join(original_dir, save_as_filename)
        result["target_path"] = target_path

        target_differs = bool(
            os.path.normcase(os.path.abspath(target_path))
            != os.path.normcase(os.path.abspath(original_path))
        )
        result["target_differs_from_original"] = target_differs
        if not target_differs:
            result["error"] = (
                "REFUSING TO SAVE: computed target path equals the original fixture's "
                "own path -- this must never happen."
            )
            return result

        result["target_exists_before_save"] = os.path.exists(target_path)

        save_ok = bool(
            vs.g_pDataModel.SaveToFile(target_path, None, "binary", format_name, root)
        )
        result["ok"] = save_ok
        if save_ok:
            try:
                result["target_size_after_save"] = os.path.getsize(target_path)
            except Exception as exc:
                result["target_size_after_save_error"] = repr(exc)
        else:
            result["error"] = "vs.g_pDataModel.SaveToFile() returned False"
    except Exception as exc:
        result["error"] = repr(exc)
    return result


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

report = {
    "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "python_version": sys.version,
    "checks": [],
    "anomalies": ANOMALIES,
    "provenance": {},
    "memory_snapshots": {},
    "production_run": {},
    "save_result": {},
    "in_progress": True,
}


def check(name, condition, detail=None):
    report["checks"].append({"name": name, "pass": bool(condition), "detail": repr(detail) if detail is not None else None})
    try:
        sys.stdout.write("[%s] %s%s\n" % ("PASS" if condition else "FAIL", name, ("" if detail is None else " -- %r" % (detail,))))
    except Exception:
        pass


def write_rolling_evidence():
    ok, err, _reparsed = write_json_atomic(JSON_OUTPUT_PATH, report)
    if not ok:
        anomaly("Rolling evidence write failed (run continues): %s" % (err,))
    return ok


main_window = None
production_bytes = None

try:
    report["memory_snapshots"]["idle_before_run"] = memory_snapshot()

    with open(PRODUCTION_NORMALIZER_PATH, "rb") as f:
        production_bytes = f.read()
    production_sha = hashlib.sha256(production_bytes).hexdigest()
    check("production_normalizer.sha256_matches_accepted_integration", production_sha == EXPECTED_PRODUCTION_NORMALIZER_SHA256, production_sha)

    with open(CANONICAL_MASTER_PATH, "rb") as f:
        master_bytes = f.read()
    master_sha = hashlib.sha256(master_bytes).hexdigest()
    check("canonical_master.sha256_unchanged", master_sha == EXPECTED_CANONICAL_MASTER_SHA256, master_sha)

    if not (production_sha == EXPECTED_PRODUCTION_NORMALIZER_SHA256
            and master_sha == EXPECTED_CANONICAL_MASTER_SHA256):
        raise CheckpointF1R2Phase1Error("One or more pre-flight SHA-256 checks failed -- refusing to proceed.")

    report["provenance"]["production_normalizer_sha256"] = production_sha
    report["provenance"]["canonical_master_sha256"] = master_sha

    # --- Bounded structural witness only -- NO external whole-85
    #     semantic capture in this phase. ---
    totals, witness_error = build_bounded_witness_totals()
    if witness_error is not None:
        raise CheckpointF1R2Phase1Error("Could not build bounded witness: %s" % witness_error)
    report["fixture_totals"] = totals
    for key, expected_value in EXPECTED_TOTALS.items():
        if key == "distinct_fold_vocabulary_hashes_among_eligible":
            continue  # requires per-target control-name folding; out of scope for the bounded witness
        actual_value = totals.get(key)
        check("fixture.totals.%s_matches_required" % key, actual_value == expected_value, (actual_value, expected_value))

    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointF1R2Phase1Error(
            "STARTING-STATE / FIXTURE MISMATCH -- aborting BEFORE any invocation of the "
            "production Normalizer or scene mutation."
        )

    main_window = sfmApp.GetMainWindow()
    check("normalizer.main_window_available", main_window is not None)

    write_rolling_evidence()

    # --- Run production All Shots ONCE. ---
    report["memory_snapshots"]["before_production_run"] = memory_snapshot()
    command_start_time = time.time()
    prod_ns = {}
    run_started = False
    run_completed_cleanly = False
    try:
        exec(compile(production_bytes, "<installed_production_normalizer_f1r2_phase1>", "exec"), prod_ns)
    except Exception as exc:
        anomaly("Production Normalizer execution raised: %r" % exc)
        anomaly(traceback.format_exc())

    run_lock_name = prod_ns.get("RUN_LOCK_NAME")

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

    active_now = normalizer_run_is_active()
    if active_now:
        run_started = True
        sys.stdout.write(
            "\n>>> Choose 'All Shots' in the real dialog that just appeared. <<<\n\n"
        )
        wait_start = time.time()
        MAX_WAIT_SECONDS = 1800
        while normalizer_run_is_active():
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.05)
            if time.time() - wait_start > MAX_WAIT_SECONDS:
                anomaly("Production run did not complete within %d seconds -- aborting wait." % MAX_WAIT_SECONDS)
                break
        else:
            run_completed_cleanly = True
        settle_start = time.time()
        while time.time() - settle_start < 1.0:
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.05)
    else:
        anomaly(
            "No run-lock was ever observed active after executing the production "
            "Normalizer source -- this most likely means the operator cancelled the "
            "scope dialog."
        )

    command_duration_seconds = time.time() - command_start_time
    check("production_run.run_was_started", run_started)
    check("production_run.run_completed_within_timeout", run_completed_cleanly if run_started else False)

    # --- Read production's own log: native-protection markers, resource
    #     checkpoints, preserve a byte-for-byte copy. ---
    native_evidence = {}
    resource_checkpoint_summary = {"checkpoint_count": 0, "first_checkpoint": None, "last_checkpoint": None, "final_report_entry_reached": False}
    try:
        with open(NORMALIZER_LOG_PATH, "rb") as f:
            log_bytes = f.read()
        log_text = log_bytes.decode("ascii", "replace")
        native_evidence["log_size_bytes"] = len(log_bytes)
        native_evidence["contains_NATIVE_GUARDS_PASS"] = ("NATIVE_GUARDS = PASS" in log_text)
        native_evidence["contains_NATIVE_REBUILD_RETURNED_PASS"] = ("NATIVE_REBUILD_RETURNED = PASS" in log_text)
        resource_checkpoint_summary = summarize_resource_checkpoints(log_text)
        preserve_ok, preserve_err = write_text_atomic(PRODUCTION_LOG_PRESERVE_PATH, log_bytes)
        if not preserve_ok:
            anomaly("Could not preserve a copy of the production log: %s" % preserve_err)
        del log_bytes, log_text
    except Exception as exc:
        native_evidence["log_read_ok"] = False
        native_evidence["log_read_error"] = repr(exc)
        anomaly("Could not read production Normalizer log for evidence: %r" % exc)

    check("production_run.native_guards_pass", native_evidence.get("contains_NATIVE_GUARDS_PASS") is True, native_evidence.get("contains_NATIVE_GUARDS_PASS"))
    check("production_run.native_rebuild_returned_pass", native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS") is True, native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS"))
    check("production_run.final_report_entry_reached", resource_checkpoint_summary.get("final_report_entry_reached") is True, resource_checkpoint_summary.get("final_report_entry_reached"))

    # --- Authority lifecycle evidence (existing qualified diagnostics only). ---
    authority_evidence = {}
    try:
        authority_runtime = prod_ns.get("authority_runtime")
        authority_evidence["module_binding_present"] = authority_runtime is not None
        if authority_runtime is not None:
            try:
                authority_evidence["runtime_api_version"] = authority_runtime.RUNTIME_API_VERSION
            except Exception as exc:
                authority_evidence["runtime_api_version_error"] = repr(exc)
            try:
                authority_evidence["runtime_build_id"] = authority_runtime.RUNTIME_BUILD_ID
            except Exception as exc:
                authority_evidence["runtime_build_id_error"] = repr(exc)
            try:
                authority_evidence["is_canonical"] = bool(authority_runtime.is_canonical())
            except Exception as exc:
                authority_evidence["is_canonical_error"] = repr(exc)
            try:
                authority_evidence["get_state"] = authority_runtime.get_state()
            except Exception as exc:
                authority_evidence["get_state_error"] = repr(exc)
            try:
                expected_api_version = prod_ns.get("_AUTHORITY_EXPECTED_API_VERSION")
                expected_build_id = prod_ns.get("_AUTHORITY_EXPECTED_BUILD_ID")
                broker = authority_runtime.get_broker(
                    expected_api_version=expected_api_version,
                    expected_build_id=expected_build_id,
                    is_main_thread_fn=lambda: (
                        QtCore.QThread.currentThread()
                        is QtCore.QCoreApplication.instance().thread()
                    ),
                )
                authority_evidence["broker_acquired_idempotently"] = broker is not None
                try:
                    authority_evidence["provider_counters"] = broker.provider_counters()
                except Exception as exc:
                    authority_evidence["provider_counters_error"] = repr(exc)
                try:
                    authority_evidence["outstanding_lease_count"] = broker.outstanding_lease_count()
                except Exception as exc:
                    authority_evidence["outstanding_lease_count_error"] = repr(exc)
            except Exception as exc:
                authority_evidence["broker_query_error"] = repr(exc)
    except Exception as exc:
        authority_evidence["capture_error"] = repr(exc)
        anomaly("Authority runtime evidence capture raised: %r" % exc)

    check("production_run.authority_broker_ready", authority_evidence.get("get_state") == "READY", authority_evidence.get("get_state"))
    check("production_run.authority_canonical", authority_evidence.get("is_canonical") is True, authority_evidence.get("is_canonical"))
    check("production_run.zero_outstanding_leases_after", authority_evidence.get("outstanding_lease_count") == 0, authority_evidence.get("outstanding_lease_count"))

    report["production_run"] = {
        "duration_seconds": command_duration_seconds,
        "run_started": run_started,
        "run_completed_cleanly": run_completed_cleanly,
        "native_protection": native_evidence,
        "production_resource_checkpoints": resource_checkpoint_summary,
        "authority_lifecycle": authority_evidence,
    }

    del prod_ns
    try:
        del authority_runtime
    except Exception:
        pass
    try:
        del broker
    except Exception:
        pass
    gc.collect()
    report["memory_snapshots"]["after_production_run_gc_collect"] = memory_snapshot()
    write_rolling_evidence()

    # -------------------------------------------------------------------
    # Save As a NEW diagnostic copy. NEVER overwrites the original
    # fixture. See save_normalized_diagnostic_copy() for the exact API
    # call used and why.
    # -------------------------------------------------------------------
    save_result = save_normalized_diagnostic_copy(SAVE_AS_FILENAME)
    report["save_result"] = save_result
    check("save.succeeded", save_result.get("ok") is True, save_result)
    check("save.target_is_not_original_fixture_path", save_result.get("target_differs_from_original") is True, save_result.get("original_path"))
    write_rolling_evidence()

    report["memory_snapshots"]["after_save"] = memory_snapshot()

except CheckpointF1R2Phase1Error as gate_exc:
    anomaly("GATE FAILURE (orderly abort, no production Normalizer invocation attempted): %s" % gate_exc)
    report["gate_failure"] = True
except Exception as top_exc:
    anomaly("UNHANDLED TOP-LEVEL EXCEPTION: %s" % repr(top_exc))
    anomaly(traceback.format_exc())
    report["gate_failure"] = False
    try:
        report["memory_snapshots"]["at_unhandled_exception"] = memory_snapshot()
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Finalize / write output.
# ---------------------------------------------------------------------------

report["in_progress"] = False
report["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

all_checks_passed = all(c["pass"] for c in report["checks"]) if report["checks"] else False
completed_without_exception = not any(a.startswith("UNHANDLED TOP-LEVEL EXCEPTION") for a in ANOMALIES)
report["overall_pass"] = bool(all_checks_passed and completed_without_exception and report.get("save_result", {}).get("ok"))

json_write_ok, json_write_error, _reparsed = write_json_atomic(JSON_OUTPUT_PATH, report)

summary_lines = []
summary_lines.append("SFM CHECKPOINT F1-R2 PHASE 1 -- CREATE NORMALIZED DIAGNOSTIC COPY")
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
if report.get("gate_failure"):
    summary_lines.append("*** GATE FAILURE: aborted BEFORE any production Normalizer invocation or scene mutation. ***")
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
summary_lines.append("--- MEMORY SNAPSHOTS ---")
for k in sorted((report.get("memory_snapshots") or {}).keys()):
    summary_lines.append("  %s: %r" % (k, report["memory_snapshots"][k]))
summary_lines.append("")
rc = (report.get("production_run") or {}).get("production_resource_checkpoints") or {}
summary_lines.append("production first_checkpoint=%r" % (rc.get("first_checkpoint"),))
summary_lines.append("production last_checkpoint=%r" % (rc.get("last_checkpoint"),))
summary_lines.append("")
summary_lines.append("save_result=%r" % report.get("save_result"))
summary_lines.append("")
summary_lines.append("OVERALL_PASS=%r" % report["overall_pass"])
summary_lines.append("")
summary_lines.append("--- ANOMALIES (%d) ---" % len(ANOMALIES))
for a in ANOMALIES:
    summary_lines.append("- %s" % a)
if not ANOMALIES:
    summary_lines.append("(none)")
summary_lines.append("")
summary_lines.append("json_output_path=%s (write_ok=%r)" % (JSON_OUTPUT_PATH, json_write_ok))

summary_text = u"\n".join(summary_lines) + u"\n"
summary_write_ok, summary_write_error = write_text_atomic(SUMMARY_OUTPUT_PATH, summary_text.encode("ascii", "replace"))

try:
    sys.stdout.write(summary_text.encode("ascii", "replace"))
    sys.stdout.write(
        "\nPhase 1 reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok)
    )
    sys.stdout.write(
        "\nPhase 1 complete. Fully restart SFM, then open ONLY the new diagnostic copy "
        "(%r) and run Checkpoint_F1_R2_Phase2_Normalized_Copy_Retest.\n" % (SAVE_AS_FILENAME,)
    )
except Exception:
    pass
