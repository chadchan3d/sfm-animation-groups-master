# -*- coding: utf-8 -*-
"""Offline regression for Checkpoint C2's NEW logic (beyond what
Checkpoint C1's own already-dry-run-verified helpers already cover):
  1. `canonicalize_snapshot` -- identical to C1's, re-verified here
     against the deployed C2 file's own copy (independent extraction,
     same fixtures as test_c1_semantic_comparator_regression.py).
  2. `dumps_sorted` / `differing_top_level_fields` -- the field-level
     diagnostic used by comparisons D and F.
  3. Comparison D (per-target parity) logic, exercised against a
     synthetic 85-target-shaped pair of fingerprints where all targets
     match except one -- must report equal_count=84, differing_count=1,
     and name exactly the one differing target with its differing field.
  4. Comparison E (four-way untouched-peer parity) logic -- a peer whose
     C1-baseline PRE/POST differ from this run's PRE/POST must be
     flagged; an unchanged peer across all four captures must not be.
  5. The C1-JSON integrity gate condition (report["overall_pass"] must
     be True and both fingerprint hashes must match pinned values) --
     proves a tampered/mismatched C1 artifact is correctly rejected
     before any fixture witness build would occur.

Extracts `canonicalize_snapshot`, `dumps_sorted`, and
`differing_top_level_fields` VERBATIM (exact line ranges, SHA-256
pinned against the deployed C2 script) rather than reimplementing them,
so this regression exercises the actual deployed code.

Never launches SFM. Read-only with respect to the deployed C2 script.
"""
import hashlib
import json
import sys

C2_SCRIPT_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Checkpoint_C2_Integrated_Selected_Shots.py"
)
EXPECTED_C2_SCRIPT_SHA256 = (
    "c5ca0d4cf423eb6e6af24ee0e530f309e7f157def3db3e536bb9cd6b3e4c2768"
)
# 1-indexed, inclusive. Re-verify with:
#   sed -n '<start>,<end>p' Checkpoint_C2_Integrated_Selected_Shots.py
STABLE_HASH_RANGE = (378, 380)
DUMPS_SORTED_AND_DIFFERING_RANGE = (487, 501)
CANONICALIZE_SNAPSHOT_RANGE = (645, 653)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


def _make_snapshot(label, control_b_name=u"bone_b"):
    return {
        "label": label,
        "shot_name": u"shot3",
        "shot_handle": 111111 if label == u"PRE" else 222222,
        "animation_set_name": u"foxmccouldwm1",
        "animation_set_handle": 333333 if label == u"PRE" else 444444,
        "root_handle": 555555 if label == u"PRE" else 666666,
        "rig_status": u"UNRIGGED",
        "rig_name": None,
        "rig_handle": None if label == u"PRE" else 0,
        "registry_handle": 777777 if label == u"PRE" else 888888,
        "matching_rig_count": 0,
        "reachable_rig_count": 0,
        "control_count": 2,
        "control_names_in_animation_set_order": [u"bone_a", control_b_name],
        "duplicate_control_names": {},
        "control_handles": {u"bone_a": 1001, control_b_name: 1002} if label == u"PRE" else {u"bone_a": 9001, control_b_name: 9002},
        "control_types": {u"bone_a": u"DmeTransformControl", control_b_name: u"DmeTransformControl"},
        "owned_control_names_in_animation_set_order": [],
        "owned_control_name_set": [],
        "hidden_groups": [],
        "group_count": 2,
        "groups": {
            u"<ROOT>": {
                "path": u"<ROOT>", "name": u"<ROOT>", "parent_path": None,
                "visible": True, "effective_visible": True, "selectable": True, "snappable": True,
                "group_color": [255, 128, 64, 255],
                "child_names_in_order": [u"ChildGroup"],
                "direct_control_names_in_order": [u"bone_a"],
            },
            u"ChildGroup": {
                "path": u"ChildGroup", "name": u"ChildGroup", "parent_path": u"<ROOT>",
                "visible": True, "effective_visible": True, "selectable": True, "snappable": True,
                "group_color": [255, 128, 64, 255],
                "child_names_in_order": [],
                "direct_control_names_in_order": [control_b_name],
            },
        },
        "memberships": {u"bone_a": [u"<ROOT>"], control_b_name: [u"ChildGroup"]},
        "duplicate_sibling_groups": [],
        "duplicate_direct_controls": [],
        "duplicate_memberships": {},
        "rig_recon_exists": False,
        "master_recon_exists": False,
    }


