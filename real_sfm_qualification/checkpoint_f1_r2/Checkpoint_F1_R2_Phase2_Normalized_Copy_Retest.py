# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint F1-R2, Phase 2:
Normalized-Copy Retest.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: this script does NOT save. It runs production All Shots
once against the ALREADY-NORMALIZED diagnostic copy Phase 1 created (never
the original fixture). **Do not save afterward.**

Prerequisite: SFM has been FULLY RESTARTED since Phase 1, and the operator
has opened ONLY the normalized diagnostic copy
(`F1_R2_NORMALIZED_DIAGNOSTIC_COPY.sfm`) Phase 1 saved -- never the
original fixture.

Purpose:
  Phase 1 established production evidence for the FIRST All-Shots
  normalization of the original fixture (~227 MiB private growth / ~222
  MiB free-VAS loss within that one command) and then saved the resulting
  normalized scene to a new file. Phase 2 tests the SAME production
  All-Shots command again, but now against a scene that is ALREADY
  normalized, in a genuinely FRESH process. This lets the two competing
  hypotheses be told apart numerically:

    (A) SCENE-RESIDENT structural growth: the first normalization made
        the scene itself bigger/more complex, and that growth is now
        already represented in the freshly-loaded, already-normalized
        copy's own idle memory footprint -- in which case this second,
        idempotent All-Shots run should add comparatively LITTLE.
    (B) PER-RUN NATIVE/allocator retention: growth that is an artifact of
        running the Rebuild process itself, which would recur on this
        second run at a similar magnitude regardless of the scene
        already being normalized.

  This script records this run's own CP0/FINAL_REPORT_ENTRY resource-
  checkpoint evidence (the "per-run" component) and this fresh process's
  own idle-before-run memory snapshot (compared against Phase 1's own
  idle-before-run snapshot, read back from its evidence file, to derive
  the "serialized/resident" component). It does NOT compute a
  classification verdict itself -- it reports the raw numeric deltas;
  classification (SCENE_RESIDENT_DOMINANT / PER_RUN_NATIVE_RETENTION_
  DOMINANT / MIXED / INCONCLUSIVE) is applied by the reviewing analyst
  from those numbers, not by an arbitrary hardcoded threshold in this
  script.

  AFTER the production run, this script performs the ONE full external
  85-eligible/78-excluded semantic verification (the only one in this
  whole two-phase diagnostic), checking the final aggregate hash against
  the already-qualified All-Shots state and the final target identities
  against the already-qualified 85/78 sets. No production command runs
  after this heavyweight verification.

Output:
  C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r2_phase2_result.json
  C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r2_phase2_result_summary.txt
  C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r2_phase2_production_log.txt

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
EXPECTED_ALLSHOTS_HASH = (
    "299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7"
)
EXPECTED_TOTALS = {
    "total_shots": 15,
    "total_targets": 163,
    "eligible_targets": 85,
    "excluded_targets": 78,
    "distinct_model_names": 22,
    "distinct_fold_vocabulary_hashes_among_eligible": 21,
}

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r2_phase2_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r2_phase2_result_summary.txt"
PRODUCTION_LOG_PRESERVE_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r2_phase2_production_log.txt"
PHASE1_RESULT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r2_phase1_result.json"

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

