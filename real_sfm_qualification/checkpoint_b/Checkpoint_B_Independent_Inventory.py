# -*- coding: ascii -*-
"""
SFM Real-MAINMENU Qualification -- Checkpoint B: Independent Real-Project
Inventory.

RUN TYPE: MAIN MENU SCRIPT
MUTATION STATUS: NON-MUTATING -- zero scene mutation, zero native
Rebuild, zero authority-generation replacement, zero Master
modification, zero save. This script does not import `vs`, does not
touch `vs.g_pDataModel`, does not call any dialog (`RebuildScopeDialog`
or otherwise), and does not alter the Clip Editor selection.

Purpose:
  Build an INDEPENDENT, read-only inventory of the live SFM document --
  shots, animation sets, models, controls, current Clip-Editor selection
  state -- that will later serve as the witness for comparing Selected
  Shots / All Shots baseline-vs-integrated Normalizer runs. This script
  never calls the Normalizer's own scope-resolution/eligibility-gate/
  classification functions (`_choose_scope`, `_resolve_selected_scope`,
  `snapshot_work`, `_gate_is_alh`, `classify_production`, etc.) and never
  imports `Rebuild_Control_Groups_Normalizer.py` at all -- it independently
  re-derives the same underlying document facts from the same real SFM
  APIs (`sfmApp.GetShots()`, `sfmClipEditor.GetSelectedShots()`,
  `shot.animationSets`, `aset.GetAttribute(...)`, `aset.GetRootControlGroup()`,
  `control.GetTypeString()`), so the witness is not circular: it reads the
  same primitive document state the Normalizer also happens to read, but
  computes its own classification independently, never by calling into
  the Normalizer's own policy code.

  One classification this script deliberately does NOT attempt: whether a
  target's rig is a Master-vocabulary-"supported active rig" (arm/leg/head
  presence per the Master TXT, the Normalizer's own `_gate_is_alh`). That
  requires cross-referencing live Master authority data, which is exactly
  the kind of policy-engine-dependent judgment this checkpoint is
  instructed to mark UNRESOLVED rather than reimplement or guess at. The
  raw facts needed to resolve it later (model name, transform-control
  name set) are still recorded per target.

Output:
  Two files are written to C:\\Users\\Public\\Documents\\:
    sfm_checkpoint_b_inventory.json           (machine-readable, full detail)
    sfm_checkpoint_b_inventory_summary.txt    (concise human-readable)
  A short summary is also printed to SFM's own console/output.

Do not save the SFM project after running this script. Do not modify
this file to "fix" an insufficient-fixture result -- report the exact
result instead.
"""
import hashlib
import json
import sys
import time
import traceback

JSON_OUTPUT_PATH = (
    "C:\\Users\\Public\\Documents\\"
    "sfm_checkpoint_b_inventory.json"
)
SUMMARY_OUTPUT_PATH = (
    "C:\\Users\\Public\\Documents\\"
    "sfm_checkpoint_b_inventory_summary.txt"
)


class CheckpointBError(Exception):
    pass


# ---------------------------------------------------------------------------
# Read-only helpers, reproduced verbatim in logic from the accepted, frozen
# production Normalizer's own equivalent free functions (native_ptr,
# to_unicode, ascii_fold, name, typ, attr, scalar, arr,
# validate_model_backed-equivalent, _gate_get_model_name,
# _gate_transform_controls) -- these are neutral, structural DME-reading
# primitives, not scope-resolution or eligibility POLICY, so reproducing
# their exact, already-qualified logic here (rather than reinventing a
# different, unverified reading strategy) is the safer choice; none of
# them decide what belongs in any scope.
# ---------------------------------------------------------------------------

def native_ptr(obj):
    if obj is None:
        return None
    try:
        return long(obj.this)
    except Exception:
        try:
            return int(obj.this)
        except Exception:
            return None


def to_unicode(value):
    if isinstance(value, unicode):
        return value
    try:
        return value.decode("utf-8")
    except Exception:
        try:
            return value.decode("latin-1")
        except Exception:
            return unicode(value)


