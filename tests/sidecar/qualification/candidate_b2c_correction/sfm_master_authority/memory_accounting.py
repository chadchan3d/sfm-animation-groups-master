# -*- coding: utf-8 -*-
"""Aggregate authority-memory accounting -- ASTRA_CORRECTED.md Section 5,
R3-B2B Section 7.

ONE shared ledger, never independent per-tool quotas. Tracks conservative
LOGICAL byte estimates per named category. `sys.getsizeof()` is never
treated as a complete native/VAS measurement -- see
`AggregateLedger.RUNTIME_QUALIFICATION_NOTE`.
"""

CATEGORY_RESIDENT_BROKER_METADATA = "resident_broker_metadata"
CATEGORY_RETAINED_VIEWS = "retained_detached_views"
CATEGORY_STALE_REFERENCED_VIEWS = "stale_invalidated_views_still_referenced"
CATEGORY_PENDING_PROJECTION = "pending_projection_payload"
CATEGORY_INCOMING_SNAPSHOT = "one_incoming_packed_snapshot"
CATEGORY_VALIDATOR_SCRATCH = "validator_scratch_estimate"
CATEGORY_PROVIDER_CACHES = "provider_caches"
CATEGORY_REPLACEMENT_OVERLAP = "temporary_replacement_overlap"

ALL_CATEGORIES = (
    CATEGORY_RESIDENT_BROKER_METADATA, CATEGORY_RETAINED_VIEWS,
    CATEGORY_STALE_REFERENCED_VIEWS, CATEGORY_PENDING_PROJECTION,
    CATEGORY_INCOMING_SNAPSHOT, CATEGORY_VALIDATOR_SCRATCH,
    CATEGORY_PROVIDER_CACHES, CATEGORY_REPLACEMENT_OVERLAP,
)

# R2-qualified envelope, retained here as AGGREGATE promotion gates
# (ASTRA_CORRECTED.md Section 5) -- never per-consumer allowances.
RETAINED_PROMOTION_GATE_BYTES = 16 * 1024 * 1024
TRANSIENT_PROMOTION_GATE_BYTES = 32 * 1024 * 1024


class AggregateLedger(object):
    """One ledger per broker instance (== one process-wide ledger, since
    exactly one broker exists per process). Entries are charged/released
    by (category, entry_id) so overlapping/replacement charges can be
    tracked without double-counting or accidentally clobbering an
    unrelated entry in the same category."""

    RUNTIME_QUALIFICATION_NOTE = (
        "This ledger accounts LOGICAL bytes computed in Python (payload "
        "size estimates, structural counts) -- it is NOT a substitute for "
        "a real external VAS/memory sampler against the actual 32-bit SFM "
        "process. The <=16 MiB retained / <=32 MiB transient envelopes "
        "remain PROMOTION GATES pending that designated runtime "
        "qualification, not proven facts established by this ledger alone."
    )

    def __init__(self):
        self._entries = {}
        for cat in ALL_CATEGORIES:
            self._entries[cat] = {}
        self._charges = {}
        for cat in ALL_CATEGORIES:
            self._charges[cat] = 0

    def charge(self, category, entry_id, estimated_bytes):
        if category not in self._entries:
            raise ValueError("unknown accounting category %r" % (category,))
        self._entries[category][entry_id] = estimated_bytes
        self._recompute(category)

    def release(self, category, entry_id):
        if category not in self._entries:
            raise ValueError("unknown accounting category %r" % (category,))
        self._entries[category].pop(entry_id, None)
        self._recompute(category)

    def _recompute(self, category):
        self._charges[category] = sum(self._entries[category].values())

    def total_retained_bytes(self):
        """'Retained' for promotion-gate purposes: broker metadata + every
        view still in the cache (live or stale-but-referenced) + provider
        caches. Transient categories are excluded -- they are bounded
        instead by the at-most-one-open-provider invariant (§6)."""
        return (
            self._charges[CATEGORY_RESIDENT_BROKER_METADATA]
            + self._charges[CATEGORY_RETAINED_VIEWS]
            + self._charges[CATEGORY_STALE_REFERENCED_VIEWS]
            + self._charges[CATEGORY_PROVIDER_CACHES]
        )

    def total_transient_bytes(self):
        return (
            self._charges[CATEGORY_PENDING_PROJECTION]
            + self._charges[CATEGORY_INCOMING_SNAPSHOT]
            + self._charges[CATEGORY_VALIDATOR_SCRATCH]
            + self._charges[CATEGORY_REPLACEMENT_OVERLAP]
        )

    def snapshot(self):
        return dict(self._charges)

    def would_exceed_retained_gate(self, additional_bytes):
        return (self.total_retained_bytes() + additional_bytes) > RETAINED_PROMOTION_GATE_BYTES

    def would_exceed_transient_gate(self, additional_bytes):
        return (self.total_transient_bytes() + additional_bytes) > TRANSIENT_PROMOTION_GATE_BYTES
