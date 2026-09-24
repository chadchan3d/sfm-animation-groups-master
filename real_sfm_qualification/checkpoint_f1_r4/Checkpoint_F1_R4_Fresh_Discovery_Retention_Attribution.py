# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint F1-R4: Fresh Discovery
Retention Attribution.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: **THIS CHECKPOINT MUTATES THE SCENE.** It runs the real
native Rebuild callback for every production-eligible target, exactly as
production and F1-R3 do, and ALSO performs fresh `discover_rig_context()`
traversal at each production semantic boundary that would normally
precede a capture -- but never the capture/composer/classification work
itself. **Do not save afterward.**

Purpose (see F1_R4_DISCOVERY_SCHEDULE_AUDIT.md for the full re-derived
branch/discovery-schedule audit this design is built from):

  F1-R3 was accepted: PASS -- CONTEXTUAL_LAYER_MATERIAL. Native Rebuild
  alone, across the same 62 targets, explains only a small fraction of
  F1-R2's own full-production retained pressure (private ratio ~0.054,
  free-VAS-loss ratio ~0.010). The unexplained gap (~+251 MiB private,
  ~235 MiB free-VAS loss, ~111 MiB largest-free loss) lives somewhere in
  the CONTEXTUAL layer F1-R3 deliberately excluded. F1-R4 measures
  whether fresh discover_rig_context() traversal ITSELF -- repeated at
  the same production semantic boundaries, exactly as production does,
  never cached or reused -- explains a material share of that remaining
  gap. This is lifetime/allocation attribution, not a proposal to reuse
  stale discovery results, and does not reopen O3's own rejected
  discovery-reuse/cache design.

Design (full audit in F1_R4_DISCOVERY_SCHEDULE_AUDIT.md; summary):
  1-4. Identical to F1-R3: exec() the pinned production bytes, locate the
     already-constructed run instance, set instance.finished = True
     immediately (before any Qt event pump), read instance.work directly
     (the exact, already-computed, production-ordered target inventory --
     never re-derived).
  5. For each shot, in instance.work's own order: activate the shot the
     same way production/F1-R3 do. For each target, in order: re-resolve
     the live aset (same narrow helper F1-R3 introduced), then run the
     matched native+fresh-discovery workload:
       a. PRE discovery: discover_rig_context(shot, aset) -- discard the
          result after reading only the fields needed for branch
          determination (status, rig_handle, owned_names_in_order,
          hidden_groups -- all present on the BARE discovery dict, never
          requiring capture_snapshot_explicit()/capture_tree()).
       b. Execute the exact native-Rebuild-relevant guarded slice
          (reused verbatim from F1-R3's own native_only_rebuild_target).
       c. If PRE itself raised: stop here for this target (after the
          unconditional terminal discovery below) -- branch =
          PRE_CAPTURE_UNSUPPORTED.
       d. Otherwise, NATIVE_POST discovery: discover_rig_context(shot,
          aset) again.
       e. If PRE's own status was not SUPPORTED_ACTIVE_RIG: stop here
          (branch = NATIVE_POST_ONLY_<status>).
       f. Compare POST vs PRE (rig_handle, owned_names_in_order,
          hidden_groups) -- a genuine mismatch here is an ANOMALY (would
          be a hard ProbeError in production), logged, not silently
          treated as a normal branch.
       g. NATIVE_POST_WRAPPER_SURVIVED check: reused directly via
          find_direct_child(root, RIG_RECON_ROOT)/MASTER_RECON_ROOT) --
          a bounded, two-lookup existence check, not a semantic capture.
          If found: stop here (branch = NATIVE_POST_WRAPPER_SURVIVED).
       h. Otherwise: composer-entry path. This also covers the two
          branch conditions (NATIVE_POST_ONLY_DUPLICATE_SEMANTICS,
          NATIVE_POST_POLICY_FALLBACK) that cannot be evaluated without
          calling capture_tree()/preflight_reconciliation_plan() -- both
          skipped and disclosed (see audit doc); this is a one-directional,
          conservative bias (can only add discovery work relative to
          production's own true branch for those two conditions, never
          remove it). Composer-before discovery, then composer-after
          discovery, both discover_rig_context(shot, aset), both
          discarded immediately.
       i. Terminal discovery (unconditional on every branch, matching
          production's own semantic_target_fingerprint()'s own discovery
          call, but WITHOUT the accompanying capture_snapshot_explicit()
          it normally feeds -- F1-R4 never calls capture_snapshot_
          explicit() at all): discover_rig_context(shot, aset), discarded.
  6. Never calls capture_snapshot_explicit, capture_tree,
     production_generic_composer, preflight_reconciliation_plan,
     isolation_fingerprint, verify_current_shot_peers, or
     semantic_target_fingerprint.
  7. Records, per target: branch, discovery_call_count, and an ordered
     (shot, target, branch, discovery_site_label) stream entry for each
     discovery call -- hashed into a single deterministic checksum for
     mechanical cross-run comparison.
  8. Resource checkpoints via instance.contextualizer_resource_checkpoint
     at the same low cadence as F1-R3 (command start, every 4th completed
     shot, final target complete, teardown before/after GC).
  9. No save. No exhaustive semantic verification of any kind.

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

