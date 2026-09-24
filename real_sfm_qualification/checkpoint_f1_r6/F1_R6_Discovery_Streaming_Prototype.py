# -*- coding: ascii -*-
"""
F1-R6 -- Fresh Streaming Discovery Prototype.

DIAGNOSTIC/PROTOTYPE CODE ONLY. Not production. Does not replace, import,
redirect, or monkey-patch discover_rig_context() or reachable() in the
accepted production Normalizer. Callable side-by-side with legacy
discovery for parity comparison only.

No global cache. No retained topology between calls. Every call performs
a fresh, live, from-scratch traversal -- this is FRESH STREAMING
OBSERVATION, not cached discovery. See F1_R6_STREAMING_DESIGN_AND_
EQUIVALENCE_CONTRACT.md for the full design rationale and the 12-point
formal equivalence contract this module is required to satisfy, and
F1_R6_CONTRACT_AND_ALLOCATION_AUDIT.md for the exact legacy contract this
was derived from.

This module intentionally does NOT define handle()/typ()/arr()/scalar()/
attr()/element_ref_pairs()/iter_attributes()/attribute_name()/
attribute_type()/name()/to_unicode()/ProbeError itself -- it calls them as
plain module-level globals, exactly matching legacy's own calling
convention, so that:
  - offline tests can supply FAKE implementations of these names (to
    exercise adversarial synthetic DME graphs without a real SFM
    environment), and
  - a real-SFM harness can supply the REAL production versions of these
    exact same names (extracted from the exec()'d production namespace,
    never reimplemented), guaranteeing the candidate calls the identical
    native-bound helpers legacy itself uses -- only the traversal/
    classification fusion is new code.

Required names, resolved as globals at call time (not imported here):
  handle(obj) -> int
  typ(obj) -> unicode
  arr(obj, attr_name) -> list
  scalar(obj, attr_name) -> value or None
  element_ref_pairs(obj) -> generator of (attr_name, child_element)
  name(obj) -> unicode
  to_unicode(value) -> unicode
  ProbeError -- exception class (module-level in production; a plain
    Exception subclass is sufficient for parity purposes)
"""


def reachable_classify_rigs_streaming(start, aset, max_elements=50000):
    """Fused equivalent of legacy's reachable(start) followed by the
    'for obj in objs: if typ(obj) != "DmeRig": continue; ...' filter loop
    inside discover_rig_context(). Performs the IDENTICAL stack-based
    depth-first traversal, IDENTICAL handle-keyed 'seen' cycle detection,
    and IDENTICAL element_ref_pairs()-based child enumeration as legacy's
    own reachable() -- but classifies each object the instant it is
    visited, instead of first collecting all of them into a persistent
    list for a later, separate pass. Never materializes the full
    reachable-object list.

    Returns (reachable_rig_count, matching_rig_count, first_match), where
    first_match is the SAME object reference legacy's own matches[0]
    would have been when matching_rig_count == 1 (identical traversal
    order preserved), or None if matching_rig_count == 0. When
    matching_rig_count > 1 (ambiguous), first_match still holds the FIRST
    match found -- callers must not surface it in that case, exactly
    mirroring legacy's own AMBIGUOUS_MULTIPLE_RIGS branch, which never
    reads matches[0] either."""
    stack = [start]
    seen = set()
    visited_count = 0
    reachable_rig_count = 0
    matching_rig_count = 0
    first_match = None

    while stack:
        obj = stack.pop()

        try:
            h = handle(obj)
        except Exception:
            continue

        if h in seen:
            continue

        seen.add(h)
        visited_count += 1

        if visited_count > max_elements:
            raise ProbeError(
                "DME traversal exceeded safety cap."
            )

        if typ(obj) == u"DmeRig":
            reachable_rig_count += 1

            try:
                if bool(obj.HasAnimationSet(aset)):
                    matching_rig_count += 1
                    if matching_rig_count == 1:
                        first_match = obj
            except Exception:
                pass

        for unused_attr, child in element_ref_pairs(obj):
            try:
                ch = handle(child)
            except Exception:
                continue

            if ch not in seen:
                stack.append(child)

    return reachable_rig_count, matching_rig_count, first_match


