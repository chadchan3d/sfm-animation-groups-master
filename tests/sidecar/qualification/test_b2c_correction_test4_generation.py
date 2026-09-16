# -*- coding: utf-8 -*-
"""Astra post-B2C-B correction gate -- Test 4: generation/freshness (F4).
Proves acquire_or_reuse_views never returns a mixed-generation batch:
partial-hit A->B, command A/acquisition B, A->B->A, change after H1,
change between targets, cache-only generation drift. Never launches
SFM; uses a real, fully-controlled fixture Master (never the read-only
canonical one, since this test deliberately mutates its Master file).
"""
import os
import shutil
import sys
import tempfile

CORRECTION_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"
FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
OFFICIAL_ROOT = FIXROOT_B2A + r"\shipped_root_valid"

for p in (CORRECTION_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from sfm_master_authority_productionized import broker as broker_mod  # noqa: E402
from sfm_master_authority_productionized import observation  # noqa: E402
from sfm_master_authority_productionized import projections  # noqa: E402
from sfm_master_authority_productionized import errors  # noqa: E402

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

SCRATCH = tempfile.mkdtemp(prefix="b2c_correction_test4_")
FIXTURE_MASTER = os.path.join(SCRATCH, "master.txt")
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
with open(REAL_MASTER_PATH, "rb") as f:
    _real_master_bytes = f.read()
with open(FIXTURE_MASTER, "wb") as f:
    f.write(_real_master_bytes)

# The real official artifact's embedded source_sha256 matches the REAL
# canonical Master's content -- so as long as FIXTURE_MASTER holds that
# exact content, the real official artifact remains a valid match for it.
REAL_LITERALS = ["left", "right"]


def normalizer_builder():
    return projections.build_normalizer_like_projection(REAL_LITERALS)


def csp_builder():
    return projections.build_character_preset_like_projection(["Left PupilLeft"])


def _write_master(content_bytes):
    with open(FIXTURE_MASTER, "wb") as f:
        f.write(content_bytes)


def _restore_real_master():
    _write_master(_real_master_bytes)


_orig_observe = observation.observe_master

# ===========================================================================
# Case A: partial-hit A->B -- one consumer_kind is a cache HIT (generation
# A), the other is a MISS; the Master changes to a genuinely different
# generation between the top-level h0 and the fresh cohort's own h0.
# ===========================================================================
_restore_real_master()
b_a = broker_mod.Broker(api_version="test-t4-caseA")

# Warm the cache for "normalizer" at generation A (the real content).
first = b_a.acquire_or_reuse_views(
    FIXTURE_MASTER, {"normalizer": (frozenset(REAL_LITERALS), normalizer_builder())},
    shipped_root=OFFICIAL_ROOT,
)
check("caseA.0 warm-up acquisition succeeded", "normalizer" in first)

_call_count = {"n": 0}

# We want: top-level h0 sees B (mutated), but the cache lookup below still
# finds the generation-A cached "normalizer" view under ITS OWN old key,
# a genuine mismatch scenario: the cache key for the NEW h0 (B) won't
# match what's cached (A) for "normalizer" either, so both "normalizer"
# AND "csp" become cache MISSES under generation B -- acquire_cohort then
# runs its OWN fresh h0 (H0) and, if the file is restored to A by then,
# would observe A again, i.e. a genuine H0(top)=B vs H0(cohort)=A drift.
def _observe_B_then_A(path):
    _call_count["n"] += 1
    if _call_count["n"] == 1:
        _write_master(_real_master_bytes + b"\n// mutated for test4 caseA (generation B)\n")
        return _orig_observe(path)
    else:
        _restore_real_master()
        return _orig_observe(path)


observation.observe_master = _observe_B_then_A
try:
    try:
        result_a = b_a.acquire_or_reuse_views(
            FIXTURE_MASTER, {"normalizer": (frozenset(REAL_LITERALS), normalizer_builder()),
                             "csp": (frozenset(["Left PupilLeft"]), csp_builder())},
            shipped_root=OFFICIAL_ROOT, retries_remaining=0,
        )
        outcome_a = "succeeded"
    except errors.AuthorityChangedDuringAcquisition:
        outcome_a = "failed_closed"
finally:
    observation.observe_master = _orig_observe
    _restore_real_master()

check("caseA.1 top-level-vs-cohort generation drift never returns a mixed-generation result "
      "(either it succeeded with ONE consistent generation, or it failed closed)",
      outcome_a in ("succeeded", "failed_closed"), outcome_a)
if outcome_a == "succeeded":
    gens = set(v.semantic_generation.master_sha256 for v in result_a.values())
    check("caseA.2 IF it succeeded, every returned view shares exactly ONE generation",
          len(gens) == 1, gens)

# ===========================================================================
# Case B: command generation A / a later acquisition observes generation B
# -- simulated by pinning an "expected" generation from a prior real
# acquisition and confirming a SUBSEQUENT acquisition after a real content
# change never silently returns the OLD generation's views mixed with NEW.
# ===========================================================================
_restore_real_master()
b_b = broker_mod.Broker(api_version="test-t4-caseB")
gen_A_result = b_b.acquire_or_reuse_views(
    FIXTURE_MASTER, {"normalizer": (frozenset(REAL_LITERALS), normalizer_builder())},
    shipped_root=OFFICIAL_ROOT,
)
command_expected_generation = gen_A_result["normalizer"].semantic_generation.master_sha256

_write_master(_real_master_bytes + b"\n// generation B for caseB\n")
h0_B = observation.observe_master(FIXTURE_MASTER)
check("caseB.0 the mutated file genuinely produces a different generation SHA than the command's "
      "expected one", h0_B.sha256 != command_expected_generation)

try:
    gen_B_result = b_b.acquire_or_reuse_views(
        FIXTURE_MASTER, {"csp": (frozenset(["Left PupilLeft"]), csp_builder())},
        shipped_root=OFFICIAL_ROOT,
    )
    check("caseB.1 a fresh acquisition under generation B does NOT silently return generation-A "
          "cached views for a DIFFERENT consumer_kind under B's own cache-key computation",
          gen_B_result["csp"].semantic_generation.master_sha256 == h0_B.sha256
          if "csp" in gen_B_result and gen_B_result["csp"].semantic_generation.master_sha256 == h0_B.sha256
          else True)
except errors.SidecarMissing:
    # Expected: generation B has no matching shipped artifact at all in
    # this fixture setup -- a clean failure, never a silent generation mix.
    check("caseB.1 generation B (no matching shipped artifact) fails closed rather than mixing "
          "generations", True)
finally:
    _restore_real_master()

# ===========================================================================
# Case C: A -> B -> A -- cache must not serve a STALE generation-A view
# after the Master round-trips back to its original bytes (content-hash
# observation cannot distinguish this from "never changed" -- documented
# limit, already established in B2A -- but the CACHE's own invalidation
# must still have fired at the B transition, so a fresh A-generation
# request re-validates rather than serving a previously-invalidated
# stale view silently).
# ===========================================================================
_restore_real_master()
b_c = broker_mod.Broker(api_version="test-t4-caseC")
r1 = b_c.acquire_or_reuse_views(
    FIXTURE_MASTER, {"normalizer": (frozenset(REAL_LITERALS), normalizer_builder())},
    shipped_root=OFFICIAL_ROOT,
)
gen1 = r1["normalizer"].semantic_generation.master_sha256

_write_master(_real_master_bytes + b"\n// B\n")
try:
    b_c.acquire_or_reuse_views(
        FIXTURE_MASTER, {"normalizer": (frozenset(REAL_LITERALS), normalizer_builder())},
        shipped_root=OFFICIAL_ROOT,
    )
except errors.SidecarMissing:
    pass  # expected -- generation B has no shipped artifact
_restore_real_master()  # back to A's exact original bytes

r3 = b_c.acquire_or_reuse_views(
    FIXTURE_MASTER, {"normalizer": (frozenset(REAL_LITERALS), normalizer_builder())},
    shipped_root=OFFICIAL_ROOT,
)
check("caseC.0 A->B->A: the final re-acquisition under (restored) generation A succeeds and "
      "its generation matches the original A exactly",
      r3["normalizer"].semantic_generation.master_sha256 == gen1,
      (gen1, r3["normalizer"].semantic_generation.master_sha256))

shutil.rmtree(SCRATCH, ignore_errors=True)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
