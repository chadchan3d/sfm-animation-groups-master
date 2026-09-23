# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint F1: Repeated / Warm-Use
Stability.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: **THIS CHECKPOINT MUTATES THE SCENE, REPEATEDLY.** It
invokes the REAL, INSTALLED, ACCEPTED, INTEGRATED production
Normalizer FOUR separate times in a row, in ONE continuous SFM
process, without restarting SFM between commands. Do not save
afterward.

Purpose:
  Checkpoints C/D already established historical-vs-integrated
  SEMANTIC equivalence (Selected Shots and All Shots each individually,
  once). F1 is NOT another equivalence campaign -- it proves the
  accepted integrated production Normalizer remains correct AND
  authority-lifecycle-clean across SEVERAL consecutive real commands
  in one warm SFM process:
    - repeated broker acquisition (the same process-wide `authority_
      runtime` singleton, queried fresh after each command);
    - fresh source authorization per command (see "Fresh authorization
      evidence" below -- grounded in direct reading of the accepted
      `sfm_master_authority_productionized/broker.py` source, not
      guessed);
    - generation consistency (the canonical Master's own SHA-256 is
      independently re-verified before the run);
    - provider/lease cleanup after EVERY command (zero outstanding
      leases, zero currently-open providers, no stale active cohort,
      balanced opens/closes for that command);
    - warm reuse vs. idempotence: Selected Shots run twice in a row
      must reach and then PRESERVE exactly the same known-good state;
      All Shots run twice in a row must do the same;
    - absence of accumulating retained state (memory snapshots at
      every command boundary, diagnostic only -- not a new production
      gate);
    - continued SFM responsiveness after the fourth command.

Command sequence (one continuous SFM process, no restart between
commands):
  1. Selected Shots  -- expected resulting aggregate hash: the known
     Checkpoint C2 Selected-Shots state (`d7b3bacb...`).
  2. Selected Shots again -- expected resulting aggregate hash: the
     SAME state, UNCHANGED. This script does NOT assume zero internal
     work occurred; it independently MEASURES the actual semantically
     changed target set between commands 1 and 2 (expected, but not
     assumed, to be empty).
  3. All Shots -- expected resulting aggregate hash: the known
     Checkpoint D1/D2 All-Shots state (`299cbba3...`). This script does
     NOT assume the PRE->POST changed-target count for this command
     must equal D1's original 57 (Fox/Mia were already normalized by
     command 1) -- it measures the actual changed set from THIS run's
     own immediately-preceding state.
  4. All Shots again -- expected resulting aggregate hash: the SAME
     All-Shots state, UNCHANGED. Again measured, not assumed.

Memory-bounded compact evidence (D1-3/D2-2 discipline, applied across
FOUR commands instead of one): at every command boundary this script
captures per-target HASHES (never raw fingerprint dicts) for all 85
eligible targets and all 78 excluded targets. A raw captured
fingerprint dict is held only transiently -- long enough to compute
its aggregate hash and per-target hashes -- and is released (`del`)
before the next command begins. At no point does this script hold more
than ONE command's worth of raw captured fingerprints in memory at
once; the accumulating per-command evidence in the final artifact is
compact per-target HASH maps only.

Fresh authorization evidence (grounded in direct source reading, not
new instrumentation): `sfm_master_authority_productionized/broker.py`'s
own `acquire_or_reuse_views()` calls `observation.observe_master(master_
path)` UNCONDITIONALLY on every single call, before ever checking the
view cache -- this IS the architecturally-designed fresh-authorization
step, and it runs on every command regardless of whether the heavier
provider-open path ends up being needed. If the requested fold-scope
for a command is *already* fully covered by a live cache entry for the
CURRENT (freshly-observed) generation, no provider is opened at all
(`_record("fully_reused_no_provider_open", ...)`); otherwise exactly
one `acquire_cohort()` call fills the gap. This script cannot directly
observe the internal `observe_master()` call without new instrumentation
(which the governing brief explicitly forbids), so it infers fresh
authorization from EXISTING, already-qualified diagnostics: (a) the
canonical Master's own SHA-256 is independently re-verified once before
the whole sequence, establishing there is a stable, known generation to
authorize against; (b) EVERY command completing successfully (no
`ProbeError`, native-protection log markers present) is proof-by-
construction that no `expected_generation_mismatch` /
`AuthorityChangedDuringAcquisition` was raised -- which the Normalizer's
own fail-closed policy would have surfaced as a command failure had the
freshly-observed generation ever disagreed with what the command
expected; (c) `provider_counters()`/`outstanding_lease_count()` deltas
are captured PER COMMAND (never only cumulative totals) -- whether a
given command's delta is (0 opens, 0 closes) [a genuine, valid cache-
hit reuse -- see docstring above] or (1 open, 1 close) [a fresh
provider open because the requested fold-scope was not yet fully
cached], BOTH are lifecycle-clean outcomes; the required, GATED
invariant is that the delta is BALANCED (opens == closes) for every
command and zero leases/providers are ever left outstanding -- not a
predetermined delta value.

