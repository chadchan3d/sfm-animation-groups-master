# -*- coding: utf-8 -*-
"""B2C-C execution-layer continuation, Section 2 of the addendum: at
least one TRUE broker-mediated migrated path, before any B2C-C PASS
claim.

Every prior B2C-C plan-layer/execution-layer comparison computed the
"migrated master" by calling `sidecar_contract._provider_module.
BoundedProvider.open_path(...)` DIRECTLY -- one layer below the
qualified broker's own `acquire_or_reuse_views`/lease/generation
machinery. That was a deliberate, disclosed simplification to isolate
the decision/execution-layer comparison from B2C-B's own already-
qualified lease/generation logic (re-testing which would duplicate,
not extend, Corrections 2-6's own qualification).

This file closes that gap with a narrow, targeted sanity case: the
REAL `Broker.acquire_or_reuse_views(...)` -> `Broker.lease_view(...)`
path, proving the actual production integration seam a real Normalizer
command would use reaches the would-be mutation boundary with:
  - source generation (embedded Master SHA-256) == the real compiled
    Master's own SHA-256;
  - sidecar embedded generation == source generation (self-consistent);
  - command generation (`expected_generation`, the pin a real command
    would set once at its own start) agrees with what the broker
    actually returned;
  - a valid, live lease;
  - `provider_counters()["current_open_provider_count"] == 0` at the
    boundary (no leaked open provider);
  - no TXT fallback (the returned payload contains no reference to, or
    result from, `parse_targeted_master`).

This does NOT re-qualify all of B2C-B (Corrections 2-6 already did
that, independently re-audited) -- it proves the ONE thing this
qualification round specifically needs: that the real integration seam
is what would actually feed the execution layer this file's sibling
tests exercise.

Never launches SFM. Read-only with respect to the frozen production
file and the qualified Correction6 candidate.
"""
import hashlib
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CORRECTION6_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction6")
TOOLS_DIR = os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir, "tools")

