# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint D2: Integrated (post-
integration) All-Shots equivalence run.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: **THIS CHECKPOINT MUTATES THE SCENE.** It invokes the
REAL, INSTALLED, ACCEPTED, INTEGRATED production Normalizer -- never a
copy, never the historical baseline D1 used -- against the same
disposable fixture, running its own real All Shots behavior. Do not
save afterward.

D2-2 CORRECTION (2026-09-22): D2-1's real run proved full runtime/
equivalence PASS -- all 44 mechanical checks, all six comparisons, a
clean authority lifecycle, and native-protection evidence all passed,
with zero anomalies. But the QUALIFICATION ARTIFACT itself failed:
`write_json_atomic()`'s own reopen/reparse verification step raised
`MemoryError()` while the SFM process was already at ~3.43GB working
set -- the artifact was attempting to persist a full ~9MB duplicate
copy of D2's own 85+85 raw captured fingerprints (on top of the
identically-sized copy already resident in memory) purely to prove
equivalence to D1, whose own already-qualified per-target hashing
algorithm makes that duplication unnecessary. This revision:
  (a) NEVER persists D2's own raw 85-target PRE/POST fingerprint dicts
      (or the 78-target excluded witness rows) into the artifact --
      only their already-computed per-target HASHES (the same
      qualified `per_target_hash()` D1's own compact manifest uses),
      reducing the artifact from ~9MB to tens of KB;
  (b) adds a `hash_of_hashes()` checksum so round-trip (serialize-then-
      reparse) fidelity of the STORED per-target hash maps can still be
      independently verified without ever needing the raw fingerprint
      content present at verification time;
  (c) if (and only if) a per-target mismatch is ever found, preserves
      the raw semantic fingerprint for JUST the mismatching target(s)
      as diagnostic evidence -- the common (all-match) case stays
      compact; a genuine divergence still carries enough raw evidence
      to diagnose;
  (d) fixes a real semantic defect in the prior degraded-fallback path:
      `degraded_report = dict(report)` could snapshot `report["overall_
      pass"]` BEFORE the later `report["overall_pass"] = False`
      correction ran, so a degraded artifact could be written to disk
      still claiming `overall_pass: true` even though the authoritative
      summary correctly said `False`. The degraded path now explicitly
      forces `overall_pass`/`artifact_write_verified` to `False`,
      independent of whatever the live `report` object held at
      snapshot time;
  (e) adds a `provenance` section and per-command timing, per the
      governing brief's explicit compact-artifact field list.
Historical Normalizer invocation, fingerprint semantics, fixture/
starting-state gates, runtime comparison logic, and native-protection
logic are otherwise byte-identical to D2-1 -- this is an evidence-
persistence correction only.

Purpose:
  Mechanically prove the integrated (post-Production-Normalizer-
  Integration) All-Shots outcome is semantically equivalent to
  Checkpoint D1-3's own already-accepted historical baseline outcome --
  the same role Checkpoint C2 played for Selected Shots vs C1. Unlike
  C2, this checkpoint never loads Checkpoint D1's own full ~5.9MB JSON
  artifact into memory: D1-3 itself demonstrated this 32-bit
  qualification-harness process approaching its memory ceiling, so D2
  compares against a compact, immutable, SHA-256-pinned manifest
  (~40KB, containing only per-target HASHES, never D1's raw captured
  fingerprint data) built offline from the real D1-3 artifact by
  `real_sfm_qualification/checkpoint_d2/build_d1_manifest.py`. D2's OWN
  output artifact follows the identical discipline (D2-2 correction,
  above): compact per-target hashes, never raw fingerprint duplication.

  This script:
    1. verifies the installed production Normalizer's own SHA-256 (the
       file this checkpoint is about to execute, exactly as C2 did);
    2. verifies the canonical Master's SHA-256;
    3. loads and integrity-verifies the compact D1 comparison manifest
       (SHA-256 pinned) -- never `json.load()`s D1's own full artifact;
       optionally, if present, verifies that full D1 artifact's own
       identity via a STREAMING SHA-256 (constant memory, the file is
       never parsed) as additional provenance, without hard-gating on
       its continued physical presence;
    4. independently re-derives the Checkpoint-B-style fixture witness
       fresh from the live document and cross-checks it against fixed
       structural totals AND the manifest's own eligible/excluded
       target key sets;
    5. captures a structural PRE fingerprint of all 85 eligible targets
       and a lightweight structural witness of all 78 excluded targets
       (same technique D1 used), computing per-target HASHES via the
       same streaming `stable_hash()`/canonical `per_target_hash()`
       D1-3 introduced;
    6. HARD GATES on: every fixture-identity check, the integrated PRE
       aggregate hash matching D1's own PRE hash exactly, all 85
       integrated PRE per-target hashes matching the D1 manifest, and
       all 78 excluded PRE witness hashes matching the D1 manifest --
       aborting BEFORE any invocation of the production Normalizer or
       scene mutation if the live starting state does not match;
    7. only if the full gate passes, executes the installed production
       Normalizer's own real source in an isolated namespace -- this
       triggers the Normalizer's own real, unmodified, interactive
       Clip-Editor scope-choice dialog; the operator must select **All
       Shots** and confirm;
    8. waits (pumping the real Qt event loop, polling the Normalizer's
       own run-lock object) for that real, asynchronous operation to
       finish;
    9. rebuilds the independent witness fresh (to detect any target
       that vanished, appeared, or was reclassified as a side effect
       of the integrated All-Shots run);
   10. captures the same structural POST fingerprint/excluded witness
       for the same targets;
   11. performs six required comparisons (A-F, see below) between this
       run's own hashes and the D1 manifest's own hashes, per target,
       never relying on aggregate hashes alone;
   12. captures shared-authority runtime evidence and native-protection
       log evidence, the same existing-qualified-diagnostics technique
       Checkpoint C2 used;
   13. writes a complete but COMPACT machine-readable result artifact:
       per-target hashes (never raw fingerprints, except for any
       mismatching target), comparisons, provenance, and runtime
       evidence.

Comparisons performed (see report["comparisons"] for the machine-
readable results of each):
  A. starting_state_parity   -- integrated PRE aggregate hash == D1 PRE
                                 hash, AND 85/85 individual PRE target
                                 hashes match the D1 manifest (also
                                 part of the hard gate, before mutation)
  B. scope_parity            -- integrated changed-target set exactly
                                 equals D1's 57-target changed set;
                                 integrated unchanged-target set exactly
                                 equals D1's 28-target unchanged set --
                                 full SET equality, never just counts
  C. final_state_parity      -- integrated POST aggregate hash == D1's
                                 own historical POST hash
  D. per_target_parity       -- ALL 85 eligible targets' POST hashes
                                 compared individually against the D1
                                 manifest's own per-target POST hashes
  E. exclusion_parity        -- ALL 78 excluded targets' structural
                                 witness hashes compared individually
                                 against the D1 manifest's own excluded
                                 POST hashes; expected changed set: []
  F. target_set_parity       -- no missing/new/reclassified targets
                                 (independently rebuilt witness vs the
                                 D1 manifest's own eligible/excluded key
                                 sets)

