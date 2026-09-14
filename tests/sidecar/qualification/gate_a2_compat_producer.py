# -*- coding: utf-8 -*-
"""GATE A2 -- TEST-ONLY sidecar-derived compatibility-view producer.

NOT production code. Never imported by tools/sfm_master_sidecar/*.py or by
the real Rebuild_Control_Groups_Normalizer.py. Takes an already-open, VALID,
bound sidecar provider (the real, unmodified `reader.SidecarReader`) plus a
`wanted_folds` set (already-folded unicode strings, exactly as the
Normalizer's own `ascii_fold()` produces) and returns a dict matching the
EXACT contract of the real Normalizer's `parse_targeted_master()` --
established by direct inspection of that function's current source (Gate A2
Part 2), not inferred from the sidecar's own design:

    mapping_count       -- GLOBAL total occurrence count across the WHOLE
                            sidecar generation (NOT scoped to wanted_folds)
    destination_count   -- GLOBAL total distinct destination count across
                            the WHOLE generation (NOT scoped)
    folded              -- dict[unicode folded_key] -> list of
                            {"literal", "destination", "global_index",
                             "local_index"}, in ORIGINAL FILE ORDER,
                            ONLY for folds in wanted_folds
    exact_literals      -- set of unicode literals, ONLY for occurrences
                            whose folded key is in wanted_folds
    group_sibling_order -- dict[wrapper-EXCLUSIVE unicode path or u"<ROOT>"]
                            -> list of child names in declare order
    group_metadata      -- dict[wrapper-EXCLUSIVE unicode path] -> narrow
                            4-key (groupColor/selectable/visible/snappable)
                            projection, exactly matching the oracle's own
                            silent-ignore-unknown-keys /
                            raise-on-duplicate-known-key behavior

This is a validation-only exercise proving the CURRENT binary format can
express the CURRENT consumer contract -- it is explicitly NOT the intended
bounded-materialization production provider (which is Gate B's job), and it
is allowed to be as inefficient as the existing eager reader/enumeration
already is.
"""

import re


def ascii_fold_unicode(value):
    """Character-level ASCII fold, IDENTICAL algorithm to the real
    Normalizer's own `ascii_fold()` (Gate A2 Part 2): fold ordinals 65-90
    ('A'-'Z') by +32, every other character unchanged. Operates on an
    already-decoded unicode string (the sidecar reader's own eager-decode
    strategy already produces unicode literals, so no additional decoding
    step is needed here)."""
    out = []
    for ch in value:
        o = ord(ch)
        if 65 <= o <= 90:
            out.append(chr(o + 32))
        else:
            out.append(ch)
    return u"".join(out)


def _parse_master_bool_text(value, label, ProbeError):
    if value is None:
        return None
    folded = value.strip().lower()
    if folded in (u"1", u"true", u"yes"):
        return True
    if folded in (u"0", u"false", u"no"):
        return False
    raise ProbeError("Cannot parse Master boolean %s=%r." % (label, value))


def _parse_master_rgba_text(value, label, ProbeError):
    if value is None:
        return None
    nums = re.findall(r"-?\d+", value)
    if len(nums) != 4:
        raise ProbeError("Cannot parse Master RGBA %s=%r." % (label, value))
    rgba = [int(x) for x in nums]
    for component in rgba:
        if component < 0 or component > 255:
            raise ProbeError("Out-of-range Master RGBA %s=%r." % (label, value))
    return rgba


def strip_wrapper(full_path, wrapper_name):
    """Convert a sidecar wrapper-INCLUSIVE full path (e.g.
    'groupFile/Face/Eyes') to the Normalizer's own wrapper-EXCLUSIVE
    convention (e.g. 'Face/Eyes'). A control/group owned directly by the
    wrapper itself maps to the empty string u"", matching the Normalizer's
    own `current_path = u"/".join([])` == u"" at wrapper-scope (Gate A2
    Part 2's exact-conversion requirement -- not silently normalized away)."""
    if full_path == wrapper_name:
        return u""
    prefix = wrapper_name + u"/"
    if full_path.startswith(prefix):
        return full_path[len(prefix):]
    raise ValueError("full_path %r does not start with wrapper %r" % (full_path, wrapper_name))