FINGERPRINT_FUNCTION_RANGES = [
    ("ProbeError_class", 791, 792),
    ("NativePostFallback_class", 795, 796),
    ("native_ptr", 802, 812),
    ("to_unicode", 834, 844),
    ("ascii_fold", 846, 858),
    ("handle", 860, 861),
    ("name_fn", 863, 867),
    ("typ", 869, 873),
    ("attr", 875, 879),
    ("scalar", 881, 893),
    ("arr", 895, 927),
    ("attribute_name", 929, 933),
    ("attribute_type", 935, 939),
    ("iter_attributes", 941, 964),
    ("element_ref_pairs", 966, 1004),
    ("reachable", 1006, 1039),
    ("is_visible", 1041, 1053),
    ("is_selectable", 1055, 1064),
    ("is_snappable", 1066, 1075),
    ("_component_value", 1077, 1092),
    ("_parse_rgba_text", 1094, 1117),
    ("group_color_rgba", 1119, 1182),
    ("children", 1184, 1189),
    ("direct_controls", 1191, 1192),
    ("path_string", 1194, 1198),
    ("capture_tree", 1200, 1334),
    ("master_lookup", 1954, 2011),
    ("one_membership", 2013, 2024),
    ("immediate_parent_path", 2026, 2041),
    ("first_path_part", 2043, 2058),
    ("find_direct_child", 2060, 2082),
    ("discover_rig_context", 3299, 3436),
    ("strip_reconciliation_wrapper", 3439, 3454),
    ("canonicalize_rig_source_snapshot", 3457, 3541),
    ("capture_snapshot_explicit", 3544, 3726),
]
FINGERPRINT_MODULE_CONSTANTS = {
    "RIG_RECON_ROOT": "__RIG_VISIBLE_RECON__",
    "MASTER_RECON_ROOT": "__MASTER_VISIBLE_RECON__",
}


class CheckpointF1R2Phase2Error(Exception):
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


