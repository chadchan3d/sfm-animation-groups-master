# -*- coding: utf-8 -*-
"""GATE C1 -- QUALIFICATION-ONLY shared-owner foundation. NOT production
code. Never imported by `tools/sfm_master_sidecar/*.py`, never imported by
the production Normalizer, never placed in any real SFM startup path.

Round 3 foundation simplification / repair (subtractive): the Astra Round 3
holistic audit (`SFM_SIDECAR_ASTRA_ROUND3_HOLISTIC_AUDIT_2026-09-13.md`)
reopened C1/C1R and C2/C2R and required this module be SIMPLIFIED around
the original product need, not expanded with more generalized machinery.
This file now implements the post-repair model:

    editable Master TXT
            -> offline deterministic compiler
    complete packed generation
            -> explicit authority-requiring boundary
    one small owner/service
      lazy admission + defensible resource check
      bounded provider decode working set
            ->
    one detached complete action view
      requested positives + proven negatives
      short-lived owner-checked lease
            ->
    release

    source change handling is NOT implemented here (belongs to minimum C3).

Removed by this repair (see `SFM_MASTER_SIDECAR_ROUND3_FOUNDATION_
SIMPLIFICATION_REPAIR_AUDIT.md` for the full mapping to each reproduced
Astra Round 3 finding):
  - the owner-level cross-action `_EpochCoverage` positive/negative cache
    and its FIFO eviction machinery (Repair F) -- every `acquire_view` call
    now resolves entirely from local candidate state;
  - the simulated `registration_install_count`/`registration_identity`
    "one callback registration" claim (Repair C) -- this qualification
    owner never installs a real SFM/OS callback; only `init_call_count`
    (call-site attempts) remains;
  - the redundant fourth guard criterion (`4 GiB - committed_vas`)
    (Repair D) -- mathematically not independent of the free-VAS criterion
    for physically consistent snapshots, and its isolation test used an
    impossible VAS total.

Fixed by this repair:
  - foreign-owner lease confusion (Repair A) -- `get_view_via_lease`/
    `release_lease` now check `lease.owner_id` first;
  - unbounded historical lease/registry retention (Repair B) -- released
    leases are deleted (not tombstoned), and `close()` removes this owner
    from the process registry;
  - a missing-artifact metadata lookup that could escape while PREPARING
    (Repair E) -- `_run_guard` now catches it and ends in UNAVAILABLE;
  - the provider's decoded-string working set could grow past its declared
    budget across refused/faulted requests (Repair G) -- `acquire_view`
    now enforces it in a `finally` block on every attempt;
  - a negative-only view could be pinned-accounted as zero bytes
    (Repair H);
  - two published views (or a view and the provider's own cache) could
    share the same mutable row objects (Repair I) -- every published
    view's rows are now per-view copies.

Scope (still, unchanged in kind from C1): one neutral process-wide owner
per resolved Master namespace; idempotent initialization; lazy admission;
a mandatory pre-admission x86 resource guard; one admitted provider shared
by two consumers; explicit lightweight leases (never Python GC/reachability
as authority); epoch-stamped, detached action-view envelopes; per-request
budget accounting; terminal/idempotent close.

Explicitly NOT implemented here (belongs to minimum C3+): source-change
invalidation, manifest-change replacement, generation replacement, TXT
fallback policy, cross-action reusable coverage (removed, not deferred --
see Repair F), Character Preset adapter, Normalizer production integration.
"""

import os
import itertools

try:
    _NUMERIC_TYPES = (int, float, long)  # noqa: F821 -- Python 2: large ctypes c_size_t
    # values (e.g. real VirtualQuery byte counts) commonly promote to
    # `long`, a distinct type from `int` on this runtime -- excluding it
    # would misclassify a genuine, correctly-typed real resource snapshot
    # as "malformed".
except NameError:
    _NUMERIC_TYPES = (int, float)


# ---------------------------------------------------------------------------
# Owner state machine (unchanged in shape from C1).
# ---------------------------------------------------------------------------

STATE_EMPTY = "EMPTY"
STATE_PREPARING = "PREPARING"
STATE_READY = "READY"
STATE_UNAVAILABLE = "UNAVAILABLE"
STATE_CLOSED = "CLOSED"

_VALID_TRANSITIONS = {
    STATE_EMPTY: {STATE_PREPARING},
    STATE_PREPARING: {STATE_READY, STATE_UNAVAILABLE, STATE_CLOSED},
    STATE_READY: {STATE_CLOSED},
    STATE_UNAVAILABLE: {STATE_PREPARING, STATE_CLOSED},
    STATE_CLOSED: set(),  # terminal
}


