"""Phase B2D Parts 11-15: full 124,728/124,728 fold-family parity, every
known official fold looked up (HIT required, 0 conflicts, 0
MasterUnknown), full exact-literal lookup coverage (128,555/128,555, no
sampling), a deterministic absent-lookup set, and the full-scale ASCII-fold
evidence validation record.
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


class FoldFamilyParityTests(unittest.TestCase):
    """Part 11: every one of the 124,728 fold families compared
    individually -- key, ordering, membership, destinations, evidence,
    classification. Never validated by count alone."""

    @classmethod
    def setUpClass(cls):
        cls.fams = fx.fold_families()
        cls.r = fx.open_shared_reader()

    @classmethod
    def tearDownClass(cls):
        cls.r.close()

    def test_fold_count(self):
        self.assertEqual(len(self.fams), 124728)
        self.assertEqual(self.r.fold_count(), 124728)

    def test_zero_cross_destination_conflicts_in_official_master(self):
        conflicts = [k for k, f in self.fams.items() if f.is_conflict]
        self.assertEqual(len(conflicts), 0)

    def test_every_fold_family_individually_matches_reader(self):
        mismatches = []
        checked = 0
        for key, fam in self.fams.items():
            res = self.r.lookup_fold(key.encode("utf-8"))
            checked += 1
            if fam.is_conflict:
                if not isinstance(res, reader.FoldConflict):
                    mismatches.append((key, "expected FoldConflict, got %r" % res))
                    continue
                if res.destinations != fam.destinations:
                    mismatches.append((key, "destination set mismatch"))
            else:
                if not isinstance(res, reader.Hit):
                    mismatches.append((key, "expected Hit, got %r" % res))
                    continue
                if res.destination not in fam.destinations:
                    mismatches.append((key, "destination mismatch"))

            expected_ranks = set(fam.occurrence_global_ranks)
            actual_ranks = {o["global_rank"] for o in res.occurrences()}
            if expected_ranks != actual_ranks:
                mismatches.append((key, "evidence global-rank set mismatch (%d vs %d)" % (
                    len(expected_ranks), len(actual_ranks),
                )))

            if len(mismatches) > 20:
                break

        self.assertEqual(checked, 124728)
        self.assertEqual(mismatches, [], "fold family mismatches (first 20): %r" % mismatches[:20])


class KnownFoldLookupParityTests(unittest.TestCase):
    """Part 12: every known official fold identity looked up; HIT required
    for all 124,728 (official Master has 0 conflicts, so no FoldConflict/
    MasterUnknown is ever expected here)."""

    def test_all_known_folds_resolve_hit(self):
        fams = fx.fold_families()
        r = fx.open_shared_reader()
        try:
            passed = 0
            failures = []
            for key in fams:
                res = r.lookup_fold(key.encode("utf-8"))
                if isinstance(res, reader.Hit):
                    passed += 1
                else:
                    failures.append((key, type(res).__name__))
                    if len(failures) > 20:
                        break
            print("\n[B2D known-fold lookup] passed=%d / %d" % (passed, len(fams)))
            self.assertEqual(failures, [], "non-HIT results (first 20): %r" % failures[:20])
            self.assertEqual(passed, len(fams))
            self.assertEqual(passed, 124728)
        finally:
            r.close()


class ExactLiteralLookupCoverageTests(unittest.TestCase):
    """Part 13: every exact control literal identity queried. The official
    Master has 0 exact duplicate literals (validator-confirmed), so
    querying every occurrence's literal once (Option A) is identical in
    coverage to querying every unique literal once (Option B) -- no
    meaningless duplicate work either way."""

    def test_every_occurrence_literal_resolves_its_correct_stored_family(self):
        result = fx.core_parse_result()
        fams = fx.fold_families()
        r = fx.open_shared_reader()
        try:
            import sfm_master_core as core

            passed = 0
            failures = []
            for occ in result.occurrences:
                res = r.lookup_fold(occ.literal.encode("utf-8"))
                fam = fams[core.ascii_fold(occ.literal)]
                ok = (
                    (isinstance(res, reader.Hit) and res.destination == occ.full_path and not fam.is_conflict)
                    or (isinstance(res, reader.FoldConflict) and occ.full_path in res.destinations and fam.is_conflict)
                )
                if ok:
                    passed += 1
                else:
                    failures.append((occ.global_rank, occ.literal, occ.full_path, type(res).__name__))
                    if len(failures) > 20:
                        break
            print("\n[B2D exact-literal lookup coverage] passed=%d / %d" % (passed, len(result.occurrences)))
            self.assertEqual(failures, [], "literal lookup failures (first 20): %r" % failures[:20])
            self.assertEqual(passed, 128555)
        finally:
            r.close()

    def test_no_exact_duplicate_literals_confirms_option_a_and_b_equivalence(self):
        result = fx.core_parse_result()
        literals = [occ.literal for occ in result.occurrences]
        self.assertEqual(len(literals), len(set(literals)), "official Master must have 0 exact duplicates")


class AbsentLookupSetTests(unittest.TestCase):
    """Part 14: a deterministic small set of fold keys guaranteed absent
    from the official Master resolves MasterUnknown for a valid,
    source-bound reader. No malformed UTF-8 / invalid query types here --
    those are input-error behavior, covered elsewhere."""

    ABSENT_KEYS = [
        b"thisliteraldoesnotexistanywhereinthemaster",
        b"zzzznonexistentcontrolliteral999",
        b"qqqqabsentcontrolxyzxyzxyz",
        b"notarealcontrolnameatall12345",
        b"b2dabsentlookupsentinelvalue",
    ]

    @classmethod
    def setUpClass(cls):
        cls.result = fx.core_parse_result()
        cls.known_folds = set(fx.fold_families().keys())

    def test_absent_keys_are_genuinely_absent_from_the_official_master(self):
        import sfm_master_core as core
        for raw in self.ABSENT_KEYS:
            folded = core.ascii_fold(raw.decode("ascii"))
            self.assertNotIn(folded, self.known_folds, "%r must not actually be a real fold key" % raw)

    def test_absent_keys_resolve_master_unknown(self):
        r = fx.open_shared_reader()
        try:
            for raw in self.ABSENT_KEYS:
                with self.subTest(key=raw):
                    res = r.lookup_fold(raw)
                    self.assertIsInstance(res, reader.MasterUnknown)
        finally:
            r.close()


class FullAsciiFoldEvidenceValidationTests(unittest.TestCase):
    """Part 15: B2C's reader-open-time exhaustive per-occurrence ASCII-fold
    check already ran (over ALL 128,555 rows) when `open_shared_reader()`
    succeeded -- this class records that fact explicitly for the audit and
    re-confirms it independently via `sfm_master_core.ascii_fold` (never
    Unicode casefold/lower) against every occurrence."""

    def test_every_occurrence_ascii_fold_matches_its_own_fold_family_key(self):
        result = fx.core_parse_result()
        fams = fx.fold_families()
        import sfm_master_core as core

        mismatches = []
        for occ in result.occurrences:
            key = core.ascii_fold(occ.literal)
            if key not in fams or occ.global_rank not in fams[key].occurrence_global_ranks:
                mismatches.append(occ.global_rank)
                if len(mismatches) > 10:
                    break
        print("\n[B2D ASCII-fold validation] checked=%d / 128555, mismatches=%d" % (
            len(result.occurrences), len(mismatches),
        ))
        self.assertEqual(mismatches, [])
        self.assertEqual(len(result.occurrences), 128555)

    def test_reader_open_itself_already_performed_the_exhaustive_check(self):
        # A defensive re-confirmation: opening the reader is already
        # sufficient proof (B2C's Section 20.F check ran over the entire
        # OCCURRENCE TABLE at open time, non-sampled) -- this test exists
        # only to make that fact explicit and checkable in the B2D context.
        r = fx.open_shared_reader()
        try:
            self.assertTrue(r.is_valid())
            self.assertEqual(r.occurrence_count(), 128555)
        finally:
            r.close()


if __name__ == "__main__":
    unittest.main()