def b_ascii_fold(value):
    s = b_to_unicode(value)
    out = []
    for ch in s:
        o = ord(ch)
        if 65 <= o <= 90:
            out.append(chr(o + 32))
        else:
            out.append(ch)
    return u"".join(out)


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
                raise CheckpointF1R2Phase2Error(
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


def b_get_transform_controls(aset):
    return [c for c in b_arr(aset, "controls") if b_typ(c) == u"DmeTransformControl"]


def b_get_root_group(aset):
    try:
        return aset.GetRootControlGroup()
    except Exception:
        return None


def stable_hash(values):
    hasher = hashlib.sha256()
    for index, item in enumerate(sorted(values)):
        if index:
            hasher.update(b"\n")
        hasher.update(item.encode("utf-8"))
    return hasher.hexdigest()


def build_independent_witness():
    if not bool(sfmApp.HasDocument()):
        return None, None, "No SFM document is open."

    all_shots = list(sfmApp.GetShots())
    if not all_shots:
        return None, None, "sfmApp.GetShots() returned zero shots."

    global_aset_ptr_seen = set()
    targets = []

    for shot in all_shots:
        shot_ptr = b_native_ptr(shot)
        shot_name = b_name(shot)

        try:
            animation_sets = list(shot.animationSets)
        except Exception:
            animation_sets = []

        for aset in animation_sets:
            aset_ptr = b_native_ptr(aset)
            aset_name = b_name(aset)
            is_duplicate = aset_ptr is not None and aset_ptr in global_aset_ptr_seen
            if aset_ptr is not None:
                global_aset_ptr_seen.add(aset_ptr)

            game_model = b_get_game_model(aset)
            model_backed = game_model is not None
            model_name = b_get_model_name(game_model) if model_backed else None
            root_group = b_get_root_group(aset)
            root_valid = bool(root_group is not None and b_native_ptr(root_group))
            eligible = bool(model_backed and root_valid and not is_duplicate)

            transform_controls = b_get_transform_controls(aset)
            control_count = len(transform_controls)
            folded_names = set(b_ascii_fold(b_name(c)) for c in transform_controls)
            fold_vocabulary_hash = stable_hash(sorted(folded_names)) if folded_names else None

            category = "excluded" if not eligible else "eligible"

            targets.append({
                "shot_ptr": shot_ptr, "shot_name": shot_name,
                "aset_ptr": aset_ptr, "aset_name": aset_name, "is_duplicate_aset_ptr": is_duplicate,
                "model_backed": model_backed, "model_name": model_name,
                "root_group_valid": root_valid, "eligible": eligible,
                "control_count": control_count, "fold_vocabulary_hash": fold_vocabulary_hash,
                "category": category,
            })

    totals = {
        "total_shots": len(all_shots),
        "total_targets": len(targets),
        "eligible_targets": sum(1 for t in targets if t["category"] != "excluded"),
        "excluded_targets": sum(1 for t in targets if t["category"] == "excluded"),
        "distinct_model_names": len(set(t["model_name"] for t in targets if t.get("model_name"))),
        "distinct_fold_vocabulary_hashes_among_eligible": len(set(
            t["fold_vocabulary_hash"] for t in targets if t["category"] != "excluded" and t.get("fold_vocabulary_hash")
        )),
    }

    return {"targets": targets, "totals": totals}, None, None


def dumps_sorted(value):
    return json.dumps(value, sort_keys=True)


def target_key(t):
    return u"%s|%s" % (t["shot_name"], t["aset_name"])


def excluded_witness_row(t):
    return {
        "shot_name": t["shot_name"],
        "aset_name": t["aset_name"],
        "model_backed": t["model_backed"],
        "model_name": t["model_name"],
        "root_group_valid": t["root_group_valid"],
        "is_duplicate_aset_ptr": t["is_duplicate_aset_ptr"],
        "control_count": t["control_count"],
        "fold_vocabulary_hash": t["fold_vocabulary_hash"],
        "category": t["category"],
    }


def per_target_hash(value):
    return hashlib.sha256(dumps_sorted(value).encode("utf-8")).hexdigest()


def compute_target_hashes(fingerprint_dict):
    return dict((k, per_target_hash(v)) for k, v in fingerprint_dict.items())


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


def read_phase1_evidence():
    """Best-effort read of Phase 1's own evidence artifact -- never
    raises. Returns (dict_or_None, error_or_None)."""
    try:
        if not os.path.exists(PHASE1_RESULT_PATH):
            return None, "Phase 1 result file not found at %r" % (PHASE1_RESULT_PATH,)
        with open(PHASE1_RESULT_PATH, "rb") as f:
            return json.load(f), None
    except Exception as exc:
        return None, repr(exc)


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
    "phase1_comparison": {},
    "final_full_verification": None,
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
fp_ns = None
capture_snapshot_explicit_fn = None
eligible_targets_of_interest = None
initial_excluded_rows = None

try:
    report["memory_snapshots"]["idle_after_loading_normalized_copy"] = memory_snapshot()

    phase1_data, phase1_read_error = read_phase1_evidence()
    if phase1_read_error is not None:
        anomaly("Could not read Phase 1 evidence for comparison: %s" % phase1_read_error)
    report["phase1_comparison"]["phase1_read_error"] = phase1_read_error
    phase1_idle_before_run = ((phase1_data or {}).get("memory_snapshots") or {}).get("idle_before_run")
    report["phase1_comparison"]["phase1_idle_before_run"] = phase1_idle_before_run
    if phase1_idle_before_run and phase1_idle_before_run.get("available"):
        this_idle = report["memory_snapshots"]["idle_after_loading_normalized_copy"]
        if this_idle.get("available"):
            report["phase1_comparison"]["serialized_resident_working_set_delta_bytes"] = (
                this_idle["working_set_bytes"] - phase1_idle_before_run["working_set_bytes"]
            )
            report["phase1_comparison"]["serialized_resident_private_delta_bytes"] = (
                this_idle["pagefile_usage_bytes"] - phase1_idle_before_run["pagefile_usage_bytes"]
            )

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
        raise CheckpointF1R2Phase2Error("One or more pre-flight SHA-256 checks failed -- refusing to proceed.")

    report["provenance"]["production_normalizer_sha256"] = production_sha
    report["provenance"]["canonical_master_sha256"] = master_sha

    pre_witness, _sbn, witness_error = build_independent_witness()
    if witness_error is not None:
        raise CheckpointF1R2Phase2Error("Could not build independent witness: %s" % witness_error)
    report["fixture_totals"] = pre_witness["totals"]
    for key, expected_value in EXPECTED_TOTALS.items():
        actual_value = pre_witness["totals"].get(key)
        check("fixture.totals.%s_matches_required" % key, actual_value == expected_value, (actual_value, expected_value))

    initial_eligible_rows = [t for t in pre_witness["targets"] if t["category"] != "excluded"]
    initial_excluded_rows = [t for t in pre_witness["targets"] if t["category"] == "excluded"]
    check("fixture.eligible_row_count_is_85", len(initial_eligible_rows) == 85, len(initial_eligible_rows))
    check("fixture.excluded_row_count_is_78", len(initial_excluded_rows) == 78, len(initial_excluded_rows))
    eligible_targets_of_interest = [(t["shot_name"], t["aset_name"]) for t in initial_eligible_rows]
    del pre_witness, initial_eligible_rows

    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointF1R2Phase2Error(
            "STARTING-STATE / FIXTURE MISMATCH -- aborting BEFORE any invocation of the "
            "production Normalizer or scene mutation. Confirm the operator opened the "
            "normalized diagnostic copy from Phase 1, not the original fixture."
        )

    main_window = sfmApp.GetMainWindow()
    check("normalizer.main_window_available", main_window is not None)
    write_rolling_evidence()

    # --- Run production All Shots ONCE against the already-normalized
    #     scene. ---
    report["memory_snapshots"]["before_production_run"] = memory_snapshot()
    command_start_time = time.time()
    prod_ns = {}
    run_started = False
    run_completed_cleanly = False
    try:
        exec(compile(production_bytes, "<installed_production_normalizer_f1r2_phase2>", "exec"), prod_ns)
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
        sys.stdout.write("\n>>> Choose 'All Shots' in the real dialog that just appeared. <<<\n\n")
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

    if resource_checkpoint_summary.get("first_checkpoint") and resource_checkpoint_summary.get("last_checkpoint"):
        first_cp = resource_checkpoint_summary["first_checkpoint"]
        last_cp = resource_checkpoint_summary["last_checkpoint"]
        report["phase1_comparison"]["per_run_private_delta_bytes"] = (
            (last_cp.get("private") or 0) - (first_cp.get("private") or 0)
        )
        report["phase1_comparison"]["per_run_free_vas_delta_bytes"] = (
            (last_cp.get("mem_free") or 0) - (first_cp.get("mem_free") or 0)
        )
        report["phase1_comparison"]["per_run_largest_free_delta_bytes"] = (
            (last_cp.get("largest_free") or 0) - (first_cp.get("largest_free") or 0)
        )

    authority_evidence = {}
    try:
        authority_runtime = prod_ns.get("authority_runtime")
        authority_evidence["module_binding_present"] = authority_runtime is not None
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

    # --- The ONE full external semantic verification in this whole
    #     two-phase diagnostic. No production command runs after this. ---
    all_lines = production_bytes.decode("ascii").splitlines()
    blocks = []
    for label, start, end in FINGERPRINT_FUNCTION_RANGES:
        blocks.append("\n".join(all_lines[start - 1:end]))
    combined_source = "\n\n".join(blocks)
    fp_ns = dict(FINGERPRINT_MODULE_CONSTANTS)
    fp_ns["hashlib"] = hashlib
    exec(compile(combined_source, "<checkpoint_f1r2_phase2_fingerprint_functions>", "exec"), fp_ns)
    capture_snapshot_explicit_fn = fp_ns["capture_snapshot_explicit"]
    del all_lines, blocks, combined_source

    def canonicalize_snapshot(snap):
        clean = dict(snap)
        for key in ("shot_handle", "animation_set_handle", "root_handle", "rig_handle", "registry_handle", "label"):
            clean.pop(key, None)
        clean.pop("control_handles", None)
        return clean

    def capture_all(label, targets_of_interest_local):
        result = {}
        all_shots_now = list(sfmApp.GetShots())
        shots_by_name_now = {}
        for shot in all_shots_now:
            shots_by_name_now.setdefault(b_name(shot), []).append(shot)
        for shot_name, aset_name in targets_of_interest_local:
            matches = shots_by_name_now.get(shot_name, [])
            if len(matches) != 1:
                anomaly("%s capture: shot %r did not resolve to exactly one live shot (found %d)."
                        % (label, shot_name, len(matches)))
                continue
            shot = matches[0]
            target_aset = None
            try:
                for aset in shot.animationSets:
                    if b_name(aset) == aset_name:
                        target_aset = aset
                        break
            except Exception as exc:
                anomaly("%s capture: shot %r animationSets raised: %r" % (label, shot_name, exc))
                continue
            if target_aset is None:
                anomaly("%s capture: animation set %r not found under shot %r." % (label, aset_name, shot_name))
                continue
            try:
                snap = capture_snapshot_explicit_fn(shot, target_aset, label)
                result[u"%s|%s" % (shot_name, aset_name)] = canonicalize_snapshot(snap)
            except Exception as exc:
                anomaly("%s capture: capture_snapshot_explicit raised for %r/%r: %r"
                        % (label, shot_name, aset_name, exc))
        return result

    report["memory_snapshots"]["before_final_full_verification"] = memory_snapshot()
    raw_final_eligible = capture_all("FINAL_FULL_VERIFICATION", eligible_targets_of_interest)
    check("final.eligible_capture_count_is_85", len(raw_final_eligible) == 85, len(raw_final_eligible))
    final_aggregate_hash = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in raw_final_eligible.items()])
    final_eligible_hashes = compute_target_hashes(raw_final_eligible)
    del raw_final_eligible

    raw_final_excluded = dict((target_key(t), excluded_witness_row(t)) for t in initial_excluded_rows)
    final_excluded_hashes = compute_target_hashes(raw_final_excluded)
    del raw_final_excluded

    final_aggregate_matches_expected = bool(final_aggregate_hash == EXPECTED_ALLSHOTS_HASH)
    check("final.aggregate_hash_matches_expected_allshots", final_aggregate_matches_expected, final_aggregate_hash)
    check("final.excluded_capture_count_is_78", len(final_excluded_hashes) == 78, len(final_excluded_hashes))

    report["final_full_verification"] = {
        "aggregate_hash": final_aggregate_hash,
        "expected_aggregate_hash": EXPECTED_ALLSHOTS_HASH,
        "aggregate_hash_matches_expected": final_aggregate_matches_expected,
        "eligible_target_hashes": final_eligible_hashes,
        "excluded_target_hashes": final_excluded_hashes,
        "eligible_hashes_checksum": stable_hash([u"%s=%s" % (k, v) for k, v in final_eligible_hashes.items()]),
        "excluded_hashes_checksum": stable_hash([u"%s=%s" % (k, v) for k, v in final_excluded_hashes.items()]),
    }
    del final_eligible_hashes, final_excluded_hashes
    gc.collect()
    report["memory_snapshots"]["after_final_full_verification"] = memory_snapshot()
    write_rolling_evidence()

    del fp_ns, capture_snapshot_explicit_fn