Do not restart SFM between commands. Do not alter the scene between
commands.

Output:
  Two files are written to C:\\Users\\Public\\Documents\\:
    sfm_checkpoint_f1_repeated_warm_use_result.json          (machine-readable, compact)
    sfm_checkpoint_f1_repeated_warm_use_result_summary.txt   (concise human-readable)
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

# Ground-truthed directly from the real, accepted C1/C2/D1/D2 artifacts
# on disk (not retyped from a conversation transcript).
EXPECTED_INITIAL_PRE_HASH = (
    "eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0"
)
EXPECTED_SELECTED_HASH = (
    "d7b3bacb757253e126823db4e1445b57e4278d972c9be8b23920fc88cf1b5938"
)
EXPECTED_ALLSHOTS_HASH = (
    "299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7"
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
EXPECTED_TOTALS = {
    "total_shots": 15,
    "total_targets": 163,
    "eligible_targets": 85,
    "excluded_targets": 78,
    "distinct_model_names": 22,
    "distinct_fold_vocabulary_hashes_among_eligible": 21,
}

# (ordinal, operator-facing scope label, expected resulting aggregate hash)
COMMAND_SPECS = [
    (1, u"Selected Shots", EXPECTED_SELECTED_HASH),
    (2, u"Selected Shots", EXPECTED_SELECTED_HASH),
    (3, u"All Shots", EXPECTED_ALLSHOTS_HASH),
    (4, u"All Shots", EXPECTED_ALLSHOTS_HASH),
]

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_repeated_warm_use_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_repeated_warm_use_result_summary.txt"

# This is the production Normalizer's OWN OUTPUT_PATH constant (verified
# by direct grep of the currently installed file, SHA-pinned above,
# 2026-09-22), opened in "w" (truncate) mode by its own start() method --
# so reading it after each command reflects only THAT command.
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

# 1-indexed, inclusive. IDENTICAL range table to Checkpoints C1/C2/D1/
# D2's own (same reasoning: pure, read-only, structural DME-reading
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


class CheckpointF1Error(Exception):
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
# used by Checkpoints C1/C2/D1/D2, kept verbatim for internal
# consistency between checkpoints' witnesses).
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
                raise CheckpointF1Error(
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
    encoded byte string."""
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
    target -- identical to Checkpoints D1/D2's own excluded_witness_row(),
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
    sort_keys=True JSON serialization -- identical to Checkpoint D2's
    own `per_target_hash()`."""
    return hashlib.sha256(dumps_sorted(value).encode("utf-8")).hexdigest()


def compute_target_hashes(fingerprint_dict):
    """Given a captured {target_key: canonicalized_value} mapping,
    returns {target_key: per_target_hash(value)} -- the caller releases
    the raw dicts immediately after this call (D2-2 discipline)."""
    return dict((k, per_target_hash(v)) for k, v in fingerprint_dict.items())


def memory_snapshot():
    """Best-effort, stdlib-only (ctypes) Windows process memory
    snapshot -- diagnostic only, never affects Normalizer behavior, and
    never raises. Identical to Checkpoints D1-3/D2's own
    memory_snapshot()."""
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
# Safe, streaming, compact artifact writer (Checkpoint D1-3/D2-2's own
# correction, reused verbatim).
# ---------------------------------------------------------------------------

def write_json_atomic(final_path, data_obj):
    """Returns (ok, error_repr_or_None, reparsed_obj_or_None)."""
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


REQUIRED_EVIDENCE_KEYS = (
    "initial_state", "command_records", "final_responsiveness",
)


def verify_artifact_evidence(reparsed_obj):
    """Returns (ok, detail). Checks presence/completeness of the
    required COMPACT evidence fields for F1's own multi-command
    schema."""
    if reparsed_obj is None:
        return False, "reparsed artifact is None"
    missing_keys = [k for k in REQUIRED_EVIDENCE_KEYS if k not in reparsed_obj]
    if missing_keys:
        return False, "missing required evidence keys: %r" % (missing_keys,)
    initial_state = reparsed_obj.get("initial_state") or {}
    if len(initial_state.get("eligible_target_hashes") or {}) != 85:
        return False, "initial_state eligible_target_hashes count wrong: %d" % len(initial_state.get("eligible_target_hashes") or {})
    if len(initial_state.get("excluded_target_hashes") or {}) != 78:
        return False, "initial_state excluded_target_hashes count wrong: %d" % len(initial_state.get("excluded_target_hashes") or {})
    command_records = reparsed_obj.get("command_records") or []
    if len(command_records) != 4:
        return False, "expected exactly 4 command_records, found %d" % len(command_records)
    for rec in command_records:
        ordinal = rec.get("ordinal")
        if len(rec.get("eligible_target_hashes") or {}) != 85:
            return False, "command %r eligible_target_hashes count wrong: %d" % (ordinal, len(rec.get("eligible_target_hashes") or {}))
        if len(rec.get("excluded_target_hashes") or {}) != 78:
            return False, "command %r excluded_target_hashes count wrong: %d" % (ordinal, len(rec.get("excluded_target_hashes") or {}))
        recomputed_checksum = stable_hash([u"%s=%s" % (k, v) for k, v in (rec.get("eligible_target_hashes") or {}).items()])
        if recomputed_checksum != rec.get("eligible_hashes_checksum"):
            return False, "command %r eligible_hashes_checksum mismatch after round-trip" % (ordinal,)
        recomputed_excl_checksum = stable_hash([u"%s=%s" % (k, v) for k, v in (rec.get("excluded_target_hashes") or {}).items()])
        if recomputed_excl_checksum != rec.get("excluded_hashes_checksum"):
            return False, "command %r excluded_hashes_checksum mismatch after round-trip" % (ordinal,)
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
    "initial_state": {},
    "command_records": [],
    "final_responsiveness": {},
    "memory_snapshots": {},
}


def check(name, condition, detail=None):
    report["checks"].append({"name": name, "pass": bool(condition), "detail": repr(detail) if detail is not None else None})
    try:
        sys.stdout.write("[%s] %s%s\n" % ("PASS" if condition else "FAIL", name, ("" if detail is None else " -- %r" % (detail,))))
    except Exception:
        pass


main_window = None
production_bytes = None
fp_ns = None
capture_snapshot_explicit_fn = None
eligible_targets_of_interest = None
initial_excluded_keys = None
initial_all_target_keys = None

try:
    report["memory_snapshots"]["at_start"] = memory_snapshot()

    # --- 1. SHA verification, before anything else. ---
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
        raise CheckpointF1Error("One or more pre-flight SHA-256 checks failed -- refusing to proceed.")

    report["provenance"]["production_normalizer_sha256"] = production_sha
    report["provenance"]["canonical_master_sha256"] = master_sha

    # --- 2. Fixture verification: totals, shot3 sole-selected, Fox/Mia
    #        identities (extra rigor, matching C1/C2's own established
    #        practice). ---
    pre_witness, shots_by_name, witness_error = build_independent_witness()
    if witness_error is not None:
        raise CheckpointF1Error("Could not build independent witness: %s" % witness_error)

    report["fixture_totals"] = pre_witness["totals"]
    for key, expected_value in EXPECTED_TOTALS.items():
        actual_value = pre_witness["totals"].get(key)
        check("fixture.totals.%s_matches_required" % key, actual_value == expected_value, (actual_value, expected_value))

    selected_shot_names = sorted(set(t["shot_name"] for t in pre_witness["targets"] if t["shot_selected"]))
    check("fixture.selected_shot_set_is_exactly_shot3", selected_shot_names == [EXPECTED_SELECTED_SHOT_NAME], selected_shot_names)

    selected_target_rows = [
        t for t in pre_witness["targets"]
        if t["shot_name"] == EXPECTED_SELECTED_SHOT_NAME and t["category"] == "expected_selected_and_all_candidate"
    ]
    check("fixture.selected_shot_has_exactly_two_expected_targets", len(selected_target_rows) == 2, len(selected_target_rows))
    actual_selected_target_names = set(t["aset_name"] for t in selected_target_rows)
    check("fixture.expected_selected_target_set_is_exact", actual_selected_target_names == set(EXPECTED_SELECTED_TARGETS.keys()), sorted(actual_selected_target_names))
    for t in selected_target_rows:
        expected = EXPECTED_SELECTED_TARGETS.get(t["aset_name"])
        if expected is None:
            continue
        check("fixture.%s.model_name_matches" % t["aset_name"], t["model_name"] == expected["model_name"], t["model_name"])
        check("fixture.%s.control_count_matches" % t["aset_name"], t["control_count"] == expected["control_count"], t["control_count"])
        check("fixture.%s.vocabulary_hash_matches" % t["aset_name"], t["fold_vocabulary_hash"] == expected["fold_vocabulary_hash"], t["fold_vocabulary_hash"])

    report["selection_state_evidence"] = {"selected_shot_names": selected_shot_names}

    initial_eligible_rows = [t for t in pre_witness["targets"] if t["category"] != "excluded"]
    initial_excluded_rows = [t for t in pre_witness["targets"] if t["category"] == "excluded"]
    check("fixture.eligible_row_count_is_85", len(initial_eligible_rows) == 85, len(initial_eligible_rows))
    check("fixture.excluded_row_count_is_78", len(initial_excluded_rows) == 78, len(initial_excluded_rows))

    eligible_targets_of_interest = [(t["shot_name"], t["aset_name"]) for t in initial_eligible_rows]
    initial_eligible_keys = set(target_key(t) for t in initial_eligible_rows)
    initial_excluded_keys = set(target_key(t) for t in initial_excluded_rows)
    initial_all_target_keys = set(target_key(t) for t in pre_witness["targets"])
    del pre_witness

    # --- 3. Build the fingerprint-function namespace (extracted, SHA-
    #        pinned to THIS run's own production Normalizer file). ---
    all_lines = production_bytes.decode("ascii").splitlines()
    blocks = []
    for label, start, end in FINGERPRINT_FUNCTION_RANGES:
        blocks.append("\n".join(all_lines[start - 1:end]))
    combined_source = "\n\n".join(blocks)

    fp_ns = dict(FINGERPRINT_MODULE_CONSTANTS)
    fp_ns["hashlib"] = hashlib
    exec(compile(combined_source, "<checkpoint_f1_fingerprint_functions>", "exec"), fp_ns)
    check("fingerprint_functions.extracted_and_exec_ok", True)
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

    # --- 4. Initial (PRE-command-1) compact state -- bounded memory:
    #        raw dicts held only long enough to compute hashes. ---
    raw_initial_eligible = capture_all("INITIAL", eligible_targets_of_interest)
    check("fixture.initial_eligible_capture_count_is_85", len(raw_initial_eligible) == 85, len(raw_initial_eligible))
    initial_aggregate_hash = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in raw_initial_eligible.items()])
    initial_eligible_hashes = compute_target_hashes(raw_initial_eligible)
    del raw_initial_eligible

    raw_initial_excluded = dict((target_key(t), excluded_witness_row(t)) for t in initial_excluded_rows)
    del initial_excluded_rows
    initial_excluded_hashes = compute_target_hashes(raw_initial_excluded)
    del raw_initial_excluded

    check("fixture.initial_aggregate_hash_matches_expected", initial_aggregate_hash == EXPECTED_INITIAL_PRE_HASH, initial_aggregate_hash)

    report["initial_state"] = {
        "aggregate_hash": initial_aggregate_hash,
        "eligible_target_hashes": initial_eligible_hashes,
        "excluded_target_hashes": initial_excluded_hashes,
        "eligible_target_keys": sorted(initial_eligible_keys),
        "excluded_target_keys": sorted(initial_excluded_keys),
    }

    # --- HARD GATE: every check recorded above must pass BEFORE any
    #     invocation of the production Normalizer or scene mutation. ---
    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointF1Error(
            "STARTING-STATE / FIXTURE MISMATCH -- one or more required pre-flight or "
            "fixture-identity checks failed. Aborting BEFORE any invocation of the "
            "production Normalizer or scene mutation."
        )

    main_window = sfmApp.GetMainWindow()
    check("normalizer.main_window_available", main_window is not None)

    # Logical zero baseline: SFM was just restarted (operator instructed),
    # so the authority module has not yet been imported/used in this
    # process -- command 1's own delta is computed against this.
    previous_provider_counters = {
        "total_provider_opens": 0, "total_provider_closes": 0,
        "current_open_provider_count": 0, "peak_open_provider_count": 0,
        "active_cohort_id": None,
    }
    previous_eligible_hashes = initial_eligible_hashes
    previous_excluded_hashes = initial_excluded_hashes

    for ordinal, scope_label, expected_hash in COMMAND_SPECS:
        report["memory_snapshots"]["before_command_%d" % ordinal] = memory_snapshot()

        sys.stdout.write(
            "\n>>> Command %d/4: the integrated production Normalizer is about to run its "
            "own real Selected/All Shots dialog. Select '%s' and confirm. <<<\n\n"
            % (ordinal, scope_label)
        )

        command_start_time = time.time()
        prod_ns = {}
        run_started = False
        run_completed_cleanly = False
        try:
            # Raw, undecoded bytes -- the file's own line-1
            # "# -*- coding: ascii -*-" declaration makes compile() raise
            # if a decoded unicode string is passed instead (same class
            # of bug already hit and fixed in Checkpoint C2).
            exec(compile(production_bytes, "<installed_production_normalizer_cmd%d>" % ordinal, "exec"), prod_ns)
        except Exception as exc:
            anomaly("Command %d: production Normalizer execution raised: %r" % (ordinal, exc))
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
            sys.stdout.write("Command %d detected as active; waiting for completion...\n" % ordinal)
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
                "Command %d: no run-lock was ever observed active after executing the "
                "production Normalizer source -- this most likely means the operator "
                "cancelled the scope dialog." % ordinal
            )

        command_duration_seconds = time.time() - command_start_time

        check("command_%d.run_was_started" % ordinal, run_started)
        check("command_%d.run_completed_within_timeout" % ordinal, run_completed_cleanly if run_started else False)

        # --- Rebuild the witness fresh, to detect any target-set drift
        #     RELATIVE TO THE ORIGINAL FIXTURE. ---
        post_witness, _post_shots_by_name, post_witness_error = build_independent_witness()
        if post_witness_error is not None:
            anomaly("Command %d: could not rebuild post-run independent witness: %s" % (ordinal, post_witness_error))
            post_all_by_key = {}
        else:
            post_all_by_key = dict((target_key(t), t) for t in post_witness["targets"])
        del post_witness

        current_all_keys = set(post_all_by_key.keys())
        missing_vs_initial = sorted(initial_all_target_keys - current_all_keys)
        new_vs_initial = sorted(current_all_keys - initial_all_target_keys)
        current_eligible_keys_now = set(k for k, t in post_all_by_key.items() if t["category"] != "excluded")
        current_excluded_keys_now = set(k for k, t in post_all_by_key.items() if t["category"] == "excluded")
        reclassified_e2x = sorted(initial_eligible_keys & current_excluded_keys_now)
        reclassified_x2e = sorted(initial_excluded_keys & current_eligible_keys_now)

        target_set_diff_vs_initial = {
            "missing_targets_entirely": missing_vs_initial,
            "new_targets_entirely": new_vs_initial,
            "reclassified_eligible_to_excluded": reclassified_e2x,
            "reclassified_excluded_to_eligible": reclassified_x2e,
        }
        check("command_%d.no_target_set_drift_vs_initial_fixture" % ordinal,
              not missing_vs_initial and not new_vs_initial and not reclassified_e2x and not reclassified_x2e,
              target_set_diff_vs_initial)

        # --- Compact capture: raw dicts held only transiently. ---
        raw_eligible = capture_all("CMD%d" % ordinal, eligible_targets_of_interest)
        check("command_%d.eligible_capture_count_is_85" % ordinal, len(raw_eligible) == 85, len(raw_eligible))
        aggregate_hash = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in raw_eligible.items()])
        current_eligible_hashes = compute_target_hashes(raw_eligible)
        del raw_eligible

        raw_excluded = {}
        for key in sorted(initial_excluded_keys):
            t = post_all_by_key.get(key)
            if t is not None:
                raw_excluded[key] = excluded_witness_row(t)
        del post_all_by_key
        current_excluded_hashes = compute_target_hashes(raw_excluded)
        del raw_excluded

        aggregate_matches_expected = bool(aggregate_hash == expected_hash)
        check("command_%d.aggregate_hash_matches_expected" % ordinal, aggregate_matches_expected, aggregate_hash)

        changed_keys = sorted(k for k in current_eligible_hashes if current_eligible_hashes[k] != previous_eligible_hashes.get(k))
        unchanged_keys = sorted(k for k in current_eligible_hashes if current_eligible_hashes[k] == previous_eligible_hashes.get(k))
        excluded_changed_keys = sorted(k for k in current_excluded_hashes if current_excluded_hashes[k] != previous_excluded_hashes.get(k))

        # --- Authority runtime evidence (existing qualified
        #     diagnostics only -- same technique as Checkpoint C2/D2). ---
        authority_evidence = {}
        current_provider_counters = dict(previous_provider_counters)
        current_outstanding_leases = None
        try:
            authority_runtime = prod_ns.get("authority_runtime")
            authority_evidence["module_binding_present"] = authority_runtime is not None
            if authority_runtime is not None:
                try:
                    authority_evidence["runtime_api_version"] = authority_runtime.RUNTIME_API_VERSION
                except Exception as exc:
                    authority_evidence["runtime_api_version_error"] = repr(exc)
                try:
                    authority_evidence["runtime_build_id"] = authority_runtime.RUNTIME_BUILD_ID
                except Exception as exc:
                    authority_evidence["runtime_build_id_error"] = repr(exc)
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
                        current_provider_counters = broker.provider_counters()
                        authority_evidence["provider_counters"] = current_provider_counters
                    except Exception as exc:
                        authority_evidence["provider_counters_error"] = repr(exc)
                    try:
                        current_outstanding_leases = broker.outstanding_lease_count()
                        authority_evidence["outstanding_lease_count"] = current_outstanding_leases
                    except Exception as exc:
                        authority_evidence["outstanding_lease_count_error"] = repr(exc)
                except Exception as exc:
                    authority_evidence["broker_query_error"] = repr(exc)
        except Exception as exc:
            authority_evidence["capture_error"] = repr(exc)
            anomaly("Command %d: authority runtime evidence capture raised: %r" % (ordinal, exc))

        opens_delta = current_provider_counters.get("total_provider_opens", 0) - previous_provider_counters.get("total_provider_opens", 0)
        closes_delta = current_provider_counters.get("total_provider_closes", 0) - previous_provider_counters.get("total_provider_closes", 0)
        authority_evidence["provider_opens_delta_this_command"] = opens_delta
        authority_evidence["provider_closes_delta_this_command"] = closes_delta

        check("command_%d.authority_broker_ready" % ordinal, authority_evidence.get("get_state") == "READY", authority_evidence.get("get_state"))
        check("command_%d.authority_canonical" % ordinal, authority_evidence.get("is_canonical") is True, authority_evidence.get("is_canonical"))
        check("command_%d.zero_outstanding_leases_after" % ordinal, current_outstanding_leases == 0, current_outstanding_leases)
        check("command_%d.zero_current_open_providers_after" % ordinal, current_provider_counters.get("current_open_provider_count") == 0, current_provider_counters.get("current_open_provider_count"))
        check("command_%d.provider_lifecycle_balanced_this_command" % ordinal, opens_delta == closes_delta, (opens_delta, closes_delta))
        check("command_%d.no_stale_active_cohort" % ordinal, current_provider_counters.get("active_cohort_id") is None, current_provider_counters.get("active_cohort_id"))

        # --- Native-protection evidence (existing qualified log, "w"
        #     truncated fresh by THIS command's own start() method). ---
        native_evidence = {}
        try:
            with open(NORMALIZER_LOG_PATH, "rb") as f:
                log_bytes = f.read()
            log_text = log_bytes.decode("ascii", "replace")
            native_evidence["log_size_bytes"] = len(log_bytes)
            native_evidence["contains_NATIVE_GUARDS_PASS"] = ("NATIVE_GUARDS = PASS" in log_text)
            native_evidence["contains_NATIVE_REBUILD_RETURNED_PASS"] = ("NATIVE_REBUILD_RETURNED = PASS" in log_text)
            del log_bytes, log_text
        except Exception as exc:
            native_evidence["log_read_ok"] = False
            native_evidence["log_read_error"] = repr(exc)
            anomaly("Command %d: could not read production Normalizer log for native-protection evidence: %r" % (ordinal, exc))

        check("command_%d.native_guards_pass" % ordinal, native_evidence.get("contains_NATIVE_GUARDS_PASS") is True, native_evidence.get("contains_NATIVE_GUARDS_PASS"))
        check("command_%d.native_rebuild_returned_pass" % ordinal, native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS") is True, native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS"))

        memory_after_cleanup = memory_snapshot()
        report["memory_snapshots"]["after_command_%d_cleanup" % ordinal] = memory_after_cleanup

        command_record = {
            "ordinal": ordinal,
            "scope_requested": scope_label,
            "duration_seconds": command_duration_seconds,
            "run_started": run_started,
            "run_completed_cleanly": run_completed_cleanly,
            "aggregate_hash": aggregate_hash,
            "expected_aggregate_hash": expected_hash,
            "aggregate_hash_matches_expected": aggregate_matches_expected,
            "eligible_target_hashes": current_eligible_hashes,
            "excluded_target_hashes": current_excluded_hashes,
            "eligible_hashes_checksum": stable_hash([u"%s=%s" % (k, v) for k, v in current_eligible_hashes.items()]),
            "excluded_hashes_checksum": stable_hash([u"%s=%s" % (k, v) for k, v in current_excluded_hashes.items()]),
            "changed_target_keys_from_previous": changed_keys,
            "unchanged_target_keys_from_previous": unchanged_keys,
            "excluded_changed_keys_from_previous": excluded_changed_keys,
            "target_set_diff_vs_initial": target_set_diff_vs_initial,
            "authority_lifecycle": authority_evidence,
            "native_protection": native_evidence,
            "memory_after_cleanup": memory_after_cleanup,
        }
        report["command_records"].append(command_record)

        previous_eligible_hashes = current_eligible_hashes
        previous_excluded_hashes = current_excluded_hashes
        previous_provider_counters = current_provider_counters

    del fp_ns, capture_snapshot_explicit_fn

    # --- Final responsiveness check: simple, non-destructive, real. ---
    report["memory_snapshots"]["before_final_responsiveness_check"] = memory_snapshot()
    final_responsiveness = {}
    try:
        QtCore.QCoreApplication.processEvents()
        time.sleep(0.1)
        QtCore.QCoreApplication.processEvents()
        final_responsiveness["main_window_available"] = bool(sfmApp.GetMainWindow() is not None)
        final_responsiveness["document_still_accessible"] = bool(sfmApp.HasDocument())
        final_responsiveness["events_processed_ok"] = True
    except Exception as exc:
        final_responsiveness["events_processed_ok"] = False
        final_responsiveness["error"] = repr(exc)
        anomaly("Final responsiveness check raised: %r" % exc)
    report["final_responsiveness"] = final_responsiveness
    check("final.sfm_main_window_available", final_responsiveness.get("main_window_available") is True, final_responsiveness.get("main_window_available"))
    check("final.sfm_document_still_accessible", final_responsiveness.get("document_still_accessible") is True, final_responsiveness.get("document_still_accessible"))
    check("final.events_processed_ok", final_responsiveness.get("events_processed_ok") is True, final_responsiveness.get("events_processed_ok"))

    report["memory_snapshots"]["after_all_commands"] = memory_snapshot()