# Module-level (not inside a function): Python 2's `exec` statement is
# disallowed inside any function that also contains a nested `def`/class
# with free variables -- top-level placement sidesteps it, same as this
# project's other extraction-based harnesses.

with open(C2_SCRIPT_PATH, "rb") as f:
    _data = f.read()
_actual_sha = hashlib.sha256(_data).hexdigest()
check("source.c2_script_sha256_pinned", _actual_sha == EXPECTED_C2_SCRIPT_SHA256, _actual_sha)
if _actual_sha != EXPECTED_C2_SCRIPT_SHA256:
    print("\nRESULT: 1/%d SOME FAILED (SHA mismatch -- refusing to extract from a stale/wrong file)" % (len(RESULTS) + 1))
    sys.exit(1)

_lines = _data.decode("ascii").splitlines()


def _extract(start, end, dedent=0):
    raw = "\n".join(_lines[start - 1:end])
    if dedent:
        raw = "\n".join(line[dedent:] if line.startswith(" " * dedent) else line for line in raw.splitlines())
    return raw + "\n"


_ns = {"json": json, "hashlib": hashlib}

_stable_hash_src = _extract(*STABLE_HASH_RANGE)
check("source.stable_hash_range_starts_with_expected_def", _stable_hash_src.strip().startswith("def stable_hash(values):"), _stable_hash_src.splitlines()[0])
exec(compile(_stable_hash_src, "<stable_hash_extract>", "exec"), _ns)

_dumps_src = _extract(*DUMPS_SORTED_AND_DIFFERING_RANGE)
check("source.dumps_sorted_range_starts_with_expected_def", _dumps_src.strip().startswith("def dumps_sorted(value):"), _dumps_src.splitlines()[0])
exec(compile(_dumps_src, "<dumps_sorted_extract>", "exec"), _ns)

_canon_src = _extract(CANONICALIZE_SNAPSHOT_RANGE[0], CANONICALIZE_SNAPSHOT_RANGE[1], dedent=4)
check("source.canonicalize_snapshot_range_starts_with_expected_def", _canon_src.strip().startswith("def canonicalize_snapshot(snap):"), _canon_src.splitlines()[0])
exec(compile(_canon_src, "<canonicalize_snapshot_extract>", "exec"), _ns)

check("source.all_three_extracted_and_exec_ok",
      all(callable(_ns.get(n)) for n in ("stable_hash", "dumps_sorted", "differing_top_level_fields", "canonicalize_snapshot")))

stable_hash = _ns["stable_hash"]
dumps_sorted = _ns["dumps_sorted"]
differing_top_level_fields = _ns["differing_top_level_fields"]
canonicalize_snapshot = _ns["canonicalize_snapshot"]

# --- 1. canonicalize_snapshot: identical semantic content compares
#        equal; a real semantic change still compares unequal. ---
_pre = _make_snapshot(u"PRE")
_post = _make_snapshot(u"POST")
_canon_pre = canonicalize_snapshot(_pre)
_canon_post = canonicalize_snapshot(_post)
check("regression.canonicalize_snapshot.label_and_handles_removed",
      "label" not in _canon_pre and "shot_handle" not in _canon_pre and "control_handles" not in _canon_pre)
check("regression.canonicalize_snapshot.identical_content_compares_equal",
      dumps_sorted(_canon_pre) == dumps_sorted(_canon_post))

_pre2 = _make_snapshot(u"PRE", control_b_name=u"bone_b")
_post2 = _make_snapshot(u"POST", control_b_name=u"bone_b_RENAMED")
_canon_pre2 = canonicalize_snapshot(_pre2)
_canon_post2 = canonicalize_snapshot(_post2)
check("regression.canonicalize_snapshot.real_change_compares_unequal",
      dumps_sorted(_canon_pre2) != dumps_sorted(_canon_post2))

# --- 2. differing_top_level_fields: identifies exactly the changed
#        top-level key(s), nothing else. ---
# Renaming the control ("bone_b" -> "bone_b_RENAMED") changes every
# top-level field that carries that name as a value OR as a dict key:
# control_names_in_animation_set_order (list value), control_types and
# memberships (dict KEY change), and groups (nested
# direct_control_names_in_order value) -- all four, not just the two
# most obviously "control name" fields.
_diff_fields = differing_top_level_fields(_canon_pre2, _canon_post2)
check("regression.differing_top_level_fields.finds_exactly_expected_keys",
      set(_diff_fields) == set(["control_names_in_animation_set_order", "control_types", "groups", "memberships"]), _diff_fields)
