"""Phase B2B: fixture-only round-trip qualification.

For every one of the 28 sidecar-profile-eligible B2A `valid/` fixtures:
parse with sfm_master_core -> compile with writer.compile_sidecar -> open
with reader.SidecarReader -> compare the opened generation against BOTH
sfm_master_core's own facts AND the independent tests/sidecar/oracle.py's
facts (not merely writer-vs-reader self-consistency, per Phase B2B Part 29).

Also covers: the 2 B2A `unsupported/` fixtures refused by the writer's
compatibility gate while still core-parseable; the 10 B2A `malformed/`
fixtures never reaching successful serialization (core rejects before the
writer is ever invoked).

Does NOT touch the official Master -- reserved for Phase B2D.
"""

import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(HERE))

import oracle  # noqa: E402
import sfm_master_core as core  # noqa: E402
from sfm_master_sidecar import reader, writer  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"


def _eligible_valid_fixture_names():
    names = []
    for name in sorted(os.listdir(str(FIXTURES_ROOT / "valid"))):
        data = (FIXTURES_ROOT / "valid" / name).read_bytes()
        result = core.parse_master_bytes(data, source_name=name)
        if result.ok and len([g for g in result.groups if g.parent_path is None]) == 1:
            names.append(name)
    return names


ELIGIBLE_VALID_FIXTURES = _eligible_valid_fixture_names()


