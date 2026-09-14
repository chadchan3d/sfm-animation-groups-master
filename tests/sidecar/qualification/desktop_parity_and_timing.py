# -*- coding: utf-8 -*-
"""GATE B -- desktop Python 3 development-evidence pass (Part 9): semantic
parity FIRST (must pass before any timing claim), then indicative timing.

THIS IS NOT THE SFM RESOURCE VERDICT. Desktop timing here is DEVELOPMENT
EVIDENCE ONLY, comparing S1 (bounded) against the current production eager
`SidecarReader` (Candidate A) on the same machine/process -- it does not
substitute for the real-SFM Qt-main-thread measurement (Part 10/17+) which
this script does not attempt.

Parity strategy (three independent comparisons per workload, not one):
  (1) reference_view  = gate_a2_compat_producer.build_compatibility_view()
                         run against the PRODUCTION eager SidecarReader --
                         this exact function/path is what Gate A2 already
                         qualified against the real Python-2.7 Normalizer
                         oracle. Treated here as the frozen ground truth.
  (2) s1_slow_view    = the SAME generic build_compatibility_view() function,
                         unmodified, run against S1 (BoundedProvider) via its
                         diagnostic-only iter_occurrences(). Isolates: does
                         S1's VALIDATION/DECODE/BACKING logic agree with
                         production reader's, independent of any bounded-path
                         scoping logic?
  (3) s1_fast_view    = bounded_view.build_view_bounded() -- S1's own fast,
                         per-fold-bounded path. Isolates: does the BOUNDED
                         SCOPING algorithm (binary search + per-fold family
                         decode) agree with the slow, full-scan path?

If (1)==(2)==(3) for every workload and every adversarial fixture: S1 is
semantically identical to the already-Gate-A2-qualified contract, and the
bounded-scoping algorithm introduces no discrepancy. If (1)==(2) but
(2)!=(3): the bug is in bounded_view's scoping. If (1)!=(2): the bug is in
BoundedProvider's own validation/decode/backing.
"""

import json
import sys
import time
import os
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
QUAL_DIR = os.path.join(REPO_ROOT, "tests", "sidecar", "qualification")
TEST_DIR = os.path.join(REPO_ROOT, "tests", "sidecar")
ADVERSARIAL_DIR = os.path.join(REPO_ROOT, "tests", "sidecar", "fixtures", "gate_a2_adversarial")

sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))
sys.path.insert(0, TEST_DIR)
sys.path.insert(0, QUAL_DIR)

import official_master_fixture as fx  # noqa: E402
from sfm_master_sidecar import reader as prod_reader  # noqa: E402
import gate_a2_compat_producer as cp  # noqa: E402
import bounded_provider  # noqa: E402
import bounded_view  # noqa: E402


class ProbeError(Exception):
    """Local probe-only exception. This harness never calls the real
    Normalizer's own extracted parsing functions (it treats the production
    `SidecarReader` as frozen ground truth, per the module docstring above),
    so it only ever needs a plain exception type to raise/catch through
    `gate_a2_compat_producer`, not the byte-for-byte Normalizer extraction
    used elsewhere during Gate A2. Kept local and trivial so this harness
    has no dependency on any not-publicly-distributed module."""

_pass = [0]
_fail = [0]
_fail_details = []


def check(label, condition, detail=""):
    if condition:
        _pass[0] += 1
        print("  PASS: %s %s" % (label, detail))
    else:
        _fail[0] += 1
        _fail_details.append((label, detail))
        print("  FAIL: %s %s" % (label, detail))
    return condition


