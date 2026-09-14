# -*- coding: utf-8 -*-
"""R1 -- QUALIFICATION-ONLY sidecar-to-Normalizer-consumer-contract projection.
NOT production code. Never imported by `tools/sfm_master_sidecar/*.py`, never
imported by the production Normalizer.

Builds TWO separate projections from an already-open bounded sidecar provider
(S1, `bounded_provider.BoundedProvider`), matching the two REAL, independently
verified (by direct source reading) Normalizer consumer contracts exactly:

  - `build_manual_projection`: the exact shape `parse_targeted_master()`
    returns in the real, currently-installed
    `Rebuild_Control_Groups_Normalizer.py` -- `mapping_count`/
    `destination_count` are WHOLE-SOURCE; `folded`/`exact_literals` are
    scoped to the requested folds; `group_sibling_order`/`group_metadata`
    cover EVERY group (not just requested ones); `group_metadata` carries
    raw per-key lists (`groupColor_raw`/`selectable_raw`/`visible_raw`/
    `snappable_raw`, duplicate-raising if any list has more than one entry)
    plus promoted `group_color_explicit`/`selectable_explicit`/
    `selectable_authority` fields -- exactly the real manual parser's
    contract, confirmed by direct reading of
    `Rebuild_Control_Groups_Normalizer.py` lines ~1416-1723.

  - `build_live_master120`: the exact shape `t120_parse_master()` returns in
    the real T120/T130 live lineage -- `sha256`/`total_controls` (also
    whole-source)/`target_conflicts` plus `folded`/`exact_literals` scoped
    to requested folds, and `group_metadata` using the live parser's own
    `explicit_fields` set + `snap`-as-alias-for-`snappable` + duplicate
    -canonical-key rejection, confirmed by direct reading of
    `SFM_20260910_T130_LiveTrigger20sOrdinaryUseRequalification.py` lines
    ~1229-1330.

Neither function reimplements `master_lookup`/`validate_master_subset_conflicts`/
`t120_master_lookup`/`t130_t95_master_from_t120` -- those REAL functions
(imported read-only via `normalizer_oracle_import.py`) are called directly
against the dicts these two functions build, exactly as a real Normalizer
run would call them against its own TXT-derived dict. This module only
supplies the missing half: turning a bounded sidecar provider into a dict
shaped exactly like what the real TXT parsers would have produced.
"""


def _parse_rgba(value, label, probe_error_cls, real_parse_rgba_fn):
    return real_parse_rgba_fn(value, label)


def build_manual_projection(provider, bounded_view_module, wanted_folds, probe_error_cls,
                             real_parse_master_rgba_text, real_parse_master_bool_text):
    """Matches the real `parse_targeted_master()` contract exactly. Raises
    `probe_error_cls` (the REAL Normalizer's own `ProbeError`, passed in by
    the caller) on a duplicate raw metadata occurrence, exactly like the
    real parser."""
    wrapper_name = provider.wrapper_path()
    wanted_folds = set(wanted_folds)

    folded = {}
    exact_literals = set()
    for fold_key in wanted_folds:
        result = provider.lookup_fold(fold_key.encode("utf-8"))
        if result.__class__.__name__ == "MasterUnknown":
            continue
        rows = []
        for occ in result.occurrences():
            dest = bounded_view_module.strip_wrapper(occ["full_path"], wrapper_name)
            rows.append({
                "literal": occ["literal"], "destination": dest,
                "global_index": occ["global_rank"], "local_index": occ["local_rank"],
            })
        rows.sort(key=lambda r: r["global_index"])
        folded[fold_key] = rows
        for r in rows:
            exact_literals.add(r["literal"])

    group_sibling_order = {u"<ROOT>": []}
    group_metadata = {}
    field_map = {
        "groupColor": "groupColor_raw", "selectable": "selectable_raw",
        "visible": "visible_raw", "snappable": "snappable_raw",
    }
    for g in provider.iter_groups():
        if g["parent_path"] is None:
            continue
        dest_path = bounded_view_module.strip_wrapper(g["full_path"], wrapper_name)
        parent_dest = (
            u"<ROOT>" if g["parent_path"] == wrapper_name
            else bounded_view_module.strip_wrapper(g["parent_path"], wrapper_name)
        )
        group_sibling_order.setdefault(parent_dest, [])
        if g["name"] not in group_sibling_order[parent_dest]:
            group_sibling_order[parent_dest].append(g["name"])
        group_sibling_order.setdefault(dest_path, [])

        raws = {"groupColor_raw": [], "selectable_raw": [], "visible_raw": [], "snappable_raw": []}
        for e in provider.iter_metadata(g["path_id"]):
            target_field = field_map.get(e["key"])
            if target_field is not None:
                raws[target_field].append(e["value"])

        for raw_key, rows in raws.items():
            if len(rows) > 1:
                raise probe_error_cls(
                    "Master group %r has duplicate %s metadata: %r." % (dest_path, raw_key, rows)
                )

        color_raw = raws["groupColor_raw"][0] if raws["groupColor_raw"] else None
        selectable_raw = raws["selectable_raw"][0] if raws["selectable_raw"] else None

        meta = {"path": dest_path}
        meta.update(raws)
        meta["group_color_explicit"] = (
            None if color_raw is None
            else real_parse_master_rgba_text(color_raw, dest_path + u".groupColor")
        )
        meta["selectable_explicit"] = (
            None if selectable_raw is None
            else real_parse_master_bool_text(selectable_raw, dest_path + u".selectable")
        )
        meta["selectable_authority"] = (
            "CANONICAL_NATIVE_POST_DEFAULT" if selectable_raw is None else "EXPLICIT_MASTER_FIELD"
        )
        group_metadata[dest_path] = meta

    return {
        "mapping_count": provider.occurrence_count(),
        "destination_count": provider.destination_count(),
        "folded": folded,
        "exact_literals": exact_literals,
        "group_sibling_order": group_sibling_order,
        "group_metadata": group_metadata,
    }


