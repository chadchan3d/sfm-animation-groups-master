# -*- coding: utf-8 -*-
"""GATE C1 -- QUALIFICATION-ONLY shared-owner foundation. NOT production
code. Never imported by `tools/sfm_master_sidecar/*.py`, never imported by
the production Normalizer, never placed in any real SFM startup path.

Scope (Gate C1 brief §0): one neutral process-wide owner per resolved
Master namespace; idempotent initialization; lazy admission; a mandatory
pre-admission x86 resource guard; one admitted provider shared by two
consumers; explicit lightweight leases (never Python GC/reachability as
authority); immutable generation-bound view envelopes; bounded cache/view
accounting with eviction/refusal; terminal/idempotent close.

Explicitly NOT implemented here (belongs to C2-C4): source-change
invalidation, manifest-change replacement, G1->G2 serialized replacement,
mid-transaction generation switching, TXT fallback policy, late-vocabulary
expansion beyond constructing two distinct views, Character Preset
adapter, Normalizer production integration.
"""

import os
import time
import itertools

try:
    _NUMERIC_TYPES = (int, float, long)  # noqa: F821 -- Python 2: large ctypes c_size_t
    # values (e.g. real VirtualQuery byte counts) commonly promote to
    # `long`, a distinct type from `int` on this runtime -- excluding it
    # would misclassify a genuine, correctly-typed real resource snapshot
    # as "malformed".
except NameError:
    _NUMERIC_TYPES = (int, float)

from sfm_master_sidecar import reader as prod_reader  # noqa: E402 -- for exception classes only


# ---------------------------------------------------------------------------
# Owner state machine (C1 minimum set).
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
    """Raised when a released or otherwise invalid lease is used to
    authorize new work. Distinct from `MasterUnknown`/`AuthorityUnavailable`
    -- this is a lease-lifecycle fact, not an authority-content fact."""


class ResourceRefused(Exception):
    """Raised by the pre-admission guard, or by a budget check, when a
    request cannot proceed. Never raised after any artifact read/allocation
    has already happened for that request."""