def deep_compare_views(label, a_view, b_view, a_name, b_name):
    check("%s top-level keys" % label, set(a_view.keys()) == set(b_view.keys()))
    check("%s mapping_count" % label, a_view["mapping_count"] == b_view["mapping_count"],
          "%r(%s) vs %r(%s)" % (a_view["mapping_count"], a_name, b_view["mapping_count"], b_name))
    check("%s destination_count" % label, a_view["destination_count"] == b_view["destination_count"],
          "%r(%s) vs %r(%s)" % (a_view["destination_count"], a_name, b_view["destination_count"], b_name))
    check("%s exact_literals" % label, a_view["exact_literals"] == b_view["exact_literals"],
          "sizes %d vs %d" % (len(a_view["exact_literals"]), len(b_view["exact_literals"])))

    a_folded_keys = set(a_view["folded"].keys())
    b_folded_keys = set(b_view["folded"].keys())
    ok = check("%s folded key set" % label, a_folded_keys == b_folded_keys,
               "sizes %d vs %d diff=%r" % (len(a_folded_keys), len(b_folded_keys),
                                           list(a_folded_keys ^ b_folded_keys)[:5]))

    all_rows_match = True
    for fk in sorted(a_folded_keys & b_folded_keys):
        a_rows = a_view["folded"][fk]
        b_rows = b_view["folded"][fk]
        if len(a_rows) != len(b_rows):
            all_rows_match = False
            continue
        for arow, brow in zip(a_rows, b_rows):
            for field in ("literal", "destination", "global_index", "local_index"):
                if arow[field] != brow[field]:
                    all_rows_match = False
    check("%s folded row-by-row exact equality" % label, all_rows_match)

    check("%s group_sibling_order" % label, a_view["group_sibling_order"] == b_view["group_sibling_order"])

    a_meta_keys = set(a_view["group_metadata"].keys())
    b_meta_keys = set(b_view["group_metadata"].keys())
    check("%s group_metadata path set" % label, a_meta_keys == b_meta_keys,
          "diff=%r" % (list(a_meta_keys ^ b_meta_keys)[:5],))
    meta_ok = True
    for k in sorted(a_meta_keys & b_meta_keys):
        am = a_view["group_metadata"][k]
        bm = b_view["group_metadata"][k]
        for field in ("path", "group_color_explicit", "selectable_explicit", "selectable_authority"):
            if am.get(field) != bm.get(field):
                meta_ok = False
    check("%s group_metadata exact values" % label, meta_ok)
    return ok


def build_workload_folds():
    prov0 = prod_reader.SidecarReader.open_generation(
        fx.compiled_artifact_bytes(), fx.core_parse_result().source_sha256,
    )
    all_occs = list(prov0.iter_occurrences())
    wrapper = prov0.wrapper_path()
    prov0.close()

    def folds_under(prefixes):
        s = set()
        for occ in all_occs:
            fp = occ["full_path"]
            for p in prefixes:
                full_prefix = wrapper + u"/" + p
                if fp == full_prefix or fp.startswith(full_prefix + u"/"):
                    s.add(cp.ascii_fold_unicode(occ["literal"]))
                    break
        return s

    single_folds = folds_under([u"Fingers"])
    medium_folds = folds_under([u"Correctives", u"Attachments", u"RigBody", u"RigArms", u"RigLegs", u"RigHelpers"])
    large_folds = folds_under([u"Body Morphs", u"Sexual Bones", u"Arms"])
    disjoint_folds = folds_under([u"Legs", u"Tail"])
    absent_fold = cp.ascii_fold_unicode(u"Gate_B_Genuinely_Absent_Literal_Sentinel_999")
    disjoint_with_absent = set(disjoint_folds)
    disjoint_with_absent.add(absent_fold)

    return [
        ("SINGLE_Fingers", single_folds),
        ("MEDIUM_6RigGroups", medium_folds),
        ("LARGE_BodyMorphsSexualBonesArms", large_folds),
        ("DISJOINT_LegsTailAbsent", disjoint_with_absent),
    ]


