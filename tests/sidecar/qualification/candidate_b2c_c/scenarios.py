# -*- coding: utf-8 -*-
"""B2C-C fixture/scope matrix: named (pre, post, wanted_folds) scenarios,
each targeting a specific classify_production category or structural
edge case named in the governing prompt's Section 6. Every scenario's
`pre`/`post` pair is IDENTICAL between the baseline and migrated
comparison runs -- only `master` (computed separately per run from the
real frozen parser vs. the qualified adapter) differs.

Each scenario also records `post_groups_spec`/`post_control_specs`/
`rig_status`/`hidden_groups` -- the SAME raw declarative spec used to
build the decision-layer `post` dict is reused, unchanged, to build the
execution-layer's LIVE fake-DME world (`fake_dme.build_world`), so the
two layers can never silently drift apart into two different physical
starting states for "the same" fixture.
"""
from fixture_builder import build_pre_post_pair, ROOT

SCENARIOS = {}


def _register(name, pre, post, post_groups_spec, post_control_specs, wanted_folds, note,
               rig_status="SUPPORTED_ACTIVE_RIG", hidden_groups=None):
    SCENARIOS[name] = {
        "pre": pre, "post": post,
        "post_groups_spec": post_groups_spec, "post_control_specs": post_control_specs,
        "rig_status": rig_status, "hidden_groups": hidden_groups or [],
        "wanted_folds": wanted_folds, "note": note,
    }


# ---------------------------------------------------------------------
# A.1 -- No-op / static baseline: nothing moved, nothing hidden. Every
# owned control stays exactly where it already is. Exercises the
# "already correct, do nothing" path -- the most common real case.
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "noop",
    groups_spec={ROOT: {"visible": True}, u"RigArms": {"visible": True}},
    control_specs=[{"name": u"valve.l_upperarm", "path": u"RigArms", "owned": True}],
)
_register("A1_noop_static", pre, post, pgs, pcs, {u"valve.l_upperarm"},
           "control already correctly placed and visible; classify_production should emit no rows for it")

# ---------------------------------------------------------------------
# A.2 -- RIG_OWNED_EFFECTIVE_CONTROL (rig_losses): native Rebuild left a
# previously-visible rig-owned group invisible in POST. Exercises the
# rig-loss reconstruction path, which Master authority (destination
# path) ultimately re-homes.
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "rig_loss",
    groups_spec={ROOT: {"visible": True}, u"RigArms": {"visible": True}},
    control_specs=[{"name": u"valve.l_upperarm", "path": u"RigArms", "owned": True}],
    post_overrides=(
        {ROOT: {"visible": True}, u"RigArms": {"visible": False}},
        [{"name": u"valve.l_upperarm", "path": u"RigArms", "owned": True}],
    ),
)
_register("A2_rig_owned_effective_control", pre, post, pgs, pcs, {u"valve.l_upperarm"},
           "RigArms visible in PRE, invisible in POST -- classic native-Rebuild rig loss")