def ascii_fold(value):
    s = to_unicode(value)
    out = []
    for ch in s:
        o = ord(ch)
        if 65 <= o <= 90:
            out.append(chr(o + 32))
        else:
            out.append(ch)
    return u"".join(out)


def name(obj):
    try:
        return to_unicode(obj.GetName())
    except Exception:
        return u"<UNNAMED>"


def typ(obj):
    try:
        return to_unicode(obj.GetTypeString())
    except Exception:
        try:
            return to_unicode(obj.__class__.__name__)
        except Exception:
            return u"<UNKNOWN_TYPE>"


def attr(obj, attr_name):
    try:
        return obj.GetAttribute(attr_name)
    except Exception:
        return None


def scalar(obj, attr_name):
    a = attr(obj, attr_name)
    if a is not None:
        try:
            return a.GetValue()
        except Exception:
            pass
    try:
        return getattr(obj, attr_name)
    except Exception:
        return None


def arr(obj, attr_name):
    a = attr(obj, attr_name)
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
                raise CheckpointBError(
                    "Cannot read %s[%d] on %r." % (attr_name, i, name(obj))
                )
    return out


def get_game_model(aset):
    """Same logic as the accepted Normalizer's own get_game_model/
    validate_model_backed: a real, present gameModel attribute with a
    resolvable native pointer, or None. A structural fact, not a policy
    decision about eligibility."""
    try:
        if not aset.HasAttribute("gameModel"):
            return None
    except Exception:
        return None
    try:
        game_model = aset.gameModel
    except Exception:
        return None
    if game_model is None or not native_ptr(game_model):
        return None
    return game_model


def get_model_name(game_model):
    """Same logic as the accepted Normalizer's own _gate_get_model_name."""
    for attr_name in ("modelName", "modelPath", "fileName", "filename", "model"):
        value = scalar(game_model, attr_name)
        if value is None:
            continue
        text = to_unicode(value).strip()
        if text:
            return text
    return None


def get_transform_controls(aset):
    """Same logic as the accepted Normalizer's own _gate_transform_controls."""
    return [c for c in arr(aset, "controls") if typ(c) == u"DmeTransformControl"]


def get_root_group(aset):
    try:
        return aset.GetRootControlGroup()
    except Exception:
        return None


def stable_hash(values):
    """SHA-256 of a sorted, newline-joined, utf-8-encoded list of strings
    -- deterministic regardless of original enumeration order."""
    joined = u"\n".join(sorted(values))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

ANOMALIES = []


def anomaly(message):
    ANOMALIES.append(message)


shot_rows = []
target_rows = []
document_has_content = False

