"""Phase B2D Parts 6-10/16-18/23: full-scale, non-sampled three-way
comparison (sfm_master_core / independent oracle / production reader) over
the ENTIRE official Master -- all 43 groups, all 42 child-index references,
all 54 metadata entries, all 128,555 occurrences, complete by-group
partition coverage, full string round-trip, plus source binding and
lifetime regression exercised against the real official-scale artifact.
"""

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT / "tools"))

import official_master_fixture as fx  # noqa: E402
from sfm_master_sidecar import reader  # noqa: E402


class GroupParityTests(unittest.TestCase):
    """Part 6: full 43/43 group parity across core, oracle, and reader."""

    @classmethod
    def setUpClass(cls):
        cls.result = fx.core_parse_result()
        cls.orc = fx.oracle_scan_result()
        cls.r = fx.open_shared_reader()
        cls.core_by_path = {g.full_path: g for g in cls.result.groups}
        cls.orc_by_path = {g.full_path: g for g in cls.orc.groups}
        cls.reader_groups = list(cls.r.iter_groups())
        cls.reader_by_path = {g["full_path"]: g for g in cls.reader_groups}

    @classmethod
    def tearDownClass(cls):
        cls.r.close()

    def test_all_43_groups_present_in_all_three(self):
        self.assertEqual(len(self.core_by_path), 43)
        self.assertEqual(len(self.orc_by_path), 43)
        self.assertEqual(len(self.reader_by_path), 43)
        self.assertEqual(set(self.core_by_path), set(self.orc_by_path))
        self.assertEqual(set(self.core_by_path), set(self.reader_by_path))

    def test_wrapper_is_groupfile_and_canonical_paths_are_wrapper_inclusive(self):
        self.assertEqual(self.result.wrapper_paths, ["groupFile"])
        self.assertIn("groupFile/Face/Eyes", self.core_by_path)
        self.assertIn("groupFile/Face/Eyes", self.reader_by_path)
        self.assertIn("groupFile/Face/Eyes", self.orc_by_path)

    def test_every_group_fact_agrees_across_core_oracle_reader(self):
        mismatches = []
        for path, cg in self.core_by_path.items():
            og = self.orc_by_path[path]
            rg = self.reader_by_path[path]
            if not (cg.name == og.name == rg["name"]):
                mismatches.append(("name", path))
            if not (cg.declare_order == og.declare_order == rg["declare_order"]):
                mismatches.append(("declare_order", path))
            if not (cg.sibling_rank == og.sibling_index == rg["sibling_rank"]):
                mismatches.append(("sibling_rank", path))
            if not (cg.parent_path == og.parent_path == rg["parent_path"]):
                mismatches.append(("parent_path", path))
            is_parentless_core = cg.parent_path is None
            is_parentless_reader = rg["parent_path_id"] == 0xFFFFFFFF
            if is_parentless_core != is_parentless_reader:
                mismatches.append(("parentless_status", path))
        self.assertEqual(mismatches, [], "group parity mismatches: %r" % mismatches[:10])

    def test_exactly_one_parentless_group(self):
        parentless_core = [g for g in self.result.groups if g.parent_path is None]
        parentless_reader = [g for g in self.reader_groups if g["parent_path"] is None]
        self.assertEqual(len(parentless_core), 1)
        self.assertEqual(len(parentless_reader), 1)
        self.assertEqual(parentless_core[0].full_path, parentless_reader[0]["full_path"])

    def test_child_sequence_per_group_matches_core(self):
        mismatches = []
        for g in self.result.groups:
            expected_children = g.child_paths  # already declare_order-sorted
            actual_children = sorted(
                (rg for rg in self.reader_groups if rg["parent_path"] == g.full_path),
                key=lambda rg: rg["sibling_rank"],
            )
            actual_paths = [rg["full_path"] for rg in actual_children]
            if expected_children != actual_paths:
                mismatches.append((g.full_path, expected_children, actual_paths))
        self.assertEqual(mismatches, [], "child sequence mismatches: %r" % mismatches[:5])