for p in (os.path.abspath(CORRECTION6_ROOT), os.path.abspath(TOOLS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

from sfm_master_authority_productionized import broker as broker_mod  # noqa: E402
from sfm_master_authority_productionized import normalizer_compat_adapter as adapter  # noqa: E402
from sfm_master_authority_productionized import sidecar_contract  # noqa: E402
sidecar_contract.ensure_loaded()

FIXROOT_AB = os.path.join(CORRECTION6_ROOT, "fixtures_ab")
with open(os.path.join(FIXROOT_AB, "generation_a_master.txt"), "rb") as f:
    MASTER_A_BYTES = f.read()
MASTER_A_SHA256 = hashlib.sha256(MASTER_A_BYTES).hexdigest()
master_path = os.path.join(FIXROOT_AB, "generation_a_master.txt")
shipped_root = os.path.join(FIXROOT_AB, "shipped_both")

b = broker_mod.Broker(api_version="b2c-c-broker-mediated-sanity")

wanted = frozenset([b"left", b"right"])
request_specs = {"normalizer": (wanted, adapter.build_targeted_master_compatible_projection(wanted))}

# A real command pins its OWN expected generation once, at command
# start (Astra F4) -- here, the real compiled Master A's own SHA-256.
COMMAND_EXPECTED_GENERATION = MASTER_A_SHA256

before_counters = b.provider_counters()
detached = b.acquire_or_reuse_views(
    master_path, request_specs, shipped_root=shipped_root,
    expected_generation=COMMAND_EXPECTED_GENERATION,
)
after_acquire_counters = b.provider_counters()

view = detached["normalizer"]
lease = b.lease_view(view)

check("source_generation_matches embedded source generation (view.semantic_generation."
      "master_sha256) matches the real compiled Master A's own SHA-256",
      view.semantic_generation.master_sha256 == MASTER_A_SHA256,
      (view.semantic_generation.master_sha256, MASTER_A_SHA256))

check("sidecar_embedded_generation_matches the sidecar artifact's own embedded source SHA-256 "
      "(artifact_identity.embedded_source_sha256) agrees with the source generation",
      view.artifact_identity.embedded_source_sha256 == MASTER_A_SHA256,
      (view.artifact_identity.embedded_source_sha256, MASTER_A_SHA256))

check("command_generation_agrees the broker's own `expected_generation` pin (what a real "
      "command sets once at start) equals what was actually returned -- acquire_or_reuse_views "
      "would have raised AuthorityChangedDuringAcquisition otherwise",
      view.semantic_generation.master_sha256 == COMMAND_EXPECTED_GENERATION)

check("valid_lease lease_view returned a real, non-None lease object", lease is not None)

check("provider_open_count_zero_at_boundary provider_counters()['current_open_provider_count'] "
      "== 0 at the would-be mutation boundary (the provider is opened transiently during "
      "acquisition and closed before acquire_or_reuse_views returns)",
      after_acquire_counters["current_open_provider_count"] == 0, after_acquire_counters)

check("no_txt_fallback the returned master payload is the qualified adapter's OWN projection "
      "dict shape (mapping_count/destination_count/folded/exact_literals/group_sibling_order/"
      "group_metadata) -- never something parse_targeted_master itself produced",
      set(view.payload.keys()) == {
          "mapping_count", "destination_count", "folded", "exact_literals",
          "group_sibling_order", "group_metadata",
      }, sorted(view.payload.keys()))

check("mapping_content_nonempty the acquired master payload has real content "
      "(mapping_count > 0)", view.payload["mapping_count"] > 0, view.payload["mapping_count"])

b.release_view_lease(lease)
final_counters = b.provider_counters()
check("lease_release_clean provider_counters() still shows zero open providers after the "
      "lease is released (no leak introduced by this sanity test itself)",
      final_counters["current_open_provider_count"] == 0, final_counters)

# ---------------------------------------------------------------------
# B2C-C Final Expansion Fixtures, "Broker-mediated sanity": at least one
# NEW fixture (here: flex-first ordering, D5) must use the REAL
# qualified broker/adapter path rather than the direct BoundedProvider.
# open_path shortcut every other B2C-C comparison in this round used
# (candidate_b2c_c/authority_pair.py's `compute_migrated_master`).
#
# This exercises the SAME b2c_c_master.txt / b2c_c.sfmsidecar authority
# fixture D5_flex_first_ordering's decision/execution comparisons use
# (containing the literal "eye_flex_control"/"eye_bone_control" flex-
# first content), through `Broker.acquire_or_reuse_views` ->
# `Broker.lease_view`, proving the real production integration seam
# also works end-to-end for this round's own new fixture content (not
# just the pre-existing Correction6 "left"/"right" fixture).
# ---------------------------------------------------------------------
_CANDIDATE_B2C_C_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_c")
if os.path.abspath(_CANDIDATE_B2C_C_ROOT) not in sys.path:
    sys.path.insert(0, os.path.abspath(_CANDIDATE_B2C_C_ROOT))
import authority_pair as ap  # noqa: E402

flex_master_path, flex_artifact_path, flex_master_sha256 = ap.load_authority_fixture()
FLEX_SHIPPED_ROOT = os.path.dirname(flex_artifact_path)

flex_wanted = frozenset([b"eye_flex_control", b"eye_bone_control"])
flex_request_specs = {
    "normalizer": (flex_wanted, adapter.build_targeted_master_compatible_projection(flex_wanted)),
}
FLEX_COMMAND_EXPECTED_GENERATION = flex_master_sha256

flex_before_counters = b.provider_counters()
flex_detached = b.acquire_or_reuse_views(
    flex_master_path, flex_request_specs, shipped_root=FLEX_SHIPPED_ROOT,
    expected_generation=FLEX_COMMAND_EXPECTED_GENERATION,
)
flex_after_acquire_counters = b.provider_counters()

flex_view = flex_detached["normalizer"]
flex_lease = b.lease_view(flex_view)

check("flex_source_generation_matches (D5 flex-first fixture) embedded source generation "
      "matches the real compiled b2c_c Master's own SHA-256",
      flex_view.semantic_generation.master_sha256 == flex_master_sha256,
      (flex_view.semantic_generation.master_sha256, flex_master_sha256))

check("flex_sidecar_embedded_generation_matches (D5) the sidecar artifact's own embedded "
      "source SHA-256 agrees with the source generation",
      flex_view.artifact_identity.embedded_source_sha256 == flex_master_sha256,
      (flex_view.artifact_identity.embedded_source_sha256, flex_master_sha256))

check("flex_command_generation_agrees (D5) the broker's own `expected_generation` pin equals "
      "what was actually returned",
      flex_view.semantic_generation.master_sha256 == FLEX_COMMAND_EXPECTED_GENERATION)

check("flex_valid_lease (D5) lease_view returned a real, non-None lease object",
      flex_lease is not None)

check("flex_provider_open_count_zero_at_boundary (D5) provider_counters()"
      "['current_open_provider_count'] == 0 at the would-be mutation boundary",
      flex_after_acquire_counters["current_open_provider_count"] == 0, flex_after_acquire_counters)

check("flex_no_txt_fallback (D5) the returned master payload is the qualified adapter's OWN "
      "projection dict shape -- never something parse_targeted_master itself produced",
      set(flex_view.payload.keys()) == {
          "mapping_count", "destination_count", "folded", "exact_literals",
          "group_sibling_order", "group_metadata",
      }, sorted(flex_view.payload.keys()))

check("flex_mapping_content_nonempty (D5) the acquired master payload has real content "
      "(mapping_count > 0)", flex_view.payload["mapping_count"] > 0, flex_view.payload["mapping_count"])

check("flex_folded_contains_eye_controls (D5) the acquired payload's `folded` vocabulary "
      "genuinely contains this fixture's own flex-first literals, not generic left/right content",
      {u"eye_flex_control", u"eye_bone_control"}.issubset(set(flex_view.payload["folded"].keys())),
      sorted(flex_view.payload["folded"].keys()))

b.release_view_lease(flex_lease)
flex_final_counters = b.provider_counters()
check("flex_lease_release_clean (D5) provider_counters() still shows zero open providers after "
      "the lease is released", flex_final_counters["current_open_provider_count"] == 0, flex_final_counters)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