# Discovery-call counts per branch, per F1_R4_DISCOVERY_SCHEDULE_AUDIT.md
# (includes the unconditional terminal discovery).
BRANCH_DISCOVERY_COUNTS = {
    "PRE_CAPTURE_UNSUPPORTED": 2,
    "NATIVE_POST_ONLY_STATUS_MISMATCH": 3,
    "NATIVE_POST_WRAPPER_SURVIVED": 3,
    "COMPOSER_ENTRY_PATH": 5,
}

# Baselines established by earlier real runs, reused here for ratio
# reporting only -- never as a pass/fail threshold.
PRODUCTION_PRIVATE_DELTA = 265461760
PRODUCTION_FREE_VAS_DELTA = -237633536
PRODUCTION_LARGEST_FREE_DELTA = -110985216
NATIVE_ONLY_PRIVATE_DELTA = 14307328
NATIVE_ONLY_FREE_VAS_DELTA = -2490368
NATIVE_ONLY_LARGEST_FREE_DELTA = 0

SHOT_CHECKPOINT_STRIDE = 4  # low-cadence: checkpoint after every 4th completed shot

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r4_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r4_result_summary.txt"
PRODUCTION_LOG_PRESERVE_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r4_native_discovery_log.txt"

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


class CheckpointF1R4Error(Exception):
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
# Narrow, separately-justified target re-resolution helper (identical to
# F1-R3's own, reused verbatim).
# ---------------------------------------------------------------------------

