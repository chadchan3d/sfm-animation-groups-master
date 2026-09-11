"""Phase B2B: reader lifetime tests (final spec Section 23, corrected in
B1.2a) -- VALID / INVALID / CLEANED, and the required invalidate-close-close
lifecycle test from final spec Section 41.

Not covered here (final spec Section 41's backing/lifetime fixture list,
Part 27): "confirmation that publishing a new manifest does not silently
retarget an already-open provider's view" -- there is no manifest or
publisher in Phase B2B's scope, so that specific fixture has nothing to
exercise yet and is deferred along with the rest of the publication work.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import sfm_master_core as core  # noqa: E402
from sfm_master_sidecar import reader, writer  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"


def _compile(name):
    path = FIXTURES_ROOT / "valid" / name
    data = path.read_bytes()
    result = core.parse_master_bytes(data, source_name=name)
    blob = writer.compile_sidecar(data, result)
    return data, result, blob


class RequiredInvalidateCloseCloseLifecycleTest(unittest.TestCase):
    """The exact 9-step test required by final spec Section 41 / B1.2a."""

    def test_invalidate_close_close(self):
        data, result, blob = _compile("06_sibling_groups.txt")

        # 1. open a valid provider
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        self.assertTrue(r.is_valid())

        # capture TWO lazy, provider-backed results obtained before
        # invalidation -- one deliberately exercised (and thereby closed,
        # per Python generator semantics: an exception escaping a generator
        # closes it) at step 3, a second held untouched for step 9, so step
        # 9 observes a genuine "first access after invalidation raises"
        # rather than re-probing an already-closed generator.
        gen_step3 = r.iter_groups()
        gen_step9 = r.iter_occurrences()
        first = next(gen_step3)
        self.assertEqual(first["path_id"], 0)

        # 2. force a fatal invalidation (direct fault-injection hook)
        r.force_invalidate_for_testing()

        # 3. verify every authority access now raises AuthorityUnavailable
        with self.assertRaises(reader.AuthorityUnavailable):
            r.group_count()
        with self.assertRaises(reader.AuthorityUnavailable):
            r.lookup_fold(b"a")
        with self.assertRaises(reader.AuthorityUnavailable):
            next(gen_step3)  # outstanding lazy result also fails on next access

        # 4. call close()
        r.close()

        # 5. owned resources released (this implementation defers cleanup to
        # close(); confirm it actually happened by checking internal state
        # directly -- the only way to observe "released" from outside is
        # step 6/7's no-op confirmation and step 8's continued unusability)
        self.assertEqual(r._state, reader.SidecarReader.STATE_CLEANED)
        self.assertIsNone(r._backing)

        # 6. call close() again
        r.close()  # must not raise

        # 7. step 6 was a harmless no-op
        self.assertEqual(r._state, reader.SidecarReader.STATE_CLEANED)

        # 8. provider remains unusable
        with self.assertRaises(reader.AuthorityUnavailable):
            r.group_count()

        # 9. every dependent lazy result/view obtained before step 2 remains
        # unusable -- checked here on the still-untouched second generator,
        # its first-ever `next()` call, well after close().
        with self.assertRaises(reader.AuthorityUnavailable):
            next(gen_step9)


class MaterializedResultSurvivesInvalidationTest(unittest.TestCase):
    """The OTHER permitted Section 23 dependent-result kind: an
    already-materialized, non-authoritative copy (Hit/FoldConflict) may
    legitimately keep returning its own already-known values after
    invalidation, since it no longer needs the provider for anything."""

    def test_hit_result_remains_readable_after_close(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        literal = result.occurrences[0].literal.encode("utf-8")
        hit = r.lookup_fold(literal)
        self.assertIsInstance(hit, reader.Hit)
        r.close()
        # already-materialized -- reading it does not touch the provider
        self.assertEqual(hit.destination, result.occurrences[0].full_path)
        self.assertEqual(len(hit.occurrences()), 1)


class BasicLifetimeStateMachineTests(unittest.TestCase):

    def test_double_close_is_harmless(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        r.close()
        r.close()  # must not raise

    def test_lookup_after_close_raises(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        r.close()
        with self.assertRaises(reader.AuthorityUnavailable):
            r.lookup_fold(b"a")

    def test_generator_started_before_close_fails_after_close(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        gen = r.iter_occurrences()
        next(gen)  # prime it
        r.close()
        with self.assertRaises(reader.AuthorityUnavailable):
            next(gen)

    def test_two_independently_opened_generations_do_not_share_state(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r1 = reader.SidecarReader.open_generation(blob, result.source_sha256)
        r2 = reader.SidecarReader.open_generation(blob, result.source_sha256)
        r1.close()
        self.assertFalse(r1.is_valid())
        self.assertTrue(r2.is_valid())
        self.assertEqual(r2.group_count(), len(result.groups))


if __name__ == "__main__":
    unittest.main()
