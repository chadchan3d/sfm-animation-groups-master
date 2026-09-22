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
EXPECTED_PRODUCTION_SHA256 = "f69a57436d46252fb78d9ae2a2155d7206e07869c74ac5f4d28f6676f5ef2cf0"
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
# position in the file changed. Cross-checked: every relocated range's
# line COUNT matches its pre-integration line count within 0-1 lines
# (the only source of variance being trailing-blank-line trimming, never
# missing/extra code), and every fixture hash this module's callers
# already recorded in R3_B2C_C_plan_layer_ledger.json/R3_B2C_C_execution_
# layer_ledger.json was re-verified to still match EXACTLY after this
# relocation (see R3_Normalizer_Production_Integration_Report.md).

# ===========================================================================
# Exact line ranges (1-indexed, inclusive) extracted verbatim from the
# frozen production file. Re-verify with:
#   sed -n '<start>,<end>p' Rebuild_Control_Groups_Normalizer.py
# Order matters only for readability -- exec() binds all names into one
# shared namespace before anything is called, so forward references
# between these functions resolve fine regardless of extraction order.
# ===========================================================================
PLAN_LAYER_RANGES = [
    ("ProbeError_class", 782, 783),
    ("NativePostFallback_class", 786, 787),
    ("native_ptr", 793, 803),
    ("to_unicode", 825, 835),
    ("ascii_fold", 837, 849),
    ("handle", 851, 852),
    ("name_fn", 854, 858),
    ("typ", 860, 864),
    ("attr", 866, 870),
    ("scalar", 872, 884),
    ("arr", 886, 918),
    ("attribute_name", 920, 924),
    ("attribute_type", 926, 930),
    ("iter_attributes", 932, 955),
    ("element_ref_pairs", 957, 995),
    ("reachable", 997, 1030),
    ("is_visible", 1032, 1044),
    ("is_selectable", 1046, 1055),
    ("is_snappable", 1057, 1066),
    ("_component_value", 1068, 1083),
    ("_parse_rgba_text", 1085, 1108),
    ("group_color_rgba", 1110, 1173),
    ("children", 1175, 1180),
    ("direct_controls", 1182, 1183),
    ("path_string", 1185, 1189),
    ("capture_tree", 1191, 1325),
    ("master_lookup", 1945, 2002),
    ("one_membership", 2004, 2015),
    ("immediate_parent_path", 2017, 2032),
    ("first_path_part", 2034, 2049),
    ("find_direct_child", 2051, 2073),
    ("target_tree_from_rows", 2309, 2347),
    ("source_child_name", 2349, 2369),
    ("pre_child_order", 2371, 2403),
    ("policy_child_order", 2405, 2496),
    ("policy_direct_order", 2498, 2620),
    ("hierarchical_path_rank", 2622, 2677),
    ("order_candidate_rows_by_policy", 2679, 2764),
    ("discover_rig_context", 3290, 3427),
    ("strip_reconciliation_wrapper", 3430, 3445),
    ("canonicalize_rig_source_snapshot", 3448, 3532),
    ("capture_snapshot_explicit", 3535, 3717),
    ("classify_production", 3720, 4319),
    ("_canonicalize_context_path", 5603, 5623),
    ("_active_rig_counterpart_destination", 5626, 5755),
    ("derive_generic_uniformity_plan", 5758, 6337),
]

# `preflight_reconciliation_plan` is a METHOD (uses `self.class_totals`,
# `self.log`, `self.production_mixed_direct_by_target`) -- extracted
# verbatim including its `self` parameter, then called with a minimal
# fake command object providing exactly those three attributes/methods.
# Line range covers the method body only (RebuildControlGroupsProductionRun.
# preflight_reconciliation_plan), verified against the class source.
PREFLIGHT_RECONCILIATION_PLAN_RANGE = (10674, 10808)

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
