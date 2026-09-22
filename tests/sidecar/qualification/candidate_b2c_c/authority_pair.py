# -*- coding: utf-8 -*-
"""B2C-C: builds the ONE shared synthetic Master TXT fixture (covering
every control literal every scenario in scenarios.py needs), compiles
it once via the REAL production sidecar compiler, and exposes two
functions that compute `master` for a given `wanted_folds` set:

  compute_baseline_master(wanted_folds)  -- calls the REAL, frozen
      production `parse_targeted_master(...)`, extracted verbatim by
      the SAME PROD_RANGES line-slicing every prior semantic-regression
      test in this project already used (never re-derived here).

  compute_migrated_master(wanted_folds)  -- calls the QUALIFIED
      Correction6 candidate's `normalizer_compat_adapter.
      build_targeted_master_compatible_projection(wanted_folds)(provider)`,
      with `provider` opened against the SAME compiled sidecar (i.e. the
      SAME underlying Master content), via the qualified candidate's own
      broker/selection machinery -- never a hand-rolled substitute.

Both authority-path assertions required by the governing prompt's
Section 8 are enforced here as hard, load-time facts: the baseline
function's own extracted source (verified via the same static text-scan
+ compiled-code-object co_names technique `test_b2c_b_mutation_absence_
proof.py` already established in this project) never references the
qualified candidate authority package, and the migrated function's
source never references `parse_targeted_master`.
"""
import hashlib
import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir, os.pardir))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
CORRECTION6_ROOT = os.path.join(_THIS_DIR, os.pardir, "candidate_b2c_correction6")
FIXROOT = os.path.join(_THIS_DIR, "fixtures_authority")

PRODUCTION_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py"
)
EXPECTED_PRODUCTION_SHA256 = "f69a57436d46252fb78d9ae2a2155d7206e07869c74ac5f4d28f6676f5ef2cf0"

# Identical extraction ranges to every prior semantic-regression test in
# this project (test_b2c_correction6_semantic_regression.py etc.) --
# BufferedChars/stream_tokens/parse_master_bool_text/parse_master_rgba_text/
# parse_targeted_master, plus the tiny READ_BLOCK constant and the
# ProbeError/ContextualCompositionSuccess exception classes it raises.
#
# 2026-09-22 Production Normalizer Integration: relocated by NAME (same
# methodology as production_plan_layer.py's PLAN_LAYER_RANGES) -- READ_
# BLOCK's own line (138) is unchanged since it sits before every edit
# this integration made; every other range shifted. No function body
# changed, only line position -- every range's line COUNT matches its
# pre-integration count within 0-1 lines (trailing-blank-line trimming
# only).
PROD_RANGES = [
    (138, 138), (782, 783), (825, 835), (837, 849),
    (1347, 1379), (1382, 1516), (1518, 1548), (1551, 1591), (1594, 1901),
]

