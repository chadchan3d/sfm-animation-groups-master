# -*- coding: utf-8 -*-
"""B2C-C: verbatim extraction of the frozen production Normalizer's
DOWNSTREAM DECISION LAYER -- the pure, dict-in/dict-out functions that
decide WHAT should move where, given the authority (`master`) dict plus
a fixed rig-state (`pre`/`post`) snapshot. This is the exact seam B2C-C
targets: `master` is the ONLY input that differs between the frozen-
parser baseline and the migrated qualified-authority-adapter candidate.

Scope decision (see R3_B2C_C_Downstream_Mutation_Equivalence_Report.md
Section 2 for the full justification): this module extracts and exec's
the REAL, UNMODIFIED source of:

  - classify_production(pre, post, master)
  - order_candidate_rows_by_policy(rows, master, source)
  - derive_generic_uniformity_plan(pre, post, master, plan)
  - `preflight_reconciliation_plan` (a method on `RebuildControlGroups
    ProductionRun` in production, using `self.class_totals`, `self.log`,
    `self.production_mixed_direct_by_target`): the REAL method body is
    extracted byte-for-byte, dedented one level, and re-bound under the
    new top-level name `preflight_reconciliation_plan_pure` -- ONLY the
    `def` line's function name changes; the `self` parameter is left
    named `self` (Python does not care what a positional parameter is
    called, so this is not a body edit). Callers pass a minimal fake
    command-shim object positionally in `self`'s place, providing only
    the three attributes/methods the body actually reads.

plus every pure helper function these four call, transitively -- ALL
extracted by exact line range from the real frozen production file,
never re-typed or reimplemented from memory. Every range below is
recorded explicitly so it can be independently re-verified against the
production file.

DELIBERATELY EXCLUDED (the native-mutation EXECUTION layer --
`production_generic_composer` and its ~15-function closure, the 7
native-call wrapper functions `set_visible`/`set_selectable`/
`set_snappable`/`set_group_color`/`apply_source_metadata`/
`create_independent_group`/`add_control_to_group`/`rename_group`,
`build_visible_layer`/`build_direct_anchor`/`capture_direct_anchor_
state`/`direct_anchor_preflight`/`validate_direct_anchor`, and anything
requiring a live/faked SFM DME object graph): faithfully replaying this
layer requires a substantially larger, harder-to-validate fake native
object model (DME element handle/attribute/iteration protocol) than
this qualification round's effort budget supports with the confidence
this project requires before claiming equivalence. This is reported
explicitly as UNCOVERED SCOPE, never silently skipped -- see the
report's coverage table.

Never imports `vs`/`sfmApp`/`sfmClipEditor`/PySide -- verified by grep
that none of the extracted ranges reference them (the one hit found
during research, `vs.Color` inside `set_group_color`, is in the
deliberately-excluded execution layer).
"""
import hashlib
import json
import os

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PRODUCTION_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py"
)
EXPECTED_PRODUCTION_SHA256 = "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"
# 2026-09-22 Production Normalizer Integration: the frozen file's own
# line numbers shifted (a qualified-authority bootstrap block was
# inserted near the top of the file, plus two new methods and a small
# native-file-protection hook, at the file's own existing Master-index-
# build call site and per-target transaction method) -- every range
# below was relocated by NAME (grep for `def <name>(`/`class <name>(` at
# the same column-0/4-space indentation as before, end = the line before
# the next same-indentation def/class, trailing blank lines trimmed),
# never by a constant line-number offset. None of the DOWNSTREAM
# function BODIES extracted below changed by even one byte -- only their
# position in the file changed.
#
# 2026-09-22 correction 2 (independent-audit fail-closed native-Master-
# protect fix): the frozen file changed AGAIN (a docstring update inside
# native_master_protect_acquire() and a fail-closed call-site addition in
# run_target_transaction(), both additive) -- every range below was
# relocated a SECOND time by the SAME name-based method, via an automated
# script (zero manual line-number entry). Every relocated range's line
# COUNT matches its immediately-prior count EXACTLY (delta 0 for all 46
# entries + the preflight_reconciliation_plan method range -- confirmed
# programmatically, not merely "within 0-1 lines"), and every fixture
# hash this module's callers already recorded in R3_B2C_C_plan_layer_
# ledger.json/R3_B2C_C_execution_layer_ledger.json was re-verified to
# still match EXACTLY after this second relocation.

# ===========================================================================
# Exact line ranges (1-indexed, inclusive) extracted verbatim from the
# frozen production file. Re-verify with:
#   sed -n '<start>,<end>p' Rebuild_Control_Groups_Normalizer.py
# Order matters only for readability -- exec() binds all names into one
# shared namespace before anything is called, so forward references
# between these functions resolve fine regardless of extraction order.
# ===========================================================================
PLAN_LAYER_RANGES = [
    ("ProbeError_class", 791, 792),
    ("NativePostFallback_class", 795, 796),
    ("native_ptr", 802, 812),
    ("to_unicode", 834, 844),
    ("ascii_fold", 846, 858),
    ("handle", 860, 861),
    ("name_fn", 863, 867),
    ("typ", 869, 873),
    ("attr", 875, 879),
    ("scalar", 881, 893),
    ("arr", 895, 927),
    ("attribute_name", 929, 933),
    ("attribute_type", 935, 939),
    ("iter_attributes", 941, 964),
    ("element_ref_pairs", 966, 1004),
    ("reachable", 1006, 1039),
    ("is_visible", 1041, 1053),
    ("is_selectable", 1055, 1064),
    ("is_snappable", 1066, 1075),
    ("_component_value", 1077, 1092),
    ("_parse_rgba_text", 1094, 1117),
    ("group_color_rgba", 1119, 1182),
    ("children", 1184, 1189),
    ("direct_controls", 1191, 1192),
    ("path_string", 1194, 1198),
    ("capture_tree", 1200, 1334),
    ("master_lookup", 1954, 2011),
    ("one_membership", 2013, 2024),
    ("immediate_parent_path", 2026, 2041),
    ("first_path_part", 2043, 2058),
    ("find_direct_child", 2060, 2082),
    ("target_tree_from_rows", 2318, 2356),
    ("source_child_name", 2358, 2378),
    ("pre_child_order", 2380, 2412),
    ("policy_child_order", 2414, 2505),
    ("policy_direct_order", 2507, 2629),
    ("hierarchical_path_rank", 2631, 2686),
    ("order_candidate_rows_by_policy", 2688, 2773),
    ("discover_rig_context", 3299, 3436),
    ("strip_reconciliation_wrapper", 3439, 3454),
    ("canonicalize_rig_source_snapshot", 3457, 3541),
    ("capture_snapshot_explicit", 3544, 3726),
    ("classify_production", 3729, 4328),
    ("_canonicalize_context_path", 5612, 5632),
    ("_active_rig_counterpart_destination", 5635, 5764),
    ("derive_generic_uniformity_plan", 5767, 6346),
]

