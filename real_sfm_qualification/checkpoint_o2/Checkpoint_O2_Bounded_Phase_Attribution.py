# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint O2: Bounded Rebuild +
Normalizer Phase Attribution.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: mutates the scene (normal Selected-Shots production
behavior, twice, in one continuous SFM process). Do not save afterward.

Purpose:
  Attribute meaningful cost inside the real qualified per-target
  transaction, WITHOUT another broad All-Shots stress campaign. O1
  (static source audit) identified three candidates; Astra's independent
  adversarial review disposed them as:
    - self.work's stored `aset` wrapper:            LOW-VALUE / REJECT
    - repeated semantic captures:                    STRONG MEASUREMENT CANDIDATE
    - zero-repair-row warm-path early-out:            UNSAFE DIRECTION (do not pursue)
  Astra also flagged, as measurement-only questions: repeated shot-graph
  discovery inside major capture boundaries; capture_tree()'s own
  recursive-closure cycle retaining its output until cyclic collection;
  and unresolved native Rebuild / shot activation / composer attribution.

  This checkpoint measures those, and ONLY those, in the smallest
  representative real-SFM workload that can answer the questions: the
  established shot3 fixture, Selected Shots scope, run once from fresh
  state and once again on the now-normalized state. It does NOT run
  another All-Shots command and does NOT expand to a whole-fixture
  campaign.

Instrumentation is strictly OBSERVATIONAL. This script never edits
Rebuild_Control_Groups_Normalizer.py -- it exec()s the pinned, SHA-256
verified production bytes into a fresh namespace (the same technique
every earlier checkpoint in this project already uses) and then
monkey-patches five specific call points in that IN-MEMORY namespace,
each wrapper calling the ORIGINAL function/method with the SAME
arguments and returning its SAME, UNMODIFIED return value -- only
recording timing/identity/compact-hash metadata around the call. No
capture is skipped, no native Rebuild call is bypassed, no composer call
is bypassed, no GC is forced between production stages, no callback
timing is altered, no DME object is cached across the wrapper's own
call, no validation is reduced, and no authority-lifecycle behavior is
touched.

