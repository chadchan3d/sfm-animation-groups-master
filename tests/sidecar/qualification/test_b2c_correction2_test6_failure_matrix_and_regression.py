# -*- coding: utf-8 -*-
"""Astra SECOND correction gate -- Test 6: failure matrix + semantic
regression through the REAL cohort route (F7).

Part A: the failure/diagnostic matrix, calling selection.py's REAL
`select_sidecar_candidate` directly (the exact function F7 corrected) --
unsupported / corrupt / missing-local / missing-shipped / resource-
refusal / pointer-mismatch / valid-shipped-recovery, each checked for the
correct exception classification AND (where applicable) a surviving
structured diagnostic entry.

Part B: re-run of the B2C-A/B2C-B parser/adapter semantic-equivalence
scope matrix (W1/W2, groupFile-wrapper regression) against THIS
(correction2) candidate's real production code paths. W3 remains
explicitly UNKNOWN (its own capture run failed against the wrong
project -- not force-substituted). Python 2.7.5 provides the real ref-
vs-candidate hash comparison; Python 3 is candidate-only structural/
compatibility evidence (parse_targeted_master's own tokenizer cannot run
under Python 3 at all -- see normalizer_compat_adapter.py's docstring).
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile

CORRECTION2_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction2"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"
FIXROOT = CORRECTION2_ROOT + r"\fixtures"
FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
OFFICIAL_ROOT = FIXROOT_B2A + r"\shipped_root_valid"
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
REAL_MASTER_PINNED_SHA256 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
PUBLIC_DOCS = r"C:\Users\Public\Documents"

for p in (CORRECTION2_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

sys.path.insert(0, r"E:\SFM Animation Group Master\tests\sidecar")
try:
    from corruption_helpers import MutableSidecar  # noqa: E402 -- Python 3 only (uses pathlib)
except ImportError:
    MutableSidecar = None

from sfm_master_authority_productionized import selection  # noqa: E402
from sfm_master_authority_productionized import observation  # noqa: E402
from sfm_master_authority_productionized import descriptors  # noqa: E402
from sfm_master_authority_productionized import errors  # noqa: E402
from sfm_master_authority_productionized import pointer as pointer_mod  # noqa: E402
from sfm_master_sidecar import format as fmt  # noqa: E402
import time  # noqa: E402

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

with open(REAL_MASTER_PATH, "rb") as f:
    real_master_bytes = f.read()
real_master_sha = hashlib.sha256(real_master_bytes).hexdigest()
check("baseline.0 real canonical Master matches pinned SHA-256",
      real_master_sha == REAL_MASTER_PINNED_SHA256, real_master_sha)
h0 = observation.observe_master(REAL_MASTER_PATH)

SCRATCH = tempfile.mkdtemp(prefix="b2c_correction2_test6_")


def fresh_shipped_root(*artifact_paths):
    d = os.path.join(SCRATCH, "shipped_%d" % len(os.listdir(SCRATCH)))
    os.makedirs(d)
    for p in artifact_paths:
        shutil.copy(p, os.path.join(d, os.path.basename(p)))
    return d


with open(OFFICIAL_ROOT + r"\official.sfmsidecar", "rb") as f:
    VALID_OFFICIAL_BYTES = f.read()

# ===========================================================================
# Part A: failure/diagnostic matrix, direct real select_sidecar_candidate.
# ===========================================================================
print("\n=== Part A: failure/diagnostic matrix ===")

if MutableSidecar is not None:
    # --- A.1: unsupported format_contract_version (checksum-valid). ---
    ms_unsupported = MutableSidecar(VALID_OFFICIAL_BYTES)
    ms_unsupported.set_header_fields(format_contract_version=9999)
    ms_unsupported.recompute_checksum()
    path_unsupported = os.path.join(SCRATCH, "unsupported.sfmsidecar")
    with open(path_unsupported, "wb") as f:
        f.write(ms_unsupported.bytes())
    root_unsupported = fresh_shipped_root(path_unsupported)
    diag_a1 = []
    try:
        selection.select_sidecar_candidate(h0, shipped_root=root_unsupported, diagnostics=diag_a1)
        outcome_a1 = "admitted"
    except Exception as exc:
        outcome_a1 = type(exc).__name__
    check("A.1 unsupported format_contract_version -> errors.SidecarMissing "
          "(the only shipped candidate is skipped as FormatUnsupported, final classification collapses "
          "to SidecarMissing per this module's own documented contract)", outcome_a1 == "SidecarMissing", outcome_a1)
    check("A.1 a structured diagnostic survived naming the REAL reason (FormatUnsupported), not just "
          "the final collapsed classification", any(
              d.get("event") == "shipped_candidate_skipped" and d.get("reason") == "FormatUnsupported"
              for d in diag_a1), diag_a1)

    # --- A.2: corrupt (structurally broken, checksum-valid so it's not
    # just a checksum-mismatch rejection). ---
    ms_corrupt = MutableSidecar(VALID_OFFICIAL_BYTES)
    ms_corrupt.set_directory_row(fmt.SECTION_GROUP_TABLE, row_count=999999)  # declares far more rows than exist
    ms_corrupt.recompute_checksum()
    path_corrupt = os.path.join(SCRATCH, "corrupt.sfmsidecar")
    with open(path_corrupt, "wb") as f:
        f.write(ms_corrupt.bytes())
    root_corrupt = fresh_shipped_root(path_corrupt)
    diag_a2 = []
    try:
        selection.select_sidecar_candidate(h0, shipped_root=root_corrupt, diagnostics=diag_a2)
        outcome_a2 = "admitted"
    except Exception as exc:
        outcome_a2 = type(exc).__name__
    check("A.2 structurally corrupt (checksum-valid) shipped candidate -> SidecarMissing "
          "(only candidate skipped as SidecarCorrupt)", outcome_a2 == "SidecarMissing", outcome_a2)
    check("A.2 a structured diagnostic survived naming SidecarCorrupt as the real reason", any(
        d.get("event") == "shipped_candidate_skipped" and d.get("reason") == "SidecarCorrupt"
        for d in diag_a2), diag_a2)
else:
    print("[SKIP] A.1/A.2 require Python 3 (corruption_helpers.py uses pathlib) -- "
          "already independently proven under Python 3.10 in this same suite's own history; "
          "A.3-A.7 below do not depend on MutableSidecar and still run under this interpreter.")

# --- A.3: missing local (valid pointer, referenced artifact file
# genuinely absent) -> falls through to a VALID shipped recovery. ---
generated_root_a3 = os.path.join(SCRATCH, "generated_a3")
os.makedirs(os.path.join(generated_root_a3, "sfmsidecar_v1"))
fake_artifact_sha = "1234567890abcdef" * 4
pointer_path_a3 = os.path.join(SCRATCH, "pointer_a3.json")
with open(pointer_path_a3, "w") as f:
    json.dump({
        "master_sha256": h0.sha256, "master_byte_length": len(real_master_bytes),
        "artifact_sha256": fake_artifact_sha, "artifact_relative_path": "sfmsidecar_v1/x.sfmsidecar",
        "format_contract_version": 1, "authority_semantics_version": 1,
    }, f)
# NOTE: the file at derive_artifact_path(generated_root_a3, ptr) is
# deliberately never created -- this IS "missing local."
root_a3 = fresh_shipped_root(OFFICIAL_ROOT + r"\official.sfmsidecar")
diag_a3 = []
result_a3 = selection.select_sidecar_candidate(
    h0, allow_local_candidates=True, local_pointer_path=pointer_path_a3,
    generated_root=generated_root_a3, shipped_root=root_a3, diagnostics=diag_a3,
)
check("A.3 missing local artifact recovers to a VALID shipped candidate (no raw IOError escapes)",
      result_a3.source_kind == selection.SOURCE_SHIPPED, result_a3)
result_a3.provider.close()
check("A.3 a structured diagnostic survived naming the missing-local passive-recovery notice", any(
    d.get("event") == "local_sidecar_missing_passive_notice" for d in diag_a3), diag_a3)

# --- A.4: missing shipped (no local candidate configured at all, shipped
# root exists but has nothing matching). ---
root_a4 = fresh_shipped_root()  # empty
diag_a4 = []
try:
    selection.select_sidecar_candidate(h0, shipped_root=root_a4, diagnostics=diag_a4)
    outcome_a4 = "admitted"
except Exception as exc:
    outcome_a4 = type(exc).__name__
check("A.4 empty shipped root, no local candidate -> SidecarMissing", outcome_a4 == "SidecarMissing", outcome_a4)

# --- A.5: resource refusal (valid artifact, but the request is too
# expensive) -- must be DISTINCT from SidecarMissing/corruption. ---
with open(FIXROOT + r"\astra_two_large_families.sfmsidecar", "rb") as f:
    astra_bytes = f.read()
with open(FIXROOT + r"\astra_two_large_families_master.txt", "rb") as f:
    astra_master_bytes = f.read()
astra_h0 = descriptors.ObservationToken(
    sha256=hashlib.sha256(astra_master_bytes).hexdigest(), byte_length=len(astra_master_bytes),
    observed_at=time.time(), path="<synthetic:astra_two_large_families>",
)
path_a5 = os.path.join(SCRATCH, "astra_a5.sfmsidecar")
shutil.copy(FIXROOT + r"\astra_two_large_families.sfmsidecar", path_a5)
root_a5 = fresh_shipped_root(path_a5)
diag_a5 = []
try:
    selection.select_sidecar_candidate(
        astra_h0, shipped_root=root_a5, diagnostics=diag_a5, runtime_cap_bytes=4 * 1024 * 1024,
        requested_folds_by_consumer={"normalizer": [b"astrafamilyone", b"astrafamilytwo"]},
    )
    outcome_a5 = "admitted"
except errors.ResourceAdmissionRefusal:
    outcome_a5 = "ResourceAdmissionRefusal"
except Exception as exc:
    outcome_a5 = type(exc).__name__
check("A.5 an expensive-but-VALID artifact is refused as ResourceAdmissionRefusal, "
      "explicitly DISTINCT from SidecarMissing/SidecarCorrupt", outcome_a5 == "ResourceAdmissionRefusal", outcome_a5)

# --- A.6: pointer/artifact SHA disagreement (local pointer references a
# real, present file, but that file's ACTUAL bytes don't match the
# pointer's declared artifact_sha256) -> recovers to shipped. ---
generated_root_a6 = os.path.join(SCRATCH, "generated_a6")
os.makedirs(os.path.join(generated_root_a6, "sfmsidecar_v1"))
declared_wrong_sha = "ab" * 32
tampered_path = os.path.join(generated_root_a6, "sfmsidecar_v1", declared_wrong_sha + ".sfmsidecar")
with open(tampered_path, "wb") as f:
    f.write(VALID_OFFICIAL_BYTES)  # real bytes, but their ACTUAL sha256 != declared_wrong_sha
pointer_path_a6 = os.path.join(SCRATCH, "pointer_a6.json")
with open(pointer_path_a6, "w") as f:
    json.dump({
        "master_sha256": h0.sha256, "master_byte_length": len(real_master_bytes),
        "artifact_sha256": declared_wrong_sha, "artifact_relative_path": "sfmsidecar_v1/x.sfmsidecar",
        "format_contract_version": 1, "authority_semantics_version": 1,
    }, f)
root_a6 = fresh_shipped_root(OFFICIAL_ROOT + r"\official.sfmsidecar")
diag_a6 = []
result_a6 = selection.select_sidecar_candidate(
    h0, allow_local_candidates=True, local_pointer_path=pointer_path_a6,
    generated_root=generated_root_a6, shipped_root=root_a6, diagnostics=diag_a6,
)
check("A.6 pointer/artifact SHA disagreement recovers to a VALID shipped candidate",
      result_a6.source_kind == selection.SOURCE_SHIPPED, result_a6)
result_a6.provider.close()
check("A.6 a structured diagnostic survived naming the pointer/artifact disagreement",
      any(d.get("event") == "local_pointer_artifact_disagreement" for d in diag_a6), diag_a6)

# --- A.7: valid shipped recovery, explicit direct case (redundant with
# A.3/A.6's own recovery outcome, called out separately per Section 13's
# own enumeration) -- a genuinely valid local pointer/artifact pair
# succeeds WITHOUT any recovery/diagnostic at all. ---
generated_root_a7 = os.path.join(SCRATCH, "generated_a7")
os.makedirs(os.path.join(generated_root_a7, "sfmsidecar_v1"))
real_official_sha = hashlib.sha256(VALID_OFFICIAL_BYTES).hexdigest()
good_local_path = os.path.join(generated_root_a7, "sfmsidecar_v1", real_official_sha + ".sfmsidecar")
with open(good_local_path, "wb") as f:
    f.write(VALID_OFFICIAL_BYTES)
pointer_path_a7 = os.path.join(SCRATCH, "pointer_a7.json")
with open(pointer_path_a7, "w") as f:
    header = fmt.unpack_header(VALID_OFFICIAL_BYTES[:fmt.HEADER_SIZE], 0)
    json.dump({
        "master_sha256": h0.sha256, "master_byte_length": len(real_master_bytes),
        "artifact_sha256": real_official_sha, "artifact_relative_path": "sfmsidecar_v1/x.sfmsidecar",
        "format_contract_version": header.format_contract_version,
        "authority_semantics_version": header.authority_semantics_version,
    }, f)
diag_a7 = []
result_a7 = selection.select_sidecar_candidate(
    h0, allow_local_candidates=True, local_pointer_path=pointer_path_a7,
    generated_root=generated_root_a7, shipped_root=fresh_shipped_root(), diagnostics=diag_a7,
)
check("A.7 a genuinely valid local pointer+artifact succeeds directly, from SOURCE_LOCAL",
      result_a7.source_kind == selection.SOURCE_LOCAL, result_a7)
result_a7.provider.close()
check("A.7 no recovery diagnostic was needed for a genuinely valid local candidate",
      len(diag_a7) == 0, diag_a7)

shutil.rmtree(SCRATCH, ignore_errors=True)

print("\n=== Part A RESULT: %d/%d ===" % (sum(1 for _, c in RESULTS if c), len(RESULTS)))

# ===========================================================================
# Part B: parser/adapter semantic-equivalence regression, against THIS
# (correction2) candidate's real production code paths.
# ===========================================================================
print("\n=== Part B: semantic-equivalence regression ===")

NORMALIZER_PROD_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py"
)
NORMALIZER_PINNED_SHA256 = "6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e"
NORMALIZER_CANDIDATE_PATH = (
    r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction2_normalizer"
    r"\Rebuild_Control_Groups_Normalizer_B2CB_correction2_candidate.py"
)

with open(NORMALIZER_PROD_PATH, "rb") as f:
    normalizer_prod_bytes = f.read()
normalizer_prod_sha = hashlib.sha256(normalizer_prod_bytes).hexdigest()
check("B.identity.1 production Normalizer matches pinned SHA-256",
      normalizer_prod_sha == NORMALIZER_PINNED_SHA256, normalizer_prod_sha)

with open(NORMALIZER_CANDIDATE_PATH, "rb") as f:
    normalizer_cand_bytes = f.read()
normalizer_cand_sha = hashlib.sha256(normalizer_cand_bytes).hexdigest()
print("[IDENTITY] correction2 candidate Normalizer SHA-256: %s" % normalizer_cand_sha)
check("B.identity.2 candidate Normalizer differs from production (patch applied)",
      normalizer_cand_sha != normalizer_prod_sha)

try:
    unicode  # noqa: F821
    _PY2 = True
except NameError:
    _PY2 = False

if _PY2:
    prod_lines = normalizer_prod_bytes.splitlines()
    cand_lines = normalizer_cand_bytes.splitlines()
else:
    prod_lines = normalizer_prod_bytes.decode("utf-8").splitlines()
    cand_lines = normalizer_cand_bytes.decode("utf-8").splitlines()


def extract(lines, first_line, last_line):
    return "\n".join(lines[first_line - 1: last_line]) + "\n"


PROD_RANGES = [
    (138, 138, "READ_BLOCK"), (604, 605, "ProbeError"), (647, 657, "to_unicode"),
    (659, 671, "ascii_fold"), (1169, 1202, "BufferedChars"), (1204, 1339, "stream_tokens"),
    (1340, 1370, "parse_master_bool_text"), (1373, 1413, "parse_master_rgba_text"),
    (1416, 1723, "parse_targeted_master"),
]
prod_src = "\n\n".join(extract(prod_lines, a, b) for a, b, _ in PROD_RANGES)
import re as _re_module  # noqa: E402
ns_ref = {"re": _re_module}
if not _PY2:
    ns_ref["unicode"] = str
exec(prod_src, ns_ref)
check("B.extract.1 parse_targeted_master extracted from PRODUCTION and exec'd", "parse_targeted_master" in ns_ref)

# correction2's acquire_master_index_via_qualified_authority: lines
# 1501-1602 (established and verified in Test 5, NOT the first
# correction's 1439-1520 range -- the function grew when F3/F4's
# expected_generation parameter and F6/F8's bootstrap-identity call were
# added).
CAND_FUNC_RANGE = (1501, 1602)
cand_func_src = extract(cand_lines, CAND_FUNC_RANGE[0], CAND_FUNC_RANGE[1])
check("B.extract.2 extracted correction2 candidate range starts with the expected def",
      cand_func_src.lstrip().startswith("def acquire_master_index_via_qualified_authority"))

from sfm_master_authority_productionized import broker as broker_mod  # noqa: E402
from sfm_master_authority_productionized import normalizer_compat_adapter as _b2c_normalizer_adapter  # noqa: E402
from sfm_master_authority_productionized import errors as authority_errors  # noqa: E402
ns_cand = {"_b2c_normalizer_adapter": _b2c_normalizer_adapter}


class _FakeAuthorityRuntimeModule(object):
    """Per-case broker isolation for the scope matrix -- NOT a stand-in
    for the real bootstrap import path (that gap is F6/F8, independently
    fixed and proven by Test 5's genuine, non-bypassed bootstrap exec).
    `.get_broker()` here always returns a REAL `broker_mod.Broker`
    instance, so every real admission/atomicity/diagnostic code path
    this scope matrix exercises is the actual corrected implementation --
    only the PER-CASE INSTANCE SELECTION is swapped in, for clean,
    independently-observable provider/ledger counters per case."""
    def __init__(self, broker_instance):
        self._broker_instance = broker_instance

    def get_broker(self, *a, **kw):
        return self._broker_instance


class _FakeQThread(object):
    @staticmethod
    def currentThread():
        return "main"


class _FakeQCoreApplication(object):
    @staticmethod
    def instance():
        return None


class _FakeQtCore(object):
    QThread = _FakeQThread
    QCoreApplication = _FakeQCoreApplication


ns_cand["QtCore"] = _FakeQtCore
# The extracted function body reads these two bootstrap-declared module-
# level constants directly (F4/F6 generation+build-identity checks) --
# extracted verbatim from the SAME candidate file, never retyped.
exec(extract(cand_lines, 159, 160), ns_cand)
exec(cand_func_src, ns_cand)
check("B.extract.3 acquire_master_index_via_qualified_authority extracted from correction2 CANDIDATE and exec'd",
      "acquire_master_index_via_qualified_authority" in ns_cand)


class _AllFolds(object):
    def __contains__(self, x):
        return True


def canon(master):
    return {
        "mapping_count": master["mapping_count"], "destination_count": master["destination_count"],
        "folded": master["folded"], "exact_literals": sorted(master["exact_literals"]),
        "group_sibling_order": master["group_sibling_order"], "group_metadata": master["group_metadata"],
    }


def canon_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


try:
    _text_type = unicode  # noqa: F821
except NameError:
    _text_type = str


def sha_of(obj):
    s = canon_json(obj)
    return hashlib.sha256(s.encode("utf-8") if isinstance(s, _text_type) else s).hexdigest()


COMPONENTS = ["mapping_count", "destination_count", "folded", "exact_literals",
              "group_sibling_order", "group_metadata"]


def run_case(label, wanted_folds, master_path=REAL_MASTER_PATH, shipped_root=OFFICIAL_ROOT,
             expect_admission_refusal=False):
    wanted_folds = list(wanted_folds) if not isinstance(wanted_folds, _AllFolds) else wanted_folds
    ref = ns_ref["parse_targeted_master"](master_path, wanted_folds, validate_conflicts=False) if _PY2 else None

    b = broker_mod.Broker(api_version="b2c-b-correction2-%s" % label)
    ns_cand["_b2c_authority_runtime"] = _FakeAuthorityRuntimeModule(b)

    if expect_admission_refusal:
        try:
            ns_cand["acquire_master_index_via_qualified_authority"](
                master_path, wanted_folds, shipped_root=shipped_root,
            )
            check("case.%s expected an admission refusal but acquisition SUCCEEDED" % label, False, "did not raise")
        except (authority_errors.ViewAdmissionRefused, authority_errors.ResourceAdmissionRefusal) as _exc:
            check("case.%s correctly refuses an unrealistic full-corpus request (%s)"
                  % (label, type(_exc).__name__), True)
        counters = b.provider_counters()
        check("case.%s current_open_provider_count == 0 after a refused acquisition "
              "(provider still closed even though admission failed)" % label,
              counters["current_open_provider_count"] == 0, counters)
        return None, ref, None, counters, b

    cand, cand_lease = ns_cand["acquire_master_index_via_qualified_authority"](
        master_path, wanted_folds, shipped_root=shipped_root,
    )
    check("case.%s corrected function returned a real lease" % label,
          cand_lease is not None and b.outstanding_lease_count() == 1, b.outstanding_lease_count())
    b.release_view_lease(cand_lease)
    check("case.%s releasing the lease at 'command completion' zeroes outstanding leases" % label,
          b.outstanding_lease_count() == 0, b.outstanding_lease_count())
    counters = b.provider_counters()

    if ref is None:
        cand_ok = (
            isinstance(cand.get("mapping_count"), int) and cand["mapping_count"] > 0
            and isinstance(cand.get("destination_count"), int) and cand["destination_count"] > 0
            and isinstance(cand.get("folded"), dict) and isinstance(cand.get("exact_literals"), set)
            and isinstance(cand.get("group_sibling_order"), dict) and isinstance(cand.get("group_metadata"), dict)
            and u"<ROOT>" in cand["group_sibling_order"]
        )
        print("[CASE %s] (Python 3, candidate-only) mapping_count=%d destination_count=%d "
              "folds_requested=%s provider_opens=%d peak=%d current=%d" % (
                  label, cand["mapping_count"], cand["destination_count"],
                  "ALL" if isinstance(wanted_folds, _AllFolds) else len(wanted_folds),
                  counters["total_provider_opens"], counters["peak_open_provider_count"],
                  counters["current_open_provider_count"]))
        check("case.%s candidate output is structurally well-formed (Python 3, no reference)" % label, cand_ok)
        check("case.%s current_open_provider_count == 0 after acquisition" % label,
              counters["current_open_provider_count"] == 0, counters)
        return cand_ok, None, cand, counters, b

    ref_c, cand_c = canon(ref), canon(cand)
    per_component = {}
    ok = True
    for comp in COMPONENTS:
        h1, h2 = sha_of(ref_c[comp]), sha_of(cand_c[comp])
        per_component[comp] = (h1 == h2)
        ok = ok and (h1 == h2)
    combined_ok = sha_of(ref_c) == sha_of(cand_c)
    ok = ok and combined_ok
    print("[CASE %s] mapping_count=%d/%d destination_count=%d/%d provider_opens=%d peak=%d current=%d" % (
        label, ref["mapping_count"], cand["mapping_count"], ref["destination_count"], cand["destination_count"],
        counters["total_provider_opens"], counters["peak_open_provider_count"], counters["current_open_provider_count"]))
    check("case.%s combined structure hash matches exactly" % label, combined_ok,
          per_component if not combined_ok else None)
    check("case.%s current_open_provider_count == 0 after acquisition" % label,
          counters["current_open_provider_count"] == 0, counters)
    return ok, ref, cand, counters, b


# --- 6A: full canonical Master, all real folds -- expected admission
# refusal (already-qualified resource gate), never TXT/silent-truncation. ---
sidecar_contract_mod = __import__("sfm_master_authority_productionized.sidecar_contract", fromlist=["x"])
sidecar_contract_mod.ensure_loaded()
_provider_for_enum = sidecar_contract_mod._provider_module.BoundedProvider.open_path(
    OFFICIAL_ROOT + r"\official.sfmsidecar", real_master_sha)
try:
    all_real_folds = set(ns_ref["ascii_fold"](occ["literal"]) if _PY2 else occ["literal"].lower()
                          for occ in _provider_for_enum.iter_occurrences())
finally:
    _provider_for_enum.close()
check("6A.0 discovered a plausible number of distinct folds", len(all_real_folds) > 100000, len(all_real_folds))
run_case("6A_full_corpus", all_real_folds, expect_admission_refusal=True)

# --- 6B: small targeted literal/fold sets. ---
if _PY2:
    def fold(lit):
        return ns_ref["ascii_fold"](lit)
else:
    def fold(lit):
        return lit.lower().encode("utf-8") if isinstance(lit, str) else lit.lower()

REAL_LITERALS = ["left", "right", "Left PupilDown", "Right PupilDown", "Left PupilGrow"]
NONEXISTENT_LITERAL = "ThisControlDoesNotExistAnywhereInTheMaster_XYZ123"
small_sets = {
    "6B_known_exact_literals": set(fold(l) for l in REAL_LITERALS),
    "6B_unknown_literal": set([fold(NONEXISTENT_LITERAL)]),
    "6B_left_right": set([fold("left"), fold("right")]),
    "6B_mixed_known_and_unknown": set(fold(l) for l in REAL_LITERALS) | set([fold(NONEXISTENT_LITERAL)]),
}
for label, folds in small_sets.items():
    run_case(label, folds)

# --- 6C/6D: real W1/W2 command-scope captures. W3 is explicitly UNKNOWN
# (per its own historical capture status -- not force-substituted). ---
w1_path = os.path.join(PUBLIC_DOCS, "SFM_R2_W1_FoxRealWorkload.json")
w2_path = os.path.join(PUBLIC_DOCS, "SFM_R2_W2_SixTargetRealWorkload.json")

with open(w1_path) as f:
    w1 = json.load(f)
check("6C.0 W1 capture's own recorded Master SHA matches pinned value",
      w1["master"]["sha256"] == REAL_MASTER_PINNED_SHA256)
w1_folds = set(w1["workload"]["unique_folded_vocabulary"])
run_case("6C_W1_single_shot_single_target_Fox", w1_folds)

with open(w2_path) as f:
    w2 = json.load(f)
check("6C.1 W2 capture's own recorded Master SHA matches pinned value",
      w2["master"]["sha256"] == REAL_MASTER_PINNED_SHA256)
w2_folds = set(w2["workload"]["union_folded_vocabulary"])
run_case("6C_W2_six_target_union", w2_folds)

print("\n[NOTE 6D] W3 (72-shot) remains explicitly UNKNOWN -- its own stored capture recorded a "
      "failed run against the wrong project (expected 72 shots, found 11). Not force-substituted "
      "with synthetic data; W3 equivalence is simply not established by this or any prior gate.")

# --- groupFile-wrapper regression, against a structurally different
# synthetic fixture (deep_hierarchy: 61 nested groups, generic root). ---
print("\n=== groupFile wrapper regression ===")
from sfm_master_authority_productionized import normalizer_compat_adapter as adapter  # noqa: E402
from sfm_master_authority_productionized import sidecar_contract  # noqa: E402
sidecar_contract.ensure_loaded()

with open(FIXROOT + r"\deep_hierarchy.sfmsidecar", "rb") as f:
    deep_bytes = f.read()
with open(FIXROOT + r"\deep_hierarchy_master.txt", "rb") as f:
    deep_master_bytes = f.read()
deep_sha = hashlib.sha256(deep_master_bytes).hexdigest()
gp = sidecar_contract._provider_module.BoundedProvider.open_path(FIXROOT + r"\deep_hierarchy.sfmsidecar", deep_sha)
try:
    groups = list(gp.iter_groups())
    root_level = [g for g in groups if g["parent_path"] is None]
    check("wrapper.1 synthetic fixture's provider exposes exactly one root-level group",
          len(root_level) == 1, root_level)
    check("wrapper.2 that root-level group is literally named 'groupFile'",
          len(root_level) == 1 and root_level[0]["name"] == u"groupFile", root_level)
    all_synth_folds = set(ns_ref["ascii_fold"](occ["literal"]) if _PY2 else occ["literal"].lower()
                           for occ in gp.iter_occurrences())
    builder = adapter.build_targeted_master_compatible_projection(all_synth_folds)
    cand_g, _cov, _est = builder(gp)
finally:
    gp.close()
check("wrapper.3 adapter's group_metadata does NOT contain a phantom 'groupFile' entry",
      u"groupFile" not in cand_g["group_metadata"])
check("wrapper.4 adapter's group_metadata count == real provider group count minus the wrapper",
      len(cand_g["group_metadata"]) == len(groups) - 1, (len(cand_g["group_metadata"]), len(groups)))

# --- provider-closed-before-would-be-mutation-boundary: this candidate's
# extracted function never references any DME/native mutation API at all
# (dynamic proof: neither the source text nor the exec'd namespace ever
# names a mutation symbol), and every run_case above already confirmed
# current_open_provider_count == 0 immediately after acquisition -- i.e.
# strictly BEFORE the point in the real Normalizer where mutation would
# begin (final_report/target processing all run AFTER acquisition
# returns, per the file's own architecture, proven in Test 4 Part B). ---
_mutation_markers = ("CDmeAnimationSet", "AddChannel", "dm.CreateElement", "vs.mutate")
check("mutation.1 the extracted candidate acquisition function references NO native/DME mutation symbol",
      not any(m in cand_func_src for m in _mutation_markers), cand_func_src)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
