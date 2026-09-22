# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint D1: Historical (pre-
integration) All-Shots baseline run.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: **THIS CHECKPOINT MUTATES THE SCENE.** It invokes the
exact historical, pre-integration frozen Normalizer's own real All
Shots behavior, unmodified, against the disposable qualification
project. Do not save afterward.

D1-3 CORRECTION (2026-09-22): D1-2 proved the writer correction itself
worked (nonzero JSON, parseable, real exception retained, OVERALL_PASS
correctly False) but a NEW failure surfaced one step earlier: a real
`MemoryError()` inside `stable_hash()`'s own `joined.encode("utf-8")`
step while hashing the 85-target POST fingerprint, in this 32-bit
qualification-harness process. This revision:
  (a) replaces `stable_hash()` with a byte-for-byte-equivalent
      streaming implementation that never builds a giant joined
      Unicode string or a giant encoded byte string -- proven
      hash-identical to the old implementation by a dedicated offline
      regression across empty/single/many-item/real-C1-C2-data/large
      synthetic inputs;
  (b) makes the JSON artifact writer genuinely streaming (`json.dump`
      directly to the temp file, no giant in-memory serialized string,
      compact -- no `indent`, no whole-document `sort_keys`, since
      qualification evidence is the data, not its on-disk formatting);
  (c) releases redundant transient structures (the full 163-target
      witness objects, the raw production-Normalizer source text, the
      historical baseline's executed module namespace) as soon as
      each is no longer needed, well before the memory-heavier
      hashing/serialization phase, instead of holding everything for
      the whole script's lifetime;
  (d) assigns captured PRE/POST fingerprint evidence into the report
      immediately after capture, before any expensive derived
      analysis (hashing) -- so a hashing failure does not also destroy
      already-captured raw evidence, unlike D1-2's own failure mode;
  (e) bounds the round-trip verification step so the live report and
      a second full reparsed-from-disk copy are not both retained
      longer than the single verification call needs them;
  (f) adds lightweight, best-effort, stdlib-only (ctypes) process
      memory snapshots at useful boundaries, diagnostic only.
Historical Normalizer invocation, fingerprint semantics, fixture/
starting-state gates, and the All-Shots operation itself are otherwise
unchanged from D1-2.

Purpose:
  Establish the historical (pre-integration) All-Shots outcome as the
  authoritative baseline Checkpoint D2 will later be compared against
  -- the same role Checkpoint C1 played for Selected Shots vs C2. This
  script:
    1. verifies the historical baseline source's SHA-256 before ever
       executing a byte of it;
    2. verifies the currently-installed production Normalizer has NOT
       been replaced (identity check only -- this checkpoint runs the
       SEPARATE historical baseline source, never the installed file);
    3. verifies the canonical Master's SHA-256;
    4. independently re-derives the Checkpoint-B-style fixture witness
       fresh from the live document and cross-checks it against the
       fixed structural totals (15 shots, 163 targets, 85 eligible, 78
       excluded, 22 distinct models, 21 distinct eligible vocabulary
       hashes) -- All-Shots scope does not depend on which shot(s) are
       selected, so no selected-shot-specific check gates this run;
       the live selection state is recorded as evidence only;
    5. HARD GATES on the above, plus a fresh 85-eligible-target PRE
       fingerprint hash matching Checkpoint C1/C2's own accepted PRE
       hash exactly -- this proves Checkpoint C2's mutation was
       discarded and this run starts from the same original fixture
       state C1/C2 did. If the live state does not match, this script
       aborts BEFORE any baseline invocation or scene mutation;
    6. captures a structural PRE fingerprint of all 85 eligible targets
       (same technique C1/C2 used), plus a lightweight, non-mutating
       STRUCTURAL witness (never the full fingerprint schema, which
       requires a valid root control group capture_snapshot_explicit
       raises ProbeError without -- not guaranteed for excluded,
       non-model-backed targets such as cameras/lights) of all 78
       independently-classified excluded targets;
    7. executes the exact, byte-verified historical baseline source in
       an isolated namespace -- this triggers the historical code's
       own real, unmodified, interactive Clip-Editor scope-choice
       dialog; the operator must select **All Shots** and confirm;
    8. waits (pumping the real Qt event loop, polling the historical
       run's own run-lock object) for that real, asynchronous
       operation to actually finish;
    9. rebuilds the independent witness fresh (to detect any target
       that vanished, appeared, or was reclassified between eligible
       and excluded as a side effect of the All-Shots run);
   10. captures the same structural POST fingerprint for the same 85
       eligible targets, plus the same lightweight structural witness
       for the same 78 excluded targets;
   11. compares PRE vs POST per eligible target (after canonicalizing
       away only process-local handle integers and the label field,
       never semantic content) to determine which targets actually
       changed -- **without assuming all 85 must change**: some may
       already match the Master and be legitimate no-ops;
   12. writes a complete machine-readable result artifact that becomes
       Checkpoint D2's own expected values.

This script never imports `sfm_master_authority_productionized`, never
imports the installed `Rebuild_Control_Groups_Normalizer.py` for
behavior (only reads its bytes for an identity SHA check), and never
touches the canonical Master for anything other than a read-only
SHA-256 check. It does not retrofit shared authority into the
historical baseline in any way.

Output:
  Two files are written to C:\\Users\\Public\\Documents\\:
    sfm_checkpoint_d1_historical_all_shots_result.json          (machine-readable, full detail)
    sfm_checkpoint_d1_historical_all_shots_result_summary.txt   (concise human-readable)
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

EXPECTED_HISTORICAL_BASELINE_SHA256 = (
    "6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e"
)
EXPECTED_PRODUCTION_NORMALIZER_SHA256 = (
    "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"
)
EXPECTED_CANONICAL_MASTER_SHA256 = (
    "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
)

# Ground-truthed directly from C1-2/C2-1's own accepted result artifacts
# on disk (not retyped from a conversation transcript). All-Shots scope
# does not depend on shot selection, so no selected-shot-specific gate
# is required here -- but the SAME 85 eligible targets, identified by
# the SAME independent structural classification, must still produce
# the SAME PRE fingerprint hash: this proves the live project has been
# reverted to the original fixture state (Checkpoint C2's mutation was
# discarded) before this historical run begins.
EXPECTED_INITIAL_PRE_HASH = (
    "eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0"
)

EXPECTED_TOTALS = {
    "total_shots": 15,
    "total_targets": 163,
    "eligible_targets": 85,
    "excluded_targets": 78,
    "distinct_model_names": 22,
    "distinct_fold_vocabulary_hashes_among_eligible": 21,
}

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_d1_historical_all_shots_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_d1_historical_all_shots_result_summary.txt"

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

# 1-indexed, inclusive. IDENTICAL range table to Checkpoints C1/C2's own
# (same reasoning: pure, read-only, structural DME-reading functions,
# never scope/eligibility POLICY, extracted from the CURRENT installed
# production Normalizer file -- identical code in both the historical
# and integrated paths, untouched by the Production Normalizer
# Integration work).
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


class CheckpointD1Error(Exception):
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
# used by Checkpoints C1/C2, kept verbatim for internal consistency
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
                raise CheckpointD1Error(
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
    """Independent-audit correction, D1-3 (Section 1): streaming
    replacement for the prior `joined = u"\\n".join(sorted(values));
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()`
    implementation, which built ONE giant joined Unicode string and
    THEN a second giant encoded byte string -- the exact operation a
    real MemoryError was observed inside (D1-2, hashing the 85-target
    POST fingerprint in this 32-bit process).

    This version feeds hashlib.sha256() incrementally, one already-
    short-lived per-item UTF-8 encoding at a time, and never holds a
    combined joined/encoded copy of the whole input. It is proven
    byte-for-byte digest-equivalent to the old implementation (same
    item ordering via the same `sorted()`, same UTF-8 encoding, same
    "\\n" separator bytes -- inserted between items exactly as
    `"\\n".join` would, never before the first or after the last --
    and the same empty-input behavior: `hashlib.sha256(b"").hexdigest()`)
    by `real_sfm_qualification/checkpoint_d1/test_d1_stable_hash_streaming_regression.py`,
    including against real captured Checkpoint C1/C2 fingerprint data
    and large synthetic inputs the old implementation cannot safely
    process in this process. `sorted(values)` itself only duplicates a
    list of references to the existing item strings, not their
    content, so it is not part of the peak-allocation pattern being
    corrected here."""
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
    target -- deliberately never routed through capture_snapshot_
    explicit(), which raises ProbeError for any target lacking a valid
    root control group (not guaranteed for non-model-backed excluded
    targets such as cameras/lights). Built entirely from the same
    independent classification fields build_independent_witness()
    already computes -- no new semantics invented. Process-local
    pointer identities (shot_ptr/aset_ptr) are intentionally excluded
    from this comparison-relevant dict, same discipline as handle
    stripping in canonicalize_snapshot."""
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


def memory_snapshot():
    """Independent-audit correction, D1-3 (Section 8): best-effort,
    stdlib-only (ctypes) Windows process memory snapshot -- diagnostic
    only for D1-3, never affects Normalizer behavior, and never raises
    (degrades to {"available": False, ...} on any failure, including
    on a non-Windows or restricted-sandbox interpreter)."""
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
# Safe artifact writer (independent-audit correction, D1-2, refined D1-3).
#
# D1-1's own writer opened JSON_OUTPUT_PATH directly in "wb" mode --
# which TRUNCATES any existing file immediately on open -- and only
# THEN called json.dumps(...). If dumps()/encode()/write() raised for
# ANY reason, the bare `except Exception: json_write_ok = False`
# discarded the actual exception, leaving a truncated ZERO-BYTE file
# with no diagnostic evidence of why.
#
# D1-2 fixed the truncation/exception-swallowing defect (proven working
# by D1-2's own MemoryError run: nonzero JSON, parseable, real
# exception retained, OVERALL_PASS correctly False) but still built one
# complete `json.dumps(..., indent=2, sort_keys=True)` string in memory
# before writing it. D1-3 replaces that with `json.dump()` streaming
# directly to the temp file (never building the whole serialized
# document as one in-memory string) and drops `indent`/whole-document
# `sort_keys` -- qualification evidence is the data, not its on-disk
# formatting.
#
# write_json_atomic() never truncates the final authoritative path
# until the streamed write itself, AND an independent reopen+reparse
# of a separate temp file, have all already succeeded.
# ---------------------------------------------------------------------------

def write_json_atomic(final_path, data_obj):
    """Returns (ok, error_repr_or_None, reparsed_obj_or_None).
    Python-2.7-compatible. Streams the JSON encoding directly to the
    temp file via json.dump() -- never builds one giant in-memory
    serialized string -- compact (no indent, no whole-document
    sort_keys). Never truncates `final_path` before the write and an
    independent reopen+reparse of a separate temp file have both
    already succeeded."""
    tmp_path = final_path + ".tmp"

    def _cleanup_tmp():
        # Best-effort removal of a temp file that is known NOT to hold
        # the only surviving copy of a fully-written, fully-verified
        # payload -- a partial/failed write (json.dump() streams
        # chunks directly to the file, so a mid-write failure can
        # leave a partially-written temp file behind, unlike the prior
        # dumps()-then-write approach which never touched disk before
        # a serialization failure) must never be left lying around.
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
                pass  # best-effort durability only; not fatal if unsupported.
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

    # Only now, with the write and reparse independently proven,
    # replace the final authoritative path. os.rename() on Windows
    # refuses to overwrite an existing destination, so remove it first
    # -- this narrows, but (without a platform-specific atomic-replace
    # call) does not fully close, the replace-window race; the temp
    # file itself is never left partially written, and the final path
    # is never touched at all unless every step above succeeded. If
    # promotion itself fails here, the temp file is deliberately LEFT
    # IN PLACE (not cleaned up) -- it is the only surviving copy of a
    # fully-written, fully-verified payload at this point.
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


REQUIRED_EVIDENCE_KEYS = (
    "pre_fingerprint_hash", "post_fingerprint_hash", "pre_fingerprint", "post_fingerprint",
    "excluded_target_witness", "target_set_diff", "fixture_totals",
    "semantically_changed_target_set", "semantically_unchanged_target_set",
)


def verify_artifact_evidence(reparsed_obj):
    """Returns (ok, detail). Checks presence/completeness of the
    required evidence fields AND that the stored PRE/POST fingerprint
    hashes recompute correctly from the stored semantic fingerprint
    data (round-trip integrity through actual JSON serialization, not
    merely that the file parses as valid JSON). Reuses the same
    streaming stable_hash()/dumps_sorted() as the main computation, so
    this recompute carries the same D1-3 low-peak-memory guarantee."""
    if reparsed_obj is None:
        return False, "reparsed artifact is None"
    missing_keys = [k for k in REQUIRED_EVIDENCE_KEYS if k not in reparsed_obj]
    if missing_keys:
        return False, "missing required evidence keys: %r" % (missing_keys,)
    pre_fp = reparsed_obj.get("pre_fingerprint") or {}
    post_fp = reparsed_obj.get("post_fingerprint") or {}
    if len(pre_fp) != 85 or len(post_fp) != 85:
        return False, "stored fingerprint counts wrong: pre=%d post=%d" % (len(pre_fp), len(post_fp))
    excluded_witness = reparsed_obj.get("excluded_target_witness") or {}
    pre_excluded_count = len(excluded_witness.get("pre") or {})
    post_excluded_count = len(excluded_witness.get("post") or {})
    if pre_excluded_count != 78 or post_excluded_count != 78:
        return False, "stored excluded-witness counts wrong: pre=%d post=%d" % (pre_excluded_count, post_excluded_count)
    recomputed_pre_hash = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in pre_fp.items()])
    recomputed_post_hash = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in post_fp.items()])
    if recomputed_pre_hash != reparsed_obj.get("pre_fingerprint_hash"):
        return False, "recomputed PRE hash %r != stored %r" % (recomputed_pre_hash, reparsed_obj.get("pre_fingerprint_hash"))
    if recomputed_post_hash != reparsed_obj.get("post_fingerprint_hash"):
        return False, "recomputed POST hash %r != stored %r" % (recomputed_post_hash, reparsed_obj.get("post_fingerprint_hash"))
    return True, None


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

report = {
    "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "python_version": sys.version,
    "checks": [],
    "anomalies": ANOMALIES,
    "target_set_diff": {},
    "excluded_target_witness": {},
    "memory_snapshots": {},
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
pre_witness = None
post_witness = None

try:
    report["memory_snapshots"]["at_start"] = memory_snapshot()

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
        raise CheckpointD1Error("One or more pre-flight SHA-256 checks failed -- refusing to proceed.")

    # --- 2. Fixture/structural-totals verification. All-Shots scope does
    #        NOT depend on shot selection, so no selected-shot-specific
    #        check gates this run -- selection state is recorded as
    #        evidence only, below. ---
    pre_witness, shots_by_name, witness_error = build_independent_witness()
    if witness_error is not None:
        raise CheckpointD1Error("Could not build independent witness: %s" % witness_error)

    # Extracted immediately (small dict) so pre_witness itself can be
    # released later without losing this evidence.
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

    # --- 3. Build the fingerprint-function namespace (extracted, SHA-
    #        pinned to the current installed production Normalizer,
    #        never executed for behavior). ---
    all_lines = production_bytes.decode("ascii").splitlines()
    blocks = []
    for label, start, end in FINGERPRINT_FUNCTION_RANGES:
        blocks.append("\n".join(all_lines[start - 1:end]))
    combined_source = "\n\n".join(blocks)

    fp_ns = dict(FINGERPRINT_MODULE_CONSTANTS)
    fp_ns["hashlib"] = hashlib
    exec(compile(combined_source, "<checkpoint_d1_fingerprint_functions>", "exec"), fp_ns)
    check("fingerprint_functions.extracted_and_exec_ok", True)

    capture_snapshot_explicit_fn = fp_ns["capture_snapshot_explicit"]

    # Independent-audit correction, D1-3 (Section 2 audit finding): the
    # raw production-Normalizer SOURCE TEXT is only needed to extract
    # the fingerprint FUNCTIONS above; once fp_ns holds the executed
    # functions, the raw text is redundant and safe to release before
    # the memory-heavier capture/hash/write phases below.
    del all_lines, blocks, combined_source, production_bytes

    def canonicalize_snapshot(snap):
        """Identical to Checkpoints C1/C2's own canonicalize_snapshot:
        strips process-local handle integers and the PRE/POST `label`
        field before any equality/hash comparison."""
        clean = dict(snap)
        for key in ("shot_handle", "animation_set_handle", "root_handle", "rig_handle", "registry_handle", "label"):
            clean.pop(key, None)
        clean.pop("control_handles", None)
        return clean

    def capture_all(label, targets_of_interest_local):
        """targets_of_interest_local: list of (shot_name, aset_name)
        pairs to re-resolve fresh from the live document (never held
        across the historical baseline's own mutation)."""
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

    # Full semantic fingerprint: all 85 eligible targets, derived
    # directly from the witness's own eligibility classification.
    eligible_targets_of_interest = [(t["shot_name"], t["aset_name"]) for t in pre_eligible_rows]

    # Independent-audit correction, D1-3 (Section 2 audit finding):
    # extract the cheap key SETS now (used later for the target-set
    # diff and excluded-witness lookups) so the full per-target row
    # LISTS can be released before the historical run's own wait,
    # rather than held across the whole script's lifetime.
    pre_eligible_keys = set(target_key(t) for t in pre_eligible_rows)
    del pre_eligible_rows

    # --- 4. Initial PRE fingerprint + excluded structural witness. ---
    report["memory_snapshots"]["before_pre_capture"] = memory_snapshot()
    pre_fingerprint = capture_all("PRE", eligible_targets_of_interest)
    check("fingerprint.pre_capture_count_matches_expected", len(pre_fingerprint) == 85, len(pre_fingerprint))
    report["memory_snapshots"]["after_pre_capture"] = memory_snapshot()

    # Independent-audit correction, D1-3 (Section 7): assign captured
    # evidence into `report` IMMEDIATELY, before any expensive derived
    # analysis (hashing) -- this is exactly the operation D1-2's
    # MemoryError occurred inside, and D1-2's own fallback artifact was
    # missing the POST fingerprint specifically because it had not yet
    # been assigned into `report` when the hash computation crashed.
    report["pre_fingerprint"] = pre_fingerprint

    pre_hash = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in pre_fingerprint.items()])
    report["initial_pre_fingerprint_hash"] = pre_hash
    report["pre_fingerprint_hash"] = pre_hash

    pre_excluded_witness = dict((target_key(t), excluded_witness_row(t)) for t in pre_excluded_rows)
    report["excluded_target_witness"]["pre"] = pre_excluded_witness
    pre_excluded_keys = set(target_key(t) for t in pre_excluded_rows)
    del pre_excluded_rows

    # --- Starting-state gate: this proves Checkpoint C2's own mutation
    #     was discarded (fresh SFM process, original disposable
    #     fixture) before any historical invocation. ---
    check("gate.initial_pre_hash_matches_c1_c2_pre_hash", pre_hash == EXPECTED_INITIAL_PRE_HASH, pre_hash)

    # --- HARD GATE: every check recorded above must pass BEFORE any
    #     invocation of the historical baseline or scene mutation.
    #     Mirrors Checkpoints C1-2/C2's own hard-gate discipline. ---
    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointD1Error(
            "STARTING-STATE / FIXTURE MISMATCH -- one or more required pre-flight, "
            "fixture-identity, or starting-state-parity checks failed (see the "
            "individual [FAIL] lines above/in this report for exactly which "
            "condition(s) did not hold). Aborting BEFORE any invocation of the "
            "historical baseline or scene mutation. Restart SFM and re-open the "
            "original disposable fixture without saving Checkpoint C2's mutation "
            "before rerunning; do not proceed on a mismatched starting state."
        )

    # Independent-audit correction, D1-3 (Section 2 audit finding): the
    # full 163-target witness list's only remaining downstream use is
    # its KEY SET (for the target-set-diff below); its per-target
    # values (model_name, control_count, etc.) are never read again.
    # Extract the key set now and release the full witness before the
    # historical run's own (potentially lengthy) wait.
    pre_all_target_keys = set(target_key(t) for t in pre_witness["targets"])
    del pre_witness

    # --- 5. Invoke the historical baseline (blocks on its own real,
    #        unmodified interactive scope dialog). ---
    main_window = sfmApp.GetMainWindow()
    check("baseline.main_window_available", main_window is not None)

    sys.stdout.write(
        "\n>>> Historical baseline is about to run its own real Selected/All "
        "Shots dialog. Select 'All Shots' and confirm. <<<\n\n"
    )

    baseline_ns = {}
    run_started = False
    try:
        exec(compile(baseline_source, "<historical_baseline_pre_integration>", "exec"), baseline_ns)
    except Exception as exc:
        anomaly("Historical baseline execution raised: %r" % exc)
        anomaly(traceback.format_exc())

    run_lock_name = baseline_ns.get("RUN_LOCK_NAME")

    # Independent-audit correction, D1-3 (Section 2 audit finding): the
    # historical baseline's entire executed module namespace and its
    # raw source text are not needed once the run-lock object NAME has
    # been extracted above -- the actually-running Qt-timer-driven job
    # holds its own internal references (Qt parent/child ownership via
    # main_window, which is how baseline_run_is_active() below finds
    # it), independent of this script's own baseline_ns/baseline_source
    # names. Releasing them here frees the largest remaining harness-
    # owned allocation for the duration of the historical run itself --
    # the single heaviest and longest phase of this whole script.
    del baseline_ns, baseline_source

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
    report["memory_snapshots"]["after_historical_run"] = memory_snapshot()

    # --- 6. Rebuild the independent witness fresh, to detect any
    #        target that vanished, appeared, or was reclassified
    #        between eligible and excluded as a side effect of the
    #        All-Shots run. ---
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

    report["target_set_diff"] = {
        "missing_targets_entirely": missing_targets_entirely,
        "new_targets_entirely": new_targets_entirely,
        "reclassified_eligible_to_excluded": reclassified_eligible_to_excluded,
        "reclassified_excluded_to_eligible": reclassified_excluded_to_eligible,
    }
    check("target_set.no_target_vanished_entirely", len(missing_targets_entirely) == 0, missing_targets_entirely)
    if new_targets_entirely:
        anomaly("New target(s) appeared after the All-Shots run that were not present before: %r" % (new_targets_entirely,))
    if reclassified_eligible_to_excluded or reclassified_excluded_to_eligible:
        anomaly(
            "Target(s) were reclassified between eligible and excluded as a side effect of the "
            "All-Shots run (eligible->excluded: %r, excluded->eligible: %r) -- reported per Section 7, "
            "not treated as an automatic regression at D1."
            % (reclassified_eligible_to_excluded, reclassified_excluded_to_eligible)
        )

    # --- 7. All-Shots historical POST fingerprint (same 85 eligible
    #        target keys, re-resolved fresh) + excluded structural
    #        witness (same 78 excluded target keys, re-resolved fresh
    #        from the rebuilt post witness where still present). ---
    report["memory_snapshots"]["before_post_capture"] = memory_snapshot()
    post_fingerprint = capture_all("POST", eligible_targets_of_interest)
    check("fingerprint.post_capture_count_matches_expected", len(post_fingerprint) == 85, len(post_fingerprint))
    report["memory_snapshots"]["after_post_capture"] = memory_snapshot()

    # Independent-audit correction, D1-3 (Section 7): same discipline
    # as PRE above -- assign captured evidence into `report`
    # immediately, before computing its hash (the exact operation
    # D1-2's MemoryError occurred inside).
    report["post_fingerprint"] = post_fingerprint

    # fp_ns/capture_snapshot_explicit_fn are not referenced again after
    # this, the last capture_all() call -- safe to release now.
    del fp_ns, capture_snapshot_explicit_fn

    post_hash = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in post_fingerprint.items()])
    report["all_shots_post_fingerprint_hash"] = post_hash
    report["post_fingerprint_hash"] = post_hash
    report["memory_snapshots"]["after_post_hash"] = memory_snapshot()

    post_excluded_witness = {}
    for key in sorted(pre_excluded_keys):
        t = post_all_by_key.get(key)
        if t is None:
            continue
        post_excluded_witness[key] = excluded_witness_row(t)
    report["excluded_target_witness"]["post"] = post_excluded_witness
    del post_all_by_key

    excluded_target_changes = []
    for key in sorted(pre_excluded_keys):
        pre_row = pre_excluded_witness.get(key)
        post_row = post_excluded_witness.get(key)
        if post_row is None:
            continue
        if dumps_sorted(pre_row) != dumps_sorted(post_row):
            excluded_target_changes.append(key)
    report["excluded_target_witness"]["changed_targets"] = excluded_target_changes
    report["excluded_target_witness"]["changed_count"] = len(excluded_target_changes)
    check("excluded_witness.complete_for_all_78_pre_excluded_targets",
          len(post_excluded_witness) == len(pre_excluded_keys), (len(post_excluded_witness), len(pre_excluded_keys)))

    # --- 8. Compare PRE vs POST, per eligible target. Do NOT assume
    #        all 85 must change -- report considered/changed/unchanged
    #        separately (Section 5). ---
    changed_targets = []
    unchanged_targets = []
    for key in sorted(set(pre_fingerprint.keys()) | set(post_fingerprint.keys())):
        pre_v = pre_fingerprint.get(key)
        post_v = post_fingerprint.get(key)
        if dumps_sorted(pre_v) != dumps_sorted(post_v):
            changed_targets.append(key)
        else:
            unchanged_targets.append(key)

    report["semantically_changed_target_set"] = sorted(changed_targets)
    report["semantically_unchanged_target_set"] = sorted(unchanged_targets)
    report["changed_target_count"] = len(changed_targets)
    report["unchanged_eligible_target_count"] = len(unchanged_targets)
    report["excluded_target_count"] = len(pre_excluded_keys)
    report["targets_considered_in_scope_note"] = (
        "The set of targets the historical All-Shots target planner actually "
        "iterated internally is not independently observable from outside the "
        "running command without new instrumentation (same class of limitation "
        "as Checkpoint C2's own in-process authority-lease state). This report "
        "distinguishes changed vs. unchanged among the 85 independently-witnessed "
        "eligible targets via direct PRE/POST semantic comparison, which is "
        "sufficient to establish Checkpoint D2's own expected values without "
        "requiring 'targets considered' as a separate observable quantity."
    )

    # Independent-audit correction, D1-3 (Section 8): bounded sizes/
    # counts of the major evidence structures -- diagnostic only,
    # computed via transient per-item dumps_sorted() calls inside a
    # generator (never materializing a list of all 85 serialized
    # strings at once).
    report["evidence_size_diagnostics"] = {
        "pre_fingerprint_target_count": len(pre_fingerprint),
        "post_fingerprint_target_count": len(post_fingerprint),
        "pre_fingerprint_approx_serialized_bytes": sum(len(dumps_sorted(v)) for v in pre_fingerprint.values()),
        "post_fingerprint_approx_serialized_bytes": sum(len(dumps_sorted(v)) for v in post_fingerprint.values()),
        "excluded_witness_pre_count": len(pre_excluded_witness),
        "excluded_witness_post_count": len(post_excluded_witness),
    }
    report["memory_snapshots"]["after_all_comparisons"] = memory_snapshot()

