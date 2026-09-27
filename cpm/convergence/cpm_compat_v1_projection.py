# -*- coding: utf-8 -*-
"""CPM-owned ``cpm_compat_v1`` fold-family projection and exact-answer
interpreter (CPM convergence Step 1).

Seam, per docs/qualification/CPM_CONVERGENCE_INTEGRATION_HANDOFF.md
sections 6-9 and 11 (the archived Astra review governs where they differ):

    canonical broker
        -> cpm_compat_v1 builder (this module, CPM-owned)
        -> fold-family facts (the cached payload)
        -> exact-literal interpreter (this module, CPM-owned)
        -> existing CPM semantic model

The broker caches views by (Master SHA, projection contract version,
covered folded-key set, consumer kind). Exact request spelling is not part
of that identity, so the cached payload holds only facts that are invariant
for a whole fold family. The exact literal is applied afterwards, by
``interpret_exact_answer``.

This module never modifies the shared authority package. It imports the
canonical package's ``views``, ``errors`` and ``resource_estimator`` modules
read-only, and only inside the functions that need them, so the pure
interpreter and identity functions import without the package on sys.path.

Runtime: Python 2.7.5 (embedded SFM) and Python 3.
"""

try:
    _TEXT = unicode  # noqa: F821 -- Python 2
    _BYTES = str
except NameError:  # Python 3
    _TEXT = str
    _BYTES = bytes


CONSUMER_KIND = "cpm_compat_v1"
PAYLOAD_CONTRACT = u"cpm-compat-v1"
COMPATIBILITY_IDENTITY_SCHEMA = u"cpm-compat-identity-v1"

# Same values as the frozen G18AN baseline's SEMANTIC_STATUS_* /
# SEMANTIC_MATCH_* constants, so reconstructed answers compare equal.
STATUS_RESOLVED = u"resolved"
STATUS_CONFLICT = u"conflict"
STATUS_ABSENT = u"absent"

MATCH_EXACT = u"exact"
MATCH_FOLDED = u"ascii-fold"
MATCH_NONE = u"none"

# Provenance fields consumed by G18AN's prod_provider_capture().
CPM_PROVIDER_CONTRACT = u"sfm-character-semantic-provider-v1"
CPM_FOLD_POLICY = u"ascii-a-z-v1"
# G18AN compares an integer provider_generation. Under the shared broker it
# must stay stable across reopenings of the same semantic generation, so it
# is a fixed value; generation changes are carried by source_sha256 and by
# compatibility_identity(), never by a broker cohort or provider-open count.
CPM_DESCRIPTOR_PROVIDER_GENERATION = 1

_FAMILY_KEYS = ("status", "resolved_path", "destinations", "spellings", "occurrence_count")
_ANSWER_KEYS = (
    "query_literal", "status", "match_kind", "resolved_path",
    "destinations", "spellings", "occurrence_count",
)

# Conservative logical overheads (bytes) for retained-size estimation. Same
# logical convention as the shared package's own estimators: explicitly not
# sys.getsizeof() and not a claim about native/VAS memory.
_ENVELOPE_BYTES = 128
_COVERAGE_ENTRY_OBJECT_BYTES = 96
_DETACHED_VIEW_OBJECT_BYTES = 512


class CpmProjectionError(Exception):
    """Fail-closed error: the projection, a request, or a view does not
    satisfy the cpm_compat_v1 contract. Never published as a healthy
    result."""


# ---------------------------------------------------------------------------
# Folding
# ---------------------------------------------------------------------------

def _to_text(value, what):
    if isinstance(value, _TEXT):
        return value
    if isinstance(value, _BYTES):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            raise CpmProjectionError("%s is not valid UTF-8: %r" % (what, value))
    raise CpmProjectionError("%s must be text, got %r" % (what, type(value).__name__))


def cpm_fold(literal):
    """Canonical ASCII A-Z fold. Returns text; non-ASCII characters and all
    whitespace are preserved exactly. Identical rule to G18AN
    ``p01_ascii_fold``."""
    text = _to_text(literal, "literal")
    out = []
    for ch in text:
        code = ord(ch)
        if 65 <= code <= 90:
            out.append(_chr(code + 32))
        else:
            out.append(ch)
    return u"".join(out)


try:
    _chr = unichr  # noqa: F821 -- Python 2
except NameError:
    _chr = chr