# ---------------------------------------------------------------------
# A.3 -- MASTER_KNOWN_BUT_STRANDED: a non-rig-owned control sits in a
# group that is (a) hidden (registered in hidden_groups) and (b) IS the
# control's own Master-known destination -- i.e. Master already agrees
# with where it physically is, but the group itself is hidden.
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "master_stranded",
    groups_spec={ROOT: {"visible": True}, u"HiddenGroup": {"visible": True}, u"RigArms": {"visible": True}},
    control_specs=[
        {"name": u"stranded_control", "path": u"HiddenGroup", "owned": False},
        # Bugfix (B2C-C Final Expansion Fixtures round): this fixture
        # originally had ZERO genuinely rig-owned controls while still
        # declaring rig_status="SUPPORTED_ACTIVE_RIG" -- the fake
        # world's OWN discover_rig_context therefore computed the REAL,
        # distinct status "STALE_ZERO_OWNERSHIP_RIG" (empty owned/
        # registry intersection), which production_generic_composer's
        # own postcondition unconditionally rejects (it is never reached
        # with anything but a genuine SUPPORTED_ACTIVE_RIG in real
        # production -- confirmed by the upstream gate in run_target_
        # transaction, ~line 11177). Both baseline and migrated raised
        # the IDENTICAL ProbeError, which the comparison technically
        # "matched" without ever exercising composer at all -- a masked
        # mutual failure, found and disclosed, not a real PASS. Fixed by
        # adding a genuinely rig-owned, already-correctly-placed,
        # unrelated anchor control (reusing A1's proven no-op pattern)
        # so the fake world's rig ownership is real.
        {"name": u"valve.l_upperarm", "path": u"RigArms", "owned": True},
    ],
    post_overrides=(
        {ROOT: {"visible": True}, u"HiddenGroup": {"visible": False}, u"RigArms": {"visible": True}},
        [
            {"name": u"stranded_control", "path": u"HiddenGroup", "owned": False},
            {"name": u"valve.l_upperarm", "path": u"RigArms", "owned": True},
        ],
    ),
    hidden_groups=[u"HiddenGroup"],
)
_register("A3_master_known_but_stranded", pre, post, pgs, pcs, {u"stranded_control", u"valve.l_upperarm"},
           "non-owned control's own group matches its Master destination exactly, but that group is hidden "
           "(plus a genuinely rig-owned, already-correctly-placed anchor control, so this fixture's rig is "
           "genuinely SUPPORTED_ACTIVE_RIG and can reach production_generic_composer)",
           hidden_groups=[u"HiddenGroup"])

# ---------------------------------------------------------------------
# A.4 -- RIG_OWNED_VISIBLE_PARENT_COLLAPSE: an owned, visible control
# moved from a nested path to its own immediate parent between PRE/POST.
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "parent_collapse",
    groups_spec={ROOT: {"visible": True}, u"RigArms": {"visible": True},
                 u"RigArms/Sub": {"visible": True}},
    control_specs=[{"name": u"collapsing_control", "path": u"RigArms/Sub", "owned": True}],
    post_overrides=(
        {ROOT: {"visible": True}, u"RigArms": {"visible": True}},
        [{"name": u"collapsing_control", "path": u"RigArms", "owned": True}],
    ),
)
_register("A4_rig_owned_visible_parent_collapse", pre, post, pgs, pcs, {u"collapsing_control"},
           "owned+visible control collapsed from RigArms/Sub (PRE) to its immediate parent RigArms (POST)")

# ---------------------------------------------------------------------
# A.5 -- RIG_OWNED_VISIBLE_MASTER_NORMALIZATION: an owned, visible
# control moved to a DIFFERENT (non-parent) path between PRE/POST, and
# that new path happens to already equal Master's own destination for
# it -- Master and native POST already agree; this classification
# proves the plan/uniformity layer correctly recognizes "already
# normalized" without asking for a redundant move.
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "master_normalization",
    groups_spec={ROOT: {"visible": True}, u"RigArms": {"visible": True},
                 u"RigLegs": {"visible": True}},
    control_specs=[{"name": u"normalizing_control", "path": u"RigArms", "owned": True}],
    post_overrides=(
        {ROOT: {"visible": True}, u"RigArms": {"visible": True}, u"RigLegs": {"visible": True}},
        [{"name": u"normalizing_control", "path": u"RigLegs", "owned": True}],
    ),
)
_register("A5_rig_owned_visible_master_normalization", pre, post, pgs, pcs, {u"normalizing_control"},
           "owned+visible control moved RigArms(PRE) -> RigLegs(POST), matching its own Master destination exactly")

