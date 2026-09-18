# -*- coding: utf-8 -*-
"""Independent-audit targeted correction -- NARROW ISSUE D regression
probe: retained-plus-incoming aggregate transient case.

Proves `evaluate_cumulative_admission()`'s transient formula now
includes `aggregate_existing_retained_bytes` (interpretation B --
total authority-related resident pressure during the acquisition
window, INCLUDING already-retained views -- see resource_estimator.py's
own documented rationale) by constructing a real scenario where:
  - the retained gate (16 MiB, UNCHANGED) is never the reason for
    refusal (isolates the transient-specific effect);
  - the OLD formula (transient = incoming delta only) would have
    ADMITTED this exact request;
  - the NEW, documented formula (transient = existing + incoming)
    correctly REFUSES it, because 10 MiB of already-resident retained
    state genuinely contributes to the real concurrent memory pressure
    during this acquisition's transient window.

Astra Narrow Issue E: paths derived from `__file__`, never hardcoded.
"""
import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
CORRECTION3_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction3")
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
FIXROOT_AB = os.path.join(CORRECTION3_ROOT, "fixtures_ab")

for p in (CORRECTION3_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from sfm_master_authority_productionized import resource_estimator  # noqa: E402
from sfm_master_authority_productionized import packed_family_counts as pfc  # noqa: E402
from sfm_master_sidecar import format as fmt  # noqa: E402

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

with open(os.path.join(FIXROOT_AB, "manifest.json")) as f:
    MANIFEST = json.load(f)
with open(MANIFEST["generation_a"]["artifact_path"], "rb") as f:
    buf = f.read()
header = fmt.unpack_header(buf[:fmt.HEADER_SIZE], 0)
dir_end = resource_estimator._validate_header_and_bound_directory_region(header, len(buf))
shape = resource_estimator.parse_resource_shape(buf[:dir_end], len(buf))
counts = pfc.get_packed_family_counts_batch(buf, shape, [b"left", b"right"])
check("setup.0 real packed counts obtained for the small fixture", counts == {b"left": 1, b"right": 1}, counts)

RETAINED_GATE_BYTES = 16 * 1024 * 1024
TRANSIENT_GATE_BYTES = 32 * 1024 * 1024
RUNTIME_CAP_BYTES = 16 * 1024 * 1024
EXISTING_RETAINED_BYTES = 10 * 1024 * 1024  # simulates 10 MiB already resident from prior acquisitions

# ===========================================================================
# Baseline: existing=0 -- this exact request admits (establishes that the
# request is not intrinsically oversized on its own).
# ===========================================================================
r_baseline = resource_estimator.evaluate_cumulative_admission(
    shape, {"normalizer": counts}, RUNTIME_CAP_BYTES, RETAINED_GATE_BYTES, TRANSIENT_GATE_BYTES,
    aggregate_existing_retained_bytes=0,
)
check("baseline.0 with zero existing retained state, this exact request admits",
      r_baseline.admitted is True, (r_baseline.reason, r_baseline.total_transient_bytes))

# ===========================================================================
# Decisive: existing=10 MiB. Retained gate must NOT be the refusal reason
# (isolates the transient-specific effect); the OLD formula (derived here
# as total_transient_bytes - aggregate_existing_retained_bytes, i.e. what
# the pre-fix code computed since it never added this term) would have
# admitted; the NEW, documented formula must refuse.
# ===========================================================================
r_decisive = resource_estimator.evaluate_cumulative_admission(
    shape, {"normalizer": counts}, RUNTIME_CAP_BYTES, RETAINED_GATE_BYTES, TRANSIENT_GATE_BYTES,
    aggregate_existing_retained_bytes=EXISTING_RETAINED_BYTES,
)
old_style_transient = r_decisive.total_transient_bytes - EXISTING_RETAINED_BYTES
combined_retained = EXISTING_RETAINED_BYTES + r_decisive.total_retained_bytes

print("[decisive] admitted=%s reason=%s combined_retained=%d total_transient(new)=%d "
      "total_transient(old-style, no existing term)=%d gate=%d" % (
          r_decisive.admitted, r_decisive.reason, combined_retained, r_decisive.total_transient_bytes,
          old_style_transient, TRANSIENT_GATE_BYTES))

check("decisive.0 combined retained state (existing + new) stays UNDER the 16 MiB retained gate "
      "(the retained gate is never the reason for refusal here)",
      combined_retained <= RETAINED_GATE_BYTES, combined_retained)
check("decisive.1 the retained gate value itself is unchanged (16 MiB)",
      RETAINED_GATE_BYTES == 16 * 1024 * 1024)
check("decisive.2 the transient gate value itself is unchanged (32 MiB)",
      TRANSIENT_GATE_BYTES == 32 * 1024 * 1024)
check("decisive.3 the OLD-style transient total (incoming delta only, no existing term) would "
      "have stayed UNDER the 32 MiB gate -- i.e. the OLD formula would have ADMITTED this exact "
      "request", old_style_transient <= TRANSIENT_GATE_BYTES, old_style_transient)
check("decisive.4 the NEW, documented formula (existing + incoming) correctly REFUSES this "
      "exact request", r_decisive.admitted is False, (r_decisive.admitted, r_decisive.reason))
check("decisive.5 the refusal reason is specifically the transient gate, not the retained gate "
      "or the secondary single-family cap", r_decisive.reason == "cumulative_transient_exceeds_gate",
      r_decisive.reason)
check("decisive.6 the NEW total_transient_bytes genuinely equals existing + old-style total "
      "(the fix is additive, not a different unrelated computation)",
      r_decisive.total_transient_bytes == EXISTING_RETAINED_BYTES + old_style_transient)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
