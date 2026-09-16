# -*- coding: utf-8 -*-
"""B2A generation-descriptor types -- the B1 four-identity separation
(ASTRA_CORRECTED.md Section 6).

B2A scope: semantic generation (#1) and artifact identity (#2) are fully
implemented and returned by the broker. Coverage (#3) is schema-only --
no consumer views are built in B2A. Live authorization (#4) is a single
observation/token type (H0/H1) only; cached descriptor equality is NEVER
treated as fresh authorization -- every freshness boundary takes a NEW
observation.
"""


class SemanticGeneration(object):
    """Identity #1: exact Master content SHA + compatible authority/
    projection semantics. Immutable once constructed."""
    __slots__ = (
        "effective_master_path", "master_sha256", "master_byte_length",
        "authority_semantics_version", "projection_contract_version",
    )

    def __init__(self, effective_master_path, master_sha256, master_byte_length,
                 authority_semantics_version, projection_contract_version):
        self.effective_master_path = effective_master_path
        self.master_sha256 = master_sha256
        self.master_byte_length = master_byte_length
        self.authority_semantics_version = authority_semantics_version
        self.projection_contract_version = projection_contract_version

    def same_semantic_generation_as(self, other):
        """master_sha256 equality is the whole test -- format/authority/
        projection version compatibility is checked separately (during
        selection/validation), never folded into this equality itself."""
        return other is not None and self.master_sha256 == other.master_sha256

    def __repr__(self):
        return "SemanticGeneration(master_sha256=%r, byte_length=%r)" % (
            self.master_sha256, self.master_byte_length,
        )


class ArtifactIdentity(object):
    """Identity #2: artifact SHA + format/integrity identity of one
    specific byte-build. NOT part of semantic-generation equality
    (ASTRA_CORRECTED.md Section 9) -- two different artifact SHAs can
    validly share one semantic generation."""
    __slots__ = (
        "sidecar_artifact_sha256", "format_contract_version",
        "authority_semantics_version", "projection_contract_version",
        "embedded_source_sha256", "embedded_source_byte_length", "producer",
    )

    def __init__(self, sidecar_artifact_sha256, format_contract_version,
                 authority_semantics_version, projection_contract_version,
                 embedded_source_sha256, embedded_source_byte_length, producer=None):
        self.sidecar_artifact_sha256 = sidecar_artifact_sha256
        self.format_contract_version = format_contract_version
        self.authority_semantics_version = authority_semantics_version
        self.projection_contract_version = projection_contract_version
        self.embedded_source_sha256 = embedded_source_sha256
        self.embedded_source_byte_length = embedded_source_byte_length
        self.producer = producer

    def __repr__(self):
        return "ArtifactIdentity(artifact_sha256=%r, embedded_source_sha256=%r)" % (
            self.sidecar_artifact_sha256, self.embedded_source_sha256,
        )


class CoverageDescriptor(object):
    """Identity #3: schema only in B2A. Real per-fold Hit/FoldConflict/
    MasterUnknown coverage tagging is B2B's responsibility (no consumer
    views are built here)."""
    __slots__ = ("covered_keys",)

    def __init__(self, covered_keys=None):
        self.covered_keys = frozenset(covered_keys or ())


class ObservationToken(object):
    """Identity #4: one exact-byte Master observation (an H0 or an H1).
    Deliberately not cached/reused as 'still fresh' by anything in this
    package -- every freshness boundary takes a brand-new observation."""
    __slots__ = ("sha256", "byte_length", "observed_at", "path")

    def __init__(self, sha256, byte_length, observed_at, path):
        self.sha256 = sha256
        self.byte_length = byte_length
        self.observed_at = observed_at
        self.path = path

    def __repr__(self):
        return "ObservationToken(sha256=%r, byte_length=%r)" % (self.sha256, self.byte_length)


class AcquiredGeneration(object):
    """The B2A acceptance result: a semantic generation plus the artifact
    identity validated against it. No provider, no decoded graph, no
    consumer view is attached -- both are already closed/undelivered by
    the time this object is returned to a caller."""
    __slots__ = ("semantic_generation", "artifact_identity", "source_kind")

    def __init__(self, semantic_generation, artifact_identity, source_kind):
        self.semantic_generation = semantic_generation
        self.artifact_identity = artifact_identity
        self.source_kind = source_kind

    def __repr__(self):
        return "AcquiredGeneration(master_sha256=%r, artifact_sha256=%r, source=%r)" % (
            self.semantic_generation.master_sha256,
            self.artifact_identity.sidecar_artifact_sha256,
            self.source_kind,
        )
