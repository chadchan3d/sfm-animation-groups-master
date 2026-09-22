# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint C1: Baseline (pre-
integration) Selected-Shots run.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: **THIS CHECKPOINT MUTATES THE SCENE.** It invokes the
exact historical, pre-integration frozen Normalizer's own real Selected
Shots behavior, unmodified, against the disposable qualification project.
Do not save afterward.

Purpose:
  Establish the historical (pre-integration) Selected-Shots outcome as
  the baseline C2 will later be compared against. This script:
    1. verifies the historical baseline source's SHA-256 before ever
       executing a byte of it;
    2. verifies the currently-installed production Normalizer has NOT
       been replaced (its own SHA-256 is checked, but it is never read
       or imported for behavior -- this checkpoint intentionally runs
       the SEPARATE historical baseline source instead);
    3. verifies the canonical Master's SHA-256;
    4. independently re-derives the Checkpoint-B-style fixture witness
       (shots/targets/eligibility/selected-scope) fresh from the live
       document, and cross-checks it against the exact witness values
       Checkpoint B (B-2) reported, before trusting the fixture;
    5. captures a structural PRE fingerprint of the 2 expected-Selected
       targets plus the 83 independently-witnessed untouched-peer
       targets, using the accepted Normalizer's own already-qualified,
       purely read-only capture_snapshot_explicit()/capture_tree()/
       discover_rig_context() functions (extracted verbatim, SHA-256
       pinned, from the CURRENT installed Normalizer file -- these are
       neutral structural-reading primitives identical in both the
       historical and integrated code paths, not the scope/eligibility
       policy this checkpoint is qualifying, and reusing them is the
       same well-precedented technique this whole project's offline
       qualification suite already uses for before/after comparison);
    6. executes the exact, byte-verified historical baseline source
       in an isolated namespace (never imported as a Python module,
       never touching sys.modules under any name the production
       Normalizer or the authority package uses -- see this file's own
       "module identity isolation" section below) -- this triggers the
       historical code's own real, unmodified, interactive Clip-Editor
       scope-choice dialog; the operator must select Selected Shots and
       confirm, exactly as the numbered instructions describe;
    7. waits (by pumping the real Qt event loop and polling for the
       historical run's own run-lock object, never by inventing a new
       synchronization mechanism) for that real, asynchronous,
       QTimer-deferred historical operation to actually finish;
    8. captures the same structural POST fingerprint for the same 85
       targets;
    9. compares PRE vs POST per target (after normalizing only
       process-local handle integers, never semantic content) to
       independently determine which targets actually changed;
   10. writes a complete machine-readable result artifact.

This script never imports `sfm_master_authority_productionized`, never
imports `Rebuild_Control_Groups_Normalizer.py`, and never touches the
canonical Master for anything other than a read-only SHA-256 check.

Output:
  Two files are written to C:\\Users\\Public\\Documents\\:
    sfm_checkpoint_c1_baseline_result.json           (machine-readable, full detail)
    sfm_checkpoint_c1_baseline_result_summary.txt    (concise human-readable)
  A short summary is also printed to SFM's own console/output.

