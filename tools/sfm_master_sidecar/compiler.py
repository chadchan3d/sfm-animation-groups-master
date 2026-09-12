# -*- coding: utf-8 -*-
"""Single production compiler orchestration path. Python 3 only.

This is THE ONE path used by official builds, custom advanced-user builds,
the CLI, and every test in this project -- there is no separate
official/custom/maintainer compiler (Phase B2E Part 1). Official-only policy
(`tools/validate_master.py`) is layered ON TOP of this generic path via an
explicit opt-in flag; it is never inherited by default.

Pipeline (final spec Section 29 / Phase B2E Part 3):

    open explicit input TXT path -> read exact bytes once -> close handle
        -> hash those exact bytes -> parse those exact bytes
            -> sidecar-profile eligibility -> writer.compile_sidecar
                -> reader self-validation (from the bytes actually written
                   to disk, when publishing) -> semantic parity

The source pathname is never semantic identity; the exact source bytes are.
"""

import hashlib
import os
import sys

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import sfm_master_core as core  # noqa: E402

from . import format as fmt  # noqa: E402
from . import reader as reader_module  # noqa: E402
from . import writer  # noqa: E402


class CompilerError(Exception):
    """Base class for every exception this module raises."""


class SourceGrammarError(CompilerError):
    """`sfm_master_core.parse_master_bytes(...).ok` was False."""


class SelfValidationError(CompilerError):
    """The freshly-compiled artifact failed reader validation or semantic
    parity against its own source -- this must never happen for correctly
    compiled output; if it does, that is a genuine defect, not a normal
    rejection path."""


class OfficialPolicyRejectedError(CompilerError):
    """`tools/validate_master.py`'s official-release-only policy rejected
    a source that the generic compiler itself would have accepted. Only
    raised when the caller explicitly opts into official policy checking."""


class SourceSnapshot(object):
    """The one exact capture of source bytes a single compilation run is
    built from -- read once, hashed once, parsed once. Never re-read from
    the path after construction."""

    __slots__ = ("path", "bytes", "sha256_hex")

    def __init__(self, path, data):
        self.path = path
        self.bytes = data
        self.sha256_hex = hashlib.sha256(data).hexdigest()


def capture_source_snapshot(source_path):
    """Open `source_path`, read its exact bytes ONCE, close the handle, and
    hash those exact bytes. Never a second read of the same path."""
    with open(source_path, "rb") as f:
        data = f.read()
    return SourceSnapshot(source_path, data)


class CompileOutcome(object):
    """Result of parsing + compiling one source snapshot, before any
    self-validation or disk I/O for publication has happened."""

    __slots__ = ("snapshot", "result", "blob", "ordinary_sha256")

    def __init__(self, snapshot, result, blob):
        self.snapshot = snapshot
        self.result = result
        self.blob = blob
        self.ordinary_sha256 = hashlib.sha256(blob).hexdigest()


def parse_and_compile(snapshot, official_policy=False):
    """Generic acceptance: `sfm_master_core` parse success + sidecar
    compatibility-profile success (exactly one parentless wrapper). Does
    NOT reject merely for duplicate control occurrences or cross-destination
    fold conflicts -- those remain representable (final spec Section 30 /
    Phase B2E Part 4).

    `official_policy=True` additionally runs `tools/validate_master.py`'s
    stricter, official-release-only policy as one more gate layered on TOP
    of generic acceptance -- never inherited by default, never changing what
    the generic writer/profile check themselves accept."""
    result = core.parse_master_bytes(snapshot.bytes, source_name=str(snapshot.path))
    if not result.ok:
        errs = "; ".join("%s@%d" % (e.kind, e.line) for e in result.grammar_errors[:5])
        raise SourceGrammarError("source is not grammatically valid: %s" % (errs or "structural error"))

    if official_policy:
        _run_official_policy_gate(snapshot)

    # writer.compile_sidecar performs its own profile-eligibility gate
    # (SidecarProfileError) -- not duplicated here.
    blob = writer.compile_sidecar(snapshot.bytes, result)
    return CompileOutcome(snapshot, result, blob)