class RoundTripAllValidFixturesTest(unittest.TestCase):
    """Exhaustive over all 28 eligible valid fixtures -- one subTest each,
    checking group/occurrence/metadata/fold parity against both oracles."""

    def test_all_valid_fixtures_are_eligible(self):
        # Sanity: B2A's 28 valid/ fixtures are, by construction, all
        # single-wrapper documents -- if this ever shrank, Part 29's
        # required-semantics coverage list would silently lose a case.
        self.assertEqual(len(ELIGIBLE_VALID_FIXTURES), 28)

    def test_round_trip_every_eligible_valid_fixture(self):
        for name in ELIGIBLE_VALID_FIXTURES:
            with self.subTest(fixture=name):
                self._round_trip_one(name)

    def _round_trip_one(self, name):
        path = FIXTURES_ROOT / "valid" / name
        data = path.read_bytes()
        result = core.parse_master_bytes(data, source_name=name)
        self.assertTrue(result.ok)
        orc = oracle.scan_bytes(data)

        blob = writer.compile_sidecar(data, result)
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)

        # --- Groups: parity vs core AND vs oracle. ---
        self.assertEqual(r.group_count(), len(result.groups))
        core_groups_by_path = {g.full_path: g for g in result.groups}
        oracle_groups_by_path = {og.full_path: og for og in orc.groups}
        reader_groups = list(r.iter_groups())
        self.assertEqual(
            {g["full_path"] for g in reader_groups}, set(core_groups_by_path.keys())
        )
        self.assertEqual(
            {g["full_path"] for g in reader_groups}, set(oracle_groups_by_path.keys())
        )
        for g in reader_groups:
            cg = core_groups_by_path[g["full_path"]]
            og = oracle_groups_by_path[g["full_path"]]
            self.assertEqual(g["declare_order"], cg.declare_order)
            self.assertEqual(g["declare_order"], og.declare_order)
            self.assertEqual(g["sibling_rank"], cg.sibling_rank)
            self.assertEqual(g["sibling_rank"], og.sibling_index)
            self.assertEqual(g["parent_path"], cg.parent_path)
            self.assertEqual(g["parent_path"], og.parent_path)

        # --- Occurrences: exact ordered parity vs core AND vs oracle. ---
        self.assertEqual(r.occurrence_count(), len(result.occurrences))
        reader_occs = list(r.iter_occurrences())
        self.assertEqual(len(reader_occs), len(orc.controls))
        for co, oc, ro in zip(result.occurrences, orc.controls, reader_occs):
            self.assertEqual(co.literal, ro["literal"])
            self.assertEqual(co.literal, oc.token)
            self.assertEqual(co.full_path, ro["full_path"])
            self.assertEqual(co.full_path, oc.owning_path)
            self.assertEqual(co.local_rank, ro["local_rank"])
            self.assertEqual(co.local_rank, oc.local_rank)

        # --- Metadata: parity vs core (source order, duplicates included). ---
        path_id_by_full_path = {g["full_path"]: g["path_id"] for g in reader_groups}
        for g in result.groups:
            gid = path_id_by_full_path[g.full_path]
            r_meta = list(r.iter_metadata(gid))
            self.assertEqual(len(r_meta), len(g.metadata.entries))
            for entry, rme in zip(g.metadata.entries, r_meta):
                self.assertEqual(entry.key, rme["key"])
                self.assertEqual(entry.value, rme["value"])

        # --- Fold lookup: HIT / FOLD_CONFLICT parity vs sfm_master_core's
        # own FoldFamily evidence, for every occurrence's exact literal. ---
        fams = core.build_fold_families(result.occurrences)
        for occ in result.occurrences:
            fam = fams[core.ascii_fold(occ.literal)]
            res = r.lookup_fold(occ.literal.encode("utf-8"))
            if fam.is_conflict:
                self.assertIsInstance(res, reader.FoldConflict)
                self.assertEqual(res.destinations, fam.destinations)
            else:
                self.assertIsInstance(res, reader.Hit)
                self.assertIn(res.destination, fam.destinations)
            # exhaustive: exact evidence set (literal, path, local_rank,
            # global_rank) at this fold matches every occurrence sharing the
            # fold key -- not merely the destination-count summary.
            expected_ranks = set(fam.occurrence_global_ranks)
            actual_ranks = {o["global_rank"] for o in res.occurrences()}
            self.assertEqual(actual_ranks, expected_ranks)

        r.close()

    def test_escape_spelling_round_trips_with_backslashes_intact(self):
        # Direct, explicit re-check of the specific escape-wording bug found
        # in Phase B1.2 (final spec Section 4): the compiled+reopened value
        # must retain every backslash exactly as written, never unescaped.
        path = FIXTURES_ROOT / "valid" / "21_escaped_quote_spelling.txt"
        data = path.read_bytes()
        result = core.parse_master_bytes(data, source_name="21")
        # Ground truth is sfm_master_core's own already-independently-verified
        # parse (never a hand-typed Python string literal here, which could
        # itself silently "fix" the very escaping behavior under test).
        expected_literal = result.occurrences[0].literal
        self.assertIn("\\", expected_literal, "fixture must actually contain a backslash")
        blob = writer.compile_sidecar(data, result)
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        occs = list(r.iter_occurrences())
        self.assertEqual(len(occs), 1)
        self.assertEqual(occs[0]["literal"], expected_literal)

    def test_non_bmp_astral_character_round_trips_exactly(self):
        path = FIXTURES_ROOT / "valid" / "20_non_bmp_text.txt"
        data = path.read_bytes()
        result = core.parse_master_bytes(data, source_name="20")
        blob = writer.compile_sidecar(data, result)
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        occs = list(r.iter_occurrences())
        self.assertEqual(occs[0]["literal"], result.occurrences[0].literal)
        # confirm it really is a non-BMP (astral) character, i.e. this test
        # actually exercises 4-byte UTF-8 sequences.
        self.assertTrue(any(ord(ch) > 0xFFFF for ch in occs[0]["literal"]))

    def test_whitespace_distinctions_round_trip_exactly(self):
        path = FIXTURES_ROOT / "valid" / "23_whitespace_distinctions.txt"
        data = path.read_bytes()
        result = core.parse_master_bytes(data, source_name="23")
        blob = writer.compile_sidecar(data, result)
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        occs = [o["literal"] for o in r.iter_occurrences()]
        core_literals = [o.literal for o in result.occurrences]
        self.assertEqual(occs, core_literals)

    def test_eof_final_entry_round_trips(self):
        path = FIXTURES_ROOT / "valid" / "26_final_entry_before_eof.txt"
        data = path.read_bytes()
        result = core.parse_master_bytes(data, source_name="26")
        blob = writer.compile_sidecar(data, result)
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        self.assertEqual(r.occurrence_count(), len(result.occurrences))
        occs = list(r.iter_occurrences())
        self.assertEqual(occs[-1]["literal"], result.occurrences[-1].literal)

    def test_custom_wrapper_name_round_trips(self):
        path = FIXTURES_ROOT / "valid" / "04_custom_wrapper_name.txt"
        data = path.read_bytes()
        result = core.parse_master_bytes(data, source_name="04")
        self.assertNotEqual(result.wrapper_paths, ["groupFile"])
        blob = writer.compile_sidecar(data, result)
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        self.assertEqual(r.wrapper_path(), result.wrapper_paths[0])

    def test_duplicate_metadata_keys_preserved_in_order(self):
        path = FIXTURES_ROOT / "valid" / "15_duplicate_metadata_keys.txt"
        data = path.read_bytes()
        result = core.parse_master_bytes(data, source_name="15")
        blob = writer.compile_sidecar(data, result)
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        for g in result.groups:
            if not g.metadata.entries:
                continue
            gid = [gg["path_id"] for gg in r.iter_groups() if gg["full_path"] == g.full_path][0]
            r_meta = list(r.iter_metadata(gid))
            self.assertEqual([m.key for m in g.metadata.entries], [m["key"] for m in r_meta])
            self.assertEqual([m.value for m in g.metadata.entries], [m["value"] for m in r_meta])

    def test_explicit_zero_metadata_value_not_conflated_with_absence(self):
        path = FIXTURES_ROOT / "valid" / "16_metadata_value_zero.txt"
        data = path.read_bytes()
        result = core.parse_master_bytes(data, source_name="16")
        blob = writer.compile_sidecar(data, result)
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        found_zero = False
        for g in result.groups:
            gid = [gg["path_id"] for gg in r.iter_groups() if gg["full_path"] == g.full_path][0]
            for m in r.iter_metadata(gid):
                if m["value"] == "0":
                    found_zero = True
        self.assertTrue(found_zero, "fixture must actually exercise an explicit \"0\" value")