# ---------------------------------------------------------------------
# B.1 -- ASCII-fold match (not exact literal): control name differs
# from Master's stored literal only by ASCII case -- exercises
# master_lookup's ASCII_CASEFOLD mode, not EXACT.
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "ascii_fold_match",
    groups_spec={ROOT: {"visible": True}, u"HiddenGroup": {"visible": True}, u"RigArms": {"visible": True}},
    control_specs=[
        {"name": u"Stranded_Control", "path": u"HiddenGroup", "owned": False},
        # Bugfix (see A3's note): genuine rig-owned anchor control so
        # this fixture's rig is genuinely SUPPORTED_ACTIVE_RIG.
        {"name": u"valve.l_upperarm", "path": u"RigArms", "owned": True},
    ],
    post_overrides=(
        {ROOT: {"visible": True}, u"HiddenGroup": {"visible": False}, u"RigArms": {"visible": True}},
        [
            {"name": u"Stranded_Control", "path": u"HiddenGroup", "owned": False},
            {"name": u"valve.l_upperarm", "path": u"RigArms", "owned": True},
        ],
    ),
    hidden_groups=[u"HiddenGroup"],
)
_register("B1_ascii_fold_match", pre, post, pgs, pcs, {u"stranded_control", u"valve.l_upperarm"},
           "control literal 'Stranded_Control' differs from the folded wanted-vocabulary entry only by ASCII "
           "case (plus a genuinely rig-owned anchor control, see A3's fixed-bug note)",
           hidden_groups=[u"HiddenGroup"])

# ---------------------------------------------------------------------
# B.2 -- valid MasterUnknown/unmatched: control genuinely absent from
# Master, sitting in a nested (non-<ROOT>) PRE group, native POST places
# it under "Unknown" -- exercises the MASTER_UNKNOWN_RESIDUAL_CANDIDATE
# path (a single, non-"strong" candidate; expected to fall through to
# AMBIGUOUS_DIAGNOSTIC_ONLY/unresolved_owned_drift, not master_unknown_
# unknown, since the "strong" test requires >=2 corroborating peers).
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "master_unknown",
    groups_spec={ROOT: {"visible": True}, u"SomeGroup": {"visible": True}},
    control_specs=[{"name": u"totally_unmapped_control", "path": u"SomeGroup", "owned": True}],
    post_overrides=(
        {ROOT: {"visible": True}, u"Unknown": {"visible": True}},
        [{"name": u"totally_unmapped_control", "path": u"Unknown", "owned": True}],
    ),
)
_register("B2_master_unknown_unmatched", pre, post, pgs, pcs, set(),
           "control absent from the wanted-fold vocabulary entirely; native POST routes it to Unknown")

# ---------------------------------------------------------------------
# B.3 -- nested group paths / sibling ordering: two owned controls both
# collapsing from distinct nested paths into the same parent, exercising
# order_candidate_rows_by_policy's sibling-ordering logic across two rows
# in one call, both consulting Master's group_sibling_order.
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "sibling_order",
    groups_spec={ROOT: {"visible": True}, u"RigArms": {"visible": True},
                 u"RigArms/A": {"visible": True}, u"RigArms/B": {"visible": True}},
    control_specs=[
        {"name": u"sibling_control_a", "path": u"RigArms/A", "owned": True},
        {"name": u"sibling_control_b", "path": u"RigArms/B", "owned": True},
    ],
    post_overrides=(
        {ROOT: {"visible": True}, u"RigArms": {"visible": True}},
        [
            {"name": u"sibling_control_a", "path": u"RigArms", "owned": True},
            {"name": u"sibling_control_b", "path": u"RigArms", "owned": True},
        ],
    ),
)
_register("B3_nested_sibling_ordering", pre, post, pgs, pcs, {u"sibling_control_a", u"sibling_control_b"},
           "two owned controls both parent-collapse into RigArms from distinct nested paths -- exercises ordering "
           "across multiple simultaneous rows")