# `preflight_reconciliation_plan` is a METHOD (uses `self.class_totals`,
# `self.log`, `self.production_mixed_direct_by_target`) -- extracted
# verbatim including its `self` parameter, then called with a minimal
# fake command object providing exactly those three attributes/methods.
# Line range covers the method body only (RebuildControlGroupsProductionRun.
# preflight_reconciliation_plan), verified against the class source.
PREFLIGHT_RECONCILIATION_PLAN_RANGE = (10683, 10817)

MODULE_CONSTANTS = {
    "RIG_RECON_ROOT": "__RIG_VISIBLE_RECON__",
    "MASTER_RECON_ROOT": "__MASTER_VISIBLE_RECON__",
}


def _read_production_lines(production_path):
    with open(production_path, "rb") as f:
        data = f.read()
    actual_sha = hashlib.sha256(data).hexdigest()
    if actual_sha != EXPECTED_PRODUCTION_SHA256:
        raise AssertionError(
            "frozen production Normalizer SHA-256 mismatch: expected %s, got %s -- "
            "refusing to extract from a file that is not the pinned frozen production "
            "candidate" % (EXPECTED_PRODUCTION_SHA256, actual_sha)
        )
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError:
        text = data.decode("utf-8")
    return text.splitlines()


def _extract(lines, start, end):
    """1-indexed, inclusive line range -> source text block (never
    dedented -- every extracted range starts at column 0, either a
    top-level `def`/`class`, or (for the method range) a `    def`
    whose body is separately re-indented by the caller)."""
    return "\n".join(lines[start - 1:end]) + "\n"


def build_plan_layer_namespace(production_path=None):
    """Returns a fresh namespace dict with every plan-layer function
    bound, extracted verbatim from the real frozen production file at
    `production_path` (defaults to the real installed SFM copy). Also
    returns the list of (name, source_text) pairs actually extracted,
    for auditability/hashing."""
    if production_path is None:
        production_path = DEFAULT_PRODUCTION_PATH
    lines = _read_production_lines(production_path)

    blocks = []
    for label, start, end in PLAN_LAYER_RANGES:
        blocks.append((label, _extract(lines, start, end)))

    combined_source = "\n\n".join(src for _, src in blocks)

    ns = dict(MODULE_CONSTANTS)
    try:
        unicode  # noqa: F821
    except NameError:
        raise RuntimeError(
            "production_plan_layer must run under a Python 2 interpreter -- "
            "the extracted source uses the Python-2-only `unicode`/`xrange` "
            "builtins directly, exactly as the frozen production file does."
        )
    exec(compile(combined_source, "<production_plan_layer_extract>", "exec"), ns)

    # preflight_reconciliation_plan: extracted as a method (with `self`),
    # re-bound under a new top-level FUNCTION NAME only -- the `self`
    # parameter itself is left named `self` in the body (no body text is
    # rewritten); callers pass a fake command shim positionally.
    method_src = _extract(lines, PREFLIGHT_RECONCILIATION_PLAN_RANGE[0], PREFLIGHT_RECONCILIATION_PLAN_RANGE[1])
    # The method is indented one level (4 spaces, class body) -- dedent
    # by exactly 4 spaces per line before re-parsing as a free function.
    dedented_lines = []
    for line in method_src.splitlines():
        if line.startswith("    "):
            dedented_lines.append(line[4:])
        elif line.strip() == "":
            dedented_lines.append(line)
        else:
            dedented_lines.append(line)
    dedented_src = "\n".join(dedented_lines) + "\n"
    # Rename the leading `self` parameter to `cmd` (first occurrence of
    # the parameter name only, in the `def` line) -- alpha-rename, body
    # references to `self.` are left untouched by using a `cmd`-named
    # local inside a thin trampoline instead of rewriting the body text.
    renamed_src = dedented_src.replace(
        "def preflight_reconciliation_plan(\n        self,",
        "def preflight_reconciliation_plan_pure(\n        self,",
        1,
    )
    exec(compile(renamed_src, "<preflight_reconciliation_plan_extract>", "exec"), ns)
    blocks.append(("preflight_reconciliation_plan_pure(method, self-param retained)", renamed_src))

    return ns, blocks


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"), default=str)


def sha_of(obj):
    s = canonical_json(obj)
    if isinstance(s, unicode):  # noqa: F821 -- Python 2 only, by design (see build_plan_layer_namespace)
        s = s.encode("utf-8")
    return hashlib.sha256(s).hexdigest()
