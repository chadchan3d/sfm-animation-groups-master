# -*- coding: utf-8 -*-
"""R3-B2F1F Stage F5: candidate Cohort -- byte-for-byte identical to the
frozen sfm_master_authority.cohort.Cohort EXCEPT `_open_provider_once`
calls select_sidecar_candidate_f5 (which returns an ALREADY-OPEN
provider) instead of select_sidecar_candidate + a separate
BoundedProvider.open_path call. Every other method (build_projections,
_close_provider, cancel, state machine) is unchanged from the frozen
original. Reuses the REAL, unmodified descriptors/errors/observation/
views modules -- no second authored authority.

Not a frozen-file edit -- a candidate copy, isolated under
tests/sidecar/qualification/candidate_b2f1f_f5/.
"""
import itertools
import time

from selection_f5 import select_sidecar_candidate_f5


class CohortF5(object):
    STATE_OPEN = "OPEN"
    STATE_PROJECTIONS_BUILT = "PROJECTIONS_BUILT"
    STATE_CLOSED_SUCCESS = "CLOSED_SUCCESS"
    STATE_CLOSED_FAILURE = "CLOSED_FAILURE"
    STATE_CANCELLED = "CANCELLED"

    _cohort_id_counter = itertools.count(1)

    def __init__(self, master_path, allow_local_candidates=False, local_pointer_path=None,
                 generated_root=None, shipped_root=None, runtime_cap_bytes=None, broker=None,
                 observation_mod=None, errors_mod=None, pointer_mod=None, sidecar_contract_mod=None,
                 descriptors_mod=None, views_mod=None):
        self.cohort_id = next(CohortF5._cohort_id_counter)
        self.master_path = master_path
        self.allow_local_candidates = allow_local_candidates
        self.local_pointer_path = local_pointer_path
        self.generated_root = generated_root
        self.shipped_root = shipped_root
        self.runtime_cap_bytes = runtime_cap_bytes
        self._broker = broker
        self.state = self.STATE_OPEN
        self.h0 = None
        self.h1 = None
        self.semantic_generation = None
        self.artifact_identity = None
        self._provider = None
        self.opened_at = time.time()
        self.closed_at = None
        self.last_selection_instrumentation = None

        # Real, unmodified authority modules -- passed in explicitly so
        # this candidate module never hardcodes its own import-path
        # assumptions about where the authority package lives.
        self._observation = observation_mod
        self._errors = errors_mod
        self._pointer = pointer_mod
        self._sidecar_contract = sidecar_contract_mod
        self._descriptors = descriptors_mod
        self._views = views_mod

    def _open_provider_once(self):
        if self._provider is not None:
            raise self._errors.BrokerInitializationFailed(
                "Cohort %d attempted to open a second provider -- forbidden." % (self.cohort_id,)
            )
        self.h0 = self._observation.observe_master(self.master_path)
        self._sidecar_contract.ensure_loaded()

        # THE F5 CHANGE: one unified select-and-open call, returning an
        # ALREADY-OPEN provider -- no separate BoundedProvider.open_path
        # call here (unlike the frozen _open_provider_once, which reopens
        # the path selection.py already fully read/validated).
        try:
            selection_result = select_sidecar_candidate_f5(
                h0=self.h0,
                errors_mod=self._errors, pointer_mod=self._pointer,
                sidecar_contract_mod=self._sidecar_contract, descriptors_mod=self._descriptors,
                allow_local_candidates=self.allow_local_candidates,
                local_pointer_path=self.local_pointer_path,
                generated_root=self.generated_root,
                shipped_root=self.shipped_root,
                runtime_cap_bytes=self.runtime_cap_bytes,
            )
        except Exception as exc:
            # R3-B2F1F Stage F6 addition (purely additive): even on
            # refusal, surface whatever CandidateOpenInstrumentation the
            # refused candidate accumulated (attached to the exception by
            # selection_f5.py) -- so F6's launchers can report genuine
            # refusal-path call counters, not just an inferred story.
            self.last_selection_instrumentation = getattr(exc, "instrumentation", None)
            raise
        self.last_selection_instrumentation = selection_result.instrumentation
        provider = selection_result.provider
        self._provider = provider
        self.artifact_identity = selection_result.artifact_identity
        if self._broker is not None:
            self._broker._on_provider_opened(self.cohort_id)
        return provider

    def build_projections(self, builder_fns):
        """Unchanged from the frozen Cohort.build_projections: opens the
        ONE provider, runs every builder against it, takes H1, then
        ALWAYS closes the provider before returning."""
        if self.state != self.STATE_OPEN:
            raise self._errors.BrokerInitializationFailed(
                "Cohort %d.build_projections() called in state %r" % (self.cohort_id, self.state)
            )
        try:
            provider = self._open_provider_once()
            built = {}
            for consumer_kind, builder_fn in builder_fns.items():
                payload, coverage, estimated_bytes = builder_fn(provider)
                built[consumer_kind] = (payload, coverage, estimated_bytes)

            self.h1 = self._observation.observe_master(self.master_path)
            if self.h1.sha256 != self.h0.sha256:
                raise self._errors.AuthorityChangedDuringAcquisition(
                    "Cohort %d: Master changed between H0 (%s) and H1 (%s)."
                    % (self.cohort_id, self.h0.sha256, self.h1.sha256)
                )
            if self.h1.sha256 != self.artifact_identity.embedded_source_sha256:
                raise self._errors.AuthorityChangedDuringAcquisition(
                    "Cohort %d: H1 (%s) does not match the artifact's embedded source_sha256 (%s)."
                    % (self.cohort_id, self.h1.sha256, self.artifact_identity.embedded_source_sha256)
                )

            self.semantic_generation = self._descriptors.SemanticGeneration(
                effective_master_path=self.master_path,
                master_sha256=self.h1.sha256,
                master_byte_length=self.h1.byte_length,
                authority_semantics_version=self.artifact_identity.authority_semantics_version,
                projection_contract_version=self.artifact_identity.projection_contract_version,
            )

            authorization = self._views.LiveAuthorizationToken(self.semantic_generation.master_sha256)
            detached_views = {}
            for consumer_kind, (payload, coverage, estimated_bytes) in built.items():
                detached_views[consumer_kind] = self._views.DetachedView(
                    semantic_generation=self.semantic_generation,
                    artifact_identity=self.artifact_identity,
                    coverage=coverage,
                    projection_contract_version=self.artifact_identity.projection_contract_version,
                    admission_id=self.cohort_id,
                    consumer_kind=consumer_kind,
                    payload=payload,
                    authorization=authorization,
                    estimated_bytes=estimated_bytes,
                )
            self.state = self.STATE_PROJECTIONS_BUILT
            return detached_views
        except Exception:
            self.state = self.STATE_CLOSED_FAILURE
            raise
        finally:
            self._close_provider()

    def _close_provider(self):
        if self._provider is not None:
            try:
                self._provider.close()
            finally:
                self._provider = None
                self.closed_at = time.time()
                if self._broker is not None:
                    self._broker._on_provider_closed(self.cohort_id)
                if self.state == self.STATE_PROJECTIONS_BUILT:
                    self.state = self.STATE_CLOSED_SUCCESS

    def cancel(self):
        self.state = self.STATE_CANCELLED
        self._close_provider()