# ---------------------------------------------------------------------
# B.4 -- left/right side normalization: two structurally-identical
# controls differing only by an 'l'/'r' side token, both stranded.
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "side_normalization",
    groups_spec={ROOT: {"visible": True}, u"HiddenGroup": {"visible": True}, u"RigArms": {"visible": True}},
    control_specs=[
        {"name": u"valve.l_hand", "path": u"HiddenGroup", "owned": False},
        {"name": u"valve.r_hand", "path": u"HiddenGroup", "owned": False},
        # Bugfix (see A3's note): genuine rig-owned anchor control.
        {"name": u"valve.l_upperarm", "path": u"RigArms", "owned": True},
    ],
    post_overrides=(
        {ROOT: {"visible": True}, u"HiddenGroup": {"visible": False}, u"RigArms": {"visible": True}},
        [
            {"name": u"valve.l_hand", "path": u"HiddenGroup", "owned": False},
            {"name": u"valve.r_hand", "path": u"HiddenGroup", "owned": False},
            {"name": u"valve.l_upperarm", "path": u"RigArms", "owned": True},
        ],
    ),
    hidden_groups=[u"HiddenGroup"],
)
_register("B4_left_right_side_normalization", pre, post, pgs, pcs,
           {u"valve.l_hand", u"valve.r_hand", u"valve.l_upperarm"},
           "paired left/right controls, both master-known-but-stranded under the same hidden group (plus a "
           "genuinely rig-owned anchor control, see A3's fixed-bug note)",
           hidden_groups=[u"HiddenGroup"])

# ---------------------------------------------------------------------
# C.1 -- unrigged target: rig_status UNRIGGED entirely (no rig-owned
# controls at all) -- exercises the non-rig-owned/master_stranded-only
# path with zero rig-loss/parent-collapse/master-normalization activity.
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "unrigged",
    groups_spec={ROOT: {"visible": True}, u"HiddenGroup": {"visible": True}},
    control_specs=[{"name": u"unrigged_stranded", "path": u"HiddenGroup", "owned": False}],
    post_overrides=(
        {ROOT: {"visible": True}, u"HiddenGroup": {"visible": False}},
        [{"name": u"unrigged_stranded", "path": u"HiddenGroup", "owned": False}],
    ),
    hidden_groups=[u"HiddenGroup"],
    rig_status="UNRIGGED",
)
_register("C1_unrigged_target", pre, post, pgs, pcs, {u"unrigged_stranded"},
           "rig_status=UNRIGGED throughout -- no rig-owned controls, only a non-owned master-stranded control",
           rig_status="UNRIGGED", hidden_groups=[u"HiddenGroup"])

# ---------------------------------------------------------------------
# D.1 -- Active-rig TOE RELOCATION (B2C-C Final Expansion Fixtures,
# Fixture A). Canonical model-backed toe controls sit in "Toes/LeftToes"/
# "Toes/RightToes" (a MODEL-level group, not rig-owned) -- with an
# active RigLegs rig present (has_riglegs=True), derive_generic_
# uniformity_plan's `model_leaf_specs`/`model_translations` mechanism
# relocates them to "RigLegs/LeftLeg/LeftToes"/"RigLegs/RightLeg/
# RightToes" REGARDLESS of whether the rig itself owns any dedicated toe
# controls (it doesn't, here -- only "leg_owned_control" is rig-owned,
# an unrelated leg control that must be preserved untouched). This path
# never consults `master_lookup` for the toe controls at all (driven
# purely by the canonical "Toes/..." group naming convention), so it
# exercises a DIFFERENT authority-sensitive mechanism than the other 10
# fixtures (has_riglegs itself IS authority-independent -- it's derived
# from `rig_source`, not `master` -- but the OVERALL uniformity_plan/
# composer pipeline this control flows through is the same authority-
# sensitive execution closure already mapped in Section 18).
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "toe_relocation",
    groups_spec={
        ROOT: {"visible": True},
        u"RigLegs": {"visible": True},
        u"RigLegs/LeftLeg": {"visible": True},
        u"RigLegs/RightLeg": {"visible": True},
        u"Toes": {"visible": True},
        u"Toes/LeftToes": {"visible": True},
        u"Toes/RightToes": {"visible": True},
    },
    control_specs=[
        {"name": u"leg_owned_control", "path": u"RigLegs", "owned": True},
        {"name": u"canon_toe_l", "path": u"Toes/LeftToes", "owned": False},
        {"name": u"canon_toe_r", "path": u"Toes/RightToes", "owned": False},
    ],
)
_register("D1_active_rig_toe_relocation", pre, post, pgs, pcs,
           {u"leg_owned_control", u"canon_toe_l", u"canon_toe_r"},
           "canonical model-backed toe controls (Toes/LeftToes, Toes/RightToes) relocate beneath "
           "RigLegs/LeftLeg/Toes and RigLegs/RightLeg/Toes purely from an active RigLegs rig's "
           "presence, even though the rig owns no dedicated toe control itself; an unrelated "
           "rig-owned leg control must be preserved untouched")