# ---------------------------------------------------------------------
# The ONE shared synthetic Master TXT covering every control literal
# every scenario needs. "totally_unmapped_control" (B2's genuinely-
# unknown control) is deliberately ABSENT.
# ---------------------------------------------------------------------
MASTER_TXT_BODY = (
    u'"RigArms"\n'
    u"{\n"
    u'\t"control"\t\t"valve.l_upperarm"\n'
    u'\t"control"\t\t"collapsing_control"\n'
    u'\t"control"\t\t"sibling_control_a"\n'
    u'\t"control"\t\t"sibling_control_b"\n'
    # B2C-C Final Expansion Fixtures -- Fixture B (flex-first ordering):
    # declared in this EXACT order (flex first) so their real
    # global_index/local_index reflect it. Both map to "RigArms" and
    # both physically sit at the SAME nested rig-visible pre_path
    # ("RigArms/Sub") -- the active-rig-family refinement rule
    # (_active_rig_counterpart_destination, "preserve the runtime
    # specificity") keeps their target_path at "RigArms/Sub" rather than
    # collapsing to the broad "RigArms" root, so BOTH land in the SAME
    # `policy_direct_order` cohort -- exercising the decision layer's
    # own Master global_index/local_index tie-break ordering (already
    # qualified 37/37), now observed all the way through to the ORDER
    # of real `add_control_to_group` native calls.
    u'\t"control"\t\t"eye_flex_control"\n'
    u'\t"control"\t\t"eye_bone_control"\n'
    u"}\n"
    u'"RigLegs"\n'
    u"{\n"
    u'\t"control"\t\t"normalizing_control"\n'
    u"}\n"
    u'"HiddenGroup"\n'
    u"{\n"
    u'\t"control"\t\t"stranded_control"\n'
    u'\t"control"\t\t"valve.l_hand"\n'
    u'\t"control"\t\t"valve.r_hand"\n'
    u'\t"control"\t\t"unrigged_stranded"\n'
    u"}\n"
    # B2C-C Targeted Audit Correction (2026-09-19) -- D2 was RENAMED from
    # "Tail relocation" to "RigBody family-counterpart refinement" (it
    # never satisfied Fixture C -- see the corrected report). Kept as an
    # ordinary anatomical "Body" destination, refined to the active-rig
    # counterpart "RigBody" by _active_rig_counterpart_destination when
    # fresh PRE proves the control is currently RigBody-rooted.
    u'"Body"\n'
    u"{\n"
    u'\t"control"\t\t"rigbody_family_control"\n'
    u"}\n"
    # B2C-C Targeted Audit Correction -- D6 (the CORRECTED Tail
    # relocation fixture, Fixture C). The REAL canonical Master
    # (sfm_defaultanimationgroups.txt, line 116343) declares "Tail" as a
    # ROOT-LEVEL group -- a direct sibling of "Body"/"RigBody"/"RigArms"/
    # etc, NOT nested under "Body" (grep-confirmed via structural
    # parsing; see the report's Tail-disposition section). Declared here,
    # at root level, matching that real structure exactly. Two controls,
    # in this declared order, so a genuine relocation into "Tail" is
    # observable via the SAME generic MASTER_NORMALIZATION reconciliation
    # category every other non-rig-family fixture already uses -- no
    # Tail-specific runtime branch exists anywhere in the frozen source
    # (grep-confirmed: zero case-insensitive "tail" matches in the entire
    # 13,594-line file), so none is invented here either.
    u'"Tail"\n'
    u"{\n"
    u'\t"selectable"\t\t"1"\n'
    u'\t"control"\t\t"tail_control_a"\n'
    u'\t"control"\t\t"tail_control_b"\n'
    u"}\n"
)


def _read_production_lines():
    with open(PRODUCTION_PATH, "rb") as f:
        data = f.read()
    actual_sha = hashlib.sha256(data).hexdigest()
    if actual_sha != EXPECTED_PRODUCTION_SHA256:
        raise AssertionError("frozen production Normalizer SHA-256 mismatch: %s" % actual_sha)
    return data.decode("ascii").splitlines()


def _extract(lines, a, b):
    return "\n".join(lines[a - 1:b]) + "\n"


def _exec_into(src, ns):
    """Isolated in its own top-level function (never inline inside a
    function with other nested defs) -- Python 2's compiler disallows
    an unqualified `exec` statement inside a function scope that also
    contains a nested function with free variables anywhere in it."""
    exec(compile(src, "<extracted_production_source>", "exec"), ns)


_BASELINE_NS = None


def _baseline_namespace():
    global _BASELINE_NS
    if _BASELINE_NS is not None:
        return _BASELINE_NS
    lines = _read_production_lines()
    src = "\n\n".join(_extract(lines, a, b) for a, b in PROD_RANGES)
    ns = {"re": __import__("re")}
    _exec_into(src, ns)
    assert "parse_targeted_master" in ns
    _BASELINE_NS = (ns, src)
    return _BASELINE_NS


def compute_baseline_master(wanted_folds, master_path):
    ns, src = _baseline_namespace()
    # Hard authority-path assertion (governing prompt Section 8): the
    # extracted baseline source must never reference the qualified
    # candidate authority package.
    forbidden = ("sfm_master_authority", "normalizer_compat_adapter", "candidate_b2c_correction6")
    hits = [f for f in forbidden if f in src]
    if hits:
        raise AssertionError("baseline source contaminated with migrated-path references: %r" % hits)
    return ns["parse_targeted_master"](master_path, set(wanted_folds), validate_conflicts=False)


_MIGRATED_MODS = None