def fold_to_lookup_bytes(folded):
    """Provider lookup boundary: the only place a folded key becomes
    bytes."""
    return _to_text(folded, "folded key").encode("utf-8")


def request_folds_for_literals(literals):
    """Folded request vocabulary (frozenset of text) for exact literals."""
    return frozenset(cpm_fold(literal) for literal in literals)


def _normalize_request_folds(wanted_folds):
    folds = set()
    for value in wanted_folds:
        folded = _to_text(value, "requested fold")
        if cpm_fold(folded) != folded:
            raise CpmProjectionError(
                "requested fold %r is not ASCII-folded; request folds, coverage keys and "
                "payload keys must share one folded text representation" % (folded,)
            )
        folds.add(folded)
    return frozenset(folds)


# ---------------------------------------------------------------------------
# Wrapper/path normalization
# ---------------------------------------------------------------------------

def _strip_wrapper(wrapper, full_path):
    """Strict wrapper stripping, same contract as G18AN
    ``g18an_normalize_sidecar_path``: a path outside the wrapper fails
    closed."""
    value = _to_text(full_path or u"", "sidecar path")
    if value == wrapper:
        return u""
    prefix = wrapper + u"/"
    if not value.startswith(prefix):
        raise CpmProjectionError("sidecar path %r is outside wrapper %r" % (value, wrapper))
    return value[len(prefix):]


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def _family_from_occurrences(folded, occurrences, wrapper, max_rows):
    if not occurrences:
        raise CpmProjectionError("provider returned a covered result with no occurrences for %r" % (folded,))
    if len(occurrences) > max_rows[0]:
        raise max_rows[1](
            "requested fold %r resolved to %d occurrences, exceeding the single-family cap of %d"
            % (folded, len(occurrences), max_rows[0])
        )
    spellings = set()
    destinations = set()
    for row in occurrences:
        literal = _to_text(row.get("literal"), "occurrence literal")
        if cpm_fold(literal) != folded:
            raise CpmProjectionError(
                "occurrence literal %r does not belong to requested family %r" % (literal, folded)
            )
        spellings.add(literal)
        destinations.add(_strip_wrapper(wrapper, row.get("full_path")))
    destinations = sorted(destinations)
    if len(destinations) == 1:
        status = STATUS_RESOLVED
        resolved_path = destinations[0]
    else:
        status = STATUS_CONFLICT
        resolved_path = None
    return {
        "status": status,
        "resolved_path": resolved_path,
        "destinations": destinations,
        "spellings": sorted(spellings),
        "occurrence_count": len(occurrences),
    }


def _absent_family():
    return {
        "status": STATUS_ABSENT,
        "resolved_path": None,
        "destinations": [],
        "spellings": [],
        "occurrence_count": 0,
    }


def build_cpm_compat_v1_projection(wanted_folds):
    """Builder factory for ``Broker.acquire_or_reuse_views``:
    ``callable(provider) -> (payload, coverage, estimated_bytes)``.

    ``wanted_folds`` must already be ASCII-folded text (bytes are decoded
    as strict UTF-8). The returned callable always carries
    ``declared_request_folds`` and ``declared_request_scale``.
    """
    folds = _normalize_request_folds(wanted_folds)

    def _builder(provider):
        from sfm_master_authority_productionized import errors, resource_estimator, views

        max_rows = (resource_estimator.MAX_SINGLE_FOLD_OCCURRENCE_ROWS, errors.ResourceAdmissionRefusal)
        wrapper = _to_text(provider.wrapper_path(), "wrapper path")
        if not wrapper:
            raise CpmProjectionError("provider reported an empty wrapper path")

        families = {}
        entries = {}
        for folded in sorted(folds):
            result = provider.lookup_fold(fold_to_lookup_bytes(folded))
            kind = type(result).__name__
            if kind == "MasterUnknown":
                families[folded] = _absent_family()
                entries[folded] = views.CoverageResult(views.MASTER_UNKNOWN, None, None)
                continue
            if kind == "Hit":
                reported = set([_strip_wrapper(wrapper, result.destination)])
            elif kind == "FoldConflict":
                reported = set(_strip_wrapper(wrapper, d) for d in result.destinations)
            else:
                raise CpmProjectionError("unsupported provider result type %r for %r" % (kind, folded))
            family = _family_from_occurrences(folded, result.occurrences(), wrapper, max_rows)
            if set(family["destinations"]) != reported:
                raise CpmProjectionError(
                    "%s for %r reports destinations %r but its occurrences span %r"
                    % (kind, folded, sorted(reported), family["destinations"])
                )
            if (kind == "Hit") != (family["status"] == STATUS_RESOLVED):
                raise CpmProjectionError("%s for %r is inconsistent with its destination count" % (kind, folded))
            families[folded] = family
            # Compact coverage: destinations only, never a copy of the
            # provider's occurrence rows.
            entries[folded] = views.CoverageResult(views.KNOWN, tuple(family["destinations"]), None)

        if frozenset(families) != folds or frozenset(entries) != folds:
            raise CpmProjectionError("projection omitted requested folds")
        payload = {"contract": PAYLOAD_CONTRACT, "families_by_fold": families}
        coverage = views.CoverageDescriptor(entries)
        if coverage.covered_keys() != folds:
            raise CpmProjectionError("coverage keys do not equal the requested folds")
        return payload, coverage, estimate_retained_bytes(payload, coverage)

    _builder.declared_request_folds = folds
    _builder.declared_request_scale = len(folds)
    _builder.consumer_kind = CONSUMER_KIND
    return _builder