# ---------------------------------------------------------------------
# D.2 -- RigBody family-counterpart refinement (RENAMED, B2C-C Targeted
# Audit Correction, 2026-09-19). This fixture was ORIGINALLY registered
# as "D2_tail_relocation" claiming to satisfy Fixture C ("Tail
# relocation"). The independent audit correctly found this claim
# unsupported: it declared a SYNTHETIC "Body/Tail/tail_control" Master
# entry that does not match the REAL canonical Master's actual structure
# (sfm_defaultanimationgroups.txt declares "Tail" as a ROOT-LEVEL group,
# a direct sibling of "Body"/"RigBody"/etc, never nested under "Body" --
# grep/structural-parse-confirmed), it always reported
# already_correct_count=1/moved_count=0 (never actually created or moved
# a control into any group named "Tail"), and it silently refined the
# destination back to "RigBody" -- a real, legitimate, already-qualified
# mechanism, but not a demonstration of Tail placement at all.
#
# RETAINED (per the correction prompt's explicit allowance) as what it
# actually is: a genuine demonstration of `_active_rig_counterpart_
# destination`'s RigBody-family refinement (lines 5480-5493) -- a
# rig-owned control whose CURRENT (fresh-PRE) rig-visible path is
# exactly "RigBody", left hidden in native POST (classic RIG_OWNED_
# EFFECTIVE_CONTROL / rig_losses, same category as fixture A2), whose
# Master destination is the ordinary anatomical "Body" -- refined by the
# active-rig-counterpart mechanism to the bare "RigBody" root. This is
# useful, valid evidence for that mechanism; it is NOT, and is no longer
# claimed to be, a Tail fixture. See D6 below for the corrected Tail
# relocation fixture, and the report's Tail-disposition section for the
# full correction record.
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "rigbody_family_counterpart_refinement",
    groups_spec={ROOT: {"visible": True}, u"RigBody": {"visible": True}},
    control_specs=[{"name": u"rigbody_family_control", "path": u"RigBody", "owned": True}],
    post_overrides=(
        {ROOT: {"visible": True}, u"RigBody": {"visible": False}},
        [{"name": u"rigbody_family_control", "path": u"RigBody", "owned": True}],
    ),
)
_register("D2_rigbody_family_counterpart_refinement", pre, post, pgs, pcs, {u"rigbody_family_control"},
           "NOT a Tail fixture (renamed from D2_tail_relocation during the B2C-C targeted audit "
           "correction -- see the report). rig-owned rigbody_family_control's rig-visible PRE path "
           "is RigBody (visible), hidden in native POST (classic rig-loss); Master destination "
           "'Body' is refined by _active_rig_counterpart_destination to the active RigBody root -- "
           "the same active-rig-family-counterpart mechanism as fixture A, applied to the RigBody "
           "family. Retained as valid evidence for this mechanism only.")

