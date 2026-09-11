"""Phase B2D: shared, cached, ONE-EXACT-SNAPSHOT fixture for the full
official-Master qualification test files.

Not a test file itself (no `test_*` name, no `Test*`/`unittest.TestCase`
class) -- pytest never collects it. Every `test_official_master_*.py` file
imports from here so the (relatively expensive: ~1s core parse, ~1.5s
independent oracle scan, ~2s compile, ~0.8s reader open/validate) pipeline
runs exactly once per test session, per final spec Part 26's "avoid
unnecessary repeated complete parses where immutable shared setup can be
reused safely" instruction -- while still keeping `sfm_master_core` and
`oracle.py` genuinely independent of each other (both are called directly
against the SAME captured source bytes; neither is ever fed the other's
output).

Phase B2D Part 1's "one exact source snapshot" requirement: `load_source_bytes()`
reads the file exactly once (via `functools.lru_cache`) and asserts its
SHA-256 against the expected value before anything else in this module ever
runs; every other cached function in this module derives from that same
captured `bytes` object, never re-reading the file.
"""

import hashlib
import sys
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(HERE))

import sfm_master_core as core  # noqa: E402
import oracle as oracle_module  # noqa: E402
from sfm_master_sidecar import reader, writer  # noqa: E402

MASTER_PATH = REPO_ROOT / "sfm_defaultanimationgroups.txt"
EXPECTED_SOURCE_SHA256 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"

EXPECTED_GROUP_COUNT = 43
EXPECTED_PARENTLESS_COUNT = 1
EXPECTED_CHILD_INDEX_ROW_COUNT = 42
EXPECTED_OCCURRENCE_COUNT = 128555
EXPECTED_FOLD_COUNT = 124728
EXPECTED_METADATA_COUNT = 54
EXPECTED_EXACT_DUPLICATES = 0
EXPECTED_ASCII_CONFLICTS = 0


@lru_cache(maxsize=1)
def load_source_bytes():
    """The ONE exact source snapshot every other cached function in this
    module derives from -- read exactly once, SHA verified immediately."""
    data = MASTER_PATH.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != EXPECTED_SOURCE_SHA256:
        raise AssertionError(
            "official Master SHA-256 does not match the expected qualification baseline: "
            "expected %s, got %s -- refusing to proceed with a changed source" % (
                EXPECTED_SOURCE_SHA256, actual,
            )
        )
    return data


def source_byte_length():
    return len(load_source_bytes())


@lru_cache(maxsize=1)
def core_parse_result():
    """Production source-semantic authority (final spec Part 2.A)."""
    return core.parse_master_bytes(load_source_bytes(), source_name=str(MASTER_PATH))


@lru_cache(maxsize=1)
def oracle_scan_result():
    """Independent source-completeness authority (final spec Part 2.B) --
    scans the SAME captured bytes directly; never receives core's output."""
    return oracle_module.scan_bytes(load_source_bytes())


@lru_cache(maxsize=1)
def fold_families():
    return core.build_fold_families(core_parse_result().occurrences)


@lru_cache(maxsize=1)
def compiled_artifact_bytes():
    """The real production writer, the same path used for every B2B/B2C
    fixture -- no full-Master-specific writer, no shortcut serializer."""
    return writer.compile_sidecar(load_source_bytes(), core_parse_result())


def open_shared_reader():
    """A fresh `SidecarReader` handle for read-only inspection/lookup tests.
    Deliberately NOT cached/shared as a single long-lived instance: several
    test files legitimately want their own handle (e.g. lifetime-regression
    tests call `close()`, which must never affect any other test's handle).
    The underlying `compiled_artifact_bytes()` IS cached, so only the
    open+validate cost (~0.8s) is repeated per fresh handle, not the parse
    or compile cost."""
    return reader.SidecarReader.open_generation(compiled_artifact_bytes(), core_parse_result().source_sha256)
