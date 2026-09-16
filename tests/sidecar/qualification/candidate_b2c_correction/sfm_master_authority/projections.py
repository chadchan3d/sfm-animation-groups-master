# -*- coding: utf-8 -*-
"""B2B projection-builder QUALIFICATION FIXTURES ONLY.

NOT wired to any production consumer. Uses the FINAL R3-A2B provider's
real query methods (`lookup_fold`, `iter_groups`, `iter_metadata`,
`wrapper_path`) against whatever provider a Cohort opens, and NEVER
retains the provider itself -- `Hit`/`FoldConflict`/`MasterUnknown`
results are already-materialized/detached by the provider's own
contract ("safe to read after the provider... is later invalidated or
closed" -- reader.py's own docstring), so storing their fields into a
plain dict payload is genuinely safe past provider close.
"""
try:
    _TEXT_TYPES = (str, unicode)  # noqa: F821 -- Python 2.7 only
except NameError:
    _TEXT_TYPES = (str,)

from . import views


def build_normalizer_like_projection(exact_literals):
    """Representative of the Normalizer's real needs: complete
    hierarchy/metadata fidelity + specific requested exact/fold lookups +
    an explicit coverage descriptor."""
    def _builder(provider):
        groups = list(provider.iter_groups())
        metadata_by_path = {}
        for g in groups:
            metadata_by_path[g["path_id"]] = list(provider.iter_metadata(g["path_id"]))

        coverage_entries = {}
        results = {}
        for literal in exact_literals:
            folded = _ascii_fold(literal)
            hit = provider.lookup_fold(folded)
            status, destination, occs = _classify_hit(hit)
            coverage_entries[folded] = views.CoverageResult(status, destination, occs)
            results[literal] = (status, destination)

        payload = {
            "groups": groups,
            "metadata_by_path": metadata_by_path,
            "lookup_results": results,
            "wrapper_path": provider.wrapper_path(),
        }
        coverage = views.CoverageDescriptor(coverage_entries)
        return payload, coverage, _estimate_payload_bytes(payload)
    return _builder


def build_character_preset_like_projection(vocabulary_literals):
    """Representative of Character Preset's narrower need: only the
    specific semantic vocabulary it actually queries -- never full
    hierarchy/metadata."""
    def _builder(provider):
        coverage_entries = {}
        results = {}
        for literal in vocabulary_literals:
            folded = _ascii_fold(literal)
            hit = provider.lookup_fold(folded)
            status, destination, occs = _classify_hit(hit)
            coverage_entries[folded] = views.CoverageResult(status, destination, occs)
            results[literal] = (status, destination)

        payload = {"lookup_results": results}
        coverage = views.CoverageDescriptor(coverage_entries)
        return payload, coverage, _estimate_payload_bytes(payload)
    return _builder


def _ascii_fold(literal):
    raw = literal.encode("utf-8") if isinstance(literal, _TEXT_TYPES) else literal
    return bytes(bytearray((c + 0x20) if 0x41 <= c <= 0x5A else c for c in bytearray(raw)))


def _classify_hit(hit):
    type_name = type(hit).__name__
    if type_name == "MasterUnknown":
        return views.MASTER_UNKNOWN, None, None
    if type_name == "Hit":
        return views.KNOWN, hit.destination, hit.occurrences()
    if type_name == "FoldConflict":
        # Still a real, covered result -- just ambiguous across
        # destinations. Never UNCOVERED, never silently treated as
        # MasterUnknown.
        return views.KNOWN, sorted(hit.destinations), hit.occurrences()
    return views.UNCOVERED, None, None


def _estimate_payload_bytes(payload):
    """Conservative LOGICAL byte estimate -- explicitly NOT
    `sys.getsizeof()` (which undercounts real CPython object overhead)
    and NOT a claim of real native/VAS memory. See
    memory_accounting.AggregateLedger.RUNTIME_QUALIFICATION_NOTE."""
    return 128 + _walk_estimate(payload)


def _walk_estimate(obj):
    if isinstance(obj, dict):
        total = 0
        for k, v in obj.items():
            total += _walk_estimate(k) + _walk_estimate(v) + 64
        return total
    if isinstance(obj, (list, tuple, set, frozenset)):
        total = 0
        for item in obj:
            total += _walk_estimate(item) + 16
        return total
    if isinstance(obj, bytes):
        return len(obj) + 32
    if isinstance(obj, _TEXT_TYPES):
        return len(obj.encode("utf-8")) + 32
    if obj is None or isinstance(obj, (int, float, bool)):
        return 16
    return 64