# ---------------------------------------------------------------------
# D.3 -- repeated-control preservation (B2C-C Final Expansion Fixtures,
# Fixture D). Two controls that fold to the SAME literal (differing only
# by exact-vs-ASCII-fold spelling, matching this project's established
# "native-Rebuild casefold" concept) both legitimately exist as separate
# animation-set controls, each independently classified/placed --
# proving no valid repeated placement is incorrectly collapsed, and no
# extra duplicate membership is introduced. Both are non-owned,
# master-known-but-stranded under the SAME hidden group (reusing B4's
# proven category), but with DISTINCT exact literals sharing one folded
# key.
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "repeated_control",
    groups_spec={ROOT: {"visible": True}, u"HiddenGroup": {"visible": True}, u"RigArms": {"visible": True}},
    control_specs=[
        {"name": u"stranded_control", "path": u"HiddenGroup", "owned": False},
        {"name": u"Stranded_Control", "path": u"HiddenGroup", "owned": False},
        # Bugfix (see A3's note): genuine rig-owned anchor control.
        {"name": u"valve.l_upperarm", "path": u"RigArms", "owned": True},
    ],
    post_overrides=(
        {ROOT: {"visible": True}, u"HiddenGroup": {"visible": False}, u"RigArms": {"visible": True}},
        [
            {"name": u"stranded_control", "path": u"HiddenGroup", "owned": False},
            {"name": u"Stranded_Control", "path": u"HiddenGroup", "owned": False},
            {"name": u"valve.l_upperarm", "path": u"RigArms", "owned": True},
        ],
    ),
    hidden_groups=[u"HiddenGroup"],
)
_register("D3_repeated_control_preservation", pre, post, pgs, pcs, {u"stranded_control", u"valve.l_upperarm"},
           "two DISTINCT exact-literal controls ('stranded_control', 'Stranded_Control') sharing "
           "one ASCII-folded key both legitimately exist and are independently classified/placed "
           "-- neither is dropped, collapsed, or given an extra duplicate membership (plus a "
           "genuinely rig-owned anchor control, see A3's fixed-bug note)",
           hidden_groups=[u"HiddenGroup"])

# ---------------------------------------------------------------------
# D.4 -- untouched custom/unrelated group preservation (B2C-C Final
# Expansion Fixtures, Fixture E). REDESIGNED during the B2C-C Targeted
# Audit Correction (2026-09-19): the ORIGINAL design declared root
# children as {"CustomUserGroup", "RigArms"} -- `fake_dme.build_world`
# creates root-level groups in ALPHABETICAL order regardless of
# groups_spec declaration order ("CustomUserGroup" < "RigArms"), while
# the REAL `production_reorder_children_by_master`'s `desired` order for
# <ROOT> always places every Master-KNOWN group ("RigArms") before every
# CONTEXTUAL/unknown group ("CustomUserGroup") -- so `current_names`
# ["CustomUserGroup", "RigArms"] never equalled `desired` ["RigArms",
# "CustomUserGroup"], and the (real, frozen, always-unconditional-when-
# order-differs) RemoveChild-all/AddChild-all root reorder genuinely
# fired, touching the custom group even though ITS OWN position among
# siblings was never semantically wrong for any Master reason -- an
# independent audit correctly rejected the resulting "zero native
# mutations" claim.
#
# FIX (verified empirically, not assumed): `production_reorder_
# children_by_master` has an early-exit -- `if desired == current_names:
# return desired` -- BEFORE any RemoveChild/AddChild call (frozen source,
# line ~6650). Renaming the custom group to "UserCustomGroup" (which
# sorts AFTER "RigArms" alphabetically, matching where a contextual group
# always lands in `desired` anyway) makes `current_names` already equal
# `desired` for <ROOT> -- confirmed by direct execution: mutation_count
# == 0 for this exact fixture. `UserCustomGroup` is also not one of the
# 6 named branches `production_reorder_contextual_tree` recurses into
# (RigArms/RigArms/LeftArm/RigArms/RightArm/RigLegs/RigLegs/LeftLeg/
# RigLegs/RightLeg), so its OWN children are never reorder-candidates
# regardless of their order.
#
# Non-trivial per the correction prompt's explicit requirements: two
# custom child groups in a known order (Alpha, Beta -- alphabetically
# created in that order by the SAME fake_dme sorting rule), two custom
# controls, non-default selectable/snappable/group_color on
# UserCustomGroup and its children, and one child (Beta) non-default-
# visible. `fixture_builder.build_snapshot`/`fake_dme.build_world` were
# both extended with OPTIONAL per-group `selectable`/`snappable`/
# `group_color` keys (defaulting to the SAME True/True/[255,255,255,255]
# every pre-existing fixture already relies on -- zero behavior change
# for any fixture that omits them) to make this representable at all.
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "untouched_custom_group",
    groups_spec={
        ROOT: {"visible": True},
        u"RigArms": {"visible": True},
        u"UserCustomGroup": {"visible": True, "selectable": False, "snappable": False,
                              "group_color": [11, 22, 33, 255]},
        u"UserCustomGroup/Alpha": {"visible": True, "group_color": [44, 55, 66, 255]},
        u"UserCustomGroup/Beta": {"visible": False, "selectable": False, "snappable": True},
    },
    control_specs=[
        {"name": u"valve.l_upperarm", "path": u"RigArms", "owned": True},
        {"name": u"custom_control_alpha", "path": u"UserCustomGroup/Alpha", "owned": False},
        {"name": u"custom_control_beta", "path": u"UserCustomGroup/Beta", "owned": False},
    ],
)
_register("D4_untouched_custom_group_preservation", pre, post, pgs, pcs, {u"valve.l_upperarm"},
           "a pre-existing custom/unrelated subtree (UserCustomGroup/{Alpha,Beta}, with two custom "
           "controls and non-default selectable/snappable/group_color/visible metadata) that no "
           "rig ownership, Master mapping, or classification touches, AND whose root-level position "
           "already matches the generic reorder function's own 'known-before-contextual' desired "
           "order (so the reorder's early-exit fires and zero RemoveChild/AddChild calls touch "
           "<ROOT> at all) -- only valve.l_upperarm (already correctly placed) is in scope. "
           "RENAMED/REDESIGNED from the original CustomUserGroup design during the B2C-C targeted "
           "audit correction, which correctly found that design's root children never reached the "
           "reorder function's early-exit -- see the report's custom-subtree-disposition section.")

