# -*- coding: utf-8 -*-
"""R3-B2F1F Stage F5: candidate Broker -- mirrors the frozen
sfm_master_authority.broker.Broker's `acquire_cohort`/
`acquire_or_reuse_views`/counter/ledger methods EXACTLY, importing the
REAL, unmodified `memory_accounting`/`view_cache`/`observation`/
`descriptors`/`errors` modules, but constructing the candidate CohortF5
(cohort_f5.py) instead of the frozen Cohort. `acquire_generation` (the
older, non-cohort B2A entry point) is intentionally NOT reproduced here
-- nothing in the F5 fixture matrix exercises it; this candidate's scope
is exactly the acquire_or_reuse_views -> acquire_cohort ->
Cohort.build_projections path every B2F/B2F1 fixture actually uses.

Not a frozen-file edit -- a candidate copy, isolated under
tests/sidecar/qualification/candidate_b2f1f_f5/.
"""
import time

from cohort_f5 import CohortF5

_MAX_DIAGNOSTICS = 32


class BrokerF5(object):
    def __init__(self, api_version, observation_mod, errors_mod, pointer_mod, sidecar_contract_mod,
                 descriptors_mod, views_mod, memory_accounting_mod, view_cache_mod):
        self.api_version = api_version
        self.created_at = time.time()
        self._diagnostics = []

        self._observation = observation_mod
        self._errors = errors_mod
        self._pointer = pointer_mod
        self._sidecar_contract = sidecar_contract_mod
        self._descriptors = descriptors_mod
        self._views = views_mod
        self._memory_accounting = memory_accounting_mod

        self._active_cohort = None
        self._last_known_master_sha256 = None
        self._ledger = memory_accounting_mod.AggregateLedger()
        self._view_cache = view_cache_mod.ViewCache(self._ledger)

        self.current_open_provider_count = 0
        self.peak_open_provider_count = 0
        self.total_provider_opens = 0
        self.total_provider_closes = 0
        self.active_cohort_id = None

        # R3-B2F1F Stage F6 addition (purely additive, side-channel only --
        # does not affect any return value, exception, or existing
        # semantic behavior): a completed Cohort is never otherwise
        # retained by design (matches the frozen Broker's own invariant),
        # so its selection/preflight instrumentation would be lost the
        # instant acquire_cohort() returns. Retained here ONLY so F6's
        # real-SFM launchers can report genuine per-run call counters
        # instead of inferring them from static code analysis alone.
        self.last_cohort_selection_instrumentation = None

    def _record(self, event, detail=None):
        entry = {"event": event, "t": time.time(), "detail": detail}
        self._diagnostics.append(entry)
        if len(self._diagnostics) > _MAX_DIAGNOSTICS:
            del self._diagnostics[0: len(self._diagnostics) - _MAX_DIAGNOSTICS]
        return entry

    def recent_diagnostics(self):
        return list(self._diagnostics)

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

    def cached_view(self, cache_key):
        return self._view_cache.get(cache_key)

    def acquire_cohort(self, master_path, builder_fns, allow_local_candidates=False,
                        local_pointer_path=None, generated_root=None, shipped_root=None,
                        runtime_cap_bytes=None, retries_remaining=1):
        if self._active_cohort is not None and self._active_cohort.state == CohortF5.STATE_OPEN:
            raise self._errors.AuthorityBusy(
                "a cohort is already open (cohort_id=%d) -- request serialized/refused, "
                "never opening a second provider." % (self._active_cohort.cohort_id,)
            )

        cohort = CohortF5(
            master_path, allow_local_candidates, local_pointer_path,
            generated_root, shipped_root, runtime_cap_bytes, broker=self,
            observation_mod=self._observation, errors_mod=self._errors, pointer_mod=self._pointer,
            sidecar_contract_mod=self._sidecar_contract, descriptors_mod=self._descriptors,
            views_mod=self._views,
        )
        self._active_cohort = cohort
        try:
            detached = cohort.build_projections(builder_fns)
        except self._errors.AuthorityChangedDuringAcquisition as exc:
            self.last_cohort_selection_instrumentation = cohort.last_selection_instrumentation
            self._active_cohort = None
            self._record("h0_h1_instability", {"cohort_id": cohort.cohort_id, "detail": str(exc)})
            if retries_remaining > 0:
                return self.acquire_cohort(
                    master_path, builder_fns, allow_local_candidates, local_pointer_path,
                    generated_root, shipped_root, runtime_cap_bytes,
                    retries_remaining=retries_remaining - 1,
                )
            raise
        except Exception:
            self.last_cohort_selection_instrumentation = cohort.last_selection_instrumentation
            self._active_cohort = None
            raise
        else:
            self.last_cohort_selection_instrumentation = cohort.last_selection_instrumentation
            self._active_cohort = None

        new_master_sha256 = cohort.semantic_generation.master_sha256
        if (self._last_known_master_sha256 is not None
                and self._last_known_master_sha256 != new_master_sha256):
            self._view_cache.invalidate_generation(self._last_known_master_sha256)
        self._last_known_master_sha256 = new_master_sha256

        for consumer_kind, view in detached.items():
            pending_key = ("pending", cohort.cohort_id, consumer_kind)
            self._ledger.charge(self._memory_accounting.CATEGORY_PENDING_PROJECTION, pending_key, view.estimated_bytes)
            try:
                self._view_cache.admit(view)
            finally:
                self._ledger.release(self._memory_accounting.CATEGORY_PENDING_PROJECTION, pending_key)

        self._record("cohort_acquired", {
            "cohort_id": cohort.cohort_id,
            "master_sha256": new_master_sha256,
            "views": list(detached.keys()),
        })
        return detached

    def acquire_or_reuse_views(self, master_path, request_specs, allow_local_candidates=False,
                                local_pointer_path=None, generated_root=None, shipped_root=None,
                                runtime_cap_bytes=None):
        h0 = self._observation.observe_master(master_path)
        reused = {}
        missing_specs = {}
        for consumer_kind, (folded_keys, builder_fn) in request_specs.items():
            candidate_key = (h0.sha256, None, frozenset(folded_keys), consumer_kind)
            cached = self._view_cache.get(candidate_key)
            if cached is not None:
                reused[consumer_kind] = cached
            else:
                missing_specs[consumer_kind] = builder_fn

        if not missing_specs:
            self._record("fully_reused_no_provider_open", {"consumers": list(reused.keys())})
            return reused

        acquired = self.acquire_cohort(
            master_path, missing_specs, allow_local_candidates, local_pointer_path,
            generated_root, shipped_root, runtime_cap_bytes,
        )
        acquired.update(reused)
        return acquired