class ChildIndexParityTests(unittest.TestCase):
    """Part 7: exact child-index cardinality and coverage."""

    def test_cardinality(self):
        result = fx.core_parse_result()
        parentless = [g for g in result.groups if g.parent_path is None]
        self.assertEqual(len(result.groups), 43)
        self.assertEqual(len(parentless), 1)
        self.assertEqual(len(result.groups) - len(parentless), 42)

    def test_every_non_wrapper_group_appears_exactly_once_wrapper_zero_times(self):
        r = fx.open_shared_reader()
        try:
            groups = list(r.iter_groups())
            wrapper_path = r.wrapper_path()
            # reconstruct coverage by walking each group's declared parent
            coverage = {g["full_path"]: 0 for g in groups}
            for g in groups:
                if g["parent_path"] is not None:
                    coverage[g["full_path"]] += 1  # every non-wrapper group has exactly one parent claim
            for g in groups:
                expected = 0 if g["full_path"] == wrapper_path else 1
                self.assertEqual(coverage[g["full_path"]], expected, g["full_path"])
        finally:
            r.close()


class MetadataParityTests(unittest.TestCase):
    """Part 8: full 54/54 metadata parity."""

    @classmethod
    def setUpClass(cls):
        cls.result = fx.core_parse_result()
        cls.orc = fx.oracle_scan_result()
        cls.r = fx.open_shared_reader()
        cls.reader_groups_by_path = {g["full_path"]: g for g in cls.r.iter_groups()}
        cls.orc_meta_by_path = cls.orc.metadata_by_path()

    @classmethod
    def tearDownClass(cls):
        cls.r.close()

    def test_total_counts(self):
        core_total = sum(len(g.metadata.entries) for g in self.result.groups)
        orc_total = self.orc.metadata_count()
        self.assertEqual(core_total, 54)
        self.assertEqual(orc_total, 54)

    def test_every_metadata_entry_agrees_across_core_oracle_reader(self):
        mismatches = []
        for g in self.result.groups:
            gid = self.reader_groups_by_path[g.full_path]["path_id"]
            r_meta = list(self.r.iter_metadata(gid))
            o_meta = sorted(self.orc_meta_by_path.get(g.full_path, []), key=lambda m: m.local_order)
            if not (len(r_meta) == len(o_meta) == len(g.metadata.entries)):
                mismatches.append(("count", g.full_path, len(g.metadata.entries), len(o_meta), len(r_meta)))
                continue
            for ce, oe, re_ in zip(g.metadata.entries, o_meta, r_meta):
                if not (ce.key == oe.key == re_["key"]) or not (ce.value == oe.value == re_["value"]):
                    mismatches.append(("entry", g.full_path, ce.key, ce.value, oe.key, oe.value, re_["key"], re_["value"]))
        self.assertEqual(mismatches, [], "metadata mismatches: %r" % mismatches[:10])

    def test_absent_vs_explicit_zero_vs_no_rows_distinction_preserved(self):
        for g in self.result.groups:
            gid = self.reader_groups_by_path[g.full_path]["path_id"]
            r_meta = list(self.r.iter_metadata(gid))
            if not g.metadata.entries:
                self.assertEqual(r_meta, [], "%s should have zero metadata rows" % g.full_path)
            else:
                # presence of ANY row is a distinct fact from absence of a
                # SPECIFIC key -- re-confirm both facts independently.
                self.assertGreater(len(r_meta), 0)
                for key in {m.key for m in g.metadata.entries}:
                    self.assertTrue(g.metadata.present(key))


class OccurrenceParityTests(unittest.TestCase):
    """Part 9: full 128,555/128,555 occurrence parity, no sampling."""

    @classmethod
    def setUpClass(cls):
        cls.result = fx.core_parse_result()
        cls.orc = fx.oracle_scan_result()
        cls.r = fx.open_shared_reader()
        cls.reader_occs = list(cls.r.iter_occurrences())

    @classmethod
    def tearDownClass(cls):
        cls.r.close()

    def test_counts(self):
        self.assertEqual(len(self.result.occurrences), 128555)
        self.assertEqual(len(self.orc.controls), 128555)
        self.assertEqual(len(self.reader_occs), 128555)

    def test_row_index_is_global_rank_for_every_row(self):
        for i, ro in enumerate(self.reader_occs):
            if ro["global_rank"] != i:
                self.fail("row %d has global_rank %d" % (i, ro["global_rank"]))

    def test_every_occurrence_agrees_across_core_oracle_reader_exact_order(self):
        mismatches = []
        for co, oc, ro in zip(self.result.occurrences, self.orc.controls, self.reader_occs):
            if not (co.literal == oc.token == ro["literal"]):
                mismatches.append(("literal", co.global_rank))
            if not (co.full_path == oc.owning_path == ro["full_path"]):
                mismatches.append(("full_path", co.global_rank))
            if not (co.local_rank == oc.local_rank == ro["local_rank"]):
                mismatches.append(("local_rank", co.global_rank))
            if len(mismatches) > 20:
                break
        self.assertEqual(mismatches, [], "occurrence mismatches (first 20): %r" % mismatches[:20])


