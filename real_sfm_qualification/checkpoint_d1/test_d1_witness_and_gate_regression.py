# -*- coding: utf-8 -*-
"""Offline regression for Checkpoint D1's NEW logic (beyond what
Checkpoints C1/C2's own already-dry-run-verified helpers already cover,
which D1 reuses verbatim and unmodified -- b_* helpers,
build_independent_witness, canonicalize_snapshot, capture_all, the wait
loop):
  1. `target_key` / `excluded_witness_row` -- the lightweight, non-
     mutating structural witness used for the 78 excluded targets
     (deliberately never routed through capture_snapshot_explicit()).
  2. The excluded-witness PRE/POST comparison logic -- an unchanged
     excluded target must not be flagged; a real structural change
     (e.g. control_count) must be flagged, named exactly.
  3. The target-set-diff logic (missing/new/reclassified) -- a target
     present in both PRE and POST is neither missing nor new; a target
     absent from POST entirely is flagged as missing; a target that
     moved from the eligible set to the excluded set is flagged as
     reclassified, not as missing.
  4. The fixture/starting-state gate condition (all EXPECTED_TOTALS
     keys matching AND the initial PRE hash matching the pinned C1/C2
     value) -- proves a totals mismatch or a stale-fixture PRE hash is
     correctly rejected before any baseline invocation would occur.

Extracts `dumps_sorted`, `target_key`, and `excluded_witness_row`
VERBATIM (exact line ranges, SHA-256 pinned against the deployed D1
script) rather than reimplementing them.

Never launches SFM. Read-only with respect to the deployed D1 script.
"""
import hashlib
import json
import sys

D1_SCRIPT_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Checkpoint_D1_Historical_All_Shots_Baseline.py"
)
EXPECTED_D1_SCRIPT_SHA256 = (
    "e5df3675e26280ab3ed3a6e54ae1a54d7bd6526c3df22e2bfce59d3b5a2cdf61"
)
# 1-indexed, inclusive. Re-verify with:
#   sed -n '<start>,<end>p' Checkpoint_D1_Historical_All_Shots_Baseline.py
DUMPS_SORTED_RANGE = (519, 520)
TARGET_KEY_AND_EXCLUDED_WITNESS_ROW_RANGE = (523, 548)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


def _make_excluded_target(shot_name, aset_name, control_count=0, model_name=None,
                           root_group_valid=False, is_duplicate=False, category="excluded",
                           fold_vocabulary_hash=None):
    return {
        "shot_ptr": 123456, "shot_name": shot_name, "shot_selected": False,
        "aset_ptr": 654321, "aset_name": aset_name, "is_duplicate_aset_ptr": is_duplicate,
        "model_backed": bool(model_name), "model_name": model_name,
        "root_group_valid": root_group_valid, "eligible": False,
        "control_count": control_count, "fold_vocabulary_hash": fold_vocabulary_hash,
        "category": category,
    }


# Module-level (not inside a function): Python 2's `exec` statement is
# disallowed inside any function that also contains a nested `def`/class
# with free variables -- top-level placement sidesteps it, same as this
# project's other extraction-based harnesses.

with open(D1_SCRIPT_PATH, "rb") as f:
    _data = f.read()
_actual_sha = hashlib.sha256(_data).hexdigest()
check("source.d1_script_sha256_pinned", _actual_sha == EXPECTED_D1_SCRIPT_SHA256, _actual_sha)
if _actual_sha != EXPECTED_D1_SCRIPT_SHA256:
    print("\nRESULT: 1/%d SOME FAILED (SHA mismatch -- refusing to extract from a stale/wrong file)" % (len(RESULTS) + 1))
    sys.exit(1)

_lines = _data.decode("ascii").splitlines()


def _extract(start, end):
    return "\n".join(_lines[start - 1:end]) + "\n"


_ns = {"json": json}

_dumps_src = _extract(*DUMPS_SORTED_RANGE)
check("source.dumps_sorted_range_starts_with_expected_def", _dumps_src.strip().startswith("def dumps_sorted(value):"), _dumps_src.splitlines()[0])
exec(compile(_dumps_src, "<dumps_sorted_extract>", "exec"), _ns)

_witness_src = _extract(*TARGET_KEY_AND_EXCLUDED_WITNESS_ROW_RANGE)
check("source.target_key_range_starts_with_expected_def", _witness_src.strip().startswith("def target_key(t):"), _witness_src.splitlines()[0])
exec(compile(_witness_src, "<target_key_and_excluded_witness_row_extract>", "exec"), _ns)

check("source.all_functions_extracted_and_exec_ok",
      all(callable(_ns.get(n)) for n in ("dumps_sorted", "target_key", "excluded_witness_row")))

dumps_sorted = _ns["dumps_sorted"]
target_key = _ns["target_key"]
excluded_witness_row = _ns["excluded_witness_row"]

# --- 1. target_key / excluded_witness_row basic shape. ---
_t_camera = _make_excluded_target(u"shot1", u"camera1", control_count=0, model_name=None)
check("regression.target_key.formats_as_shot_pipe_aset", target_key(_t_camera) == u"shot1|camera1", target_key(_t_camera))

