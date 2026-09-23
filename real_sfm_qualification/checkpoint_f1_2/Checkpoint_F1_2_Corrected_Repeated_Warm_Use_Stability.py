# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint F1-2: Corrected Repeated /
Warm-Use Stability.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: **THIS CHECKPOINT MUTATES THE SCENE, REPEATEDLY.** It
invokes the REAL, INSTALLED, ACCEPTED, INTEGRATED production Normalizer
FOUR separate times in a row, in ONE continuous SFM process, without
restarting SFM between commands. Do not save afterward.

Purpose:
  F1-1 (the original four-command design) crashed the real SFM process
  during command 3. Diagnostic F1-R1 then produced DECISIVE ATTRIBUTION
  evidence: production's own command boundaries showed ZERO retained
  private/pagefile/VAS growth (command 2: identical CP0_COMMAND_START and
  FINAL_REPORT_ENTRY figures, 6.430s elapsed), while the QUALIFICATION
  HARNESS's own post-command semantic verification -- which, even in the
  "minimal-footprint" F1-R1 design, still transiently captured the FULL
  85-eligible-target semantic tree on every command merely to compute an
  aggregate hash -- added ~76.15 MiB that did not return after `del` +
  `gc.collect()`. A follow-up static trace
  (`F1-R1_SEMANTIC_CAPTURE_STATIC_PROOF.md`) plus an offline empirical test
  under the real embedded Python 2.7.5
  (`test_allocator_highwater_retention.py`) confirmed this is a THIRD,
  previously-undistinguished retention category -- Python/CRT allocator
  high-water retention (freed pymalloc arenas are not returned to the OS
  merely because the Python objects that used them became unreachable and
  were swept by gc.collect()) -- distinct from live-reference retention
  (ruled out) and cyclic garbage (already fixed, and still insufficient).

  F1-2 corrects this: it no longer inserts ANY whole-85-eligible-target
  semantic capture BETWEEN production commands. C1/C2/D1/D2 already
  established full historical-vs-integrated semantic equivalence for both
  Selected Shots and All Shots; F1-2 is about repeated-USE stability, not
  re-proving full equivalence after every intermediate command.

Command sequence (restored to all four, unlike F1-R1's deliberately
truncated three):
  1. Selected Shots
  2. Selected Shots again
  3. All Shots
  4. All Shots again

Between-command evidence (commands 1-4) is now genuinely lightweight:
  - production command completion evidence (started/completed cleanly);
  - production's OWN pre-existing CONTEXTUALIZER_RESOURCE_CHECKPOINT log
    diagnostic, parsed (not reinstrumented) -- first/last checkpoint per
    command, including free VAS, largest free region, private/pagefile;
  - broker/provider/lease counters and source/generation identity
    (existing authority_runtime diagnostics, same as every earlier
    checkpoint);
  - for Selected-Shots commands (1, 2) ONLY: the two Selected targets'
    (Fox, Mia) own semantic hashes -- captured via the SAME capture_all()
    helper every earlier checkpoint uses, but given a target list
    containing ONLY those two targets, never the 85-target eligible
    fixture. This does NOT traverse the whole fixture;
  - lightweight fixture identity/count checks (a bounded structural
    witness rebuild -- shot/target classification only, no rig-tree walk)
    to detect target-set drift, for all four commands;
  - explicit `del prod_ns` (and any other diagnostic temporaries) plus
    `gc.collect()` before the next production command, exactly as F1-R1's
    own correction already established.

For Selected commands specifically: command 1 verifies Fox/Mia's own
structural identity (model name, control count, fold-vocabulary hash --
the same fields this whole project has pinned since Checkpoint B) via the
bounded witness, plus that their semantic capture succeeded (2/2, no
anomaly). This project has never pinned an external "Fox-alone" or
"Mia-alone" semantic hash constant (only 85-target AGGREGATE hashes, which
by definition require all 85 targets and are therefore exactly the
operation being eliminated here) -- so command 1 does not claim to match
a pre-pinned Fox/Mia semantic hash. Command 2 instead proves Selected
idempotence directly and self-containedly: its own captured Fox/Mia
hashes must be EXACTLY IDENTICAL to command 1's own captured Fox/Mia
hashes. This requires no external pin and no 85-target scan.

For All-Shots commands (3, 4): no external semantic capture of any kind.
Only production completion evidence, lifecycle evidence, native-protection
evidence, resource-checkpoint evidence, and the bounded structural
witness's own totals (target inventory counts/source identity).