# ---------------------------------------------------------------------
# D.5 -- flex-first visible ordering (B2C-C Final Expansion Fixtures,
# Fixture B). Grep-confirmed: the frozen source has NO literal "flex"/
# "Face"/"Eyes"/"Clothing" special-cased ordering rule anywhere -- the
# REAL canonical Master (sfm_defaultanimationgroups.txt, lines 43-54)
# explicitly documents "There is no universal rule that flexes should
# precede bones" -- ordering is entirely DATA-driven, reproduced by the
# GENERIC ordering machinery, specifically `policy_direct_order` (lines
# 2320-2442): when 2+ Master-EXACT-known controls share one `relative_
# path` cohort, they are sorted by real Master `(global_index,
# local_index)` -- i.e. their DECLARATION ORDER in the Master TXT.
#
# Design note (verified empirically, not assumed): a control whose
# physical POST location already equals its FINAL target_path is
# "already correct" and never reaches `add_control_to_group` at all
# (confirmed: this is what A3/A5/master_stranded/master_normalization
# fixtures correctly do -- they are GROUP-visibility-restoration cases,
# never control moves). To get a REAL, OBSERVABLE `add_control_to_group`
# ordering effect, both controls must share ONE nested rig-visible PRE
# path ("RigArms/Sub") that differs from their physical POST location
# ("RigArms") -- the SAME "preserve the runtime specificity" refinement
# mechanism fixture A4/B3 use (`_active_rig_counterpart_destination`
# preserves the more-specific PRE path over Master's broad "RigArms"
# root when PRE proves it), which forces a genuine technical-group
# recreation + `add_control_to_group` for both. Both controls are
# declared in the shared Master TXT's "RigArms" group in this EXACT
# order (flex first) -- their real global_index/local_index reflect it,
# and `policy_direct_order` places both in the SAME `by_path["RigArms/
# Sub"]` cohort (authority="MASTER"), sorted by that declared order --
# this is the decision layer's own (already-qualified, 37/37) ordering
# mechanism, now observed all the way through to the real native
# `add_control_to_group` call order.
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "flex_first_ordering",
    groups_spec={ROOT: {"visible": True}, u"RigArms": {"visible": True}, u"RigArms/Sub": {"visible": True}},
    control_specs=[
        {"name": u"eye_flex_control", "path": u"RigArms/Sub", "owned": True},
        {"name": u"eye_bone_control", "path": u"RigArms/Sub", "owned": True},
    ],
    post_overrides=(
        {ROOT: {"visible": True}, u"RigArms": {"visible": True}},
        [
            {"name": u"eye_flex_control", "path": u"RigArms", "owned": True},
            {"name": u"eye_bone_control", "path": u"RigArms", "owned": True},
        ],
    ),
)
_register("D5_flex_first_ordering", pre, post, pgs, pcs, {u"eye_flex_control", u"eye_bone_control"},
           "two owned controls both parent-collapse from the SAME nested RigArms/Sub path into "
           "RigArms, both Master-exact-known (flex declared before bone in the authority Master "
           "TXT) -- policy_direct_order's cohort ordering by real Master global_index/local_index "
           "determines the exact order add_control_to_group is called in")