If ANY per-target mismatch occurs (Comparison D or E, or the PRE-side
starting-state gate), the raw semantic fingerprint for JUST the
mismatching target(s) is preserved in `report["mismatch_diagnostics"]`
as diagnostic evidence -- this script never builds a bulk in-process
structural diff object across all targets; when every target matches
(the expected, qualified case), this section stays empty and the
artifact stays compact.

This script never modifies the historical baseline, the production
Normalizer, the canonical Master (other than the read-only SHA-256
check), or `sfm_master_authority_productionized`/`sfm_master_sidecar`
except by reading the module bindings the production Normalizer's own
source already imports.

Output:
  Two files are written to C:\\Users\\Public\\Documents\\:
    sfm_checkpoint_d2_integrated_all_shots_result.json          (machine-readable, compact)
    sfm_checkpoint_d2_integrated_all_shots_result_summary.txt   (concise human-readable)
  A short summary is also printed to SFM's own console/output.

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

# Ground-truthed directly from the real, accepted Checkpoint D1-3
# artifact and its offline-built compact manifest (not retyped from a
# conversation transcript) -- see build_d1_manifest.py.
EXPECTED_D1_ARTIFACT_SHA256 = (
    "55cd0447f3d215afaa4fa334b1daf2d905055363972ead524672da822ed6e85f"
)
EXPECTED_D1_MANIFEST_SHA256 = (
    "64917b46896ced079bfc68e777d7e7c250e3875230a477ece1cb9320b0d4e42f"
)
EXPECTED_PRE_HASH = (
    "eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0"
)
EXPECTED_POST_HASH = (
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

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_d2_integrated_all_shots_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_d2_integrated_all_shots_result_summary.txt"
D1_ARTIFACT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_d1_historical_all_shots_result.json"

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
D1_MANIFEST_PATH = os.path.join(
    os.path.dirname(os.path.abspath(sys.executable)),
    "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
    "_qualification_manifests", "d1_comparison_manifest.json",
)

# 1-indexed, inclusive. IDENTICAL range table to Checkpoints C1/C2/D1's
# own (same reasoning: pure, read-only, structural DME-reading
# functions, never scope/eligibility POLICY, extracted from THIS run's
# own production Normalizer file, SHA-pinned above).
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


class CheckpointD2Error(Exception):
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
# used by Checkpoints C1/C2/D1, kept verbatim for internal consistency
# between checkpoints' witnesses).
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
                raise CheckpointD2Error(
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
    """Streaming implementation (Checkpoint D1-3's own correction,
    reused verbatim): feeds hashlib.sha256() incrementally instead of
    building one giant joined Unicode string and then a second giant
    encoded byte string. Proven byte-for-byte digest-equivalent to the
    prior two-giant-copies implementation."""
    hasher = hashlib.sha256()
    for index, item in enumerate(sorted(values)):
        if index:
            hasher.update(b"\n")
        hasher.update(item.encode("utf-8"))
    return hasher.hexdigest()


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


def target_key(t):
    return u"%s|%s" % (t["shot_name"], t["aset_name"])


def excluded_witness_row(t):
    """Lightweight, non-mutating STRUCTURAL witness for an excluded
    target -- identical to Checkpoint D1's own excluded_witness_row(),
    deliberately never routed through capture_snapshot_explicit()."""
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
    """Canonical per-target hash: SHA-256 of the target's own
    sort_keys=True JSON serialization -- the exact function
    `real_sfm_qualification/checkpoint_d2/build_d1_manifest.py` used to
    build the D1 comparison manifest's own per-target hashes. Reusing
    the identical function here is what makes the two sides of every
    per-target comparison actually comparable."""
    return hashlib.sha256(dumps_sorted(value).encode("utf-8")).hexdigest()


def compute_target_hashes(fingerprint_dict):
    """Given a captured {target_key: canonicalized_value} mapping,
    returns {target_key: per_target_hash(value)} -- the caller releases
    the raw dicts once these hashes (the D2-2-qualified compact
    evidence) are computed; D2 never needs to hold D1's raw dicts at
    all, only the manifest's own precomputed hashes."""
    return dict((k, per_target_hash(v)) for k, v in fingerprint_dict.items())


def hash_of_hashes(hash_dict):
    """Independent-audit correction, D2-2: a round-trip-verifiable
    checksum over a {target_key: per_target_hash} MAP -- distinct from
    the semantic aggregate hash (which is computed once, in memory,
    from the raw target CONTENT, before that content is ever
    discarded). This lets `verify_artifact_evidence()` confirm the
    STORED per-target hash maps survived JSON serialization/reparse
    intact, without ever needing D2's own raw captured fingerprint
    dicts to be present at verification time -- exactly the design
    that keeps the compact artifact's own write+verify step cheap."""
    return stable_hash([u"%s=%s" % (k, v) for k, v in hash_dict.items()])


def compare_hash_maps(actual_hashes, expected_hashes):
    """Returns (matching_keys, mismatching_keys, missing_in_actual,
    missing_in_expected) -- all sorted lists of target keys (small
    strings), never a bulk structural diff object."""
    actual_keys = set(actual_hashes.keys())
    expected_keys = set(expected_hashes.keys())
    missing_in_actual = sorted(expected_keys - actual_keys)
    missing_in_expected = sorted(actual_keys - expected_keys)
    common = actual_keys & expected_keys
    matching = sorted(k for k in common if actual_hashes[k] == expected_hashes[k])
    mismatching = sorted(k for k in common if actual_hashes[k] != expected_hashes[k])
    return matching, mismatching, missing_in_actual, missing_in_expected


def stream_file_sha256(path, chunk_size=1048576):
    """Streaming SHA-256 of a file -- reads in fixed-size chunks, never
    holding the whole file (or a decoded copy of it) in memory at once.
    Used ONLY to verify the D1 artifact's own on-disk identity as
    optional additional provenance; the file's content is never parsed
    here."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def memory_snapshot():
    """Best-effort, stdlib-only (ctypes) Windows process memory
    snapshot -- diagnostic only, never affects Normalizer behavior, and
    never raises. Identical to Checkpoint D1-3's own memory_snapshot()."""
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


# ---------------------------------------------------------------------------
# Safe, streaming, compact artifact writer (Checkpoint D1-3's own
# correction, reused verbatim). Never truncates the final authoritative
# path until the write itself, and an independent reopen+reparse of a
# separate temp file, have both already succeeded. On any write-phase
# failure, the temp file is cleaned up; on a final-promote failure, the
# temp file is deliberately left in place as the only surviving copy of
# an already-verified payload.
# ---------------------------------------------------------------------------

def write_json_atomic(final_path, data_obj):
    """Returns (ok, error_repr_or_None, reparsed_obj_or_None).
    Python-2.7-compatible. Streams via json.dump() -- never builds one
    giant in-memory serialized string -- compact (no indent, no
    whole-document sort_keys)."""
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
    """Same discipline as write_json_atomic(), for the plain-text
    summary file. Returns (ok, error_repr_or_None)."""
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


# Independent-audit correction, D2-2: REQUIRED_EVIDENCE_KEYS and
# verify_artifact_evidence() now operate purely on the COMPACT per-
# target hash maps (never raw fingerprint dicts) -- see the module
# docstring's D2-2 correction notice for the full reasoning.
REQUIRED_EVIDENCE_KEYS = (
    "integrated_pre_fingerprint_hash", "integrated_post_fingerprint_hash",
    "eligible_pre_target_hashes", "eligible_post_target_hashes",
    "excluded_pre_target_hashes", "excluded_post_target_hashes",
    "changed_target_keys", "unchanged_target_keys",
    "eligible_pre_hashes_checksum", "eligible_post_hashes_checksum",
    "excluded_pre_hashes_checksum", "excluded_post_hashes_checksum",
    "comparisons",
)


def verify_artifact_evidence(reparsed_obj):
    """Returns (ok, detail). Checks presence/completeness of the
    required COMPACT evidence fields AND that the stored per-target
    hash maps recompute a matching `hash_of_hashes()` checksum after
    JSON round-trip -- proving serialization/reparse fidelity of the
    stored HASH data without ever needing D2's own raw captured
    fingerprint content to be present at verification time."""
    if reparsed_obj is None:
        return False, "reparsed artifact is None"
    missing_keys = [k for k in REQUIRED_EVIDENCE_KEYS if k not in reparsed_obj]
    if missing_keys:
        return False, "missing required evidence keys: %r" % (missing_keys,)
    eligible_pre = reparsed_obj.get("eligible_pre_target_hashes") or {}
    eligible_post = reparsed_obj.get("eligible_post_target_hashes") or {}
    excluded_pre = reparsed_obj.get("excluded_pre_target_hashes") or {}
    excluded_post = reparsed_obj.get("excluded_post_target_hashes") or {}
    if len(eligible_pre) != 85 or len(eligible_post) != 85:
        return False, "stored eligible per-target hash counts wrong: pre=%d post=%d" % (len(eligible_pre), len(eligible_post))
    if len(excluded_pre) != 78 or len(excluded_post) != 78:
        return False, "stored excluded per-target hash counts wrong: pre=%d post=%d" % (len(excluded_pre), len(excluded_post))
    changed = reparsed_obj.get("changed_target_keys") or []
    unchanged = reparsed_obj.get("unchanged_target_keys") or []
    if len(changed) != 57 or len(unchanged) != 28:
        return False, "stored changed/unchanged target-set counts wrong: changed=%d unchanged=%d" % (len(changed), len(unchanged))
    recomputed_eligible_pre_checksum = hash_of_hashes(eligible_pre)
    recomputed_eligible_post_checksum = hash_of_hashes(eligible_post)
    recomputed_excluded_pre_checksum = hash_of_hashes(excluded_pre)
    recomputed_excluded_post_checksum = hash_of_hashes(excluded_post)
    if recomputed_eligible_pre_checksum != reparsed_obj.get("eligible_pre_hashes_checksum"):
        return False, "recomputed eligible PRE hashes-checksum %r != stored %r" % (recomputed_eligible_pre_checksum, reparsed_obj.get("eligible_pre_hashes_checksum"))
    if recomputed_eligible_post_checksum != reparsed_obj.get("eligible_post_hashes_checksum"):
        return False, "recomputed eligible POST hashes-checksum %r != stored %r" % (recomputed_eligible_post_checksum, reparsed_obj.get("eligible_post_hashes_checksum"))
    if recomputed_excluded_pre_checksum != reparsed_obj.get("excluded_pre_hashes_checksum"):
        return False, "recomputed excluded PRE hashes-checksum %r != stored %r" % (recomputed_excluded_pre_checksum, reparsed_obj.get("excluded_pre_hashes_checksum"))
    if recomputed_excluded_post_checksum != reparsed_obj.get("excluded_post_hashes_checksum"):
        return False, "recomputed excluded POST hashes-checksum %r != stored %r" % (recomputed_excluded_post_checksum, reparsed_obj.get("excluded_post_hashes_checksum"))
    return True, None


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
    "memory_snapshots": {},
    "provenance": {},
    "mismatch_diagnostics": {"eligible": {}, "excluded": {}},
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
pre_witness = None
post_witness = None

try:
    report["memory_snapshots"]["at_start"] = memory_snapshot()

    # --- 1. SHA verification of the file this checkpoint is ABOUT TO
    #        EXECUTE. ---
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
        raise CheckpointD2Error("One or more pre-flight SHA-256 checks failed -- refusing to proceed.")

    report["provenance"]["production_normalizer_sha256"] = production_sha
    report["provenance"]["canonical_master_sha256"] = master_sha
    report["provenance"]["d1_artifact_sha256_expected"] = EXPECTED_D1_ARTIFACT_SHA256
    report["provenance"]["d1_manifest_sha256_expected"] = EXPECTED_D1_MANIFEST_SHA256

    # --- 2. Load and integrity-verify the COMPACT D1 comparison
    #        manifest -- never json.load() D1's own full ~5.9MB
    #        artifact. ---
    try:
        with open(D1_MANIFEST_PATH, "rb") as f:
            manifest_bytes = f.read()
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    except Exception as exc:
        raise CheckpointD2Error("Could not read D1 comparison manifest at %r: %r" % (D1_MANIFEST_PATH, exc))
    check("d1_manifest.sha256_matches_pinned", manifest_sha256 == EXPECTED_D1_MANIFEST_SHA256, manifest_sha256)
    if manifest_sha256 != EXPECTED_D1_MANIFEST_SHA256:
        raise CheckpointD2Error("D1 comparison manifest SHA-256 mismatch -- refusing to trust a stale/tampered manifest.")

    manifest = json.loads(manifest_bytes.decode("utf-8"))
    del manifest_bytes
    check("d1_manifest.d1_overall_pass_was_true", manifest.get("d1_overall_pass") is True, manifest.get("d1_overall_pass"))
    check("d1_manifest.d1_pre_hash_matches_pinned", manifest.get("d1_pre_fingerprint_hash") == EXPECTED_PRE_HASH, manifest.get("d1_pre_fingerprint_hash"))
    check("d1_manifest.d1_post_hash_matches_pinned", manifest.get("d1_post_fingerprint_hash") == EXPECTED_POST_HASH, manifest.get("d1_post_fingerprint_hash"))
    check("d1_manifest.eligible_target_keys_count_is_85", len(manifest.get("eligible_target_keys") or []) == 85, len(manifest.get("eligible_target_keys") or []))
    check("d1_manifest.excluded_target_keys_count_is_78", len(manifest.get("excluded_target_keys") or []) == 78, len(manifest.get("excluded_target_keys") or []))
    check("d1_manifest.changed_target_keys_count_is_57", len(manifest.get("changed_target_keys") or []) == 57, len(manifest.get("changed_target_keys") or []))
    check("d1_manifest.unchanged_target_keys_count_is_28", len(manifest.get("unchanged_target_keys") or []) == 28, len(manifest.get("unchanged_target_keys") or []))
    check("d1_manifest.excluded_changed_target_keys_is_empty", manifest.get("excluded_changed_target_keys") == [], manifest.get("excluded_changed_target_keys"))

    # --- 3. OPTIONAL additional provenance: if the full D1 artifact is
    #        still physically present, verify its identity via a
    #        STREAMING SHA-256 (constant memory; the file's content is
    #        never parsed here). Its continued physical presence is not
    #        itself required -- the pinned, self-contained manifest is
    #        the load-bearing gate -- so this is recorded as evidence,
    #        not hard-gated. ---
    d1_artifact_evidence = {}
    if os.path.exists(D1_ARTIFACT_PATH):
        try:
            streamed_sha = stream_file_sha256(D1_ARTIFACT_PATH)
            d1_artifact_evidence["present"] = True
            d1_artifact_evidence["streamed_sha256"] = streamed_sha
            d1_artifact_evidence["matches_pinned"] = bool(streamed_sha == EXPECTED_D1_ARTIFACT_SHA256)
            check("d1_artifact.present_and_streamed_sha256_matches_pinned", d1_artifact_evidence["matches_pinned"], streamed_sha)
        except Exception as exc:
            d1_artifact_evidence["present"] = True
            d1_artifact_evidence["stream_hash_error"] = repr(exc)
            anomaly("D1 artifact present but streaming SHA-256 failed: %r" % exc)
    else:
        d1_artifact_evidence["present"] = False
        d1_artifact_evidence["note"] = "D1 artifact not physically present at this path; not required (the pinned manifest is self-contained)."
    report["d1_artifact_provenance"] = d1_artifact_evidence

    # --- 4. Fixture/structural-totals verification, cross-checked
    #        against the D1 manifest's own key sets. ---
    pre_witness, shots_by_name, witness_error = build_independent_witness()
    if witness_error is not None:
        raise CheckpointD2Error("Could not build independent witness: %s" % witness_error)

    report["fixture_totals"] = pre_witness["totals"]
    for key, expected_value in EXPECTED_TOTALS.items():
        actual_value = pre_witness["totals"].get(key)
        check("fixture.totals.%s_matches_required" % key, actual_value == expected_value, (actual_value, expected_value))

    selected_shot_names_evidence = sorted(set(t["shot_name"] for t in pre_witness["targets"] if t["shot_selected"]))
    report["selection_state_evidence"] = {
        "selected_shot_names": selected_shot_names_evidence,
        "note": "All-Shots scope does not depend on this; recorded for evidence only, not gated.",
    }

    pre_eligible_rows = [t for t in pre_witness["targets"] if t["category"] != "excluded"]
    pre_excluded_rows = [t for t in pre_witness["targets"] if t["category"] == "excluded"]
    check("fixture.eligible_row_count_is_85", len(pre_eligible_rows) == 85, len(pre_eligible_rows))
    check("fixture.excluded_row_count_is_78", len(pre_excluded_rows) == 78, len(pre_excluded_rows))

    eligible_targets_of_interest = [(t["shot_name"], t["aset_name"]) for t in pre_eligible_rows]
    pre_eligible_keys = set(target_key(t) for t in pre_eligible_rows)
    pre_excluded_keys = set(target_key(t) for t in pre_excluded_rows)
    del pre_eligible_rows

    check("fixture.eligible_key_set_matches_d1_manifest", pre_eligible_keys == set(manifest["eligible_target_keys"]),
          sorted(pre_eligible_keys ^ set(manifest["eligible_target_keys"])))
    check("fixture.excluded_key_set_matches_d1_manifest", pre_excluded_keys == set(manifest["excluded_target_keys"]),
          sorted(pre_excluded_keys ^ set(manifest["excluded_target_keys"])))

    # --- 5. Build the fingerprint-function namespace (extracted, SHA-
    #        pinned to the SAME file this checkpoint is about to
    #        execute). ---
    all_lines = production_bytes.decode("ascii").splitlines()
    blocks = []
    for label, start, end in FINGERPRINT_FUNCTION_RANGES:
        blocks.append("\n".join(all_lines[start - 1:end]))
    combined_source = "\n\n".join(blocks)

    fp_ns = dict(FINGERPRINT_MODULE_CONSTANTS)
    fp_ns["hashlib"] = hashlib
    exec(compile(combined_source, "<checkpoint_d2_fingerprint_functions>", "exec"), fp_ns)
    check("fingerprint_functions.extracted_and_exec_ok", True)

    capture_snapshot_explicit_fn = fp_ns["capture_snapshot_explicit"]

    # Release the raw source text now that the functions are extracted
    # (D1-3's own memory-hygiene discipline).
    del all_lines, blocks, combined_source

    def canonicalize_snapshot(snap):
        """Identical to Checkpoints C1/C2/D1's own canonicalize_snapshot:
        strips process-local handle integers and the PRE/POST `label`
        field before any equality/hash comparison."""
        clean = dict(snap)
        for key in ("shot_handle", "animation_set_handle", "root_handle", "rig_handle", "registry_handle", "label"):
            clean.pop(key, None)
        clean.pop("control_handles", None)
        return clean

    def capture_all(label, targets_of_interest_local):
        """targets_of_interest_local: list of (shot_name, aset_name)
        pairs to re-resolve fresh from the live document."""
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

    # --- 6. Integrated PRE fingerprint (non-mutating, all 85 targets)
    #        + excluded PRE structural witness (78 targets). D2-2:
    #        the raw dicts stay LOCAL only, long enough to compute
    #        their aggregate/per-target hashes (and, if a mismatch is
    #        ever found, to populate mismatch_diagnostics for those
    #        specific keys) -- never persisted into the artifact. ---
    report["memory_snapshots"]["before_pre_capture"] = memory_snapshot()
    integrated_pre_fingerprint = capture_all("PRE", eligible_targets_of_interest)
    check("fingerprint.pre_capture_count_matches_expected", len(integrated_pre_fingerprint) == 85, len(integrated_pre_fingerprint))
    report["memory_snapshots"]["after_pre_capture"] = memory_snapshot()

    integrated_pre_hash = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in integrated_pre_fingerprint.items()])
    report["integrated_pre_fingerprint_hash"] = integrated_pre_hash
    integrated_pre_target_hashes = compute_target_hashes(integrated_pre_fingerprint)
    report["eligible_pre_target_hashes"] = integrated_pre_target_hashes
    report["eligible_pre_hashes_checksum"] = hash_of_hashes(integrated_pre_target_hashes)
    pre_approx_serialized_bytes = sum(len(dumps_sorted(v)) for v in integrated_pre_fingerprint.values())

    pre_excluded_witness = dict((target_key(t), excluded_witness_row(t)) for t in pre_excluded_rows)
    del pre_excluded_rows
    integrated_excluded_pre_hashes = compute_target_hashes(pre_excluded_witness)
    report["excluded_pre_target_hashes"] = integrated_excluded_pre_hashes
    report["excluded_pre_hashes_checksum"] = hash_of_hashes(integrated_excluded_pre_hashes)

    # --- Comparison A (starting-state parity) -- also part of the hard
    #     gate: a mismatch here means the live state does not match D1,
    #     and this script must abort BEFORE invoking the production
    #     Normalizer. ---
    check("gate.integrated_pre_hash_matches_d1_pre_hash", integrated_pre_hash == EXPECTED_PRE_HASH, integrated_pre_hash)

    pre_matching, pre_mismatching, pre_missing_actual, pre_missing_expected = compare_hash_maps(
        integrated_pre_target_hashes, manifest["eligible_pre_target_hashes"]
    )
    check("gate.all_85_pre_target_hashes_match_d1_manifest",
          len(pre_mismatching) == 0 and len(pre_missing_actual) == 0 and len(pre_missing_expected) == 0,
          {"mismatching": pre_mismatching, "missing_in_actual": pre_missing_actual, "missing_in_expected": pre_missing_expected})

    excluded_pre_matching, excluded_pre_mismatching, excluded_pre_missing_actual, excluded_pre_missing_expected = compare_hash_maps(
        integrated_excluded_pre_hashes, manifest["excluded_pre_target_hashes"]
    )
    check("gate.all_78_excluded_pre_hashes_match_d1_manifest",
          len(excluded_pre_mismatching) == 0 and len(excluded_pre_missing_actual) == 0 and len(excluded_pre_missing_expected) == 0,
          {"mismatching": excluded_pre_mismatching, "missing_in_actual": excluded_pre_missing_actual, "missing_in_expected": excluded_pre_missing_expected})

    # D2-2: preserve raw diagnostic evidence for any PRE-side mismatch
    # BEFORE the raw dicts are released -- this is the one case where
    # the starting-state gate itself is about to abort the run.
    for _key in pre_mismatching:
        report["mismatch_diagnostics"]["eligible"][_key] = {
            "integrated_pre": integrated_pre_fingerprint.get(_key),
            "note": "PRE-state mismatch detected before mutation (starting-state gate).",
        }
    for _key in excluded_pre_mismatching:
        report["mismatch_diagnostics"]["excluded"][_key] = {
            "integrated_pre": pre_excluded_witness.get(_key),
            "note": "PRE-state mismatch detected before mutation (starting-state gate).",
        }

    # --- HARD GATE: every check recorded above must pass BEFORE any
    #     invocation of the production Normalizer or scene mutation. ---
    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointD2Error(
            "STARTING-STATE / FIXTURE MISMATCH -- one or more required pre-flight, "
            "D1-manifest-integrity, fixture-identity, or starting-state-parity checks "
            "failed. Aborting BEFORE any invocation of the production Normalizer or "
            "scene mutation. Restart SFM and re-open the original disposable fixture "
            "without saving any prior checkpoint's mutation before rerunning."
        )

    # D2-2: the raw PRE fingerprint/excluded-witness dicts are no longer
    # needed -- their aggregate/per-target hashes are already computed
    # and stored, and any PRE-side mismatch diagnostics (there are none,
    # since the gate above just passed) have already been captured.
    # Release them now, before the memory-heavier integrated run.
    del integrated_pre_fingerprint, pre_excluded_witness

    # Release the full 163-target witness now that its only remaining
    # downstream use (the key-set diff) can be served by the cheap
    # key sets already extracted above (D1-3's own memory-hygiene
    # discipline).
    pre_all_target_keys = set(target_key(t) for t in pre_witness["targets"])
    del pre_witness

    # --- 7. Invoke the REAL installed, accepted, integrated production
    #        Normalizer. ---
    main_window = sfmApp.GetMainWindow()
    check("normalizer.main_window_available", main_window is not None)

    sys.stdout.write(
        "\n>>> The integrated production Normalizer is about to run its own real "
        "Selected/All Shots dialog. Select 'All Shots' and confirm. <<<\n\n"
    )

    command_start_time = time.time()
    prod_ns = {}
    run_started = False
    try:
        # Raw, undecoded bytes -- the file's own line-1
        # "# -*- coding: ascii -*-" declaration makes compile() raise
        # if a decoded unicode string is passed instead (same class of
        # bug already hit and fixed in Checkpoint C2).
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

    report["command_duration_seconds"] = time.time() - command_start_time

    check("normalizer.run_was_started", run_started)
    check("normalizer.run_completed_within_timeout", run_completed_cleanly if run_started else False)
    report["memory_snapshots"]["after_integrated_run"] = memory_snapshot()

    # --- 8. Rebuild the independent witness fresh, to detect any
    #        target that vanished, appeared, or was reclassified as a
    #        side effect of the integrated All-Shots run. ---
    post_witness, post_shots_by_name, post_witness_error = build_independent_witness()
    if post_witness_error is not None:
        anomaly("Could not rebuild post-run independent witness: %s" % post_witness_error)
        post_all_by_key = {}
    else:
        post_all_by_key = dict((target_key(t), t) for t in post_witness["targets"])
    del post_witness

    post_eligible_keys = set(k for k, t in post_all_by_key.items() if t["category"] != "excluded")
    post_excluded_keys = set(k for k, t in post_all_by_key.items() if t["category"] == "excluded")

    missing_targets_entirely = sorted(pre_all_target_keys - set(post_all_by_key.keys()))
    new_targets_entirely = sorted(set(post_all_by_key.keys()) - pre_all_target_keys)
    reclassified_eligible_to_excluded = sorted(pre_eligible_keys & post_excluded_keys)
    reclassified_excluded_to_eligible = sorted(pre_excluded_keys & post_eligible_keys)

    target_set_diff = {
        "missing_targets_entirely": missing_targets_entirely,
        "new_targets_entirely": new_targets_entirely,
        "reclassified_eligible_to_excluded": reclassified_eligible_to_excluded,
        "reclassified_excluded_to_eligible": reclassified_excluded_to_eligible,
    }
    report["target_set_diff"] = target_set_diff

    # --- Comparison F: target-set parity. ---
    comp_f = {
        "target_set_diff": target_set_diff,
        "pass": bool(
            len(missing_targets_entirely) == 0 and len(new_targets_entirely) == 0
            and len(reclassified_eligible_to_excluded) == 0 and len(reclassified_excluded_to_eligible) == 0
        ),
    }
    report["comparisons"]["F_target_set_parity"] = comp_f
    check("comparison.F_target_set_parity", comp_f["pass"], target_set_diff)

    # --- 9. Integrated POST fingerprint (85 targets) + excluded POST
    #        structural witness (78 targets). Same D2-2 discipline:
    #        raw dicts stay local only long enough to compute hashes
    #        and any mismatch diagnostics. ---
    report["memory_snapshots"]["before_post_capture"] = memory_snapshot()
    integrated_post_fingerprint = capture_all("POST", eligible_targets_of_interest)
    check("fingerprint.post_capture_count_matches_expected", len(integrated_post_fingerprint) == 85, len(integrated_post_fingerprint))
    report["memory_snapshots"]["after_post_capture"] = memory_snapshot()

    # fp_ns/capture_snapshot_explicit_fn are not referenced again after
    # this, the last capture_all() call -- safe to release now.
    del fp_ns, capture_snapshot_explicit_fn

    integrated_post_hash = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in integrated_post_fingerprint.items()])
    report["integrated_post_fingerprint_hash"] = integrated_post_hash
    integrated_post_target_hashes = compute_target_hashes(integrated_post_fingerprint)
    report["eligible_post_target_hashes"] = integrated_post_target_hashes
    report["eligible_post_hashes_checksum"] = hash_of_hashes(integrated_post_target_hashes)
    post_approx_serialized_bytes = sum(len(dumps_sorted(v)) for v in integrated_post_fingerprint.values())
    report["memory_snapshots"]["after_post_hash"] = memory_snapshot()

    post_excluded_witness = {}
    for key in sorted(pre_excluded_keys):
        t = post_all_by_key.get(key)
        if t is None:
            continue
        post_excluded_witness[key] = excluded_witness_row(t)
    del post_all_by_key
    integrated_excluded_post_hashes = compute_target_hashes(post_excluded_witness)
    report["excluded_post_target_hashes"] = integrated_excluded_post_hashes
    report["excluded_post_hashes_checksum"] = hash_of_hashes(integrated_excluded_post_hashes)

    # ------------------------------------------------------------------
    # Comparison A: starting-state parity (recap; already gated above).
    # ------------------------------------------------------------------
    report["comparisons"]["A_starting_state_parity"] = {
        "integrated_pre_hash": integrated_pre_hash,
        "d1_pre_hash": EXPECTED_PRE_HASH,
        "pre_target_mismatching": pre_mismatching,
        "pass": bool(integrated_pre_hash == EXPECTED_PRE_HASH and len(pre_mismatching) == 0
                     and len(pre_missing_actual) == 0 and len(pre_missing_expected) == 0),
    }

    # ------------------------------------------------------------------
    # Comparison B: scope/result classification parity -- exact SET
    # equality, never just counts.
    # ------------------------------------------------------------------
    integrated_changed_keys = sorted(
        k for k in integrated_pre_target_hashes
        if integrated_pre_target_hashes[k] != integrated_post_target_hashes.get(k)
    )
    integrated_unchanged_keys = sorted(
        k for k in integrated_pre_target_hashes
        if integrated_pre_target_hashes[k] == integrated_post_target_hashes.get(k)
    )
    report["changed_target_keys"] = integrated_changed_keys
    report["unchanged_target_keys"] = integrated_unchanged_keys
    d1_changed_keys = sorted(manifest["changed_target_keys"])
    d1_unchanged_keys = sorted(manifest["unchanged_target_keys"])
    comp_b = {
        "integrated_changed_count": len(integrated_changed_keys),
        "integrated_unchanged_count": len(integrated_unchanged_keys),
        "changed_set_matches_d1_exactly": bool(integrated_changed_keys == d1_changed_keys),
        "unchanged_set_matches_d1_exactly": bool(integrated_unchanged_keys == d1_unchanged_keys),
        "changed_set_symmetric_difference": sorted(set(integrated_changed_keys) ^ set(d1_changed_keys)),
        "unchanged_set_symmetric_difference": sorted(set(integrated_unchanged_keys) ^ set(d1_unchanged_keys)),
    }
    comp_b["pass"] = bool(comp_b["changed_set_matches_d1_exactly"] and comp_b["unchanged_set_matches_d1_exactly"])
    report["comparisons"]["B_scope_parity"] = comp_b
    check("comparison.B_scope_parity_exact_57_and_28_set_match", comp_b["pass"],
          (comp_b["changed_set_symmetric_difference"], comp_b["unchanged_set_symmetric_difference"]))

    # ------------------------------------------------------------------
    # Comparison C: final-state aggregate parity.
    # ------------------------------------------------------------------
    comp_c = {
        "integrated_post_hash": integrated_post_hash,
        "d1_post_hash": EXPECTED_POST_HASH,
        "pass": bool(integrated_post_hash == EXPECTED_POST_HASH),
    }
    report["comparisons"]["C_final_state_parity"] = comp_c
    check("comparison.C_final_state_parity", comp_c["pass"], integrated_post_hash)

    # ------------------------------------------------------------------
    # Comparison D: per-target parity, all 85 eligible targets,
    # individually, against the D1 manifest's own POST hashes. D2-2:
    # if ANY target mismatches, its raw PRE/POST fingerprint is
    # preserved in mismatch_diagnostics as diagnostic evidence -- no
    # bulk in-process structural diff object is ever built.
    # ------------------------------------------------------------------
    post_matching, post_mismatching, post_missing_actual, post_missing_expected = compare_hash_maps(
        integrated_post_target_hashes, manifest["eligible_post_target_hashes"]
    )
    comp_d = {
        "total_targets_compared": len(integrated_post_target_hashes),
        "matching_count": len(post_matching),
        "mismatching_count": len(post_mismatching),
        "mismatching_targets": post_mismatching,
        "missing_in_integrated": post_missing_actual,
        "missing_in_d1_manifest": post_missing_expected,
        "pass": bool(len(post_mismatching) == 0 and len(post_missing_actual) == 0 and len(post_missing_expected) == 0
                     and len(integrated_post_target_hashes) == 85),
    }
    report["comparisons"]["D_per_target_parity"] = comp_d
    check("comparison.D_per_target_parity_all_85_individually_equal", comp_d["pass"], (comp_d["matching_count"], comp_d["mismatching_count"]))

    for _key in post_mismatching:
        report["mismatch_diagnostics"]["eligible"].setdefault(_key, {})
        report["mismatch_diagnostics"]["eligible"][_key]["integrated_post"] = integrated_post_fingerprint.get(_key)
        report["mismatch_diagnostics"]["eligible"][_key].setdefault("note", "POST-state per-target mismatch (Comparison D).")

    # ------------------------------------------------------------------
    # Comparison E: exclusion parity, all 78 excluded targets.
    # ------------------------------------------------------------------
    excl_matching, excl_mismatching, excl_missing_actual, excl_missing_expected = compare_hash_maps(
        integrated_excluded_post_hashes, manifest["excluded_post_target_hashes"]
    )
    comp_e = {
        "total_excluded_compared": len(integrated_excluded_post_hashes),
        "matching_count": len(excl_matching),
        "mismatching_count": len(excl_mismatching),
        "mismatching_targets": excl_mismatching,
        "missing_in_integrated": excl_missing_actual,
        "missing_in_d1_manifest": excl_missing_expected,
        "pass": bool(len(excl_mismatching) == 0 and len(excl_missing_actual) == 0 and len(excl_missing_expected) == 0
                     and len(integrated_excluded_post_hashes) == 78),
    }
    report["comparisons"]["E_exclusion_parity"] = comp_e
    check("comparison.E_exclusion_parity_all_78_individually_equal", comp_e["pass"], (comp_e["matching_count"], comp_e["mismatching_count"]))

    for _key in excl_mismatching:
        report["mismatch_diagnostics"]["excluded"].setdefault(_key, {})
        report["mismatch_diagnostics"]["excluded"][_key]["integrated_post"] = post_excluded_witness.get(_key)
        report["mismatch_diagnostics"]["excluded"][_key].setdefault("note", "POST-state excluded-witness mismatch (Comparison E).")

    report["evidence_size_diagnostics"] = {
        "integrated_pre_target_count": len(integrated_pre_target_hashes),
        "integrated_post_target_count": len(integrated_post_target_hashes),
        "integrated_pre_approx_serialized_bytes": pre_approx_serialized_bytes,
        "integrated_post_approx_serialized_bytes": post_approx_serialized_bytes,
        "excluded_witness_pre_count": len(integrated_excluded_pre_hashes),
        "excluded_witness_post_count": len(integrated_excluded_post_hashes),
        "mismatch_diagnostics_eligible_count": len(report["mismatch_diagnostics"]["eligible"]),
        "mismatch_diagnostics_excluded_count": len(report["mismatch_diagnostics"]["excluded"]),
    }

    # D2-2: the raw POST fingerprint/excluded-witness dicts are no
    # longer needed -- their hashes are computed, and any mismatch
    # diagnostics have already been captured above. Release them
    # before the (already-small) finalize/write phase.
    del integrated_post_fingerprint, post_excluded_witness

    # ------------------------------------------------------------------
    # 10. Shared-authority runtime evidence -- via the exec-exposed
    #     module bindings the production Normalizer's own source
    #     already imports (existing qualified diagnostics, no invasive
    #     instrumentation). Identical technique to Checkpoint C2.
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

    check("authority.broker_state_is_ready", evidence.get("get_state") == "READY", evidence.get("get_state"))
    check("authority.is_canonical_true", evidence.get("is_canonical") is True, evidence.get("is_canonical"))
    check("authority.zero_outstanding_leases", evidence.get("outstanding_lease_count") == 0, evidence.get("outstanding_lease_count"))
    _provider_counters = evidence.get("provider_counters") or {}
    check("authority.zero_currently_open_providers", _provider_counters.get("current_open_provider_count") == 0, _provider_counters.get("current_open_provider_count"))
    check("authority.provider_opens_closes_balanced",
          _provider_counters.get("total_provider_opens") == _provider_counters.get("total_provider_closes"),
          (_provider_counters.get("total_provider_opens"), _provider_counters.get("total_provider_closes")))

    report["provenance"]["authority_api_version"] = evidence.get("runtime_api_version")
    report["provenance"]["authority_build_id"] = evidence.get("runtime_build_id")

    # ------------------------------------------------------------------
    # 11. Native-protection / command-completion evidence -- via the
    #     production Normalizer's OWN existing log file, opened in "w"
    #     (truncate) mode by this exact run's own start() method.
    #     Identical technique to Checkpoint C2. Not the later dedicated
    #     native-handle coordination test.
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
        del log_bytes, log_text
        native_evidence["inference"] = (
            "This run's own start() method opens OUTPUT_PATH in \"w\" (truncate) "
            "mode, so the content read here reflects only this run. The "
            "production Normalizer's own fail-closed gate raises ProbeError "
            "before reaching self.rebuild(...) if native-handle acquisition "
            "did not succeed, so the presence of the "
            "\"NATIVE_REBUILD_RETURNED = PASS\" log line is proof-by-"
            "construction that native protection was successfully acquired "
            "for this exact run -- an inference from an existing qualified "
            "log, not new instrumentation. This is NOT the later dedicated "
            "native-handle coordination test."
        )
    except Exception as exc:
        native_evidence["log_read_ok"] = False
        native_evidence["log_read_error"] = repr(exc)
        anomaly("Could not read production Normalizer log for native-protection evidence: %r" % exc)

    check("native_protection.guards_pass", native_evidence.get("contains_NATIVE_GUARDS_PASS") is True, native_evidence.get("contains_NATIVE_GUARDS_PASS"))
    check("native_protection.rebuild_returned_pass", native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS") is True, native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS"))
    check("native_protection.production_revision_marker_present", native_evidence.get("contains_production_revision_marker") is True, native_evidence.get("contains_production_revision_marker"))

    report["memory_snapshots"]["after_all_comparisons"] = memory_snapshot()

