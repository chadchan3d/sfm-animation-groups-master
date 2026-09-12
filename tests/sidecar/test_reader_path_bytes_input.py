"""Python-2.7 path/bytes input-boundary fix (post-Gate-2A): explicit
regression coverage for the corrected `SidecarReader` entry points.

Root cause this file guards against: under Python 2.7, `bytes is str`, so a
type-based `isinstance(x, (bytes, bytearray))` check can never distinguish
"this is a filesystem path" from "this is raw artifact bytes" -- the
previous `_read_all(path_or_bytes)` helper relied on exactly that ambiguous
check and silently misread an ordinary path string as if it WERE the
artifact's own bytes. The fix removes all type-based dispatch: every entry
point's NAME now states its input mode explicitly
(`open_generation_bytes`/`open_generation_path`/
`open_generation_unbound_bytes`/`open_generation_unbound_path`), and the
legacy `open_generation`/`open_generation_unbound` names are now
explicitly-documented BYTES-ONLY aliases, never a path, on any Python
version.

These tests run under Python 3 (this repository's only available
interpreter, per the qualified support contract) -- the real Python-2.7
embedded-SFM re-qualification of this exact corrected file is a separate,
mandatory step (Gate 1 H1 rerun), not substituted by anything here.
"""

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT / "tools"))

import sfm_master_core as core  # noqa: E402
from sfm_master_sidecar import reader, writer  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"


def _compile(name="06_sibling_groups.txt"):
    path = FIXTURES_ROOT / "valid" / name
    data = path.read_bytes()
    result = core.parse_master_bytes(data, source_name=name)
    blob = writer.compile_sidecar(data, result)
    return data, result, blob


class ExplicitBytesEntryPointTests(unittest.TestCase):

    def test_open_generation_bytes_succeeds(self):
        data, result, blob = _compile()
        r = reader.SidecarReader.open_generation_bytes(blob, result.source_sha256)
        try:
            self.assertTrue(r.is_valid())
            self.assertEqual(r.group_count(), 4)
        finally:
            r.close()

    def test_open_generation_bytes_rejects_non_bytes_type(self):
        with self.assertRaises(TypeError):
            reader.SidecarReader.open_generation_bytes(12345, "0" * 64)
        with self.assertRaises(TypeError):
            reader.SidecarReader.open_generation_bytes(None, "0" * 64)

    def test_open_generation_bytes_never_treats_a_path_looking_string_as_a_path(self):
        # A bytes object that happens to CONTAIN path-like text must still
        # be rejected as corrupt artifact content, never opened as a file --
        # `open_generation_bytes` performs no filesystem access at all.
        fake = b"E:\\not\\a\\real\\sidecar\\path.bin"
        with self.assertRaises(reader.AuthorityUnavailable):
            reader.SidecarReader.open_generation_bytes(fake, "0" * 64)

    def test_open_generation_unbound_bytes_succeeds_diagnostic_only(self):
        data, result, blob = _compile()
        r = reader.SidecarReader.open_generation_unbound_bytes(blob)
        try:
            self.assertEqual(r.group_count(), 4)
            with self.assertRaises(reader.AuthorityUnavailable):
                r.lookup_fold(b"a")
        finally:
            r.close()


