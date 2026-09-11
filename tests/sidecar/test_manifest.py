"""Phase B2E: tools/sfm_master_sidecar/manifest.py -- build/serialize/parse
round trip and the full hardened-parser rejection matrix (Part 12).
"""

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from sfm_master_sidecar import compiler, manifest  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"


def _sample_manifest_dict():
    snap = compiler.capture_source_snapshot(FIXTURES_ROOT / "valid" / "06_sibling_groups.txt")
    outcome = compiler.parse_and_compile(snap)
    gen_name = compiler.generation_basename(outcome.ordinary_sha256)
    return manifest.build_manifest_dict(outcome, gen_name), outcome


class BuildSerializeParseRoundTripTests(unittest.TestCase):

    def test_round_trip(self):
        d, outcome = _sample_manifest_dict()
        data = manifest.serialize_manifest(d)
        parsed = manifest.parse_manifest_bytes(data)
        self.assertEqual(parsed.generation_basename, d["generation_basename"])
        self.assertEqual(parsed.sidecar_sha256, outcome.ordinary_sha256)
        self.assertEqual(parsed.source_sha256, outcome.snapshot.sha256_hex)
        self.assertEqual(parsed.source_byte_length, len(outcome.snapshot.bytes))
        self.assertEqual(parsed.counts["groups"], len(outcome.result.groups))
        self.assertEqual(parsed.counts["occurrences"], len(outcome.result.occurrences))

    def test_serialization_is_deterministic(self):
        d, _ = _sample_manifest_dict()
        self.assertEqual(manifest.serialize_manifest(d), manifest.serialize_manifest(dict(d)))

    def test_serialized_manifest_is_valid_json(self):
        d, _ = _sample_manifest_dict()
        data = manifest.serialize_manifest(d)
        json.loads(data.decode("utf-8"))  # must not raise


class ManifestHardeningTests(unittest.TestCase):

    def setUp(self):
        self.d, _ = _sample_manifest_dict()

    def _mutate(self, **overrides):
        d = dict(self.d)
        d.update(overrides)
        return manifest.serialize_manifest(d)

    def test_oversized_manifest_rejected(self):
        with self.assertRaises(manifest.ManifestError):
            manifest.parse_manifest_bytes(b"x" * (manifest.MAX_MANIFEST_BYTES + 1))

    def test_invalid_json_rejected(self):
        with self.assertRaises(manifest.ManifestError):
            manifest.parse_manifest_bytes(b"{not valid json")

    def test_top_level_not_an_object_rejected(self):
        with self.assertRaises(manifest.ManifestError):
            manifest.parse_manifest_bytes(b"[1, 2, 3]")

    def test_duplicate_json_keys_rejected(self):
        raw = b'{"generation_basename": "a", "generation_basename": "b"}'
        with self.assertRaises(manifest.ManifestError):
            manifest.parse_manifest_bytes(raw)

    def test_each_required_key_missing_is_rejected(self):
        for key in [
            "generation_basename", "sidecar_sha256", "source_sha256", "source_byte_length",
            "format_contract_version", "authority_semantics_version", "counts",
        ]:
            with self.subTest(missing=key):
                d = dict(self.d)
                del d[key]
                with self.assertRaises(manifest.ManifestError):
                    manifest.parse_manifest_bytes(manifest.serialize_manifest(d))

    def test_wrong_type_for_each_required_key_is_rejected(self):
        wrong_values = {
            "generation_basename": 12345,
            "sidecar_sha256": 12345,
            "source_sha256": 12345,
            "source_byte_length": "not-an-int",
            "format_contract_version": "0",
            "authority_semantics_version": "0",
            "counts": "not-a-dict",
        }
        for key, bad_value in wrong_values.items():
            with self.subTest(key=key):
                with self.assertRaises(manifest.ManifestError):
                    manifest.parse_manifest_bytes(self._mutate(**{key: bad_value}))

    def test_invalid_sha256_values_rejected(self):
        for key in ("sidecar_sha256", "source_sha256"):
            with self.subTest(key=key):
                for bad in ["not-hex", "a" * 63, "a" * 65, "A" * 64, ""]:
                    with self.assertRaises(manifest.ManifestError):
                        manifest.parse_manifest_bytes(self._mutate(**{key: bad}))

    def test_unsupported_format_contract_version_rejected(self):
        with self.assertRaises(manifest.ManifestError):
            manifest.parse_manifest_bytes(self._mutate(format_contract_version=999))

    def test_unsupported_authority_semantics_version_rejected(self):
        with self.assertRaises(manifest.ManifestError):
            manifest.parse_manifest_bytes(self._mutate(authority_semantics_version=999))

    def test_generation_basename_path_traversal_variants_rejected(self):
        bad_names = [
            "../evil.bin",
            "../../etc/passwd",
            "/absolute/path.bin",
            "sub/dir/evil.bin",
            "sub\\dir\\evil.bin",
            "C:\\evil.bin",
            "C:evil.bin",
            "..",
            "",
            "   ",
        ]
        for bad in bad_names:
            with self.subTest(name=bad):
                with self.assertRaises(manifest.ManifestError):
                    manifest.parse_manifest_bytes(self._mutate(generation_basename=bad))

    def test_generation_basename_not_matching_naming_scheme_rejected(self):
        with self.assertRaises(manifest.ManifestError):
            manifest.parse_manifest_bytes(self._mutate(generation_basename="not_the_right_scheme.bin"))

    def test_missing_count_subkey_rejected(self):
        d = dict(self.d)
        counts = dict(d["counts"])
        del counts["folds"]
        d["counts"] = counts
        with self.assertRaises(manifest.ManifestError):
            manifest.parse_manifest_bytes(manifest.serialize_manifest(d))

    def test_negative_source_byte_length_rejected(self):
        with self.assertRaises(manifest.ManifestError):
            manifest.parse_manifest_bytes(self._mutate(source_byte_length=-1))

    def test_non_utf8_bytes_rejected(self):
        with self.assertRaises(manifest.ManifestError):
            manifest.parse_manifest_bytes(b"\xff\xfe\x00\x01")


class ResolveGenerationPathTests(unittest.TestCase):

    def test_resolves_within_output_dir(self):
        import tempfile
        d, _ = _sample_manifest_dict()
        with tempfile.TemporaryDirectory() as tmp:
            m = manifest.parse_manifest_bytes(manifest.serialize_manifest(d))
            path = manifest.resolve_generation_path(tmp, m)
            self.assertEqual(Path(path).parent, Path(tmp))
            self.assertEqual(Path(path).name, d["generation_basename"])


if __name__ == "__main__":
    unittest.main()