except CheckpointD2Error as gate_exc:
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

all_checks_passed = all(c["pass"] for c in report["checks"]) if report["checks"] else False
completed_without_exception = not any(
    a.startswith("UNHANDLED TOP-LEVEL EXCEPTION") for a in ANOMALIES
)
all_comparisons_passed = all(
    bool(v.get("pass")) for v in report["comparisons"].values()
) if report["comparisons"] else False
runtime_checks_passed = bool(all_checks_passed and completed_without_exception and run_started and all_comparisons_passed)
report["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

evidence_expected = runtime_checks_passed

report["overall_pass"] = False  # provisional/conservative; corrected below only if fully verified.
report["artifact_write_verified"] = False
report["artifact_evidence_detail"] = None
report["json_write_error"] = None

write1_ok, write1_error, reparsed1 = write_json_atomic(JSON_OUTPUT_PATH, report)

if evidence_expected:
    if write1_ok:
        evidence_ok, evidence_detail = verify_artifact_evidence(reparsed1)
    else:
        evidence_ok, evidence_detail = False, "artifact write failed: %s" % (write1_error,)
else:
    evidence_ok, evidence_detail = True, "not required (run did not reach evidence-building stage)"

reparsed1 = None
try:
    gc.collect()
except Exception:
    pass

report["artifact_write_verified"] = bool(write1_ok and evidence_ok)
report["artifact_evidence_detail"] = evidence_detail
if not write1_ok:
    report["json_write_error"] = write1_error
report["overall_pass"] = bool(runtime_checks_passed and report["artifact_write_verified"])

json_write_ok, write2_error, _reparsed2 = write_json_atomic(JSON_OUTPUT_PATH, report)
_reparsed2 = None
if not json_write_ok:
    report["json_write_error"] = (
        ("%s ; retry also failed: %s" % (write1_error, write2_error)) if not write1_ok else write2_error
    )
    # Independent-audit correction, D2-2: the compact artifact no
    # longer carries a large raw-fingerprint payload to drop, so the
    # degraded fallback instead drops the (comparatively larger)
    # per-target hash maps and any mismatch diagnostics, keeping
    # aggregate hashes, counts, comparisons, checks, provenance, and
    # runtime evidence intact. CRITICAL FIX: overall_pass and
    # artifact_write_verified are set EXPLICITLY on degraded_report
    # itself, never merely inherited from whatever `report` happened
    # to hold at snapshot time -- `dict(report)` is a point-in-time
    # copy, and D2-1's own bug was exactly this: `report["overall_
    # pass"]` was corrected to False only AFTER this snapshot was
    # already taken and written to disk, so a degraded artifact could
    # falsely claim `overall_pass: true` even while the authoritative
    # summary correctly said False. A degraded/fallback artifact must
    # never claim qualification PASS.
    degraded_report = dict(report)
    degraded_report.pop("eligible_pre_target_hashes", None)
    degraded_report.pop("eligible_post_target_hashes", None)
    degraded_report.pop("excluded_pre_target_hashes", None)
    degraded_report.pop("excluded_post_target_hashes", None)
    degraded_report.pop("mismatch_diagnostics", None)
    degraded_report["degraded_artifact"] = True
    degraded_report["overall_pass"] = False
    degraded_report["artifact_write_verified"] = False
    degraded_report["degraded_reason"] = (
        "Per-target hash maps and mismatch diagnostics omitted because the "
        "complete compact artifact write failed (%s). This degraded fallback "
        "preserves every mechanical check, aggregate hash, count, comparison "
        "result, provenance field, and anomaly so evidence is never left as a "
        "misleading zero-byte file. overall_pass and artifact_write_verified "
        "are forced False here regardless of the live report's own state at "
        "snapshot time." % (report["json_write_error"],)
    )
    fallback_ok, fallback_error, _r3 = write_json_atomic(JSON_OUTPUT_PATH, degraded_report)
    _r3 = None
    report["degraded_fallback_written"] = fallback_ok
    if fallback_ok:
        json_write_ok = True  # SOMETHING complete and evidentiary (and correctly non-PASS) is now on disk.
    else:
        report["json_write_error"] = "%s ; degraded fallback also failed: %s" % (report["json_write_error"], fallback_error)
    report["overall_pass"] = False

summary_lines = []
summary_lines.append("SFM CHECKPOINT D2 -- INTEGRATED (POST-INTEGRATION) ALL-SHOTS EQUIVALENCE RUN")
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
if report.get("gate_failure"):
    summary_lines.append("")
    summary_lines.append("*** GATE FAILURE: aborted BEFORE any production Normalizer invocation or scene mutation. ***")
    summary_lines.append("*** No mutation occurred. See the FAIL line(s) below for exactly which fixture, ***")
    summary_lines.append("*** D1-manifest-integrity, or starting-state condition did not hold. ***")
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
summary_lines.append("--- COMPARISONS A-F ---")
for comp_name in ("A_starting_state_parity", "B_scope_parity", "C_final_state_parity", "D_per_target_parity", "E_exclusion_parity", "F_target_set_parity"):
    comp_val = report["comparisons"].get(comp_name)
    summary_lines.append("[%s] %s" % ("PASS" if (comp_val and comp_val.get("pass")) else "FAIL/MISSING", comp_name))
summary_lines.append("")
summary_lines.append("run_started=%r  run_completed_cleanly=%r  command_duration_seconds=%r" % (run_started, run_completed_cleanly, report.get("command_duration_seconds")))
summary_lines.append("integrated_pre_fingerprint_hash=%r" % report.get("integrated_pre_fingerprint_hash"))
summary_lines.append("integrated_post_fingerprint_hash=%r" % report.get("integrated_post_fingerprint_hash"))
summary_lines.append("d1_pre_hash(expected)=%r" % EXPECTED_PRE_HASH)
summary_lines.append("d1_post_hash(expected)=%r" % EXPECTED_POST_HASH)
summary_lines.append("changed_target_count=%r  unchanged_target_count=%r" % (len(report.get("changed_target_keys") or []), len(report.get("unchanged_target_keys") or [])))
summary_lines.append("mismatch_diagnostics_eligible_count=%r  mismatch_diagnostics_excluded_count=%r"
                      % (len((report.get("mismatch_diagnostics") or {}).get("eligible") or {}), len((report.get("mismatch_diagnostics") or {}).get("excluded") or {})))
summary_lines.append("evidence_size_diagnostics=%r" % report.get("evidence_size_diagnostics"))
summary_lines.append("")
summary_lines.append("--- PROVENANCE ---")
for k in sorted((report.get("provenance") or {}).keys()):
    summary_lines.append("  %s = %r" % (k, report["provenance"][k]))
summary_lines.append("")
summary_lines.append("--- MEMORY SNAPSHOTS (diagnostic only) ---")
for k in sorted((report.get("memory_snapshots") or {}).keys()):
    summary_lines.append("  %s: %r" % (k, report["memory_snapshots"][k]))
summary_lines.append("")
summary_lines.append("--- AUTHORITY RUNTIME EVIDENCE ---")
for k in sorted(report["authority_runtime_evidence"].keys()):
    summary_lines.append("  %s = %r" % (k, report["authority_runtime_evidence"][k]))
summary_lines.append("")
summary_lines.append("--- NATIVE PROTECTION EVIDENCE ---")
for k in sorted(report["native_protection_evidence"].keys()):
    summary_lines.append("  %s = %r" % (k, report["native_protection_evidence"][k]))
summary_lines.append("")
summary_lines.append("artifact_write_verified=%r" % report.get("artifact_write_verified"))
summary_lines.append("artifact_evidence_detail=%r" % report.get("artifact_evidence_detail"))
summary_lines.append("json_write_error=%r" % report.get("json_write_error"))
if report.get("degraded_artifact"):
    summary_lines.append("")
    summary_lines.append("*** DEGRADED ARTIFACT: per-target hash maps/mismatch diagnostics were omitted ***")
    summary_lines.append("*** because the complete compact artifact write failed. degraded_fallback_written=%r ***" % report.get("degraded_fallback_written"))
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
        "\nCheckpoint D2 reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r, error=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok, summary_write_error)
    )
    sys.stdout.write("\nDO NOT SAVE. Restart SFM to discard this integrated-run mutation.\n")
except Exception:
    pass
