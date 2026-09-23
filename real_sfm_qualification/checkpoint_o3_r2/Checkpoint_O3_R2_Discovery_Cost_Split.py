# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint O3-R2: Discovery Cost
Split Measurement.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: mutates the scene (normal Selected-Shots production
behavior, twice, in one continuous SFM process). Do not save afterward.

Purpose:
  O3-R1 concluded MORE_MEASUREMENT_REQUIRED for the sole remaining
  optimization candidate (outer native POST -> composer-before discovery
  substitution, "Option C": reuse only the expensive whole-scene
  reachable() traversal, freshly re-execute every discovery-derived
  validation read before composer writes). The unresolved question:

    Of the measured ~0.17-0.19s per discover_rig_context() call, how
    much belongs to the reusable whole-scene traversal (reachable())
    versus the fresh validation Option C must retain?

  This checkpoint answers that question by observationally splitting
  discover_rig_context()'s own internal cost into phases, using the
  EXACT same production code path, unmodified -- Option C is NOT
  implemented here. See O3_R2_DISCOVERY_PHASE_MAP.md for the exact
  phase-to-source-line mapping this instrumentation is built from, and
  O3_R2_MEASUREMENT_CONTRACT.md for the full reporting schema and
  decision thresholds.

Instrumentation is strictly OBSERVATIONAL. This script never edits
Rebuild_Control_Groups_Normalizer.py -- it exec()s the pinned, SHA-256
verified production bytes into a fresh namespace and monkey-patches
module-level helper functions in that IN-MEMORY namespace only, each
wrapper calling the ORIGINAL function with the SAME arguments and
returning its SAME, unmodified return value -- only recording timing
metadata. Call order, arguments, return values, exception behavior, Qt
timing, native calls, and scene mutations are all unchanged. The
production path still executes the COMPLETE, unmodified
discover_rig_context() -- this script never substitutes Option C's own
reduced-cost path.