Do NOT save the SFM project after running this script.
"""
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

EXPECTED_HISTORICAL_BASELINE_SHA256 = (
    "6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e"
)
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
EXPECTED_B2_TOTALS = {
    "total_shots": 15,
    "total_targets": 163,
    "eligible_targets": 85,
    "excluded_targets": 78,
    "expected_selected_candidates": 2,
    "untouched_peer_targets": 83,
    "distinct_model_names": 22,
    "distinct_fold_vocabulary_hashes_among_eligible": 21,
}

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_c1_baseline_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_c1_baseline_result_summary.txt"

BASELINE_SOURCE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
    "_qualification_baseline_source",
    "Rebuild_Control_Groups_Normalizer_PRE_INTEGRATION_BASELINE.py.txt",
)
PRODUCTION_NORMALIZER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
    "Rebuild_Control_Groups_Normalizer.py",
)
CANONICAL_MASTER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "cfg", "sfm_defaultanimationgroups.txt",
)

# 1-indexed, inclusive. Extracted from the CURRENT installed production
# Normalizer (same SHA pinned above), reusing the exact, already-proven
# range table this project's own candidate_b2c_c/production_plan_layer.py
# extraction module uses for these same functions (verified 55/55 PASS
# against this exact file this session) -- not re-derived from scratch.
# These are pure, read-only, structural DME-reading functions (group/
# control hierarchy + rig discovery), never scope/eligibility POLICY, and
# they are IDENTICAL code in both the historical baseline and the
# integrated Normalizer (this exact function text is untouched by the
# Production Normalizer Integration work), so extracting them from the
# CURRENT file for use as the PRE/POST fingerprint mechanism is not
# circular with respect to what this checkpoint is actually qualifying
# (the scope/mutation-outcome difference between the two code paths).
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


class CheckpointC1Error(Exception):
    pass


ANOMALIES = []


def anomaly(message):
    ANOMALIES.append(message)
    try:
        sys.stdout.write("ANOMALY: %s\n" % message)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Independent Checkpoint-B-style fact/classification helpers (own copy,
# same logic already offline-dry-run-verified in Checkpoint B -- these
# are the SAME neutral structural primitives, reused for internal
# consistency between the two checkpoints' witnesses, not borrowed from
# the Normalizer's own scope-resolution functions).
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
                raise CheckpointC1Error(
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
    joined = u"\n".join(sorted(values))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def build_independent_witness():
    """Re-derives the same shot/target/eligibility/classification witness
    Checkpoint B independently established, fresh from the live document.
    Returns (witness_dict, shots_by_name, error_or_None)."""
    if not bool(sfmApp.HasDocument()):
        return None, None, "No SFM document is open."

    all_shots = list(sfmApp.GetShots())
    if not all_shots:
        return None, None, "sfmApp.GetShots() returned zero shots."

    selected_shots_raw = list(sfmClipEditor.GetSelectedShots())
    selected_ptr_set = set()
    for selected_shot in selected_shots_raw:
        selected_handle = None
        try:
            selected_handle = int(selected_shot.GetHandle())
        except Exception:
            pass
        selected_ptr = b_native_ptr(selected_shot)
        matches = []
        for shot in all_shots:
            shot_handle = None
            try:
                shot_handle = int(shot.GetHandle())
            except Exception:
                pass
            shot_ptr = b_native_ptr(shot)
            matched = (
                (selected_handle is not None and shot_handle is not None and selected_handle == shot_handle)
                or (selected_ptr is not None and shot_ptr is not None and selected_ptr == shot_ptr)
            )
            if matched:
                matches.append(shot_ptr)
        unique_matches = set(matches)
        if len(unique_matches) == 1:
            selected_ptr_set.update(unique_matches)

    global_aset_ptr_seen = set()
    targets = []
    shots_by_name = {}

    for shot in all_shots:
        shot_ptr = b_native_ptr(shot)
        shot_name = b_name(shot)
        shot_selected = shot_ptr in selected_ptr_set
        shots_by_name.setdefault(shot_name, []).append(shot)

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

            if not eligible:
                category = "excluded"
            elif shot_selected:
                category = "expected_selected_and_all_candidate"
            else:
                category = "untouched_peer_eligible_all_only"

            targets.append({
                "shot_ptr": shot_ptr, "shot_name": shot_name, "shot_selected": shot_selected,
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
        "expected_selected_candidates": sum(1 for t in targets if t["category"] == "expected_selected_and_all_candidate"),
        "untouched_peer_targets": sum(1 for t in targets if t["category"] == "untouched_peer_eligible_all_only"),
        "distinct_model_names": len(set(t["model_name"] for t in targets if t.get("model_name"))),
        "distinct_fold_vocabulary_hashes_among_eligible": len(set(
            t["fold_vocabulary_hash"] for t in targets if t["category"] != "excluded" and t.get("fold_vocabulary_hash")
        )),
    }

    return {"targets": targets, "totals": totals}, shots_by_name, None


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

report = {
    "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "python_version": sys.version,
    "checks": [],
    "anomalies": ANOMALIES,
}


def check(name, condition, detail=None):
    report["checks"].append({"name": name, "pass": bool(condition), "detail": repr(detail) if detail is not None else None})
    try:
        sys.stdout.write("[%s] %s%s\n" % ("PASS" if condition else "FAIL", name, ("" if detail is None else " -- %r" % (detail,))))
    except Exception:
        pass


pre_fingerprint = None
post_fingerprint = None
baseline_ns = None
run_started = False
run_completed_cleanly = False

try:
    # --- 1. SHA verification, before anything else. ---
    with open(BASELINE_SOURCE_PATH, "rb") as f:
        baseline_source = f.read()
    baseline_sha = hashlib.sha256(baseline_source).hexdigest()
    check("baseline.sha256_matches_expected", baseline_sha == EXPECTED_HISTORICAL_BASELINE_SHA256, baseline_sha)

    with open(PRODUCTION_NORMALIZER_PATH, "rb") as f:
        production_bytes = f.read()
    production_sha = hashlib.sha256(production_bytes).hexdigest()
    check("production_normalizer.sha256_unreplaced", production_sha == EXPECTED_PRODUCTION_NORMALIZER_SHA256, production_sha)

    with open(CANONICAL_MASTER_PATH, "rb") as f:
        master_bytes = f.read()
    master_sha = hashlib.sha256(master_bytes).hexdigest()
    check("canonical_master.sha256_unchanged", master_sha == EXPECTED_CANONICAL_MASTER_SHA256, master_sha)

    if not (baseline_sha == EXPECTED_HISTORICAL_BASELINE_SHA256
            and production_sha == EXPECTED_PRODUCTION_NORMALIZER_SHA256
            and master_sha == EXPECTED_CANONICAL_MASTER_SHA256):
        raise CheckpointC1Error("One or more pre-flight SHA-256 checks failed -- refusing to proceed.")

    # --- 2. Fixture/selected-shot identity verification. ---
    witness, shots_by_name, witness_error = build_independent_witness()
    if witness_error is not None:
        raise CheckpointC1Error("Could not build independent witness: %s" % witness_error)

    for key, expected_value in EXPECTED_B2_TOTALS.items():
        actual_value = witness["totals"].get(key)
        check("fixture.totals.%s_matches_B2" % key, actual_value == expected_value, (actual_value, expected_value))

    matching_shots = shots_by_name.get(EXPECTED_SELECTED_SHOT_NAME, [])
    check("fixture.selected_shot_name_present_exactly_once", len(matching_shots) == 1, len(matching_shots))
    selected_shot_obj = matching_shots[0] if len(matching_shots) == 1 else None

    selected_target_rows = [
        t for t in witness["targets"]
        if t["shot_name"] == EXPECTED_SELECTED_SHOT_NAME and t["category"] == "expected_selected_and_all_candidate"
    ]
    check("fixture.selected_shot_has_exactly_two_expected_targets", len(selected_target_rows) == 2, len(selected_target_rows))

    for t in selected_target_rows:
        expected = EXPECTED_SELECTED_TARGETS.get(t["aset_name"])
        if expected is None:
            anomaly("Unexpected selected target name in shot3: %r" % t["aset_name"])
            continue
        check("fixture.%s.model_name_matches" % t["aset_name"], t["model_name"] == expected["model_name"], t["model_name"])
        check("fixture.%s.control_count_matches" % t["aset_name"], t["control_count"] == expected["control_count"], t["control_count"])
        check("fixture.%s.vocabulary_hash_matches" % t["aset_name"],
              t["fold_vocabulary_hash"] == expected["fold_vocabulary_hash"], t["fold_vocabulary_hash"])

    untouched_peer_rows = [t for t in witness["targets"] if t["category"] == "untouched_peer_eligible_all_only"]
    check("fixture.untouched_peer_count_matches_B2", len(untouched_peer_rows) == EXPECTED_B2_TOTALS["untouched_peer_targets"], len(untouched_peer_rows))

    fixture_ok = all(c["pass"] for c in report["checks"])
    if not fixture_ok:
        anomaly("Fixture identity verification did not fully match the B-2 witness -- proceeding to fingerprint capture "
                "anyway so the mismatch is fully documented, but this run cannot be trusted as equivalent to B-2's fixture.")

    # --- 3. Build the fingerprint-function namespace (extracted, SHA-pinned). ---
    all_lines = production_bytes.decode("ascii").splitlines()
    blocks = []
    for label, start, end in FINGERPRINT_FUNCTION_RANGES:
        blocks.append("\n".join(all_lines[start - 1:end]))
    combined_source = "\n\n".join(blocks)

    fp_ns = dict(FINGERPRINT_MODULE_CONSTANTS)
    fp_ns["hashlib"] = hashlib
    exec(compile(combined_source, "<checkpoint_c1_fingerprint_functions>", "exec"), fp_ns)
    check("fingerprint_functions.extracted_and_exec_ok", True)

    capture_snapshot_explicit_fn = fp_ns["capture_snapshot_explicit"]

    def canonicalize_snapshot(snap):
        """Strips process-local handle integers (nondeterministic across
        sessions); keeps every semantic field."""
        clean = dict(snap)
        for key in ("shot_handle", "animation_set_handle", "root_handle", "rig_handle", "registry_handle"):
            clean.pop(key, None)
        clean.pop("control_handles", None)
        return clean

    def capture_all(label, targets_of_interest):
        """targets_of_interest: list of (shot_obj, aset_name) pairs to
        re-resolve fresh from the live document (never held across the
        baseline's own mutation)."""
        result = {}
        all_shots_now = list(sfmApp.GetShots())
        shots_by_name_now = {}
        for shot in all_shots_now:
            shots_by_name_now.setdefault(b_name(shot), []).append(shot)

        for shot_name, aset_name in targets_of_interest:
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

    targets_of_interest = [(EXPECTED_SELECTED_SHOT_NAME, name_) for name_ in EXPECTED_SELECTED_TARGETS.keys()]
    targets_of_interest.extend((t["shot_name"], t["aset_name"]) for t in untouched_peer_rows)

    # --- 4. PRE fingerprint. ---
    pre_fingerprint = capture_all("PRE", targets_of_interest)
    check("fingerprint.pre_capture_count_matches_expected", len(pre_fingerprint) == 85, len(pre_fingerprint))
    pre_hash = stable_hash([u"%s=%s" % (k, json.dumps(v, sort_keys=True)) for k, v in pre_fingerprint.items()])

    # --- 5. Invoke the historical baseline (blocks on its own real,
    #        unmodified interactive scope dialog). ---
    main_window = sfmApp.GetMainWindow()
    check("baseline.main_window_available", main_window is not None)

    sys.stdout.write(
        "\n>>> Historical baseline is about to run its own real Selected/All "
        "Shots dialog. Select 'Selected Shots' and confirm. <<<\n\n"
    )

    baseline_ns = {}
    run_started = False
    try:
        exec(compile(baseline_source, "<historical_baseline_pre_integration>", "exec"), baseline_ns)
    except Exception as exc:
        anomaly("Historical baseline execution raised: %r" % exc)
        anomaly(traceback.format_exc())

    run_lock_name = baseline_ns.get("RUN_LOCK_NAME")

    def baseline_run_is_active():
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

    active_now = baseline_run_is_active()
    if active_now:
        run_started = True
        sys.stdout.write("Baseline run detected as active; waiting for completion...\n")
        wait_start = time.time()
        MAX_WAIT_SECONDS = 1800
        while baseline_run_is_active():
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.05)
            if time.time() - wait_start > MAX_WAIT_SECONDS:
                anomaly("Baseline run did not complete within %d seconds -- aborting wait." % MAX_WAIT_SECONDS)
                break
        else:
            run_completed_cleanly = True
        # Drain a little extra to let any final deferred callback settle.
        settle_start = time.time()
        while time.time() - settle_start < 1.0:
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.05)
    else:
        anomaly(
            "No historical run-lock was ever observed active after executing the baseline source -- "
            "this most likely means the operator cancelled the scope dialog, or the dialog is still "
            "awaiting operator interaction. No mutation is believed to have occurred."
        )

    check("baseline.run_was_started", run_started)
    check("baseline.run_completed_within_timeout", run_completed_cleanly if run_started else False)

    # --- 6. POST fingerprint. ---
    post_fingerprint = capture_all("POST", targets_of_interest)
    check("fingerprint.post_capture_count_matches_expected", len(post_fingerprint) == 85, len(post_fingerprint))
    post_hash = stable_hash([u"%s=%s" % (k, json.dumps(v, sort_keys=True)) for k, v in post_fingerprint.items()])

    # --- 7. Compare. ---
    touched_targets = []
    unchanged_targets = []
    for key in sorted(set(pre_fingerprint.keys()) | set(post_fingerprint.keys())):
        pre_v = pre_fingerprint.get(key)
        post_v = post_fingerprint.get(key)
        if json.dumps(pre_v, sort_keys=True) != json.dumps(post_v, sort_keys=True):
            touched_targets.append(key)
        else:
            unchanged_targets.append(key)

    expected_touched_keys = set(u"%s|%s" % (EXPECTED_SELECTED_SHOT_NAME, n) for n in EXPECTED_SELECTED_TARGETS.keys())
    actual_touched_keys = set(touched_targets)

    check("comparison.touched_set_equals_expected_selected_targets",
          actual_touched_keys == expected_touched_keys, sorted(actual_touched_keys))
    unexpected_touched = actual_touched_keys - expected_touched_keys
    missing_expected_touch = expected_touched_keys - actual_touched_keys
    check("comparison.no_unexpected_targets_touched", len(unexpected_touched) == 0, sorted(unexpected_touched))
    check("comparison.both_expected_selected_targets_touched", len(missing_expected_touch) == 0, sorted(missing_expected_touch))

    untouched_peer_keys = set(u"%s|%s" % (t["shot_name"], t["aset_name"]) for t in untouched_peer_rows)
    unexpectedly_touched_peers = untouched_peer_keys & actual_touched_keys
    check("comparison.no_untouched_peer_was_touched", len(unexpectedly_touched_peers) == 0, sorted(unexpectedly_touched_peers))

    report["pre_fingerprint_hash"] = pre_hash
    report["post_fingerprint_hash"] = post_hash
    report["touched_targets"] = sorted(touched_targets)
    report["unchanged_targets_count"] = len(unchanged_targets)
    report["pre_fingerprint"] = pre_fingerprint
    report["post_fingerprint"] = post_fingerprint