Only AFTER command 4 completes -- when no further production command
depends on remaining address-space headroom -- does this script perform
the one, single, full external 85-eligible/78-excluded semantic
verification, checking the final aggregate hash against the already-
qualified All-Shots state (`299cbba3...`) and the final target identities
against the already-qualified 85/78 sets. No production command runs
after this heavy verification.

Do not restart SFM between commands. Do not alter the scene between
commands.

Output:
  Two files are written to C:\\Users\\Public\\Documents\\, rewritten
  atomically after EVERY command boundary (not only at the end):
    sfm_checkpoint_f1_2_result.json
    sfm_checkpoint_f1_2_result_summary.txt
  Plus a per-command preserved copy of production's own log:
    sfm_checkpoint_f1_2_production_log_command{1,2,3,4}.txt

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
# Pinned identities (identical to F1-1/F1-R1's own pinned constants).
# ---------------------------------------------------------------------------

EXPECTED_PRODUCTION_NORMALIZER_SHA256 = (
    "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"
)
EXPECTED_CANONICAL_MASTER_SHA256 = (
    "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
)
EXPECTED_INITIAL_PRE_HASH = (
    "eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0"
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

COMPACT_SELECTED_TARGET_KEYS = [
    u"%s|%s" % (EXPECTED_SELECTED_SHOT_NAME, aset_name)
    for aset_name in sorted(EXPECTED_SELECTED_TARGETS.keys())
]
COMPACT_SELECTED_TARGETS_OF_INTEREST = [
    (EXPECTED_SELECTED_SHOT_NAME, aset_name)
    for aset_name in sorted(EXPECTED_SELECTED_TARGETS.keys())
]

SELECTED_ORDINALS = frozenset([1, 2])
ALLSHOTS_ORDINALS = frozenset([3, 4])

# (ordinal, operator-facing scope label). No per-command expected aggregate
# hash -- no command performs an 85-target aggregate capture any more; the
# ONLY aggregate-hash check in this whole script happens once, after the
# loop, in the final heavyweight verification.
COMMAND_SPECS = [
    (1, u"Selected Shots"),
    (2, u"Selected Shots"),
    (3, u"All Shots"),
    (4, u"All Shots"),
]

JSON_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_2_result.json"
SUMMARY_OUTPUT_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_2_result_summary.txt"
PER_COMMAND_LOG_PRESERVE_TEMPLATE = (
    "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_2_production_log_command%d.txt"
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


class CheckpointF12Error(Exception):
    pass


ANOMALIES = []


def anomaly(message):
    ANOMALIES.append(message)
    try:
        sys.stdout.write("ANOMALY: %s\n" % message)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Checkpoint-B-style fact/classification helpers (verbatim).
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
                raise CheckpointF12Error(
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
    """Streaming implementation (D1-3's own correction, reused
    verbatim)."""
    hasher = hashlib.sha256()
    for index, item in enumerate(sorted(values)):
        if index:
            hasher.update(b"\n")
        hasher.update(item.encode("utf-8"))
    return hasher.hexdigest()


def build_independent_witness():
    """Re-derives the same shot/target/eligibility/classification witness
    Checkpoint B independently established, fresh from the live document
    -- BOUNDED: control-name lists/sets per target, never rig-tree/
    attribute-value data. Returns (witness_dict, shots_by_name, error_or_None)."""
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
    """Best-effort, stdlib-only (ctypes) Windows process memory
    snapshot -- diagnostic only, never affects Normalizer behavior, and
    never raises."""
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
# Production's OWN existing CONTEXTUALIZER_RESOURCE_CHECKPOINT log-line
# diagnostic -- parsed here, never reinstrumented (reused verbatim from
# F1-R1).
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Safe, streaming, compact artifact writer (D1-3/D2-2/F1/F1-R1's own
# correction, reused verbatim).
# ---------------------------------------------------------------------------

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


def copy_bytes_atomic(final_path, raw_bytes):
    return write_text_atomic(final_path, raw_bytes)


REQUIRED_EVIDENCE_KEYS = (
    "initial_state", "command_records", "final_responsiveness",
)


def verify_artifact_evidence(reparsed_obj, expected_command_count, expect_final_verification):
    """Returns (ok, detail). Tolerates a PARTIAL command_records list
    (this artifact is rewritten incrementally after every command
    boundary). Structurally enforces the corrected design: ordinals 1-2
    carry ONLY a 2-entry selected_target_hashes map (never a full 85/78
    hash map); ordinals 3-4 carry NO hash-map field at all; the one full
    85/78 verification lives ONLY in the separate top-level
    final_full_verification key, present only once command 4 has
    completed."""
    if reparsed_obj is None:
        return False, "reparsed artifact is None"
    missing_keys = [k for k in REQUIRED_EVIDENCE_KEYS if k not in reparsed_obj]
    if missing_keys:
        return False, "missing required evidence keys: %r" % (missing_keys,)
    command_records = reparsed_obj.get("command_records") or []
    if len(command_records) > expected_command_count:
        return False, "found MORE command_records (%d) than commands attempted so far (%d)" % (
            len(command_records), expected_command_count,
        )
    for rec in command_records:
        ordinal = rec.get("ordinal")
        has_selected = "selected_target_hashes" in rec
        has_full = ("eligible_target_hashes" in rec) or ("excluded_target_hashes" in rec)
        if has_full:
            return False, "command %r illegally carries a full eligible/excluded hash map -- corrected design forbids this on any command record" % (ordinal,)
        if ordinal in SELECTED_ORDINALS:
            compact = rec.get("selected_target_hashes") or {}
            if set(compact.keys()) != set(COMPACT_SELECTED_TARGET_KEYS):
                return False, "command %r selected_target_hashes key set wrong: %r" % (ordinal, sorted(compact.keys()))
            if ordinal == 2:
                if "selected_target_hashes_match_command_1" not in rec:
                    return False, "command 2 missing selected_target_hashes_match_command_1"
        else:
            if has_selected:
                return False, "command %r (All Shots) illegally carries selected_target_hashes -- corrected design forbids any external semantic capture on All-Shots commands" % (ordinal,)
    if expect_final_verification:
        final_verification = reparsed_obj.get("final_full_verification")
        if not final_verification:
            return False, "final_full_verification missing but expected"
        if len(final_verification.get("eligible_target_hashes") or {}) != 85:
            return False, "final_full_verification eligible_target_hashes count wrong: %d" % len(final_verification.get("eligible_target_hashes") or {})
        if len(final_verification.get("excluded_target_hashes") or {}) != 78:
            return False, "final_full_verification excluded_target_hashes count wrong: %d" % len(final_verification.get("excluded_target_hashes") or {})
        recomputed_checksum = stable_hash(
            [u"%s=%s" % (k, v) for k, v in (final_verification.get("eligible_target_hashes") or {}).items()]
        )
        if recomputed_checksum != final_verification.get("eligible_hashes_checksum"):
            return False, "final_full_verification eligible_hashes_checksum mismatch after round-trip"
        recomputed_excl_checksum = stable_hash(
            [u"%s=%s" % (k, v) for k, v in (final_verification.get("excluded_target_hashes") or {}).items()]
        )
        if recomputed_excl_checksum != final_verification.get("excluded_hashes_checksum"):
            return False, "final_full_verification excluded_hashes_checksum mismatch after round-trip"
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
    "final_full_verification": None,
    "final_responsiveness": {},
    "memory_snapshots": {},
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
initial_excluded_keys = None
initial_excluded_rows = None
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
        raise CheckpointF12Error("One or more pre-flight SHA-256 checks failed -- refusing to proceed.")

    report["provenance"]["production_normalizer_sha256"] = production_sha
    report["provenance"]["canonical_master_sha256"] = master_sha

    # --- 2. Fixture verification. ---
    pre_witness, shots_by_name, witness_error = build_independent_witness()
    if witness_error is not None:
        raise CheckpointF12Error("Could not build independent witness: %s" % witness_error)

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

    # --- 3. Build the fingerprint-function namespace. ---
    all_lines = production_bytes.decode("ascii").splitlines()
    blocks = []
    for label, start, end in FINGERPRINT_FUNCTION_RANGES:
        blocks.append("\n".join(all_lines[start - 1:end]))
    combined_source = "\n\n".join(blocks)

    fp_ns = dict(FINGERPRINT_MODULE_CONSTANTS)
    fp_ns["hashlib"] = hashlib
    exec(compile(combined_source, "<checkpoint_f1_2_fingerprint_functions>", "exec"), fp_ns)
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
        """Captures ONLY the targets in targets_of_interest_local -- never
        implicitly the whole 85-target fixture. Callers control the cost
        entirely by what list they pass."""
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

    # --- 4. Initial (PRE-command-1) state -- the ONLY full-85 capture
    #        before the command loop begins (it does not sit BETWEEN two
    #        production commands, so it cannot contribute to the
    #        between-command retention pattern that motivated this
    #        correction). Only the aggregate hash and the compact Fox/Mia
    #        subset are persisted. ---
    raw_initial_eligible = capture_all("INITIAL", eligible_targets_of_interest)
    check("fixture.initial_eligible_capture_count_is_85", len(raw_initial_eligible) == 85, len(raw_initial_eligible))
    initial_aggregate_hash = stable_hash([u"%s=%s" % (k, dumps_sorted(v)) for k, v in raw_initial_eligible.items()])
    initial_eligible_hashes_full = compute_target_hashes(raw_initial_eligible)
    del raw_initial_eligible

    check("fixture.initial_aggregate_hash_matches_expected", initial_aggregate_hash == EXPECTED_INITIAL_PRE_HASH, initial_aggregate_hash)

    report["initial_state"] = {
        "aggregate_hash": initial_aggregate_hash,
        "selected_target_hashes": dict(
            (k, v) for k, v in initial_eligible_hashes_full.items() if k in COMPACT_SELECTED_TARGET_KEYS
        ),
        "eligible_target_keys": sorted(initial_eligible_keys),
        "excluded_target_keys": sorted(initial_excluded_keys),
    }
    del initial_eligible_hashes_full

    fixture_gate_passed = all(c["pass"] for c in report["checks"])
    if not fixture_gate_passed:
        raise CheckpointF12Error(
            "STARTING-STATE / FIXTURE MISMATCH -- one or more required pre-flight or "
            "fixture-identity checks failed. Aborting BEFORE any invocation of the "
            "production Normalizer or scene mutation."
        )

    main_window = sfmApp.GetMainWindow()
    check("normalizer.main_window_available", main_window is not None)

    write_rolling_evidence()

    previous_provider_counters = {
        "total_provider_opens": 0, "total_provider_closes": 0,
        "current_open_provider_count": 0, "peak_open_provider_count": 0,
        "active_cohort_id": None,
    }
    previous_selected_target_hashes = None

    for ordinal, scope_label in COMMAND_SPECS:
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

        # --- Read production's own log ONCE per command: native-
        #     protection markers, existing resource-checkpoint diagnostic,
        #     preserve a byte-for-byte copy. ---
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

            preserve_path = PER_COMMAND_LOG_PRESERVE_TEMPLATE % ordinal
            preserve_ok, preserve_err = copy_bytes_atomic(preserve_path, log_bytes)
            if not preserve_ok:
                anomaly("Command %d: could not preserve a copy of the production log: %s" % (ordinal, preserve_err))
            del log_bytes, log_text
        except Exception as exc:
            native_evidence["log_read_ok"] = False
            native_evidence["log_read_error"] = repr(exc)
            anomaly("Command %d: could not read production Normalizer log for evidence: %r" % (ordinal, exc))

        check("command_%d.native_guards_pass" % ordinal, native_evidence.get("contains_NATIVE_GUARDS_PASS") is True, native_evidence.get("contains_NATIVE_GUARDS_PASS"))
        check("command_%d.native_rebuild_returned_pass" % ordinal, native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS") is True, native_evidence.get("contains_NATIVE_REBUILD_RETURNED_PASS"))
        check("command_%d.production_final_report_entry_reached" % ordinal, resource_checkpoint_summary.get("final_report_entry_reached") is True, resource_checkpoint_summary.get("final_report_entry_reached"))

        # --- Bounded structural witness (no rig-tree walk) for target-set
        #     drift + totals -- cheap, safe for every command. ---
        post_witness, _post_shots_by_name, post_witness_error = build_independent_witness()
        if post_witness_error is not None:
            anomaly("Command %d: could not rebuild post-run independent witness: %s" % (ordinal, post_witness_error))
            post_all_by_key = {}
            post_totals = {}
        else:
            post_all_by_key = dict((target_key(t), t) for t in post_witness["targets"])
            post_totals = post_witness["totals"]
        del post_witness

        current_all_keys = set(post_all_by_key.keys())
        missing_vs_initial = sorted(initial_all_target_keys - current_all_keys)
        new_vs_initial = sorted(current_all_keys - initial_all_target_keys)
        current_eligible_keys_now = set(k for k, t in post_all_by_key.items() if t["category"] != "excluded")
        current_excluded_keys_now = set(k for k, t in post_all_by_key.items() if t["category"] == "excluded")
        reclassified_e2x = sorted(initial_eligible_keys & current_excluded_keys_now)
        reclassified_x2e = sorted(initial_excluded_keys & current_eligible_keys_now)
        del post_all_by_key

        target_set_diff_vs_initial = {
            "missing_targets_entirely": missing_vs_initial,
            "new_targets_entirely": new_vs_initial,
            "reclassified_eligible_to_excluded": reclassified_e2x,
            "reclassified_excluded_to_eligible": reclassified_x2e,
        }
        check("command_%d.no_target_set_drift_vs_initial_fixture" % ordinal,
              not missing_vs_initial and not new_vs_initial and not reclassified_e2x and not reclassified_x2e,
              target_set_diff_vs_initial)
        for key, expected_value in EXPECTED_TOTALS.items():
            check("command_%d.totals.%s_matches_required" % (ordinal, key), post_totals.get(key) == expected_value, (post_totals.get(key), expected_value))

        command_record = {
            "ordinal": ordinal,
            "scope_requested": scope_label,
            "duration_seconds": command_duration_seconds,
            "run_started": run_started,
            "run_completed_cleanly": run_completed_cleanly,
            "target_set_diff_vs_initial": target_set_diff_vs_initial,
            "fixture_totals_snapshot": post_totals,
            "native_protection": native_evidence,
            "production_resource_checkpoints": resource_checkpoint_summary,
        }

        if ordinal in SELECTED_ORDINALS:
            # --- ONLY the two Selected targets -- never the 85-target
            #     fixture. This is the corrected design's central fix. ---
            raw_selected = capture_all("CMD%d_SELECTED" % ordinal, COMPACT_SELECTED_TARGETS_OF_INTEREST)
            check("command_%d.selected_capture_count_is_2" % ordinal, len(raw_selected) == 2, len(raw_selected))
            current_selected_hashes = compute_target_hashes(raw_selected)
            del raw_selected
            command_record["selected_target_hashes"] = current_selected_hashes

            if ordinal == 1:
                # Structural identity re-check (bounded witness, no rig
                # walk) -- this project has never pinned an external
                # Fox-alone/Mia-alone SEMANTIC hash (only 85-target
                # AGGREGATE hashes, which by definition require the whole
                # fixture); "reaches known qualified state" is therefore
                # verified as: structural identity intact + capture
                # succeeded cleanly.
                fresh_selected_rows, _sbn, fresh_err = build_independent_witness()
                if fresh_err is None:
                    fresh_by_name = dict(
                        (t["aset_name"], t) for t in fresh_selected_rows["targets"]
                        if t["shot_name"] == EXPECTED_SELECTED_SHOT_NAME
                    )
                    del fresh_selected_rows
                    for aset_name, expected in EXPECTED_SELECTED_TARGETS.items():
                        row = fresh_by_name.get(aset_name)
                        check(
                            "command_1.%s.structural_identity_matches_expected" % aset_name,
                            bool(row and row["model_name"] == expected["model_name"]
                                 and row["control_count"] == expected["control_count"]
                                 and row["fold_vocabulary_hash"] == expected["fold_vocabulary_hash"]),
                            row,
                        )
                    del fresh_by_name
            else:
                matches_command_1 = bool(
                    previous_selected_target_hashes is not None
                    and current_selected_hashes == previous_selected_target_hashes
                )
                command_record["selected_target_hashes_match_command_1"] = matches_command_1
                check("command_2.selected_target_hashes_match_command_1_exactly", matches_command_1,
                      (current_selected_hashes, previous_selected_target_hashes))
            previous_selected_target_hashes = current_selected_hashes
        # else: ordinal in ALLSHOTS_ORDINALS -- NO external semantic
        #     capture of any kind. Only the evidence already gathered
        #     above (production/lifecycle/native/resource-checkpoint/
        #     bounded-witness-totals).

        # --- Authority runtime evidence (existing qualified
        #     diagnostics only). ---
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

        command_record["authority_lifecycle"] = authority_evidence
        previous_provider_counters = current_provider_counters

        # --- Drop this command's own exec namespace and force a
        #     collection BEFORE the next production command. ---
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
        memory_after_collect = memory_snapshot()
        command_record["harness_memory_after_gc_collect"] = memory_after_collect
        report["memory_snapshots"]["after_command_%d_gc_collect" % ordinal] = memory_after_collect

        report["command_records"].append(command_record)
        write_rolling_evidence()

    # --- Only AFTER command 4: the ONE full 85-eligible/78-excluded
    #     semantic verification. No production command depends on
    #     remaining headroom past this point. ---
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

    # --- Final responsiveness check. ---
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

except CheckpointF12Error as gate_exc:
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

all_checks_passed = all(c["pass"] for c in report["checks"]) if report["checks"] else False
completed_without_exception = not any(
    a.startswith("UNHANDLED TOP-LEVEL EXCEPTION") for a in ANOMALIES
)
all_commands_started = bool(
    len(report["command_records"]) == len(COMMAND_SPECS)
    and all(rec.get("run_started") for rec in report["command_records"])
)
final_verification_present = bool(report.get("final_full_verification"))
runtime_checks_passed = bool(
    all_checks_passed and completed_without_exception and all_commands_started and final_verification_present
)
report["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

evidence_expected = runtime_checks_passed

report["overall_pass"] = False
report["artifact_write_verified"] = False
report["artifact_evidence_detail"] = None
report["json_write_error"] = None

write1_ok, write1_error, reparsed1 = write_json_atomic(JSON_OUTPUT_PATH, report)

if evidence_expected:
    if write1_ok:
        evidence_ok, evidence_detail = verify_artifact_evidence(reparsed1, len(COMMAND_SPECS), True)
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
    degraded_report = dict(report)
    degraded_command_records = []
    for rec in report["command_records"]:
        degraded_rec = dict(rec)
        degraded_rec.pop("selected_target_hashes", None)
        degraded_command_records.append(degraded_rec)
    degraded_report["command_records"] = degraded_command_records
    if degraded_report.get("final_full_verification"):
        degraded_final = dict(degraded_report["final_full_verification"])
        degraded_final.pop("eligible_target_hashes", None)
        degraded_final.pop("excluded_target_hashes", None)
        degraded_report["final_full_verification"] = degraded_final
    degraded_report.pop("initial_state", None)
    degraded_report["degraded_artifact"] = True
    degraded_report["overall_pass"] = False
    degraded_report["artifact_write_verified"] = False
    degraded_report["degraded_reason"] = (
        "Per-target hash maps and initial_state omitted because the complete compact "
        "artifact write failed (%s). overall_pass and artifact_write_verified are forced "
        "False here regardless of the live report's own state at snapshot time." % (report["json_write_error"],)
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
summary_lines.append("SFM CHECKPOINT F1-2 -- CORRECTED REPEATED / WARM-USE STABILITY")
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
    rc = rec.get("production_resource_checkpoints") or {}
    summary_lines.append(
        "[cmd %d] scope=%r duration=%.2fs run_completed_cleanly=%r final_report_entry_reached=%r"
        % (rec["ordinal"], rec["scope_requested"], rec["duration_seconds"], rec["run_completed_cleanly"],
           rc.get("final_report_entry_reached"))
    )
    summary_lines.append("         first_checkpoint=%r" % (rc.get("first_checkpoint"),))
    summary_lines.append("         last_checkpoint=%r" % (rc.get("last_checkpoint"),))
    summary_lines.append("         harness_memory_after_gc_collect=%r" % (rec.get("harness_memory_after_gc_collect"),))
    if "selected_target_hashes_match_command_1" in rec:
        summary_lines.append("         selected_target_hashes_match_command_1=%r" % (rec["selected_target_hashes_match_command_1"],))
summary_lines.append("")
fv = report.get("final_full_verification") or {}
summary_lines.append("final_full_verification.aggregate_hash=%r" % fv.get("aggregate_hash"))
summary_lines.append("final_full_verification.aggregate_hash_matches_expected=%r" % fv.get("aggregate_hash_matches_expected"))
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
    summary_lines.append("*** DEGRADED ARTIFACT. degraded_fallback_written=%r ***" % report.get("degraded_fallback_written"))
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
        "\nCheckpoint F1-2 reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r, error=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok, summary_write_error)
    )
    sys.stdout.write("\nDO NOT SAVE. Restart SFM to discard this mutation.\n")
except Exception:
    pass