_LIVE_METADATA_KEYS = ("groupColor", "selectable", "visible", "snappable", "snap")


def build_live_master120(provider, bounded_view_module, wanted_folds, probe_error_cls, source_sha256):
    """Matches the real `t120_parse_master()` contract exactly, including
    the `snap` alias for `snappable` and duplicate-canonical-key rejection.
    `sha256` is supplied by the caller (the same command-boundary-hashed
    value used elsewhere in this qualification arc) rather than recomputed
    here, since this function's input is the sidecar provider, not the raw
    TXT path `t120_sha256` would stream."""
    wrapper_name = provider.wrapper_path()
    wanted_folds = set(wanted_folds)

    folded = {}
    exact_literals = set()
    for fold_key in wanted_folds:
        result = provider.lookup_fold(fold_key.encode("utf-8"))
        if result.__class__.__name__ == "MasterUnknown":
            continue
        rows = []
        for occ in result.occurrences():
            dest = bounded_view_module.strip_wrapper(occ["full_path"], wrapper_name)
            rows.append({
                "literal": occ["literal"], "destination": dest,
                "global_index": occ["global_rank"], "local_index": occ["local_rank"],
            })
        rows.sort(key=lambda r: r["global_index"])
        folded[fold_key] = rows
        for r in rows:
            exact_literals.add(r["literal"])

    group_sibling_order = {u"<ROOT>": []}
    group_metadata = {}
    for g in provider.iter_groups():
        if g["parent_path"] is None:
            continue
        dest_path = bounded_view_module.strip_wrapper(g["full_path"], wrapper_name)
        parent_dest = (
            u"<ROOT>" if g["parent_path"] == wrapper_name
            else bounded_view_module.strip_wrapper(g["parent_path"], wrapper_name)
        )
        group_sibling_order.setdefault(parent_dest, [])
        if g["name"] not in group_sibling_order[parent_dest]:
            group_sibling_order[parent_dest].append(g["name"])
        group_sibling_order.setdefault(dest_path, [])

        explicit_fields = set()
        meta = {"groupColor": None, "selectable": None, "visible": None, "snappable": None,
                 "explicit_fields": explicit_fields}
        for e in provider.iter_metadata(g["path_id"]):
            key = e["key"]
            if key not in _LIVE_METADATA_KEYS:
                continue
            canon = u"snappable" if key == "snap" else key
            if canon in explicit_fields:
                raise probe_error_cls("Duplicate Master metadata %r.%s" % (dest_path, canon))
            explicit_fields.add(canon)
            meta[canon] = e["value"]
        group_metadata[dest_path] = meta

    conflicts = []
    for ff, rows in folded.items():
        dests = sorted(set(r["destination"] for r in rows))
        if len(dests) > 1:
            conflicts.append((ff, tuple(dests)))

    return {
        "sha256": source_sha256,
        "folded": folded,
        "exact_literals": exact_literals,
        "group_metadata": group_metadata,
        "group_sibling_order": group_sibling_order,
        "total_controls": provider.occurrence_count(),
        "target_conflicts": tuple(conflicts),
    }
