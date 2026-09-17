# -*- coding: utf-8 -*-
"""R3-B2C production-intent migration adapter (NOT a qualification
fixture -- unlike projections.py, which is explicitly fixture-only).

Reshapes a qualified broker acquisition into the EXACT return-dict
contract that `parse_targeted_master()` currently provides at its single
real call site (Rebuild_Control_Groups_Normalizer.py, line ~13195):

    {
        "mapping_count": int,        # GLOBAL occurrence count
        "destination_count": int,    # GLOBAL distinct-destination count
        "folded": {folded_literal: [{"literal", "destination",
                                      "global_index", "local_index"}, ...]},
        "exact_literals": set(...),
        "group_sibling_order": {parent_full_path_or_"<ROOT>": [child_name, ...]},
        "group_metadata": {full_path: {"path", "groupColor_raw",
                                        "selectable_raw", "visible_raw",
                                        "snappable_raw", "group_color_explicit",
                                        "selectable_explicit",
                                        "selectable_authority"}},
    }

so the Normalizer's existing call site can be replaced with a call into
the qualified shared authority without changing anything downstream of
it (GATE/TARGET phase logic, group reorder, groupColor/selectable
mutation, etc. -- all read this SAME dict shape unchanged).

Field-for-field provenance, verified against parse_targeted_master's
real, unmodified source (Rebuild_Control_Groups_Normalizer.py lines
1416-1723, read directly 2026-09-16):
  mapping_count       <- provider.occurrence_count()      (GLOBAL, bounded,
                          one row per "control" occurrence in the whole
                          Master, matching total_mapping_count's own
                          "increment on every control line seen" semantics)
  destination_count   <- provider.destination_count()     (GLOBAL, bounded)
  folded              <- provider.lookup_fold(fold.encode("utf-8")) per
                          wanted fold; Hit/FoldConflict occurrences() give
                          {"literal","full_path","local_rank","global_rank"},
                          renamed here to {"literal","destination",
                          "local_index","global_index"} -- same fields,
                          same values, matching names only.
  exact_literals      <- the literal spellings actually found for the
                          wanted folds (mirrors the hand-rolled parser's
                          own exact_literals.add(literal) on each in-scope
                          "control" line)
  group_sibling_order <- provider.iter_groups(), each parent's children
                          sorted by declare_order, with the sidecar's
                          synthetic "groupFile" wrapper group stripped
                          (see WRAPPER STRIPPING below)
  group_metadata      <- provider.iter_metadata(path_id) reduced through
                          the SAME field_map + duplicate-per-key rejection
                          + parse_master_rgba_text/parse_master_bool_text
                          semantics, reproduced byte-for-byte below from
                          the verified source (see note below on why this
                          is a reproduction rather than a direct import).

Why a reproduction of parse_master_rgba_text/parse_master_bool_text
rather than importing them from the production module: importing
Rebuild_Control_Groups_Normalizer.py directly triggers real module-scope
side effects (ifm.dll native discovery, SFM-specific globals) outside
real SFM, so it cannot safely be imported from an offline script or from
this package. The two functions reproduced below (_parse_master_rgba_
text/_parse_master_bool_text) are transcribed verbatim from the read
source at lines 1340-1413, with only `unicode`/`str` handled via a
2/3-compatible _to_text() helper in place of the original's Python-2-only
`to_unicode()` (which relies on the `unicode` builtin) -- logic
unchanged, not reimplemented from scratch.

WRAPPER STRIPPING (found and fixed by real-Python-2.7.5 empirical
verification, not caught by offline structural self-consistency checks
alone): the sidecar compiler represents the file's outer
`groupFile { ... }` block as a REAL synthetic root-level group row
(path_id 0, declare_order 0, the single group whose parent_path is
None, no metadata of its own) -- parse_targeted_master's hand-rolled
tokenizer instead treats "groupFile" as pure syntax consumed before its
own token loop starts, using the sentinel string u"<ROOT>" for what that
wrapper's direct children's parent is, and every other provider
full_path is prefixed with "groupFile/" where the reference has no such
prefix. The `_strip()` helper below removes exactly that prefix from
every group full_path, group_sibling_order parent key, and occurrence
destination/full_path, and the wrapper group itself is excluded entirely
from group_metadata/group_sibling_order (matching parse_targeted_
master's own silent-discard of any top-level scalar metadata, verified
empirically to be moot for the real Master -- the wrapper group carries
zero metadata rows there).

EMPIRICALLY VERIFIED (real Python 2.7.5, tests/sidecar/qualification/
verify_py27_equivalence.py, 2026-09-16): parse_targeted_master() was
extracted VERBATIM (exact line ranges, never retyped) from the real,
hash-pinned production Normalizer and run against the REAL canonical
Master with every one of its 124,728 distinct folds requested (128,555
total occurrences, 42 groups/destinations); this adapter's builder was
run directly against the SAME real Master + real official artifact with
the same full fold set. mapping_count, destination_count, folded,
exact_literals, group_sibling_order, and group_metadata all produced
BYTE-IDENTICAL canonical JSON hashes (order-preserving -- list/occurrence
ordering included, not merely set/count equality), and the COMBINED
structure hash matched exactly
(3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2) on
both sides. This is a real, both-sides-real-Python-2.7.5, full-corpus
proof -- not an architectural assumption.
"""
import re