def _run_official_policy_gate(snapshot):
    """`tools/validate_master.py`'s `validate(path)` reads its own file from
    disk -- to honor Part 3's "never mix a read from one snapshot with a
    read from another" contract, this writes the EXACT captured snapshot
    bytes to a private temporary file and validates THAT, never re-reading
    the live source path (which could have changed since capture)."""
    _TOOLS_DIR_LOCAL = _TOOLS_DIR
    if _TOOLS_DIR_LOCAL not in sys.path:
        sys.path.insert(0, _TOOLS_DIR_LOCAL)
    import validate_master  # local import: official-only policy, never a generic dependency
    import tempfile

    fd, tmp_path = tempfile.mkstemp(suffix=".txt", prefix="b2e-official-policy-snapshot-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(snapshot.bytes)
        report = validate_master.validate(tmp_path)
    finally:
        os.remove(tmp_path)

    if report.get("fatal") or report.get("failures"):
        raise OfficialPolicyRejectedError(
            "tools/validate_master.py official policy rejected this source:\n%s" % validate_master.format_report(report)
        )


def verify_semantic_parity(result, r):
    """Exhaustive (never sampled), generically-sized comparison between a
    `sfm_master_core.MasterParseResult` and an opened `SidecarReader` --
    proves the compiled artifact represents the input generation correctly
    (Phase B2E Part 8). Raises `SelfValidationError` on the first
    discrepancy found. Used by every compile-then-publish AND every
    `--check-only` invocation; never a second, separate compiler-side binary
    reader is used here -- always the real production `reader.py`."""

    reader_groups = list(r.iter_groups())
    if len(reader_groups) != len(result.groups):
        raise SelfValidationError(
            "group count mismatch: core=%d reader=%d" % (len(result.groups), len(reader_groups))
        )
    reader_by_path = {g["full_path"]: g for g in reader_groups}
    if set(reader_by_path) != {g.full_path for g in result.groups}:
        raise SelfValidationError("group path set mismatch between core and reader")

    for g in result.groups:
        rg = reader_by_path[g.full_path]
        if rg["name"] != g.name:
            raise SelfValidationError("group name mismatch: %s" % g.full_path)
        if rg["declare_order"] != g.declare_order:
            raise SelfValidationError("group declare_order mismatch: %s" % g.full_path)
        if rg["sibling_rank"] != g.sibling_rank:
            raise SelfValidationError("group sibling_rank mismatch: %s" % g.full_path)
        if rg["parent_path"] != g.parent_path:
            raise SelfValidationError("group parent_path mismatch: %s" % g.full_path)

    for g in result.groups:
        gid = reader_by_path[g.full_path]["path_id"]
        r_meta = list(r.iter_metadata(gid))
        if len(r_meta) != len(g.metadata.entries):
            raise SelfValidationError("metadata count mismatch: %s" % g.full_path)
        for entry, rme in zip(g.metadata.entries, r_meta):
            if entry.key != rme["key"] or entry.value != rme["value"]:
                raise SelfValidationError("metadata entry mismatch: %s" % g.full_path)

    reader_occs = list(r.iter_occurrences())
    if len(reader_occs) != len(result.occurrences):
        raise SelfValidationError(
            "occurrence count mismatch: core=%d reader=%d" % (len(result.occurrences), len(reader_occs))
        )
    for co, ro in zip(result.occurrences, reader_occs):
        if co.literal != ro["literal"] or co.full_path != ro["full_path"] or co.local_rank != ro["local_rank"]:
            raise SelfValidationError("occurrence mismatch at global_rank=%d" % co.global_rank)

    fams = core.build_fold_families(result.occurrences)
    if len(fams) != r.fold_count():
        raise SelfValidationError("fold count mismatch: core=%d reader=%d" % (len(fams), r.fold_count()))

    for key, fam in fams.items():
        res = r.lookup_fold(key.encode("utf-8"))
        if fam.is_conflict:
            if not isinstance(res, reader_module.FoldConflict):
                raise SelfValidationError("expected FoldConflict for fold %r, got %r" % (key, res))
            if res.destinations != fam.destinations:
                raise SelfValidationError("fold destination-set mismatch for %r" % key)
        else:
            if not isinstance(res, reader_module.Hit):
                raise SelfValidationError("expected Hit for fold %r, got %r" % (key, res))
            if res.destination not in fam.destinations:
                raise SelfValidationError("fold destination mismatch for %r" % key)
        expected_ranks = set(fam.occurrence_global_ranks)
        actual_ranks = {o["global_rank"] for o in res.occurrences()}
        if expected_ranks != actual_ranks:
            raise SelfValidationError("fold evidence rank-set mismatch for %r" % key)


def self_validate_from_bytes(outcome):
    """Self-validation entry point for `--check-only` (no disk I/O): opens
    the compiled artifact directly from its in-memory bytes, via the real
    production reader, and runs the full semantic-parity check. Uses the
    explicit bytes entry point -- `outcome.blob` is never a filesystem
    path."""
    r = reader_module.SidecarReader.open_generation_bytes(outcome.blob, outcome.result.source_sha256)
    try:
        verify_semantic_parity(outcome.result, r)
    finally:
        r.close()


def self_validate_from_path(outcome, artifact_path):
    """Self-validation entry point for a real publication: opens the
    compiled artifact from the ACTUAL BYTES WRITTEN TO DISK (not the
    in-memory `blob`), proving what will be published is what was
    validated, not merely what was intended. Uses the explicit path entry
    point -- `artifact_path` is always opened as a file, never treated as
    raw bytes."""
    r = reader_module.SidecarReader.open_generation_path(str(artifact_path), outcome.result.source_sha256)
    try:
        verify_semantic_parity(outcome.result, r)
    finally:
        r.close()


def generation_basename(ordinary_sha256_hex, format_contract_version=None):
    if format_contract_version is None:
        format_contract_version = fmt.FORMAT_CONTRACT_VERSION_EXPERIMENTAL
    return "sfm_master_%d_%s.bin" % (format_contract_version, ordinary_sha256_hex)
