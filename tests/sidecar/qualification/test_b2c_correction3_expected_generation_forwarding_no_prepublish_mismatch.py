# -*- coding: utf-8 -*-
"""Independent-audit targeted correction -- BLOCKER A + BLOCKER B
regression probe.

Name states both bugs this test directly encodes:
  - expected-generation-forwarding / no-prepublish-mismatch (BLOCKER A):
    `acquire_or_reuse_views()` must forward `expected_generation` into
    its `acquire_cohort()` call, so a mismatch is rejected BEFORE any
    cache invalidation/publication, never after.
  - valid-B-sidecar command-A rejection (BLOCKER B): the decisive test
    uses REAL, compiled, validated sidecars for BOTH generation A and
    generation B, placed in the SAME shipped root, so B is genuinely
    available -- `errors.SidecarMissing` must NEVER be accepted as
    satisfying the mismatch-rejection requirement; only an explicit
    generation-mismatch classification (`AuthorityChangedDuringAcquisition`)
    is acceptable.

Astra Narrow Issue E: every path here is derived from this file's own
location (`__file__`) -- no hardcoded `E:\\SFM Animation Group Master\\...`
anywhere in this file.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
CORRECTION3_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction3")
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")

for p in (CORRECTION3_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from sfm_master_authority_productionized import broker as broker_mod  # noqa: E402
from sfm_master_authority_productionized import normalizer_compat_adapter as adapter  # noqa: E402
from sfm_master_authority_productionized import errors  # noqa: E402
from sfm_master_authority_productionized import view_cache as view_cache_mod  # noqa: E402

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

FIXROOT = os.path.join(CORRECTION3_ROOT, "fixtures_ab")
with open(os.path.join(FIXROOT, "manifest.json")) as f:
    MANIFEST = json.load(f)
SHARED_SHIPPED_ROOT = MANIFEST["shared_shipped_root"]

with open(MANIFEST["generation_a"]["master_path"], "rb") as f:
    MASTER_A_BYTES = f.read()
with open(MANIFEST["generation_b"]["master_path"], "rb") as f:
    MASTER_B_BYTES = f.read()
GEN_A = MANIFEST["generation_a"]["master_sha256"]
GEN_B = MANIFEST["generation_b"]["master_sha256"]
check("fixtures.0 generation A and B have distinct source hashes", GEN_A != GEN_B, (GEN_A, GEN_B))

SCRATCH = tempfile.mkdtemp(prefix="b2c_correction3_genbinding_")
MUTABLE_MASTER = os.path.join(SCRATCH, "master.txt")

WANTED = frozenset([b"left", b"right"])
REQUEST_SPECS = {"normalizer": (WANTED, adapter.build_targeted_master_compatible_projection(WANTED))}

# ---------------------------------------------------------------------
# Instrumentation: count REAL publication events (ViewCache.admit_batch
# calls that actually reach the charge/insert step) and REAL cohort-
# acquisition attempts (Broker.acquire_cohort calls), process-wide for
# the duration of this file.
# ---------------------------------------------------------------------
_orig_admit_batch = view_cache_mod.ViewCache.admit_batch
_publication_count = [0]


def _counting_admit_batch(self, views):
    result = _orig_admit_batch(self, views)
    if views:
        _publication_count[0] += 1
    return result


view_cache_mod.ViewCache.admit_batch = _counting_admit_batch

_orig_acquire_cohort = broker_mod.Broker.acquire_cohort
_cohort_attempt_count = [0]


def _counting_acquire_cohort(self, *a, **kw):
    _cohort_attempt_count[0] += 1
    return _orig_acquire_cohort(self, *a, **kw)


broker_mod.Broker.acquire_cohort = _counting_acquire_cohort


def snapshot(b):
    return {
        "last_known_master_sha256": b._last_known_master_sha256,
        "view_cache_entry_count": b.view_cache_entry_count(),
        "view_cache_keys": sorted(str(k) for k in b._view_cache._entries.keys()),
        "ledger_total_retained": sum(b.ledger_snapshot().values()),
    }


def write_master(content_bytes):
    with open(MUTABLE_MASTER, "wb") as f:
        f.write(content_bytes)


# ===========================================================================
# Case 1: command expected A + current A + sidecar A -> PASS.
# ===========================================================================
write_master(MASTER_A_BYTES)
b1 = broker_mod.Broker(api_version="test-genbinding-case1")
before1 = snapshot(b1)
pub_before1, retry_before1 = _publication_count[0], _cohort_attempt_count[0]
result1 = b1.acquire_or_reuse_views(
    MUTABLE_MASTER, REQUEST_SPECS, shipped_root=SHARED_SHIPPED_ROOT, expected_generation=GEN_A,
)
after1 = snapshot(b1)
pub_after1, retry_after1 = _publication_count[0], _cohort_attempt_count[0]
check("case1.0 command A + current A + sidecar A succeeds", "normalizer" in result1, result1)
check("case1.1 result view carries generation A",
      result1["normalizer"].semantic_generation.master_sha256 == GEN_A,
      result1["normalizer"].semantic_generation.master_sha256)
check("case1.2 exactly one publication occurred", pub_after1 - pub_before1 == 1, pub_after1 - pub_before1)
check("case1.3 broker _last_known_master_sha256 is now A", after1["last_known_master_sha256"] == GEN_A, after1)
print("[case1] before=%s after=%s publications=%d cohort_attempts=%d" % (
    before1, after1, pub_after1 - pub_before1, retry_after1 - retry_before1))
b1.release_view_lease(b1.lease_view(result1["normalizer"]))

# ===========================================================================
# Case 2 (DECISIVE): command expected A + current B + VALID sidecar B ->
# must reject on generation mismatch specifically, never SidecarMissing.
# ===========================================================================
write_master(MASTER_B_BYTES)
b2 = broker_mod.Broker(api_version="test-genbinding-case2")
before2 = snapshot(b2)
pub_before2, retry_before2 = _publication_count[0], _cohort_attempt_count[0]
try:
    b2.acquire_or_reuse_views(
        MUTABLE_MASTER, REQUEST_SPECS, shipped_root=SHARED_SHIPPED_ROOT, expected_generation=GEN_A,
    )
    outcome2 = "admitted"
except Exception as exc:
    outcome2 = "%s: %s" % (type(exc).__name__, exc)
after2 = snapshot(b2)
pub_after2, retry_after2 = _publication_count[0], _cohort_attempt_count[0]
print("[case2] outcome=%s before=%s after=%s publications=%d cohort_attempts=%d" % (
    outcome2, before2, after2, pub_after2 - pub_before2, retry_after2 - retry_before2))
check("case2.0 (DECISIVE) rejects specifically on generation mismatch "
      "(AuthorityChangedDuringAcquisition) -- SidecarMissing is NOT an acceptable PASS",
      outcome2.startswith("AuthorityChangedDuringAcquisition"), outcome2)
check("case2.1 valid sidecar B was genuinely available in the shipped root (proves this "
      "is a real generation-mismatch rejection, not an absent-B fallback)",
      os.path.exists(os.path.join(SHARED_SHIPPED_ROOT, "generation_b.sfmsidecar")))
check("case2.2 B was NOT published into the cache (entry count unchanged)",
      after2["view_cache_entry_count"] == before2["view_cache_entry_count"], (before2, after2))
check("case2.3 broker _last_known_master_sha256 was NOT mutated to B (prior state preserved)",
      after2["last_known_master_sha256"] == before2["last_known_master_sha256"], (before2, after2))
check("case2.4 no publication occurred", pub_after2 - pub_before2 == 0, pub_after2 - pub_before2)
check("case2.5 exactly one bounded total retry budget was consumed (not two independently "
      "stacking retries)", retry_after2 - retry_before2 <= 2, retry_after2 - retry_before2)

# ===========================================================================
# Case 3: A -> B -> A. Command pinned to A throughout. B exists/valid but
# cannot publish while pinned to A; returning to A succeeds normally.
# ===========================================================================
write_master(MASTER_A_BYTES)
b3 = broker_mod.Broker(api_version="test-genbinding-case3")
r3a = b3.acquire_or_reuse_views(
    MUTABLE_MASTER, REQUEST_SPECS, shipped_root=SHARED_SHIPPED_ROOT, expected_generation=GEN_A,
)
check("case3.0 initial A acquisition (pinned A) succeeds", "normalizer" in r3a)
lease3a = b3.lease_view(r3a["normalizer"])

write_master(MASTER_B_BYTES)
try:
    b3.acquire_or_reuse_views(
        MUTABLE_MASTER, REQUEST_SPECS, shipped_root=SHARED_SHIPPED_ROOT, expected_generation=GEN_A,
    )
    outcome3b = "admitted"
except errors.AuthorityChangedDuringAcquisition as exc:
    outcome3b = "AuthorityChangedDuringAcquisition: %s" % exc
check("case3.1 while still pinned to A, current B cannot be acquired/published",
      outcome3b.startswith("AuthorityChangedDuringAcquisition"), outcome3b)

write_master(MASTER_A_BYTES)
try:
    r3a2 = b3.acquire_or_reuse_views(
        MUTABLE_MASTER, REQUEST_SPECS, shipped_root=SHARED_SHIPPED_ROOT, expected_generation=GEN_A,
    )
    outcome3c = "admitted"
except Exception as exc:
    outcome3c = "%s: %s" % (type(exc).__name__, exc)
    r3a2 = None
check("case3.2 A->B->A: returning to A succeeds under normal bounded retry/freshness rules",
      outcome3c == "admitted", outcome3c)
if r3a2 is not None:
    check("case3.3 the restored-A result carries generation A",
          r3a2["normalizer"].semantic_generation.master_sha256 == GEN_A)
    b3.release_view_lease(b3.lease_view(r3a2["normalizer"]))
b3.release_view_lease(lease3a)

# ===========================================================================
# Case 4: cache contains valid A (leased/live), current source becomes B.
# Command expected A: must not return stale A as if current, must not
# publish B before mismatch handling.
# ===========================================================================
write_master(MASTER_A_BYTES)
b4 = broker_mod.Broker(api_version="test-genbinding-case4")
r4a = b4.acquire_or_reuse_views(
    MUTABLE_MASTER, REQUEST_SPECS, shipped_root=SHARED_SHIPPED_ROOT, expected_generation=GEN_A,
)
check("case4.0 initial A acquisition succeeds and is cached", "normalizer" in r4a)
before4 = snapshot(b4)

write_master(MASTER_B_BYTES)
try:
    b4.acquire_or_reuse_views(
        MUTABLE_MASTER, REQUEST_SPECS, shipped_root=SHARED_SHIPPED_ROOT, expected_generation=GEN_A,
    )
    outcome4 = "admitted"
except errors.AuthorityChangedDuringAcquisition as exc:
    outcome4 = "AuthorityChangedDuringAcquisition: %s" % exc
after4 = snapshot(b4)
check("case4.1 cache contains valid A, source becomes B, command expected A -> rejects "
      "(never silently returns stale A as if it were current, never publishes B)",
      outcome4.startswith("AuthorityChangedDuringAcquisition"), outcome4)
check("case4.2 view_cache state is unchanged by the rejected attempt",
      after4["view_cache_entry_count"] == before4["view_cache_entry_count"], (before4, after4))

view_cache_mod.ViewCache.admit_batch = _orig_admit_batch
broker_mod.Broker.acquire_cohort = _orig_acquire_cohort
shutil.rmtree(SCRATCH, ignore_errors=True)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