class OwnerStateError(Exception):
    """Raised on an attempted illegal state transition. Qualification-only
    -- never raised by production code."""


class LeaseRejected(Exception):
    """Raised when a released, foreign-owner, or otherwise invalid lease is
    used to authorize or release work. Distinct from
    `MasterUnknown`/`AuthorityUnavailable` -- this is a lease-lifecycle/
    ownership fact, not an authority-content fact."""


class ResourceRefused(Exception):
    """Raised by the pre-admission guard, or by a budget check, when a
    request cannot proceed. Never raised after any artifact read/allocation
    has already happened for that request."""


# ---------------------------------------------------------------------------
# Namespace identity -- static authority facts only (never project/model
# identity, per the brief's explicit instruction).
#
# Round 3 §12: this remains "one owner for one equal qualification registry
# key in one module instance." Real source-change/generation replacement
# (a different key resolving to a fresh namespace over time) is explicitly
# NOT implemented here -- it belongs to minimum C3.
# ---------------------------------------------------------------------------


class NamespaceIdentity(object):
    __slots__ = ("source_path", "source_sha256", "artifact_sha256",
                 "format_version", "authority_version", "profile_version")

    def __init__(self, source_path, source_sha256, artifact_sha256,
                 format_version, authority_version, profile_version):
        self.source_path = source_path
        self.source_sha256 = source_sha256
        self.artifact_sha256 = artifact_sha256
        self.format_version = format_version
        self.authority_version = authority_version
        self.profile_version = profile_version

    def _key(self):
        return (self.source_path, self.source_sha256, self.artifact_sha256,
                self.format_version, self.authority_version, self.profile_version)

    def __eq__(self, other):
        return isinstance(other, NamespaceIdentity) and self._key() == other._key()

    def __hash__(self):
        return hash(self._key())

    def __repr__(self):
        return "NamespaceIdentity(source_path=%r, source_sha256=%r, artifact_sha256=%r, " \
               "format_version=%r, authority_version=%r, profile_version=%r)" % self._key()


# ---------------------------------------------------------------------------
# Injectable resource-snapshot interface.
# ---------------------------------------------------------------------------


class ResourceSnapshot(object):
    __slots__ = ("private_usage", "committed_vas", "reserved_vas", "free_vas",
                 "largest_free_region", "bitness")

    def __init__(self, private_usage, committed_vas, reserved_vas, free_vas,
                 largest_free_region, bitness=32):
        self.private_usage = private_usage
        self.committed_vas = committed_vas
        self.reserved_vas = reserved_vas
        self.free_vas = free_vas
        self.largest_free_region = largest_free_region
        self.bitness = bitness


class GuardPolicy(object):
    """PROVISIONAL qualification policy -- explicit, conservative,
    test-facing values, NOT a frozen production threshold.

    Round 3 Repair D: the C1R fourth criterion (`4 GiB - committed_vas >=
    min_committed_ceiling_reserve_bytes`) is REMOVED. The Astra Round 3
    audit found it mathematically redundant with the free-VAS criterion
    for any physically consistent snapshot under the threshold
    relationship this policy actually used, and found its own claimed
    "independence" isolation test relied on an impossible VAS snapshot
    (a committed+reserved+free total that exceeds the assumed 4 GiB
    ceiling itself). Removing it is a genuine simplification, not a
    weakening masked as one: the guard retains only inputs it can
    defensibly evaluate from a real snapshot without assuming a specific
    system-commit-limit subsystem.

    The guard now evaluates exactly:
      1. valid snapshot presence/types;
      2. free VAS below `min_free_vas_bytes`;
      3. largest free contiguous region below `min_largest_free_region_bytes`;
      4. artifact bytes exceeding `artifact_budget_bytes`.
    """

    def __init__(self, min_free_vas_bytes, min_largest_free_region_bytes,
                 artifact_budget_bytes):
        self.min_free_vas_bytes = min_free_vas_bytes
        self.min_largest_free_region_bytes = min_largest_free_region_bytes
        self.artifact_budget_bytes = artifact_budget_bytes

    @classmethod
    def provisional_default(cls):
        """Provisional qualification policy, deliberately conservative and
        explicitly NOT a production SLA."""
        return cls(
            min_free_vas_bytes=64 * 1024 * 1024,
            min_largest_free_region_bytes=32 * 1024 * 1024,
            artifact_budget_bytes=64 * 1024 * 1024,  # matches resource_budgets.BUDGET_ARTIFACT_BYTES_BEFORE_ACQUISITION
        )

    def evaluate(self, snapshot, artifact_byte_length):
        """Returns (ok: bool, reason: str). NEVER opens/reads the artifact
        -- `artifact_byte_length` must be obtained via cheap metadata
        (e.g. os.path.getsize) by the caller, never a full read."""
        if snapshot is None:
            return False, "resource snapshot unavailable (None)"
        try:
            free_vas = snapshot.free_vas
            largest = snapshot.largest_free_region
        except Exception as exc:
            return False, "malformed resource snapshot: %r" % (exc,)
        if not isinstance(free_vas, _NUMERIC_TYPES) or not isinstance(largest, _NUMERIC_TYPES):
            return False, "malformed resource snapshot: non-numeric VAS fields"
        if artifact_byte_length > self.artifact_budget_bytes:
            return False, "artifact is %d bytes, exceeding the artifact budget of %d bytes" % (
                artifact_byte_length, self.artifact_budget_bytes,
            )
        if free_vas < self.min_free_vas_bytes:
            return False, "free VAS %r below required minimum %d" % (free_vas, self.min_free_vas_bytes)
        if largest < self.min_largest_free_region_bytes:
            return False, "largest free contiguous region %r below required minimum %d" % (
                largest, self.min_largest_free_region_bytes,
            )
        return True, "sufficient headroom"