class UnsupportedFixturesRefusedTest(unittest.TestCase):
    """The 2 B2A unsupported/ fixtures: core-parseable, but the writer's
    compatibility-profile gate must refuse them (final spec Section 3)."""

    def test_zero_parentless_groups_refused(self):
        path = FIXTURES_ROOT / "unsupported" / "empty_document.txt"
        data = path.read_bytes()
        result = core.parse_master_bytes(data, source_name="empty")
        self.assertTrue(result.ok)
        with self.assertRaises(writer.SidecarProfileError):
            writer.compile_sidecar(data, result)

    def test_multiple_parentless_groups_refused(self):
        path = FIXTURES_ROOT / "unsupported" / "multiple_parentless_groups.txt"
        data = path.read_bytes()
        result = core.parse_master_bytes(data, source_name="multi")
        self.assertTrue(result.ok)
        with self.assertRaises(writer.SidecarProfileError):
            writer.compile_sidecar(data, result)


class MalformedFixturesNeverReachWriterTest(unittest.TestCase):
    """All 10 B2A malformed/ fixtures: sfm_master_core.result.ok is False
    (or a UnicodeDecodeError is raised at decode time), so a correctly-wired
    compile orchestration never even calls the writer on them. This proves
    the refusal happens at the intended layer (core's own grammar gate),
    not merely "the writer also would have rejected it.\""""

    def test_every_malformed_fixture_is_rejected_before_the_writer(self):
        d = FIXTURES_ROOT / "malformed"
        names = sorted(os.listdir(str(d)))
        self.assertEqual(len(names), 10)
        for name in names:
            with self.subTest(fixture=name):
                data = (d / name).read_bytes()
                try:
                    result = core.parse_master_bytes(data, source_name=name)
                except UnicodeDecodeError:
                    continue  # malformed_utf8.txt: rejected before parsing even starts
                self.assertFalse(result.ok, "%s should not parse cleanly" % name)


if __name__ == "__main__":
    unittest.main()