def run_official_workloads():
    print("=" * 70)
    print("OFFICIAL-MASTER WORKLOAD PARITY (S1 vs production eager reader)")
    print("=" * 70)
    source_sha = fx.core_parse_result().source_sha256
    artifact_bytes = fx.compiled_artifact_bytes()

    workloads = build_workload_folds()
    timings = {}

    for label, wanted in workloads:
        print("\n-- workload %s (%d folds) --" % (label, len(wanted)))

        t0 = time.perf_counter()
        prod_prov = prod_reader.SidecarReader.open_generation(artifact_bytes, source_sha)
        t1 = time.perf_counter()
        reference_view = cp.build_compatibility_view(prod_prov, wanted, ProbeError)
        t2 = time.perf_counter()
        prod_prov.close()

        t3 = time.perf_counter()
        s1 = bounded_provider.BoundedProvider.open_bytes(artifact_bytes, source_sha)
        t4 = time.perf_counter()

        t5 = time.perf_counter()
        s1_slow_view = cp.build_compatibility_view(s1, wanted, ProbeError)
        t6 = time.perf_counter()

        t7 = time.perf_counter()
        s1_fast_view = bounded_view.build_view_bounded(s1, wanted, ProbeError)
        t8 = time.perf_counter()

        s1.close()

        deep_compare_views(label + " [prod_eager vs S1_slow_reference]", reference_view, s1_slow_view,
                            "prod_eager", "S1_slow_ref")
        deep_compare_views(label + " [S1_slow_reference vs S1_fast_bounded]", s1_slow_view, s1_fast_view,
                            "S1_slow_ref", "S1_fast")

        timings[label] = {
            "n_folds": len(wanted),
            "prod_admission_s": t1 - t0,
            "prod_view_build_s": t2 - t1,
            "s1_admission_s": t4 - t3,
            "s1_slow_view_build_s": t6 - t5,
            "s1_fast_view_build_s": t8 - t7,
        }
        print("  timing: prod_admission=%.4fs prod_view=%.4fs | "
              "s1_admission=%.4fs s1_slow_view=%.4fs s1_fast_view=%.4fs" % (
                  t1 - t0, t2 - t1, t4 - t3, t6 - t5, t8 - t7,
              ))

        o_conflicts = bounded_view.compat_validate_master_subset_conflicts(s1_fast_view, wanted)
        c_conflicts = cp.compat_validate_master_subset_conflicts(reference_view, wanted)
        check("%s validate_master_subset_conflicts parity (fast S1 vs ref)" % label, o_conflicts == c_conflicts)

        sample_literals = list(reference_view["exact_literals"])[:3]
        for lit in sample_literals:
            r_res = cp.compat_master_lookup(reference_view, lit)
            f_res = bounded_view.compat_master_lookup(s1_fast_view, lit)
            check("%s master_lookup(%r) parity" % (label, lit), r_res == f_res, "%r vs %r" % (r_res, f_res))

        r_absent = cp.compat_master_lookup(reference_view, u"Gate_B_Genuinely_Absent_Literal_Sentinel_999")
        f_absent = bounded_view.compat_master_lookup(s1_fast_view, u"Gate_B_Genuinely_Absent_Literal_Sentinel_999")
        check("%s master_lookup(absent) parity" % label, r_absent == f_absent)

    return timings


def run_adversarial_fixtures():
    print("\n" + "=" * 70)
    print("ADVERSARIAL FIXTURE PARITY (S1 vs production eager reader)")
    print("=" * 70)
    manifest_path = os.path.join(ADVERSARIAL_DIR, "manifest.json")
    if not os.path.isfile(manifest_path):
        print("  SKIPPED: adversarial manifest not found at %s" % manifest_path)
        return
    manifest = json.load(open(manifest_path))

    for name, meta in manifest.items():
        bin_path = os.path.join(ADVERSARIAL_DIR, name + ".bin")
        data = open(bin_path, "rb").read()
        source_sha = meta["source_sha256"]

        prod_prov = prod_reader.SidecarReader.open_generation(data, source_sha)
        wrapper = prod_prov.wrapper_path()
        all_occs = list(prod_prov.iter_occurrences())
        wanted = set(cp.ascii_fold_unicode(o["literal"]) for o in all_occs)

        reference_view = None
        reference_exc = None
        try:
            reference_view = cp.build_compatibility_view(prod_prov, wanted, ProbeError)
        except Exception as exc:
            reference_exc = exc
        prod_prov.close()

        s1 = bounded_provider.BoundedProvider.open_bytes(data, source_sha)
        s1_fast_view = None
        s1_exc = None
        try:
            s1_fast_view = bounded_view.build_view_bounded(s1, wanted, ProbeError)
        except Exception as exc:
            s1_exc = exc
        s1.close()

        if reference_exc is not None or s1_exc is not None:
            check("adversarial %s: exception-parity (both raise same class+message, or neither raises)" % name,
                  type(reference_exc) is type(s1_exc) and str(reference_exc) == str(s1_exc),
                  "reference raised %r; S1 raised %r" % (reference_exc, s1_exc))
            continue

        deep_compare_views("adversarial_%s" % name, reference_view, s1_fast_view, "prod_eager", "S1_fast")


def main():
    print("Gate B desktop parity+timing pass. sys.version=%r" % (sys.version,))
    print("official Master source_sha256=%s" % fx.core_parse_result().source_sha256)
    print("official artifact bytes=%d" % len(fx.compiled_artifact_bytes()))

    timings = run_official_workloads()
    run_adversarial_fixtures()

    print("\n" + "=" * 70)
    print("RESULT: %d PASS / %d FAIL" % (_pass[0], _fail[0]))
    print("=" * 70)
    if _fail_details:
        print("FAILURES:")
        for label, detail in _fail_details:
            print("  - %s :: %s" % (label, detail))

    out = {
        "pass": _pass[0],
        "fail": _fail[0],
        "failures": _fail_details,
        "timings": timings,
    }
    out_path = os.path.join(tempfile.gettempdir(), "gate_b_desktop_parity_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print("\nWrote %s" % out_path)

    return 0 if _fail[0] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