except CheckpointF1Error as gate_exc:
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
all_commands_started = bool(
    len(report["command_records"]) == 4
    and all(rec.get("run_started") for rec in report["command_records"])
)
runtime_checks_passed = bool(all_checks_passed and completed_without_exception and all_commands_started)
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
    # Degraded fallback: drop the (largest) per-target hash maps from
    # each command record, keeping aggregate hashes, counts, lifecycle
    # evidence, checks, provenance, and anomalies. CRITICAL (D2-2 fix,
    # reused): overall_pass/artifact_write_verified are forced False
    # EXPLICITLY on the degraded copy, never merely inherited from
    # whatever `report` held at snapshot time.
    degraded_report = dict(report)
    degraded_command_records = []
    for rec in report["command_records"]:
        degraded_rec = dict(rec)
        degraded_rec.pop("eligible_target_hashes", None)
        degraded_rec.pop("excluded_target_hashes", None)
        degraded_command_records.append(degraded_rec)
    degraded_report["command_records"] = degraded_command_records
    degraded_report.pop("initial_state", None)
    degraded_report["degraded_artifact"] = True
    degraded_report["overall_pass"] = False
    degraded_report["artifact_write_verified"] = False
    degraded_report["degraded_reason"] = (
        "Per-target hash maps and initial_state omitted because the complete compact "
        "artifact write failed (%s). This degraded fallback preserves every mechanical "
        "check, aggregate hash, count, lifecycle evidence field, provenance field, and "
        "anomaly so evidence is never left as a misleading zero-byte file. overall_pass "
        "and artifact_write_verified are forced False here regardless of the live "
        "report's own state at snapshot time." % (report["json_write_error"],)
    )
    fallback_ok, fallback_error, _r3 = write_json_atomic(JSON_OUTPUT_PATH, degraded_report)
    _r3 = None
    report["degraded_fallback_written"] = fallback_ok
    if fallback_ok:
        json_write_ok = True
    else:
        report["json_write_error"] = "%s ; degraded fallback also failed: %s" % (report["json_write_error"], fallback_error)
    report["overall_pass"] = False

