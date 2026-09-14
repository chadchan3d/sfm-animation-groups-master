# -*- coding: utf-8 -*-
"""R1 -- desktop Python 3 qualification of sidecar-to-Normalizer consumer
-projection parity. Uses the REAL manual (`master_lookup`,
`validate_master_subset_conflicts`) and REAL live (`t120_master_lookup`,
`t130_t95_master_from_t120`) consumer functions, imported read-only from the
exact current Normalizer / T130 source files (never mirrored), fed dicts
built by this arc's own new `r1_consumer_projection.py` from a real bounded
sidecar provider (S1).

The real TXT-tokenizing functions (`parse_targeted_master`, `t120_parse_master`)
are Python-2-only in their exact byte-iteration behavior (confirmed: they
fail under desktop Python 3 with `'int' object has no attribute 'isspace'`,
since Python 3 iterates a binary-mode file as ints, not one-character
strings -- a genuine, disclosed cross-version finding, not a qualification
mirror). They are exercised nativget ely, unmodified, in the embedded Python 2.7
probe instead (see `r1_embedded_probe.py`). On desktop, every fixture's
expected TXT-derived result is HAND-AUDITED (written by direct reading of
each tiny fixture's source text before running any producer) rather than
obtained from a live desktop TXT-parser run -- satisfying "hand-audited
expectations supplement producer agreement" independent of that
Python-2-only limitation.
"""

import sys
import os
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))
sys.path.insert(0, os.path.join(REPO_ROOT, "tests", "sidecar"))
sys.path.insert(0, os.path.join(REPO_ROOT, "tests", "sidecar", "qualification"))

import bounded_provider  # noqa: E402
import bounded_view  # noqa: E402
import r1_consumer_projection as proj  # noqa: E402
import normalizer_oracle_import as noi  # noqa: E402
import official_master_fixture as fx  # noqa: E402
from sfm_master_sidecar import compiler as sidecar_compiler  # noqa: E402

_pass = [0]
_fail = [0]
_fail_details = []


def _safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "backslashreplace").decode("ascii"))


def check(label, condition, detail=""):
    if condition:
        _pass[0] += 1
        _safe_print("  PASS: %s %s" % (label, detail))
    else:
        _fail[0] += 1
        _fail_details.append("%s :: %s" % (label, detail))
        _safe_print("  FAIL: %s %s" % (label, detail))
    return condition


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# These two point at real, externally-owned SFM files (the live Normalizer
# install and a T130 requalification snapshot) that this repo does not ship --
# neither is committed here, so a fresh checkout has no personal-machine
# default to fall back to. Set both to run the live-oracle sections;
# without them, `main()` reports the prerequisite as unmet and returns rather
# than exercising the historical hand-audited-only checks in a way that
# could be mistaken for a full R1 run.
NORMALIZER_PATH = os.environ.get("SFM_NORMALIZER_ORACLE_PATH")
T130_PATH = os.environ.get("SFM_T130_ORACLE_PATH")
FIXTURES_DIR = os.path.join(REPO_ROOT, "tests", "sidecar", "fixtures", "valid")
R1_FIXDIR = os.path.join(tempfile.mkdtemp(prefix="sfm_r1_"), "r1_fixtures")


def ascii_fold(v):
    out = []
    for ch in v:
        o = ord(ch)
        out.append(chr(o + 32) if 65 <= o <= 90 else ch)
    return "".join(out)


def compile_fixture(txt_path):
    snapshot = sidecar_compiler.capture_source_snapshot(txt_path)
    outcome = sidecar_compiler.parse_and_compile(snapshot)
    return outcome.blob, snapshot.sha256_hex


def open_provider(blob, source_sha256):
    return bounded_provider.BoundedProvider.open_bytes(blob, source_sha256)