from . import errors
from . import resource_estimator
from . import views

_METADATA_FIELD_MAP = {
    "groupColor": "groupColor_raw",
    "selectable": "selectable_raw",
    "visible": "visible_raw",
    "snappable": "snappable_raw",
}

_BOOL_TRUE = (u"1", u"true", u"yes")
_BOOL_FALSE = (u"0", u"false", u"no")

try:
    _TEXT_TYPES = (str, unicode)  # noqa: F821 -- Python 2.7 only
except NameError:
    _TEXT_TYPES = (str,)


class AdapterCorrupt(Exception):
    """Raised when the qualified authority's own decoded data violates an
    invariant parse_targeted_master enforced (e.g. more than one
    groupColor line in one group, or an unparsable bool/RGBA value) --
    the SAME class of failure the hand-rolled parser's ProbeError would
    signal, so callers observe an equivalent failure mode, never a silent
    divergence. Deliberately NOT errors.SidecarCorrupt/ResourceAdmission
    Refusal -- this is a semantic-content problem in an already-validated
    artifact, not a structural/resource one."""
    pass


def _to_text(value):
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except Exception:
            return value.decode("latin-1")
    return value


def _parse_master_bool_text(value, label):
    """Transcribed verbatim (semantics unchanged) from
    Rebuild_Control_Groups_Normalizer.py parse_master_bool_text,
    lines 1340-1370."""
    if value is None:
        return None
    folded = _to_text(value).strip().lower()
    if folded in _BOOL_TRUE:
        return True
    if folded in _BOOL_FALSE:
        return False
    raise AdapterCorrupt("Cannot parse Master boolean %s=%r." % (label, value))


def _parse_master_rgba_text(value, label):
    """Transcribed verbatim (semantics unchanged) from
    Rebuild_Control_Groups_Normalizer.py parse_master_rgba_text,
    lines 1373-1413."""
    if value is None:
        return None
    nums = re.findall(r"-?\d+", _to_text(value))
    if len(nums) != 4:
        raise AdapterCorrupt("Cannot parse Master RGBA %s=%r." % (label, value))
    rgba = [int(x) for x in nums]
    for component in rgba:
        if component < 0 or component > 255:
            raise AdapterCorrupt("Out-of-range Master RGBA %s=%r." % (label, value))
    return rgba


def _ascii_fold_to_bytes(literal):
    raw = literal.encode("utf-8") if isinstance(literal, _TEXT_TYPES) else literal
    return bytes(bytearray((c + 0x20) if 0x41 <= c <= 0x5A else c for c in bytearray(raw)))