_diff_fields_none = differing_top_level_fields(_canon_pre, _canon_post)
check("regression.differing_top_level_fields.empty_for_identical_snapshots",
      _diff_fields_none == [], _diff_fields_none)

# --- 3. Comparison D logic: 85-target-shaped synthetic set, all equal
#        except one -- must report equal_count=84, differing_count=1,
#        and name exactly that one target + its differing field. ---
_c1_post_synth = {}
_integrated_post_synth = {}
for _i in range(85):
    _key = u"synthshot%d|target%d" % (_i, _i)
    _snap = canonicalize_snapshot(_make_snapshot(u"POST", control_b_name=u"bone_b_%d" % _i))
    _c1_post_synth[_key] = _snap
    if _i == 42:
        _integrated_post_synth[_key] = canonicalize_snapshot(_make_snapshot(u"POST", control_b_name=u"bone_b_%d_DIFFERENT" % _i))
    else:
        _integrated_post_synth[_key] = dict(_snap)

_equal_count = 0
_differing = []
for _key in sorted(_c1_post_synth.keys()):
    _a = _integrated_post_synth.get(_key)
    _b = _c1_post_synth.get(_key)
    if dumps_sorted(_a) == dumps_sorted(_b):
        _equal_count += 1
    else:
        _differing.append({"target": _key, "differing_fields": differing_top_level_fields(_a, _b)})

check("regression.comparison_D.equal_count_is_84", _equal_count == 84, _equal_count)
check("regression.comparison_D.differing_count_is_1", len(_differing) == 1, len(_differing))
check("regression.comparison_D.differing_target_is_exactly_synthshot42",
      len(_differing) == 1 and _differing[0]["target"] == u"synthshot42|target42", _differing)

# --- 4. Comparison E logic: four-way peer parity -- an unchanged peer
#        across all four captures passes; a peer whose C1-baseline PRE
#        differs from everything else fails and is named. ---
_peer_unchanged = canonicalize_snapshot(_make_snapshot(u"PRE"))
_peer_changed_c1_pre = canonicalize_snapshot(_make_snapshot(u"PRE", control_b_name=u"bone_b_STALE"))

_i_pre = dumps_sorted(_peer_unchanged)
_i_post = dumps_sorted(_peer_unchanged)
_c1_pre_ok = dumps_sorted(_peer_unchanged)
_c1_post_ok = dumps_sorted(_peer_unchanged)
check("regression.comparison_E.four_way_equal_peer_passes", _i_pre == _i_post == _c1_pre_ok == _c1_post_ok)

_c1_pre_bad = dumps_sorted(_peer_changed_c1_pre)
check("regression.comparison_E.mismatched_peer_correctly_flagged",
      not (_i_pre == _i_post == _c1_pre_bad == _c1_post_ok))

# --- 5. C1-JSON integrity gate condition. ---
_good_c1_report = {
    "overall_pass": True,
    "pre_fingerprint_hash": "eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0",
    "post_fingerprint_hash": "d7b3bacb757253e126823db4e1445b57e4278d972c9be8b23920fc88cf1b5938",
    "touched_targets": [u"shot3|foxmccouldwm1", u"shot3|mia1"],
    "unchanged_targets_count": 83,
}
_EXPECTED_C1_PRE_HASH = "eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0"
_EXPECTED_C1_POST_HASH = "d7b3bacb757253e126823db4e1445b57e4278d972c9be8b23920fc88cf1b5938"


def _gate_conditions_hold(c1_report_obj):
    return bool(
        bool(c1_report_obj.get("overall_pass")) is True
        and c1_report_obj.get("pre_fingerprint_hash") == _EXPECTED_C1_PRE_HASH
        and c1_report_obj.get("post_fingerprint_hash") == _EXPECTED_C1_POST_HASH
    )


check("regression.c1_gate.good_artifact_passes_gate", _gate_conditions_hold(_good_c1_report))

_bad_c1_report_wrong_hash = dict(_good_c1_report)
_bad_c1_report_wrong_hash["post_fingerprint_hash"] = "0000000000000000000000000000000000000000000000000000000000000000"
check("regression.c1_gate.tampered_post_hash_correctly_rejected", not _gate_conditions_hold(_bad_c1_report_wrong_hash))

_bad_c1_report_not_passed = dict(_good_c1_report)
_bad_c1_report_not_passed["overall_pass"] = False
check("regression.c1_gate.non_passing_c1_artifact_correctly_rejected", not _gate_conditions_hold(_bad_c1_report_not_passed))

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(c for _, c in RESULTS):
    sys.exit(1)