class ExplicitPathEntryPointTests(unittest.TestCase):

    def test_open_generation_path_succeeds(self):
        data, result, blob = _compile()
        path = FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"
        with __import__("tempfile").TemporaryDirectory() as tmp:
            artifact_path = Path(tmp) / "artifact.bin"
            artifact_path.write_bytes(blob)
            r = reader.SidecarReader.open_generation_path(str(artifact_path), result.source_sha256)
            try:
                self.assertTrue(r.is_valid())
                self.assertEqual(r.group_count(), 4)
            finally:
                r.close()

    def test_open_generation_path_never_treats_the_path_text_as_artifact_bytes(self):
        # The specific Gate 2A failure mode: a path string must always be
        # OPENED, never misread as if its characters were the sidecar's own
        # bytes. Confirmed by using a path whose length exceeds the header
        # size (so if it were ever misread as content, it would attempt --
        # and fail -- structural validation on the path text itself; here it
        # must instead succeed, because the real file at that path is opened).
        data, result, blob = _compile()
        with __import__("tempfile").TemporaryDirectory() as tmp:
            artifact_path = Path(tmp) / "a_path_with_more_than_eight_characters_in_it.bin"
            artifact_path.write_bytes(blob)
            r = reader.SidecarReader.open_generation_path(str(artifact_path), result.source_sha256)
            try:
                self.assertTrue(r.is_valid())
            finally:
                r.close()

    def test_open_generation_path_rejects_nonexistent_path(self):
        with self.assertRaises(OSError):
            reader.SidecarReader.open_generation_path(
                r"C:\this\path\definitely\does\not\exist\anywhere.bin", "0" * 64,
            )

    def test_open_generation_unbound_path_succeeds_diagnostic_only(self):
        data, result, blob = _compile()
        with __import__("tempfile").TemporaryDirectory() as tmp:
            artifact_path = Path(tmp) / "artifact.bin"
            artifact_path.write_bytes(blob)
            r = reader.SidecarReader.open_generation_unbound_path(str(artifact_path))
            try:
                self.assertEqual(r.group_count(), 4)
                with self.assertRaises(reader.AuthorityUnavailable):
                    r.lookup_fold(b"a")
            finally:
                r.close()


class PathBytesSemanticEquivalenceTests(unittest.TestCase):
    """The core regression proof: opening the SAME artifact via the bytes
    entry point and via the path entry point must produce semantically
    identical, fully-agreeing results."""

    def test_path_and_bytes_open_agree_on_official_master_scale_fixture(self):
        data, result, blob = _compile("28_large_alias_family.txt")
        with __import__("tempfile").TemporaryDirectory() as tmp:
            artifact_path = Path(tmp) / "artifact.bin"
            artifact_path.write_bytes(blob)

            r_bytes = reader.SidecarReader.open_generation_bytes(blob, result.source_sha256)
            r_path = reader.SidecarReader.open_generation_path(str(artifact_path), result.source_sha256)
            try:
                self.assertEqual(r_bytes.group_count(), r_path.group_count())
                self.assertEqual(r_bytes.occurrence_count(), r_path.occurrence_count())
                self.assertEqual(r_bytes.fold_count(), r_path.fold_count())
                self.assertEqual(list(r_bytes.iter_groups()), list(r_path.iter_groups()))
                self.assertEqual(list(r_bytes.iter_occurrences()), list(r_path.iter_occurrences()))

                for occ in result.occurrences:
                    res_bytes = r_bytes.lookup_fold(occ.literal.encode("utf-8"))
                    res_path = r_path.lookup_fold(occ.literal.encode("utf-8"))
                    self.assertEqual(type(res_bytes), type(res_path))
                    if isinstance(res_bytes, reader.Hit):
                        self.assertEqual(res_bytes.destination, res_path.destination)
                    elif isinstance(res_bytes, reader.FoldConflict):
                        self.assertEqual(res_bytes.destinations, res_path.destinations)
            finally:
                r_bytes.close()
                r_path.close()

    def test_path_and_bytes_open_agree_checksum_failure(self):
        data, result, blob = _compile()
        bad = bytearray(blob)
        bad[-1] ^= 0xFF  # corrupt a content byte without recomputing the digest
        bad = bytes(bad)
        with __import__("tempfile").TemporaryDirectory() as tmp:
            artifact_path = Path(tmp) / "artifact.bin"
            artifact_path.write_bytes(bad)

            with self.assertRaises(reader.AuthorityUnavailable):
                reader.SidecarReader.open_generation_bytes(bad, result.source_sha256)
            with self.assertRaises(reader.AuthorityUnavailable):
                reader.SidecarReader.open_generation_path(str(artifact_path), result.source_sha256)

    def test_path_and_bytes_open_agree_source_mismatch(self):
        data, result, blob = _compile()
        wrong_sha = "0" * 64
        with __import__("tempfile").TemporaryDirectory() as tmp:
            artifact_path = Path(tmp) / "artifact.bin"
            artifact_path.write_bytes(blob)

            with self.assertRaises(reader.SourceMismatchError):
                reader.SidecarReader.open_generation_bytes(blob, wrong_sha)
            with self.assertRaises(reader.SourceMismatchError):
                reader.SidecarReader.open_generation_path(str(artifact_path), wrong_sha)

    def test_path_and_bytes_open_agree_close_lifetime(self):
        data, result, blob = _compile()
        with __import__("tempfile").TemporaryDirectory() as tmp:
            artifact_path = Path(tmp) / "artifact.bin"
            artifact_path.write_bytes(blob)

            r_bytes = reader.SidecarReader.open_generation_bytes(blob, result.source_sha256)
            r_path = reader.SidecarReader.open_generation_path(str(artifact_path), result.source_sha256)

            r_bytes.close()
            r_path.close()
            r_bytes.close()  # idempotent
            r_path.close()  # idempotent

            with self.assertRaises(reader.AuthorityUnavailable):
                r_bytes.lookup_fold(b"a")
            with self.assertRaises(reader.AuthorityUnavailable):
                r_path.lookup_fold(b"a")