# ---------------------------------------------------------------------------
# Namespace identity -- static authority facts only (never project/model
# identity, per the brief's explicit instruction).
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
# Injectable resource-snapshot interface (Part 7.1).
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
    """PROVISIONAL C1 QUALIFICATION POLICY -- explicit, conservative,
    test-facing values, NOT a frozen production threshold derived from the
    single C0 loaded run (per Part 7.1's explicit instruction). Every value
    here is documented in the C1 audit as provisional.

    Gate C1R Repair C: the guard's four criteria are each genuinely
    INDEPENDENT (each can fail while every other one passes):
      1. free VAS below `min_free_vas_bytes`;
      2. largest free contiguous region below `min_largest_free_region_bytes`;
      3. artifact bytes exceed `artifact_budget_bytes`;
      4. committed VAS leaves less than `min_committed_ceiling_reserve_bytes`
         of headroom against `assumed_address_space_ceiling_bytes` -- a
         DIFFERENT measured quantity (`committed_vas`) than criteria 1-2
         use (`free_vas`/`largest_free_region`), so it is possible to
         construct a snapshot that fails ONLY this criterion (large free
         VAS and a large contiguous free region, but committed VAS already
         close to the assumed ceiling) or ONLY criteria 1-2 (small/
         fragmented free VAS, but committed VAS far from the ceiling).
    The prior C1 implementation set `projected_headroom = free_vas` for
    this fourth criterion, making it mathematically incapable of failing
    independently of criterion 1 (the review finding this repair closes).
    """

    # Gate C1R: real, checked evidence (not an assumption) -- sfm.exe's own
    # PE header declares IMAGE_FILE_LARGE_ADDRESS_AWARE. Verified this
    # session: `Characteristics = 0x0122`, and
    # `0x0122 & IMAGE_FILE_LARGE_ADDRESS_AWARE(0x0020) != 0`. A 32-bit LAA
    # process on 64-bit Windows is not subject to the 2 GiB non-LAA
    # ceiling; the practical usable ceiling is a 32-bit pointer's full
    # 4 GiB range (not "4 GiB usable" as a claim about available system
    # memory -- purely the address-space SIZE this process's pointers can
    # represent, which committed+reserved+free VAS never exceeds by
    # construction, per the C0/Gate-2 sampler's own VAS-scan ceiling).
    ASSUMED_ADDRESS_SPACE_CEILING_BYTES = 4 * 1024 * 1024 * 1024

    def __init__(self, min_free_vas_bytes, min_largest_free_region_bytes,
                 min_committed_ceiling_reserve_bytes, artifact_budget_bytes,
                 assumed_address_space_ceiling_bytes=None):
        self.min_free_vas_bytes = min_free_vas_bytes
        self.min_largest_free_region_bytes = min_largest_free_region_bytes
        self.min_committed_ceiling_reserve_bytes = min_committed_ceiling_reserve_bytes
        self.artifact_budget_bytes = artifact_budget_bytes
        self.assumed_address_space_ceiling_bytes = (
            assumed_address_space_ceiling_bytes
            if assumed_address_space_ceiling_bytes is not None
            else self.ASSUMED_ADDRESS_SPACE_CEILING_BYTES
        )

    @classmethod
    def provisional_default(cls):
        """Provisional C1 qualification policy, deliberately conservative
        and explicitly NOT a production SLA. See C1 audit §10 / C1R §4."""
        return cls(
            min_free_vas_bytes=64 * 1024 * 1024,
            min_largest_free_region_bytes=32 * 1024 * 1024,
            min_committed_ceiling_reserve_bytes=32 * 1024 * 1024,
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
            committed = snapshot.committed_vas
        except Exception as exc:
            return False, "malformed resource snapshot: %r" % (exc,)
        if (not isinstance(free_vas, _NUMERIC_TYPES) or not isinstance(largest, _NUMERIC_TYPES)
                or not isinstance(committed, _NUMERIC_TYPES)):
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
        # Independent criterion (Gate C1R Repair C): committed VAS against
        # the documented LAA address-space ceiling -- a different measured
        # quantity than free_vas/largest_free_region, so this can fail (or
        # pass) independently of criteria 1-2.
        ceiling_reserve = self.assumed_address_space_ceiling_bytes - committed
        if ceiling_reserve < self.min_committed_ceiling_reserve_bytes:
            return False, (
                "committed VAS %r leaves only %r bytes of reserve against the assumed "
                "%r-byte address-space ceiling, below required minimum %d" % (
                    committed, ceiling_reserve, self.assumed_address_space_ceiling_bytes,
                    self.min_committed_ceiling_reserve_bytes,
                )
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
        self.payload = payload  # the existing Normalizer-compatible dict, immutable by convention
        self.accounted_bytes = accounted_bytes


# ---------------------------------------------------------------------------
# The owner itself.
# ---------------------------------------------------------------------------

_OWNER_REGISTRY = {}  # NamespaceIdentity -> MasterAuthorityOwner (process-wide singleton per namespace)
_OWNER_ID_COUNTER = itertools.count(1)
_REGISTRATION_ID_COUNTER = itertools.count(1)


class OwnerBusy(Exception):
    """Gate C1R Repair B: raised (never silently swallowed) when a
    consumer-facing operation cannot proceed because the owner is not in
    an appropriate state for it -- currently used for `close()` while
    active leases remain. Distinct from `ResourceRefused` (a resource
    decision) and `LeaseRejected` (a lease-authority decision): this is an
    owner-lifecycle-sequencing fact."""


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
        self._leases = {}       # lease_id -> Lease
        self._views = {}        # view_id -> ViewEnvelope
        self._lease_id_counter = itertools.count(1)
        self._view_id_counter = itertools.count(1)

        # Independent evidence counters (Part 5), corrected per Gate C1R
        # Repair A: `init_call_count` counts every call into
        # get_or_create_owner()/simulate_autoinit_call() for this
        # namespace (whether or not it created a new owner);
        # `registration_install_count` and `registration_identity` are set
        # EXACTLY ONCE, here in __init__, and never incremented/changed
        # again for this owner's lifetime -- they prove "one installed
        # registration," not "how many times someone asked for one."
        self.init_call_count = 0
        self.registration_install_count = 1
        self.registration_identity = "owner-registration-%d" % next(_REGISTRATION_ID_COUNTER)
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
        """Gate C1R Repair A: records an INIT-CALL ATTEMPT only. Never
        touches `registration_install_count`/`registration_identity` --
        those are fixed at construction time (see `__init__`), proving
        "one installed registration" independent of how many times any
        call site subsequently asks for this namespace's owner."""
        self.init_call_count += 1

    # -- lazy admission --

    def _artifact_byte_length(self):
        return os.path.getsize(self.artifact_path)

    def _run_guard(self):
        snapshot = None
        snapshot_error = None
        try:
            snapshot = self._resource_snapshot_fn()
        except Exception as exc:
            snapshot_error = exc
        if snapshot_error is not None:
            self.guard_refusal_count += 1
            return False, "resource snapshot provider raised: %r" % (snapshot_error,)
        artifact_bytes = self._artifact_byte_length()
        ok, reason = self.guard_policy.evaluate(snapshot, artifact_bytes)
        if not ok:
            self.guard_refusal_count += 1
        return ok, reason

    def _ensure_admitted(self):
        """Lazy admission: the FIRST time this is called (state EMPTY),
        runs the pre-admission guard BEFORE any artifact read. If the
        provider is already admitted (state READY), this is a no-op --
        the second consumer reuses it, never re-admits."""
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

    # -- consumer-facing lease/view acquisition --

    def acquire_view(self, consumer_id, wanted_folds, probe_error_cls, consumer_profile="generic"):
        if self.state == STATE_CLOSED:
            raise ResourceRefused("owner is CLOSED -- no new lease/view may be created")

        ok, reason = self._ensure_admitted()
        if not ok:
            raise ResourceRefused("cannot acquire view: %s" % (reason,))

        # Per-fold family budget + consumer-snapshot budget, BEFORE
        # publishing any new view (Gate C0.7 mechanism, reused here at the
        # owner level).
        for fold_key in wanted_folds:
            result = self.provider.lookup_fold(fold_key.encode("utf-8"))
            if result.__class__.__name__ != "MasterUnknown":
                occs = result.occurrences()
                if len(occs) > self.view_budgets.one_family_result_rows:
                    raise ResourceRefused(
                        "fold %r resolves to %d rows, exceeding the one-family budget of %d rows -- "
                        "refused before publishing any view" % (
                            fold_key, len(occs), self.view_budgets.one_family_result_rows,
                        )
                    )

        view = self._bounded_view_module.build_view_bounded(self.provider, wanted_folds, probe_error_cls)
        total_rows = sum(len(v) for v in view["folded"].values())
        if total_rows > self.view_budgets.one_snapshot_rows:
            raise ResourceRefused(
                "requested view would retain %d rows, exceeding the one-snapshot budget of %d rows -- "
                "refused before publishing" % (total_rows, self.view_budgets.one_snapshot_rows,)
            )
        accounted_bytes = total_rows * self.view_budgets.estimated_bytes_per_row
        pinned_total = sum(v.accounted_bytes for v in self._views.values()) + accounted_bytes
        if pinned_total > self.view_budgets.total_pinned_bytes:
            raise ResourceRefused(
                "publishing this view would bring total pinned-view accounting to %d bytes, "
                "exceeding the total-pinned budget of %d bytes -- refused before publishing; "
                "existing views remain valid" % (pinned_total, self.view_budgets.total_pinned_bytes,)
            )

        view_id = next(self._view_id_counter)
        envelope = ViewEnvelope(
            view_id=view_id, namespace_identity=self.namespace_identity,
            artifact_sha256=self.namespace_identity.artifact_sha256, epoch=self.epoch,
            consumer_profile=consumer_profile, wanted_folds=wanted_folds, payload=view,
            accounted_bytes=accounted_bytes,
        )
        self._views[view_id] = envelope

        lease_id = next(self._lease_id_counter)
        lease = Lease(lease_id, self.owner_id, self.namespace_identity, consumer_id, view_id)
        self._leases[lease_id] = lease
        return lease, envelope

    def get_view_via_lease(self, lease):
        """The authority gate: a released lease, a lease from a closed
        owner, or a lease whose view no longer belongs to the current
        epoch never authorizes access -- this is checked EVERY time, not
        just at acquisition."""
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
        """Idempotent: releasing an already-released lease is a harmless
        no-op (documented single outcome), never an error."""
        stored = self._leases.get(lease.lease_id)
        if stored is None:
            return "unknown-lease-noop"
        if not stored.active:
            return "already-released-noop"
        stored.active = False
        lease.active = False
        # Drop the view envelope only when no other active lease still
        # references it (a real owner might share one view across leases;
        # C1 keeps this simple -- one view per lease -- so this always
        # drops it here).
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
        """Terminal, idempotent -- Gate C1R Repair B corrected semantics.

        If any lease is still active, close() REFUSES/DEFERS: the owner's
        state is left completely unchanged, the provider is not touched,
        `_views` is not cleared, every active lease keeps authorizing
        access exactly as before -- no partial cleanup of any kind. This
        replaces the prior (incorrect) behavior, which closed the provider
        and cleared views regardless of outstanding leases, silently
        invalidating any consumer that had not yet released.

        Only once `active_lease_count() == 0` does close() actually
        terminate the owner: closes the provider (if any), clears the
        (already-empty, by construction) view registry, and transitions to
        CLOSED. Repeated close() on an already-CLOSED owner remains a
        harmless idempotent no-op."""
        if self.state == STATE_CLOSED:
            return "already-closed-noop"
        outstanding = self.active_lease_count()
        if outstanding > 0:
            return "deferred-active-leases:%d" % outstanding
        if self.provider is not None and self.provider.is_valid():
            self.provider.close()
        self.state = STATE_CLOSED
        self._views.clear()
        return "closed"

    def close_or_raise(self):
        """Convenience wrapper some callers may prefer: raises `OwnerBusy`
        instead of returning a sentinel string when leases are
        outstanding. `close()` itself never raises for this case -- both
        forms are supported, per the brief's 'return/raise one explicit
        documented result' wording."""
        result = self.close()
        if isinstance(result, str) and result.startswith("deferred-active-leases:"):
            raise OwnerBusy(result)
        return result


class ViewBudgets(object):
    def __init__(self, one_family_result_rows, one_snapshot_rows, total_pinned_bytes,
                 estimated_bytes_per_row=256):
        self.one_family_result_rows = one_family_result_rows
        self.one_snapshot_rows = one_snapshot_rows
        self.total_pinned_bytes = total_pinned_bytes
        self.estimated_bytes_per_row = estimated_bytes_per_row

    @classmethod
    def from_qualification_defaults(cls, resource_budgets_module):
        rb = resource_budgets_module
        return cls(
            one_family_result_rows=rb.BUDGET_ONE_FAMILY_RESULT_OCCURRENCE_ROWS,
            one_snapshot_rows=rb.BUDGET_ONE_CONSUMER_SNAPSHOT_OCCURRENCE_ROWS,
            total_pinned_bytes=rb.BUDGET_TOTAL_PINNED_VIEWS_ESTIMATED_BYTES,
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

    Gate C1R Repair D: the prior version only cleared the dict, leaving
    any owner/provider a test scenario had admitted still fully valid and
    reachable through any reference a test still held -- an independent
    test running immediately afterward against a NEW namespace was
    unaffected by this in practice (each test used its own namespace), but
    a reused namespace, or an old owner reference used by mistake, could
    silently observe stale state. Every owner is now guaranteed CLOSED
    (`is_valid() == False` on its provider, if any) before the registry is
    cleared, and any leftover reference a test still holds to it will
    correctly find it unusable.

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
