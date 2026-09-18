# -*- coding: utf-8 -*-
"""Detached-view envelope + coverage semantics -- ASTRA_CORRECTED.md
Sections 6/8, R3-B2B Sections 3-4.

Coverage semantics, never conflated:
  - Known: requested literal/fold family is covered and mapped to a
    destination (including a fold conflict -- still a real, covered
    result, just ambiguous across destinations).
  - MasterUnknown: requested vocabulary is covered by the view and
    validly absent from the Master -- a real, trustworthy negative (the
    fold table was searched and had no match), never a failure.
  - Uncovered: vocabulary was never requested/materialized into this
    view at all. The view has no opinion -- this is not a lookup result,
    it is the absence of one.
  - AuthorityUnavailable: no valid authority view exists at all. This is
    a property of an ACQUISITION ATTEMPT (see `errors.py`), never of an
    already-published view's coverage lookup.
"""
import itertools
import time

from . import errors

_lease_id_counter = itertools.count(1)

KNOWN = "Known"
MASTER_UNKNOWN = "MasterUnknown"
UNCOVERED = "Uncovered"


class CoverageResult(object):
    __slots__ = ("status", "destination", "occurrences")

    def __init__(self, status, destination=None, occurrences=None):
        self.status = status
        self.destination = destination
        self.occurrences = occurrences

    def __repr__(self):
        return "CoverageResult(status=%r, destination=%r)" % (self.status, self.destination)


class CoverageDescriptor(object):
    """A REAL (not schema-only) coverage descriptor: an immutable mapping
    from folded-key bytes to a CoverageResult, sufficient on its own to
    answer `lookup(key)` without ever reopening the provider. Any key
    absent from `_entries` is Uncovered -- explicitly distinct from a key
    that WAS looked up and mapped to MASTER_UNKNOWN."""
    __slots__ = ("_entries",)

    def __init__(self, entries):
        self._entries = dict(entries)  # folded_key_bytes -> CoverageResult

    def lookup(self, folded_key_bytes):
        result = self._entries.get(folded_key_bytes)
        if result is None:
            return CoverageResult(UNCOVERED)
        return result

    def covered_keys(self):
        return frozenset(self._entries.keys())

    def __len__(self):
        return len(self._entries)

    def __repr__(self):
        return "CoverageDescriptor(%d entries)" % (len(self._entries),)


class LiveAuthorizationToken(object):
    """Identity #4, kept EXPLICITLY distinct from a view's payload -- can
    be invalidated independently, without touching or freeing the
    payload's bytes (ASTRA_CORRECTED.md Section 6: 'a view payload may
    remain readable for logs/diagnosis after invalidation while its
    mutation permission is revoked'). One token may be shared by every
    view a single cohort published (they all represent one acquisition of
    one generation, so they go stale together)."""
    __slots__ = ("_valid", "generation_master_sha256", "issued_at")

    def __init__(self, generation_master_sha256):
        self._valid = True
        self.generation_master_sha256 = generation_master_sha256
        self.issued_at = time.time()

    def is_valid(self):
        return self._valid

    def invalidate(self):
        self._valid = False

    def require_valid(self, what="mutation"):
        if not self._valid:
            raise errors.ViewInvalidated(
                "authorization for %s was revoked (generation %s is no longer live)"
                % (what, self.generation_master_sha256)
            )


class ViewLease(object):
    """Astra F3 correction: explicit CONSUMER ownership, kept structurally
    distinct from CACHE ownership. A DetachedView is "leased" (not merely
    Boolean-`pinned`) by zero or more independent ViewLease tokens, one
    per real consumer/operation that is actively holding it -- never a
    single shared flag that cannot represent two simultaneous borrowers,
    or a same-key replacement racing an in-flight borrower. Deterministic
    release is the caller's responsibility (command completion,
    cancellation, failure, or dialog/operation close) -- never implicit
    garbage-collection-timing-dependent (`__del__` is deliberately NOT
    used for release; a leaked, never-released lease is a caller bug,
    surfaced by `ViewCache.outstanding_lease_count()` diagnostics, not
    silently masked by relying on GC to eventually reclaim it)."""
    __slots__ = ("lease_id", "view", "_released")

    def __init__(self, lease_id, view):
        self.lease_id = lease_id
        self.view = view
        self._released = False

    def is_released(self):
        return self._released

    def __repr__(self):
        return "ViewLease(lease_id=%r, released=%r)" % (self.lease_id, self._released)


class DetachedView(object):
    """The B2B detached-view envelope. Immutable payload by convention;
    a separate, independently-revocable authorization token. Never holds
    a provider reference, packed backing bytes, validation scratch, a
    file handle, or an acquisition-time traceback frame -- `payload` is
    always plain, already-decoded data assembled by a projection builder
    while the provider was open, never a live reference into it.

    Astra F3 correction: `pinned` (a single Boolean, unable to represent
    more than one simultaneous borrower) is REPLACED by `_active_leases`,
    a set of outstanding ViewLease ids. `has_live_leases()` is the
    eviction-safety predicate ViewCache now consults instead of the old
    `pinned` flag."""
    __slots__ = (
        "semantic_generation", "artifact_identity", "coverage",
        "projection_contract_version", "admission_id", "created_at",
        "consumer_kind", "payload", "authorization", "estimated_bytes",
        "_active_leases",
    )

    def __init__(self, semantic_generation, artifact_identity, coverage,
                 projection_contract_version, admission_id, consumer_kind,
                 payload, authorization, estimated_bytes):
        self.semantic_generation = semantic_generation
        self.artifact_identity = artifact_identity
        self.coverage = coverage
        self.projection_contract_version = projection_contract_version
        self.admission_id = admission_id
        self.created_at = time.time()
        self.consumer_kind = consumer_kind
        self.payload = payload
        self.authorization = authorization
        self.estimated_bytes = estimated_bytes
        self._active_leases = set()

    def acquire_lease(self):
        lease = ViewLease(next(_lease_id_counter), self)
        self._active_leases.add(lease.lease_id)
        return lease

    def release_lease(self, lease):
        if lease.is_released():
            return  # idempotent -- a caller releasing twice is not itself an error
        if lease.view is not self:
            raise errors.ViewInvalidated(
                "attempted to release a lease that was issued by a different view"
            )
        self._active_leases.discard(lease.lease_id)
        lease._released = True

    def has_live_leases(self):
        return len(self._active_leases) > 0

    def live_lease_count(self):
        return len(self._active_leases)

    # Backward-compatible read-only shim: existing code/tests that only
    # ever READ `.pinned` (never assign it) keep working unchanged.
    @property
    def pinned(self):
        return self.has_live_leases()

    def is_stale(self):
        return not self.authorization.is_valid()

    def cache_key(self):
        return (
            self.semantic_generation.master_sha256,
            self.projection_contract_version,
            self.coverage.covered_keys(),
            self.consumer_kind,
        )

    def __repr__(self):
        return "DetachedView(consumer=%r, master_sha256=%r, stale=%r)" % (
            self.consumer_kind, self.semantic_generation.master_sha256, self.is_stale(),
        )
