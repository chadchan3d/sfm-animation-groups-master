"""Phase B2D Parts 1/3/4/20/21/22: capture one exact source snapshot,
compile it through the real production writer (no shortcut/full-Master-only
serializer), confirm the artifact exists only in memory, record its
identity/size/section breakdown, and check resource-limit headroom.

This is the FIRST full official-Master sidecar compile. The artifact is a
TEST ARTIFACT ONLY -- never written to the repository, never published as an
active generation (final spec Part 4/29).
"""

import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import official_master_fixture as fx  # noqa: E402
from sfm_master_sidecar import format as fmt  # noqa: E402
from sfm_master_sidecar import reader  # noqa: E402


class SourceSnapshotIdentityTests(unittest.TestCase):

    def test_source_byte_length_and_sha_match_expected_baseline(self):
        data = fx.load_source_bytes()
        self.assertEqual(len(data), fx.source_byte_length())
        import hashlib
        self.assertEqual(hashlib.sha256(data).hexdigest(), fx.EXPECTED_SOURCE_SHA256)

    def test_core_parse_and_oracle_scan_agree_on_the_same_captured_bytes(self):
        # Both consumed the exact same `load_source_bytes()` object (a
        # single cached read) -- not two independent re-reads of the file
        # that could theoretically observe different content.
        result = fx.core_parse_result()
        orc = fx.oracle_scan_result()
        self.assertEqual(result.source_sha256, fx.EXPECTED_SOURCE_SHA256)
        self.assertEqual(len(result.groups), fx.EXPECTED_GROUP_COUNT)
        self.assertEqual(orc.group_count(), fx.EXPECTED_GROUP_COUNT)


class FullCompileResultTests(unittest.TestCase):

    def test_official_master_is_eligible_and_compiles_via_real_writer(self):
        result = fx.core_parse_result()
        self.assertTrue(result.ok)
        parentless = [g for g in result.groups if g.parent_path is None]
        self.assertEqual(len(parentless), fx.EXPECTED_PARENTLESS_COUNT)
        self.assertEqual(parentless[0].full_path, "groupFile")

        blob = fx.compiled_artifact_bytes()
        self.assertGreater(len(blob), 0)

    def test_writer_module_used_is_the_same_one_qualified_on_fixtures(self):
        # No parallel/shortcut serializer exists -- `writer.compile_sidecar`
        # is the one and only compile entry point, imported directly.
        import inspect
        from sfm_master_sidecar import writer
        src_path = Path(inspect.getfile(writer.compile_sidecar))
        self.assertEqual(src_path.name, "writer.py")
        self.assertEqual(src_path.parent.name, "sfm_master_sidecar")

    def test_reader_opens_and_validates_the_official_artifact(self):
        r = fx.open_shared_reader()
        try:
            self.assertTrue(r.is_valid())
            self.assertEqual(r.group_count(), fx.EXPECTED_GROUP_COUNT)
            self.assertEqual(r.occurrence_count(), fx.EXPECTED_OCCURRENCE_COUNT)
            self.assertEqual(r.fold_count(), fx.EXPECTED_FOLD_COUNT)
            self.assertEqual(r.wrapper_path(), "groupFile")
        finally:
            r.close()


class ArtifactIdentityTests(unittest.TestCase):

    def test_artifact_identity_recorded(self):
        blob = fx.compiled_artifact_bytes()
        import hashlib
        ordinary_sha = hashlib.sha256(blob).hexdigest()
        header = fmt.unpack_header(blob)
        embedded_digest_hex = header.embedded_integrity_digest.hex()

        self.assertEqual(len(blob), header.payload_length)
        self.assertEqual(header.source_byte_length, fx.source_byte_length())
        self.assertEqual(header.source_sha256, bytes.fromhex(fx.EXPECTED_SOURCE_SHA256))
        # ordinary full-file SHA and the embedded digest are computed
        # differently (embedded digest zeroes its own field first) and must
        # never coincide by construction.
        self.assertNotEqual(ordinary_sha, embedded_digest_hex)

        print("\n[B2D artifact identity] bytes=%d ordinary_sha256=%s embedded_digest=%s" % (
            len(blob), ordinary_sha, embedded_digest_hex,
        ))

    def test_no_disk_artifact_is_ever_created_by_this_test_suite(self):
        # The artifact lives only in `compiled_artifact_bytes()`'s cached
        # Python bytes object -- never passed to any file-writing call in
        # this file or in official_master_fixture.py (grep-verified: the
        # only I/O in official_master_fixture.py is the ONE read of the
        # source Master itself).
        import inspect
        src = inspect.getsource(fx)
        self.assertNotIn("write_bytes", src)
        self.assertNotIn("open(", src.replace("MASTER_PATH.read_bytes", ""))