def _migrated_modules():
    global _MIGRATED_MODS
    if _MIGRATED_MODS is not None:
        return _MIGRATED_MODS
    for name in list(sys.modules.keys()):
        if name == "sfm_master_authority_productionized" or name.startswith("sfm_master_authority_productionized."):
            del sys.modules[name]
    for p in (os.path.abspath(CORRECTION6_ROOT), TOOLS_DIR):
        if p not in sys.path:
            sys.path.insert(0, p)
    from sfm_master_authority_productionized import sidecar_contract  # noqa: E402
    from sfm_master_authority_productionized import normalizer_compat_adapter as adapter  # noqa: E402
    sidecar_contract.ensure_loaded()
    src_path = os.path.join(os.path.dirname(os.path.abspath(adapter.__file__)), "normalizer_compat_adapter.py")
    with open(src_path, "rb") as f:
        adapter_src = f.read().decode("utf-8", "replace")
    # Bare mentions of "parse_targeted_master()" (empty parens, as a
    # documentation reference to the function BY NAME -- e.g. "the
    # contract parse_targeted_master() currently provides") are expected
    # and harmless; only a REAL call (non-empty argument list) would be
    # contamination.
    if "parse_targeted_master(" in adapter_src.replace("parse_targeted_master()", ""):
        raise AssertionError("migrated adapter source contaminated with a call to the frozen parser")
    _MIGRATED_MODS = (sidecar_contract, adapter)
    return _MIGRATED_MODS


def compute_migrated_master(wanted_folds, artifact_path, expected_source_sha256):
    sidecar_contract, adapter = _migrated_modules()
    provider = sidecar_contract._provider_module.BoundedProvider.open_path(artifact_path, expected_source_sha256)
    try:
        builder = adapter.build_targeted_master_compatible_projection(set(wanted_folds))
        result, _coverage, _estimate = builder(provider)
        return result
    finally:
        provider.close()


def build_authority_fixture():
    """Compiles MASTER_TXT_BODY once via the REAL production sidecar
    compiler, returns (master_path, artifact_path, master_sha256)."""
    if not os.path.isdir(FIXROOT):
        os.makedirs(FIXROOT)
    if TOOLS_DIR not in sys.path:
        sys.path.insert(0, TOOLS_DIR)
    from sfm_master_sidecar import compiler  # noqa: E402

    data = (u'"groupFile"\n{\n' + MASTER_TXT_BODY + u"}\n").encode("utf-8")
    assert b"\r" not in data
    snapshot = compiler.SourceSnapshot(path="<synthetic:b2c_c_authority>", data=data)
    outcome = compiler.parse_and_compile(snapshot)
    compiler.self_validate_from_bytes(outcome)

    master_path = os.path.join(FIXROOT, "b2c_c_master.txt")
    artifact_path = os.path.join(FIXROOT, "b2c_c.sfmsidecar")
    with open(master_path, "wb") as f:
        f.write(data)
    with open(artifact_path, "wb") as f:
        f.write(outcome.blob)

    master_sha256 = hashlib.sha256(data).hexdigest()
    manifest = {
        "master_relative_path": "b2c_c_master.txt",
        "artifact_relative_path": "b2c_c.sfmsidecar",
        "master_sha256": master_sha256,
        "artifact_sha256": hashlib.sha256(outcome.blob).hexdigest(),
        "occurrence_count": len(outcome.result.occurrences),
    }
    with open(os.path.join(FIXROOT, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    return master_path, artifact_path, master_sha256


def load_authority_fixture():
    """Reads back an already-built fixture's manifest (written by
    `build_authority_fixture`, which requires Python 3 -- the real
    sidecar COMPILER, `sfm_master_core.py`, uses Python-3-only type
    hints). This loader itself has no Python-version constraint and is
    what the Python-2.7 comparison harness calls."""
    with open(os.path.join(FIXROOT, "manifest.json")) as f:
        manifest = json.load(f)
    master_path = os.path.join(FIXROOT, manifest["master_relative_path"])
    artifact_path = os.path.join(FIXROOT, manifest["artifact_relative_path"])
    return master_path, artifact_path, manifest["master_sha256"]


if __name__ == "__main__":
    # Fixture-build entry point -- run this file directly under Python 3
    # (the compiler dependency) to (re)build fixtures_authority/ before
    # running the Python-2.7 comparison harness.
    _master_path, _artifact_path, _master_sha256 = build_authority_fixture()
    print("built: %s / %s / %s" % (_master_path, _artifact_path, _master_sha256[:16]))