def find_unique_registry_streaming(rig, aset):
    """Fused equivalent of legacy's 'for rec in arr(rig, "animSetList"):
    ...' registry-search loop -- same count+first-match pattern as
    reachable_classify_rigs_streaming, applied to the (small-scale, not
    command-scale) registry search. Returns (registry_match_count,
    first_registry_match)."""
    registry_match_count = 0
    first_registry_match = None

    for rec in arr(rig, "animSetList"):
        if typ(rec) != u"DmeRigAnimSetElements":
            continue

        linked = scalar(rec, "animationSet")

        try:
            same = bool(
                linked is not None
                and handle(linked) == handle(aset)
            )
        except Exception:
            same = False

        if same:
            registry_match_count += 1
            if registry_match_count == 1:
                first_registry_match = rec

    return registry_match_count, first_registry_match


def discover_rig_context_streaming(shot, aset):
    """Candidate streaming discovery. Same signature, same return-dict
    shape, same status vocabulary, same branch structure as legacy's own
    discover_rig_context() -- required to be exactly equivalent per
    F1_R6_STREAMING_DESIGN_AND_EQUIVALENCE_CONTRACT.md's own 12-point
    contract, verified by F1-R6's own offline adversarial parity suite.
    Only the whole-scene rig search and the rig's own registry search are
    fused (streamed); every other step is copied unchanged from legacy."""
    result = {
        "status": "UNRIGGED",
        "rig": None,
        "registry": None,
        "rig_handle": None,
        "registry_handle": None,
        "matching_rig_count": 0,
        "reachable_rig_count": 0,
        "owned_handles": set(),
        "owned_names_in_order": [],
        "hidden_groups": [],
    }

    scene = scalar(shot, "scene")

    if scene is None:
        try:
            scene = shot.scene
        except Exception:
            scene = None

    if scene is None:
        result["status"] = "RIG_CONTEXT_UNAVAILABLE"
        return result

    try:
        reachable_rig_count, matching_rig_count, first_match = (
            reachable_classify_rigs_streaming(scene, aset)
        )
    except Exception:
        result["status"] = "RIG_TRAVERSAL_FAILED"
        return result

    result["reachable_rig_count"] = reachable_rig_count
    result["matching_rig_count"] = matching_rig_count

    if matching_rig_count == 0:
        result["status"] = "UNRIGGED"
        return result

    if matching_rig_count != 1:
        result["status"] = "AMBIGUOUS_MULTIPLE_RIGS"
        return result

    rig = first_match

    registry_match_count, first_registry_match = find_unique_registry_streaming(rig, aset)

    if registry_match_count != 1:
        result["status"] = "AMBIGUOUS_RIG_REGISTRY"
        result["rig"] = rig
        result["rig_handle"] = handle(rig)
        return result

    registry = first_registry_match

    # Unchanged from legacy, verbatim, from this point on: ownership
    # derivation is small-scale (bounded by target control count, not
    # scene-scale) and genuinely multi-pass over control_objs -- not a
    # streaming candidate, per F1_R6_CONTRACT_AND_ALLOCATION_AUDIT.md's
    # own Phase B classification.
    control_objs = arr(aset, "controls")
    control_handles = set([
        handle(control)
        for control in control_objs
    ])

    registry_handles = set()

    for obj in arr(registry, "elementList"):
        try:
            registry_handles.add(handle(obj))
        except Exception:
            pass

    owned_handles = (
        control_handles
        .intersection(registry_handles)
    )

    if not owned_handles:
        result["status"] = "STALE_ZERO_OWNERSHIP_RIG"
        result["rig"] = rig
        result["registry"] = registry
        result["rig_handle"] = handle(rig)
        result["registry_handle"] = handle(registry)
        return result

    owned_names = []

    for control in control_objs:
        if handle(control) in owned_handles:
            owned_names.append(name(control))

    result.update({
        "status": "SUPPORTED_ACTIVE_RIG",
        "rig": rig,
        "registry": registry,
        "rig_handle": handle(rig),
        "registry_handle": handle(registry),
        "owned_handles": owned_handles,
        "owned_names_in_order": owned_names,
        "hidden_groups": [
            to_unicode(x)
            for x in arr(
                registry,
                "hiddenGroups"
            )
        ],
    })

    return result