try:
    has_document = False
    try:
        has_document = bool(sfmApp.HasDocument())
    except Exception as exc:
        anomaly("sfmApp.HasDocument() raised: %r" % (exc,))

    if not has_document:
        anomaly("No SFM document is open -- inventory cannot proceed.")
    else:
        all_shots = list(sfmApp.GetShots())
        if not all_shots:
            anomaly("sfmApp.GetShots() returned zero shots.")

        selected_shots_raw = []
        try:
            selected_shots_raw = list(sfmClipEditor.GetSelectedShots())
        except Exception as exc:
            anomaly("sfmClipEditor.GetSelectedShots() raised: %r" % (exc,))

        # Independently cross-match Clip-Editor-selected shots against
        # sfmApp.GetShots() by BOTH GetHandle() and native_ptr(), the same
        # dual-key identity comparison the accepted Normalizer's own
        # _resolve_selected_scope() uses -- reproduced here as a neutral
        # identity-matching technique, not a call into that function.
        # Unlike that function, an ambiguous/non-unique match is recorded
        # as an ANOMALY, never raised -- this script's job is to report
        # facts, not enforce policy.
        selected_ptr_set = set()
        for selected_shot in selected_shots_raw:
            selected_handle = None
            try:
                selected_handle = int(selected_shot.GetHandle())
            except Exception:
                pass
            selected_ptr = native_ptr(selected_shot)

            matches = []
            for shot in all_shots:
                shot_handle = None
                try:
                    shot_handle = int(shot.GetHandle())
                except Exception:
                    pass
                shot_ptr = native_ptr(shot)
                matched = (
                    (selected_handle is not None and shot_handle is not None and selected_handle == shot_handle)
                    or (selected_ptr is not None and shot_ptr is not None and selected_ptr == shot_ptr)
                )
                if matched:
                    matches.append(shot_ptr)

            unique_matches = set(matches)
            if len(unique_matches) != 1:
                anomaly(
                    "Clip-Editor-selected shot (native_ptr=%r) did not resolve uniquely to "
                    "sfmApp.GetShots(); unique_matches=%d." % (selected_ptr, len(unique_matches))
                )
                continue
            selected_ptr_set.update(unique_matches)

        document_has_content = True
        global_aset_ptr_seen = set()

        for shot_index, shot in enumerate(all_shots):
            shot_ptr = native_ptr(shot)
            shot_name = name(shot)
            shot_selected = shot_ptr in selected_ptr_set

            if shot_ptr is None:
                anomaly("Shot at index %d has no resolvable native_ptr (name=%r)." % (shot_index, shot_name))

            shot_rows.append({
                "shot_index": shot_index,
                "shot_ptr": shot_ptr,
                "shot_name": shot_name,
                "shot_selected": shot_selected,
            })

            try:
                animation_sets = list(shot.animationSets)
            except Exception as exc:
                anomaly("shot %r (ptr=%r): shot.animationSets raised: %r" % (shot_name, shot_ptr, exc))
                animation_sets = []

            for aset_index, aset in enumerate(animation_sets):
                try:
                    aset_ptr = native_ptr(aset)
                    aset_name = name(aset)

                    is_duplicate = aset_ptr is not None and aset_ptr in global_aset_ptr_seen
                    if aset_ptr is not None:
                        global_aset_ptr_seen.add(aset_ptr)
                    if is_duplicate:
                        anomaly(
                            "Duplicate animation-set native_ptr=%r (name=%r) encountered under shot %r -- "
                            "later comparison for this target will need explicit resolution."
                            % (aset_ptr, aset_name, shot_name)
                        )

                    game_model = get_game_model(aset)
                    model_backed = game_model is not None
                    model_name = get_model_name(game_model) if model_backed else None
                    model_ptr = native_ptr(game_model) if model_backed else None

                    root_group = get_root_group(aset)
                    root_valid = bool(root_group is not None and native_ptr(root_group))

                    eligible = bool(model_backed and root_valid and not is_duplicate)

                    transform_controls = get_transform_controls(aset)
                    control_count = len(transform_controls)
                    folded_names = set()
                    for control in transform_controls:
                        folded_names.add(ascii_fold(name(control)))
                    fold_vocabulary = sorted(folded_names)
                    fold_vocabulary_hash = stable_hash(fold_vocabulary) if fold_vocabulary else None

                    if not eligible:
                        category = "excluded"
                    elif shot_selected:
                        category = "expected_selected_and_all_candidate"
                    else:
                        category = "untouched_peer_eligible_all_only"

                    target_rows.append({
                        "shot_ptr": shot_ptr,
                        "shot_name": shot_name,
                        "shot_selected": shot_selected,
                        "aset_ptr": aset_ptr,
                        "aset_name": aset_name,
                        "aset_index_in_shot": aset_index,
                        "is_duplicate_aset_ptr": is_duplicate,
                        "model_backed": model_backed,
                        "model_ptr": model_ptr,
                        "model_name": model_name,
                        "root_group_valid": root_valid,
                        "eligible": eligible,
                        "control_count": control_count,
                        "fold_vocabulary_hash": fold_vocabulary_hash,
                        "rig_support_classification": "UNRESOLVED (requires Master-authority lookup; out of this checkpoint's independent-witness scope)",
                        "category": category,
                    })
                except Exception as exc:
                    anomaly(
                        "shot %r aset index %d: unhandled exception during fact extraction: %r"
                        % (shot_name, aset_index, exc)
                    )
                    target_rows.append({
                        "shot_ptr": shot_ptr,
                        "shot_name": shot_name,
                        "shot_selected": shot_selected,
                        "aset_ptr": None,
                        "aset_name": None,
                        "aset_index_in_shot": aset_index,
                        "category": "unsupported_unknown",
                        "error": repr(exc),
                    })

