# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint F1-R3: Native-Only Retention
Attribution.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: **THIS CHECKPOINT MUTATES THE SCENE.** It runs the real
native Rebuild callback for every production-eligible target, exactly as
production does. It does NOT run contextual classification, policy
planning, the composer, or any semantic capture/verification. **Do not
save afterward.**

Purpose (see F1_R3_NATIVE_PATH_AUDIT.md for the full static audit this
design is built from):

  F1-R2 established PASS as an attribution checkpoint: the reopened
  normalized scene itself did NOT retain the prior run's large memory
  increase (serialized-resident deltas were small and negative), but a
  second All-Shots production run against that same normalized scene
  reproduced essentially the same process-retained pressure (~+265 MiB
  private / ~-238 MiB free VAS / ~-111 MiB largest free block). This
  establishes PER-RUN PROCESS-RETAINED PRESSURE, but not its internal
  owner. F1-R3 answers exactly one question: on the SAME normalized
  scene, in a fresh process, how much of that retained pressure occurs
  from native Rebuild ALONE, across the same 62 production-eligible
  targets, in the same order, WITHOUT the contextual reconciliation/
  composer/capture workload that normally follows each native call.

  This is a measurement checkpoint. It does not implement or authorize
  any optimization, and does not reopen O3.

Design (full static audit in F1_R3_NATIVE_PATH_AUDIT.md; summary):
  1. exec()s the pinned, SHA-256-verified production bytes into a fresh
     namespace -- exactly as every earlier checkpoint does. This
     unavoidably triggers the real scope-choice dialog and runs
     production's own start() synchronously through snapshot_work()
     (the exact eligibility gate) and the one-time whole-session
     fingerprint baseline, before returning control here. This one-time
     cost is NOT skipped (it cannot be, without reimplementing the
     eligibility gate from scratch) but it is NOT measured, because this
     script's own "before" checkpoint is taken strictly after exec()
     returns.
  2. Locates the already-constructed run instance (same
     main_window.findChildren(QtCore.QObject) + objectName()==
     RUN_LOCK_NAME technique every earlier checkpoint already uses).
  3. Sets instance.finished = True IMMEDIATELY, before ever pumping the
     Qt event loop -- every state-machine method on the real instance
     begins "if self.finished: return" (verified by direct reading), so
     this permanently and safely neutralizes production's own further
     progression (including the already-scheduled first-shot QTimer
     callback) without any monkey-patch and without any risk from
     pumping events later for this script's own purposes.
  4. Reads instance.work directly -- the exact, already-computed,
     production-ordered target inventory. Never re-derives the
     eligibility gate.
  5. For each shot, in instance.work's own order: activates the shot the
     same way production does (sfmApp.SetHeadTimeInSeconds + immediate
     GetShotAtCurrentTime verification). For each target in that shot,
     in order: re-resolves the live aset object fresh (same aset_ptr+
     name uniqueness match instance.contextualizer_resolve_resume_target
     itself uses, reused via a narrow helper that omits only the single
     production_terminal_results membership check that method requires
     for index>0 -- a fact that only exists in production's fuller
     pipeline this script deliberately never runs; see the audit doc),
     then executes ONLY the native-Rebuild-relevant guarded slice of
     run_target_transaction: pointer-stability check, get_game_model/
     get_root_group validity checks, dm.SetUndoEnabled(False)+verify,
     native_master_protect_acquire, assert_master_stable(),
     self.rebuild(ctypes.c_void_p(aset_ptr)), then in a finally:
     native_master_protect_release + restore Undo state -- every one of
     these calls the REAL instance's own already-qualified method or a
     reused module-level function, never reimplemented.
  6. Never calls discover_rig_context, capture_snapshot_explicit,
     production_generic_composer, preflight_reconciliation_plan, or any
     other contextual/composer/capture function.
  7. Resource checkpoints via instance.contextualizer_resource_checkpoint
     (the same helper production itself uses -- writes to the same
     production log in the exact CONTEXTUALIZER_RESOURCE_CHECKPOINT
     format every earlier checkpoint's own parser already reads) at
     low cadence only: command start, after every 4th completed shot,
     final native target complete, harness teardown, post-GC.
  8. No save. No exhaustive semantic verification of any kind.

Do NOT run this against the original testscripts.dmx fixture -- this
script structurally refuses to proceed if the currently open document's
own filename does not match the expected normalized-copy filename.
"""
import ctypes
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
EXPECTED_NORMALIZED_COPY_FILENAME = u"F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx"
FORBIDDEN_ORIGINAL_FIXTURE_FILENAME = u"testscripts.dmx"

EXPECTED_TOTAL_SHOTS = 15
EXPECTED_MODEL_BACKED_TARGETS = 85
EXPECTED_GATE_STATIC_SKIPS = 12
EXPECTED_GATE_FOLLOWER_SKIPS = 4
EXPECTED_GATE_LOWBONE_SKIPS = 7
EXPECTED_GATE_FAILCLOSED_PROCESS = 0
EXPECTED_ELIGIBLE_NATIVE_TARGETS = 62

# Baseline established by F1-R2 Phase 2's own real production interval
# (CP0_COMMAND_START -> FINAL_REPORT_ENTRY), reused here for the ratio
# report only -- never as a pass/fail threshold.
PRODUCTION_PRIVATE_DELTA = 265461760
PRODUCTION_FREE_VAS_DELTA = -237633536
PRODUCTION_LARGEST_FREE_DELTA = -110985216

SHOT_CHECKPOINT_STRIDE = 4  # low-cadence: checkpoint after every 4th completed shot

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r3_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r3_result_summary.txt"
PRODUCTION_LOG_PRESERVE_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r3_native_only_log.txt"

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


class CheckpointF1R3Error(Exception):
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


def b_name(obj):
    try:
        return b_to_unicode(obj.GetName())
    except Exception:
        return u"<UNNAMED>"


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
    head = body[:vas_error_idx] if vas_error_idx >= 0 else body
    fields = {}
    for token in head.split(" "):
        if not token or "=" not in token:
            continue
        k, _sep, v = token.partition("=")
        fields[k] = _typed_checkpoint_value(v)
    return fields


def parse_all_resource_checkpoints(log_text):
    out = []
    for line in log_text.splitlines():
        parsed = parse_resource_checkpoint_line(line)
        if parsed is not None:
            out.append(parsed)
    return out


def checkpoints_by_label(log_text, label):
    return [c for c in parse_all_resource_checkpoints(log_text) if c.get("label") == label]


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


def sequence_checksum(ordered_pairs):
    payload = json.dumps(ordered_pairs, ensure_ascii=True)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


# ---------------------------------------------------------------------------
# Narrow, separately-justified target re-resolution helper.
#
# Reuses instance.contextualizer_resolve_resume_target()'s own core
# matching logic (aset_ptr + name uniqueness within the CURRENT shot's own
# animationSets), omitting only the single production_terminal_results
# membership check that method requires for the second-or-later target in
# a shot -- a fact that only exists once production's own terminal
# semantic-fingerprint capture has run, which this checkpoint deliberately
# never performs. See F1_R3_NATIVE_PATH_AUDIT.md for the full justification.
# This does not alter native Rebuild's own semantics; it only affects how
# the live aset object is located immediately beforehand.
# ---------------------------------------------------------------------------

def native_only_resolve_target(instance, shot_record, target):
    instance.contextualizer_assert_run_lock_present()
    instance.assert_master_stable()

    at_head = sfmApp.GetShotAtCurrentTime()

    if at_head is None or native_ptr(at_head) != shot_record["ptr"]:
        raise CheckpointF1R3Error(
            "Native-only target resolve lost expected shot context."
        )

    matches = []

    for aset in at_head.animationSets:
        try:
            aset_ptr = native_ptr(aset)
        except Exception:
            continue

        if aset_ptr != target["ptr"]:
            continue

        try:
            aset_name = b_to_unicode(aset.GetName())
        except Exception:
            aset_name = u""

        if aset_name != b_to_unicode(target["name"]):
            continue

        matches.append(aset)

    if len(matches) != 1:
        raise CheckpointF1R3Error(
            "Native-only target resolve failed unique match: shot=%r target=%r matches=%d."
            % (b_to_unicode(shot_record["name"]), b_to_unicode(target["name"]), len(matches))
        )

    return matches[0]


def native_only_rebuild_target(instance, dm, aset, expected_ptr):
    """Reproduces exactly the guarded slice of run_target_transaction()
    surrounding self.rebuild() -- pointer-stability check, model/root
    validity, Undo-disable, Master-protection acquire, assert_master_
    stable(), the native call itself, then release/restore in a finally.
    Never performs discovery, capture, classification, or composer. Every
    call below is either the real instance's own already-qualified
    method or a reused module-level function -- none reimplemented."""
    aset_ptr = native_ptr(aset)

    if aset_ptr != expected_ptr:
        raise CheckpointF1R3Error(
            "Native-only pointer-stability check failed: expected=%r actual=%r."
            % (expected_ptr, aset_ptr)
        )

    if instance.get_game_model(aset) is None:
        raise CheckpointF1R3Error("Native-only: animation set lost model backing.")

    root = instance.get_root_group(aset)
    if root is None or not native_ptr(root):
        raise CheckpointF1R3Error("Native-only: animation set lost its root control group.")

    undo_prior = bool(dm.IsUndoEnabled())
    dm.SetUndoEnabled(False)
    if bool(dm.IsUndoEnabled()):
        raise CheckpointF1R3Error("Native-only: could not disable Undo.")

    native_master_protect_handle = native_master_protect_acquire(instance.master_path)
    if native_master_protect_handle is None:
        raise CheckpointF1R3Error(
            "Native-only: could not acquire native Master protection handle."
        )

    undo_restored = False

    try:
        instance.assert_master_stable()

        t0 = time.time()
        instance.rebuild(ctypes.c_void_p(aset_ptr))
        t1 = time.time()

        return t1 - t0
    finally:
        try:
            native_master_protect_release(native_master_protect_handle)
        except Exception:
            pass

        try:
            dm.SetUndoEnabled(undo_prior)
            undo_restored = bool(dm.IsUndoEnabled() == undo_prior)
        except Exception:
            undo_restored = False

        if not undo_restored:
            raise CheckpointF1R3Error("Native-only: Undo-enabled state failed to restore.")


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

report = {
    "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "python_version": sys.version,
    "checks": [],
    "anomalies": ANOMALIES,
    "provenance": {},
    "shots_processed": [],
    "targets_processed": [],
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
instance = None

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
        raise CheckpointF1R3Error("Pre-flight SHA-256 check failed -- refusing to proceed.")
    report["provenance"]["production_normalizer_sha256"] = production_sha
    report["provenance"]["canonical_master_sha256"] = master_sha

    if not bool(sfmApp.HasDocument()):
        raise CheckpointF1R3Error("No SFM document is open.")

    root_for_filename = sfmApp.GetDocumentRoot()
    if root_for_filename is None:
        raise CheckpointF1R3Error("sfmApp.GetDocumentRoot() returned None.")
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
        raise CheckpointF1R3Error(
            "REFUSING TO RUN against the original disposable qualification fixture (%r) -- "
            "F1-R3 must run only against the F1-R2 Phase 2 normalized copy." % (open_basename,)
        )
    if open_basename.lower() != EXPECTED_NORMALIZED_COPY_FILENAME.lower():
        raise CheckpointF1R3Error(
            "Open document (%r) does not match the expected normalized-copy filename (%r)."
            % (open_basename, EXPECTED_NORMALIZED_COPY_FILENAME)
        )

    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointF1R3Error("Starting-state fixture gate failed -- aborting before any production invocation.")

    main_window = sfmApp.GetMainWindow()
    check("f1r3.main_window_available", main_window is not None)
    write_rolling_evidence()

    before_memory = None
    before_vas = None

    prod_ns = {}
    try:
        exec(compile(production_bytes, "<installed_production_normalizer_f1r3>", "exec"), prod_ns)
    except Exception as exc:
        anomaly("Production Normalizer execution raised: %r" % (exc,))
        anomaly(traceback.format_exc())

    # NOTE: vs/sfmApp are SFM-injected ambient globals already available in
    # THIS script's own top-level namespace (already used above, before
    # exec() ever ran, e.g. sfmApp.HasDocument()) -- they are NOT literal
    # keys inside the fresh prod_ns dict exec() was given, so they must
    # NOT be re-extracted from prod_ns (doing so would silently overwrite
    # them with None). Only genuinely production-internal module-level
    # names are extracted below.
    native_ptr = prod_ns.get("native_ptr")
    native_master_protect_acquire = prod_ns.get("native_master_protect_acquire")
    native_master_protect_release = prod_ns.get("native_master_protect_release")
    contextualizer_process_memory_sample = prod_ns.get("contextualizer_process_memory_sample")
    contextualizer_virtual_address_sample = prod_ns.get("contextualizer_virtual_address_sample")

    for required_name, required_value in (
        ("native_ptr", native_ptr),
        ("native_master_protect_acquire", native_master_protect_acquire),
        ("native_master_protect_release", native_master_protect_release),
        ("contextualizer_process_memory_sample", contextualizer_process_memory_sample),
        ("contextualizer_virtual_address_sample", contextualizer_virtual_address_sample),
    ):
        if required_value is None:
            raise CheckpointF1R3Error("Required production name not found in exec'd namespace: %s" % required_name)

    run_lock_name = prod_ns.get("RUN_LOCK_NAME")
    if run_lock_name is None:
        raise CheckpointF1R3Error("RUN_LOCK_NAME not found in exec'd namespace.")

    for child in main_window.findChildren(QtCore.QObject):
        try:
            if b_to_unicode(child.objectName()) == run_lock_name:
                instance = child
                break
        except Exception:
            continue

    check("f1r3.run_instance_located", instance is not None)
    if instance is None:
        raise CheckpointF1R3Error("Could not locate the already-constructed run instance immediately after exec().")

    # Neutralize the real instance's own further progression BEFORE ever
    # pumping the Qt event loop -- see F1_R3_NATIVE_PATH_AUDIT.md. Every
    # state-machine method begins "if self.finished: return".
    instance.finished = True
    check("f1r3.real_instance_neutralized", bool(instance.finished))

    work = instance.work
    check("f1r3.instance_work_present", bool(work))

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

    ordered_pairs = []
    for shot_record in work:
        shot_name = b_to_unicode(shot_record["name"])
        for target in shot_record["targets"]:
            ordered_pairs.append((shot_name, b_to_unicode(target["name"])))

    checksum = sequence_checksum(ordered_pairs)
    report["provenance"]["ordered_sequence_checksum_sha256"] = checksum
    report["provenance"]["ordered_sequence_length"] = len(ordered_pairs)

    dm = vs.g_pDataModel

    # --- Before checkpoint (this script's own measured interval starts
    #     here -- strictly AFTER exec()'s own unavoidable one-time
    #     whole-session fingerprint baseline has already been paid). ---
    instance.contextualizer_resource_checkpoint("F1R3_CP0_NATIVE_ONLY_START", True)
    before_memory = contextualizer_process_memory_sample()
    before_vas = contextualizer_virtual_address_sample()
    report["memory_snapshots"] = {"before": {"memory": before_memory, "vas": before_vas}}
    write_rolling_evidence()

    total_native_calls = 0
    total_native_elapsed = 0.0
    shots_completed = 0

    for shot_index, shot_record in enumerate(work):
        shot_name = b_to_unicode(shot_record["name"])

        try:
            sfmApp.SetHeadTimeInSeconds(shot_record["midpoint"])
        except Exception as exc:
            raise CheckpointF1R3Error("Could not move playhead into %r: %r" % (shot_name, exc))

        at_head = sfmApp.GetShotAtCurrentTime()
        if at_head is None or native_ptr(at_head) != shot_record["ptr"]:
            raise CheckpointF1R3Error("Playhead did not enter expected shot %r." % (shot_name,))

        shot_targets_ok = 0

        for target_index, target in enumerate(shot_record["targets"]):
            target_name = b_to_unicode(target["name"])

            aset = native_only_resolve_target(instance, shot_record, target)
            elapsed = native_only_rebuild_target(instance, dm, aset, target["ptr"])

            total_native_calls += 1
            total_native_elapsed += elapsed
            shot_targets_ok += 1

            report["targets_processed"].append({
                "shot": shot_name,
                "target": target_name,
                "elapsed_seconds": elapsed,
            })

        shots_completed += 1
        report["shots_processed"].append({
            "shot": shot_name,
            "target_count": len(shot_record["targets"]),
            "targets_ok": shot_targets_ok,
        })

        if shots_completed % SHOT_CHECKPOINT_STRIDE == 0 or shot_index == len(work) - 1:
            instance.contextualizer_resource_checkpoint(
                "F1R3_CP_SHOT_%d_OF_%d" % (shots_completed, len(work)),
                True,
            )
            write_rolling_evidence()

    check("native.total_calls_matches_expected_target_count", total_native_calls == EXPECTED_ELIGIBLE_NATIVE_TARGETS, total_native_calls)
    check("native.all_shots_completed", shots_completed == len(work), shots_completed)
    check("neutralization.real_pipeline_never_advanced", getattr(instance, "total_shots_processed", 0) == 0, getattr(instance, "total_shots_processed", None))

    report["native_summary"] = {
        "total_calls": total_native_calls,
        "total_elapsed_seconds": total_native_elapsed,
    }

    instance.contextualizer_resource_checkpoint("F1R3_CP_FINAL_NATIVE_TARGET_COMPLETE", True)

    # --- After / harness-teardown checkpoint. ---
    after_memory = contextualizer_process_memory_sample()
    after_vas = contextualizer_virtual_address_sample()
    instance.contextualizer_resource_checkpoint("F1R3_TEARDOWN_BEFORE_GC", True)

    gc.collect()

    postgc_memory = contextualizer_process_memory_sample()
    postgc_vas = contextualizer_virtual_address_sample()
    instance.contextualizer_resource_checkpoint("F1R3_TEARDOWN_AFTER_GC", True)

    report["memory_snapshots"]["after"] = {"memory": after_memory, "vas": after_vas}
    report["memory_snapshots"]["after_gc"] = {"memory": postgc_memory, "vas": postgc_vas}

    def _delta(a, b, key):
        try:
            return a[key] - b[key]
        except Exception:
            return None

    native_private_delta = _delta(after_memory, before_memory, "private")
    native_free_vas_delta = _delta(after_vas, before_vas, "free")
    native_largest_free_delta = _delta(after_vas, before_vas, "largest_free")
    native_working_set_delta = _delta(after_memory, before_memory, "working_set")

    postgc_private_delta = _delta(postgc_memory, before_memory, "private")
    postgc_free_vas_delta = _delta(postgc_vas, before_vas, "free")
    postgc_largest_free_delta = _delta(postgc_vas, before_vas, "largest_free")

    def _ratio(native_value, production_value):
        if native_value is None or production_value in (None, 0):
            return None
        return float(native_value) / float(production_value)

    report["resource_deltas"] = {
        "native_private_delta": native_private_delta,
        "native_free_vas_delta": native_free_vas_delta,
        "native_largest_free_delta": native_largest_free_delta,
        "native_working_set_delta": native_working_set_delta,
        "postgc_private_delta": postgc_private_delta,
        "postgc_free_vas_delta": postgc_free_vas_delta,
        "postgc_largest_free_delta": postgc_largest_free_delta,
        "production_baseline": {
            "private_delta": PRODUCTION_PRIVATE_DELTA,
            "free_vas_delta": PRODUCTION_FREE_VAS_DELTA,
            "largest_free_delta": PRODUCTION_LARGEST_FREE_DELTA,
        },
        "ratios": {
            "native_private_ratio": _ratio(native_private_delta, PRODUCTION_PRIVATE_DELTA),
            "native_free_vas_loss_ratio": _ratio(native_free_vas_delta, PRODUCTION_FREE_VAS_DELTA),
            "native_largest_free_loss_ratio": _ratio(native_largest_free_delta, PRODUCTION_LARGEST_FREE_DELTA),
        },
    }

    check("resource.before_after_gc_deltas_captured", native_private_delta is not None and postgc_private_delta is not None)

except CheckpointF1R3Error as gate_exc:
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

try:
    with open(NORMALIZER_LOG_PATH, "rb") as f:
        log_bytes = f.read()
    preserve_ok, preserve_err = write_text_atomic(PRODUCTION_LOG_PRESERVE_PATH, log_bytes)
    if not preserve_ok:
        anomaly("Could not preserve native-only production log: %s" % preserve_err)
except Exception as exc:
    anomaly("Could not read native-only production log: %r" % (exc,))

json_write_ok, json_write_error, _r = write_json_atomic(JSON_OUTPUT_PATH, report)
if not json_write_ok:
    anomaly("Final JSON write failed: %s" % json_write_error)

summary_lines = []
summary_lines.append("SFM CHECKPOINT F1-R3 -- NATIVE-ONLY RETENTION ATTRIBUTION")
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
if report.get("gate_failure"):
    summary_lines.append("*** GATE FAILURE: aborted before or during the native-only run. ***")
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
if "provenance" in report:
    summary_lines.append("ordered_sequence_checksum_sha256=%r" % report["provenance"].get("ordered_sequence_checksum_sha256"))
    summary_lines.append("ordered_sequence_length=%r" % report["provenance"].get("ordered_sequence_length"))
if "native_summary" in report:
    summary_lines.append("native_total_calls=%r native_total_elapsed_seconds=%r" % (report["native_summary"]["total_calls"], report["native_summary"]["total_elapsed_seconds"]))
if "resource_deltas" in report:
    rd = report["resource_deltas"]
    summary_lines.append("native_private_delta=%r native_free_vas_delta=%r native_largest_free_delta=%r" % (rd["native_private_delta"], rd["native_free_vas_delta"], rd["native_largest_free_delta"]))
    summary_lines.append("postgc_private_delta=%r postgc_free_vas_delta=%r postgc_largest_free_delta=%r" % (rd["postgc_private_delta"], rd["postgc_free_vas_delta"], rd["postgc_largest_free_delta"]))
    summary_lines.append("ratios=%r" % (rd["ratios"],))
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
        "\nCheckpoint F1-R3 reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok)
    )
    sys.stdout.write("\nDO NOT SAVE. Restart SFM afterward.\n")
except Exception:
    pass