except Exception as top_exc:
    anomaly("UNHANDLED TOP-LEVEL EXCEPTION: %s" % repr(top_exc))
    anomaly(traceback.format_exc())

# ---------------------------------------------------------------------------
# Finalize / write output.
# ---------------------------------------------------------------------------

all_checks_passed = all(c["pass"] for c in report["checks"]) if report["checks"] else False
completed_without_exception = not any("UNHANDLED TOP-LEVEL EXCEPTION" in a for a in ANOMALIES)
report["overall_pass"] = bool(all_checks_passed and completed_without_exception and run_started)
report["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

json_write_ok = True
try:
    with open(JSON_OUTPUT_PATH, "wb") as f:
        f.write(json.dumps(report, indent=2, sort_keys=True).encode("utf-8"))
except Exception:
    json_write_ok = False

summary_lines = []
summary_lines.append("SFM CHECKPOINT C1 -- BASELINE (PRE-INTEGRATION) SELECTED-SHOTS RUN")
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
summary_lines.append("run_started=%r  run_completed_cleanly=%r" % (run_started, run_completed_cleanly))
summary_lines.append("pre_fingerprint_hash=%r" % report.get("pre_fingerprint_hash"))
summary_lines.append("post_fingerprint_hash=%r" % report.get("post_fingerprint_hash"))
summary_lines.append("touched_targets=%r" % report.get("touched_targets"))
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
summary_write_ok = True
try:
    with open(SUMMARY_OUTPUT_PATH, "wb") as f:
        f.write(summary_text.encode("ascii", "replace"))
except Exception:
    summary_write_ok = False

try:
    sys.stdout.write(summary_text.encode("ascii", "replace"))
    sys.stdout.write(
        "\nCheckpoint C1 reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok)
    )
    sys.stdout.write("\nDO NOT SAVE. Restart SFM to discard this baseline mutation before C2.\n")
except Exception:
    pass