# ---------------------------------------------------------------------------
# Lease.
# ---------------------------------------------------------------------------


class Lease(object):
    __slots__ = ("lease_id", "owner_id", "namespace_identity", "consumer_id",
                 "view_id", "active")

    def __init__(self, lease_id, owner_id, namespace_identity, consumer_id, view_id):
        self.lease_id = lease_id
        self.owner_id = owner_id
        self.namespace_identity = namespace_identity
        self.consumer_id = consumer_id
        self.view_id = view_id
        self.active = True


class ViewEnvelope(object):
    """Round 3 Repair I/J terminology correction: this is a DETACHED STABLE
    ACTION VIEW, not an "immutable payload copy." The payload itself
    remains ordinary mutable Python data (a dict of dicts/lists/sets); what
    is actually guaranteed is narrower and enforced by construction in
    `MasterAuthorityOwner.acquire_view`: every row published in `payload`
    is a fresh per-view copy, so mutating one published view's rows cannot
    mutate another published view or the provider's own decode cache."""
    __slots__ = ("view_id", "namespace_identity", "artifact_sha256", "epoch",
                 "consumer_profile", "wanted_folds", "payload", "accounted_bytes")

    def __init__(self, view_id, namespace_identity, artifact_sha256, epoch,
                 consumer_profile, wanted_folds, payload, accounted_bytes):
        self.view_id = view_id
        self.namespace_identity = namespace_identity
        self.artifact_sha256 = artifact_sha256
        self.epoch = epoch
        self.consumer_profile = consumer_profile
        self.wanted_folds = frozenset(wanted_folds)
        self.payload = payload
        self.accounted_bytes = accounted_bytes


# ---------------------------------------------------------------------------
# The owner itself.
# ---------------------------------------------------------------------------

_OWNER_REGISTRY = {}  # NamespaceIdentity -> MasterAuthorityOwner (process-wide singleton per namespace)
_OWNER_ID_COUNTER = itertools.count(1)


class OwnerBusy(Exception):
    """Raised (never silently swallowed) when a consumer-facing operation
    cannot proceed because the owner is not in an appropriate state for it
    -- currently used for `close()` while active leases remain. Distinct
    from `ResourceRefused` (a resource decision) and `LeaseRejected` (a
    lease-authority decision): this is an owner-lifecycle-sequencing
    fact."""


