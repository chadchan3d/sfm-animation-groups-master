# -*- coding: utf-8 -*-
"""Offline regression for Checkpoint C1's semantic fingerprint comparator
(`canonicalize_snapshot`), added per independent-audit correction
2026-09-22 (defect: `capture_snapshot_explicit`'s own `"label"` field
made every PRE/POST pair compare unequal regardless of real content).

Extracts `canonicalize_snapshot` VERBATIM (exact line range, SHA-256
pinned against the current deployed C1-2 script) and proves, against
synthetic `capture_snapshot_explicit`-shaped dicts:

  1. two otherwise-identical fingerprints tagged PRE/POST (differing
     ONLY in `label`, `shot_handle`, `animation_set_handle`,
     `root_handle`, `rig_handle`, `registry_handle`, `control_handles`
     -- exactly the fields the comparator is supposed to strip) compare
     EQUAL after canonicalization;
  2. a real semantic field change (a control name inside the group
     tree) still compares UNEQUAL after canonicalization -- proving the
     fix does not silently mask real differences.

Never launches SFM. Read-only with respect to the deployed C1 script.
"""
import hashlib
import json
import sys

C1_SCRIPT_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Checkpoint_C1_Baseline_Selected_Shots.py"
)
EXPECTED_C1_SCRIPT_SHA256 = (
    "4387b03de820ae05e6647d68d22bb2bc084b1bf3ae4c78cbb060dddc412219dc"
)
# 1-indexed, inclusive. Re-verify with:
#   sed -n '589,606p' Checkpoint_C1_Baseline_Selected_Shots.py
CANONICALIZE_SNAPSHOT_RANGE = (589, 606)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


def _make_snapshot(label, control_b_name=u"bone_b"):
    """A synthetic capture_snapshot_explicit()-shaped dict -- same shape
    as the real function's return value, with deliberately DIFFERENT
    handle values per call (simulating two separate captures in the
    same or different sessions) and a caller-controlled control name so
    a real semantic change can be introduced on demand."""
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
# with free variables (a real, longstanding CPython 2 grammar
# restriction, hit and worked around this same way elsewhere in this
# project's own qualification suite) -- top-level placement sidesteps it
# entirely and matches this project's other extraction-based harnesses.

with open(C1_SCRIPT_PATH, "rb") as f:
    _data = f.read()
_actual_sha = hashlib.sha256(_data).hexdigest()
check("source.c1_script_sha256_pinned", _actual_sha == EXPECTED_C1_SCRIPT_SHA256, _actual_sha)
if _actual_sha != EXPECTED_C1_SCRIPT_SHA256:
    print("\nRESULT: 1/%d SOME FAILED (SHA mismatch -- refusing to extract from a stale/wrong file)" % (len(RESULTS) + 1))
    sys.exit(1)

_lines = _data.decode("ascii").splitlines()
_start, _end = CANONICALIZE_SNAPSHOT_RANGE
_raw = "\n".join(_lines[_start - 1:_end])
check("source.range_starts_with_expected_def", _raw.strip().startswith("def canonicalize_snapshot(snap):"), _raw.splitlines()[0])

# Dedent by 4 spaces (nested one level inside the real script's `try:`).
_dedented = "\n".join(line[4:] if line.startswith("    ") else line for line in _raw.splitlines()) + "\n"

_ns = {}
exec(compile(_dedented, "<canonicalize_snapshot_extract>", "exec"), _ns)
check("source.extracted_and_exec_ok", "canonicalize_snapshot" in _ns and callable(_ns["canonicalize_snapshot"]))
canonicalize_snapshot = _ns["canonicalize_snapshot"]

# --- 1. Identical semantic content, PRE vs POST -- must compare EQUAL. ---
_pre = _make_snapshot(u"PRE")
_post = _make_snapshot(u"POST")
check("fixture.pre_and_post_differ_in_raw_form_before_canonicalization",
      json.dumps(_pre, sort_keys=True) != json.dumps(_post, sort_keys=True))

_canon_pre = canonicalize_snapshot(_pre)
_canon_post = canonicalize_snapshot(_post)
check("regression.label_field_removed_from_both", "label" not in _canon_pre and "label" not in _canon_post)
check("regression.handle_fields_removed_from_both",
      not any(k in _canon_pre for k in ("shot_handle", "animation_set_handle", "root_handle", "rig_handle", "registry_handle", "control_handles")))
check("regression.identical_semantic_content_compares_equal_after_canonicalization",
      json.dumps(_canon_pre, sort_keys=True) == json.dumps(_canon_post, sort_keys=True))

# --- 2. A REAL semantic change (a control's name inside the group
#        tree) must still compare UNEQUAL after canonicalization. ---
_pre2 = _make_snapshot(u"PRE", control_b_name=u"bone_b")
_post2 = _make_snapshot(u"POST", control_b_name=u"bone_b_RENAMED")
_canon_pre2 = canonicalize_snapshot(_pre2)
_canon_post2 = canonicalize_snapshot(_post2)
check("regression.real_semantic_change_still_compares_unequal",
      json.dumps(_canon_pre2, sort_keys=True) != json.dumps(_canon_post2, sort_keys=True))

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(c for _, c in RESULTS):
    sys.exit(1)
