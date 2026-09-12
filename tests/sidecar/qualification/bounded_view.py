# -*- coding: utf-8 -*-
"""GATE B -- QUALIFICATION-ONLY fast/bounded Normalizer master_view builder
for the S1 `BoundedProvider`.

Reuses the frozen Gate A2 contract and its exact conversions (wrapper-strip,
narrow 4-key metadata projection, duplicate-raises) VERBATIM from
`gate_a2_compat_producer.py` -- this module changes ONLY how the `folded`/
`exact_literals` fields are computed: instead of a single O(occurrence_count)
scan over every occurrence in the generation (what
`gate_a2_compat_producer.build_compatibility_view` does, and what the
eager production `SidecarReader` necessarily costs), this builder does
O(len(wanted_folds) * log(fold_count)) FOLD TABLE probes, each one decoding
only that fold's own occurrence family -- never the whole table.

`mapping_count`/`destination_count` remain GLOBAL/unscoped per the frozen
contract, and are obtained here in O(1)/O(group_count) respectively, from
`BoundedProvider.occurrence_count()` / `BoundedProvider.destination_count()`
-- never by iterating occurrences at all, bounded or otherwise.

`group_sibling_order`/`group_metadata` are already bounded in
`BoundedProvider` (group_count/metadata_row_count, not occurrence_count/
fold_count), so that half of the construction is reused unchanged in
structure from `gate_a2_compat_producer.build_compatibility_view` -- only
retargeted at `BoundedProvider.iter_groups()`/`iter_metadata()`.
"""

import re


def ascii_fold_unicode(value):
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
    if full_path == wrapper_name:
        return u""
    prefix = wrapper_name + u"/"
    if full_path.startswith(prefix):
        return full_path[len(prefix):]
    raise ValueError("full_path %r does not start with wrapper %r" % (full_path, wrapper_name))


def build_view_bounded(provider, wanted_folds, ProbeError):
    """`provider`: an open `BoundedProvider` (S1). `wanted_folds`: a set of
    already-folded unicode strings. `ProbeError`: the real oracle exception
    class, reused for error-type parity exactly as Gate A2 required.

    Cost shape (Gate B's whole point): O(1) for mapping_count,
    O(group_count) for destination_count/hierarchy/metadata, and
    O(len(wanted_folds) * log(fold_count) + total occurrences actually
    owned by those specific folds) for folded/exact_literals -- NEVER
    O(total occurrence_count) or O(total fold_count) for the scoped part."""
    wrapper_name = provider.wrapper_path()

    mapping_count = provider.occurrence_count()
    destination_count = provider.destination_count()

    folded = {}
    exact_literals = set()
    for fold_key in wanted_folds:
        result = provider.lookup_fold(fold_key.encode("utf-8"))
        if result.__class__.__name__ == "MasterUnknown":
            continue
        rows = []
        for occ in result.occurrences():
            dest = strip_wrapper(occ["full_path"], wrapper_name)
            literal = occ["literal"]
            exact_literals.add(literal)
            rows.append({
                "literal": literal,
                "destination": dest,
                "global_index": occ["global_rank"],
                "local_index": occ["local_rank"],
            })
        rows.sort(key=lambda r: r["global_index"])
        folded[fold_key] = rows

    group_sibling_order = {u"<ROOT>": []}
    group_metadata = {}
    for g in provider.iter_groups():
        if g["parent_path"] is None:
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
    conflicts = []
    for folded in wanted_folds:
        rows = view["folded"].get(folded, [])
        if not rows:
            continue
        destinations = sorted(set([row["destination"] for row in rows]))
        if len(destinations) > 1:
            conflicts.append((folded, destinations))
    return conflicts