except Exception as top_exc:
    anomaly("UNHANDLED TOP-LEVEL EXCEPTION: %s" % repr(top_exc))
    anomaly(traceback.format_exc())

# ---------------------------------------------------------------------------
# Aggregate, classify, hash.
# ---------------------------------------------------------------------------

total_shots = len(shot_rows)
total_targets = len(target_rows)

eligible_targets = [t for t in target_rows if t.get("category") not in ("excluded", "unsupported_unknown")]
excluded_targets = [t for t in target_rows if t.get("category") == "excluded"]
unsupported_targets = [t for t in target_rows if t.get("category") == "unsupported_unknown"]
expected_selected_targets = [t for t in target_rows if t.get("category") == "expected_selected_and_all_candidate"]
untouched_peer_targets = [t for t in target_rows if t.get("category") == "untouched_peer_eligible_all_only"]
expected_all_targets = expected_selected_targets + untouched_peer_targets

distinct_model_names = sorted(set(
    t["model_name"] for t in target_rows if t.get("model_name")
))
distinct_fold_vocabulary_hashes = sorted(set(
    t["fold_vocabulary_hash"] for t in eligible_targets if t.get("fold_vocabulary_hash")
))

def target_key(t):
    return u"%r|%r|%r" % (t.get("shot_ptr"), t.get("aset_ptr"), t.get("aset_name"))

hashes = {
    "shot_inventory_hash": stable_hash([u"%r|%s" % (r["shot_ptr"], r["shot_name"]) for r in shot_rows]),
    "target_inventory_hash": stable_hash([target_key(t) for t in target_rows]),
    "model_inventory_hash": stable_hash(distinct_model_names) if distinct_model_names else None,
    "selected_shot_set_hash": stable_hash([u"%r" % r["shot_ptr"] for r in shot_rows if r["shot_selected"]]) if any(r["shot_selected"] for r in shot_rows) else None,
    "expected_selected_target_set_hash": stable_hash([target_key(t) for t in expected_selected_targets]) if expected_selected_targets else None,
    "expected_all_target_set_hash": stable_hash([target_key(t) for t in expected_all_targets]) if expected_all_targets else None,
    "excluded_target_set_hash": stable_hash([target_key(t) for t in excluded_targets]) if excluded_targets else None,
    "untouched_peer_target_set_hash": stable_hash([target_key(t) for t in untouched_peer_targets]) if untouched_peer_targets else None,
}

sufficiency = {
    "multiple_shots (>=2)": total_shots >= 2,
    "multiple_eligible_targets (>=2)": len(eligible_targets) >= 2,
    "at_least_one_target_expected_processed (eligible>=1)": len(eligible_targets) >= 1,
    "at_least_one_expected_selected_candidate (>=1)": len(expected_selected_targets) >= 1,
    "at_least_one_untouched_peer (>=1)": len(untouched_peer_targets) >= 1,
    "no_duplicate_or_unsupported_targets (excluded via duplicates/unsupported == 0)": (
        sum(1 for t in target_rows if t.get("is_duplicate_aset_ptr")) == 0
        and len(unsupported_targets) == 0
    ),
    "preferred_two_distinct_vocabularies (>=2, NOT a hard requirement)": len(distinct_fold_vocabulary_hashes) >= 2,
}
hard_requirements_met = all(
    v for k, v in sufficiency.items() if "NOT a hard requirement" not in k
)

