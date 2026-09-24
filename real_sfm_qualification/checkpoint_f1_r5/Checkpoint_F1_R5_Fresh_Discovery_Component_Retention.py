# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint F1-R5: Fresh Discovery
Component (Allocation/Traversal) Retention.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: **THIS CHECKPOINT MUTATES THE SCENE, TWICE, IN ONE
CONTINUOUS SFM PROCESS.** It runs the real native Rebuild callback for
every production-eligible target, in both commands. **Do not save
afterward.**

Purpose (see F1_R5_ALLOCATION_TRAVERSAL_AUDIT.md for the full static
audit this design is built from):

  F1-R4 was accepted: PASS -- DISCOVERY_DOMINANT. Fresh discover_rig_
  context() traversal, repeated at the same 250 production semantic
  boundaries across the same 62 targets, reproduced the large majority
  of F1-R2's own full-production retained pressure. F1-R5 answers a
  narrower question: within that fresh-discovery cost, how much comes
  specifically from reachable()'s own whole-scene traversal/
  materialization (the ~94.4%-of-timing component O3-R2 already
  measured), as opposed to the smaller candidate/registry/ownership
  derivation that follows it -- using MEMORY retention evidence this
  time, not just timing.

  This is lifetime/allocation attribution, not a proposal to reuse stale
  discovery results. Freshness semantics remain mandatory: every
  production semantic boundary that currently requires a fresh
  observation still receives one in this checkpoint. This does not
  reopen O3's own rejected discovery-reuse/cache design, and does not
  implement any production change.

Design (full audit in F1_R5_ALLOCATION_TRAVERSAL_AUDIT.md; summary):
  reachable(start, max_elements=50000) is already an independently-
  defined, directly-callable module-level function inside the production
  Normalizer -- the exact code path production itself uses for the
  expensive whole-scene traversal component of every discover_rig_
  context() call. Calling scalar(shot,"scene") then reachable(scene)
  directly reproduces that component in isolation, using the identical,
  unmodified production code, with zero semantic difference from what
  production executes internally.

  F1-R4's own branch determination (which of the 62 targets take the
  3-site NATIVE_POST_ONLY_STATUS_MISMATCH branch versus the 5-site
  COMPOSER_ENTRY_PATH branch) requires the FULL discover_rig_context()
  result (status, rig_handle, owned_names_in_order, hidden_groups) at
  the PRE and NATIVE_POST sites for every target -- this is a genuine
  logical necessity of knowing which branch applies, not a measurement
  artifact, and cannot be avoided without abandoning the exact 62-target/
  250-site schedule F1-R4 already established. PRE+NATIVE_POST account
  for 124 of the 250 sites (62 x 2). The remaining 126 sites (32
  composer-entry targets x 3 extra sites each [composer-before,
  composer-after, terminal] = 96, plus 30 status-mismatch targets x 1
  extra site each [terminal] = 30) occur strictly AFTER the branch is
  already known. For these 126 sites specifically, this script
  substitutes the isolated traversal-only seam (reachable() alone) in
  place of the full discover_rig_context() call F1-R4 performed there.
  The 124 branch-determining sites remain full, correctness-complete
  fresh discovery calls, identical to F1-R4's own.

  Command 1 (native-only, identical to F1-R3's own design, reused
  verbatim): establishes THIS process's own native-only baseline, for a
  same-process matched comparison against command 2.
  Command 2 (native + PRE/NATIVE_POST full discovery for branch
  determination + isolated-traversal-only for the 126 remaining sites):
  the measurement this checkpoint exists to produce.

  Never performs contextual classification, policy planning, composer
  mutation, semantic snapshot/tree capture, direct-target semantic
  fingerprints, current-shot peer verification, or exhaustive semantic
  verification, in either command.

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

BRANCH_DISCOVERY_COUNTS = {
    "PRE_CAPTURE_UNSUPPORTED": 2,
    "NATIVE_POST_ONLY_STATUS_MISMATCH": 3,
    "NATIVE_POST_WRAPPER_SURVIVED": 3,
    "COMPOSER_ENTRY_PATH": 5,
}