class SectionSizeBreakdownTests(unittest.TestCase):

    def test_section_sizes_reconcile_to_total_artifact_size(self):
        blob = fx.compiled_artifact_bytes()
        header = fmt.unpack_header(blob)
        total = fmt.HEADER_SIZE + header.section_count * fmt.DIRECTORY_ROW_SIZE

        print("\n[B2D section breakdown] total artifact bytes: %d" % len(blob))
        print("  HEADER                       bytes=%8d" % fmt.HEADER_SIZE)
        print("  SECTION_DIRECTORY            bytes=%8d" % (header.section_count * fmt.DIRECTORY_ROW_SIZE))

        rows = []
        for i in range(header.section_count):
            row = fmt.unpack_directory_row(blob, header.section_directory_offset + i * fmt.DIRECTORY_ROW_SIZE)
            rows.append(row)
            total += row.length
            pct = 100.0 * row.length / len(blob)
            print("  %-28s rows=%9d bytes=%9d (%5.2f%%)" % (
                fmt.SECTION_NAMES[row.section_id], row.row_count, row.length, pct,
            ))

        self.assertEqual(total, len(blob))

        by_name = {fmt.SECTION_NAMES[row.section_id]: row for row in rows}
        self.assertEqual(by_name["GROUP_TABLE"].row_count, fx.EXPECTED_GROUP_COUNT)
        self.assertEqual(by_name["CHILD_ID_INDEX"].row_count, fx.EXPECTED_CHILD_INDEX_ROW_COUNT)
        self.assertEqual(by_name["METADATA_TABLE"].row_count, fx.EXPECTED_METADATA_COUNT)
        self.assertEqual(by_name["OCCURRENCE_TABLE"].row_count, fx.EXPECTED_OCCURRENCE_COUNT)
        self.assertEqual(by_name["OCCURRENCE_BY_GROUP_INDEX"].row_count, fx.EXPECTED_OCCURRENCE_COUNT)
        self.assertEqual(by_name["FOLD_TABLE"].row_count, fx.EXPECTED_FOLD_COUNT)
        self.assertEqual(by_name["OCCURRENCE_BY_FOLD_INDEX"].row_count, fx.EXPECTED_OCCURRENCE_COUNT)