The five wrap points (module functions patched via reassignment in the
exec'd namespace dict; class methods patched via class-attribute
reassignment on the exec'd class object -- both act only on THIS
process's in-memory copy, never on the file on disk):
  1. discover_rig_context(shot, aset)          -- module function
  2. capture_tree(root)                        -- module function
  3. capture_snapshot_explicit(shot,aset,label,rig_context=None) -- module function
  4. RebuildControlGroupsProductionRun.run_target_transaction(self, shot_record, target)
  5. RebuildControlGroupsProductionRun.prepare_native_callback(self, ...)
     (wrapped only to post-process the already-assigned self.rebuild
     with a timing/resource wrapper around the native call itself --
     the setup method's own logic and return value are untouched)

Several requested stage boundaries are DERIVED from the timestamp gaps
between these five wrap points' own recorded events, rather than adding
further wraps (per the explicit instruction: "Do not add a boundary if
observing it requires invasive behavioral changes"):
  - classification/planning completion   = gap between NATIVE_POST capture
    end and the next capture's start (or run_target_transaction's own end,
    if the native-only fallback branch was taken -- revealed by capture
    COUNT, see below, not by catching the fallback exception).
  - contextual writes completion          = gap between composer-before
    capture end and composer-after capture start.
  - target isolation                      = gap between the terminal
    capture's end and run_target_transaction's own end.

Branch truth (reconciled-path vs. native-only-fallback) is read directly
from which capture LABELS actually occurred for a given target, not
inferred or assumed: the native-only fallback path raises
NativePostFallback internally (production's own control-flow exception,
confirmed by direct source reading) BEFORE the composer-before capture
would ever run -- so a target that shows only "PRE" and "NATIVE_POST"
captures took the fallback branch; a target that additionally shows
"PRODUCTION_GENERIC_COMPOSER_PRE"/"_POST" and
"PRODUCTION_SEMANTIC_FINGERPRINT" took the reconciled branch. This
script does not catch or alter that exception's own control flow.

Composer-before/outer-POST and composer-after/terminal EQUIVALENCE
witnesses are computed by canonicalizing (stripping only native-handle
fields, the same technique every earlier checkpoint already uses) and
hashing EVERY capture's own returned snapshot -- both one AGGREGATE hash
and PER-FIELD hashes (rig_status, groups, memberships,
duplicate_sibling_groups, duplicate_direct_controls,
duplicate_memberships) -- then mechanically comparing hashes for the
SAME target across labels. A full aggregate-hash match is necessary but
not sufficient on its own; per-field comparison is what actually answers
"which semantics, if any, differ."

Resource sampling is LOW-CADENCE: once per target (at
run_target_transaction's own entry/exit) and once immediately around the
native Rebuild call -- never inside capture_tree's own recursive walk,
never per DME element. This is deliberate: the diagnostic must not
recreate the qualification-harness's own earlier mistake of measurement
becoming the dominant cost.

Do not restart SFM between the two commands. Do not alter the scene
between commands.

Output (written incrementally after each command boundary):
  C:\\Users\\Public\\Documents\\sfm_checkpoint_o2_result.json
  C:\\Users\\Public\\Documents\\sfm_checkpoint_o2_result_summary.txt
  C:\\Users\\Public\\Documents\\sfm_checkpoint_o2_production_log_command{1,2}.txt

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
COMPACT_SELECTED_TARGETS_OF_INTEREST = [
    (EXPECTED_SELECTED_SHOT_NAME, aset_name)
    for aset_name in sorted(EXPECTED_SELECTED_TARGETS.keys())
]

COMMAND_SPECS = [
    (1, u"Selected Shots", u"fresh"),
    (2, u"Selected Shots", u"already_normalized"),
]

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_o2_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_o2_result_summary.txt"
PER_COMMAND_LOG_PRESERVE_TEMPLATE = (
    "C:\\Users\\Public\\Documents\\sfm_checkpoint_o2_production_log_command%d.txt"
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


class CheckpointO2Error(Exception):
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
    """Identical stripping discipline to every earlier checkpoint's own
    canonicalize_snapshot(): removes only native-handle fields, never
    semantic content."""
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
        raise CheckpointO2Error("Pre-flight SHA-256 check failed -- refusing to proceed.")
    report["provenance"]["production_normalizer_sha256"] = production_sha
    report["provenance"]["canonical_master_sha256"] = master_sha

    if not bool(sfmApp.HasDocument()):
        raise CheckpointO2Error("No SFM document is open.")
    all_shots = list(sfmApp.GetShots())
    shot3_present = any(b_name(s) == EXPECTED_SELECTED_SHOT_NAME for s in all_shots)
    check("fixture.shot3_present", shot3_present)
    if not shot3_present:
        raise CheckpointO2Error("shot3 not found in the open document -- wrong fixture?")

    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointO2Error("Starting-state fixture gate failed -- aborting before any production invocation.")

    main_window = sfmApp.GetMainWindow()
    check("o2.main_window_available", main_window is not None)
    write_rolling_evidence()

    for ordinal, scope_label, expected_state in COMMAND_SPECS:
        command_start_time = time.time()
        prod_ns = {}
        try:
            exec(compile(production_bytes, "<installed_production_normalizer_o2_cmd%d>" % ordinal, "exec"), prod_ns)
        except Exception as exc:
            anomaly("Command %d: production Normalizer execution raised: %r" % (ordinal, exc))
            anomaly(traceback.format_exc())

        # -------------------------------------------------------------
        # Install the five observational wrappers, BEFORE the dialog
        # ever triggers the real run. Each wrapper calls the ORIGINAL
        # function/method with the SAME arguments and returns its SAME
        # return value unmodified -- only recording metadata.
        # -------------------------------------------------------------
        events = []  # flat, time-ordered list of dicts: kind, label/target/timing/etc.

        original_discover_rig_context = prod_ns.get("discover_rig_context")
        original_capture_tree = prod_ns.get("capture_tree")
        original_capture_snapshot_explicit = prod_ns.get("capture_snapshot_explicit")
        RunClass = prod_ns.get("RebuildControlGroupsProductionRun")
        original_run_target_transaction = getattr(RunClass, "run_target_transaction", None) if RunClass else None
        original_prepare_native_callback = getattr(RunClass, "prepare_native_callback", None) if RunClass else None

        def make_discover_rig_context_wrapper(original_fn):
            def wrapped(shot, aset):
                t0 = time.time()
                result = original_fn(shot, aset)
                t1 = time.time()
                try:
                    target_name = b_name(aset)
                except Exception:
                    target_name = u"<unknown>"
                events.append({
                    "kind": "discover_rig_context",
                    "target": target_name,
                    "start": t0,
                    "end": t1,
                    "elapsed": t1 - t0,
                    "status": (result or {}).get("status") if isinstance(result, dict) else None,
                    "reachable_rig_count": (result or {}).get("reachable_rig_count") if isinstance(result, dict) else None,
                    "matching_rig_count": (result or {}).get("matching_rig_count") if isinstance(result, dict) else None,
                })
                return result
            return wrapped

        def make_capture_tree_wrapper(original_fn):
            def wrapped(root):
                t0 = time.time()
                result = original_fn(root)
                t1 = time.time()
                events.append({
                    "kind": "capture_tree",
                    "start": t0,
                    "end": t1,
                    "elapsed": t1 - t0,
                    "group_count": (result or {}).get("group_count") if isinstance(result, dict) else None,
                    "membership_count": len((result or {}).get("memberships") or {}) if isinstance(result, dict) else None,
                    "duplicate_sibling_count": len((result or {}).get("duplicate_sibling_groups") or []) if isinstance(result, dict) else None,
                    "duplicate_direct_control_count": len((result or {}).get("duplicate_direct_controls") or []) if isinstance(result, dict) else None,
                })
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
                per_field_hashes = {}
                if isinstance(clean, dict):
                    for field_key in ("rig_status", "groups", "memberships", "group_count",
                                       "duplicate_sibling_groups", "duplicate_direct_controls",
                                       "duplicate_memberships"):
                        if field_key in clean:
                            per_field_hashes[field_key] = per_value_hash(clean[field_key])
                events.append({
                    "kind": "capture_snapshot_explicit",
                    "label": label,
                    "target": target_name,
                    "start": t0,
                    "end": t1,
                    "elapsed": t1 - t0,
                    "aggregate_hash": aggregate_hash,
                    "per_field_hashes": per_field_hashes,
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
                events.append({
                    "kind": "target_transaction_entry",
                    "target": target_name,
                    "start": t0,
                    "memory": mem_before,
                })
                result = original_method(self, shot_record, target)
                t1 = time.time()
                mem_after = memory_snapshot()
                events.append({
                    "kind": "target_transaction_exit",
                    "target": target_name,
                    "end": t1,
                    "elapsed": t1 - t0,
                    "memory": mem_after,
                })
                return result
            return wrapped

        def make_prepare_native_callback_wrapper(original_method):
            def wrapped(self, *args, **kwargs):
                result = original_method(self, *args, **kwargs)
                original_rebuild = self.rebuild

                def observed_rebuild(aset_ptr_arg):
                    t0 = time.time()
                    mem_before = memory_snapshot()
                    ret = original_rebuild(aset_ptr_arg)
                    t1 = time.time()
                    mem_after = memory_snapshot()
                    events.append({
                        "kind": "native_rebuild_call",
                        "start": t0,
                        "end": t1,
                        "elapsed": t1 - t0,
                        "memory_before": mem_before,
                        "memory_after": mem_after,
                    })
                    return ret

                self.rebuild = observed_rebuild
                return result
            return wrapped

        wrap_ok = True
        try:
            if original_discover_rig_context is not None:
                prod_ns["discover_rig_context"] = make_discover_rig_context_wrapper(original_discover_rig_context)
            else:
                wrap_ok = False
                anomaly("Command %d: discover_rig_context not found in exec'd namespace -- instrumentation incomplete." % ordinal)

            if original_capture_tree is not None:
                prod_ns["capture_tree"] = make_capture_tree_wrapper(original_capture_tree)
            else:
                wrap_ok = False
                anomaly("Command %d: capture_tree not found in exec'd namespace -- instrumentation incomplete." % ordinal)

            if original_capture_snapshot_explicit is not None:
                prod_ns["capture_snapshot_explicit"] = make_capture_snapshot_explicit_wrapper(original_capture_snapshot_explicit)
            else:
                wrap_ok = False
                anomaly("Command %d: capture_snapshot_explicit not found in exec'd namespace -- instrumentation incomplete." % ordinal)

            if RunClass is not None and original_run_target_transaction is not None:
                RunClass.run_target_transaction = make_run_target_transaction_wrapper(original_run_target_transaction)
            else:
                wrap_ok = False
                anomaly("Command %d: run_target_transaction not found -- instrumentation incomplete." % ordinal)

            if RunClass is not None and original_prepare_native_callback is not None:
                RunClass.prepare_native_callback = make_prepare_native_callback_wrapper(original_prepare_native_callback)
            else:
                wrap_ok = False
                anomaly("Command %d: prepare_native_callback not found -- native-Rebuild timing unavailable this command." % ordinal)
        except Exception as exc:
            wrap_ok = False
            anomaly("Command %d: installing observational wrappers raised: %r" % (ordinal, exc))
            anomaly(traceback.format_exc())

        check("command_%d.instrumentation_installed" % ordinal, wrap_ok)

        run_started = False
        run_completed_cleanly = False
        run_lock_name = prod_ns.get("RUN_LOCK_NAME")

        # NOTE: the production dialog itself was already triggered by the
        # module-level exec() above (matching every earlier checkpoint's
        # own established pattern) -- the wrappers installed just above
        # take effect for the async, Qt-deferred per-target processing
        # that follows, since Python resolves these names at CALL time
        # via the shared exec'd-namespace globals, not at definition time.

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
                "\n>>> Command %d/2: choose '%s' in the real dialog that just appeared. <<<\n\n"
                % (ordinal, scope_label)
            )
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
            anomaly(
                "Command %d: no run-lock was ever observed active -- this most likely means the "
                "operator cancelled the scope dialog." % ordinal
            )

        command_duration_seconds = time.time() - command_start_time
        check("command_%d.run_was_started" % ordinal, run_started)
        check("command_%d.run_completed_within_timeout" % ordinal, run_completed_cleanly if run_started else False)

        # --- Native-protection / resource-checkpoint / lifecycle evidence
        #     (existing qualified diagnostics only, same as every earlier
        #     checkpoint). ---
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
                        is_main_thread_fn=lambda: (
                            QtCore.QThread.currentThread() is QtCore.QCoreApplication.instance().thread()
                        ),
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

        # --- Derive stage boundaries from event gaps; compute per-target
        #     capture sequences, branch truth, and equivalence witnesses. ---
        capture_events = [e for e in events if e["kind"] == "capture_snapshot_explicit"]
        by_target = {}
        for e in capture_events:
            by_target.setdefault(e["target"], []).append(e)
        for t in by_target:
            by_target[t].sort(key=lambda e: e["start"])

        per_target_summary = {}
        for target_name, seq in by_target.items():
            labels_in_order = [e["label"] for e in seq]
            label_set = set(labels_in_order)
            if "PRODUCTION_GENERIC_COMPOSER_PRE" in label_set:
                branch = "reconciled"
            elif label_set == {"PRE", "NATIVE_POST"}:
                branch = "native_only_fallback"
            else:
                branch = "unknown"

            def find(label):
                for e in seq:
                    if e["label"] == label:
                        return e
                return None

            outer_post = find("NATIVE_POST")
            composer_pre = find("PRODUCTION_GENERIC_COMPOSER_PRE")
            composer_post = find("PRODUCTION_GENERIC_COMPOSER_POST")
            terminal = find("PRODUCTION_SEMANTIC_FINGERPRINT")

            def compare(a, b):
                if a is None or b is None:
                    return "FRESHNESS_OR_EXCEPTION_SEMANTICS_UNRESOLVED"
                if a["aggregate_hash"] == b["aggregate_hash"]:
                    return "EXERCISED_PATH_EQUIVALENT_NO_INTERVENING_MUTATION"
                return "NOT_EQUIVALENT"

            def field_diff(a, b):
                if a is None or b is None:
                    return None
                fa, fb = a.get("per_field_hashes") or {}, b.get("per_field_hashes") or {}
                diffs = {}
                for k in set(fa.keys()) | set(fb.keys()):
                    if fa.get(k) != fb.get(k):
                        diffs[k] = {"a": fa.get(k), "b": fb.get(k)}
                return diffs

            composer_before_witness = compare(outer_post, composer_pre)
            composer_after_terminal_witness = compare(composer_post, terminal) if branch == "reconciled" else "UNRESOLVED_NATIVE_ONLY_FALLBACK_NO_TERMINAL_COMPARISON"

            per_target_summary[target_name] = {
                "branch": branch,
                "capture_labels_in_order": labels_in_order,
                "capture_count": len(seq),
                "composer_before_vs_outer_post_witness": composer_before_witness,
                "composer_before_vs_outer_post_field_diffs": field_diff(outer_post, composer_pre),
                "composer_after_vs_terminal_witness": composer_after_terminal_witness,
                "composer_after_vs_terminal_field_diffs": field_diff(composer_post, terminal) if branch == "reconciled" else None,
                "capture_timings": [{"label": e["label"], "elapsed": e["elapsed"]} for e in seq],
                "classification_planning_gap_seconds": (
                    (composer_pre["start"] - outer_post["end"]) if (outer_post and composer_pre) else None
                ),
                "contextual_writes_gap_seconds": (
                    (composer_post["start"] - composer_pre["end"]) if (composer_pre and composer_post) else None
                ),
            }

        discovery_events = [e for e in events if e["kind"] == "discover_rig_context"]
        tree_events = [e for e in events if e["kind"] == "capture_tree"]
        native_rebuild_events = [e for e in events if e["kind"] == "native_rebuild_call"]
        transaction_entries = [e for e in events if e["kind"] == "target_transaction_entry"]
        transaction_exits = [e for e in events if e["kind"] == "target_transaction_exit"]

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
            "per_target_summary": per_target_summary,
            "discovery_stage_summary": {
                "call_count": len(discovery_events),
                "total_elapsed_seconds": sum(e["elapsed"] for e in discovery_events),
                "mean_elapsed_seconds": (sum(e["elapsed"] for e in discovery_events) / len(discovery_events)) if discovery_events else None,
                "reachable_rig_counts": [e.get("reachable_rig_count") for e in discovery_events],
            },
            "tree_construction_stage_summary": {
                "call_count": len(tree_events),
                "total_elapsed_seconds": sum(e["elapsed"] for e in tree_events),
                "mean_elapsed_seconds": (sum(e["elapsed"] for e in tree_events) / len(tree_events)) if tree_events else None,
                "group_counts": [e.get("group_count") for e in tree_events],
            },
            "native_rebuild_stage_summary": {
                "call_count": len(native_rebuild_events),
                "total_elapsed_seconds": sum(e["elapsed"] for e in native_rebuild_events),
                "per_call_memory_deltas_working_set_bytes": [
                    ((e["memory_after"].get("working_set_bytes") or 0) - (e["memory_before"].get("working_set_bytes") or 0))
                    if e["memory_after"].get("available") and e["memory_before"].get("available") else None
                    for e in native_rebuild_events
                ],
            },
            "target_transaction_memory": {
                "entries": [{"target": e.get("target"), "memory": e.get("memory")} for e in transaction_entries],
                "exits": [{"target": e.get("target"), "memory": e.get("memory")} for e in transaction_exits],
            },
        }
        report["command_records"].append(command_record)

        # --- Drop this command's own exec namespace and force a
        #     collection before the next command (F1-2/F1-R2's own
        #     established correction). ---
        del prod_ns, events, capture_events, by_target
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

except CheckpointO2Error as gate_exc:
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

json_write_ok, json_write_error, _r = write_json_atomic(JSON_OUTPUT_PATH, report)
if not json_write_ok:
    anomaly("Final JSON write failed: %s" % json_write_error)

summary_lines = []
summary_lines.append("SFM CHECKPOINT O2 -- BOUNDED REBUILD + NORMALIZER PHASE ATTRIBUTION")
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
    ds = rec["discovery_stage_summary"]
    ts = rec["tree_construction_stage_summary"]
    ns = rec["native_rebuild_stage_summary"]
    summary_lines.append("  discovery: calls=%r total_s=%r mean_s=%r" % (ds["call_count"], ds["total_elapsed_seconds"], ds["mean_elapsed_seconds"]))
    summary_lines.append("  tree_construction: calls=%r total_s=%r mean_s=%r" % (ts["call_count"], ts["total_elapsed_seconds"], ts["mean_elapsed_seconds"]))
    summary_lines.append("  native_rebuild: calls=%r total_s=%r" % (ns["call_count"], ns["total_elapsed_seconds"]))
    for target_name, summary in rec["per_target_summary"].items():
        summary_lines.append(
            "  target=%r branch=%s captures=%r composer_before_witness=%s composer_after_terminal_witness=%s"
            % (target_name, summary["branch"], summary["capture_labels_in_order"],
               summary["composer_before_vs_outer_post_witness"], summary["composer_after_vs_terminal_witness"])
        )
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
        "\nCheckpoint O2 reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok)
    )
    sys.stdout.write("\nDO NOT SAVE. Restart SFM to discard this mutation.\n")
except Exception:
    pass