class LegacyAliasExplicitContractTests(unittest.TestCase):
    """The legacy `open_generation`/`open_generation_unbound` names must
    remain explicitly bytes-only -- proven directly, not merely asserted in
    a docstring, so their contract cannot silently drift back into
    ambiguity."""

    def test_legacy_open_generation_is_bytes_only(self):
        data, result, blob = _compile()
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        try:
            self.assertTrue(r.is_valid())
        finally:
            r.close()

    def test_legacy_open_generation_never_opens_a_path(self):
        # Passing a real, valid path string to the LEGACY entry point must
        # NEVER open that file -- confirming the legacy alias is
        # unambiguous even when given path-shaped text. WHICH exception
        # type results is itself a direct, correct consequence of the
        # Python-version type system: under Python 3, `str` is genuinely
        # not `bytes`, so `_coerce_bytes`'s defense-in-depth check catches
        # it immediately with `TypeError` (never reaching the filesystem or
        # the artifact validator at all -- the strictest possible outcome).
        # Under Python 2.7, `str` IS `bytes`, so the path text passes the
        # type check and is instead validated AS artifact content, which
        # then correctly fails with `AuthorityUnavailable` (magic mismatch)
        # -- safely reproducing the original Gate 2A failure mode's
        # rejection, never silently opening the file. Both are acceptable;
        # what matters is that the file is NEVER opened by this call.
        data, result, blob = _compile()
        with __import__("tempfile").TemporaryDirectory() as tmp:
            artifact_path = Path(tmp) / "artifact.bin"
            artifact_path.write_bytes(blob)
            with self.assertRaises((TypeError, reader.AuthorityUnavailable)):
                reader.SidecarReader.open_generation(str(artifact_path), result.source_sha256)

    def test_legacy_open_generation_unbound_is_bytes_only(self):
        data, result, blob = _compile()
        r = reader.SidecarReader.open_generation_unbound(blob)
        try:
            self.assertEqual(r.group_count(), 4)
        finally:
            r.close()

    def test_legacy_aliases_delegate_to_explicit_bytes_entry_points(self):
        # Structural proof the aliases are thin delegations, not a second
        # independent implementation that could drift.
        import inspect
        src_bound = inspect.getsource(reader.SidecarReader.open_generation.__func__)
        src_unbound = inspect.getsource(reader.SidecarReader.open_generation_unbound.__func__)
        self.assertIn("open_generation_bytes", src_bound)
        self.assertIn("open_generation_unbound_bytes", src_unbound)


if __name__ == "__main__":
    unittest.main()