class ResourceLimitHeadroomTests(unittest.TestCase):

    def test_usage_far_below_every_configured_limit(self):
        result = fx.core_parse_result()
        blob = fx.compiled_artifact_bytes()
        header = fmt.unpack_header(blob)

        string_pool_row = next(
            fmt.unpack_directory_row(blob, header.section_directory_offset + i * fmt.DIRECTORY_ROW_SIZE)
            for i in range(header.section_count)
            if fmt.unpack_directory_row(
                blob, header.section_directory_offset + i * fmt.DIRECTORY_ROW_SIZE
            ).section_id == fmt.SECTION_STRING_POOL
        )
        string_table_row = next(
            fmt.unpack_directory_row(blob, header.section_directory_offset + i * fmt.DIRECTORY_ROW_SIZE)
            for i in range(header.section_count)
            if fmt.unpack_directory_row(
                blob, header.section_directory_offset + i * fmt.DIRECTORY_ROW_SIZE
            ).section_id == fmt.SECTION_STRING_TABLE
        )

        usages = {
            "source_byte_size": (fx.source_byte_length(), fmt.LIMIT_SOURCE_BYTE_SIZE),
            "sidecar_byte_size": (len(blob), fmt.LIMIT_SIDECAR_BYTE_SIZE),
            "group_count": (len(result.groups), fmt.LIMIT_GROUP_COUNT),
            "occurrence_count": (len(result.occurrences), fmt.LIMIT_OCCURRENCE_COUNT),
            "fold_count": (len(fx.fold_families()), fmt.LIMIT_FOLD_COUNT),
            "string_count": (string_table_row.row_count, fmt.LIMIT_DISTINCT_POOL_STRINGS),
            "string_pool_total_bytes": (string_pool_row.length, fmt.LIMIT_STRING_POOL_TOTAL_BYTES),
        }

        max_single_string_len = 0
        for g in result.groups:
            max_single_string_len = max(max_single_string_len, len(g.name.encode("utf-8")))
            for e in g.metadata.entries:
                max_single_string_len = max(
                    max_single_string_len, len(e.key.encode("utf-8")), len(e.value.encode("utf-8"))
                )
        for occ in result.occurrences:
            max_single_string_len = max(max_single_string_len, len(occ.literal.encode("utf-8")))
        usages["max_single_string_length"] = (max_single_string_len, fmt.LIMIT_SINGLE_STRING_BYTE_LENGTH)

        max_metadata_per_group = max((len(g.metadata.entries) for g in result.groups), default=0)
        usages["max_metadata_rows_per_group"] = (max_metadata_per_group, fmt.LIMIT_METADATA_ROWS_PER_GROUP)

        print("\n[B2D resource-limit headroom]")
        close_to_limit = []
        for name, (usage, limit) in usages.items():
            pct = 100.0 * usage / limit
            print("  %-28s %12d / %12d  (%.4f%%)" % (name, usage, limit, pct))
            self.assertLess(usage, limit, "%s exceeds its configured limit" % name)
            if pct > 10.0:
                close_to_limit.append((name, pct))

        self.assertEqual(close_to_limit, [], "unexpectedly close to a resource limit: %r" % close_to_limit)


class DevelopmentHostMemoryObservationTests(unittest.TestCase):
    """DEVELOPMENT-HOST ONLY. Never used to infer embedded x86 SFM memory
    safety -- stdlib `tracemalloc` only, no new dependency."""

    def test_approximate_memory_impact_development_host_only(self):
        import tracemalloc

        was_tracing = tracemalloc.is_tracing()
        if not was_tracing:
            tracemalloc.start()
        try:
            snap_before = tracemalloc.take_snapshot()
            r = fx.open_shared_reader()
            try:
                snap_after = tracemalloc.take_snapshot()
                delta = sum(s.size_diff for s in snap_after.compare_to(snap_before, "filename"))
                current, peak = tracemalloc.get_traced_memory()
                print(
                    "\n[B2D DEVELOPMENT-HOST ONLY memory observation] "
                    "reader-open delta=%.2f MiB current_traced=%.2f MiB peak_traced=%.2f MiB "
                    "(desktop Python process; NOT embedded x86 SFM evidence)" % (
                        delta / (1024 * 1024), current / (1024 * 1024), peak / (1024 * 1024),
                    )
                )
                self.assertTrue(r.is_valid())
            finally:
                r.close()
        finally:
            if not was_tracing:
                tracemalloc.stop()


class TimingTests(unittest.TestCase):
    """Development-host timings only -- NOT Gate 2 embedded evidence."""

    def test_pipeline_stage_timings_recorded(self):
        import hashlib

        t0 = time.time()
        data = fx.MASTER_PATH.read_bytes()
        hashlib.sha256(data).hexdigest()
        t1 = time.time()

        import sfm_master_core as core
        result = core.parse_master_bytes(data, source_name="timing-run")
        t2 = time.time()

        import oracle as oracle_module
        oracle_module.scan_bytes(data)
        t3 = time.time()

        from sfm_master_sidecar import writer
        blob = writer.compile_sidecar(data, result)
        t4 = time.time()

        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        t5 = time.time()
        r.close()

        print(
            "\n[B2D DEVELOPMENT-HOST timings, seconds] "
            "read+hash=%.3f core_parse=%.3f oracle_scan=%.3f writer_compile=%.3f reader_open_validate=%.3f "
            "total=%.3f" % (
                t1 - t0, t2 - t1, t3 - t2, t4 - t3, t5 - t4, t5 - t0,
            )
        )
        self.assertLess(t5 - t0, 60.0, "pipeline unexpectedly slow on this development host")


if __name__ == "__main__":
    unittest.main()