class MasterAuthorityOwner(object):
    def __init__(self, namespace_identity, artifact_path, resource_snapshot_fn, guard_policy,
                 view_budgets, bounded_provider_module, bounded_view_module):
        self.owner_id = next(_OWNER_ID_COUNTER)
        self.namespace_identity = namespace_identity
        self.artifact_path = artifact_path
        self._resource_snapshot_fn = resource_snapshot_fn
        self.guard_policy = guard_policy
        self.view_budgets = view_budgets
        self._bounded_provider_module = bounded_provider_module
        self._bounded_view_module = bounded_view_module

        self.state = STATE_EMPTY
        self.provider = None
        self.epoch = 0
        self._leases = {}       # lease_id -> Lease; an entry exists IFF that lease is active (Repair B)
        self._views = {}        # view_id -> ViewEnvelope
        self._lease_id_counter = itertools.count(1)
        self._view_id_counter = itertools.count(1)

        # Round 3 Repair C: `init_call_count` counts every call into
        # get_or_create_owner()/simulate_autoinit_call() for this
        # namespace (whether or not it created a new owner) -- the only
        # supported fact is "3 initialization call sites -> 1 owner
        # object." This qualification owner does not install any real
        # SFM/OS callback, so no "registration installation" count or
        # identity is tracked or asserted.
        self.init_call_count = 0
        self.admission_attempt_count = 0
        self.admission_success_count = 0
        self.provider_allocation_count = 0
        self.guard_refusal_count = 0

        self._set_state(STATE_EMPTY, STATE_EMPTY)  # no-op transition, records nothing

    # -- state machine --

    def _set_state(self, expected_current, new_state):
        if self.state != expected_current:
            raise OwnerStateError(
                "expected state %r, actually %r" % (expected_current, self.state)
            )
        if new_state != self.state and new_state not in _VALID_TRANSITIONS.get(self.state, set()):
            raise OwnerStateError(
                "illegal transition %r -> %r" % (self.state, new_state)
            )
        self.state = new_state

    # -- initialization (idempotent via get_or_create, see module-level function) --

    def _record_init_call(self):
        """Records an init-CALL attempt only (Round 3 Repair C) -- this
        owner never installs a real callback, so there is nothing else to
        record here."""
        self.init_call_count += 1

    # -- lazy admission --

    def _artifact_byte_length(self):
        return os.path.getsize(self.artifact_path)

    def _run_guard(self):
        """Round 3 Repair E: this method must NEVER raise. Both the
        resource-snapshot call AND the artifact-metadata lookup are now
        caught here -- previously, a missing/unreadable artifact's
        `os.path.getsize` call could raise straight out of `_ensure_
        admitted` while the owner was still in PREPARING, leaving it
        stuck outside the state machine's normal transition table instead
        of landing in the recoverable UNAVAILABLE state."""
        snapshot = None
        snapshot_error = None
        try:
            snapshot = self._resource_snapshot_fn()
        except Exception as exc:
            snapshot_error = exc
        if snapshot_error is not None:
            self.guard_refusal_count += 1
            return False, "resource snapshot provider raised: %r" % (snapshot_error,)

        try:
            artifact_bytes = self._artifact_byte_length()
        except Exception as exc:
            self.guard_refusal_count += 1
            return False, "artifact metadata unavailable: %r" % (exc,)

        ok, reason = self.guard_policy.evaluate(snapshot, artifact_bytes)
        if not ok:
            self.guard_refusal_count += 1
        return ok, reason

    def _ensure_admitted(self):
        """Lazy admission: the FIRST time this is called (state EMPTY or
        UNAVAILABLE), runs the pre-admission guard BEFORE any artifact
        read. If the provider is already admitted (state READY), this is
        a no-op -- the second consumer reuses it, never re-admits.

        Round 3 Repair E: any failure during guard evaluation (including a
        missing/unreadable artifact) now always lands in UNAVAILABLE, with
        no provider allocated and no partial lease/view published. A later
        call (after the artifact is restored) may return through PREPARING
        and succeed."""
        if self.state == STATE_READY:
            return True, "already admitted"
        if self.state == STATE_CLOSED:
            return False, "owner is CLOSED"
        if self.state not in (STATE_EMPTY, STATE_UNAVAILABLE):
            return False, "owner in unexpected state %r" % (self.state,)

        prior_state = self.state
        self._set_state(prior_state, STATE_PREPARING)
        self.admission_attempt_count += 1

        guard_ok, guard_reason = self._run_guard()
        if not guard_ok:
            self._set_state(STATE_PREPARING, STATE_UNAVAILABLE)
            return False, "resource guard refused admission: %s" % (guard_reason,)

        # Guard passed -- NOW it is safe to read the artifact and construct
        # the provider (validation happens inside BoundedProvider.open_path,
        # delegating to the single shared production validator).
        try:
            provider = self._bounded_provider_module.BoundedProvider.open_path(
                self.artifact_path, self.namespace_identity.source_sha256,
            )
        except Exception as exc:
            self._set_state(STATE_PREPARING, STATE_UNAVAILABLE)
            return False, "admission failed: %r" % (exc,)

        self.provider = provider
        self.provider_allocation_count += 1
        self.admission_success_count += 1
        self.epoch += 1
        self._set_state(STATE_PREPARING, STATE_READY)
        return True, "admitted"

    def _enforce_decode_cache_bound(self):
        """Round 3 Repair G: the provider's reusable decoded-string/
        metadata working set must never be left arbitrarily grown after
        ANY `acquire_view` attempt -- ordinary, refused, or faulted alike.
        Enforcement is by eviction (a performance cost on the next lookup
        only -- never a truth change, and never affects an already-
        published, detached `ViewEnvelope` payload, since those hold their
        own per-view row copies, not references into this cache)."""
        if self.provider is None or not self.provider.is_valid():
            return
        budget = self.view_budgets.decode_cache_estimated_bytes_budget
        if budget is None:
            return
        if self.provider.string_cache_estimated_bytes() > budget:
            self.provider.evict_reusable_cache()

    def _estimate_accounted_bytes(self, wanted_folds, folded):
        """Round 3 Repair H: a negative-only view (every requested fold
        proven absent, so `folded` is empty) must not be pinned-accounted
        as zero bytes. Every REQUESTED fold (positive or negative) is
        charged a conservative per-fold overhead allowance, plus a small
        fixed per-view overhead, plus the existing per-row estimate for
        actually-retained positive rows. This is a provisional estimate,
        never a claim of exact RSS/private bytes."""
        total_rows = sum(len(v) for v in folded.values())
        row_bytes = total_rows * self.view_budgets.estimated_bytes_per_row
        fold_overhead = len(wanted_folds) * self.view_budgets.per_requested_fold_overhead_bytes
        return self.view_budgets.per_view_fixed_overhead_bytes + fold_overhead + row_bytes

    # -- consumer-facing lease/view acquisition --

    def acquire_view(self, consumer_id, wanted_folds, probe_error_cls, consumer_profile="generic",
                      fault_injector=None):
        """Round 3 Repair F: NO owner-level cross-action reusable cache.
        Every call resolves every requested fold against the already-
        admitted provider into a PRIVATE local candidate (never touching
        `self._views`/`self._leases` until publication). Repeated calls
        for the same fold across separate `acquire_view` invocations
        perform repeated provider lookups -- intentionally not optimized
        in this repair.

        Round 3 Repair J (narrowed publication guarantee): no lease/view
        becomes authorized before candidate resolution, every budget
        check, and the epoch check all succeed; a failed candidate
        publishes nothing and merges nothing; existing published views
        remain valid; the provider's own diagnostic/decode cache may
        change (via `_enforce_decode_cache_bound`, always run in the
        `finally` block below) so long as it remains truthful and within
        its retained bound -- this is NOT a "byte-identical whole-owner
        rollback" claim and none is made.

        Round 3 Repair I: every published row is copied fresh for this
        view (`[dict(r) for r in rows]`) so mutating one published view's
        rows can never mutate another published view or the provider's
        own cache.

        Coverage contract (Repair F): the published payload distinguishes
        a requested positive fold (`payload["folded"]`), a requested
        proven-negative fold (`payload["proven_negative_folds"]`), and a
        fold not requested by this action (absent from both) -- a global
        negative is never inferred from mere absence in some other view.
        """
        if self.state == STATE_CLOSED:
            raise ResourceRefused("owner is CLOSED -- no new lease/view may be created")

        ok, reason = self._ensure_admitted()
        if not ok:
            raise ResourceRefused("cannot acquire view: %s" % (reason,))

        wanted_folds = set(wanted_folds)
        epoch_at_start = self.epoch

        try:
            wrapper_name = self.provider.wrapper_path()
            candidate_positive = {}   # fold_key -> rows (Gate A2 contract shape), private until publish
            candidate_negative = set()

            for i, fold_key in enumerate(sorted(wanted_folds), start=1):
                result = self.provider.lookup_fold(fold_key.encode("utf-8"))
                if result.__class__.__name__ == "MasterUnknown":
                    candidate_negative.add(fold_key)
                else:
                    rows = []
                    for occ in result.occurrences():
                        dest = self._bounded_view_module.strip_wrapper(occ["full_path"], wrapper_name)
                        rows.append({
                            "literal": occ["literal"], "destination": dest,
                            "global_index": occ["global_rank"], "local_index": occ["local_rank"],
                        })
                    rows.sort(key=lambda r: r["global_index"])
                    if len(rows) > self.view_budgets.one_family_result_rows:
                        raise ResourceRefused(
                            "fold %r resolves to %d rows, exceeding the one-family budget of %d rows -- "
                            "candidate discarded, nothing published" % (
                                fold_key, len(rows), self.view_budgets.one_family_result_rows,
                            )
                        )
                    candidate_positive[fold_key] = rows

                if fault_injector is not None:
                    fault_injector(i, fold_key)  # qualification-only; may raise -- candidate discarded below

                if self.epoch != epoch_at_start:
                    raise ResourceRefused(
                        "owner epoch changed during resolution (expected %r, now %r) -- "
                        "candidate discarded, nothing published" % (
                            epoch_at_start, self.epoch,
                        )
                    )

            # Global stats/hierarchy (mapping_count/destination_count/
            # group_sibling_order/group_metadata) are scope-independent --
            # computed once here from the already-admitted provider, never
            # cached/reused across separate acquire_view calls (Repair F).
            base = self._bounded_view_module.build_view_bounded(self.provider, set(), probe_error_cls)

            folded = {}
            proven_negative_folds = set()
            exact_literals = set()
            for fold_key in wanted_folds:
                if fold_key in candidate_negative:
                    proven_negative_folds.add(fold_key)
                    continue
                rows = candidate_positive.get(fold_key)
                if rows is None:
                    continue
                folded[fold_key] = [dict(r) for r in rows]  # Repair I: fresh per-view copy
                for r in rows:
                    exact_literals.add(r["literal"])

            total_rows = sum(len(v) for v in folded.values())
            if total_rows > self.view_budgets.one_snapshot_rows:
                raise ResourceRefused(
                    "requested view would retain %d rows, exceeding the one-snapshot budget of %d rows -- "
                    "candidate discarded, nothing published" % (
                        total_rows, self.view_budgets.one_snapshot_rows,
                    )
                )
            accounted_bytes = self._estimate_accounted_bytes(wanted_folds, folded)
            pinned_total = sum(v.accounted_bytes for v in self._views.values()) + accounted_bytes
            if pinned_total > self.view_budgets.total_pinned_bytes:
                raise ResourceRefused(
                    "publishing this view would bring total pinned-view accounting to %d bytes, "
                    "exceeding the total-pinned budget of %d bytes -- candidate discarded, nothing "
                    "published; existing views remain valid" % (
                        pinned_total, self.view_budgets.total_pinned_bytes,
                    )
                )
            if self.epoch != epoch_at_start:
                raise ResourceRefused(
                    "owner epoch changed just before publication (expected %r, now %r) -- "
                    "candidate discarded" % (epoch_at_start, self.epoch)
                )

            view_payload = {
                "mapping_count": base["mapping_count"], "destination_count": base["destination_count"],
                "folded": folded, "exact_literals": exact_literals,
                "proven_negative_folds": frozenset(proven_negative_folds),
                "group_sibling_order": base["group_sibling_order"], "group_metadata": base["group_metadata"],
            }

            view_id = next(self._view_id_counter)
            envelope = ViewEnvelope(
                view_id=view_id, namespace_identity=self.namespace_identity,
                artifact_sha256=self.namespace_identity.artifact_sha256, epoch=self.epoch,
                consumer_profile=consumer_profile, wanted_folds=wanted_folds, payload=view_payload,
                accounted_bytes=accounted_bytes,
            )
            self._views[view_id] = envelope

            lease_id = next(self._lease_id_counter)
            lease = Lease(lease_id, self.owner_id, self.namespace_identity, consumer_id, view_id)
            self._leases[lease_id] = lease
            return lease, envelope
        finally:
            self._enforce_decode_cache_bound()

    def get_view_via_lease(self, lease):
        """The authority gate: a released lease, a foreign-owner lease
        (Round 3 Repair A), a lease from a closed owner, or a lease whose
        view no longer belongs to the current epoch never authorizes
        access -- this is checked EVERY time, not just at acquisition."""
        if lease.owner_id != self.owner_id:
            raise LeaseRejected(
                "lease %r belongs to owner %r, not this owner %r -- does not authorize access" % (
                    lease.lease_id, lease.owner_id, self.owner_id,
                )
            )
        if self.state == STATE_CLOSED:
            raise LeaseRejected("owner is CLOSED -- lease no longer authorizes access")
        stored = self._leases.get(lease.lease_id)
        if stored is None or not stored.active:
            raise LeaseRejected("lease %r is released/unknown -- does not authorize access" % (lease.lease_id,))
        envelope = self._views.get(stored.view_id)
        if envelope is None:
            raise LeaseRejected("lease %r has no corresponding view" % (lease.lease_id,))
        if envelope.epoch != self.epoch:
            raise LeaseRejected("lease %r's view belongs to a stale epoch" % (lease.lease_id,))
        return envelope

    def release_lease(self, lease):
        """Round 3 Repair A: a foreign-owner lease is rejected outright --
        it can neither release nor mutate this owner's state.

        Round 3 Repair B: releasing a lease DELETES its record from
        `self._leases` (no retained tombstone/history entry). Idempotency
        for repeated release of the SAME already-inactive external `Lease`
        object is detected from that object's own `.active` flag (the
        exact object returned by `acquire_view` is the same object stored
        internally, so this flag is authoritative), not from a
        server-side history table -- so repeated release never grows any
        central record."""
        if lease.owner_id != self.owner_id:
            raise LeaseRejected(
                "lease %r belongs to owner %r, not this owner %r -- cannot be released here" % (
                    lease.lease_id, lease.owner_id, self.owner_id,
                )
            )
        if not lease.active:
            return "already-released-noop"
        stored = self._leases.get(lease.lease_id)
        if stored is None:
            # Same-owner but no live record -- defensive fallback only;
            # does not occur in normal use, since a genuine same-owner
            # Lease object's `.active` flag is flipped in the same
            # operation that removes its `_leases` entry.
            lease.active = False
            return "unknown-lease-noop"
        stored.active = False
        lease.active = False
        del self._leases[lease.lease_id]
        # Drop the view envelope only when no other active lease still
        # references it (a real owner might share one view across leases;
        # this repair keeps that simple -- one view per lease -- so this
        # always drops it here).
        still_referenced = any(
            l.active and l.view_id == stored.view_id for l in self._leases.values()
        )
        if not still_referenced and stored.view_id in self._views:
            del self._views[stored.view_id]
        return "released"

    # -- accounting --

    def active_lease_count(self):
        return sum(1 for l in self._leases.values() if l.active)

    def active_view_count(self):
        return len(self._views)

    def total_pinned_view_bytes(self):
        return sum(v.accounted_bytes for v in self._views.values())

    def resource_snapshot_dict(self):
        d = {"owner_state": self.state, "active_leases": self.active_lease_count(),
             "active_views": self.active_view_count(),
             "total_pinned_view_bytes": self.total_pinned_view_bytes()}
        if self.provider is not None and self.provider.is_valid():
            d.update(self.provider.resource_snapshot())
        return d

    # -- close --

    def close(self):
        """Terminal, idempotent.

        If any lease is still active, close() REFUSES/DEFERS: the owner's
        state is left completely unchanged, the provider is not touched,
        `_views` is not cleared, every active lease keeps authorizing
        access exactly as before -- no partial cleanup of any kind.

        Only once `active_lease_count() == 0` does close() actually
        terminate the owner: closes the provider (if any), clears the
        (already-empty, by construction) view registry, clears the lease
        registry, and -- Round 3 Repair B -- removes this owner from the
        process-wide registry IF that registry entry still points to this
        exact owner object, so a closed owner is never discoverable via
        the normal `get_or_create_owner` lookup path. Repeated close() on
        an already-CLOSED owner remains a harmless idempotent no-op."""
        if self.state == STATE_CLOSED:
            return "already-closed-noop"
        outstanding = self.active_lease_count()
        if outstanding > 0:
            return "deferred-active-leases:%d" % outstanding
        if self.provider is not None and self.provider.is_valid():
            self.provider.close()
        self.provider = None
        self.state = STATE_CLOSED
        self._views.clear()
        self._leases.clear()
        if _OWNER_REGISTRY.get(self.namespace_identity) is self:
            del _OWNER_REGISTRY[self.namespace_identity]
        return "closed"

    def close_or_raise(self):
        """Convenience wrapper some callers may prefer: raises `OwnerBusy`
        instead of returning a sentinel string when leases are
        outstanding. `close()` itself never raises for this case -- both
        forms are supported."""
        result = self.close()
        if isinstance(result, str) and result.startswith("deferred-active-leases:"):
            raise OwnerBusy(result)
        return result