def native_only_resolve_target(instance, shot_record, target):
    instance.contextualizer_assert_run_lock_present()
    instance.assert_master_stable()

    at_head = sfmApp.GetShotAtCurrentTime()

    if at_head is None or native_ptr(at_head) != shot_record["ptr"]:
        raise CheckpointF1R4Error(
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
        raise CheckpointF1R4Error(
            "Native-only target resolve failed unique match: shot=%r target=%r matches=%d."
            % (b_to_unicode(shot_record["name"]), b_to_unicode(target["name"]), len(matches))
        )

    return matches[0]


def native_only_rebuild_target(instance, dm, aset, expected_ptr):
    """Identical to F1-R3's own native_only_rebuild_target -- the exact
    guarded slice of run_target_transaction() surrounding self.rebuild().
    Reused verbatim, not reimplemented."""
    aset_ptr = native_ptr(aset)

    if aset_ptr != expected_ptr:
        raise CheckpointF1R4Error(
            "Native-only pointer-stability check failed: expected=%r actual=%r."
            % (expected_ptr, aset_ptr)
        )

    if instance.get_game_model(aset) is None:
        raise CheckpointF1R4Error("Native-only: animation set lost model backing.")

    root = instance.get_root_group(aset)
    if root is None or not native_ptr(root):
        raise CheckpointF1R4Error("Native-only: animation set lost its root control group.")

    undo_prior = bool(dm.IsUndoEnabled())
    dm.SetUndoEnabled(False)
    if bool(dm.IsUndoEnabled()):
        raise CheckpointF1R4Error("Native-only: could not disable Undo.")

    native_master_protect_handle = native_master_protect_acquire(instance.master_path)
    if native_master_protect_handle is None:
        raise CheckpointF1R4Error(
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
            raise CheckpointF1R4Error("Native-only: Undo-enabled state failed to restore.")


def timed_discovery(discover_rig_context_fn, shot, aset):
    t0 = time.time()
    rig_context = discover_rig_context_fn(shot, aset)
    t1 = time.time()
    return rig_context, (t1 - t0)


def matched_native_and_discovery_workload(
        instance, dm, discover_rig_context_fn, find_direct_child_fn,
        rig_recon_root, master_recon_root,
        shot_record, target, aset):
    """Reproduces the exact production discovery-call schedule for one
    target (see F1_R4_DISCOVERY_SCHEDULE_AUDIT.md), performing ONLY
    discover_rig_context() calls at each production semantic boundary --
    never capture_snapshot_explicit()/capture_tree()/composer/
    classification. Returns (branch, discovery_call_count,
    discovery_elapsed_total, native_elapsed, stream_entries, anomalies)."""
    shot_name = b_to_unicode(shot_record["name"])
    target_name = b_to_unicode(target["name"])
    stream = []
    local_anomalies = []
    discovery_elapsed_total = 0.0

    def record_site(label):
        stream.append((shot_name, target_name, None, label))

    pre_raised = False
    pre_rig = None
    try:
        pre_rig, elapsed = timed_discovery(discover_rig_context_fn, shot_record["shot"], aset)
        discovery_elapsed_total += elapsed
        record_site("PRE")
    except Exception as exc:
        pre_raised = True
        record_site("PRE")
        local_anomalies.append("PRE discovery raised for %r/%r: %r" % (shot_name, target_name, exc))

    native_elapsed = native_only_rebuild_target(instance, dm, aset, target["ptr"])

    if pre_raised or pre_rig is None:
        branch = "PRE_CAPTURE_UNSUPPORTED"
        _, elapsed = timed_discovery(discover_rig_context_fn, shot_record["shot"], aset)
        discovery_elapsed_total += elapsed
        record_site("TERMINAL")
        stream_labeled = [(s, t, branch, site) for (s, t, _b, site) in stream]
        return branch, len(stream_labeled), discovery_elapsed_total, native_elapsed, stream_labeled, local_anomalies

    post_rig, elapsed = timed_discovery(discover_rig_context_fn, shot_record["shot"], aset)
    discovery_elapsed_total += elapsed
    record_site("NATIVE_POST")

    if pre_rig.get("status") != "SUPPORTED_ACTIVE_RIG":
        branch = "NATIVE_POST_ONLY_STATUS_MISMATCH"
        _, elapsed = timed_discovery(discover_rig_context_fn, shot_record["shot"], aset)
        discovery_elapsed_total += elapsed
        record_site("TERMINAL")
        stream_labeled = [(s, t, branch, site) for (s, t, _b, site) in stream]
        return branch, len(stream_labeled), discovery_elapsed_total, native_elapsed, stream_labeled, local_anomalies

    if (
        post_rig.get("status") != "SUPPORTED_ACTIVE_RIG"
        or post_rig.get("rig_handle") != pre_rig.get("rig_handle")
    ):
        local_anomalies.append(
            "POST rig identity changed across native Rebuild for %r/%r (would be a hard ProbeError in production)."
            % (shot_name, target_name)
        )
    if sorted(post_rig.get("owned_names_in_order") or []) != sorted(pre_rig.get("owned_names_in_order") or []):
        local_anomalies.append(
            "POST owned-control-name set changed across native Rebuild for %r/%r (would be a hard ProbeError in production)."
            % (shot_name, target_name)
        )
    if (post_rig.get("hidden_groups") or []) != (pre_rig.get("hidden_groups") or []):
        local_anomalies.append(
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
            local_anomalies.append("WRAPPER_SURVIVED check raised for %r/%r: %r" % (shot_name, target_name, exc))

    if wrapper_survived:
        branch = "NATIVE_POST_WRAPPER_SURVIVED"
        _, elapsed = timed_discovery(discover_rig_context_fn, shot_record["shot"], aset)
        discovery_elapsed_total += elapsed
        record_site("TERMINAL")
        stream_labeled = [(s, t, branch, site) for (s, t, _b, site) in stream]
        return branch, len(stream_labeled), discovery_elapsed_total, native_elapsed, stream_labeled, local_anomalies

    # Composer-entry path. Also covers NATIVE_POST_ONLY_DUPLICATE_SEMANTICS
    # and NATIVE_POST_POLICY_FALLBACK, deliberately not evaluated -- see
    # F1_R4_DISCOVERY_SCHEDULE_AUDIT.md ("disclosed handling").
    branch = "COMPOSER_ENTRY_PATH"

    _, elapsed = timed_discovery(discover_rig_context_fn, shot_record["shot"], aset)
    discovery_elapsed_total += elapsed
    record_site("COMPOSER_BEFORE")

    _, elapsed = timed_discovery(discover_rig_context_fn, shot_record["shot"], aset)
    discovery_elapsed_total += elapsed
    record_site("COMPOSER_AFTER")

    _, elapsed = timed_discovery(discover_rig_context_fn, shot_record["shot"], aset)
    discovery_elapsed_total += elapsed
    record_site("TERMINAL")

    stream_labeled = [(s, t, branch, site) for (s, t, _b, site) in stream]
    return branch, len(stream_labeled), discovery_elapsed_total, native_elapsed, stream_labeled, local_anomalies


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
        raise CheckpointF1R4Error("Pre-flight SHA-256 check failed -- refusing to proceed.")
    report["provenance"]["production_normalizer_sha256"] = production_sha
    report["provenance"]["canonical_master_sha256"] = master_sha

    if not bool(sfmApp.HasDocument()):
        raise CheckpointF1R4Error("No SFM document is open.")

    root_for_filename = sfmApp.GetDocumentRoot()
    if root_for_filename is None:
        raise CheckpointF1R4Error("sfmApp.GetDocumentRoot() returned None.")
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
        raise CheckpointF1R4Error(
            "REFUSING TO RUN against the original disposable qualification fixture (%r) -- "
            "F1-R4 must run only against the F1-R2 Phase 2 normalized copy." % (open_basename,)
        )
    if open_basename.lower() != EXPECTED_NORMALIZED_COPY_FILENAME.lower():
        raise CheckpointF1R4Error(
            "Open document (%r) does not match the expected normalized-copy filename (%r)."
            % (open_basename, EXPECTED_NORMALIZED_COPY_FILENAME)
        )

    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointF1R4Error("Starting-state fixture gate failed -- aborting before any production invocation.")

    main_window = sfmApp.GetMainWindow()
    check("f1r4.main_window_available", main_window is not None)
    write_rolling_evidence()

    before_memory = None
    before_vas = None

    prod_ns = {}
    try:
        exec(compile(production_bytes, "<installed_production_normalizer_f1r4>", "exec"), prod_ns)
    except Exception as exc:
        anomaly("Production Normalizer execution raised: %r" % (exc,))
        anomaly(traceback.format_exc())

    # NOTE: vs/sfmApp are SFM-injected ambient globals already available in
    # THIS script's own top-level namespace -- never re-extracted from
    # prod_ns (see F1-R3's own established fix for why that would be a bug).
    native_ptr = prod_ns.get("native_ptr")
    native_master_protect_acquire = prod_ns.get("native_master_protect_acquire")
    native_master_protect_release = prod_ns.get("native_master_protect_release")
    contextualizer_process_memory_sample = prod_ns.get("contextualizer_process_memory_sample")
    contextualizer_virtual_address_sample = prod_ns.get("contextualizer_virtual_address_sample")
    discover_rig_context = prod_ns.get("discover_rig_context")
    find_direct_child = prod_ns.get("find_direct_child")
    rig_recon_root = prod_ns.get("RIG_RECON_ROOT")
    master_recon_root = prod_ns.get("MASTER_RECON_ROOT")

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
    ):
        if required_value is None:
            raise CheckpointF1R4Error("Required production name not found in exec'd namespace: %s" % required_name)

    run_lock_name = prod_ns.get("RUN_LOCK_NAME")
    if run_lock_name is None:
        raise CheckpointF1R4Error("RUN_LOCK_NAME not found in exec'd namespace.")

    for child in main_window.findChildren(QtCore.QObject):
        try:
            if b_to_unicode(child.objectName()) == run_lock_name:
                instance = child
                break
        except Exception:
            continue

    check("f1r4.run_instance_located", instance is not None)
    if instance is None:
        raise CheckpointF1R4Error("Could not locate the already-constructed run instance immediately after exec().")

    # Neutralize the real instance's own further progression BEFORE ever
    # pumping the Qt event loop -- see F1_R3_NATIVE_PATH_AUDIT.md /
    # F1_R4_DISCOVERY_SCHEDULE_AUDIT.md.
    instance.finished = True
    check("f1r4.real_instance_neutralized", bool(instance.finished))

    work = instance.work
    check("f1r4.instance_work_present", bool(work))

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

    dm = vs.g_pDataModel

    instance.contextualizer_resource_checkpoint("F1R4_CP0_NATIVE_DISCOVERY_START", True)
    before_memory = contextualizer_process_memory_sample()
    before_vas = contextualizer_virtual_address_sample()
    report["memory_snapshots"] = {"before": {"memory": before_memory, "vas": before_vas}}
    write_rolling_evidence()

    total_native_calls = 0
    total_native_elapsed = 0.0
    total_discovery_calls = 0
    total_discovery_elapsed = 0.0
    branch_counts = {}
    full_stream = []
    shots_completed = 0

    for shot_index, shot_record in enumerate(work):
        shot_name = b_to_unicode(shot_record["name"])

        try:
            sfmApp.SetHeadTimeInSeconds(shot_record["midpoint"])
        except Exception as exc:
            raise CheckpointF1R4Error("Could not move playhead into %r: %r" % (shot_name, exc))

        at_head = sfmApp.GetShotAtCurrentTime()
        if at_head is None or native_ptr(at_head) != shot_record["ptr"]:
            raise CheckpointF1R4Error("Playhead did not enter expected shot %r." % (shot_name,))

        shot_targets_ok = 0

        for target_index, target in enumerate(shot_record["targets"]):
            target_name = b_to_unicode(target["name"])

            aset = native_only_resolve_target(instance, shot_record, target)

            branch, disc_count, disc_elapsed, native_elapsed, stream_entries, target_anomalies = (
                matched_native_and_discovery_workload(
                    instance, dm, discover_rig_context, find_direct_child,
                    rig_recon_root, master_recon_root,
                    shot_record, target, aset,
                )
            )

            for a in target_anomalies:
                anomaly(a)

            total_native_calls += 1
            total_native_elapsed += native_elapsed
            total_discovery_calls += disc_count
            total_discovery_elapsed += disc_elapsed
            branch_counts[branch] = branch_counts.get(branch, 0) + 1
            full_stream.extend(stream_entries)

            shot_targets_ok += 1

            report["targets_processed"].append({
                "shot": shot_name,
                "target": target_name,
                "branch": branch,
                "discovery_call_count": disc_count,
                "native_elapsed_seconds": native_elapsed,
                "discovery_elapsed_seconds": disc_elapsed,
            })

        shots_completed += 1
        report["shots_processed"].append({
            "shot": shot_name,
            "target_count": len(shot_record["targets"]),
            "targets_ok": shot_targets_ok,
        })

        if shots_completed % SHOT_CHECKPOINT_STRIDE == 0 or shot_index == len(work) - 1:
            instance.contextualizer_resource_checkpoint(
                "F1R4_CP_SHOT_%d_OF_%d" % (shots_completed, len(work)),
                True,
            )
            write_rolling_evidence()

    check("native.total_calls_matches_expected_target_count", total_native_calls == EXPECTED_ELIGIBLE_NATIVE_TARGETS, total_native_calls)
    check("native.all_shots_completed", shots_completed == len(work), shots_completed)
    check("neutralization.real_pipeline_never_advanced", getattr(instance, "total_shots_processed", 0) == 0, getattr(instance, "total_shots_processed", None))

    expected_total_discovery_calls = sum(
        BRANCH_DISCOVERY_COUNTS[branch] * count for branch, count in branch_counts.items()
    )
    check(
        "discovery.actual_total_matches_branch_formula_derived_expected_total",
        total_discovery_calls == expected_total_discovery_calls,
        (total_discovery_calls, expected_total_discovery_calls),
    )

    stream_checksum = sequence_checksum(full_stream)

    report["provenance"]["invocation_stream_checksum_sha256"] = stream_checksum
    report["provenance"]["invocation_stream_length"] = len(full_stream)
    report["branch_counts"] = branch_counts
    report["discovery_summary"] = {
        "expected_total_discovery_calls": expected_total_discovery_calls,
        "actual_total_discovery_calls": total_discovery_calls,
        "total_discovery_elapsed_seconds": total_discovery_elapsed,
    }
    report["native_summary"] = {
        "total_calls": total_native_calls,
        "total_elapsed_seconds": total_native_elapsed,
    }

    instance.contextualizer_resource_checkpoint("F1R4_CP_FINAL_NATIVE_DISCOVERY_TARGET_COMPLETE", True)

    after_memory = contextualizer_process_memory_sample()
    after_vas = contextualizer_virtual_address_sample()
    instance.contextualizer_resource_checkpoint("F1R4_TEARDOWN_BEFORE_GC", True)

    gc.collect()

    postgc_memory = contextualizer_process_memory_sample()
    postgc_vas = contextualizer_virtual_address_sample()
    instance.contextualizer_resource_checkpoint("F1R4_TEARDOWN_AFTER_GC", True)

    report["memory_snapshots"]["after"] = {"memory": after_memory, "vas": after_vas}
    report["memory_snapshots"]["after_gc"] = {"memory": postgc_memory, "vas": postgc_vas}

    def _delta(a, b, key):
        try:
            return a[key] - b[key]
        except Exception:
            return None

    native_discovery_private_delta = _delta(after_memory, before_memory, "private")
    native_discovery_free_vas_delta = _delta(after_vas, before_vas, "free")
    native_discovery_largest_free_delta = _delta(after_vas, before_vas, "largest_free")
    native_discovery_working_set_delta = _delta(after_memory, before_memory, "working_set")

    postgc_private_delta = _delta(postgc_memory, before_memory, "private")
    postgc_free_vas_delta = _delta(postgc_vas, before_vas, "free")
    postgc_largest_free_delta = _delta(postgc_vas, before_vas, "largest_free")

    def _ratio(value, baseline):
        if value is None or baseline in (None, 0):
            return None
        return float(value) / float(baseline)

    incremental_private_delta = (
        None if native_discovery_private_delta is None else native_discovery_private_delta - NATIVE_ONLY_PRIVATE_DELTA
    )
    incremental_free_vas_delta = (
        None if native_discovery_free_vas_delta is None else native_discovery_free_vas_delta - NATIVE_ONLY_FREE_VAS_DELTA
    )
    incremental_largest_free_delta = (
        None if native_discovery_largest_free_delta is None else native_discovery_largest_free_delta - NATIVE_ONLY_LARGEST_FREE_DELTA
    )

    report["resource_deltas"] = {
        "native_discovery_private_delta": native_discovery_private_delta,
        "native_discovery_free_vas_delta": native_discovery_free_vas_delta,
        "native_discovery_largest_free_delta": native_discovery_largest_free_delta,
        "native_discovery_working_set_delta": native_discovery_working_set_delta,
        "postgc_private_delta": postgc_private_delta,
        "postgc_free_vas_delta": postgc_free_vas_delta,
        "postgc_largest_free_delta": postgc_largest_free_delta,
        "incremental_vs_native_only": {
            "private_delta": incremental_private_delta,
            "free_vas_delta": incremental_free_vas_delta,
            "largest_free_delta": incremental_largest_free_delta,
        },
        "baselines": {
            "native_only": {
                "private_delta": NATIVE_ONLY_PRIVATE_DELTA,
                "free_vas_delta": NATIVE_ONLY_FREE_VAS_DELTA,
                "largest_free_delta": NATIVE_ONLY_LARGEST_FREE_DELTA,
            },
            "full_production": {
                "private_delta": PRODUCTION_PRIVATE_DELTA,
                "free_vas_delta": PRODUCTION_FREE_VAS_DELTA,
                "largest_free_delta": PRODUCTION_LARGEST_FREE_DELTA,
            },
        },
        "ratios_vs_full_production": {
            "private_ratio": _ratio(native_discovery_private_delta, PRODUCTION_PRIVATE_DELTA),
            "free_vas_loss_ratio": _ratio(native_discovery_free_vas_delta, PRODUCTION_FREE_VAS_DELTA),
            "largest_free_loss_ratio": _ratio(native_discovery_largest_free_delta, PRODUCTION_LARGEST_FREE_DELTA),
        },
    }

    check("resource.before_after_gc_deltas_captured", native_discovery_private_delta is not None and postgc_private_delta is not None)

except CheckpointF1R4Error as gate_exc:
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
        anomaly("Could not preserve native+discovery production log: %s" % preserve_err)
except Exception as exc:
    anomaly("Could not read native+discovery production log: %r" % (exc,))

json_write_ok, json_write_error, _r = write_json_atomic(JSON_OUTPUT_PATH, report)
if not json_write_ok:
    anomaly("Final JSON write failed: %s" % json_write_error)

summary_lines = []
summary_lines.append("SFM CHECKPOINT F1-R4 -- FRESH DISCOVERY RETENTION ATTRIBUTION")
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
if report.get("gate_failure"):
    summary_lines.append("*** GATE FAILURE: aborted before or during the native+discovery run. ***")
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
if "provenance" in report:
    summary_lines.append("invocation_stream_checksum_sha256=%r" % report["provenance"].get("invocation_stream_checksum_sha256"))
    summary_lines.append("invocation_stream_length=%r" % report["provenance"].get("invocation_stream_length"))
if "branch_counts" in report:
    summary_lines.append("branch_counts=%r" % (report["branch_counts"],))
if "discovery_summary" in report:
    summary_lines.append("discovery_summary=%r" % (report["discovery_summary"],))
if "native_summary" in report:
    summary_lines.append("native_summary=%r" % (report["native_summary"],))
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
summary_lines.append("json_output_path=%s (write_ok=%r)" % (JSON_OUTPUT_PATH, json_write_ok))

summary_text = u"\n".join(summary_lines) + u"\n"
summary_write_ok, summary_write_error = write_text_atomic(SUMMARY_OUTPUT_PATH, summary_text.encode("ascii", "replace"))

try:
    sys.stdout.write(summary_text.encode("ascii", "replace"))
    sys.stdout.write(
        "\nCheckpoint F1-R4 reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok)
    )
    sys.stdout.write("\nDO NOT SAVE. Restart SFM afterward.\n")
except Exception:
    pass