def validate_builder_contract(builder_fn, requested_folds):
    """CPM-side check; the broker silently defaults a missing
    ``declared_request_folds`` to an empty set and never reads
    ``declared_request_scale``, so these are rejected here."""
    requested = _normalize_request_folds(requested_folds)
    if not hasattr(builder_fn, "declared_request_folds"):
        raise CpmProjectionError("builder is missing declared_request_folds")
    if not hasattr(builder_fn, "declared_request_scale"):
        raise CpmProjectionError("builder is missing declared_request_scale")
    declared = frozenset(builder_fn.declared_request_folds)
    if declared != requested:
        raise CpmProjectionError(
            "builder declares %d folds that disagree with the %d requested"
            % (len(declared), len(requested))
        )
    if builder_fn.declared_request_scale != len(requested):
        raise CpmProjectionError(
            "builder declares scale %r for %d requested folds"
            % (builder_fn.declared_request_scale, len(requested))
        )


def make_request_specs(requested_folds, consumer_kind=CONSUMER_KIND):
    """``request_specs`` mapping for ``Broker.acquire_or_reuse_views``,
    with the builder contract already validated."""
    folds = _normalize_request_folds(requested_folds)
    builder = build_cpm_compat_v1_projection(folds)
    validate_builder_contract(builder, folds)
    return {consumer_kind: (folds, builder)}


# ---------------------------------------------------------------------------
# Post-acquisition validation
# ---------------------------------------------------------------------------

def validate_view(view, requested_folds, consumer_kind=CONSUMER_KIND):
    """Strict coverage validation of an acquired or reused view before any
    CPM use. Every requested fold must be covered (Known or
    MasterUnknown); payload families must agree with coverage."""
    from sfm_master_authority_productionized import views

    requested = _normalize_request_folds(requested_folds)
    if getattr(view, "consumer_kind", None) != consumer_kind:
        raise CpmProjectionError("view consumer kind %r is not %r" % (getattr(view, "consumer_kind", None), consumer_kind))
    payload = getattr(view, "payload", None)
    if not isinstance(payload, dict) or payload.get("contract") != PAYLOAD_CONTRACT:
        raise CpmProjectionError("view payload is not a %s payload" % (PAYLOAD_CONTRACT,))
    families = payload.get("families_by_fold")
    if not isinstance(families, dict):
        raise CpmProjectionError("view payload has no families_by_fold mapping")
    covered = view.coverage.covered_keys()
    if frozenset(families) != covered:
        raise CpmProjectionError("payload families and coverage keys disagree")
    missing = requested - covered
    if missing:
        raise CpmProjectionError("view does not cover %d requested folds" % (len(missing),))
    for folded in requested:
        entry = view.coverage.lookup(folded)
        family = families[folded]
        if entry.status == views.MASTER_UNKNOWN:
            ok = family.get("status") == STATUS_ABSENT
        elif entry.status == views.KNOWN:
            ok = (family.get("status") in (STATUS_RESOLVED, STATUS_CONFLICT)
                  and list(entry.destination or ()) == family.get("destinations"))
        else:
            ok = False
        if not ok:
            raise CpmProjectionError("coverage and family disagree for %r" % (folded,))


# ---------------------------------------------------------------------------
# Exact-answer interpreter
# ---------------------------------------------------------------------------