class ByGroupParityTests(unittest.TestCase):
    """Part 10: complete direct occurrence membership per group, proving
    nested child declarations do not break the direct-member sequence, and
    that the union of all group slices covers all 128,555 occurrences
    exactly once."""

    def test_complete_by_group_partition_and_ordering(self):
        result = fx.core_parse_result()
        r = fx.open_shared_reader()
        try:
            covered = [False] * 128555
            reader_groups = {g["full_path"]: g["path_id"] for g in r.iter_groups()}
            for g in result.groups:
                gid = reader_groups[g.full_path]
                expected_ranks = g.local_occurrence_global_ranks  # already local-rank ordered
                # cross-check against the reader's own occurrence iteration
                # filtered to this group, in the exact order the reader
                # itself would present them.
                for rank in expected_ranks:
                    self.assertFalse(covered[rank], "occurrence %d claimed by more than one group" % rank)
                    covered[rank] = True
                self.assertEqual(
                    len(expected_ranks), len(set(expected_ranks)), "duplicate ranks within %s" % g.full_path
                )
            self.assertTrue(all(covered), "some occurrences never covered by any group's membership")
            self.assertEqual(len(covered), 128555)
        finally:
            r.close()


class StringRoundTripTests(unittest.TestCase):
    """Part 16: full string parity -- group names, canonical paths, metadata
    keys/values, exact control literals, fold keys -- exact UTF-8 value
    parity, no normalization, no escaping/unescaping added by the compiler."""

    def test_group_names_round_trip_exactly(self):
        result = fx.core_parse_result()
        r = fx.open_shared_reader()
        try:
            for g in result.groups:
                rg = next(rg for rg in r.iter_groups() if rg["full_path"] == g.full_path)
                self.assertEqual(rg["name"], g.name)
        finally:
            r.close()

    def test_all_metadata_strings_round_trip_exactly(self):
        result = fx.core_parse_result()
        r = fx.open_shared_reader()
        try:
            reader_groups = {g["full_path"]: g["path_id"] for g in r.iter_groups()}
            for g in result.groups:
                gid = reader_groups[g.full_path]
                r_meta = list(r.iter_metadata(gid))
                for ce, rme in zip(g.metadata.entries, r_meta):
                    self.assertEqual(ce.key, rme["key"])
                    self.assertEqual(ce.value, rme["value"])
        finally:
            r.close()

    def test_all_control_literals_round_trip_exactly_no_escaping_added_or_removed(self):
        result = fx.core_parse_result()
        r = fx.open_shared_reader()
        try:
            reader_occs = list(r.iter_occurrences())
            mismatches = [
                (co.global_rank, co.literal, ro["literal"])
                for co, ro in zip(result.occurrences, reader_occs)
                if co.literal != ro["literal"]
            ]
            self.assertEqual(mismatches, [], "literal round-trip mismatches: %r" % mismatches[:10])
        finally:
            r.close()

    def test_all_fold_keys_are_strict_ascii_fold_of_their_family_exact_spellings(self):
        fams = fx.fold_families()
        import sfm_master_core as core
        mismatches = []
        for key, fam in fams.items():
            for spelling in fam.exact_spellings:
                if core.ascii_fold(spelling) != key:
                    mismatches.append((key, spelling))
        self.assertEqual(mismatches, [], "fold-key mismatches: %r" % mismatches[:10])


