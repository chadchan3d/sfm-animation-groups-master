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

# ---------------------------------------------------------------------
# B2C-C Targeted Audit Correction, Section 6: make broker-to-execution
# composition explicit. This does NOT re-qualify B2C-B/the broker's own
# lease/generation logic (already qualified, Corrections 2-6) -- it
# proves the payload the REAL broker hands back for D5 IS, byte-for-
# byte, the exact payload whose downstream native-mutation behavior
# B2C-C already qualified (117+/117+ execution-layer PASS) via the
# direct-provider shortcut every other B2C-C comparison in this project
# uses. `flex_view`/`flex_master_path`/`flex_artifact_path`/
# `flex_master_sha256` are the SAME broker-acquired objects Section
# 10-18's flex-first checks above already established.
# ---------------------------------------------------------------------
print("\n=== Broker-to-execution composition closure (D5) ===")
import canon  # noqa: E402
import production_execution_layer as pel  # noqa: E402
import fake_dme  # noqa: E402
from scenarios import SCENARIOS  # noqa: E402

d5_spec = SCENARIOS["D5_flex_first_ordering"]

# 2+3: canonical-hash the broker-returned payload AND the direct-
# provider Correction6 adapter projection the ordinary D5 execution
# harness (`test_b2c_c_execution_layer_equivalence.py`) actually uses.
direct_provider_master = ap.compute_migrated_master(d5_spec["wanted_folds"], flex_artifact_path, flex_master_sha256)
flex_payload_hash = canon.sha_of(flex_view.payload)
direct_provider_hash = canon.sha_of(direct_provider_master)

# 4: require exact equality.
check("broker_payload_equals_direct_provider_projection (D5) canonical-hashing the REAL broker's "
      "flex_view.payload exactly equals canonical-hashing the direct-provider Correction6 adapter "
      "projection the ordinary D5 execution harness uses -- proves the broker-returned payload IS "
      "the exact payload whose downstream native-mutation behavior B2C-C already qualified",
      flex_payload_hash == direct_provider_hash, (flex_payload_hash, direct_provider_hash))

# 5: run one D5 migrated execution using flex_view.payload DIRECTLY (not
# the direct-provider projection) and require the same mutation-stream/
# final-tree hashes as the direct-provider projection's own run.
_exec_ns, _exec_blocks = pel.build_full_namespace()
_exec_ns["vs"] = fake_dme.FakeVsModule()


class _ClosureFakeCommand(object):
    def __init__(self):
        self.class_totals = {
            "pre_hidden_master_active": 0, "rig_losses": 0, "master_stranded": 0,
            "parent_collapses": 0, "master_normalizations": 0, "master_unknown_unknown": 0,
            "weak_unknown_diagnostics": 0, "ambiguous_losses": 0, "unresolved_owned_drift": 0,
        }
        self.production_mixed_direct_by_target = {}
        self.log_calls = []

    def log(self, msg):
        self.log_calls.append(msg)


def _closure_run_execution(spec, master):
    shot, aset, root, mlog, handles, groups_by_path, controls_by_name = fake_dme.build_world(
        spec["post_groups_spec"], spec["post_control_specs"],
        rig_status=spec["rig_status"], hidden_groups=spec["hidden_groups"])
    rig_context = _exec_ns["discover_rig_context"](shot, aset)
    post = _exec_ns["capture_snapshot_explicit"](shot, aset, "POST", rig_context)
    pre = spec["pre"]
    cmd = _ClosureFakeCommand()
    plan = _exec_ns["preflight_reconciliation_plan_pure"](cmd, pre, post, master, (u"shot1", u"aset1"))
    uniformity_plan = _exec_ns["derive_generic_uniformity_plan"](pre, post, master, plan)
    composer_result = _exec_ns["production_generic_composer"](root, pre, post, master, shot, aset, plan, uniformity_plan)
    final_rig_context = _exec_ns["discover_rig_context"](shot, aset)
    final_tree = _exec_ns["capture_snapshot_explicit"](shot, aset, "FINAL", final_rig_context)
    return {"native_mutation_stream": list(mlog.entries), "final_tree": final_tree, "composer_result": composer_result}


run_via_direct_provider = _closure_run_execution(d5_spec, direct_provider_master)
run_via_broker_payload = _closure_run_execution(d5_spec, flex_view.payload)

check("broker_payload_execution_stream_matches (D5) running the SAME D5 fixture through the real "
      "production_generic_composer with the broker-acquired flex_view.payload as `master` produces "
      "the IDENTICAL native mutation stream as running it with the direct-provider projection",
      canon.sha_of(run_via_direct_provider["native_mutation_stream"]) == canon.sha_of(run_via_broker_payload["native_mutation_stream"]))

check("broker_payload_execution_tree_matches (D5) running the SAME D5 fixture through the real "
      "production_generic_composer with the broker-acquired flex_view.payload as `master` produces "
      "the IDENTICAL final logical control-group tree as running it with the direct-provider "
      "projection", canon.sha_of(run_via_direct_provider["final_tree"]) == canon.sha_of(run_via_broker_payload["final_tree"]))

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))

# B2C-C Targeted Audit Correction, Section 4: a failed check must cause
# a failed process.
if not all(condition for _, condition in RESULTS):
    sys.exit(1)