class ViewBudgets(object):
    def __init__(self, one_family_result_rows, one_snapshot_rows, total_pinned_bytes,
                 estimated_bytes_per_row=256, decode_cache_estimated_bytes_budget=None,
                 per_view_fixed_overhead_bytes=256, per_requested_fold_overhead_bytes=64):
        self.one_family_result_rows = one_family_result_rows
        self.one_snapshot_rows = one_snapshot_rows
        self.total_pinned_bytes = total_pinned_bytes
        self.estimated_bytes_per_row = estimated_bytes_per_row
        # Round 3 Repair G: the bound enforced (via eviction, in
        # `MasterAuthorityOwner._enforce_decode_cache_bound`) against the
        # PROVIDER's own reusable decoded-string/metadata working set --
        # not a view-payload bound. `None` disables enforcement (not used
        # by `from_qualification_defaults`).
        self.decode_cache_estimated_bytes_budget = decode_cache_estimated_bytes_budget
        # Round 3 Repair H: provisional per-view/per-requested-fold
        # overhead estimates, so a negative-only (or mixed) view is never
        # accounted as merely its positive row count.
        self.per_view_fixed_overhead_bytes = per_view_fixed_overhead_bytes
        self.per_requested_fold_overhead_bytes = per_requested_fold_overhead_bytes

    @classmethod
    def from_qualification_defaults(cls, resource_budgets_module):
        rb = resource_budgets_module
        return cls(
            one_family_result_rows=rb.BUDGET_ONE_FAMILY_RESULT_OCCURRENCE_ROWS,
            one_snapshot_rows=rb.BUDGET_ONE_CONSUMER_SNAPSHOT_OCCURRENCE_ROWS,
            total_pinned_bytes=rb.BUDGET_TOTAL_PINNED_VIEWS_ESTIMATED_BYTES,
            decode_cache_estimated_bytes_budget=rb.BUDGET_STRING_CACHE_ESTIMATED_BYTES,
        )