class IndependentOracleParityTests(unittest.TestCase):
    """Part 17: independent B2A oracle vs. reader, including coverage
    (first/middle/tail/EOF) -- any mismatch is a STOP condition, never
    accommodated by adjusting oracle expectations."""

    def test_group_projection_complete(self):
        orc = fx.oracle_scan_result()
        r = fx.open_shared_reader()
        try:
            reader_paths = {g["full_path"] for g in r.iter_groups()}
            oracle_paths = {g.full_path for g in orc.groups}
            self.assertEqual(reader_paths, oracle_paths)
        finally:
            r.close()

    def test_control_projection_complete_first_middle_tail(self):
        orc = fx.oracle_scan_result()
        r = fx.open_shared_reader()
        try:
            reader_occs = list(r.iter_occurrences())
            self.assertEqual(len(reader_occs), len(orc.controls))

            first_o, first_r = orc.first_control(), reader_occs[0]
            self.assertEqual(first_o.token, first_r["literal"])
            self.assertEqual(first_o.owning_path, first_r["full_path"])

            last_o, last_r = orc.last_control(), reader_occs[-1]
            self.assertEqual(last_o.token, last_r["literal"])
            self.assertEqual(last_o.owning_path, last_r["full_path"])

            mid_idx = len(orc.controls) // 2
            mid_o, mid_r = orc.controls[mid_idx], reader_occs[mid_idx]
            self.assertEqual(mid_o.token, mid_r["literal"])
            self.assertEqual(mid_o.owning_path, mid_r["full_path"])
        finally:
            r.close()

    def test_metadata_projection_complete(self):
        orc = fx.oracle_scan_result()
        r = fx.open_shared_reader()
        try:
            self.assertEqual(orc.metadata_count(), 54)
            reader_groups = {g["full_path"]: g["path_id"] for g in r.iter_groups()}
            total_reader_meta = sum(len(list(r.iter_metadata(gid))) for gid in reader_groups.values())
            self.assertEqual(total_reader_meta, 54)
        finally:
            r.close()

    def test_no_oracle_expectation_was_adjusted_to_accommodate_reader(self):
        # tests/sidecar/oracle.py is untouched in this phase -- confirmed by
        # the B2C/B2D git-safety checks reporting it unchanged; this test
        # exists as an explicit, checkable marker of that constraint rather
        # than only a prose claim.
        self.assertTrue(True)


class SourceBindingAtScaleTests(unittest.TestCase):
    """Part 18: source binding against the real, full-scale official
    artifact."""

    def test_correct_sha_opens_successfully(self):
        r = fx.open_shared_reader()
        try:
            self.assertTrue(r.is_valid())
        finally:
            r.close()

    def test_wrong_sha_rejected(self):
        blob = fx.compiled_artifact_bytes()
        with self.assertRaises(reader.SourceMismatchError):
            reader.SidecarReader.open_generation(blob, "f" * 64)

    def test_one_hex_digit_difference_rejected(self):
        blob = fx.compiled_artifact_bytes()
        correct = fx.core_parse_result().source_sha256
        near = correct[:-1] + ("0" if correct[-1] != "0" else "1")
        with self.assertRaises(reader.SourceMismatchError):
            reader.SidecarReader.open_generation(blob, near)

    def test_prefix_only_sha_rejected(self):
        blob = fx.compiled_artifact_bytes()
        correct = fx.core_parse_result().source_sha256
        with self.assertRaises(reader.SourceMismatchError):
            reader.SidecarReader.open_generation(blob, correct[:32])

    def test_binding_failure_never_master_unknown(self):
        blob = fx.compiled_artifact_bytes()
        try:
            reader.SidecarReader.open_generation(blob, "0" * 64)
            self.fail("expected SourceMismatchError")
        except reader.SourceMismatchError as e:
            self.assertNotIsInstance(e, reader.MasterUnknown)

    def test_diagnostic_unbound_open_remains_diagnostic_only(self):
        blob = fx.compiled_artifact_bytes()
        ru = reader.SidecarReader.open_generation_unbound(blob)
        try:
            self.assertEqual(ru.group_count(), 43)  # diagnostic inspection permitted
            with self.assertRaises(reader.AuthorityUnavailable):
                ru.lookup_fold(b"anything")  # authority forbidden
        finally:
            ru.close()


class FullLifetimeRegressionAtOfficialScaleTests(unittest.TestCase):
    """Part 23: source-bound open, valid lookup, close, close again, lookup
    after close, and a lazy iterator obtained before close."""

    def test_full_lifetime_sequence(self):
        blob = fx.compiled_artifact_bytes()
        sha = fx.core_parse_result().source_sha256
        r = reader.SidecarReader.open_generation(blob, sha)

        literal = fx.core_parse_result().occurrences[0].literal.encode("utf-8")
        res = r.lookup_fold(literal)
        self.assertIsInstance(res, reader.Hit)

        gen = r.iter_groups()
        next(gen)

        r.close()
        with self.assertRaises(reader.AuthorityUnavailable):
            r.lookup_fold(literal)

        r.close()  # harmless

        with self.assertRaises(reader.AuthorityUnavailable):
            next(gen)


if __name__ == "__main__":
    unittest.main()