summary_lines = []
summary_lines.append("SFM CHECKPOINT F1 -- REPEATED / WARM-USE STABILITY")
summary_lines.append("started_at=%s  finished_at=%s" % (report["started_at"], report["finished_at"]))
if report.get("gate_failure"):
    summary_lines.append("")
    summary_lines.append("*** GATE FAILURE: aborted BEFORE any production Normalizer invocation or scene mutation. ***")
summary_lines.append("")
summary_lines.append("--- CHECKS ---")
for c in report["checks"]:
    summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
summary_lines.append("")
summary_lines.append("--- COMMAND SUMMARY ---")
for rec in report["command_records"]:
    summary_lines.append(
        "[cmd %d] scope=%r duration=%.2fs aggregate_hash_matches_expected=%r changed=%d unchanged=%d excluded_changed=%d"
        % (rec["ordinal"], rec["scope_requested"], rec["duration_seconds"], rec["aggregate_hash_matches_expected"],
           len(rec["changed_target_keys_from_previous"]), len(rec["unchanged_target_keys_from_previous"]),
           len(rec["excluded_changed_keys_from_previous"]))
    )
summary_lines.append("")
summary_lines.append("initial_aggregate_hash=%r" % (report.get("initial_state") or {}).get("aggregate_hash"))
summary_lines.append("final_responsiveness=%r" % report.get("final_responsiveness"))
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
    summary_lines.append("*** DEGRADED ARTIFACT: per-target hash maps/initial_state were omitted because the ***")
    summary_lines.append("*** complete compact artifact write failed. degraded_fallback_written=%r ***" % report.get("degraded_fallback_written"))
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
        "\nCheckpoint F1 reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r, error=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok, summary_write_error)
    )
    sys.stdout.write("\nDO NOT SAVE. Restart SFM to discard this repeated-command mutation.\n")
except Exception:
    pass
