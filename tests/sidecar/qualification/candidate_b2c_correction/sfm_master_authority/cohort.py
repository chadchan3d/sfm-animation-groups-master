# -*- coding: utf-8 -*-
"""Finite acquisition/cohort object -- ASTRA_CORRECTED.md Section 4,
R3-B2B Section 2.

One request/cohort ID; one semantic generation; one H0 observation; at
most one open packed provider; one declared finite projection request
set; one H1 observation; explicit success/failure end; deterministic
provider close on every exit -- success, failure, or cancellation alike.

A cohort never remains open waiting for a future UI event, survives idle
dialog time, survives target-mutation time, retains provider backing
after its projections are detached, silently switches source generation,
or silently opens a second provider (`_open_provider_once` refuses a
second call outright).
"""
import itertools
import time

from . import descriptors
from . import errors
from . import observation
from . import selection as selection_mod
from . import sidecar_contract
from . import views

_cohort_id_counter = itertools.count(1)


class Cohort(object):
    STATE_OPEN = "OPEN"
    STATE_PROJECTIONS_BUILT = "PROJECTIONS_BUILT"
    STATE_CLOSED_SUCCESS = "CLOSED_SUCCESS"
    STATE_CLOSED_FAILURE = "CLOSED_FAILURE"
    STATE_CANCELLED = "CANCELLED"

    def __init__(self, master_path, allow_local_candidates=False, local_pointer_path=None,
                 generated_root=None, shipped_root=None, runtime_cap_bytes=None, broker=None,
                 requested_fold_count=0):
        self.cohort_id = next(_cohort_id_counter)
        self.master_path = master_path
        self.allow_local_candidates = allow_local_candidates
        self.local_pointer_path = local_pointer_path
        self.generated_root = generated_root
        self.shipped_root = shipped_root
        self.runtime_cap_bytes = runtime_cap_bytes
        self._broker = broker
        # Astra F2: the aggregate requested fold/literal vocabulary size
        # across every builder_fn this cohort will build, known at
        # construction time (before any I/O) -- forwarded to the
        # preflight/admission layer so a candidate's resource decision
        # reflects the caller's actual requested scale.
        self.requested_fold_count = requested_fold_count
        self.state = self.STATE_OPEN
        self.h0 = None
        self.h1 = None
        self.semantic_generation = None
        self.artifact_identity = None
        self._provider = None
        self.opened_at = time.time()
        self.closed_at = None
        # R3-B2C addition (purely additive, side-channel only): the last
        # selection/preflight instrumentation, captured on both success
        # and failure of _open_provider_once, for qualification/
        # diagnostic reporting -- never affects any return value or
        # exception.
        self.last_selection_instrumentation = None

    def _open_provider_once(self):
        if self._provider is not None:
            raise errors.BrokerInitializationFailed(
                "Cohort %d attempted to open a second provider -- forbidden." % (self.cohort_id,)
            )
        self.h0 = observation.observe_master(self.master_path)
        sidecar_contract.ensure_loaded()

        # R3-B2C CHANGE: select_sidecar_candidate now returns the
        # winning candidate's ALREADY-OPEN provider directly (via the
        # F5-qualified resource_preflight primitive) -- no separate
        # BoundedProvider.open_path call here (unlike the pre-B2C
        # _open_provider_once, which reopened the path selection.py
        # had already fully read/validated, the 5th full read F5's
        # own report documented).
        try:
            selection_result = selection_mod.select_sidecar_candidate(
                h0=self.h0,
                allow_local_candidates=self.allow_local_candidates,
                local_pointer_path=self.local_pointer_path,
                generated_root=self.generated_root,
                shipped_root=self.shipped_root,
                runtime_cap_bytes=self.runtime_cap_bytes,
                requested_fold_count=self.requested_fold_count,
                ledger=self._broker._ledger if self._broker is not None else None,
            )
        except Exception as exc:
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
        """`builder_fns`: {consumer_kind: callable(provider) -> (payload,
        coverage, estimated_bytes)}. Opens the ONE provider, runs every
        builder against it, takes H1, then ALWAYS closes the provider
        before returning -- success, failure, or exception alike."""
        if self.state != self.STATE_OPEN:
            raise errors.BrokerInitializationFailed(
                "Cohort %d.build_projections() called in state %r" % (self.cohort_id, self.state)
            )
        try:
            provider = self._open_provider_once()
            built = {}
            for consumer_kind, builder_fn in builder_fns.items():
                payload, coverage, estimated_bytes = builder_fn(provider)
                built[consumer_kind] = (payload, coverage, estimated_bytes)

            self.h1 = observation.observe_master(self.master_path)
            if self.h1.sha256 != self.h0.sha256:
                raise errors.AuthorityChangedDuringAcquisition(
                    "Cohort %d: Master changed between H0 (%s) and H1 (%s)."
                    % (self.cohort_id, self.h0.sha256, self.h1.sha256)
                )
            if self.h1.sha256 != self.artifact_identity.embedded_source_sha256:
                raise errors.AuthorityChangedDuringAcquisition(
                    "Cohort %d: H1 (%s) does not match the artifact's embedded source_sha256 (%s)."
                    % (self.cohort_id, self.h1.sha256, self.artifact_identity.embedded_source_sha256)
                )

            self.semantic_generation = descriptors.SemanticGeneration(
                effective_master_path=self.master_path,
                master_sha256=self.h1.sha256,
                master_byte_length=self.h1.byte_length,
                authority_semantics_version=self.artifact_identity.authority_semantics_version,
                projection_contract_version=self.artifact_identity.projection_contract_version,
            )

            authorization = views.LiveAuthorizationToken(self.semantic_generation.master_sha256)
            detached_views = {}
            for consumer_kind, (payload, coverage, estimated_bytes) in built.items():
                detached_views[consumer_kind] = views.DetachedView(
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
        """Explicit cancellation before publication -- deterministically
        closes whatever provider is open, if any, and never leaves the
        cohort's own state ambiguous."""
        self.state = self.STATE_CANCELLED
        self._close_provider()