def build_targeted_master_compatible_projection(wanted_folds):
    """Builder for Broker.acquire_cohort/acquire_or_reuse_views:
    callable(provider) -> (payload, coverage, estimated_bytes).
    `wanted_folds` is an iterable of already-ASCII-folded literal strings
    (str/unicode) -- the SAME frozenset_of_folded_keys shape every other
    consumer_kind in this package's builder_fns dict expects. `payload`
    IS the parse_targeted_master()-compatible dict described in this
    module's docstring -- an existing caller reading only that dict shape
    needs no further translation.

    Astra F2 correction: the returned callable carries an explicit
    `.declared_request_scale` attribute (== len(wanted_folds)) so
    Cohort/Broker can compute an AGGREGATE requested-vocabulary size
    across every builder_fn in a batch, BEFORE opening the provider, and
    forward it to the preflight/admission layer -- the pre-correction
    adapter gave callers no way to learn the request's own scale at all.
    Independently, `_builder` itself enforces
    resource_estimator.MAX_SINGLE_FOLD_OCCURRENCE_ROWS as a hard runtime
    backstop: materialization aborts (ResourceAdmissionRefusal) the
    moment any ONE requested fold's REAL, observed occurrence count
    exceeds that cap -- the single-pathological-family case no
    structural, pre-open estimate can predict."""
    wanted_folds = list(wanted_folds)

    def _builder(provider):
        groups = list(provider.iter_groups())

        # R3-B2C-A evidence-gap #1 finding (real-Python-2.7.5 hash
        # comparison against the real, unmodified parse_targeted_master):
        # the sidecar compiler represents the file's outer
        # `groupFile { ... }` block as a REAL synthetic root-level group
        # row (declare_order=0, one single root, no metadata of its own)
        # -- the hand-rolled parser instead treats "groupFile" as pure
        # syntax consumed before its own token loop even starts, and
        # uses the sentinel string u"<ROOT>" for what that wrapper's
        # direct children's parent is. Every other provider full_path is
        # therefore prefixed with "groupFile/" where the reference has
        # no such prefix at all. Strip it here so full_path values (both
        # for groups and for occurrence destinations) exactly match the
        # reference's un-prefixed paths.
        root_groups = [g for g in groups if g["parent_path"] is None]
        if len(root_groups) != 1 or root_groups[0]["name"] != u"groupFile":
            raise AdapterCorrupt(
                "Expected exactly one root-level group named 'groupFile' "
                "(the sidecar's synthetic wrapper for the file's outer "
                "groupFile{...} block); found %r." % (root_groups,)
            )
        wrapper = root_groups[0]
        wrapper_metadata = list(provider.iter_metadata(wrapper["path_id"]))
        if wrapper_metadata:
            # Matches parse_targeted_master's own behavior for scalar
            # metadata declared directly at file top-level (current_path
            # == "" there): silently discarded, never attached to
            # anything, never an error -- see module docstring.
            pass
        wrapper_prefix = wrapper["full_path"] + u"/"

        def _strip(full_path):
            if full_path == wrapper["full_path"]:
                return u""
            if full_path.startswith(wrapper_prefix):
                return full_path[len(wrapper_prefix):]
            return full_path  # defensive; should be unreachable for a single-root tree

        real_groups = [g for g in groups if g["path_id"] != wrapper["path_id"]]

        group_sibling_order = {u"<ROOT>": []}
        group_metadata = {}
        for g in real_groups:
            full_path = _strip(g["full_path"])
            parent_raw = g["parent_path"]
            parent = u"<ROOT>" if parent_raw == wrapper["full_path"] else _strip(parent_raw)
            group_sibling_order.setdefault(parent, [])
            group_sibling_order.setdefault(full_path, [])
            group_metadata[full_path] = {
                "path": full_path,
                "groupColor_raw": [],
                "selectable_raw": [],
                "visible_raw": [],
                "snappable_raw": [],
            }

        # Per-parent child order: declare_order is 0-based/contiguous,
        # assigned by a single first-seen file traversal (writer.py
        # invariant); sorting each parent's children by declare_order
        # reproduces that same first-seen order. Empirically confirmed
        # identical to parse_targeted_master's own first-seen order for
        # the real canonical Master (see verify_py27_equivalence.py,
        # real Python 2.7.5, exact hash match after the wrapper-stripping
        # fix above).
        for g in sorted(real_groups, key=lambda row: row["declare_order"]):
            full_path = _strip(g["full_path"])
            parent_raw = g["parent_path"]
            parent = u"<ROOT>" if parent_raw == wrapper["full_path"] else _strip(parent_raw)
            group_sibling_order[parent].append(g["name"])

        for g in real_groups:
            meta = group_metadata[_strip(g["full_path"])]
            for row in provider.iter_metadata(g["path_id"]):
                target_field = _METADATA_FIELD_MAP.get(row["key"])
                if target_field is not None:
                    meta[target_field].append(row["value"])

        for full_path, meta in group_metadata.items():
            for raw_key in ("groupColor_raw", "selectable_raw", "visible_raw", "snappable_raw"):
                if len(meta[raw_key]) > 1:
                    raise AdapterCorrupt(
                        "Master group %r has duplicate %s metadata: %r."
                        % (full_path, raw_key, meta[raw_key])
                    )
            color_raw = meta["groupColor_raw"][0] if meta["groupColor_raw"] else None
            selectable_raw = meta["selectable_raw"][0] if meta["selectable_raw"] else None
            meta["group_color_explicit"] = (
                None if color_raw is None
                else _parse_master_rgba_text(color_raw, full_path + u".groupColor")
            )
            meta["selectable_explicit"] = (
                None if selectable_raw is None
                else _parse_master_bool_text(selectable_raw, full_path + u".selectable")
            )
            meta["selectable_authority"] = (
                "CANONICAL_NATIVE_POST_DEFAULT" if selectable_raw is None
                else "EXPLICIT_MASTER_FIELD"
            )

        mapping_count = provider.occurrence_count()
        destination_count = provider.destination_count()

        folded_out = {}
        exact_literals = set()
        coverage_entries = {}
        for folded in wanted_folds:
            query = folded.encode("utf-8") if isinstance(folded, _TEXT_TYPES) else folded
            hit = provider.lookup_fold(query)
            type_name = type(hit).__name__
            if type_name == "MasterUnknown":
                coverage_entries[folded] = views.CoverageResult(views.MASTER_UNKNOWN, None, None)
                continue
            if type_name == "Hit":
                occs = hit.occurrences()
                destination = _strip(hit.destination)
            else:  # FoldConflict -- still a real, covered result
                occs = hit.occurrences()
                destination = sorted(_strip(d) for d in hit.destinations)
            # Astra F2 hard runtime backstop: a single requested fold's
            # REAL, observed occurrence family must never exceed the
            # explicit cap, regardless of what any pre-open estimate
            # predicted. Aborts materialization immediately -- never
            # finishes building an oversized single-family payload first.
            if len(occs) > resource_estimator.MAX_SINGLE_FOLD_OCCURRENCE_ROWS:
                raise errors.ResourceAdmissionRefusal(
                    "requested fold %r resolved to %d occurrences, exceeding the hard single-family "
                    "cap of %d -- refusing before materializing this family"
                    % (folded, len(occs), resource_estimator.MAX_SINGLE_FOLD_OCCURRENCE_ROWS)
                )
            coverage_entries[folded] = views.CoverageResult(views.KNOWN, destination, occs)
            rows = []
            for occ in occs:
                literal = occ["literal"]
                exact_literals.add(literal)
                rows.append({
                    "literal": literal,
                    "destination": _strip(occ["full_path"]),
                    "global_index": occ["global_rank"],
                    "local_index": occ["local_rank"],
                })
            folded_out[folded] = rows

        payload = {
            "mapping_count": mapping_count,
            "destination_count": destination_count,
            "folded": folded_out,
            "exact_literals": exact_literals,
            "group_sibling_order": group_sibling_order,
            "group_metadata": group_metadata,
        }
        coverage = views.CoverageDescriptor(coverage_entries)
        estimated_bytes = _estimate_payload_bytes(payload)
        return payload, coverage, estimated_bytes
    _builder.declared_request_scale = len(wanted_folds)
    # Astra second-correction-gate F2: the REAL requested fold SET (not
    # merely its size) -- broker.py's acquire_cohort reads this to build
    # requested_folds_by_consumer for the packed-per-family cumulative
    # admission check (resource_estimator.evaluate_cumulative_admission),
    # which needs the actual folds to look up their real packed
    # occurrence counts, not just a count to multiply an average by.
    _builder.declared_request_folds = frozenset(wanted_folds)
    return _builder


def _estimate_payload_bytes(payload):
    """Conservative LOGICAL byte estimate, same convention as
    projections._estimate_payload_bytes -- explicitly NOT
    sys.getsizeof() and NOT a claim of real native/VAS memory."""
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