except CheckpointF1R2Phase2Error as gate_exc:
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
final_verification_present = bool(report.get("final_full_verification"))
report["overall_pass"] = bool(all_checks_passed and completed_without_exception and final_verification_present)

json_write_ok, json_write_error, _reparsed = write_json_atomic(JSON_OUTPUT_PATH, report)

summary_lines = []
summary_lines.append("SFM CHECKPOINT F1-R2 PHASE 2 -- NORMALIZED-COPY RETEST")
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
if report.get("gate_failure"):
    summary_lines.append("*** GATE FAILURE: aborted BEFORE any production Normalizer invocation. ***")
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
summary_lines.append("--- COMPARISON (raw deltas only -- classification applied by the reviewing analyst) ---")
for k in sorted((report.get("phase1_comparison") or {}).keys()):
    summary_lines.append("  %s: %r" % (k, report["phase1_comparison"][k]))
summary_lines.append("")
summary_lines.append("--- MEMORY SNAPSHOTS ---")
for k in sorted((report.get("memory_snapshots") or {}).keys()):
    summary_lines.append("  %s: %r" % (k, report["memory_snapshots"][k]))
summary_lines.append("")
fv = report.get("final_full_verification") or {}
summary_lines.append("final_full_verification.aggregate_hash=%r" % fv.get("aggregate_hash"))
summary_lines.append("final_full_verification.aggregate_hash_matches_expected=%r" % fv.get("aggregate_hash_matches_expected"))
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
        "\nPhase 2 reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok)
    )
    sys.stdout.write("\nDO NOT SAVE. This diagnostic is complete.\n")
except Exception:
    pass