# ---------------------------------------------------------------------
# D.6 -- Tail relocation, CORRECTED (B2C-C Targeted Audit Correction,
# 2026-09-19, Fixture C). Replaces the disclaimed D2 design (see D2's
# own note above and the report's Tail-disposition section).
#
# Case A finding (see the report for the full derivation): the REAL
# canonical Master (sfm_defaultanimationgroups.txt, line 116343)
# declares "Tail" as a ROOT-LEVEL group -- a direct sibling of "Body"/
# "RigBody"/"RigArms"/etc, structurally confirmed by a full parent-path
# walk of every indent-1 group in the file. No Tail-specific Normalizer
# runtime branch exists anywhere in the 13,594-line frozen source
# (grep-confirmed: zero case-insensitive "tail" matches). "Tail
# relocation" is therefore a Master-taxonomy fact only, reconciled by
# the SAME generic machinery every other destination uses -- exercised
# here via the SAME RIG_OWNED_EFFECTIVE_CONTROL / "rig_losses" category
# fixture A2 already uses (an owned, visible control whose OWN group
# becomes hidden in native POST), just pointed at the synthetic Master's
# real root-level "Tail" group instead of a rig-family destination.
# Verified empirically (not assumed) to produce a genuine, observable
# relocation: `production_generic_composer` creates a NEW "Tail" group,
# calls `add_control_to_group` for BOTH controls (source_path=
# "WrongGroup", destination_path="Tail"), and the destination order
# (tail_control_a before tail_control_b) is derived from the real Master
# declaration order via `EXACT_MASTER_DESTINATION_TOTAL_ORDER` --
# exactly the same order-authority mechanism D5 already qualified,
# applied here to a genuinely-created (not merely already-correct)
# destination group.
# ---------------------------------------------------------------------
pre, post, pgs, pcs = build_pre_post_pair(
    "tail_relocation",
    groups_spec={ROOT: {"visible": True}, u"WrongGroup": {"visible": True}},
    control_specs=[
        {"name": u"tail_control_a", "path": u"WrongGroup", "owned": True},
        {"name": u"tail_control_b", "path": u"WrongGroup", "owned": True},
    ],
    post_overrides=(
        {ROOT: {"visible": True}, u"WrongGroup": {"visible": False}},
        [
            {"name": u"tail_control_a", "path": u"WrongGroup", "owned": True},
            {"name": u"tail_control_b", "path": u"WrongGroup", "owned": True},
        ],
    ),
)
_register("D6_tail_relocation", pre, post, pgs, pcs, {u"tail_control_a", u"tail_control_b"},
           "CORRECTED Tail relocation fixture (replaces the disclaimed D2 design). Two rig-owned "
           "controls whose own group (WrongGroup) is visible in PRE, hidden in native POST (classic "
           "RIG_OWNED_EFFECTIVE_CONTROL / rig-loss, same category as fixture A2); Master destination "
           "is the REAL canonical Master's actual root-level 'Tail' group (verified structurally "
           "against sfm_defaultanimationgroups.txt) -- production_generic_composer genuinely creates "
           "'Tail' and moves both controls into it, in Master-declared order")