def build_compatibility_view(provider, wanted_folds, ProbeError):
    """`provider`: an open, VALID, bound `reader.SidecarReader`.
    `wanted_folds`: a set of already-folded unicode strings.
    `ProbeError`: the REAL exception class imported from the extracted
    oracle module, reused here (not re-implemented) so error-type parity
    (Part 9/11) is meaningful -- both sides raise the exact same class."""
    wrapper_name = provider.wrapper_path()

    mapping_count = provider.occurrence_count()

    all_destinations = set()
    folded = {}
    exact_literals = set()
    for occ in provider.iter_occurrences():
        dest = strip_wrapper(occ["full_path"], wrapper_name)
        all_destinations.add(dest)
        literal = occ["literal"]
        fold_key = ascii_fold_unicode(literal)
        if fold_key not in wanted_folds:
            continue
        exact_literals.add(literal)
        folded.setdefault(fold_key, []).append({
            "literal": literal,
            "destination": dest,
            "global_index": occ["global_rank"],
            "local_index": occ["local_rank"],
        })
    destination_count = len(all_destinations)

    group_sibling_order = {u"<ROOT>": []}
    group_metadata = {}
    for g in provider.iter_groups():
        if g["parent_path"] is None:
            # This IS the wrapper group itself -- the Normalizer's own
            # construction never creates a group_sibling_order/group_metadata
            # entry for the wrapper (it is consumed by the initial
            # `take() != "groupFile"` check and never pushed onto `stack`).
            continue

        dest_path = strip_wrapper(g["full_path"], wrapper_name)
        parent_dest = (
            u"<ROOT>" if g["parent_path"] == wrapper_name
            else strip_wrapper(g["parent_path"], wrapper_name)
        )
        group_sibling_order.setdefault(parent_dest, [])
        if g["name"] not in group_sibling_order[parent_dest]:
            group_sibling_order[parent_dest].append(g["name"])
        group_sibling_order.setdefault(dest_path, [])

        meta_entries = list(provider.iter_metadata(g["path_id"]))
        raws = {"groupColor": [], "selectable": [], "visible": [], "snappable": []}
        for e in meta_entries:
            if e["key"] in raws:
                raws[e["key"]].append(e["value"])

        for known_key, rows in raws.items():
            if len(rows) > 1:
                raise ProbeError(
                    "Master group %r has duplicate %s metadata: %r." % (
                        dest_path, known_key + "_raw", rows,
                    )
                )

        color_raw = raws["groupColor"][0] if raws["groupColor"] else None
        selectable_raw = raws["selectable"][0] if raws["selectable"] else None

        group_metadata[dest_path] = {
            "path": dest_path,
            "group_color_explicit": (
                None if color_raw is None
                else _parse_master_rgba_text(color_raw, dest_path + u".groupColor", ProbeError)
            ),
            "selectable_explicit": (
                None if selectable_raw is None
                else _parse_master_bool_text(selectable_raw, dest_path + u".selectable", ProbeError)
            ),
            "selectable_authority": (
                "CANONICAL_NATIVE_POST_DEFAULT" if selectable_raw is None
                else "EXPLICIT_MASTER_FIELD"
            ),
        }

    return {
        "mapping_count": mapping_count,
        "destination_count": destination_count,
        "folded": folded,
        "exact_literals": exact_literals,
        "group_sibling_order": group_sibling_order,
        "group_metadata": group_metadata,
    }


def compat_master_lookup(view, literal):
    """Mirrors the real Normalizer's own `master_lookup()` exactly (Gate A2
    Part 11) -- same result shape, same conflict-raises-on-lookup behavior,
    operating on a compatibility view instead of a TXT-derived one."""
    folded = ascii_fold_unicode(literal)
    rows = view["folded"].get(folded, [])
    if not rows:
        return {
            "known": False, "destination": None, "mode": "NONE",
            "global_index": None, "local_index": None,
        }
    destinations = sorted(set([row["destination"] for row in rows]))
    if len(destinations) != 1:
        raise ValueError(
            "Multiple targeted Master destinations for %r: %r" % (literal, destinations)
        )
    first = sorted(rows, key=lambda row: (row["global_index"], row["local_index"]))[0]
    return {
        "known": True,
        "destination": destinations[0],
        "mode": "EXACT" if literal in view["exact_literals"] else "ASCII_CASEFOLD",
        "global_index": first["global_index"],
        "local_index": first["local_index"],
    }


def compat_validate_master_subset_conflicts(view, wanted_folds):
    """Mirrors the real Normalizer's own `validate_master_subset_conflicts()`
    exactly."""
    conflicts = []
    for folded in wanted_folds:
        rows = view["folded"].get(folded, [])
        if not rows:
            continue
        destinations = sorted(set([row["destination"] for row in rows]))
        if len(destinations) > 1:
            conflicts.append((folded, destinations))
    return conflicts