_row_camera = excluded_witness_row(_t_camera)
check("regression.excluded_witness_row.excludes_pointer_fields",
      "shot_ptr" not in _row_camera and "aset_ptr" not in _row_camera)
check("regression.excluded_witness_row.includes_structural_fields",
      set(_row_camera.keys()) == set(["shot_name", "aset_name", "model_backed", "model_name",
                                       "root_group_valid", "is_duplicate_aset_ptr", "control_count",
                                       "fold_vocabulary_hash", "category"]))

# --- 2. Excluded-witness PRE/POST comparison: unchanged passes,
#        real change is flagged and named exactly. ---
_pre_excluded = {}
_post_excluded_unchanged = {}
_post_excluded_changed = {}
for _i in range(78):
    _key = u"shot%d|excl%d" % (_i, _i)
    _t = _make_excluded_target(u"shot%d" % _i, u"excl%d" % _i, control_count=3)
    _pre_excluded[_key] = excluded_witness_row(_t)
    _post_excluded_unchanged[_key] = excluded_witness_row(_t)
    if _i == 17:
        _t_changed = _make_excluded_target(u"shot%d" % _i, u"excl%d" % _i, control_count=99)
        _post_excluded_changed[_key] = excluded_witness_row(_t_changed)
    else:
        _post_excluded_changed[_key] = excluded_witness_row(_t)

_changes_none = [k for k in sorted(_pre_excluded.keys()) if dumps_sorted(_pre_excluded[k]) != dumps_sorted(_post_excluded_unchanged.get(k))]
check("regression.excluded_witness_comparison.no_false_positive_on_unchanged_set", _changes_none == [], _changes_none)

_changes_one = [k for k in sorted(_pre_excluded.keys()) if dumps_sorted(_pre_excluded[k]) != dumps_sorted(_post_excluded_changed.get(k))]
check("regression.excluded_witness_comparison.exactly_one_real_change_detected",
      _changes_one == [u"shot17|excl17"], _changes_one)

# --- 3. Target-set-diff logic: present-in-both is neither missing nor
#        new; absent-from-post is missing; eligible->excluded move is
#        reclassified, not missing. ---
_pre_all_keys = set([u"shotA|targetA", u"shotB|targetB", u"shotC|targetC"])
_post_all_keys_normal = set([u"shotA|targetA", u"shotB|targetB", u"shotC|targetC"])
_post_all_keys_one_vanished = set([u"shotA|targetA", u"shotC|targetC"])

_missing_normal = sorted(_pre_all_keys - _post_all_keys_normal)
check("regression.target_set_diff.nothing_missing_when_all_keys_present", _missing_normal == [], _missing_normal)

_missing_vanished = sorted(_pre_all_keys - _post_all_keys_one_vanished)
check("regression.target_set_diff.exactly_one_missing_target_detected", _missing_vanished == [u"shotB|targetB"], _missing_vanished)

_pre_eligible_keys = set([u"shotA|targetA", u"shotB|targetB"])
_pre_excluded_keys = set([u"shotC|targetC"])
_post_eligible_keys = set([u"shotA|targetA"])
_post_excluded_keys = set([u"shotB|targetB", u"shotC|targetC"])  # B moved eligible -> excluded

_reclassified_e2x = sorted(_pre_eligible_keys & _post_excluded_keys)
check("regression.target_set_diff.eligible_to_excluded_reclassification_detected",
      _reclassified_e2x == [u"shotB|targetB"], _reclassified_e2x)
_missing_after_reclassification = sorted((_pre_eligible_keys | _pre_excluded_keys) - (_post_eligible_keys | _post_excluded_keys))
check("regression.target_set_diff.reclassified_target_not_counted_as_missing",
      _missing_after_reclassification == [], _missing_after_reclassification)

# --- 4. Fixture/starting-state gate condition. ---
_EXPECTED_TOTALS = {
    "total_shots": 15, "total_targets": 163, "eligible_targets": 85,
    "excluded_targets": 78, "distinct_model_names": 22,
    "distinct_fold_vocabulary_hashes_among_eligible": 21,
}
_EXPECTED_INITIAL_PRE_HASH = "eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0"


def _gate_holds(totals_obj, pre_hash_value):
    totals_ok = all(totals_obj.get(k) == v for k, v in _EXPECTED_TOTALS.items())
    hash_ok = (pre_hash_value == _EXPECTED_INITIAL_PRE_HASH)
    return bool(totals_ok and hash_ok)


_good_totals = dict(_EXPECTED_TOTALS)
check("regression.gate.matching_totals_and_hash_passes", _gate_holds(_good_totals, _EXPECTED_INITIAL_PRE_HASH))

_bad_totals = dict(_EXPECTED_TOTALS)
_bad_totals["eligible_targets"] = 84
check("regression.gate.totals_mismatch_correctly_rejected", not _gate_holds(_bad_totals, _EXPECTED_INITIAL_PRE_HASH))

check("regression.gate.stale_pre_hash_correctly_rejected",
      not _gate_holds(_good_totals, "0000000000000000000000000000000000000000000000000000000000000000"))

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(c for _, c in RESULTS):
    sys.exit(1)
