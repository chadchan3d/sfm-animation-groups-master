# -*- coding: utf-8 -*-
"""Explicit B2A result/exception categories.
ASTRA_CORRECTED.md Section 12 (via R3-B2A prompt Section 12).

`MasterUnknown` deliberately does NOT belong here -- there is no
consumer semantic lookup in B2A (no detached views are built)."""


class BrokerError(Exception):
    """Base class for every sfm_master_authority error."""


class MasterAbsent(BrokerError):
    pass


class MasterUnreadable(BrokerError):
    pass


class AmbiguousMasterPath(BrokerError):
    pass


class SidecarMissing(BrokerError):
    pass


class SourceGenerationMismatch(BrokerError):
    pass


class SidecarCorrupt(BrokerError):
    pass


class FormatUnsupported(BrokerError):
    pass


class AuthoritySemanticsUnsupported(BrokerError):
    pass


class ResourceAdmissionRefusal(BrokerError):
    pass


class AuthorityChangedDuringAcquisition(BrokerError):
    pass


class LocalPointerCorrupt(BrokerError):
    pass


class LocalGenerationMissing(BrokerError):
    pass


class RebuildRequired(BrokerError):
    pass


class BrokerIdentityConflict(BrokerError):
    pass


class BrokerInitializationFailed(BrokerError):
    pass


# --- R3-B2B additions ---

class AuthorityBusy(BrokerError):
    """A cohort is already open; a second acquisition request was
    serialized/refused rather than opening a second provider."""


class ViewAdmissionRefused(BrokerError):
    """A new detached view could not be admitted into the retained-view
    cache without exceeding the aggregate memory promotion gate, and no
    further unpinned view could be evicted to make room."""


class ViewUncovered(BrokerError):
    """Raised only where a caller explicitly demands a covered result and
    the requested vocabulary was never materialized into the view at all
    -- kept distinct from a MasterUnknown covered-negative result."""


class ViewInvalidated(BrokerError):
    """A detached view's live-authorization token was revoked (its
    generation is no longer current); the payload may still be readable
    for diagnosis, but mutation authorization is gone."""


class AggregateResourceRefusal(BrokerError):
    """The aggregate authority-memory ledger refused an operation because
    admitting it would exceed a configured promotion gate, distinct from
    a single artifact's own ResourceAdmissionRefusal."""


class CohortCancelled(BrokerError):
    """A cohort was explicitly cancelled before publication."""


class EvictedViewLeaseRefused(BrokerError):
    """Astra SECOND correction gate F3/F4: a caller attempted to lease a
    view that the cache no longer tracks in ANY accounted state -- not a
    current cache entry, and not a leased orphan (a view evicted while at
    least one lease was already live keeps its deferred charge and may
    still gain further leases; see ViewCache._remove/acquire_lease). A
    view reaching this state was evicted with ZERO live leases at the
    time, so its ledger charge was already fully released -- honoring a
    new lease on it would create an active lease backed by no retained-
    bytes charge at all. The caller must re-acquire a fresh view instead
    of leasing a stale Python reference to a previously-returned one."""
