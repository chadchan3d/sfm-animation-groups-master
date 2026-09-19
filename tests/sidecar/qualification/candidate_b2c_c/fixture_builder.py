# -*- coding: utf-8 -*-
"""B2C-C: declarative builder for `pre`/`post` rig-state snapshot dicts,
matching EXACTLY the schema the real, frozen `capture_snapshot_explicit`/
`capture_tree` functions are confirmed (by direct reading of their
source, `Rebuild_Control_Groups_Normalizer.py` lines 1013-1148 and
3357-3541) to return. Hand-constructed rather than derived from a fake
native DME object graph -- see the B2C-C report's Section 2 scope
decision for why (this is the fixture-authoring approach, not a
fake-object-model approach; `pre`/`post` do not depend on the Master
authority at all, so a schema-accurate hand fixture is a low-risk,
directly-source-verified substitute here).

`pre` and `post` are IDENTICAL for every fixture in this qualification
(no fixture models an actual mid-transaction rig change) -- the ONLY
input that ever differs between the baseline and migrated comparison
runs is `master`, which is exactly the authority-acquisition seam
B2C-C targets.
"""
import copy

ROOT = u"<ROOT>"


def _immediate_parent(path):
    if path == ROOT:
        return None
    if u"/" not in path:
        return ROOT
    return path.rsplit(u"/", 1)[0]


def build_snapshot(label, groups_spec, control_specs, rig_status="SUPPORTED_ACTIVE_RIG",
                    hidden_groups=None, shot_name=u"shot1", aset_name=u"aset1"):
    """
    groups_spec: {path: {"visible": bool}} -- "<ROOT>" is implicit if
        omitted (always visible). Parent path is derived from the path
        string itself (the same convention `target_tree_from_rows`
        and `path_string` use -- "/"-joined segments).
    control_specs: list of dicts, each:
        {"name": ..., "path": <group path the control sits in>,
         "type": "DmeTransformControl" (default) or other,
         "owned": bool (rig-owned, default False)}
    hidden_groups: list of group paths considered `hiddenGroups` on the
        rig registry (pre['hidden_groups'] / used by classify_production
        via `hidden = set(pre["hidden_groups"])`).
    """
    hidden_groups = hidden_groups or []
    groups_spec = dict(groups_spec)
    groups_spec.setdefault(ROOT, {"visible": True})

    # Compute child_names_in_order per parent from the path set (root
    # always first-declared; order here is deterministic — insertion
    # order of groups_spec, which the caller controls explicitly).
    all_paths = list(groups_spec.keys())
    children_of = {}
    for p in all_paths:
        parent = _immediate_parent(p)
        if parent is not None:
            children_of.setdefault(parent, []).append(p.rsplit(u"/", 1)[-1] if u"/" in p else p)

    direct_controls_of = {}
    for c in control_specs:
        direct_controls_of.setdefault(c["path"], []).append(c["name"])

    # effective_visible = ancestor_visible AND own visible, walked from root.
    effective = {}

    def compute_effective(path):
        if path in effective:
            return effective[path]
        parent = _immediate_parent(path)
        ancestor_visible = True if parent is None else compute_effective(parent)
        own_visible = groups_spec[path]["visible"]
        effective[path] = bool(ancestor_visible and own_visible)
        return effective[path]

    for p in all_paths:
        compute_effective(p)

    groups = {}
    for p in all_paths:
        parent = _immediate_parent(p)
        groups[p] = {
            "path": p,
            "name": ROOT if p == ROOT else p.rsplit(u"/", 1)[-1],
            "parent_path": parent,
            "visible": groups_spec[p]["visible"],
            "effective_visible": effective[p],
            "selectable": True,
            "snappable": True,
            "group_color": [255, 255, 255, 255],
            "child_names_in_order": children_of.get(p, []),
            "direct_control_names_in_order": direct_controls_of.get(p, []),
        }

    memberships = {}
    control_names_in_order = []
    control_handles = {}
    control_types = {}
    owned_names = []
    for i, c in enumerate(control_specs):
        cname = c["name"]
        control_names_in_order.append(cname)
        control_handles[cname] = 1000 + i
        control_types[cname] = c.get("type", u"DmeTransformControl")
        memberships.setdefault(cname, []).append(c["path"])
        if c.get("owned", False):
            owned_names.append(cname)

    return {
        "label": label,
        "shot_name": shot_name, "shot_handle": 1,
        "animation_set_name": aset_name, "animation_set_handle": 2,
        "root_handle": 3,
        "rig_status": rig_status,
        "rig_name": u"rig1" if rig_status == "SUPPORTED_ACTIVE_RIG" else None,
        "rig_handle": 4 if rig_status == "SUPPORTED_ACTIVE_RIG" else None,
        "registry_handle": 5 if rig_status == "SUPPORTED_ACTIVE_RIG" else None,
        "matching_rig_count": 1 if rig_status == "SUPPORTED_ACTIVE_RIG" else 0,
        "reachable_rig_count": 1 if rig_status == "SUPPORTED_ACTIVE_RIG" else 0,
        "control_count": len(control_names_in_order),
        "control_names_in_animation_set_order": control_names_in_order,
        "duplicate_control_names": {},
        "control_handles": control_handles,
        "control_types": control_types,
        "owned_control_names_in_animation_set_order": owned_names,
        "owned_control_name_set": sorted(owned_names),
        "hidden_groups": list(hidden_groups),
        "group_count": len(groups),
        "groups": groups,
        "memberships": memberships,
        "duplicate_sibling_groups": [],
        "duplicate_direct_controls": [],
        "duplicate_memberships": {},
        "rig_recon_exists": False,
        "master_recon_exists": False,
    }


def build_pre_post_pair(label, groups_spec, control_specs, **kwargs):
    """The overwhelming majority of B2C-C's decisive fixtures model a
    STATIC rig (native Rebuild does not itself move anything -- Master-
    driven reconciliation is entirely downstream of it) -- pre and post
    are therefore byte-identical snapshots, differing only in `label`.
    A fixture that wants pre != post (to exercise the PARENT_COLLAPSE /
    MASTER_NORMALIZATION categories, which require `pre_path !=
    post_path` for an owned control) passes `post_overrides`.

    Returns (pre, post, post_groups_spec, post_control_specs) -- the
    raw POST spec is also returned (not just the built dict) so the
    execution-layer harness (`fake_dme.build_world`) can construct a
    LIVE fake tree in the exact POST physical state, from the SAME
    declarative source of truth as this decision-layer `post` dict --
    never two independently-authored fixtures that could silently
    drift apart."""
    post_overrides = kwargs.pop("post_overrides", None)
    pre = build_snapshot("PRE_" + label, groups_spec, control_specs, **kwargs)
    if post_overrides is None:
        post = copy.deepcopy(pre)
        post["label"] = "POST_" + label
        return pre, post, groups_spec, control_specs

    post_groups_spec, post_control_specs = post_overrides
    post = build_snapshot("POST_" + label, post_groups_spec, post_control_specs, **kwargs)
    return pre, post, post_groups_spec, post_control_specs
