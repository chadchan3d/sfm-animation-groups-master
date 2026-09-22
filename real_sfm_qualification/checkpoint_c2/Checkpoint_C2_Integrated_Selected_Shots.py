# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint C2: Integrated (post-
integration) Selected-Shots run.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: **THIS CHECKPOINT MUTATES THE SCENE.** It invokes the
REAL, INSTALLED, ACCEPTED, INTEGRATED production Normalizer (the exact
file this session's own SHA-256 gate below pins), never a copy, never
the historical baseline, against the SAME disposable qualification
project Checkpoint C1 used. Do not save afterward.

Purpose:
  Mechanically prove that the integrated (post-Production-Normalizer-
  Integration) Selected-Shots outcome is semantically equivalent to
  Checkpoint C1's own already-accepted historical baseline outcome --
  not merely "close", but equivalent on a per-target basis for every
  one of the 85 independently-witnessed eligible targets. This script:
    1. verifies the currently-installed production Normalizer's own
       SHA-256 (the file this checkpoint is ABOUT TO EXECUTE, not just
       identity-check -- unlike C1, which only fingerprinted with this
       file's functions but executed a SEPARATE historical file);
    2. verifies the canonical Master's SHA-256;
    3. loads Checkpoint C1's own machine-readable result artifact from
       disk and integrity-checks it (its own pre/post fingerprint
       hashes must equal the exact values the operator reported as
       C1-2's accepted PASS result) before trusting it as ground truth;
    4. independently re-derives the Checkpoint-B-style fixture witness
       fresh from the live document, cross-checked against the exact
       B-2 witness values (same fixture Checkpoint C1 required);
    5. captures a structural PRE fingerprint of all 85 eligible targets
       using the SAME already-qualified, purely read-only
       capture_snapshot_explicit()/capture_tree()/discover_rig_context()
       functions C1 used, extracted verbatim from this run's own
       production Normalizer file;
    6. HARD GATES on: every fixture-identity check above, AND the fresh
       integrated PRE fingerprint hash matching C1's own accepted PRE
       hash exactly (starting-state parity) -- if the live state does
       not match this required baseline, this script aborts BEFORE any
       invocation of the production Normalizer or scene mutation;
    7. only if that combined gate passes, executes the exact, byte-
       verified, installed production Normalizer source in an isolated
       namespace (never imported as a module) -- this triggers the
       Normalizer's own real, unmodified, interactive Clip-Editor
       scope-choice dialog; the operator must select Selected Shots
       and confirm, exactly as C1 required;
    8. waits (pumping the real Qt event loop, polling the production
       Normalizer's own RUN_LOCK_NAME run-lock object) for that real,
       asynchronous operation to finish;
    9. captures the same structural POST fingerprint for all 85 targets;
   10. performs six required comparisons (A-F, see below) between this
       run's own PRE/POST captures and C1's own accepted PRE/POST
       captures, per-target, never relying on aggregate hashes alone;
   11. captures shared-authority runtime evidence (API version, build
       id, canonical state, provider/lease counters) via the exec-
       exposed `authority_runtime`/`authority_errors` module bindings
       this run's own production Normalizer source already imports --
       an EXISTING qualified diagnostic, not new instrumentation;
   12. captures native-protection/command-completion evidence by
       reading the production Normalizer's OWN existing log file
       (OUTPUT_PATH), which this exact run's own start() method opens
       in "w" (truncate) mode -- so its content, read after this run
       completes, pertains ONLY to this run;
   13. writes a complete machine-readable result artifact.

Comparisons performed (see report["comparisons"] for the machine-
readable results of each):
  A. starting_state_parity   -- integrated PRE hash == C1 PRE hash
  B. scope_parity            -- touched-target set (this run) == the
                                 fixed expected 2-target set == C1's
                                 own reported touched-target set
  C. final_state_parity      -- integrated POST hash == C1 POST hash
  D. per_target_parity       -- ALL 85 eligible targets compared
                                 individually (this run's canonicalized
                                 POST snapshot vs C1's own canonicalized
                                 POST snapshot), never aggregate-hash-only
  E. untouched_peer_parity   -- for all 83 untouched peers: this run's
                                 PRE == this run's POST == C1's PRE ==
                                 C1's POST (four-way, per target)
  F. selected_target_parity  -- Fox and Mia compared individually
                                 (this run's POST vs C1's own POST)

This script never modifies the historical baseline file, never
modifies the production Normalizer, never modifies the canonical
Master (other than the read-only SHA-256 check), and never touches
`sfm_master_authority_productionized`/`sfm_master_sidecar` except by
reading the module bindings the production Normalizer's own source
already imports at its own module scope.

Output:
  Two files are written to C:\\Users\\Public\\Documents\\:
    sfm_checkpoint_c2_integrated_result.json           (machine-readable, full detail)
    sfm_checkpoint_c2_integrated_result_summary.txt    (concise human-readable)
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

EXPECTED_PRODUCTION_NORMALIZER_SHA256 = (
    "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"
)
EXPECTED_CANONICAL_MASTER_SHA256 = (
    "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
)

# The exact C1-2 accepted result, ground-truthed directly from the real
# sfm_checkpoint_c1_baseline_result.json artifact on disk at authoring
# time (not retyped from a conversation transcript).
EXPECTED_C1_PRE_HASH = (
    "eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0"
)
EXPECTED_C1_POST_HASH = (
    "d7b3bacb757253e126823db4e1445b57e4278d972c9be8b23920fc88cf1b5938"
)
EXPECTED_C1_TOUCHED_TARGETS = [u"shot3|foxmccouldwm1", u"shot3|mia1"]
EXPECTED_C1_UNCHANGED_TARGETS_COUNT = 83

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

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_c2_integrated_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_c2_integrated_result_summary.txt"
C1_JSON_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_c1_baseline_result.json"

# This is the production Normalizer's OWN OUTPUT_PATH constant (verified
# by direct grep of the currently installed file, SHA-pinned above,
# 2026-09-22), opened in "w" (truncate) mode by its own start() method --
# so reading it after THIS run completes reflects only THIS run.
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

# 1-indexed, inclusive. IDENTICAL range table to Checkpoint C1's own
# (same reasoning: pure, read-only, structural DME-reading functions,
# never scope/eligibility POLICY, extracted from THIS run's own
# production Normalizer file, SHA-pinned above). Re-verify with:
#   sed -n '<start>,<end>p' Rebuild_Control_Groups_Normalizer.py
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


class CheckpointC2Error(Exception):
    pass


ANOMALIES = []


def anomaly(message):
    ANOMALIES.append(message)
    try:
        sys.stdout.write("ANOMALY: %s\n" % message)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Independent Checkpoint-B-style fact/classification helpers (same copy
# used by Checkpoint C1, kept verbatim for internal consistency between
# checkpoints' witnesses).
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
                raise CheckpointC2Error(
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


def dumps_sorted(value):
    return json.dumps(value, sort_keys=True)


def differing_top_level_fields(a, b):
    """Best-effort diagnostic: which top-level keys of two canonicalized
    snapshot dicts differ (by their own JSON-serialized value)."""
    if not isinstance(a, dict) or not isinstance(b, dict):
        return ["<non-dict-comparison>"]
    keys = sorted(set(a.keys()) | set(b.keys()))
    out = []
    for k in keys:
        if dumps_sorted(a.get(k)) != dumps_sorted(b.get(k)):
            out.append(k)
    return out


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

report = {
    "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "python_version": sys.version,
    "checks": [],
    "anomalies": ANOMALIES,
    "comparisons": {},
    "authority_runtime_evidence": {},
    "native_protection_evidence": {},
}


def check(name, condition, detail=None):
    report["checks"].append({"name": name, "pass": bool(condition), "detail": repr(detail) if detail is not None else None})
    try:
        sys.stdout.write("[%s] %s%s\n" % ("PASS" if condition else "FAIL", name, ("" if detail is None else " -- %r" % (detail,))))
    except Exception:
        pass


integrated_pre_fingerprint = None
integrated_post_fingerprint = None
prod_ns = None
run_started = False
run_completed_cleanly = False
c1_report = None

try:
    # --- 1. SHA verification of the file this checkpoint is ABOUT TO
    #        EXECUTE (unlike C1, which only fingerprinted with this
    #        file's functions but executed a SEPARATE historical file). ---
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
        raise CheckpointC2Error("One or more pre-flight SHA-256 checks failed -- refusing to proceed.")

    # --- 2. Load and integrity-verify Checkpoint C1's own accepted
    #        result artifact -- this is the ground truth every later
    #        comparison is measured against. ---
    try:
        with open(C1_JSON_PATH, "rb") as f:
            c1_raw = f.read()
        c1_report = json.loads(c1_raw.decode("utf-8"))
    except Exception as exc:
        raise CheckpointC2Error("Could not read/parse Checkpoint C1 result artifact at %r: %r" % (C1_JSON_PATH, exc))

    check("c1_baseline.overall_pass_was_true", bool(c1_report.get("overall_pass")) is True, c1_report.get("overall_pass"))
    check("c1_baseline.pre_fingerprint_hash_matches_pinned", c1_report.get("pre_fingerprint_hash") == EXPECTED_C1_PRE_HASH, c1_report.get("pre_fingerprint_hash"))
    check("c1_baseline.post_fingerprint_hash_matches_pinned", c1_report.get("post_fingerprint_hash") == EXPECTED_C1_POST_HASH, c1_report.get("post_fingerprint_hash"))
    check("c1_baseline.touched_targets_matches_pinned", sorted(c1_report.get("touched_targets") or []) == sorted(EXPECTED_C1_TOUCHED_TARGETS), c1_report.get("touched_targets"))
    check("c1_baseline.unchanged_targets_count_matches_pinned", c1_report.get("unchanged_targets_count") == EXPECTED_C1_UNCHANGED_TARGETS_COUNT, c1_report.get("unchanged_targets_count"))

    c1_pre_fingerprint = c1_report.get("pre_fingerprint") or {}
    c1_post_fingerprint = c1_report.get("post_fingerprint") or {}
    check("c1_baseline.pre_fingerprint_has_85_targets", len(c1_pre_fingerprint) == 85, len(c1_pre_fingerprint))
    check("c1_baseline.post_fingerprint_has_85_targets", len(c1_post_fingerprint) == 85, len(c1_post_fingerprint))

    if not all(c["pass"] for c in report["checks"]):
        raise CheckpointC2Error(
            "C1 BASELINE ARTIFACT MISMATCH -- the loaded Checkpoint C1 result artifact "
            "does not match the pinned accepted C1-2 identity, or is not a PASSing "
            "result, or does not carry per-target fingerprint data. Aborting BEFORE "
            "any fixture witness build, fingerprinting, or Normalizer invocation."
        )

    # --- 3. Fixture/selected-shot identity verification (identical
    #        fixture Checkpoint C1 required -- same disposable project,
    #        same live selection). ---
    witness, shots_by_name, witness_error = build_independent_witness()
    if witness_error is not None:
        raise CheckpointC2Error("Could not build independent witness: %s" % witness_error)

    for key, expected_value in EXPECTED_B2_TOTALS.items():
        actual_value = witness["totals"].get(key)
        check("fixture.totals.%s_matches_B2" % key, actual_value == expected_value, (actual_value, expected_value))

    selected_shot_names = sorted(set(t["shot_name"] for t in witness["targets"] if t["shot_selected"]))
    check("fixture.selected_shot_set_is_exactly_shot3", selected_shot_names == [EXPECTED_SELECTED_SHOT_NAME], selected_shot_names)

    matching_shots = shots_by_name.get(EXPECTED_SELECTED_SHOT_NAME, [])
    check("fixture.selected_shot_name_present_exactly_once", len(matching_shots) == 1, len(matching_shots))

    selected_target_rows = [
        t for t in witness["targets"]
        if t["shot_name"] == EXPECTED_SELECTED_SHOT_NAME and t["category"] == "expected_selected_and_all_candidate"
    ]
    check("fixture.selected_shot_has_exactly_two_expected_targets", len(selected_target_rows) == 2, len(selected_target_rows))

    expected_target_names = set(EXPECTED_SELECTED_TARGETS.keys())
    actual_selected_target_names = set(t["aset_name"] for t in selected_target_rows)
    check("fixture.expected_selected_target_set_is_exact", actual_selected_target_names == expected_target_names, sorted(actual_selected_target_names))

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

    all_eligible_rows = [t for t in witness["targets"] if t["category"] != "excluded"]
    check("fixture.all_eligible_count_is_85", len(all_eligible_rows) == 85, len(all_eligible_rows))

    targets_of_interest = [(t["shot_name"], t["aset_name"]) for t in all_eligible_rows]
    live_target_keys = set(u"%s|%s" % (sn, an) for sn, an in targets_of_interest)
    c1_target_keys = set(c1_post_fingerprint.keys())
    check("fixture.live_target_key_set_matches_c1_baseline_target_key_set", live_target_keys == c1_target_keys, sorted(live_target_keys ^ c1_target_keys))

    # --- 4. Build the fingerprint-function namespace (extracted, SHA-
    #        pinned to the SAME file this checkpoint is about to
    #        execute). ---
    all_lines = production_bytes.decode("ascii").splitlines()
    blocks = []
    for label, start, end in FINGERPRINT_FUNCTION_RANGES:
        blocks.append("\n".join(all_lines[start - 1:end]))
    combined_source = "\n\n".join(blocks)

    fp_ns = dict(FINGERPRINT_MODULE_CONSTANTS)
    fp_ns["hashlib"] = hashlib
    exec(compile(combined_source, "<checkpoint_c2_fingerprint_functions>", "exec"), fp_ns)
    check("fingerprint_functions.extracted_and_exec_ok", True)

    capture_snapshot_explicit_fn = fp_ns["capture_snapshot_explicit"]

    def canonicalize_snapshot(snap):
        """Identical to Checkpoint C1's own canonicalize_snapshot: strips
        process-local handle integers and the PRE/POST `label` field
        before any equality/hash comparison."""
        clean = dict(snap)
        for key in ("shot_handle", "animation_set_handle", "root_handle", "rig_handle", "registry_handle", "label"):
            clean.pop(key, None)
        clean.pop("control_handles", None)
        return clean

    def capture_all(label, targets_of_interest_local):
        """targets_of_interest_local: list of (shot_name, aset_name) pairs
        to re-resolve fresh from the live document (never held across the
        Normalizer's own mutation)."""
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

    # --- 5. Integrated PRE fingerprint (non-mutating, all 85 targets). ---
    integrated_pre_fingerprint = capture_all("PRE", targets_of_interest)
    check("fingerprint.pre_capture_count_matches_expected", len(integrated_pre_fingerprint) == 85, len(integrated_pre_fingerprint))
    integrated_pre_hash = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in integrated_pre_fingerprint.items()])
    report["integrated_pre_fingerprint_hash"] = integrated_pre_hash

    # --- Comparison A: starting-state parity. This is also part of the
    #     hard gate below -- a mismatch here means the live state does
    #     not match the required C1 baseline, and this script must abort
    #     BEFORE invoking the production Normalizer. ---
    check("gate.integrated_pre_hash_matches_c1_pre_hash", integrated_pre_hash == EXPECTED_C1_PRE_HASH, integrated_pre_hash)

    # --- HARD GATE: every check recorded above -- structural fixture
    #     identity AND starting-state fingerprint parity -- must pass
    #     BEFORE any invocation of the production Normalizer or scene
    #     mutation. Mirrors Checkpoint C1's own corrected (C1-2) hard-
    #     gate discipline; this is a hard abort, not a documented-and-
    #     continue anomaly. ---
    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointC2Error(
            "STARTING-STATE / FIXTURE MISMATCH -- one or more required pre-flight, "
            "C1-artifact-integrity, fixture-identity, or starting-state-parity checks "
            "failed (see the individual [FAIL] lines above/in this report for exactly "
            "which condition(s) did not hold). Aborting BEFORE any invocation of the "
            "production Normalizer or scene mutation. The live selection/project does "
            "not match the required C1 baseline state -- re-verify the selected shot, "
            "project, and installed files before rerunning; do not proceed on a "
            "mismatched starting state."
        )

    # --- 6. Invoke the REAL installed, accepted, integrated production
    #        Normalizer (blocks on its own real, unmodified interactive
    #        scope dialog; its own module-level StartRebuildControlGroups()
    #        call fires as soon as this exec() runs the module body). ---
    main_window = sfmApp.GetMainWindow()
    check("normalizer.main_window_available", main_window is not None)

    sys.stdout.write(
        "\n>>> The integrated production Normalizer is about to run its own real "
        "Selected/All Shots dialog. Select 'Selected Shots' and confirm. <<<\n\n"
    )

    prod_ns = {}
    run_started = False
    try:
        # `production_bytes` is passed RAW (undecoded), not the decoded
        # unicode `all_lines`/`combined_source` used for fingerprint-
        # function extraction above -- the file's own line-1
        # "# -*- coding: ascii -*-" declaration makes compile() raise
        # "SyntaxError: encoding declaration in Unicode string" if a
        # decoded unicode string is passed instead (same class of bug
        # already hit and fixed elsewhere in this project's own
        # qualification suite). Matches Checkpoint C1's own working
        # `compile(baseline_source, ...)` call, which also passes raw
        # bytes read straight from disk.
        exec(compile(production_bytes, "<installed_production_normalizer>", "exec"), prod_ns)
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
        sys.stdout.write("Integrated run detected as active; waiting for completion...\n")
        wait_start = time.time()
        MAX_WAIT_SECONDS = 1800
        while normalizer_run_is_active():
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.05)
            if time.time() - wait_start > MAX_WAIT_SECONDS:
                anomaly("Integrated run did not complete within %d seconds -- aborting wait." % MAX_WAIT_SECONDS)
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
            "No integrated run-lock was ever observed active after executing the "
            "production Normalizer source -- this most likely means the operator "
            "cancelled the scope dialog, or the dialog is still awaiting operator "
            "interaction. No mutation is believed to have occurred."
        )

    check("normalizer.run_was_started", run_started)
    check("normalizer.run_completed_within_timeout", run_completed_cleanly if run_started else False)

    # --- 7. Integrated POST fingerprint (all 85 targets). ---
    integrated_post_fingerprint = capture_all("POST", targets_of_interest)
    check("fingerprint.post_capture_count_matches_expected", len(integrated_post_fingerprint) == 85, len(integrated_post_fingerprint))
    integrated_post_hash = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in integrated_post_fingerprint.items()])
    report["integrated_post_fingerprint_hash"] = integrated_post_hash

    # --- 8. This run's own touched/unchanged determination (integrated
    #        PRE vs integrated POST), same technique C1 used. ---
    touched_targets = []
    unchanged_targets = []
    for key in sorted(set(integrated_pre_fingerprint.keys()) | set(integrated_post_fingerprint.keys())):
        pre_v = integrated_pre_fingerprint.get(key)
        post_v = integrated_post_fingerprint.get(key)
        if dumps_sorted(pre_v) != dumps_sorted(post_v):
            touched_targets.append(key)
        else:
            unchanged_targets.append(key)
    report["touched_targets"] = sorted(touched_targets)
    report["unchanged_targets_count"] = len(unchanged_targets)

    expected_touched_keys = set(u"%s|%s" % (EXPECTED_SELECTED_SHOT_NAME, n) for n in EXPECTED_SELECTED_TARGETS.keys())
    actual_touched_keys = set(touched_targets)
    c1_touched_keys = set(c1_report.get("touched_targets") or [])

    # ------------------------------------------------------------------
    # Comparison B: scope parity.
    # ------------------------------------------------------------------
    comp_b = {}
    comp_b["touched_set_equals_fixed_expected_set"] = (actual_touched_keys == expected_touched_keys)
    comp_b["touched_set_equals_c1_touched_set"] = (actual_touched_keys == c1_touched_keys)
    comp_b["unexpected_targets_touched"] = sorted(actual_touched_keys - expected_touched_keys)
    comp_b["expected_targets_not_touched"] = sorted(expected_touched_keys - actual_touched_keys)
    comp_b["pass"] = bool(comp_b["touched_set_equals_fixed_expected_set"] and comp_b["touched_set_equals_c1_touched_set"])
    report["comparisons"]["B_scope_parity"] = comp_b
    check("comparison.B_scope_parity", comp_b["pass"], (sorted(actual_touched_keys), sorted(c1_touched_keys)))

    # ------------------------------------------------------------------
    # Comparison C: final-state parity (aggregate hash).
    # ------------------------------------------------------------------
    comp_c = {
        "integrated_post_hash": integrated_post_hash,
        "c1_post_hash": EXPECTED_C1_POST_HASH,
        "pass": bool(integrated_post_hash == EXPECTED_C1_POST_HASH),
    }
    report["comparisons"]["C_final_state_parity"] = comp_c
    check("comparison.C_final_state_parity", comp_c["pass"], integrated_post_hash)

    # ------------------------------------------------------------------
    # Comparison D: per-target parity, ALL 85 eligible targets
    # individually -- never aggregate-hash-only, even though C already
    # passed/failed on the aggregate hash above.
    # ------------------------------------------------------------------
    per_target_results = []
    equal_count = 0
    differing_count = 0
    missing_in_c1 = []
    missing_in_integrated = []
    for key in sorted(live_target_keys):
        integrated_v = integrated_post_fingerprint.get(key)
        c1_v = c1_post_fingerprint.get(key)
        if key not in c1_post_fingerprint:
            missing_in_c1.append(key)
            continue
        if key not in integrated_post_fingerprint:
            missing_in_integrated.append(key)
            continue
        is_equal = dumps_sorted(integrated_v) == dumps_sorted(c1_v)
        if is_equal:
            equal_count += 1
        else:
            differing_count += 1
        entry = {"target": key, "equal": is_equal}
        if not is_equal:
            entry["differing_fields"] = differing_top_level_fields(integrated_v, c1_v)
        per_target_results.append(entry)

    comp_d = {
        "total_targets_compared": len(per_target_results),
        "equal_count": equal_count,
        "differing_count": differing_count,
        "missing_in_c1_baseline": missing_in_c1,
        "missing_in_integrated_run": missing_in_integrated,
        "differing_targets": [e for e in per_target_results if not e["equal"]],
        "pass": bool(
            len(per_target_results) == 85
            and differing_count == 0
            and not missing_in_c1
            and not missing_in_integrated
        ),
    }
    report["comparisons"]["D_per_target_parity"] = comp_d
    check("comparison.D_per_target_parity_all_85_individually_equal", comp_d["pass"], (equal_count, differing_count))

    # ------------------------------------------------------------------
    # Comparison E: untouched-peer parity, four-way, per target:
    # integrated PRE == integrated POST == C1 PRE == C1 POST.
    # ------------------------------------------------------------------
    untouched_peer_keys = sorted(u"%s|%s" % (t["shot_name"], t["aset_name"]) for t in untouched_peer_rows)
    peer_results = []
    peer_all_equal = True
    for key in untouched_peer_keys:
        i_pre = integrated_pre_fingerprint.get(key)
        i_post = integrated_post_fingerprint.get(key)
        c1_pre_v = c1_pre_fingerprint.get(key)
        c1_post_v = c1_post_fingerprint.get(key)
        forms = {
            "integrated_pre": dumps_sorted(i_pre),
            "integrated_post": dumps_sorted(i_post),
            "c1_pre": dumps_sorted(c1_pre_v),
            "c1_post": dumps_sorted(c1_post_v),
        }
        four_way_equal = (forms["integrated_pre"] == forms["integrated_post"] == forms["c1_pre"] == forms["c1_post"])
        if not four_way_equal:
            peer_all_equal = False
            peer_results.append({"target": key, "four_way_equal": False})
    comp_e = {
        "peer_count": len(untouched_peer_keys),
        "peers_failing_four_way_parity": peer_results,
        "pass": bool(peer_all_equal and len(untouched_peer_keys) == 83),
    }
    report["comparisons"]["E_untouched_peer_parity"] = comp_e
    check("comparison.E_untouched_peer_parity_all_83_four_way_equal", comp_e["pass"], len(peer_results))

    # ------------------------------------------------------------------
    # Comparison F: selected-target parity, Fox and Mia individually.
    # ------------------------------------------------------------------
    comp_f = {}
    for aset_name in EXPECTED_SELECTED_TARGETS.keys():
        key = u"%s|%s" % (EXPECTED_SELECTED_SHOT_NAME, aset_name)
        integrated_v = integrated_post_fingerprint.get(key)
        c1_v = c1_post_fingerprint.get(key)
        is_equal = dumps_sorted(integrated_v) == dumps_sorted(c1_v) if (integrated_v is not None and c1_v is not None) else False
        entry = {"present_in_integrated": key in integrated_post_fingerprint, "present_in_c1": key in c1_post_fingerprint, "equal": is_equal}
        if not is_equal:
            entry["differing_fields"] = differing_top_level_fields(integrated_v, c1_v)
        comp_f[aset_name] = entry
        check("comparison.F_selected_target_parity.%s" % aset_name, is_equal, entry)
    comp_f["pass"] = bool(all(comp_f[n]["equal"] for n in EXPECTED_SELECTED_TARGETS.keys()))
    report["comparisons"]["F_selected_target_parity"] = comp_f

    # A recap entry for Comparison A (already gated above, restated here
    # for a complete A-F record in one place).
    report["comparisons"]["A_starting_state_parity"] = {
        "integrated_pre_hash": integrated_pre_hash,
        "c1_pre_hash": EXPECTED_C1_PRE_HASH,
        "pass": bool(integrated_pre_hash == EXPECTED_C1_PRE_HASH),
    }

    report["pre_fingerprint_hash"] = integrated_pre_hash
    report["post_fingerprint_hash"] = integrated_post_hash
    report["integrated_pre_fingerprint"] = integrated_pre_fingerprint
    report["integrated_post_fingerprint"] = integrated_post_fingerprint

    # ------------------------------------------------------------------
    # 9. Shared-authority runtime evidence -- via the exec-exposed
    #    module bindings the production Normalizer's own source already
    #    imports at its own module scope (existing qualified
    #    diagnostics, no invasive instrumentation).
    # ------------------------------------------------------------------
    evidence = report["authority_runtime_evidence"]
    try:
        authority_runtime = prod_ns.get("authority_runtime")
        evidence["module_binding_present"] = authority_runtime is not None
        if authority_runtime is not None:
            try:
                evidence["runtime_api_version"] = authority_runtime.RUNTIME_API_VERSION
            except Exception as exc:
                evidence["runtime_api_version_error"] = repr(exc)
            try:
                evidence["runtime_build_id"] = authority_runtime.RUNTIME_BUILD_ID
            except Exception as exc:
                evidence["runtime_build_id_error"] = repr(exc)
            try:
                evidence["is_canonical"] = bool(authority_runtime.is_canonical())
            except Exception as exc:
                evidence["is_canonical_error"] = repr(exc)
            try:
                evidence["get_state"] = authority_runtime.get_state()
            except Exception as exc:
                evidence["get_state_error"] = repr(exc)
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
                evidence["broker_acquired_idempotently"] = broker is not None
                try:
                    evidence["provider_counters"] = broker.provider_counters()
                except Exception as exc:
                    evidence["provider_counters_error"] = repr(exc)
                try:
                    evidence["outstanding_lease_count"] = broker.outstanding_lease_count()
                except Exception as exc:
                    evidence["outstanding_lease_count_error"] = repr(exc)
            except Exception as exc:
                evidence["broker_query_error"] = repr(exc)
        evidence["live_canonical_master_sha256"] = master_sha
        evidence["note"] = (
            "Captured from the exec-exposed module-level bindings the "
            "integrated production Normalizer's own source already "
            "imports (authority_runtime, plus a second, idempotent "
            "get_broker() call after the run to read aggregate "
            "provider/lease counters -- no new view is acquired or "
            "leased by this diagnostic call). No invasive instrumentation "
            "was added to the Normalizer or the authority package."
        )
    except Exception as exc:
        evidence["capture_error"] = repr(exc)
        anomaly("Authority runtime evidence capture raised: %r" % exc)

    # ------------------------------------------------------------------
    # 10. Native-protection / command-completion evidence -- via the
    #     production Normalizer's OWN existing log file, opened in "w"
    #     (truncate) mode by this exact run's own start() method, so its
    #     content reflects only this run. This is an inference from
    #     existing log evidence (the fail-closed gate raises ProbeError
    #     before reaching the "NATIVE_REBUILD_RETURNED = PASS" log line
    #     if native-handle acquisition/protection did not succeed), not
    #     new instrumentation. Checkpoint C2 does NOT build a dedicated
    #     native-handle coordination test -- that is a later checkpoint.
    # ------------------------------------------------------------------
    native_evidence = report["native_protection_evidence"]
    try:
        with open(NORMALIZER_LOG_PATH, "rb") as f:
            log_bytes = f.read()
        log_text = log_bytes.decode("ascii", "replace")
        native_evidence["log_path"] = NORMALIZER_LOG_PATH
        native_evidence["log_read_ok"] = True
        native_evidence["log_size_bytes"] = len(log_bytes)
        native_evidence["contains_NATIVE_GUARDS_PASS"] = ("NATIVE_GUARDS = PASS" in log_text)
        native_evidence["contains_NATIVE_REBUILD_RETURNED_PASS"] = ("NATIVE_REBUILD_RETURNED = PASS" in log_text)
        native_evidence["contains_production_revision_marker"] = (
            "SFM_REBUILD_CONTROL_GROUPS_CONTEXTUALIZER_PRODUCTION_2026_09_22_QUALIFIED_AUTHORITY" in log_text
        )
        native_evidence["inference"] = (
            "This run's own start() method opens OUTPUT_PATH in \"w\" (truncate) "
            "mode, so the content read here reflects only this run. The "
            "production Normalizer's own fail-closed gate raises ProbeError "
            "before reaching self.rebuild(...) if native-handle acquisition "
            "did not succeed, so the presence of the "
            "\"NATIVE_REBUILD_RETURNED = PASS\" log line is proof-by-"
            "construction that native protection was successfully acquired "
            "for this exact run -- an inference from an existing qualified "
            "log, not new instrumentation. The running command instance's "
            "own in-process state (its lease/broker reference) is a local "
            "variable inside StartRebuildControlGroups() and is not exposed "
            "as a module global, so it cannot be read directly; this log-"
            "based inference is the available substitute."
        )
    except Exception as exc:
        native_evidence["log_read_ok"] = False
        native_evidence["log_read_error"] = repr(exc)
        anomaly("Could not read production Normalizer log for native-protection evidence: %r" % exc)