def interpret_exact_answer(literal, payload):
    """Reconstruct the G18AN-compatible exact answer for one current exact
    live literal from fold-family facts. An uncovered fold raises; it is
    never treated as absent."""
    literal = _to_text(literal, "literal")
    if not isinstance(payload, dict) or payload.get("contract") != PAYLOAD_CONTRACT:
        raise CpmProjectionError("not a %s payload" % (PAYLOAD_CONTRACT,))
    family = payload["families_by_fold"].get(cpm_fold(literal))
    if family is None:
        raise CpmProjectionError("literal %r is not covered by this projection" % (literal,))
    status = family["status"]
    spellings = list(family["spellings"])
    if status == STATUS_ABSENT:
        match_kind = MATCH_NONE
    elif literal in spellings:
        match_kind = MATCH_EXACT
    else:
        match_kind = MATCH_FOLDED
    return {
        "query_literal": literal,
        "status": status,
        "match_kind": match_kind,
        "resolved_path": family["resolved_path"],
        "destinations": list(family["destinations"]),
        "spellings": spellings,
        "occurrence_count": family["occurrence_count"],
    }


def interpret_exact_answers(literals, payload):
    return dict((_to_text(literal, "literal"), interpret_exact_answer(literal, payload)) for literal in literals)


# ---------------------------------------------------------------------------
# Compatibility identity and provenance (handoff section 11, review 6C)
# ---------------------------------------------------------------------------

def compatibility_identity(master_sha256, semantic_policy_revision, projection_identity=CONSUMER_KIND):
    """Pure CPM compatibility identity: Master SHA + projection identity +
    semantic policy revision. Broker cohort IDs, provider-open counters and
    artifact IDs are not inputs and cannot affect it."""
    sha = _to_text(master_sha256, "master_sha256").lower()
    if len(sha) != 64 or any(c not in u"0123456789abcdef" for c in sha):
        raise CpmProjectionError("master_sha256 must be a 64-character hex digest")
    policy = _to_text(semantic_policy_revision, "semantic_policy_revision")
    if not policy:
        raise CpmProjectionError("semantic_policy_revision must be non-empty")
    return (COMPATIBILITY_IDENTITY_SCHEMA, sha, _to_text(projection_identity, "projection identity"), policy)


def compatibility_identity_for_view(view, semantic_policy_revision):
    return compatibility_identity(view.semantic_generation.master_sha256, semantic_policy_revision, view.consumer_kind)


def provider_capture_descriptor(view):
    """Descriptor carrying the provenance fields G18AN's
    prod_provider_capture() reads. The cohort id is kept as a diagnostic
    only; it is not part of any compatibility comparison."""
    return {
        "provider_contract": CPM_PROVIDER_CONTRACT,
        "source_sha256": _to_text(view.semantic_generation.master_sha256, "master_sha256"),
        "fold_policy": CPM_FOLD_POLICY,
        "provider_generation": CPM_DESCRIPTOR_PROVIDER_GENERATION,
        "projection_contract": PAYLOAD_CONTRACT,
        "diagnostics": {"broker_cohort_id": getattr(view, "admission_id", None)},
    }


# ---------------------------------------------------------------------------
# Retained-size estimation
# ---------------------------------------------------------------------------

def _walk(obj):
    if isinstance(obj, dict):
        return sum(_walk(k) + _walk(v) + 64 for k, v in obj.items())
    if isinstance(obj, (list, tuple, set, frozenset)):
        return sum(_walk(item) + 16 for item in obj)
    if isinstance(obj, _BYTES):
        return len(obj) + 32
    if isinstance(obj, _TEXT):
        return len(obj.encode("utf-8")) + 32
    if obj is None or isinstance(obj, (bool, int, float)):
        return 16
    return 64


def estimate_retained_bytes(payload, coverage):
    """Conservative logical estimate of everything the CPM view retains:
    detached semantic payload + coverage storage + retained view envelope
    data. The broker charges its cache with this value as given."""
    total = _ENVELOPE_BYTES + _DETACHED_VIEW_OBJECT_BYTES + _walk(payload)
    for key in coverage.covered_keys():
        entry = coverage.lookup(key)
        total += _COVERAGE_ENTRY_OBJECT_BYTES + _walk(key) + _walk(entry.status)
        total += _walk(entry.destination) + _walk(entry.occurrences)
    return total