except CheckpointD1Error as gate_exc:
    # Orderly, expected abort (pre-flight SHA mismatch or fixture/
    # starting-state gate failure) -- distinct from an unexpected
    # crash, so the report makes clear this was a deliberate refusal
    # to proceed, not a bug.
    anomaly("GATE FAILURE (orderly abort, no baseline invocation attempted): %s" % gate_exc)
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
# D1 does not require a predetermined changed-target count or POST
# hash (Section 8) -- the runtime portion of overall_pass is decided
# purely by mechanical gate/capture/completeness checks, never by what
# the historical run actually changed.
runtime_checks_passed = bool(all_checks_passed and completed_without_exception and run_started)
report["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

# Artifact writing is part of PASS (D1-2, unchanged principle). OVERALL_
# PASS may not be True unless the JSON evidence artifact itself was
# written, is nonzero, reopens/reparses, contains the complete required
# evidence, and its own stored PRE/POST hashes recompute correctly from
# the stored semantic data. Evidence completeness/hash-recompute is
# only REQUIRED when the run actually reached the evidence-building
# stage -- an orderly gate abort legitimately never builds pre_
# fingerprint/post_fingerprint/etc, and already fails overall_pass via
# run_started=False regardless.
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

# Independent-audit correction, D1-3 (Section 4): release the separate
# reparsed-from-disk copy immediately after it has served its one
# purpose (round-trip evidence verification) -- do not carry a second
# full in-memory copy of the fingerprint data forward into the
# corrective final write below, where only the ORIGINAL `report`
# object (never duplicated) is needed.
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

# write1, if it succeeded, already promoted a conservative
# (overall_pass=False) version to JSON_OUTPUT_PATH. Always perform one
# corrective final write carrying the now-accurate overall_pass/
# artifact_write_verified fields -- whether or not write1 itself
# succeeded (if it failed, JSON_OUTPUT_PATH was never touched at all,
# so this is the only real attempt).
json_write_ok, write2_error, _reparsed2 = write_json_atomic(JSON_OUTPUT_PATH, report)
_reparsed2 = None
if not json_write_ok:
    report["json_write_error"] = (
        ("%s ; retry also failed: %s" % (write1_error, write2_error)) if not write1_ok else write2_error
    )
    # Last-resort degraded artifact: the full per-target fingerprint
    # payload is dropped (it is by far the largest part of the
    # payload, and the most likely thing implicated in a repeat
    # failure), but every mechanical check, hash, count, and anomaly
    # is preserved -- so evidence is never reduced to a misleading
    # zero-byte file even in this pathological case (first write
    # succeeded, the corrective final write did not).
    degraded_report = dict(report)
    degraded_report.pop("pre_fingerprint", None)
    degraded_report.pop("post_fingerprint", None)
    degraded_report["degraded_artifact"] = True
    degraded_report["degraded_reason"] = (
        "Full per-target fingerprint payload omitted because the complete "
        "artifact write failed (%s). This degraded fallback preserves every "
        "mechanical check, hash, count, and anomaly so evidence is never "
        "left as a misleading zero-byte file." % (report["json_write_error"],)
    )
    fallback_ok, fallback_error, _r3 = write_json_atomic(JSON_OUTPUT_PATH, degraded_report)
    _r3 = None
    report["degraded_fallback_written"] = fallback_ok
    if fallback_ok:
        json_write_ok = True  # SOMETHING complete and evidentiary is now on disk.
    else:
        report["json_write_error"] = "%s ; degraded fallback also failed: %s" % (report["json_write_error"], fallback_error)
    report["overall_pass"] = False

summary_lines = []
summary_lines.append("SFM CHECKPOINT D1 -- HISTORICAL (PRE-INTEGRATION) ALL-SHOTS BASELINE RUN")
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
if report.get("gate_failure"):
    summary_lines.append("")
    summary_lines.append("*** GATE FAILURE: aborted BEFORE any baseline invocation or scene mutation. ***")
    summary_lines.append("*** No mutation occurred. See the FAIL line(s) below for exactly which fixture ***")
    summary_lines.append("*** or starting-state condition did not hold. ***")
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
summary_lines.append("run_started=%r  run_completed_cleanly=%r" % (run_started, run_completed_cleanly))
summary_lines.append("selection_state_evidence=%r" % report.get("selection_state_evidence"))
summary_lines.append("initial_pre_fingerprint_hash=%r" % report.get("initial_pre_fingerprint_hash"))
summary_lines.append("all_shots_post_fingerprint_hash=%r" % report.get("all_shots_post_fingerprint_hash"))
summary_lines.append("changed_target_count=%r" % report.get("changed_target_count"))
summary_lines.append("unchanged_eligible_target_count=%r" % report.get("unchanged_eligible_target_count"))
summary_lines.append("excluded_target_count=%r" % report.get("excluded_target_count"))
summary_lines.append("excluded_targets_changed_count=%r" % (report.get("excluded_target_witness", {}) or {}).get("changed_count"))
summary_lines.append("target_set_diff=%r" % report.get("target_set_diff"))
summary_lines.append("evidence_size_diagnostics=%r" % report.get("evidence_size_diagnostics"))
summary_lines.append("")
summary_lines.append("--- MEMORY SNAPSHOTS (diagnostic only) ---")
for k in sorted((report.get("memory_snapshots") or {}).keys()):
    summary_lines.append("  %s: %r" % (k, report["memory_snapshots"][k]))
summary_lines.append("")
summary_lines.append("artifact_write_verified=%r" % report.get("artifact_write_verified"))
summary_lines.append("artifact_evidence_detail=%r" % report.get("artifact_evidence_detail"))
summary_lines.append("json_write_error=%r" % report.get("json_write_error"))
if report.get("degraded_artifact"):
    summary_lines.append("")
    summary_lines.append("*** DEGRADED ARTIFACT: the full per-target fingerprint payload was omitted ***")
    summary_lines.append("*** because the complete artifact write failed. degraded_fallback_written=%r ***" % report.get("degraded_fallback_written"))
    summary_lines.append("*** degraded_reason=%r ***" % report.get("degraded_reason"))
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
        "\nCheckpoint D1 reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r, error=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok, summary_write_error)
    )
    sys.stdout.write("\nDO NOT SAVE. Restart SFM to discard this baseline mutation before D2.\n")
except Exception:
    pass