# Baselines established by earlier real runs, reused here for ratio/
# comparison reporting only -- never as a pass/fail threshold.
PRODUCTION_PRIVATE_DELTA = 265461760
PRODUCTION_FREE_VAS_DELTA = -237633536
PRODUCTION_LARGEST_FREE_DELTA = -110985216
NATIVE_ONLY_PRIVATE_DELTA = 14307328
NATIVE_ONLY_FREE_VAS_DELTA = -2490368
NATIVE_ONLY_LARGEST_FREE_DELTA = 0
NATIVE_PLUS_FULL_DISCOVERY_PRIVATE_DELTA = 243748864
NATIVE_PLUS_FULL_DISCOVERY_FREE_VAS_DELTA = -221839360
NATIVE_PLUS_FULL_DISCOVERY_LARGEST_FREE_DELTA = -184778752

SHOT_CHECKPOINT_STRIDE = 4  # low-cadence: checkpoint after every 4th completed shot

COMMAND_SPECS = [
    (1, u"All Shots", u"native_only"),
    (2, u"All Shots", u"native_plus_isolated_traversal"),
]

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r5_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r5_result_summary.txt"
PRODUCTION_LOG_PRESERVE_TEMPLATE = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r5_production_log_command%d.txt"

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


class CheckpointF1R5Error(Exception):
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


def sequence_checksum(ordered_entries):
    payload = json.dumps(ordered_entries, ensure_ascii=True)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


# ---------------------------------------------------------------------------
# Narrow, separately-justified target re-resolution/native-rebuild helpers
# (identical to F1-R3/F1-R4's own, reused verbatim).
# ---------------------------------------------------------------------------

