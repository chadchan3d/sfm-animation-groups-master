"""Phase B2C Parts 13-18: source-binding hardening, the provider
invalidation model, the invalidate-close-close lifecycle (cleanup-strategy
proof), resource-release observability, lazy-object invalidation across
every currently-exposed lazy accessor, and ordinary close().

The core invalidate-close-close 9-step lifecycle test itself was already
established in Phase B2B's test_reader_lifetime.py and is NOT duplicated
here; this file adds the specific coverage Phase B2C's Parts 13-18 call out
that B2B did not yet exercise: exact (non-prefix) source-SHA comparison,
MasterUnknown-never-substituted-for-invalidation, explicit proof of WHICH of
the two permitted cleanup-timing strategies this implementation uses, and
invalidation coverage for `iter_metadata` (the one lazy accessor B2B's
lifecycle test did not touch).
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(HERE))

import sfm_master_core as core  # noqa: E402
from sfm_master_sidecar import reader, writer  # noqa: E402
from corruption_helpers import compiled_fixture  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"


def _compile(name):
    return compiled_fixture(core, writer, FIXTURES_ROOT, name)


# ---------------------------------------------------------------------------
# Part 13: source binding hardening.
# ---------------------------------------------------------------------------


class SourceBindingHardeningTests(unittest.TestCase):

    def test_correct_source_sha_allows_authority_open(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        self.assertTrue(r.is_valid())

    def test_single_hex_digit_difference_is_rejected_no_prefix_matching(self):
        # The correct SHA with only its FINAL hex character changed --
        # proves the comparison is exact full-digest equality, never a
        # prefix/substring match.
        data, result, blob = _compile("06_sibling_groups.txt")
        correct = result.source_sha256
        last = correct[-1]
        replacement = "0" if last != "0" else "1"
        near_miss = correct[:-1] + replacement
        self.assertNotEqual(correct, near_miss)
        self.assertEqual(correct[:-1], near_miss[:-1])  # shares every byte except the last
        with self.assertRaises(reader.SourceMismatchError):
            reader.SidecarReader.open_generation(blob, near_miss)

    def test_truncated_prefix_of_correct_sha_is_rejected(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        prefix_only = result.source_sha256[:32]  # first half only
        with self.assertRaises(reader.SourceMismatchError):
            reader.SidecarReader.open_generation(blob, prefix_only)

    def test_binding_failure_raises_never_returns_master_unknown(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        try:
            reader.SidecarReader.open_generation(blob, "f" * 64)
            self.fail("expected SourceMismatchError")
        except reader.SourceMismatchError as e:
            self.assertNotIsInstance(e, reader.MasterUnknown)

    def test_unbound_open_never_grants_source_bound_authority(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation_unbound(blob)
        self.assertFalse(r._bound)
        with self.assertRaises(reader.AuthorityUnavailable):
            r.lookup_fold(b"a")


# ---------------------------------------------------------------------------
# Part 14: provider invalidation model.
# ---------------------------------------------------------------------------


class InvalidationModelTests(unittest.TestCase):

    def test_invalidation_never_falls_back_to_master_unknown(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        r.force_invalidate_for_testing()
        try:
            result_value = r.lookup_fold(b"a")
            self.fail("expected AuthorityUnavailable, got a return value: %r" % (result_value,))
        except reader.AuthorityUnavailable as e:
            self.assertNotIsInstance(e, reader.MasterUnknown)

    def test_invalidation_affects_all_subsequent_calls_not_just_the_first(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        r.force_invalidate_for_testing()
        for _ in range(3):
            with self.assertRaises(reader.AuthorityUnavailable):
                r.group_count()
        with self.assertRaises(reader.AuthorityUnavailable):
            r.lookup_fold(result.occurrences[0].literal.encode("utf-8"))

    def test_invalidation_before_any_lookup_still_refuses_previously_unproblematic_queries(self):
        # "Partial continued service from a known-compromised provider is
        # never permitted" (final spec Section 23) -- even a query that
        # would have cleanly resolved Hit on valid backing must be refused.
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        literal = result.occurrences[0].literal.encode("utf-8")
        hit = r.lookup_fold(literal)
        self.assertIsInstance(hit, reader.Hit)
        r.force_invalidate_for_testing()
        with self.assertRaises(reader.AuthorityUnavailable):
            r.lookup_fold(literal)


# ---------------------------------------------------------------------------
# Part 15/16: cleanup-timing strategy, explicitly proven (not merely
# asserted in prose) -- resource-release observability via the minimum
# necessary internal-state check.
# ---------------------------------------------------------------------------


class CleanupStrategyTests(unittest.TestCase):

    def test_this_implementation_defers_cleanup_to_close_not_to_invalidation(self):
        # Explicit proof of WHICH permitted strategy (final spec Section 23)
        # this implementation uses: invalidation alone does NOT release the
        # backing buffer -- only close() does. (The other permitted
        # strategy -- cleanup performed immediately at invalidation -- is
        # NOT what this code does; this test would fail if it were changed
        # to do that without also updating this test's expectations.)
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        self.assertIsNotNone(r._backing)
        r.force_invalidate_for_testing()
        self.assertEqual(r._state, reader.SidecarReader.STATE_INVALID)
        self.assertIsNotNone(r._backing, "resources must still be held immediately after invalidation")
        r.close()
        self.assertEqual(r._state, reader.SidecarReader.STATE_CLEANED)
        self.assertIsNone(r._backing, "close() must be the point where resources are actually released")

    def test_path_cache_also_released_on_close(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        r.group_full_path(0)  # populate the memoization cache
        self.assertTrue(len(r._path_cache) > 0)
        r.close()
        self.assertIsNone(r._path_cache)

    def test_cleanup_cannot_happen_twice_double_close_does_not_re_release(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        r.close()
        self.assertIsNone(r._backing)
        r.close()  # must not raise, and there is nothing left to double-release
        self.assertIsNone(r._backing)
        self.assertEqual(r._state, reader.SidecarReader.STATE_CLEANED)


# ---------------------------------------------------------------------------
# Part 17: lazy-object invalidation, across every currently-exposed lazy
# accessor. `iter_groups`/`iter_occurrences` are already covered by Phase
# B2B's required 9-step lifecycle test; `iter_metadata` is new here.
# ---------------------------------------------------------------------------


class LazyObjectInvalidationTests(unittest.TestCase):

    def test_iter_metadata_fails_on_next_access_after_invalidation(self):
        data, result, blob = _compile("15_duplicate_metadata_keys.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        gen = r.iter_metadata(1)  # "Grp" owns 2 metadata rows
        first = next(gen)
        self.assertIn(first["key"], ("selectable",))
        r.force_invalidate_for_testing()
        with self.assertRaises(reader.AuthorityUnavailable):
            next(gen)

    def test_iter_metadata_fails_on_next_access_after_close(self):
        data, result, blob = _compile("15_duplicate_metadata_keys.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        gen = r.iter_metadata(1)
        next(gen)
        r.close()
        with self.assertRaises(reader.AuthorityUnavailable):
            next(gen)

    def test_never_yet_started_generator_also_fails_immediately(self):
        # A generator that was OBTAINED before invalidation but never even
        # had its first `next()` called -- confirms the check happens
        # before the generator body touches `_backing` at all, not merely
        # on some later iteration.
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        gen_groups = r.iter_groups()
        gen_occs = r.iter_occurrences()
        gen_meta = r.iter_metadata(0)
        r.force_invalidate_for_testing()
        for gen in (gen_groups, gen_occs, gen_meta):
            with self.assertRaises(reader.AuthorityUnavailable):
                next(gen)

    def test_materialized_fold_results_are_the_documented_exception(self):
        # Hit/FoldConflict are the OTHER permitted kind (already-materialized,
        # non-authoritative copies) -- they legitimately remain usable after
        # invalidation. Documented and tested here explicitly so the two
        # categories are never blurred (Phase B2C Part 17's own instruction).
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        hit = r.lookup_fold(result.occurrences[0].literal.encode("utf-8"))
        r.force_invalidate_for_testing()
        # still readable -- this is correct, not a lifetime-contract leak.
        self.assertEqual(hit.destination, result.occurrences[0].full_path)


# ---------------------------------------------------------------------------
# Part 18: ordinary close, expanded.
# ---------------------------------------------------------------------------


class OrdinaryCloseExpandedTests(unittest.TestCase):

    def test_close_never_restores_or_reopens_authority(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        r.close()
        for _ in range(3):
            r.close()
            self.assertFalse(r.is_valid())
            with self.assertRaises(reader.AuthorityUnavailable):
                r.lookup_fold(b"a")

    def test_closing_one_handle_never_affects_an_independently_opened_second_handle(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r1 = reader.SidecarReader.open_generation(blob, result.source_sha256)
        r2 = reader.SidecarReader.open_generation(blob, result.source_sha256)
        r1.close()
        self.assertFalse(r1.is_valid())
        self.assertTrue(r2.is_valid())
        res = r2.lookup_fold(result.occurrences[0].literal.encode("utf-8"))
        self.assertIsInstance(res, reader.Hit)


if __name__ == "__main__":
    unittest.main()