Wrap points (extends O2-R1's own already-verified technique):
  1. discover_rig_context(shot, aset)  -- module function; own total
     elapsed time, status/counts, and a nesting depth flag that lets
     wraps 2-6 attribute their own timing to "inside discovery."
  2. reachable(start, max_elements=50000) -- module function; Phase 1
     (the one phase Option C proposes to skip).
  3. typ(obj) -- module function; Phase 2 (candidate filtering).
  4. arr(obj, attr_name) -- module function; bucketed by attr_name into
     Phase 4 ("animSetList"), Phase 6 ("controls"/"elementList"), or
     Phase 7 ("hiddenGroups").
  5. scalar(obj, attr_name) -- module function; Phase 4.
  6. handle(obj) -- module function; Phase 8 (aggregate).
  7. capture_snapshot_explicit(shot,aset,label,rig_context=None) --
     module function; label/target/branch correlation (same technique
     as O2/O2-R1), pops the most recently completed discovery's own
     phase-bucketed result off a small FIFO queue to associate it with
     this capture's own label.
  8. RebuildControlGroupsProductionRun.run_target_transaction -- class
     method; target-level timing/resource snapshots (same as O2-R1).
  9. <run_instance>.rebuild -- INSTANCE-attribute patch, applied
     immediately after exec() returns (O2-R1's own corrected fix for
     the native-Rebuild timing gap -- reused verbatim, same root-cause
     reasoning: exec() synchronously constructs the run instance and
     performs native-callback setup before returning control, so a
     class-level patch installed afterward would be too late).

Resource sampling is command-level only, reusing production's own
existing CONTEXTUALIZER_RESOURCE_CHECKPOINT log diagnostic -- no new
per-phase VirtualQuery or equivalent probe is introduced. This
checkpoint is CPU/time attribution, not a memory diagnostic.

Do not restart SFM between the two commands. Do not alter the scene
between commands.

Output (written incrementally after each command boundary):
  C:\\Users\\Public\\Documents\\sfm_checkpoint_o3r2_result.json
  C:\\Users\\Public\\Documents\\sfm_checkpoint_o3r2_result_summary.txt
  C:\\Users\\Public\\Documents\\sfm_checkpoint_o3r2_production_log_command{1,2}.txt

Do NOT save the SFM project after running this script.
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
EXPECTED_SELECTED_SHOT_NAME = u"shot3"
EXPECTED_SELECTED_TARGETS = {
    u"foxmccouldwm1": {
        "model_name": u"models/fursonas/foxmccouldwm.mdl",
        "control_count": 136,
        "fold_vocabulary_hash": "a2cff1af84fff4b1802aff5011c2de1d3739cabb88d86192d0245bf50a4d2f73",
    },
    u"mia1": {
        "model_name": u"models/annoad/foxbase/mia/mia.mdl",
        "control_count": 174,
        "fold_vocabulary_hash": "457f5093db427b0d4e15600c5cebb5e89da80f0dd1bd35ef8c1a8482b7b9b67d",
    },
}

COMMAND_SPECS = [
    (1, u"Selected Shots", u"fresh"),
    (2, u"Selected Shots", u"already_normalized"),
]

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_o3r2_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_o3r2_result_summary.txt"
PER_COMMAND_LOG_PRESERVE_TEMPLATE = (
    "C:\\Users\\Public\\Documents\\sfm_checkpoint_o3r2_production_log_command%d.txt"
)
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

# attr_name -> phase bucket, per O3_R2_DISCOVERY_PHASE_MAP.md
ARR_ATTR_TO_PHASE = {
    "animSetList": "phase_4_rig_animset_binding_seconds",
    "controls": "phase_6_registry_elementlist_seconds",
    "elementList": "phase_6_registry_elementlist_seconds",
    "hiddenGroups": "phase_7_hiddengroups_seconds",
}

# scalar()'s own attr_name -> phase bucket. discover_rig_context() calls
# scalar() exactly twice: scalar(shot,"scene") (line 3313, the scene
# lookup that precedes and feeds reachable() -- bucketed to Phase 1 per
# O3_R2_DISCOVERY_PHASE_MAP.md row 1's own listed underlying calls) and
# scalar(rec,"animationSet") (line 3365, inside the rig->animset binding
# loop -- Phase 4). Confirmed against the actual production source
# (audit_external_runtime/Rebuild_Control_Groups_Normalizer.py) before
# writing this wrap -- do not assume a single blanket bucket.
SCALAR_ATTR_TO_PHASE = {
    "scene": "phase_1_reachable_traversal_seconds",
    "animationSet": "phase_4_rig_animset_binding_seconds",
}


class CheckpointO3R2Error(Exception):
    pass


ANOMALIES = []


def anomaly(message):
    ANOMALIES.append(message)
    try:
        sys.stdout.write("ANOMALY: %s\n" % message)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Checkpoint-B-style fact helpers (verbatim, same copy every earlier
# checkpoint uses).
# ---------------------------------------------------------------------------

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


def stable_hash(values):
    hasher = hashlib.sha256()
    for index, item in enumerate(sorted(values)):
        if index:
            hasher.update(b"\n")
        hasher.update(item.encode("utf-8"))
    return hasher.hexdigest()


def dumps_sorted(value):
    return json.dumps(value, sort_keys=True)


def per_value_hash(value):
    return hashlib.sha256(dumps_sorted(value).encode("utf-8")).hexdigest()


def canonicalize_snapshot(snap):
    if not isinstance(snap, dict):
        return snap
    clean = dict(snap)
    for key in ("shot_handle", "animation_set_handle", "root_handle", "rig_handle",
                "registry_handle", "label", "control_handles"):
        clean.pop(key, None)
    return clean


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
            return {"available": False}
        return {
            "available": True,
            "working_set_bytes": int(counters.WorkingSetSize),
            "pagefile_usage_bytes": int(counters.PagefileUsage),
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
    else:
        head = body
    fields = {}
    for token in head.split(" "):
        if not token or "=" not in token:
            continue
        k, _sep, v = token.partition("=")
        fields[k] = _typed_checkpoint_value(v)
    return fields


def summarize_resource_checkpoints(log_text):
    checkpoints = [c for c in (parse_resource_checkpoint_line(l) for l in log_text.splitlines()) if c is not None]
    if not checkpoints:
        return {"checkpoint_count": 0, "first_checkpoint": None, "last_checkpoint": None, "final_report_entry_reached": False}
    return {
        "checkpoint_count": len(checkpoints),
        "first_checkpoint": checkpoints[0],
        "last_checkpoint": checkpoints[-1],
        "final_report_entry_reached": any(c.get("label") == "FINAL_REPORT_ENTRY" for c in checkpoints),
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


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

report = {
    "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "python_version": sys.version,
    "checks": [],
    "anomalies": ANOMALIES,
    "provenance": {},
    "command_records": [],
    "in_progress": True,
}


def check(name, condition, detail=None):
    report["checks"].append({"name": name, "pass": bool(condition), "detail": repr(detail) if detail is not None else None})
    try:
        sys.stdout.write("[%s] %s%s\n" % ("PASS" if condition else "FAIL", name, ("" if detail is None else " -- %r" % (detail,))))
    except Exception:
        pass


def write_rolling_evidence():
    ok, err, _r = write_json_atomic(JSON_OUTPUT_PATH, report)
    if not ok:
        anomaly("Rolling evidence write failed (run continues): %s" % (err,))
    return ok


main_window = None
production_bytes = None

try:
    with open(PRODUCTION_NORMALIZER_PATH, "rb") as f:
        production_bytes = f.read()
    production_sha = hashlib.sha256(production_bytes).hexdigest()
    check("production_normalizer.sha256_matches_accepted_integration", production_sha == EXPECTED_PRODUCTION_NORMALIZER_SHA256, production_sha)

    with open(CANONICAL_MASTER_PATH, "rb") as f:
        master_bytes = f.read()
    master_sha = hashlib.sha256(master_bytes).hexdigest()
    check("canonical_master.sha256_unchanged", master_sha == EXPECTED_CANONICAL_MASTER_SHA256, master_sha)

    if not (production_sha == EXPECTED_PRODUCTION_NORMALIZER_SHA256 and master_sha == EXPECTED_CANONICAL_MASTER_SHA256):
        raise CheckpointO3R2Error("Pre-flight SHA-256 check failed -- refusing to proceed.")
    report["provenance"]["production_normalizer_sha256"] = production_sha
    report["provenance"]["canonical_master_sha256"] = master_sha

    if not bool(sfmApp.HasDocument()):
        raise CheckpointO3R2Error("No SFM document is open.")
    all_shots = list(sfmApp.GetShots())
    shot3_present = any(b_name(s) == EXPECTED_SELECTED_SHOT_NAME for s in all_shots)
    check("fixture.shot3_present", shot3_present)
    if not shot3_present:
        raise CheckpointO3R2Error("shot3 not found in the open document -- wrong fixture?")

    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointO3R2Error("Starting-state fixture gate failed -- aborting before any production invocation.")

    main_window = sfmApp.GetMainWindow()
    check("o3r2.main_window_available", main_window is not None)
    write_rolling_evidence()

    for ordinal, scope_label, expected_state in COMMAND_SPECS:
        command_start_time = time.time()
        events = []          # capture_snapshot_explicit events, with phase-bucketed discovery data attached
        pending_discoveries = []  # FIFO queue of completed discover_rig_context phase results

        prod_ns = {}
        try:
            exec(compile(production_bytes, "<installed_production_normalizer_o3r2_cmd%d>" % ordinal, "exec"), prod_ns)
        except Exception as exc:
            anomaly("Command %d: production Normalizer execution raised: %r" % (ordinal, exc))
            anomaly(traceback.format_exc())

        # --- O2-R1's own corrected native-Rebuild wrap: locate the
        #     already-constructed run instance immediately after exec()
        #     returns, wrap its own self.rebuild instance attribute. ---
        run_lock_name_early = prod_ns.get("RUN_LOCK_NAME")
        run_instance = None
        if run_lock_name_early is not None and main_window is not None:
            try:
                for child in main_window.findChildren(QtCore.QObject):
                    try:
                        if b_to_unicode(child.objectName()) == run_lock_name_early:
                            run_instance = child
                            break
                    except Exception:
                        continue
            except Exception as exc:
                anomaly("Command %d: locating the run instance via findChildren raised: %r" % (ordinal, exc))

        native_rebuild_wrap_ok = False
        if run_instance is not None and getattr(run_instance, "rebuild", None) is not None:
            original_rebuild = run_instance.rebuild

            def make_observed_rebuild(original_callable):
                def observed_rebuild(aset_ptr_arg):
                    t0 = time.time()
                    mem_before = memory_snapshot()
                    ret = original_callable(aset_ptr_arg)
                    t1 = time.time()
                    mem_after = memory_snapshot()
                    events.append({
                        "kind": "native_rebuild_call",
                        "start": t0, "end": t1, "elapsed": t1 - t0,
                        "memory_before": mem_before, "memory_after": mem_after,
                    })
                    return ret
                return observed_rebuild

            run_instance.rebuild = make_observed_rebuild(original_rebuild)
            native_rebuild_wrap_ok = True
        else:
            anomaly("Command %d: could not locate the run instance or its self.rebuild attribute immediately after exec()." % ordinal)
        check("command_%d.native_rebuild_instance_wrap_installed" % ordinal, native_rebuild_wrap_ok)

        # --- Discovery phase-split instrumentation state. ---
        discovery_depth = [0]  # list-wrapped int for closure mutability under Python 2

        def make_phase_bucket():
            return {
                "phase_1_reachable_traversal_seconds": 0.0,
                "phase_2_candidate_filtering_seconds": 0.0,
                "phase_4_rig_animset_binding_seconds": 0.0,
                "phase_6_registry_elementlist_seconds": 0.0,
                "phase_7_hiddengroups_seconds": 0.0,
                "phase_8_handle_extraction_seconds": 0.0,
                "typ_call_count": 0,
                "handle_call_count": 0,
            }

        current_bucket = [None]

        original_discover_rig_context = prod_ns.get("discover_rig_context")
        original_reachable = prod_ns.get("reachable")
        original_typ = prod_ns.get("typ")
        original_arr = prod_ns.get("arr")
        original_scalar = prod_ns.get("scalar")
        original_handle = prod_ns.get("handle")
        original_capture_snapshot_explicit = prod_ns.get("capture_snapshot_explicit")
        RunClass = prod_ns.get("RebuildControlGroupsProductionRun")
        original_run_target_transaction = getattr(RunClass, "run_target_transaction", None) if RunClass else None

        def make_discover_rig_context_wrapper(original_fn):
            def wrapped(shot, aset):
                bucket = make_phase_bucket()
                prev_bucket = current_bucket[0]
                current_bucket[0] = bucket
                discovery_depth[0] += 1
                t0 = time.time()
                try:
                    result = original_fn(shot, aset)
                    exc_repr = None
                except Exception as exc:
                    result = None
                    exc_repr = repr(exc)
                    discovery_depth[0] -= 1
                    current_bucket[0] = prev_bucket
                    total = time.time() - t0
                    bucket["total_discovery_elapsed_seconds"] = total
                    bucket["status"] = None
                    bucket["exception"] = exc_repr
                    pending_discoveries.append(bucket)
                    raise
                t1 = time.time()
                discovery_depth[0] -= 1
                current_bucket[0] = prev_bucket
                total = t1 - t0
                bucket["total_discovery_elapsed_seconds"] = total
                bucket["status"] = (result or {}).get("status") if isinstance(result, dict) else None
                bucket["reachable_rig_count"] = (result or {}).get("reachable_rig_count") if isinstance(result, dict) else None
                bucket["matching_rig_count"] = (result or {}).get("matching_rig_count") if isinstance(result, dict) else None
                bucket["exception"] = None
                explained = sum(bucket[k] for k in bucket if k.startswith("phase_"))
                bucket["residual_unexplained_seconds"] = total - explained
                pending_discoveries.append(bucket)
                return result
            return wrapped

        def make_reachable_wrapper(original_fn):
            def wrapped(start, max_elements=50000):
                t0 = time.time()
                result = original_fn(start, max_elements)
                t1 = time.time()
                if discovery_depth[0] > 0 and current_bucket[0] is not None:
                    current_bucket[0]["phase_1_reachable_traversal_seconds"] += (t1 - t0)
                    current_bucket[0]["reachable_element_count"] = len(result) if result is not None else None
                return result
            return wrapped

        def make_typ_wrapper(original_fn):
            def wrapped(obj):
                t0 = time.time()
                result = original_fn(obj)
                t1 = time.time()
                if discovery_depth[0] > 0 and current_bucket[0] is not None:
                    current_bucket[0]["phase_2_candidate_filtering_seconds"] += (t1 - t0)
                    current_bucket[0]["typ_call_count"] += 1
                return result
            return wrapped

        def make_arr_wrapper(original_fn):
            def wrapped(obj, attr_name):
                t0 = time.time()
                result = original_fn(obj, attr_name)
                t1 = time.time()
                if discovery_depth[0] > 0 and current_bucket[0] is not None:
                    phase_key = ARR_ATTR_TO_PHASE.get(attr_name)
                    if phase_key is not None:
                        current_bucket[0][phase_key] += (t1 - t0)
                return result
            return wrapped

        def make_scalar_wrapper(original_fn):
            def wrapped(obj, attr_name):
                t0 = time.time()
                result = original_fn(obj, attr_name)
                t1 = time.time()
                if discovery_depth[0] > 0 and current_bucket[0] is not None:
                    phase_key = SCALAR_ATTR_TO_PHASE.get(attr_name)
                    if phase_key is not None:
                        current_bucket[0][phase_key] += (t1 - t0)
                return result
            return wrapped

        def make_handle_wrapper(original_fn):
            def wrapped(obj):
                t0 = time.time()
                result = original_fn(obj)
                t1 = time.time()
                if discovery_depth[0] > 0 and current_bucket[0] is not None:
                    current_bucket[0]["phase_8_handle_extraction_seconds"] += (t1 - t0)
                    current_bucket[0]["handle_call_count"] += 1
                return result
            return wrapped

        def make_capture_snapshot_explicit_wrapper(original_fn):
            def wrapped(shot, aset, label, rig_context=None):
                t0 = time.time()
                result = original_fn(shot, aset, label, rig_context)
                t1 = time.time()
                try:
                    target_name = b_name(aset)
                except Exception:
                    target_name = u"<unknown>"
                clean = canonicalize_snapshot(result)
                aggregate_hash = per_value_hash(clean) if clean is not None else None
                discovery_phase_data = pending_discoveries.pop() if pending_discoveries else None
                events.append({
                    "kind": "capture_snapshot_explicit",
                    "label": label,
                    "target": target_name,
                    "start": t0, "end": t1, "elapsed": t1 - t0,
                    "aggregate_hash": aggregate_hash,
                    "discovery_phase_data": discovery_phase_data,
                })
                return result
            return wrapped

        def make_run_target_transaction_wrapper(original_method):
            def wrapped(self, shot_record, target):
                try:
                    target_name = target.get("name") if isinstance(target, dict) else None
                except Exception:
                    target_name = None
                t0 = time.time()
                mem_before = memory_snapshot()
                events.append({"kind": "target_transaction_entry", "target": target_name, "start": t0, "memory": mem_before})
                result = original_method(self, shot_record, target)
                t1 = time.time()
                mem_after = memory_snapshot()
                events.append({"kind": "target_transaction_exit", "target": target_name, "end": t1, "elapsed": t1 - t0, "memory": mem_after})
                return result
            return wrapped

        wrap_ok = True
        try:
            if original_discover_rig_context is not None:
                prod_ns["discover_rig_context"] = make_discover_rig_context_wrapper(original_discover_rig_context)
            else:
                wrap_ok = False
                anomaly("Command %d: discover_rig_context not found -- instrumentation incomplete." % ordinal)
            if original_reachable is not None:
                prod_ns["reachable"] = make_reachable_wrapper(original_reachable)
            else:
                wrap_ok = False
                anomaly("Command %d: reachable not found -- instrumentation incomplete." % ordinal)
            if original_typ is not None:
                prod_ns["typ"] = make_typ_wrapper(original_typ)
            else:
                wrap_ok = False
                anomaly("Command %d: typ not found -- instrumentation incomplete." % ordinal)
            if original_arr is not None:
                prod_ns["arr"] = make_arr_wrapper(original_arr)
            else:
                wrap_ok = False
                anomaly("Command %d: arr not found -- instrumentation incomplete." % ordinal)
            if original_scalar is not None:
                prod_ns["scalar"] = make_scalar_wrapper(original_scalar)
            else:
                wrap_ok = False
                anomaly("Command %d: scalar not found -- instrumentation incomplete." % ordinal)
            if original_handle is not None:
                prod_ns["handle"] = make_handle_wrapper(original_handle)
            else:
                wrap_ok = False
                anomaly("Command %d: handle not found -- instrumentation incomplete." % ordinal)
            if original_capture_snapshot_explicit is not None:
                prod_ns["capture_snapshot_explicit"] = make_capture_snapshot_explicit_wrapper(original_capture_snapshot_explicit)
            else:
                wrap_ok = False
                anomaly("Command %d: capture_snapshot_explicit not found -- instrumentation incomplete." % ordinal)
            if RunClass is not None and original_run_target_transaction is not None:
                RunClass.run_target_transaction = make_run_target_transaction_wrapper(original_run_target_transaction)
            else:
                wrap_ok = False
                anomaly("Command %d: run_target_transaction not found -- instrumentation incomplete." % ordinal)
        except Exception as exc:
            wrap_ok = False
            anomaly("Command %d: installing observational wrappers raised: %r" % (ordinal, exc))
            anomaly(traceback.format_exc())
        check("command_%d.instrumentation_installed" % ordinal, wrap_ok)

        run_started = False
        run_completed_cleanly = False
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
            sys.stdout.write("\n>>> Command %d/2: choose '%s' in the real dialog that just appeared. <<<\n\n" % (ordinal, scope_label))
            wait_start = time.time()
            MAX_WAIT_SECONDS = 1800
            while normalizer_run_is_active():
                QtCore.QCoreApplication.processEvents()
                time.sleep(0.05)
                if time.time() - wait_start > MAX_WAIT_SECONDS:
                    anomaly("Command %d did not complete within %d seconds -- aborting wait." % (ordinal, MAX_WAIT_SECONDS))
                    break
            else:
                run_completed_cleanly = True
            settle_start = time.time()
            while time.time() - settle_start < 1.0:
                QtCore.QCoreApplication.processEvents()
                time.sleep(0.05)
        else:
            anomaly("Command %d: no run-lock was ever observed active -- operator likely cancelled the scope dialog." % ordinal)

        command_duration_seconds = time.time() - command_start_time
        check("command_%d.run_was_started" % ordinal, run_started)
        check("command_%d.run_completed_within_timeout" % ordinal, run_completed_cleanly if run_started else False)

        native_evidence = {}
        resource_checkpoint_summary = {"checkpoint_count": 0, "first_checkpoint": None, "last_checkpoint": None, "final_report_entry_reached": False}
        try:
            with open(NORMALIZER_LOG_PATH, "rb") as f:
                log_bytes = f.read()
            log_text = log_bytes.decode("ascii", "replace")
            native_evidence["contains_NATIVE_GUARDS_PASS"] = ("NATIVE_GUARDS = PASS" in log_text)
            native_evidence["contains_NATIVE_REBUILD_RETURNED_PASS"] = ("NATIVE_REBUILD_RETURNED = PASS" in log_text)
            resource_checkpoint_summary = summarize_resource_checkpoints(log_text)
            preserve_path = PER_COMMAND_LOG_PRESERVE_TEMPLATE % ordinal
            preserve_ok, preserve_err = write_text_atomic(preserve_path, log_bytes)
            if not preserve_ok:
                anomaly("Command %d: could not preserve production log: %s" % (ordinal, preserve_err))
            del log_bytes, log_text
        except Exception as exc:
            native_evidence["log_read_error"] = repr(exc)
            anomaly("Command %d: could not read production log: %r" % (ordinal, exc))

        check("command_%d.native_guards_pass" % ordinal, native_evidence.get("contains_NATIVE_GUARDS_PASS") is True, native_evidence.get("contains_NATIVE_GUARDS_PASS"))
        check("command_%d.native_rebuild_returned_pass" % ordinal, native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS") is True, native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS"))
        check("command_%d.production_final_report_entry_reached" % ordinal, resource_checkpoint_summary.get("final_report_entry_reached") is True, resource_checkpoint_summary.get("final_report_entry_reached"))

        authority_evidence = {}
        try:
            authority_runtime = prod_ns.get("authority_runtime")
            if authority_runtime is not None:
                try:
                    authority_evidence["is_canonical"] = bool(authority_runtime.is_canonical())
                except Exception as exc:
                    authority_evidence["is_canonical_error"] = repr(exc)
                try:
                    authority_evidence["get_state"] = authority_runtime.get_state()
                except Exception as exc:
                    authority_evidence["get_state_error"] = repr(exc)
                try:
                    broker = authority_runtime.get_broker(
                        expected_api_version=prod_ns.get("_AUTHORITY_EXPECTED_API_VERSION"),
                        expected_build_id=prod_ns.get("_AUTHORITY_EXPECTED_BUILD_ID"),
                        is_main_thread_fn=lambda: (QtCore.QThread.currentThread() is QtCore.QCoreApplication.instance().thread()),
                    )
                    authority_evidence["outstanding_lease_count"] = broker.outstanding_lease_count()
                    authority_evidence["provider_counters"] = broker.provider_counters()
                except Exception as exc:
                    authority_evidence["broker_query_error"] = repr(exc)
        except Exception as exc:
            authority_evidence["capture_error"] = repr(exc)

        check("command_%d.authority_broker_ready" % ordinal, authority_evidence.get("get_state") == "READY", authority_evidence.get("get_state"))
        check("command_%d.authority_canonical" % ordinal, authority_evidence.get("is_canonical") is True, authority_evidence.get("is_canonical"))
        check("command_%d.zero_outstanding_leases_after" % ordinal, authority_evidence.get("outstanding_lease_count") == 0, authority_evidence.get("outstanding_lease_count"))

        # --- Correlate capture events with branch truth (same technique
        #     as O2/O2-R1) and assemble the per-target, per-label
        #     discovery-phase report. ---
        capture_events = [e for e in events if e["kind"] == "capture_snapshot_explicit"]
        by_target = {}
        for e in capture_events:
            by_target.setdefault(e["target"], []).append(e)
        for t in by_target:
            by_target[t].sort(key=lambda e: e["start"])

        per_target_discovery = {}
        for target_name, seq in by_target.items():
            labels_in_order = [e["label"] for e in seq]
            label_set = set(labels_in_order)
            if "PRODUCTION_GENERIC_COMPOSER_PRE" in label_set:
                branch = "reconciled"
            elif label_set == {"PRE", "NATIVE_POST"}:
                branch = "native_only_fallback"
            else:
                branch = "unknown"
            per_target_discovery[target_name] = {
                "branch": branch,
                "captures": [
                    {"label": e["label"], "capture_elapsed": e["elapsed"], "discovery": e.get("discovery_phase_data")}
                    for e in seq
                ],
            }

        native_rebuild_events = [e for e in events if e["kind"] == "native_rebuild_call"]
        transaction_entries = [e for e in events if e["kind"] == "target_transaction_entry"]

        command_record = {
            "ordinal": ordinal,
            "scope_requested": scope_label,
            "expected_state": expected_state,
            "duration_seconds": command_duration_seconds,
            "run_started": run_started,
            "run_completed_cleanly": run_completed_cleanly,
            "native_protection": native_evidence,
            "production_resource_checkpoints": resource_checkpoint_summary,
            "authority_lifecycle": authority_evidence,
            "target_count_transacted": len(transaction_entries),
            "per_target_discovery": per_target_discovery,
            "native_rebuild_stage_summary": {
                "call_count": len(native_rebuild_events),
                "total_elapsed_seconds": sum(e["elapsed"] for e in native_rebuild_events),
            },
        }
        report["command_records"].append(command_record)

        del prod_ns, events, pending_discoveries, capture_events, by_target
        try:
            del authority_runtime
        except Exception:
            pass
        try:
            del broker
        except Exception:
            pass
        gc.collect()
        report.setdefault("memory_snapshots", {})["after_command_%d_gc_collect" % ordinal] = memory_snapshot()
        write_rolling_evidence()

except CheckpointO3R2Error as gate_exc:
    anomaly("GATE FAILURE (orderly abort, no production Normalizer invocation attempted): %s" % gate_exc)
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
all_commands_started = bool(
    len(report["command_records"]) == len(COMMAND_SPECS)
    and all(rec.get("run_started") for rec in report["command_records"])
)
report["overall_pass"] = bool(all_checks_passed and completed_without_exception and all_commands_started)

# --- Mechanical decision computation for composer-before discoveries
#     specifically, per O3_R2_MEASUREMENT_CONTRACT.md. ---
composer_pre_removable = []
composer_pre_retained = []
composer_pre_total = []
for rec in report["command_records"]:
    for target_name, info in (rec.get("per_target_discovery") or {}).items():
        for cap in info.get("captures", []):
            if cap["label"] != "PRODUCTION_GENERIC_COMPOSER_PRE":
                continue
            d = cap.get("discovery")
            if not d:
                continue
            removable = d.get("phase_1_reachable_traversal_seconds", 0.0)
            total = d.get("total_discovery_elapsed_seconds", 0.0)
            retained = total - removable
            composer_pre_removable.append(removable)
            composer_pre_retained.append(retained)
            composer_pre_total.append(total)

decision = "UNRESOLVED"
decision_detail = {}
if composer_pre_total:
    sum_removable = sum(composer_pre_removable)
    sum_retained = sum(composer_pre_retained)
    sum_total = sum(composer_pre_total)
    removable_fraction = (sum_removable / sum_total) if sum_total > 0 else None
    decision_detail = {
        "sample_count": len(composer_pre_total),
        "sum_removable_seconds": sum_removable,
        "sum_retained_seconds": sum_retained,
        "sum_total_seconds": sum_total,
        "removable_fraction": removable_fraction,
    }
    if removable_fraction is None:
        decision = "UNRESOLVED"
    elif removable_fraction >= 0.5:
        decision = "OPTION_C_MATERIAL"
    elif removable_fraction >= 0.15:
        decision = "OPTION_C_MARGINAL"
    else:
        decision = "OPTION_C_IMMATERIAL"
report["option_c_decision"] = decision
report["option_c_decision_detail"] = decision_detail

json_write_ok, json_write_error, _r = write_json_atomic(JSON_OUTPUT_PATH, report)
if not json_write_ok:
    anomaly("Final JSON write failed: %s" % json_write_error)

summary_lines = []
summary_lines.append("SFM CHECKPOINT O3-R2 -- DISCOVERY COST SPLIT MEASUREMENT")
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
if report.get("gate_failure"):
    summary_lines.append("*** GATE FAILURE: aborted BEFORE any production Normalizer invocation. ***")
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
for rec in report["command_records"]:
    summary_lines.append("=== Command %d (%s, %s) ===" % (rec["ordinal"], rec["scope_requested"], rec["expected_state"]))
    summary_lines.append("  duration=%.3fs targets_transacted=%d" % (rec["duration_seconds"], rec["target_count_transacted"]))
    ns = rec["native_rebuild_stage_summary"]
    summary_lines.append("  native_rebuild: calls=%r total_s=%r" % (ns["call_count"], ns["total_elapsed_seconds"]))
    for target_name, info in rec["per_target_discovery"].items():
        summary_lines.append("  target=%r branch=%s" % (target_name, info["branch"]))
        for cap in info["captures"]:
            d = cap.get("discovery") or {}
            summary_lines.append(
                "    label=%s capture_elapsed=%.4f discovery_total=%.4f reachable=%.4f residual=%.4f"
                % (cap["label"], cap["capture_elapsed"], d.get("total_discovery_elapsed_seconds", 0.0),
                   d.get("phase_1_reachable_traversal_seconds", 0.0), d.get("residual_unexplained_seconds", 0.0))
            )
    summary_lines.append("")
summary_lines.append("--- OPTION C DECISION ---")
summary_lines.append("decision=%s" % decision)
summary_lines.append("detail=%r" % decision_detail)
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
        "\nCheckpoint O3-R2 reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok)
    )
    sys.stdout.write("\nDO NOT SAVE. Restart SFM to discard this mutation.\n")
except Exception:
    pass