def get_or_create_owner(namespace_identity, artifact_path, resource_snapshot_fn, guard_policy,
                         view_budgets, bounded_provider_module, bounded_view_module):
    """Idempotent, process-wide-per-namespace owner lookup/creation. This
    is the ONE entry point every call site (direct call, simulated
    autoinit, repeated calls) must use -- it is what makes "one owner per
    namespace" an enforced invariant rather than a convention."""
    existing = _OWNER_REGISTRY.get(namespace_identity)
    if existing is not None and existing.state != STATE_CLOSED:
        existing._record_init_call()
        return existing
    owner = MasterAuthorityOwner(
        namespace_identity, artifact_path, resource_snapshot_fn, guard_policy,
        view_budgets, bounded_provider_module, bounded_view_module,
    )
    owner._record_init_call()
    _OWNER_REGISTRY[namespace_identity] = owner
    return owner


def simulate_autoinit_call(namespace_identity, artifact_path, resource_snapshot_fn, guard_policy,
                            view_budgets, bounded_provider_module, bounded_view_module):
    """A second, independent call site (simulating a real autoinit-style
    startup call) into the SAME idempotent entry point -- proves
    idempotency is not merely "don't call it twice yourself" but holds
    across genuinely different call sites too. Does not modify any real
    SFM startup file."""
    return get_or_create_owner(
        namespace_identity, artifact_path, resource_snapshot_fn, guard_policy,
        view_budgets, bounded_provider_module, bounded_view_module,
    )


def _reset_registry_for_testing():
    """Test-only: DETERMINISTICALLY releases every active lease and closes
    every owner still in the registry (via the NORMAL, unmodified public
    `release_lease()`/`close()` API -- no production-semantics bypass, no
    special test-only close path) before clearing the registry itself.
    Every owner is now guaranteed CLOSED (`is_valid() == False` on its
    provider, if any) before the registry is cleared, and any leftover
    reference a test still holds to it will correctly find it unusable.

    Never called by any non-test code path."""
    for owner in list(_OWNER_REGISTRY.values()):
        if owner.state == STATE_CLOSED:
            continue
        for lease in list(owner._leases.values()):
            if lease.active:
                owner.release_lease(lease)
        result = owner.close()
        assert result == "closed" or result == "already-closed-noop", (
            "test reset could not close owner %r after releasing all its leases: %r" % (owner.owner_id, result)
        )
    _OWNER_REGISTRY.clear()
