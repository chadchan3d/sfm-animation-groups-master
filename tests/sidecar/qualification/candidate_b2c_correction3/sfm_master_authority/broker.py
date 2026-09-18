# -*- coding: utf-8 -*-
"""The resident Broker object -- B2A minimum resident state,
ASTRA_CORRECTED.md Sections 2/3.

Permitted resident state in B2A: resolver configuration/binding
(implicit -- resolver takes explicit params, nothing cached here);
supported contract versions (not yet enforced beyond what the FINAL
R3-A2B validator itself checks); package/build/API identity
(`api_version`); request serialization/initialization state (owned by
`runtime.py`, not duplicated here); a small bounded diagnostic-record
list.

Explicitly NEVER held as instance state: a packed provider; a decoded
Master graph; any consumer DME/model/rig state; dialog ownership; a
detached semantic-view cache. `acquire_generation()` opens, validates,
and closes/discards a provider entirely within one call -- it is never
returned to the caller and never retained past that call.
"""
import time

from . import cohort as cohort_mod
from . import descriptors
from . import errors
from . import memory_accounting
from . import observation
from . import resolver as resolver_mod
from . import selection as selection_mod
from . import view_cache as view_cache_mod

_MAX_DIAGNOSTICS = 32


class Broker(object):
    def __init__(self, api_version):
        self.api_version = api_version
        self.created_at = time.time()
        self._diagnostics = []

        # --- R3-B2B: finite-cohort / detached-view / aggregate-memory state ---
        self._active_cohort = None
        self._last_known_master_sha256 = None
        self._ledger = memory_accounting.AggregateLedger()
        self._view_cache = view_cache_mod.ViewCache(self._ledger)

        # Diagnostic counters (ASTRA_CORRECTED.md Section 6 qualification
        # requirement): current/peak open-provider count, total opens/
        # closes, active cohort ID. Updated ONLY by Cohort's own real
        # open/close calls via `_on_provider_opened`/`_on_provider_closed`
        # -- always-active production instrumentation, not test-only
        # monkeypatching.
        self.current_open_provider_count = 0
        self.peak_open_provider_count = 0
        self.total_provider_opens = 0
        self.total_provider_closes = 0
        self.active_cohort_id = None

        # Astra F6 correction: the legacy identity-only acquire_generation
        # path previously opened/closed its own provider entirely outside
        # the Cohort/_active_cohort busy-check machinery -- a reentrant
        # call (a side effect during one acquisition calling back into
        # the other) could therefore open a SECOND provider concurrently,
        # violating the "at most one open provider" invariant that
        # acquire_cohort's own busy-check otherwise guarantees. Serialized
        # here via the same kind of explicit in-progress flag, checked by
        # BOTH acquire_generation and acquire_cohort.
        self._legacy_acquisition_in_progress = False

    def _record(self, event, detail=None):
        entry = {"event": event, "t": time.time(), "detail": detail}
        self._diagnostics.append(entry)
        if len(self._diagnostics) > _MAX_DIAGNOSTICS:
            del self._diagnostics[0: len(self._diagnostics) - _MAX_DIAGNOSTICS]
        return entry

    def recent_diagnostics(self):
        return list(self._diagnostics)

    def resolve_effective_master(self, ifm_dll_path, valve_mod_dir=None):
        resolved = resolver_mod.resolve_effective_master(ifm_dll_path, valve_mod_dir)
        self._record("resolved_master", {"outcome": resolved.outcome, "path": resolved.path})
        return resolved

    def observe(self, master_path):
        obs = observation.observe_master(master_path)
        self._record("observed", {"sha256": obs.sha256, "byte_length": obs.byte_length})
        return obs

    def acquire_generation(self, master_path, allow_local_candidates=False, local_pointer_path=None,
                            generated_root=None, shipped_root=None, runtime_cap_bytes=None):
        """The full B2A acceptance flow: H0 -> select candidate -> validate
        (via sidecar_contract, provider closed internally) -> H1 -> require
        H0 == H1 == embedded source generation -> return an
        AcquiredGeneration. Retries the WHOLE H0..H1 cycle at most once,
        total, for this call, on AuthorityChangedDuringAcquisition
        (ASTRA_CORRECTED.md Section 17 -- "at most one H0/H1 retry TOTAL").
        No mutation occurs anywhere in this method."""
        last_exc = None
        for attempt in range(2):
            try:
                return self._acquire_generation_once(
                    master_path, allow_local_candidates, local_pointer_path,
                    generated_root, shipped_root, runtime_cap_bytes,
                )
            except errors.AuthorityChangedDuringAcquisition as exc:
                last_exc = exc
                self._record("h0_h1_instability", {"attempt": attempt + 1, "detail": str(exc)})
                continue
        raise last_exc

    def _acquire_generation_once(self, master_path, allow_local_candidates, local_pointer_path,
                                  generated_root, shipped_root, runtime_cap_bytes):
        # Astra F6: serialize against BOTH a concurrently-open cohort and
        # a reentrant call into this same legacy path -- never a second
        # simultaneously-open provider via either route.
        if self._active_cohort is not None and self._active_cohort.state == cohort_mod.Cohort.STATE_OPEN:
            raise errors.AuthorityBusy(
                "a cohort is already open (cohort_id=%d) -- legacy acquire_generation refused "
                "rather than opening a second provider." % (self._active_cohort.cohort_id,)
            )
        if self._legacy_acquisition_in_progress:
            raise errors.AuthorityBusy(
                "a legacy acquire_generation() call is already in progress on this broker -- "
                "refusing a reentrant second call rather than opening a second provider."
            )
        self._legacy_acquisition_in_progress = True
        try:
            h0 = observation.observe_master(master_path)

            selection_result = selection_mod.select_sidecar_candidate(
                h0=h0,
                allow_local_candidates=allow_local_candidates,
                local_pointer_path=local_pointer_path,
                generated_root=generated_root,
                shipped_root=shipped_root,
                runtime_cap_bytes=runtime_cap_bytes,
                diagnostics=self._diagnostics,
                ledger=self._ledger,
            )
            # R3-B2C fix: select_sidecar_candidate now returns the winning
            # candidate's ALREADY-OPEN provider (selection_result.provider),
            # unlike the pre-B2C version which only ever returned an
            # identity (its own internal provider was opened-and-closed
            # inside sidecar_contract.validate_selected_artifact). This
            # method's contract is explicitly "identity only, no retained
            # provider, no mutation" -- close it immediately, matching that
            # contract exactly; never leak it past this method. Uses getattr
            # (not a direct attribute access) because this is also reached
            # by test doubles/fakes that duck-type only the fields they
            # need (e.g. offline H0/H1-instability probes that stub
            # select_sidecar_candidate entirely) -- .provider stays
            # optional for any caller, matching SelectionResult's own
            # additive/backward-compatible field design.
            provider = getattr(selection_result, "provider", None)
            if provider is not None:
                provider.close()
        finally:
            self._legacy_acquisition_in_progress = False

        h1 = observation.observe_master(master_path)
        if h1.sha256 != h0.sha256:
            raise errors.AuthorityChangedDuringAcquisition(
                "Master changed between H0 (%s) and H1 (%s) during sidecar acquisition."
                % (h0.sha256, h1.sha256)
            )
        if h1.sha256 != selection_result.artifact_identity.embedded_source_sha256:
            raise errors.AuthorityChangedDuringAcquisition(
                "H1 (%s) does not match the selected artifact's own embedded source_sha256 (%s)."
                % (h1.sha256, selection_result.artifact_identity.embedded_source_sha256)
            )

        semantic_generation = descriptors.SemanticGeneration(
            effective_master_path=master_path,
            master_sha256=h1.sha256,
            master_byte_length=h1.byte_length,
            authority_semantics_version=selection_result.artifact_identity.authority_semantics_version,
            projection_contract_version=selection_result.artifact_identity.projection_contract_version,
        )

        self._record("generation_acquired", {
            "master_sha256": semantic_generation.master_sha256,
            "artifact_sha256": selection_result.artifact_identity.sidecar_artifact_sha256,
            "source": selection_result.source_kind,
        })

        return descriptors.AcquiredGeneration(
            semantic_generation=semantic_generation,
            artifact_identity=selection_result.artifact_identity,
            source_kind=selection_result.source_kind,
        )

    # -----------------------------------------------------------------
    # R3-B2B: finite acquisition/cohort + detached-view + aggregate memory
    # -----------------------------------------------------------------

    def _on_provider_opened(self, cohort_id):
        self.current_open_provider_count += 1
        self.total_provider_opens += 1
        if self.current_open_provider_count > self.peak_open_provider_count:
            self.peak_open_provider_count = self.current_open_provider_count
        self.active_cohort_id = cohort_id

    def _on_provider_closed(self, cohort_id):
        self.current_open_provider_count -= 1
        self.total_provider_closes += 1
        if self.current_open_provider_count <= 0:
            self.active_cohort_id = None

    def provider_counters(self):
        return {
            "current_open_provider_count": self.current_open_provider_count,
            "peak_open_provider_count": self.peak_open_provider_count,
            "total_provider_opens": self.total_provider_opens,
            "total_provider_closes": self.total_provider_closes,
            "active_cohort_id": self.active_cohort_id,
        }

    def ledger_snapshot(self):
        return self._ledger.snapshot()

    def view_cache_entry_count(self):
        return self._view_cache.entry_count()

    def acquire_cohort(self, master_path, builder_fns, allow_local_candidates=False,
                        local_pointer_path=None, generated_root=None, shipped_root=None,
                        runtime_cap_bytes=None, retries_remaining=1, requested_folds_by_consumer=None,
                        expected_generation=None):
        """The B2B finite-cohort acquisition flow. `builder_fns` is a dict
        of {consumer_kind: callable(provider) -> (payload, coverage,
        estimated_bytes)}. Serializes cohort construction on this
        (single, canonical) broker: a second acquisition attempted while
        one cohort is already OPEN raises AuthorityBusy rather than
        opening a second provider -- this is the only way "concurrency"
        can arise in a single-threaded process (a REENTRANT call, e.g. a
        builder_fn side effect calling back into acquire_cohort).

        `requested_folds_by_consumer` (Astra second correction gate F2):
        {consumer_kind: iterable_of_folded_keys} -- the REAL per-consumer
        requested fold sets for this batch, forwarded to the resource-
        admission layer for packed-per-family cumulative reservation
        (never an average/count-only proxy). If omitted (None), derived
        automatically from each builder_fn's own `.declared_request_
        folds` attribute where present (normalizer_compat_adapter.py's
        builders set this); callers that pass an explicit value always
        take precedence over this fallback.

        `expected_generation` (Astra F4): if given, every view this call
        returns must carry EXACTLY this `semantic_generation.master_
        sha256` -- checked here, at the SAME point the internal H0/H1
        cross-check already runs, so a caller pinning a command-level
        generation can never silently receive a different one even on a
        cache-bypassing direct call.

        `retries_remaining` (Astra F4 -- ONE total retry budget): when
        called directly, defaults to 1 (matching the pre-existing H0/H1-
        instability contract). When called FROM `acquire_or_reuse_views`
        (which owns a single combined retry budget covering BOTH H0/H1
        instability AND post-acquisition generation-mismatch), this is
        explicitly passed as 0 so this method never retries on its own
        -- all retry decisions surface to that single outer caller,
        never two independently-stacking budgets."""
        if requested_folds_by_consumer is None:
            requested_folds_by_consumer = dict(
                (consumer_kind, getattr(fn, "declared_request_folds", frozenset()))
                for consumer_kind, fn in builder_fns.items()
            )
        if self._active_cohort is not None and self._active_cohort.state == cohort_mod.Cohort.STATE_OPEN:
            raise errors.AuthorityBusy(
                "a cohort is already open (cohort_id=%d) -- request serialized/refused, "
                "never opening a second provider." % (self._active_cohort.cohort_id,)
            )
        if self._legacy_acquisition_in_progress:
            # Astra F6: the legacy identity-only path is serialized
            # against acquire_cohort too, symmetrically.
            raise errors.AuthorityBusy(
                "a legacy acquire_generation() call is already in progress on this broker -- "
                "acquire_cohort refused rather than opening a second provider."
            )

        cohort = cohort_mod.Cohort(
            master_path, allow_local_candidates, local_pointer_path,
            generated_root, shipped_root, runtime_cap_bytes, broker=self,
            requested_folds_by_consumer=requested_folds_by_consumer,
        )
        self._active_cohort = cohort
        try:
            detached = cohort.build_projections(builder_fns)
        except errors.AuthorityChangedDuringAcquisition as exc:
            self._active_cohort = None
            self._record("h0_h1_instability", {"cohort_id": cohort.cohort_id, "detail": str(exc)})
            if retries_remaining > 0:
                return self.acquire_cohort(
                    master_path, builder_fns, allow_local_candidates, local_pointer_path,
                    generated_root, shipped_root, runtime_cap_bytes,
                    retries_remaining=retries_remaining - 1,
                    requested_folds_by_consumer=requested_folds_by_consumer,
                    expected_generation=expected_generation,
                )
            raise
        except Exception:
            self._active_cohort = None
            raise
        else:
            self._active_cohort = None

        new_master_sha256 = cohort.semantic_generation.master_sha256

        # Astra F4: explicit command/view generation binding -- checked
        # BEFORE any cache mutation, so a mismatch never gets a chance to
        # publish anything (consistent with F3's "no partial cache
        # mutations" requirement).
        if expected_generation is not None and new_master_sha256 != expected_generation:
            self._record("expected_generation_mismatch", {
                "cohort_id": cohort.cohort_id, "expected": expected_generation, "actual": new_master_sha256,
            })
            if retries_remaining > 0:
                return self.acquire_cohort(
                    master_path, builder_fns, allow_local_candidates, local_pointer_path,
                    generated_root, shipped_root, runtime_cap_bytes,
                    retries_remaining=retries_remaining - 1,
                    requested_folds_by_consumer=requested_folds_by_consumer,
                    expected_generation=expected_generation,
                )
            raise errors.AuthorityChangedDuringAcquisition(
                "acquire_cohort: command pinned to expected generation %r, but this acquisition "
                "produced generation %r -- refusing to publish or return it."
                % (expected_generation, new_master_sha256)
            )

        if (self._last_known_master_sha256 is not None
                and self._last_known_master_sha256 != new_master_sha256):
            self._view_cache.invalidate_generation(self._last_known_master_sha256)
        self._last_known_master_sha256 = new_master_sha256

        # Astra F3: ATOMIC batch publication -- compute/verify/charge the
        # WHOLE batch as one unit (view_cache.admit_batch), never one
        # `admit()` call per view (which let a later view's own eviction
        # silently orphan an earlier view from the SAME batch that the
        # caller still received). If the whole batch cannot be admitted,
        # `admit_batch` raises BEFORE touching the cache/ledger at all --
        # nothing here needs to roll anything back.
        views_list = list(detached.values())
        pending_keys = [("pending", cohort.cohort_id, consumer_kind) for consumer_kind in detached.keys()]
        for pending_key, view in zip(pending_keys, views_list):
            self._ledger.charge(memory_accounting.CATEGORY_PENDING_PROJECTION, pending_key, view.estimated_bytes)
        try:
            self._view_cache.admit_batch(views_list)
        finally:
            for pending_key in pending_keys:
                self._ledger.release(memory_accounting.CATEGORY_PENDING_PROJECTION, pending_key)

        self._record("cohort_acquired", {
            "cohort_id": cohort.cohort_id,
            "master_sha256": new_master_sha256,
            "views": list(detached.keys()),
        })
        return detached

    def cached_view(self, cache_key):
        return self._view_cache.get(cache_key)

    def lease_view(self, view):
        """Astra F3: the canonical, broker-level entry point a real
        consumer uses to take explicit, trackable ownership of a
        detached view for the duration of one operation/command --
        never relying on the mere fact that it holds a Python reference
        to `view.payload`. Returns a views.ViewLease; the caller MUST
        eventually pass it to release_lease(), deterministically, on
        command completion, cancellation, failure, or dialog/operation
        close."""
        return self._view_cache.acquire_lease(view)

    def release_view_lease(self, lease):
        return self._view_cache.release_lease(lease)

    def outstanding_lease_count(self):
        return self._view_cache.outstanding_lease_count()

    def acquire_or_reuse_views(self, master_path, request_specs, allow_local_candidates=False,
                                local_pointer_path=None, generated_root=None, shipped_root=None,
                                runtime_cap_bytes=None, retries_remaining=1, expected_generation=None):
        """`request_specs`: {consumer_kind: (frozenset_of_folded_keys,
        builder_fn)}. Checks the view cache FIRST using a cheap H0
        observation alone (no provider open) -- if every requested
        consumer_kind already has a live, covering cached view for the
        CURRENT generation, returns them all without opening a provider
        at all. Otherwise falls through to one real `acquire_cohort()`
        call covering exactly the missing/stale consumers -- never one
        provider open per consumer, always at most one for the whole
        batch.

        NOTE: the candidate cache key uses `projection_contract_version
        = None`, matching the FINAL R3-A2B header format's current
        reality (this field does not yet exist in the header and is
        always None everywhere in this package) -- a real, populated
        projection_contract_version would need this pre-check taught how
        to predict it before this shortcut remains correct.

        `expected_generation` (Astra F4): the COMMAND's own pinned
        expected source generation (e.g. the Normalizer's `self.
        master_hash` at command start) -- if given, EVERY view this call
        returns (reused AND freshly acquired alike) must carry exactly
        this `semantic_generation.master_sha256`. Distinct from, and in
        ADDITION to, the internal h0-vs-acquired-batch cross-check below
        (that check only proves internal self-consistency for ONE
        acquisition; this one proves the result matches what the
        COMMAND, across its whole lifetime, actually expects -- e.g. a
        pure cache-hit with zero fresh acquisition would never otherwise
        be checked against the command's own pin at all). Do NOT treat
        either hash check as a file lock -- both are content-hash
        observations with the documented edit-then-exact-restore blind
        spot already established in B2A; they detect drift, they do not
        prevent it.

        Astra F4 correction (ONE total retry budget, re-affirmed):
        `retries_remaining` is the SOLE retry budget for this entire
        operation, covering BOTH the internal H0/H1-instability failure
        class AND the mixed-generation / expected-generation-mismatch
        failure class -- `acquire_cohort` is always called with
        `retries_remaining=0` from here, so it never independently
        retries; every retry decision is made exactly once, at this single
        outer level, never stacking two separate budgets."""
        h0 = observation.observe_master(master_path)
        reused = {}
        missing_specs = {}
        missing_folds_by_consumer = {}
        for consumer_kind, (folded_keys, builder_fn) in request_specs.items():
            candidate_key = (h0.sha256, None, frozenset(folded_keys), consumer_kind)
            cached = self._view_cache.get(candidate_key)
            if cached is not None:
                reused[consumer_kind] = cached
            else:
                missing_specs[consumer_kind] = builder_fn
                missing_folds_by_consumer[consumer_kind] = frozenset(folded_keys)

        if not missing_specs:
            if expected_generation is not None and h0.sha256 != expected_generation:
                self._record("expected_generation_mismatch_cache_only", {
                    "expected": expected_generation, "actual": h0.sha256,
                })
                if retries_remaining > 0:
                    return self.acquire_or_reuse_views(
                        master_path, request_specs, allow_local_candidates, local_pointer_path,
                        generated_root, shipped_root, runtime_cap_bytes,
                        retries_remaining=retries_remaining - 1, expected_generation=expected_generation,
                    )
                raise errors.AuthorityChangedDuringAcquisition(
                    "acquire_or_reuse_views: command pinned to expected generation %r, but the "
                    "fully-cached result (no fresh acquisition needed) is generation %r."
                    % (expected_generation, h0.sha256)
                )
            self._record("fully_reused_no_provider_open", {"consumers": list(reused.keys())})
            return reused

        try:
            acquired = self.acquire_cohort(
                master_path, missing_specs, allow_local_candidates, local_pointer_path,
                generated_root, shipped_root, runtime_cap_bytes,
                retries_remaining=0,  # single combined budget owned here -- see docstring
                requested_folds_by_consumer=missing_folds_by_consumer,
                # Independent-audit BLOCKER A fix: this call previously
                # never forwarded `expected_generation` at all, so
                # acquire_cohort's OWN pre-publication mismatch check
                # (lines ~305-327 above -- which already runs BEFORE
                # `_view_cache.invalidate_generation`/`admit_batch`, i.e.
                # already correctly ordered) was always skipped here --
                # acquire_cohort would happily invalidate the old
                # generation and publish the freshly-acquired one to the
                # SHARED cache, and only AFTER that publication had
                # already happened did this method's own post-hoc
                # `acquired_generations` check (below) notice the
                # mismatch and reject the RETURN VALUE -- but the cache
                # mutation itself was never undone. Forwarding
                # `expected_generation` here means the SAME existing
                # check now actually runs where it was designed to: a
                # mismatch is rejected inside acquire_cohort itself,
                # strictly BEFORE any cache invalidation or publication
                # occurs, so wrong-generation authority can no longer
                # mutate shared cache state at all, partially or
                # otherwise. No second/redundant generation system was
                # added; this is the exact wiring the existing check
                # already required.
                expected_generation=expected_generation,
            )
        except errors.AuthorityChangedDuringAcquisition:
            if retries_remaining > 0:
                return self.acquire_or_reuse_views(
                    master_path, request_specs, allow_local_candidates, local_pointer_path,
                    generated_root, shipped_root, runtime_cap_bytes,
                    retries_remaining=retries_remaining - 1, expected_generation=expected_generation,
                )
            raise

        acquired_generations = set(
            view.semantic_generation.master_sha256 for view in acquired.values()
        )
        expected_for_batch = expected_generation if expected_generation is not None else h0.sha256
        if acquired_generations and (expected_for_batch not in acquired_generations or len(acquired_generations) != 1):
            self._record("mixed_generation_partial_reuse_discarded", {
                "expected_generation": expected_for_batch,
                "acquired_generations": sorted(acquired_generations),
                "consumers": list(acquired.keys()),
            })
            if retries_remaining > 0:
                return self.acquire_or_reuse_views(
                    master_path, request_specs, allow_local_candidates, local_pointer_path,
                    generated_root, shipped_root, runtime_cap_bytes,
                    retries_remaining=retries_remaining - 1, expected_generation=expected_generation,
                )
            raise errors.AuthorityChangedDuringAcquisition(
                "acquire_or_reuse_views: partial cache reuse observed generation(s) %r while the "
                "freshly-acquired batch expected generation %r -- refusing to return a mixed-"
                "generation result." % (sorted(acquired_generations), expected_for_batch)
            )

        acquired.update(reused)
        return acquired