completed_without_exception = document_has_content and len(unsupported_targets) == 0 and not any(
    "UNHANDLED TOP-LEVEL EXCEPTION" in a for a in ANOMALIES
)

report = {
    "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "python_version": sys.version,
    "document_has_content": document_has_content,
    "totals": {
        "total_shots": total_shots,
        "total_targets": total_targets,
        "eligible_targets": len(eligible_targets),
        "excluded_targets": len(excluded_targets),
        "unsupported_unknown_targets": len(unsupported_targets),
        "expected_selected_candidates": len(expected_selected_targets),
        "expected_all_candidates": len(expected_all_targets),
        "untouched_peer_targets": len(untouched_peer_targets),
        "distinct_model_names": len(distinct_model_names),
        "distinct_fold_vocabulary_hashes_among_eligible": len(distinct_fold_vocabulary_hashes),
    },
    "hashes": hashes,
    "sufficiency": sufficiency,
    "hard_requirements_met": hard_requirements_met,
    "completed_without_exception": completed_without_exception,
    "overall_pass": bool(hard_requirements_met and completed_without_exception),
    "distinct_model_names_list": distinct_model_names,
    "shots": shot_rows,
    "targets": target_rows,
    "anomalies": ANOMALIES,
}

json_write_ok = True
try:
    json_file = open(JSON_OUTPUT_PATH, "wb")
    try:
        json_file.write(json.dumps(report, indent=2, sort_keys=True).encode("utf-8"))
    finally:
        json_file.close()
except Exception:
    json_write_ok = False

summary_lines = []
summary_lines.append("SFM CHECKPOINT B -- INDEPENDENT REAL-PROJECT INVENTORY")
summary_lines.append("started_at=%s" % report["started_at"])
summary_lines.append("python_version=%r" % sys.version)
summary_lines.append("")
summary_lines.append("document_has_content=%r" % document_has_content)
summary_lines.append("")
summary_lines.append("--- TOTALS ---")
for k, v in sorted(report["totals"].items()):
    summary_lines.append("%s = %r" % (k, v))
summary_lines.append("")
summary_lines.append("--- HASHES ---")
for k, v in sorted(hashes.items()):
    summary_lines.append("%s = %r" % (k, v))
summary_lines.append("")
summary_lines.append("--- SUFFICIENCY (hard requirements unless noted) ---")
for k, v in sorted(sufficiency.items()):
    summary_lines.append("[%s] %s" % ("PASS" if v else "FAIL", k))
summary_lines.append("")
summary_lines.append("hard_requirements_met=%r" % hard_requirements_met)
summary_lines.append("completed_without_exception=%r" % completed_without_exception)
summary_lines.append("OVERALL_PASS=%r" % report["overall_pass"])
summary_lines.append("")
summary_lines.append("--- ANOMALIES (%d) ---" % len(ANOMALIES))
for a in ANOMALIES:
    summary_lines.append("- %s" % a)
if not ANOMALIES:
    summary_lines.append("(none)")
summary_lines.append("")
summary_lines.append("json_output_path=%s (write_ok=%r)" % (JSON_OUTPUT_PATH, json_write_ok))
summary_lines.append("finished_at=%s" % time.strftime("%Y-%m-%d %H:%M:%S"))

summary_text = u"\n".join(summary_lines) + u"\n"

summary_write_ok = True
try:
    summary_file = open(SUMMARY_OUTPUT_PATH, "wb")
    try:
        summary_file.write(summary_text.encode("ascii", "replace"))
    finally:
        summary_file.close()
except Exception:
    summary_write_ok = False

try:
    sys.stdout.write(summary_text.encode("ascii", "replace"))
    sys.stdout.write(
        "\nCheckpoint B reports written to:\n  %s (write_ok=%r)\n  %s (write_ok=%r)\n"
        % (JSON_OUTPUT_PATH, json_write_ok, SUMMARY_OUTPUT_PATH, summary_write_ok)
    )
except Exception:
    pass
