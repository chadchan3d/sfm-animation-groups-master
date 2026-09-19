# -*- coding: utf-8 -*-
"""B2C-C execution-layer continuation: verbatim extraction of the frozen
production Normalizer's native-mutation EXECUTION layer --
`production_generic_composer` and its complete dependency closure --
extending `production_plan_layer.py`'s already-qualified DECISION-layer
namespace (never re-extracting it separately; one shared namespace, one
extraction pass, exactly matching the governing prompt's Section 6
"execution-layer code itself should be byte-identical... except for the
authority seam" requirement -- the decision-layer functions inside this
namespace are the SAME extracted bytes already proven 37/37 in
`test_b2c_c_plan_layer_equivalence.py`).

Dependency map (Section 2 of the governing prompt) -- every function
below traced by direct source reading, never guessed:

| Function | Frozen lines | Reads from target/DME | Writes/mutations | Native dependency | Intercepted? |
|---|---:|---|---|---|---:|
| set_visible | 1897-1921 | group.IsVisible (fallback only) | group.SetVisible | native `SetVisible` | via fake object's own method |
| set_selectable | 1922-1938 | - | group.SetSelectable | native `SetSelectable` | via fake object |
| set_snappable | 1939-1955 | - | group.SetSnappable | native `SetSnappable` | via fake object |
| set_group_color | 1956-1988 | group.GroupColor (verify) | group.SetGroupColor | native `SetGroupColor`, `vs.Color` | via fake object (vs.Color faked, see fake_dme.FakeColor) |
| apply_source_metadata | 1989-2012 | - | calls the 4 above | (none directly) | transitively |
| create_independent_group | 2013-2064 | children(parent), handle() | root.CreateControlGroup, parent.AddChild, set_visible | native `CreateControlGroup`, `AddChild` | via fake object |
| add_control_to_group | 2065-2077 | - | group.AddControl | native `AddControl` (exclusive membership -- see fake_dme docstring) | via fake object |
| rename_group | 2078-2105 | handle(group), name(group) | group.SetName | native `SetName` | via fake object |
| technical_group_name | 2106-2121 | - | (pure string builder) | none | n/a |
| live_control_map | 2122-2130 | arr(aset,"controls"), name() | - | read-only | n/a |
| production_resolve_group_path | 6161-6182 | find_direct_child (tree walk) | - | read-only | n/a |
| production_master_metadata_path | 6183-6241 | master dict only | - | pure | n/a |
| production_source_paths_for_target | 6242-6310 | - | - | pure | n/a |
| production_source_meta_for_target | 6311-6352 | pre/post/rig_source dicts | - | pure | n/a |
| production_raw_selectable | 6353-6366 | scalar(group,"selectable") | - | native `GetAttribute` fallback | via fake object |
| production_apply_explicit_master_metadata | 6367-6411 | master dict | set_group_color, set_selectable | (transitive) | via fake object |
| production_apply_active_group_policy | 6412-6470 | pre/post/rig_source, master | set_visible/selectable/snappable/group_color, explicit-metadata | (transitive) | via fake object |
| production_ensure_group_path | 6471-6570 | find_direct_child (tree walk) | create_independent_group, apply_source_metadata/set_visible, rename_group, production_apply_active_group_policy | (transitive) | via fake object |
| production_reorder_children_by_master | 6571-6744 | children(parent), name(), handle() | parent.RemoveChild (ALL children), parent.AddChild (desired order) | native `RemoveChild`+`AddChild` -- **direct native calls, not through a wrapper function** | via fake object |
| production_reorder_contextual_tree | 6745-6806 | production_resolve_group_path | calls production_reorder_children_by_master for <ROOT> + 6 rig branches | (transitive) | via fake object |
| production_claim_destination | 6807-6860 | - | mutates a plain `desired` dict (not DME) | none | n/a |
| production_apply_exact_master_destination_total_order | 6861-6974 | master_lookup, _canonicalize_context_path | mutates a plain `by_target` dict (not DME) | none | n/a |
| production_generic_composer | 6975-7924 | discover_rig_context+capture_snapshot_explicit (BEFORE and AFTER, on `shot`/`aset`), live_control_map(aset), children(root) | production_ensure_group_path (create groups), add_control_to_group (move controls), set_visible (toe hide, RigHelpers), production_apply_explicit_master_metadata (RigHelpers), production_reorder_contextual_tree (sibling reorder) | orchestrates every mutation above; also re-derives `after` via a SECOND real discover_rig_context/capture_snapshot_explicit call on the (now-mutated) fake tree, then raises ProbeError on ANY of ~15 postcondition checks | via fake object (transitively, through everything it calls) |

Identity/equality/ordering assumptions confirmed by direct reading (never
inferred): group/control identity is by `handle()` (`int(obj.GetHandle())`,
assigned once, never reassigned by rename/reparent); `AddControl`
implies EXCLUSIVE membership (a control belongs to exactly one group at
a time in real SFM -- confirmed indirectly: `production_generic_composer`'s
own postcondition checks `duplicate_memberships` must be empty in `after`,
and NO code path anywhere calls a "RemoveControl"-equivalent before
`AddControl`, so exclusivity must be a NATIVE-side guarantee of the real
`AddControl` implementation, not something the Python layer arranges --
`fake_dme.py`'s `AddControl` therefore also enforces it); group-list
`RemoveChild`/`AddChild` reordering preserves `handle()` identity for
every child (explicitly verified by the extracted `production_reorder_
children_by_master` code itself, lines ~6724-6740, which we exec
UNCHANGED); collection reads always go through `arr()`/`attr()`
(never index a native collection by position directly), so `fake_dme`'s
`GetAttribute` returning a plain Python list is sufficient (verified in
`production_plan_layer.py`'s own `arr()`/`attr()` extraction, reused
unchanged from that module -- `arr()`'s own fallback path handles a
plain list via `len()`/`__getitem__`, needing no `.Count()` wrapper).

DEAD-CODE EXCLUSION (verified, not assumed): `build_visible_layer`,
`capture_direct_anchor_state`, `direct_anchor_preflight`,
`build_direct_anchor`, `validate_direct_anchor` (lines 2588-3111) are
defined in the frozen file but never called from anywhere outside their
own small mutual cluster (grep-confirmed: zero call sites in
`run_target_transaction`, `production_generic_composer`, or any other
reachable function) -- excluded from this extraction, not because they
were overlooked, but because they are provably unreachable from every
fixture this qualification exercises.
"""
import hashlib