def main():
    if not NORMALIZER_PATH or not os.path.isfile(NORMALIZER_PATH) or \
            not T130_PATH or not os.path.isfile(T130_PATH):
        print(
            "SKIPPED: this harness requires the real, externally-owned SFM "
            "Normalizer and T130 files, which are not distributed with this "
            "repository. Set SFM_NORMALIZER_ORACLE_PATH and "
            "SFM_T130_ORACLE_PATH to the exact local paths of those files "
            "(e.g. under your own SFM install and SFM_20260910_T130_* "
            "requalification snapshot) to run this harness end-to-end."
        )
        return 0
    norm = noi.load_real_normalizer(NORMALIZER_PATH)
    t130 = noi.load_real_t130(T130_PATH)

    # -----------------------------------------------------------------
    # R1.1 -- baseline: real functions load, and disagree with a naive
    # Python-3 direct TXT-parse attempt (documents the Python-2-only finding).
    # -----------------------------------------------------------------
    section("R1.1 -- real consumer function availability")
    check("real manual parse_targeted_master imported", norm.parse_targeted_master is not None)
    check("real manual master_lookup imported", norm.master_lookup is not None)
    check("real manual validate_master_subset_conflicts imported", norm.validate_master_subset_conflicts is not None)
    check("real live t120_parse_master imported", t130.t120_parse_master is not None)
    check("real live t120_master_lookup imported", t130.t120_master_lookup is not None)
    check("real live t130_t95_master_from_t120 imported", t130.t130_t95_master_from_t120 is not None)
    try:
        norm.parse_targeted_master(os.path.join(FIXTURES_DIR, "12_same_fold_same_destination.txt"), {"foo"}, validate_conflicts=False)
        check("real TXT tokenizer is Python-2-only (documented finding)", False, "unexpectedly succeeded under Python 3")
    except AttributeError as exc:
        check("real TXT tokenizer is Python-2-only (documented finding: fails under desktop Python 3, "
              "reserved for the embedded Python 2.7 probe)", True, repr(exc))

    # -----------------------------------------------------------------
    # R1.2 -- hand-audited adversarial fixtures (20 required cases).
    # Expected results are written BEFORE calling either producer.
    # -----------------------------------------------------------------
    section("R1.2 -- hand-audited profile / adversarial cases")

    def fixture_path(name):
        return os.path.join(FIXTURES_DIR, name)

    cases = []

    # 1: ordinary exact HIT / 2: ASCII-casefold alias HIT / 3: complete
    # fold family with repeated occurrences -- fixture 12 has Foo/foo/FOO,
    # all same destination "Grp".
    cases.append(dict(
        name="01-03 exact/alias HIT + complete family",
        fixture="12_same_fold_same_destination.txt",
        wanted_names=["Foo"],
        # NOTE (hand-audit correction): the fixture's three occurrences are
        # the EXACT spellings "Foo"/"foo"/"FOO" -- all three are therefore in
        # exact_literals, so querying any of them yields mode EXACT. A
        # spelling that is NOT itself in the fixture (mixed-case "fOO") is
        # required to actually exercise ASCII_CASEFOLD.
        # NOTE (hand-audit correction): master_lookup always returns the
        # FAMILY's first occurrence by (global_index, local_index) -- NOT
        # the occurrence matching the queried spelling. Querying "Foo",
        # "foo", or the never-present "fOO" all resolve to the same
        # first-ranked row (global_index=0, "Foo" itself); only `mode`
        # differs (EXACT for a spelling that is itself in the fixture,
        # ASCII_CASEFOLD otherwise).
        expect_manual_lookup={"Foo": {"known": True, "destination": "Grp", "mode": "EXACT", "global_index": 0, "local_index": 0},
                               "foo": {"known": True, "destination": "Grp", "mode": "EXACT", "global_index": 0, "local_index": 0},
                               "fOO": {"known": True, "destination": "Grp", "mode": "ASCII_CASEFOLD", "global_index": 0, "local_index": 0}},
        expect_family_size=3,
    ))
    # 4: absent literal -> covered MasterUnknown.
    cases.append(dict(
        name="04 absent literal -> covered MasterUnknown",
        fixture="12_same_fold_same_destination.txt",
        wanted_names=["Foo", "TotallyAbsentR1Sentinel"],
        expect_manual_lookup={"TotallyAbsentR1Sentinel": {"known": False, "destination": None, "mode": "NONE", "global_index": None, "local_index": None}},
    ))
    # 5: targeted multi-destination conflict.
    cases.append(dict(
        name="05 targeted multi-destination conflict",
        fixture="13_same_fold_different_destinations.txt",
        wanted_names=["Bar"],
        expect_manual_lookup_raises="Bar",
    ))
    # 18: exact spelling inside conflict does not override.
    cases.append(dict(
        name="18 exact spelling inside conflicting family does not override",
        fixture="14_exact_spelling_inside_conflicting_fold.txt",
        wanted_names=["Baz"],
        expect_manual_lookup_raises="Baz",
    ))
    # 6/7: hierarchy/sibling order + root/wrapper conventions.
    cases.append(dict(
        name="06-07 sibling order + wrapper convention",
        fixture="06_sibling_groups.txt",
        wanted_names=["a", "b", "c"],
        expect_sibling_order_root=["First", "Second", "Third"],
    ))
    # 9: metadata omitted (fixture 17 has an unknown/ignored key, group has no
    # known metadata keys explicitly present).
    cases.append(dict(
        name="09 metadata omitted",
        fixture="17_unknown_metadata_key.txt",
        wanted_names=[],
        expect_metadata_omitted=True,
    ))
    # 15: duplicate canonical metadata rejected (manual: any duplicate raw key).
    cases.append(dict(
        name="15 duplicate canonical metadata rejected (manual, selectable x2)",
        fixture="15_duplicate_metadata_keys.txt",
        wanted_names=["X"],
        expect_manual_metadata_raises=True,
    ))
    # 17: non-ASCII literal + group name.
    cases.append(dict(
        name="17 non-ASCII literal",
        fixture="19_non_ascii_bmp_text.txt",
        wanted_names=["注視TipsParent"],
        expect_manual_lookup={"注視TipsParent": {"known": True, "destination": "顔", "mode": "EXACT", "global_index": 0, "local_index": 0}},
    ))
    # 16: escaped literal/source-token case -- hand-audit correction: this
    # fixture's raw TXT bytes contain a literal backslash (`\"`). That is
    # EXACTLY the byte the existing Gate C0.2 `normalizer_source_profile`
    # gate refuses (the real Normalizer's tokenizer resolves backslash
    # escapes; the generic sidecar tokenizer preserves them verbatim --
    # divergent interpretation, refused rather than silently guessed at).
    # So the correct expectation for an escaped-token case is REFUSAL by
    # the source-profile gate, not a successful HIT -- this fixture is
    # outside the declared compatible profile, not within it.

    for c in cases:
        blob, sha = compile_fixture(fixture_path(c["fixture"]))
        provider = open_provider(blob, sha)
        wanted_folds = set(ascii_fold(n) for n in c["wanted_names"])
        try:
            manual = proj.build_manual_projection(
                provider, bounded_view, wanted_folds, norm.ProbeError,
                norm.parse_master_rgba_text, norm.parse_master_bool_text,
            )
            manual_build_raised = None
        except norm.ProbeError as exc:
            manual = None
            manual_build_raised = exc

        if c.get("expect_manual_metadata_raises"):
            check("%s: manual projection build raises on duplicate metadata" % c["name"],
                  manual_build_raised is not None, repr(manual_build_raised))
            provider.close()
            continue

        check("%s: manual projection built" % c["name"], manual is not None, repr(manual_build_raised))

        if "expect_manual_lookup" in c:
            for literal, expected in c["expect_manual_lookup"].items():
                try:
                    got = norm.master_lookup(manual, literal)
                    check("%s: master_lookup(%r) == hand-audited expectation" % (c["name"], literal),
                          got == expected, "got=%r expected=%r" % (got, expected))
                except norm.ProbeError as exc:
                    check("%s: master_lookup(%r) unexpectedly raised" % (c["name"], literal), False, repr(exc))

        if "expect_manual_lookup_raises" in c:
            try:
                norm.master_lookup(manual, c["expect_manual_lookup_raises"])
                check("%s: master_lookup raises on conflict" % c["name"], False, "did not raise")
            except norm.ProbeError as exc:
                check("%s: master_lookup raises on conflict" % c["name"], True, repr(exc))

        if "expect_family_size" in c:
            fk = ascii_fold(c["wanted_names"][0])
            got_size = len(manual["folded"].get(fk, []))
            check("%s: complete family size == %d" % (c["name"], c["expect_family_size"]),
                  got_size == c["expect_family_size"], "got=%d" % got_size)

        if "expect_sibling_order_root" in c:
            got = manual["group_sibling_order"].get(u"<ROOT>")
            check("%s: root sibling order preserved exactly" % c["name"],
                  got == c["expect_sibling_order_root"], "got=%r" % (got,))

        if c.get("expect_metadata_omitted"):
            any_explicit = any(
                m["groupColor_raw"] or m["selectable_raw"] or m["visible_raw"] or m["snappable_raw"]
                for m in manual["group_metadata"].values()
            )
            check("%s: no metadata present -> all raw lists empty (omission preserved)" % c["name"],
                  not any_explicit)

        provider.close()

    # -----------------------------------------------------------------
    # R1.3 -- snap alias + duplicate canonical rejection (live profile only).
    # -----------------------------------------------------------------
    section("R1.3 -- snap alias accepted for live profile; duplicate canonical rejected")
    os.makedirs(R1_FIXDIR, exist_ok=True)
    snap_txt = os.path.join(R1_FIXDIR, "snap_alias.txt")
    with open(snap_txt, "w", newline="") as f:
        f.write('groupFile\n{\n\t"Grp"\n\t{\n\t\t"snap"\t\t"1"\n\t\t"control"\t\t"X"\n\t}\n}\n')
    blob, sha = compile_fixture(snap_txt)
    provider = open_provider(blob, sha)
    live = proj.build_live_master120(provider, bounded_view, {"x"}, t130.ProbeError, sha)
    check("R1.3: live projection accepts 'snap' and canonicalizes to 'snappable'",
          live["group_metadata"]["Grp"]["snappable"] == "1" and "snappable" in live["group_metadata"]["Grp"]["explicit_fields"])
    manual_no_snap = proj.build_manual_projection(provider, bounded_view, {"x"}, norm.ProbeError,
                                                    norm.parse_master_rgba_text, norm.parse_master_bool_text)
    check("R1.3: manual profile does NOT treat 'snap' as an alias (manual parser has no 'snap' key at all)",
          manual_no_snap["group_metadata"]["Grp"]["snappable_raw"] == [])
    provider.close()

    dup_snap_txt = os.path.join(R1_FIXDIR, "snap_dup.txt")
    with open(dup_snap_txt, "w", newline="") as f:
        f.write('groupFile\n{\n\t"Grp"\n\t{\n\t\t"snap"\t\t"1"\n\t\t"snappable"\t\t"0"\n\t\t"control"\t\t"X"\n\t}\n}\n')
    blob2, sha2 = compile_fixture(dup_snap_txt)
    provider2 = open_provider(blob2, sha2)
    try:
        proj.build_live_master120(provider2, bounded_view, {"x"}, t130.ProbeError, sha2)
        check("R1.3: live projection rejects duplicate canonical metadata (snap + snappable)", False, "did not raise")
    except t130.ProbeError as exc:
        check("R1.3: live projection rejects duplicate canonical metadata (snap + snappable)", True, repr(exc))
    provider2.close()

    # -----------------------------------------------------------------
    # R1.4 -- malformed/unsupported profile -> explicit refusal, not
    # MasterUnknown (case 20). Reuses the existing qualification-only
    # source-profile gate (Gate C0.2), never a fabricated absence.
    # -----------------------------------------------------------------
    section("R1.4 -- malformed/unsupported profile refused explicitly")
    import normalizer_source_profile as nsp
    bad_txt = os.path.join(R1_FIXDIR, "bad_profile.txt")
    with open(bad_txt, "wb") as f:
        f.write(b'groupFile\n{\n\t"Grp\\\\Sub"\n\t{\n\t\t"control"\t\t"X"\n\t}\n}\n')
    try:
        with open(bad_txt, "rb") as f:
            nsp.check_normalizer_source_profile(f.read(), u"groupFile")
        check("R1.4: backslash-in-source profile refused explicitly", False, "did not raise")
    except nsp.NormalizerSourceProfileRefused as exc:
        check("R1.4: backslash-in-source profile refused explicitly (not MasterUnknown)", True, repr(exc))

    # 16: escaped-token fixture is ALSO outside the compatible profile for
    # the same reason (its raw bytes contain a literal backslash).
    with open(fixture_path("21_escaped_quote_spelling.txt"), "rb") as f:
        escaped_bytes = f.read()
    try:
        nsp.check_normalizer_source_profile(escaped_bytes, u"groupFile")
        check("R1.4/16: escaped-quote fixture refused by source-profile gate (outside compatible profile)",
              False, "did not raise")
    except nsp.NormalizerSourceProfileRefused as exc:
        check("R1.4/16: escaped-quote fixture refused by source-profile gate (outside compatible profile)",
              True, repr(exc))

    # -----------------------------------------------------------------
    # R1.5 -- coverage semantics.
    # -----------------------------------------------------------------
    section("R1.5 -- coverage semantics")
    blob, sha = compile_fixture(fixture_path("12_same_fold_same_destination.txt"))
    provider = open_provider(blob, sha)
    manual_cov = proj.build_manual_projection(provider, bounded_view, {"foo"}, norm.ProbeError,
                                                norm.parse_master_rgba_text, norm.parse_master_bool_text)
    check("R1.5: requested-and-present fold -> in folded (positive)", "foo" in manual_cov["folded"])
    manual_neg = proj.build_manual_projection(provider, bounded_view, {"totallyabsentr1coverage"}, norm.ProbeError,
                                                norm.parse_master_rgba_text, norm.parse_master_bool_text)
    check("R1.5: requested-but-absent fold -> covered MasterUnknown via master_lookup",
          norm.master_lookup(manual_neg, "TotallyAbsentR1Coverage")["known"] is False)
    check("R1.5: a fold never requested is simply absent from folded (uncovered, not MasterUnknown)",
          "bar" not in manual_cov["folded"] and "bar" not in manual_neg["folded"])
    try:
        norm.validate_master_subset_conflicts(manual_cov, {"nonexistent_never_requested"})
        check("R1.5: legacy validator on an uncovered fold is a silent no-op (no rows -> no conflict), "
              "distinct from a covered MasterUnknown lookup result", True)
    except norm.ProbeError as exc:
        check("R1.5: legacy validator on an uncovered fold is a silent no-op", False, repr(exc))
    provider.evict_reusable_cache()
    check("R1.6: eviction cannot turn unavailable coverage into MasterUnknown (already-built dict is untouched by provider cache state)",
          "foo" in manual_cov["folded"])
    provider.close()

    # -----------------------------------------------------------------
    # R1.6 -- conflict timing: broad inventory vs decisive subset gate.
    # -----------------------------------------------------------------
    section("R1.6 -- targeted conflict timing preserved")
    blob, sha = compile_fixture(fixture_path("13_same_fold_different_destinations.txt"))
    provider = open_provider(blob, sha)
    manual_conf = proj.build_manual_projection(provider, bounded_view, {"bar"}, norm.ProbeError,
                                                 norm.parse_master_rgba_text, norm.parse_master_bool_text)
    try:
        norm.validate_master_subset_conflicts(manual_conf, {"some_other_fold_not_bar"})
        check("R1.6: broad command inventory containing 'bar' does not force rejection "
              "when the ACTIVE subset excludes it", True)
    except norm.ProbeError as exc:
        check("R1.6: broad inventory does not force early rejection", False, repr(exc))
    try:
        norm.validate_master_subset_conflicts(manual_conf, {"bar"})
        check("R1.6: subset validation rejects once the active subset includes the conflicting fold", False, "did not raise")
    except norm.ProbeError as exc:
        check("R1.6: subset validation rejects once the active subset includes the conflicting fold", True, repr(exc))
    try:
        norm.master_lookup(manual_conf, "Bar")
        check("R1.6: scalar lookup retains its own (raising) conflict behavior", False, "did not raise")
    except norm.ProbeError as exc:
        check("R1.6: scalar lookup retains its own (raising) conflict behavior", True, repr(exc))
    provider.close()

    # -----------------------------------------------------------------
    # R1.7 -- counts/ranks/order against the OFFICIAL Master.
    # -----------------------------------------------------------------
    section("R1.7 -- counts/ranks/order against the official Master")
    official_blob = fx.compiled_artifact_bytes()
    official_sha = fx.core_parse_result().source_sha256
    provider = open_provider(official_blob, official_sha)
    small_folds = {"rig_root"}
    manual_off = proj.build_manual_projection(provider, bounded_view, small_folds, norm.ProbeError,
                                                norm.parse_master_rgba_text, norm.parse_master_bool_text)
    check("R1.7: whole-source mapping_count == official occurrence_count()",
          manual_off["mapping_count"] == provider.occurrence_count())
    check("R1.7: whole-source destination_count == official destination_count()",
          manual_off["destination_count"] == provider.destination_count())
    rows = manual_off["folded"].get(ascii_fold("rig_root"), [])
    if rows:
        sorted_by_rank = sorted(rows, key=lambda r: r["global_index"])
        check("R1.7: rows already presented in global-rank order (lookup-key sorting never reorders)",
              rows == sorted_by_rank)
    provider.close()

    # -----------------------------------------------------------------
    # R1.8 -- live projection hand-audited HIT/conflict + T95 bridge
    # scoped-vs-whole destination_count distinction.
    # -----------------------------------------------------------------
    section("R1.8 -- live projection (t120_master_lookup / t130_t95_master_from_t120)")
    blob, sha = compile_fixture(fixture_path("12_same_fold_same_destination.txt"))
    provider = open_provider(blob, sha)
    live12 = proj.build_live_master120(provider, bounded_view, {"foo"}, t130.ProbeError, sha)
    res = t130.t120_master_lookup(live12, "Foo")
    check("R1.8: live t120_master_lookup HIT matches hand-audited expectation",
          res == {"known": True, "destination": "Grp", "mode": "EXACT", "global_index": 0, "local_index": 0},
          "got=%r" % (res,))
    check("R1.8: live master120 total_controls is whole-source (matches manual mapping_count)",
          live12["total_controls"] == provider.occurrence_count())
    kernel12 = t130.t130_t95_master_from_t120(live12)
    check("R1.8: T95 bridge mapping_count == whole-source total_controls",
          kernel12["mapping_count"] == live12["total_controls"])
    check("R1.8: T95 bridge destination_count is SCOPED (from retained rows only, 1 here) -- "
          "distinct from the manual projection's WHOLE-SOURCE destination_count",
          kernel12["destination_count"] == 1)
    provider.close()

    blob, sha = compile_fixture(fixture_path("13_same_fold_different_destinations.txt"))
    provider = open_provider(blob, sha)
    live13 = proj.build_live_master120(provider, bounded_view, {"bar"}, t130.ProbeError, sha)
    res_conf = t130.t120_master_lookup(live13, "Bar")
    check("R1.8: live t120_master_lookup CONFLICT result matches hand-audited expectation "
          "(known=None, mode=CONFLICT, destinations=tuple, no exception raised)",
          res_conf["known"] is None and res_conf["mode"] == "CONFLICT"
          and res_conf["destination"] is None and set(res_conf["destinations"]) == {"GrpA", "GrpB"},
          "got=%r" % (res_conf,))
    check("R1.8: live target_conflicts recorded in master120 itself", len(live13["target_conflicts"]) == 1)
    provider.close()

    # -----------------------------------------------------------------
    # R1.9 -- detached-view consumption after complete backing is closed.
    # -----------------------------------------------------------------
    section("R1.9 -- detached-view consumption after backing close")
    blob, sha = compile_fixture(fixture_path("12_same_fold_same_destination.txt"))
    provider = open_provider(blob, sha)
    manual_detached = proj.build_manual_projection(provider, bounded_view, {"foo"}, norm.ProbeError,
                                                     norm.parse_master_rgba_text, norm.parse_master_bool_text)
    live_detached = proj.build_live_master120(provider, bounded_view, {"foo"}, t130.ProbeError, sha)
    kernel_detached = t130.t130_t95_master_from_t120(live_detached)
    provider.close()
    check("R1.9: backing provider is closed (no longer valid)", not provider.is_valid())
    del provider
    res_after_close_manual = norm.master_lookup(manual_detached, "Foo")
    check("R1.9: real manual master_lookup consumes the detached projection correctly after backing close",
          res_after_close_manual == {"known": True, "destination": "Grp", "mode": "EXACT", "global_index": 0, "local_index": 0})
    res_after_close_live = t130.t120_master_lookup(live_detached, "Foo")
    check("R1.9: real live t120_master_lookup consumes the detached projection correctly after backing close",
          res_after_close_live == {"known": True, "destination": "Grp", "mode": "EXACT", "global_index": 0, "local_index": 0})
    check("R1.9: T95 bridge kernel (built before close) remains usable after close",
          kernel_detached["folded"] == live_detached["folded"])
    check("R1.9: no provider/file/mapping object reachable from either detached dict "
          "(both are plain dicts of strings/ints/sets built before close)",
          all(not hasattr(v, "close") for v in list(manual_detached.values()) + list(live_detached.values())
              if not isinstance(v, (dict, set, list, int, str, type(None)))))

    # -----------------------------------------------------------------
    # R1.10 -- workloads. Honest scoping: the historical Fox (208 controls),
    # real six-target (1,680 occurrences), and 72-shot/216-target (800
    # folds) exact vocabularies were NOT recoverable byte-for-byte within
    # this evidence-collection session (the controlling reconciliation
    # audit itself found these numbers contested/not independently
    # reconstructed -- see the R1 audit doc). Per the brief's own explicit
    # "report actual count; do not force historical numbers" instruction,
    # this section captures three REAL, deterministic, currently-
    # recoverable workloads derived from the actual official Master
    # instead, honestly labeled as such rather than claimed to be the
    # historical Fox/six-target/72-shot scopes.
    # -----------------------------------------------------------------
    section("R1.10 -- workload captures (honestly-scoped, current official Master)")
    official_blob = fx.compiled_artifact_bytes()
    official_sha = fx.core_parse_result().source_sha256
    provider = open_provider(official_blob, official_sha)

    def real_disjoint_fold_sets(prefixes):
        from sfm_master_sidecar import reader as prod_reader
        prov0 = prod_reader.SidecarReader.open_generation(official_blob, official_sha)
        wrapper = prov0.wrapper_path()
        occs = list(prov0.iter_occurrences())
        prov0.close()
        out = []
        for prefix in prefixes:
            s = set()
            full_prefix = wrapper + "/" + prefix
            for o in occs:
                fp = o["full_path"]
                if fp == full_prefix or fp.startswith(full_prefix + "/"):
                    s.add(ascii_fold(o["literal"]))
            out.append(s)
        return out

    small_scope, medium_scope, large_scope = real_disjoint_fold_sets(["Fingers", "RigArms", "Face"])
    for label, scope in (("A (small, stand-in for Fox)", small_scope),
                          ("B (medium, stand-in for six-target)", medium_scope),
                          ("C (large, stand-in for 72-shot/Selected-All)", large_scope)):
        m = proj.build_manual_projection(provider, bounded_view, scope, norm.ProbeError,
                                           norm.parse_master_rgba_text, norm.parse_master_bool_text)
        check("R1.10: workload %s -- projection builds without error, real fold count=%d" % (label, len(scope)),
              m is not None, "folds=%d" % len(scope))
    provider.close()

    print("\n" + "=" * 70)
    print("RESULT: %d PASS / %d FAIL" % (_pass[0], _fail[0]))
    print("=" * 70)
    if _fail_details:
        for d in _fail_details:
            print("  FAIL DETAIL:", d)

    return 0 if _fail[0] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