def native_only_resolve_target(instance, shot_record, target):
    instance.contextualizer_assert_run_lock_present()
    instance.assert_master_stable()

    at_head = sfmApp.GetShotAtCurrentTime()

    if at_head is None or native_ptr(at_head) != shot_record["ptr"]:
        raise CheckpointF1R5Error(
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
        raise CheckpointF1R5Error(
            "Native-only target resolve failed unique match: shot=%r target=%r matches=%d."
            % (b_to_unicode(shot_record["name"]), b_to_unicode(target["name"]), len(matches))
        )

    return matches[0]


def native_only_rebuild_target(instance, dm, aset, expected_ptr):
    """Identical to F1-R3/F1-R4's own native_only_rebuild_target -- the
    exact guarded slice of run_target_transaction() surrounding
    self.rebuild(). Reused verbatim, not reimplemented."""
    aset_ptr = native_ptr(aset)

    if aset_ptr != expected_ptr:
        raise CheckpointF1R5Error(
            "Native-only pointer-stability check failed: expected=%r actual=%r."
            % (expected_ptr, aset_ptr)
        )

    if instance.get_game_model(aset) is None:
        raise CheckpointF1R5Error("Native-only: animation set lost model backing.")

    root = instance.get_root_group(aset)
    if root is None or not native_ptr(root):
        raise CheckpointF1R5Error("Native-only: animation set lost its root control group.")

    undo_prior = bool(dm.IsUndoEnabled())
    dm.SetUndoEnabled(False)
    if bool(dm.IsUndoEnabled()):
        raise CheckpointF1R5Error("Native-only: could not disable Undo.")

    native_master_protect_handle = native_master_protect_acquire(instance.master_path)
    if native_master_protect_handle is None:
        raise CheckpointF1R5Error(
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
            raise CheckpointF1R5Error("Native-only: Undo-enabled state failed to restore.")


def timed_discovery(discover_rig_context_fn, shot, aset):
    t0 = time.time()
    rig_context = discover_rig_context_fn(shot, aset)
    t1 = time.time()
    return rig_context, (t1 - t0)


def timed_traversal_only(scalar_fn, reachable_fn, shot):
    t0 = time.time()
    scene = scalar_fn(shot, "scene")
    if scene is not None:
        reachable_fn(scene)
    t1 = time.time()
    return t1 - t0


def branch_determining_discovery(instance, dm, discover_rig_context_fn, find_direct_child_fn,
                                   rig_recon_root, master_recon_root,
                                   shot_record, target, aset):
    """PRE + NATIVE_POST full discovery, plus native Rebuild in between --
    identical decision logic to F1-R4's own matched_native_and_discovery_
    workload, EXCLUDING the composer-before/composer-after/terminal sites
    (those are handled separately by the caller, per command). Returns
    (branch, native_elapsed, pre_ok)."""
    shot_name = b_to_unicode(shot_record["name"])
    target_name = b_to_unicode(target["name"])

    pre_raised = False
    pre_rig = None
    try:
        pre_rig, _elapsed = timed_discovery(discover_rig_context_fn, shot_record["shot"], aset)
    except Exception as exc:
        pre_raised = True
        anomaly("PRE discovery raised for %r/%r: %r" % (shot_name, target_name, exc))

    native_elapsed = native_only_rebuild_target(instance, dm, aset, target["ptr"])

    if pre_raised or pre_rig is None:
        return "PRE_CAPTURE_UNSUPPORTED", native_elapsed

    post_rig, _elapsed = timed_discovery(discover_rig_context_fn, shot_record["shot"], aset)

    if pre_rig.get("status") != "SUPPORTED_ACTIVE_RIG":
        return "NATIVE_POST_ONLY_STATUS_MISMATCH", native_elapsed

    if (
        post_rig.get("status") != "SUPPORTED_ACTIVE_RIG"
        or post_rig.get("rig_handle") != pre_rig.get("rig_handle")
    ):
        anomaly(
            "POST rig identity changed across native Rebuild for %r/%r (would be a hard ProbeError in production)."
            % (shot_name, target_name)
        )
    if sorted(post_rig.get("owned_names_in_order") or []) != sorted(pre_rig.get("owned_names_in_order") or []):
        anomaly(
            "POST owned-control-name set changed across native Rebuild for %r/%r (would be a hard ProbeError in production)."
            % (shot_name, target_name)
        )
    if (post_rig.get("hidden_groups") or []) != (pre_rig.get("hidden_groups") or []):
        anomaly(
            "POST hiddenGroups changed across native Rebuild for %r/%r (would be a hard ProbeError in production)."
            % (shot_name, target_name)
        )

    root = instance.get_root_group(aset)
    wrapper_survived = False
    if root is not None:
        try:
            if find_direct_child_fn(root, rig_recon_root) is not None or find_direct_child_fn(root, master_recon_root) is not None:
                wrapper_survived = True
        except Exception as exc:
            anomaly("WRAPPER_SURVIVED check raised for %r/%r: %r" % (shot_name, target_name, exc))

    if wrapper_survived:
        return "NATIVE_POST_WRAPPER_SURVIVED", native_elapsed

    return "COMPOSER_ENTRY_PATH", native_elapsed


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
        raise CheckpointF1R5Error("Pre-flight SHA-256 check failed -- refusing to proceed.")
    report["provenance"]["production_normalizer_sha256"] = production_sha
    report["provenance"]["canonical_master_sha256"] = master_sha

    if not bool(sfmApp.HasDocument()):
        raise CheckpointF1R5Error("No SFM document is open.")

    root_for_filename = sfmApp.GetDocumentRoot()
    if root_for_filename is None:
        raise CheckpointF1R5Error("sfmApp.GetDocumentRoot() returned None.")
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
        raise CheckpointF1R5Error(
            "REFUSING TO RUN against the original disposable qualification fixture (%r)." % (open_basename,)
        )
    if open_basename.lower() != EXPECTED_NORMALIZED_COPY_FILENAME.lower():
        raise CheckpointF1R5Error(
            "Open document (%r) does not match the expected normalized-copy filename (%r)."
            % (open_basename, EXPECTED_NORMALIZED_COPY_FILENAME)
        )

    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointF1R5Error("Starting-state fixture gate failed -- aborting before any production invocation.")

    main_window = sfmApp.GetMainWindow()
    check("f1r5.main_window_available", main_window is not None)
    write_rolling_evidence()

    for ordinal, scope_label, command_mode in COMMAND_SPECS:
        command_start_time = time.time()

        sys.stdout.write(
            "\n>>> Command %d/2 (%s): choose '%s' in the real dialog that is about to appear. <<<\n\n"
            % (ordinal, command_mode, scope_label)
        )

        prod_ns = {}
        try:
            exec(compile(production_bytes, "<installed_production_normalizer_f1r5_cmd%d>" % ordinal, "exec"), prod_ns)
        except Exception as exc:
            anomaly("Command %d: production Normalizer execution raised: %r" % (ordinal, exc))
            anomaly(traceback.format_exc())

        native_ptr = prod_ns.get("native_ptr")
        native_master_protect_acquire = prod_ns.get("native_master_protect_acquire")
        native_master_protect_release = prod_ns.get("native_master_protect_release")
        contextualizer_process_memory_sample = prod_ns.get("contextualizer_process_memory_sample")
        contextualizer_virtual_address_sample = prod_ns.get("contextualizer_virtual_address_sample")
        discover_rig_context = prod_ns.get("discover_rig_context")
        find_direct_child = prod_ns.get("find_direct_child")
        rig_recon_root = prod_ns.get("RIG_RECON_ROOT")
        master_recon_root = prod_ns.get("MASTER_RECON_ROOT")
        scalar_fn = prod_ns.get("scalar")
        reachable_fn = prod_ns.get("reachable")

        for required_name, required_value in (
            ("native_ptr", native_ptr),
            ("native_master_protect_acquire", native_master_protect_acquire),
            ("native_master_protect_release", native_master_protect_release),
            ("contextualizer_process_memory_sample", contextualizer_process_memory_sample),
            ("contextualizer_virtual_address_sample", contextualizer_virtual_address_sample),
            ("discover_rig_context", discover_rig_context),
            ("find_direct_child", find_direct_child),
            ("RIG_RECON_ROOT", rig_recon_root),
            ("MASTER_RECON_ROOT", master_recon_root),
            ("scalar", scalar_fn),
            ("reachable", reachable_fn),
        ):
            if required_value is None:
                raise CheckpointF1R5Error("Command %d: required production name not found: %s" % (ordinal, required_name))

        run_lock_name = prod_ns.get("RUN_LOCK_NAME")
        if run_lock_name is None:
            raise CheckpointF1R5Error("Command %d: RUN_LOCK_NAME not found." % ordinal)

        instance = None
        for child in main_window.findChildren(QtCore.QObject):
            try:
                if b_to_unicode(child.objectName()) == run_lock_name:
                    instance = child
                    break
            except Exception:
                continue

        check("command_%d.run_instance_located" % ordinal, instance is not None)
        if instance is None:
            raise CheckpointF1R5Error("Command %d: could not locate the run instance." % ordinal)

        instance.finished = True
        check("command_%d.real_instance_neutralized" % ordinal, bool(instance.finished))

        work = instance.work
        check("command_%d.instance_work_present" % ordinal, bool(work))

        total_shots_in_work = len(work)
        total_targets_in_work = sum(len(r["targets"]) for r in work)

        check("command_%d.gate.total_shots_matches_expected" % ordinal, total_shots_in_work == EXPECTED_TOTAL_SHOTS, total_shots_in_work)
        check("command_%d.gate.total_eligible_native_targets_matches_expected" % ordinal, total_targets_in_work == EXPECTED_ELIGIBLE_NATIVE_TARGETS, total_targets_in_work)

        static_skips = getattr(instance, "total_gate_static_skips", None)
        follower_skips = getattr(instance, "total_gate_follower_skips", None)
        lowbone_skips = getattr(instance, "total_gate_lowbone_skips", None)
        failclosed = getattr(instance, "total_gate_failclosed_process", None)
        model_backed = getattr(instance, "total_model_backed", None)

        check("command_%d.gate.static_skips_matches_expected" % ordinal, static_skips == EXPECTED_GATE_STATIC_SKIPS, static_skips)
        check("command_%d.gate.follower_skips_matches_expected" % ordinal, follower_skips == EXPECTED_GATE_FOLLOWER_SKIPS, follower_skips)
        check("command_%d.gate.lowbone_skips_matches_expected" % ordinal, lowbone_skips == EXPECTED_GATE_LOWBONE_SKIPS, lowbone_skips)
        check("command_%d.gate.failclosed_process_matches_expected" % ordinal, failclosed == EXPECTED_GATE_FAILCLOSED_PROCESS, failclosed)
        check("command_%d.gate.model_backed_matches_expected" % ordinal, model_backed == EXPECTED_MODEL_BACKED_TARGETS, model_backed)

        dm = vs.g_pDataModel

        instance.contextualizer_resource_checkpoint("F1R5_CMD%d_CP0_START" % ordinal, True)
        before_memory = contextualizer_process_memory_sample()
        before_vas = contextualizer_virtual_address_sample()
        write_rolling_evidence()

        total_native_calls = 0
        total_native_elapsed = 0.0
        total_traversal_calls = 0
        total_traversal_elapsed = 0.0
        total_full_discovery_calls = 0
        branch_counts = {}
        ordered_stream = []
        shots_completed = 0

        for shot_index, shot_record in enumerate(work):
            shot_name = b_to_unicode(shot_record["name"])

            try:
                sfmApp.SetHeadTimeInSeconds(shot_record["midpoint"])
            except Exception as exc:
                raise CheckpointF1R5Error("Command %d: could not move playhead into %r: %r" % (ordinal, shot_name, exc))

            at_head = sfmApp.GetShotAtCurrentTime()
            if at_head is None or native_ptr(at_head) != shot_record["ptr"]:
                raise CheckpointF1R5Error("Command %d: playhead did not enter expected shot %r." % (ordinal, shot_name))

            for target_index, target in enumerate(shot_record["targets"]):
                aset = native_only_resolve_target(instance, shot_record, target)

                if command_mode == u"native_only":
                    native_elapsed = native_only_rebuild_target(instance, dm, aset, target["ptr"])
                    total_native_calls += 1
                    total_native_elapsed += native_elapsed
                else:
                    branch, native_elapsed = branch_determining_discovery(
                        instance, dm, discover_rig_context, find_direct_child,
                        rig_recon_root, master_recon_root,
                        shot_record, target, aset,
                    )
                    total_native_calls += 1
                    total_native_elapsed += native_elapsed
                    total_full_discovery_calls += (
                        1 if branch == "PRE_CAPTURE_UNSUPPORTED" else 2
                    )
                    branch_counts[branch] = branch_counts.get(branch, 0) + 1
                    ordered_stream.append((shot_name, b_to_unicode(target["name"]), branch))

                    extra_sites = 0
                    if branch == "COMPOSER_ENTRY_PATH":
                        extra_sites = 3  # composer-before, composer-after, terminal
                    elif branch in ("NATIVE_POST_ONLY_STATUS_MISMATCH", "NATIVE_POST_WRAPPER_SURVIVED"):
                        extra_sites = 1  # terminal only
                    elif branch == "PRE_CAPTURE_UNSUPPORTED":
                        extra_sites = 1  # terminal only

                    for _ in range(extra_sites):
                        traversal_elapsed = timed_traversal_only(scalar_fn, reachable_fn, shot_record["shot"])
                        total_traversal_calls += 1
                        total_traversal_elapsed += traversal_elapsed

            shots_completed += 1

            if shots_completed % SHOT_CHECKPOINT_STRIDE == 0 or shot_index == len(work) - 1:
                instance.contextualizer_resource_checkpoint(
                    "F1R5_CMD%d_CP_SHOT_%d_OF_%d" % (ordinal, shots_completed, len(work)),
                    True,
                )
                write_rolling_evidence()

        check("command_%d.native.total_calls_matches_expected_target_count" % ordinal, total_native_calls == EXPECTED_ELIGIBLE_NATIVE_TARGETS, total_native_calls)
        check("command_%d.native.all_shots_completed" % ordinal, shots_completed == len(work), shots_completed)
        check("command_%d.neutralization.real_pipeline_never_advanced" % ordinal, getattr(instance, "total_shots_processed", 0) == 0, getattr(instance, "total_shots_processed", None))

        if command_mode != u"native_only":
            expected_total_sites = sum(BRANCH_DISCOVERY_COUNTS[b] * c for b, c in branch_counts.items())
            actual_total_sites = total_full_discovery_calls + total_traversal_calls
            check(
                "command_%d.discovery.actual_total_sites_matches_branch_formula_derived_expected_total" % ordinal,
                actual_total_sites == expected_total_sites,
                (actual_total_sites, expected_total_sites),
            )

        instance.contextualizer_resource_checkpoint("F1R5_CMD%d_CP_FINAL_TARGET_COMPLETE" % ordinal, True)

        after_memory = contextualizer_process_memory_sample()
        after_vas = contextualizer_virtual_address_sample()
        instance.contextualizer_resource_checkpoint("F1R5_CMD%d_TEARDOWN_BEFORE_GC" % ordinal, True)

        gc.collect()

        postgc_memory = contextualizer_process_memory_sample()
        postgc_vas = contextualizer_virtual_address_sample()
        instance.contextualizer_resource_checkpoint("F1R5_CMD%d_TEARDOWN_AFTER_GC" % ordinal, True)

        def _delta(a, b, key):
            try:
                return a[key] - b[key]
            except Exception:
                return None

        private_delta = _delta(after_memory, before_memory, "private")
        free_vas_delta = _delta(after_vas, before_vas, "free")
        largest_free_delta = _delta(after_vas, before_vas, "largest_free")
        working_set_delta = _delta(after_memory, before_memory, "working_set")

        postgc_private_delta = _delta(postgc_memory, before_memory, "private")
        postgc_free_vas_delta = _delta(postgc_vas, before_vas, "free")
        postgc_largest_free_delta = _delta(postgc_vas, before_vas, "largest_free")

        command_record = {
            "ordinal": ordinal,
            "command_mode": command_mode,
            "duration_seconds": time.time() - command_start_time,
            "native_summary": {"total_calls": total_native_calls, "total_elapsed_seconds": total_native_elapsed},
            "full_discovery_summary": {"total_calls": total_full_discovery_calls},
            "traversal_only_summary": {"total_calls": total_traversal_calls, "total_elapsed_seconds": total_traversal_elapsed},
            "branch_counts": branch_counts,
            "ordered_branch_stream_checksum_sha256": sequence_checksum(ordered_stream) if ordered_stream else None,
            "ordered_branch_stream_length": len(ordered_stream),
            "resource_deltas": {
                "private_delta": private_delta,
                "free_vas_delta": free_vas_delta,
                "largest_free_delta": largest_free_delta,
                "working_set_delta": working_set_delta,
                "postgc_private_delta": postgc_private_delta,
                "postgc_free_vas_delta": postgc_free_vas_delta,
                "postgc_largest_free_delta": postgc_largest_free_delta,
            },
        }
        report["command_records"].append(command_record)

        try:
            with open(NORMALIZER_LOG_PATH, "rb") as f:
                log_bytes = f.read()
            preserve_ok, preserve_err = write_text_atomic(PRODUCTION_LOG_PRESERVE_TEMPLATE % ordinal, log_bytes)
            if not preserve_ok:
                anomaly("Command %d: could not preserve production log: %s" % (ordinal, preserve_err))
        except Exception as exc:
            anomaly("Command %d: could not read production log: %r" % (ordinal, exc))

        write_rolling_evidence()

    # --- Cross-command comparison (native-only vs native+isolated-traversal
    #     component), within this same process. ---
    if len(report["command_records"]) == 2:
        cmd1 = report["command_records"][0]
        cmd2 = report["command_records"][1]

        def _cmp(key):
            a = cmd2["resource_deltas"].get(key)
            b = cmd1["resource_deltas"].get(key)
            if a is None or b is None:
                return None
            return a - b

        report["cross_command_comparison"] = {
            "incremental_private_delta": _cmp("private_delta"),
            "incremental_free_vas_delta": _cmp("free_vas_delta"),
            "incremental_largest_free_delta": _cmp("largest_free_delta"),
            "baselines": {
                "native_only": {
                    "private_delta": NATIVE_ONLY_PRIVATE_DELTA,
                    "free_vas_delta": NATIVE_ONLY_FREE_VAS_DELTA,
                    "largest_free_delta": NATIVE_ONLY_LARGEST_FREE_DELTA,
                },
                "native_plus_full_discovery": {
                    "private_delta": NATIVE_PLUS_FULL_DISCOVERY_PRIVATE_DELTA,
                    "free_vas_delta": NATIVE_PLUS_FULL_DISCOVERY_FREE_VAS_DELTA,
                    "largest_free_delta": NATIVE_PLUS_FULL_DISCOVERY_LARGEST_FREE_DELTA,
                },
                "full_production": {
                    "private_delta": PRODUCTION_PRIVATE_DELTA,
                    "free_vas_delta": PRODUCTION_FREE_VAS_DELTA,
                    "largest_free_delta": PRODUCTION_LARGEST_FREE_DELTA,
                },
            },
        }

except CheckpointF1R5Error as gate_exc:
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

json_write_ok, json_write_error, _r = write_json_atomic(JSON_OUTPUT_PATH, report)
if not json_write_ok:
    anomaly("Final JSON write failed: %s" % json_write_error)

summary_lines = []
summary_lines.append("SFM CHECKPOINT F1-R5 -- FRESH DISCOVERY COMPONENT RETENTION")
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
if report.get("gate_failure"):
    summary_lines.append("*** GATE FAILURE ***")
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
for rec in report["command_records"]:
    summary_lines.append("=== Command %d (%s) ===" % (rec["ordinal"], rec["command_mode"]))
    summary_lines.append("  native_summary=%r" % (rec["native_summary"],))
    summary_lines.append("  full_discovery_summary=%r" % (rec["full_discovery_summary"],))
    summary_lines.append("  traversal_only_summary=%r" % (rec["traversal_only_summary"],))
    summary_lines.append("  branch_counts=%r" % (rec["branch_counts"],))
    summary_lines.append("  resource_deltas=%r" % (rec["resource_deltas"],))
    summary_lines.append("")
if "cross_command_comparison" in report:
    summary_lines.append("cross_command_comparison=%r" % (report["cross_command_comparison"],))
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
        "\nCheckpoint F1-R5 reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok)
    )
    sys.stdout.write("\nDO NOT SAVE. Restart SFM afterward.\n")
except Exception:
    pass