import production_plan_layer as ppl

_THIS_DIR = ppl._THIS_DIR
DEFAULT_PRODUCTION_PATH = ppl.DEFAULT_PRODUCTION_PATH
EXPECTED_PRODUCTION_SHA256 = ppl.EXPECTED_PRODUCTION_SHA256

EXECUTION_LAYER_RANGES = [
    ("set_visible", 1897, 1921),
    ("set_selectable", 1922, 1938),
    ("set_snappable", 1939, 1955),
    ("set_group_color", 1956, 1988),
    ("apply_source_metadata", 1989, 2012),
    ("create_independent_group", 2013, 2064),
    ("add_control_to_group", 2065, 2077),
    ("rename_group", 2078, 2105),
    ("technical_group_name", 2106, 2121),
    ("live_control_map", 2122, 2130),
    ("production_resolve_group_path", 6161, 6182),
    ("production_master_metadata_path", 6183, 6241),
    ("production_source_paths_for_target", 6242, 6310),
    ("production_source_meta_for_target", 6311, 6352),
    ("production_raw_selectable", 6353, 6366),
    ("production_apply_explicit_master_metadata", 6367, 6411),
    ("production_apply_active_group_policy", 6412, 6470),
    ("production_ensure_group_path", 6471, 6570),
    ("production_reorder_children_by_master", 6571, 6744),
    ("production_reorder_contextual_tree", 6745, 6806),
    ("production_claim_destination", 6807, 6860),
    ("production_apply_exact_master_destination_total_order", 6861, 6974),
    ("production_generic_composer", 6975, 7924),
    # --- Eligibility-gate authority-sensitive island (see this module's
    # own docstring "authority-dependency cut" note below): the ENTIRE
    # rest of the eligibility gate (MDL header parsing, bone counting,
    # follower detection, snapshot_work's scene walk) never references
    # `master` at all (grep-confirmed) -- only `_gate_is_alh` does, via
    # `master_lookup`. Extracted here as a small, separately-testable
    # pure(ish) function: `_gate_is_alh(aset, master)` needs only
    # `aset.controls` (already in fake_dme's FakeDmeAnimationSet), no
    # scene/shot/rig graph at all.
    ("_gate_normalized_token", 8264, 8275),
    ("_gate_path_segments", 8276, 8288),
    ("_gate_has_arm_segment", 8289, 8310),
    ("_gate_has_leg_segment", 8311, 8332),
    ("_gate_literal_head_neck_token", 8333, 8368),
    ("_gate_has_head_path_segment", 8369, 8381),
    ("_gate_transform_controls", 8382, 8414),
    ("_gate_is_alh", 8415, 8463),
]


def build_full_namespace(production_path=None):
    """Returns (ns, blocks) with BOTH the decision layer (already
    qualified, 37/37) and the execution layer bound in ONE shared
    namespace -- the SAME decision-layer bytes `production_plan_layer.
    build_plan_layer_namespace` extracts, extended with the execution-
    layer ranges above. `vs` is intentionally never imported here --
    `set_group_color`'s one `vs.Color(...)` call site is satisfied by
    `fake_dme.py` installing a lightweight stand-in as `ns["vs"]`
    before that function is ever invoked (see fake_dme.install_fake_vs)."""
    ns, blocks = ppl.build_plan_layer_namespace(production_path)
    ns["re"] = __import__("re")  # needed by _gate_literal_head_neck_token
    if production_path is None:
        production_path = DEFAULT_PRODUCTION_PATH
    lines = ppl._read_production_lines(production_path)
    for label, start, end in EXECUTION_LAYER_RANGES:
        src = ppl._extract(lines, start, end)
        blocks.append((label, src))
        _exec_into(src, ns)
    return ns, blocks


def _exec_into(src, ns):
    """Isolated in its own top-level function -- same Python-2 compiler
    restriction noted in authority_pair.py's `_exec_into`."""
    exec(compile(src, "<production_execution_layer_extract>", "exec"), ns)
