"""Phase B2E Parts 21/22: the real public compiler/writer/reader/publisher
path run against non-official B2A fixtures (Part 21), plus one modest,
hand-authored, combined custom Master exercising every remaining
custom-Gate-1A element in a single source, compared exhaustively across
core / independent B2A oracle / writer / reader / the public compiler
orchestration (Part 22).

No official/custom branch exists anywhere in this file's assertions --
every check below uses the exact same `compiler`/`writer`/`reader`/
`publisher` modules the official Master goes through.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT / "tools"))

import oracle  # noqa: E402
import sfm_master_core as core  # noqa: E402
from sfm_master_sidecar import compiler, publisher, reader  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"
COMBINED_CUSTOM_MASTER = FIXTURES_ROOT / "custom_gate1" / "combined_custom_master.txt"


class CustomMasterPublicCompilerTests(unittest.TestCase):
    """Part 21: run the real public compiler path on a representative set
    of non-official B2A fixtures covering every named element."""

    REPRESENTATIVE_FIXTURES = [
        "04_custom_wrapper_name.txt",       # custom wrapper
        "02_wrapper_owned_control.txt",     # wrapper-owned control
        "03_wrapper_owned_metadata.txt",    # wrapper-owned metadata
        "10_repeated_identical_control_one_group.txt",   # duplicate controls (one group)
        "11_repeated_identical_control_across_groups.txt",  # duplicate controls (across groups)
        "12_same_fold_same_destination.txt",  # same-destination aliases
        "13_same_fold_different_destinations.txt",  # cross-destination FoldConflict
        "19_non_ascii_bmp_text.txt",        # UTF-8/non-ASCII
        "20_non_bmp_text.txt",              # astral-plane UTF-8
        "21_escaped_quote_spelling.txt",    # escape spelling preserved
        "22_escaped_backslash_spelling.txt",
        "15_duplicate_metadata_keys.txt",   # duplicate metadata
        "17_unknown_metadata_key.txt",      # unknown metadata key
    ]

    def test_every_representative_fixture_compiles_check_only(self):
        for name in self.REPRESENTATIVE_FIXTURES:
            with self.subTest(fixture=name):
                result = publisher.check_only(FIXTURES_ROOT / "valid" / name)
                self.assertGreater(len(result.outcome.blob), 0)

    def test_every_representative_fixture_publishes_via_real_publisher(self):
        with tempfile.TemporaryDirectory() as out:
            for name in self.REPRESENTATIVE_FIXTURES:
                with self.subTest(fixture=name):
                    sub_out = Path(out) / name
                    result = publisher.publish(FIXTURES_ROOT / "valid" / name, sub_out)
                    self.assertTrue(result.generation_path.exists())
                    m = publisher.read_active_manifest(sub_out)
                    self.assertEqual(m.generation_basename, result.generation_basename)

    def test_cross_destination_conflict_fixture_resolves_correctly_through_full_stack(self):
        with tempfile.TemporaryDirectory() as out:
            result = publisher.publish(FIXTURES_ROOT / "valid" / "13_same_fold_different_destinations.txt", out)
            m = publisher.read_active_manifest(out)
            gen_path = Path(out) / m.generation_basename
            r = reader.SidecarReader.open_generation(str(gen_path), m.source_sha256)
            try:
                res = r.lookup_fold(b"Bar")
                self.assertIsInstance(res, reader.FoldConflict)
            finally:
                r.close()


class CombinedCustomGateOneATests(unittest.TestCase):
    """Part 22: one modest, hand-auditable custom Master combining custom
    wrapper, nested groups, ordered metadata (including an unknown key),
    duplicate control occurrences, same-destination ASCII aliases,
    cross-destination FoldConflict, non-ASCII UTF-8, and preserved escape
    spelling -- compared exhaustively across core, the independent B2A
    oracle, the writer, the reader, and the public compiler orchestration."""

    @classmethod
    def setUpClass(cls):
        cls.data = COMBINED_CUSTOM_MASTER.read_bytes()
        cls.result = core.parse_master_bytes(cls.data, source_name=str(COMBINED_CUSTOM_MASTER))
        cls.orc = oracle.scan_bytes(cls.data)

    def test_fixture_actually_contains_every_required_element(self):
        # Sanity-check the fixture itself before trusting comparisons built
        # on top of it.
        self.assertTrue(self.result.ok)
        self.assertEqual(self.result.wrapper_paths, ["CustomRoot"])  # custom wrapper, not "groupFile"
        self.assertEqual(len(self.result.groups), 4)  # wrapper + NestedA + NestedB + NestedC
        self.assertEqual(len(self.result.occurrences), 8)

        literals = [o.literal for o in self.result.occurrences]
        self.assertEqual(literals.count("Bar"), 2)  # duplicate control occurrences

        fams = core.build_fold_families(self.result.occurrences)
        self.assertFalse(fams["foo"].is_conflict)  # same-destination alias family (Foo/foo/FOO)
        self.assertEqual(len(fams["foo"].exact_spellings), 3)
        self.assertTrue(fams["bar"].is_conflict)  # cross-destination FoldConflict (Bar vs bar)

        self.assertTrue(any(ord(ch) > 0x2000 for lit in literals for ch in lit))  # non-ASCII present
        self.assertTrue(any("\\" in lit for lit in literals))  # escape spelling present

        meta_pairs = [(g.full_path, e.key) for g in self.result.groups for e in g.metadata.entries]
        self.assertIn(("CustomRoot/NestedA/NestedB", "someCustomKey"), meta_pairs)  # unknown key preserved

    def test_core_vs_oracle_full_parity(self):
        core_by_path = {g.full_path: g for g in self.result.groups}
        orc_by_path = {g.full_path: g for g in self.orc.groups}
        self.assertEqual(set(core_by_path), set(orc_by_path))
        for path, cg in core_by_path.items():
            og = orc_by_path[path]
            self.assertEqual(cg.name, og.name)
            self.assertEqual(cg.declare_order, og.declare_order)
            self.assertEqual(cg.sibling_rank, og.sibling_index)
            self.assertEqual(cg.parent_path, og.parent_path)

        self.assertEqual(len(self.orc.controls), len(self.result.occurrences))
        for co, oc in zip(self.result.occurrences, self.orc.controls):
            self.assertEqual(co.literal, oc.token)
            self.assertEqual(co.full_path, oc.owning_path)
            self.assertEqual(co.local_rank, oc.local_rank)

        self.assertEqual(self.orc.metadata_count(), sum(len(g.metadata.entries) for g in self.result.groups))

    def test_writer_reader_round_trip_matches_core_and_oracle(self):
        from sfm_master_sidecar import writer as writer_module
        blob = writer_module.compile_sidecar(self.data, self.result)
        r = reader.SidecarReader.open_generation(blob, self.result.source_sha256)
        try:
            reader_groups = {g["full_path"]: g for g in r.iter_groups()}
            orc_by_path = {g.full_path: g for g in self.orc.groups}
            for g in self.result.groups:
                rg = reader_groups[g.full_path]
                og = orc_by_path[g.full_path]
                self.assertEqual(rg["name"], g.name)
                self.assertEqual(rg["name"], og.name)
                self.assertEqual(rg["parent_path"], g.parent_path)

            reader_occs = list(r.iter_occurrences())
            for co, oc, ro in zip(self.result.occurrences, self.orc.controls, reader_occs):
                self.assertEqual(co.literal, oc.token)
                self.assertEqual(co.literal, ro["literal"])
                self.assertEqual(co.full_path, ro["full_path"])

            # fold semantics through the reader
            res_foo = r.lookup_fold("Foo".encode("utf-8"))
            self.assertIsInstance(res_foo, reader.Hit)
            res_bar = r.lookup_fold("Bar".encode("utf-8"))
            self.assertIsInstance(res_bar, reader.FoldConflict)
            self.assertEqual(res_bar.destinations, {"CustomRoot/NestedA/NestedB", "CustomRoot/NestedC"})

            # escape spelling preserved end to end
            occs = [o["literal"] for o in reader_occs]
            self.assertIn(self.result.occurrences[-1].literal, occs)
            self.assertIn("\\", self.result.occurrences[-1].literal)
        finally:
            r.close()

    def test_public_compiler_orchestration_reproduces_identical_artifact(self):
        outcome = compiler.parse_and_compile(compiler.capture_source_snapshot(COMBINED_CUSTOM_MASTER))
        from sfm_master_sidecar import writer as writer_module
        direct_blob = writer_module.compile_sidecar(self.data, self.result)
        self.assertEqual(outcome.blob, direct_blob, "public compiler must produce byte-identical output to the direct writer call")
        compiler.self_validate_from_bytes(outcome)  # full semantic parity, via the real reader

    def test_public_compiler_check_only_and_publish_both_succeed(self):
        check_result = publisher.check_only(COMBINED_CUSTOM_MASTER)
        self.assertEqual(len(check_result.outcome.result.groups), 4)

        with tempfile.TemporaryDirectory() as out:
            pub_result = publisher.publish(COMBINED_CUSTOM_MASTER, out)
            m = publisher.read_active_manifest(out)
            self.assertEqual(m.counts["groups"], 4)
            self.assertEqual(m.counts["occurrences"], 8)

            r = reader.SidecarReader.open_generation(str(Path(out) / m.generation_basename), m.source_sha256)
            try:
                res = r.lookup_fold(b"bar")
                self.assertIsInstance(res, reader.FoldConflict)
            finally:
                r.close()


if __name__ == "__main__":
    unittest.main()