except CheckpointC2Error as gate_exc:
    # Orderly, expected abort (pre-flight SHA mismatch, C1-artifact
    # integrity failure, fixture-identity mismatch, or starting-state
    # parity failure) -- distinct from an unexpected crash.
    anomaly("GATE FAILURE (orderly abort, no production Normalizer invocation attempted): %s" % gate_exc)
    report["gate_failure"] = True
except Exception as top_exc:
    anomaly("UNHANDLED TOP-LEVEL EXCEPTION: %s" % repr(top_exc))
    anomaly(traceback.format_exc())
    report["gate_failure"] = False

# ---------------------------------------------------------------------------
# Finalize / write output.
# ---------------------------------------------------------------------------

all_checks_passed = all(c["pass"] for c in report["checks"]) if report["checks"] else False
completed_without_exception = not any(
    a.startswith("UNHANDLED TOP-LEVEL EXCEPTION") for a in ANOMALIES
)
all_comparisons_passed = all(
    bool(v.get("pass")) for v in report["comparisons"].values()
) if report["comparisons"] else False
report["overall_pass"] = bool(
    all_checks_passed and completed_without_exception and run_started and all_comparisons_passed
)
report["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

json_write_ok = True
try:
    with open(JSON_OUTPUT_PATH, "wb") as f:
        f.write(json.dumps(report, indent=2, sort_keys=True).encode("utf-8"))
except Exception:
    json_write_ok = False

summary_lines = []
summary_lines.append("SFM CHECKPOINT C2 -- INTEGRATED (POST-INTEGRATION) SELECTED-SHOTS RUN")
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
if report.get("gate_failure"):
    summary_lines.append("")
    summary_lines.append("*** GATE FAILURE: aborted BEFORE any production Normalizer invocation or scene mutation. ***")
    summary_lines.append("*** No mutation occurred. See the FAIL line(s) below for exactly which fixture, ***")
    summary_lines.append("*** C1-artifact-integrity, or starting-state condition did not hold. ***")
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
summary_lines.append("--- COMPARISONS A-F ---")
for comp_name in ("A_starting_state_parity", "B_scope_parity", "C_final_state_parity", "D_per_target_parity", "E_untouched_peer_parity", "F_selected_target_parity"):
    comp_val = report["comparisons"].get(comp_name)
    summary_lines.append("[%s] %s" % ("PASS" if (comp_val and comp_val.get("pass")) else "FAIL/MISSING", comp_name))
summary_lines.append("")
summary_lines.append("run_started=%r  run_completed_cleanly=%r" % (run_started, run_completed_cleanly))
summary_lines.append("integrated_pre_fingerprint_hash=%r" % report.get("integrated_pre_fingerprint_hash"))
summary_lines.append("integrated_post_fingerprint_hash=%r" % report.get("integrated_post_fingerprint_hash"))
summary_lines.append("c1_pre_fingerprint_hash(expected)=%r" % EXPECTED_C1_PRE_HASH)
summary_lines.append("c1_post_fingerprint_hash(expected)=%r" % EXPECTED_C1_POST_HASH)
summary_lines.append("touched_targets=%r" % report.get("touched_targets"))
summary_lines.append("")
summary_lines.append("--- AUTHORITY RUNTIME EVIDENCE ---")
for k in sorted(report["authority_runtime_evidence"].keys()):
    summary_lines.append("  %s = %r" % (k, report["authority_runtime_evidence"][k]))
summary_lines.append("")
summary_lines.append("--- NATIVE PROTECTION EVIDENCE ---")
for k in sorted(report["native_protection_evidence"].keys()):
    summary_lines.append("  %s = %r" % (k, report["native_protection_evidence"][k]))
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
        "\nCheckpoint C2 reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok)
    )
    sys.stdout.write("\nDO NOT SAVE. Restart SFM to discard this integrated-run mutation.\n")
except Exception:
    pass
