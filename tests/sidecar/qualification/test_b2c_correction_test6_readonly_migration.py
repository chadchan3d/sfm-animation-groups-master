# -*- coding: utf-8 -*-
"""R3-B2C-B: read-only migration qualification. Compares the FROZEN
production parse_targeted_master() against the ISOLATED CANDIDATE
Normalizer's new acquire_master_index_via_qualified_authority(), both
extracted VERBATIM (exact line ranges, never retyped) from their
respective hash-identified files, across the required scope matrix
(Section 6), with provider-lifecycle (Section 7), cache/reuse
(Section 8), and groupFile-wrapper regression (Section 10) proofs.

Never launches SFM. Never calls any mutation API (neither extracted
function references dm/vs/ctypes native mutation calls at all -- see
mutation.* checks below for the dynamic proof). Read-only against the
real canonical Master, the real official artifact, and qualification
fixtures throughout.
"""
import hashlib
import json
import os
import sys

# ---------------------------------------------------------------------
# Identities (Section 2) -- re-verified fresh for THIS run.
# ---------------------------------------------------------------------
NORMALIZER_PROD_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py"
)
NORMALIZER_PINNED_SHA256 = "6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e"

NORMALIZER_CANDIDATE_PATH = (
    r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction_normalizer"
    r"\Rebuild_Control_Groups_Normalizer_B2CB_correction_candidate.py"
)

REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
REAL_MASTER_PINNED_SHA256 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"

CANDIDATE_AUTHORITY_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"
FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
OFFICIAL_ROOT = FIXROOT_B2A + r"\shipped_root_valid"
FIXROOT_B2F = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2f\fixtures"

PUBLIC_DOCS = r"C:\Users\Public\Documents"

for p in (CANDIDATE_AUTHORITY_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

with open(NORMALIZER_PROD_PATH, "rb") as f:
    normalizer_prod_bytes = f.read()
normalizer_prod_sha = hashlib.sha256(normalizer_prod_bytes).hexdigest()
check("identity.1 production Normalizer matches pinned SHA-256", normalizer_prod_sha == NORMALIZER_PINNED_SHA256, normalizer_prod_sha)

with open(NORMALIZER_CANDIDATE_PATH, "rb") as f:
    normalizer_cand_bytes = f.read()
normalizer_cand_sha = hashlib.sha256(normalizer_cand_bytes).hexdigest()
print("[IDENTITY] candidate Normalizer SHA-256: %s" % normalizer_cand_sha)
check("identity.2 candidate Normalizer differs from production (patch applied)", normalizer_cand_sha != normalizer_prod_sha)

with open(REAL_MASTER_PATH, "rb") as f:
    master_bytes = f.read()
master_sha = hashlib.sha256(master_bytes).hexdigest()
check("identity.3 real canonical Master matches pinned SHA-256", master_sha == REAL_MASTER_PINNED_SHA256, master_sha)

# ---------------------------------------------------------------------
# Verbatim extraction: parse_targeted_master + deps from the PRODUCTION
# file (unchanged line ranges, already used/verified in B2C-A); the new
# acquire_master_index_via_qualified_authority from the CANDIDATE file.
# ---------------------------------------------------------------------
try:
    unicode  # noqa: F821 -- only defined on Python 2
    _PY2 = True
except NameError:
    _PY2 = False

if _PY2:
    prod_lines = normalizer_prod_bytes.splitlines()  # Python 2.7: bytes IS str already
    cand_lines = normalizer_cand_bytes.splitlines()
else:
    # Python 3: source files are declared ASCII (`# -*- coding: ascii -*-`),
    # so a plain UTF-8 decode is exact and lossless for this content.
    prod_lines = normalizer_prod_bytes.decode("utf-8").splitlines()
    cand_lines = normalizer_cand_bytes.decode("utf-8").splitlines()


def extract(lines, first_line, last_line):
    return "\n".join(lines[first_line - 1: last_line]) + "\n"


PROD_RANGES = [
    (138, 138, "READ_BLOCK"),
    (604, 605, "ProbeError"),
    (647, 657, "to_unicode"),
    (659, 671, "ascii_fold"),
    (1169, 1202, "BufferedChars"),
    (1204, 1339, "stream_tokens"),
    (1340, 1370, "parse_master_bool_text"),
    (1373, 1413, "parse_master_rgba_text"),
    (1416, 1723, "parse_targeted_master"),
]
prod_src = "\n\n".join(extract(prod_lines, a, b) for a, b, _ in PROD_RANGES)

import re as _re_module
ns_ref = {"re": _re_module}
if not _PY2:
    # Same idiom the production file itself already uses at its own top
    # (`try: unicode except NameError: unicode = str`) -- to_unicode()
    # references the `unicode` builtin, which only exists on Python 2;
    # under Python 3, str IS the text/unicode type, so this shim changes
    # no semantics, it only supplies the name.
    ns_ref["unicode"] = str
exec(prod_src, ns_ref)
check("extract.1 parse_targeted_master extracted from PRODUCTION and exec'd", "parse_targeted_master" in ns_ref)

CAND_FUNC_RANGE = (1439, 1520, "acquire_master_index_via_qualified_authority")
cand_func_src = extract(cand_lines, CAND_FUNC_RANGE[0], CAND_FUNC_RANGE[1])
check("extract.2 extracted candidate range starts with the expected def",
      cand_func_src.lstrip().startswith("def acquire_master_index_via_qualified_authority"))

from sfm_master_authority import broker as broker_mod  # noqa: E402
from sfm_master_authority import normalizer_compat_adapter as _b2c_normalizer_adapter  # noqa: E402
from sfm_master_authority import errors as authority_errors  # noqa: E402
ns_cand = {"_b2c_normalizer_adapter": _b2c_normalizer_adapter}


class _FakeAuthorityRuntimeModule(object):
    """Stands in for the candidate's `_b2c_authority_runtime` module
    reference inside the extracted function body -- .get_broker() below
    is bound per-test to a FRESH broker.Broker instance so each scope-
    matrix case gets clean, independently-observable provider counters
    (Section 7/8), rather than sharing one implicit process-global
    broker across every test case in this file."""
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

exec(cand_func_src, ns_cand)
check("extract.3 acquire_master_index_via_qualified_authority extracted from CANDIDATE and exec'd",
      "acquire_master_index_via_qualified_authority" in ns_cand)


class _AllFolds(object):
    def __contains__(self, x):
        return True


def canon(master):
    return {
        "mapping_count": master["mapping_count"],
        "destination_count": master["destination_count"],
        "folded": master["folded"],
        "exact_literals": sorted(master["exact_literals"]),
        "group_sibling_order": master["group_sibling_order"],
        "group_metadata": master["group_metadata"],
    }


def canon_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


try:
    _text_type = unicode  # noqa: F821 -- Python 2.7 only
except NameError:
    _text_type = str


def sha_of(obj):
    s = canon_json(obj)
    return hashlib.sha256(s.encode("utf-8") if isinstance(s, _text_type) else s).hexdigest()


COMPONENTS = ["mapping_count", "destination_count", "folded", "exact_literals",
              "group_sibling_order", "group_metadata"]


def run_case(label, wanted_folds, master_path=REAL_MASTER_PATH, shipped_root=OFFICIAL_ROOT,
             expect_admission_refusal=False):
    """Runs BOTH sides for one scope-matrix case; returns
    (ok, ref, cand, ref_counters, cand_counters). If
    expect_admission_refusal is True, the candidate call is required to
    raise errors.ViewAdmissionRefused (the already-qualified B2B
    retained-gate policy correctly refusing an unrealistically large
    request) -- ref is still computed (parse_targeted_master has no such
    gate) so the CALLER can separately cite the already-established
    full-corpus structural-hash proof from B2C-A instead.

    Under Python 3: parse_targeted_master's own BufferedChars/
    stream_tokens tokenizer treats `open(path, "rb")` output as Python-2
    str-as-bytes throughout (indexing a bytes buffer yields an int under
    Python 3, breaking ch.isspace()/character comparisons) -- the SAME
    real constraint documented in normalizer_compat_adapter.py's module
    docstring and in the B2C-A report. The reference side is therefore
    SKIPPED under Python 3 (not force-translated -- that would carry
    unverified risk, exactly what B2C-A deliberately avoided); only the
    candidate side is exercised and self-consistency-checked. The real
    ref-vs-candidate cross-comparison only ever runs under real Python
    2.7.5 -- see the B2C-B report's interpreter-coverage table."""
    wanted_folds = list(wanted_folds) if not isinstance(wanted_folds, _AllFolds) else wanted_folds

    ref = ns_ref["parse_targeted_master"](master_path, wanted_folds, validate_conflicts=False) if _PY2 else None

    b = broker_mod.Broker(api_version="b2c-b-%s" % label)
    ns_cand["_b2c_authority_runtime"] = _FakeAuthorityRuntimeModule(b)

    if expect_admission_refusal:
        try:
            ns_cand["acquire_master_index_via_qualified_authority"](
                master_path, wanted_folds, shipped_root=shipped_root,
            )
            check("case.%s expected an admission refusal for an unrealistic full-corpus "
                  "request but acquisition SUCCEEDED" % label, False, "did not raise")
        except (authority_errors.ViewAdmissionRefused, authority_errors.ResourceAdmissionRefusal) as _exc:
            # Astra F2 correction: the request-aware estimator now
            # correctly reflects requested_fold_count, so an unrealistic
            # full-corpus request is refused EARLIER, at the cheaper
            # preflight stage (errors.ResourceAdmissionRefusal, before
            # the provider is even opened) rather than only at the
            # later view_cache.admit() stage (ViewAdmissionRefused, after
            # a full open+decode+build) -- a genuine improvement, both
            # are correct "refused" outcomes.
            check("case.%s correctly refuses an unrealistic full-corpus request (%s)"
                  % (label, type(_exc).__name__), True)
        counters = b.provider_counters()
        check("case.%s current_open_provider_count == 0 after a refused acquisition "
              "(provider still closed even though admission failed)" % label,
              counters["current_open_provider_count"] == 0, counters)
        ref_mc = ref["mapping_count"] if ref is not None else -1
        ref_dc = ref["destination_count"] if ref is not None else -1
        print("[CASE %s] ref(py2-only)=%r mapping_count=%d destination_count=%d folds_requested=%s "
              "(candidate correctly refused admission; see B2C-A verify_py27_equivalence.py "
              "for the already-established full-corpus structural-hash proof of the SAME, "
              "hash-unchanged adapter code)" % (
                  label, ref is not None, ref_mc, ref_dc,
                  "ALL" if isinstance(wanted_folds, _AllFolds) else len(wanted_folds)))
        return None, ref, None, counters, b

    # Astra F3: the corrected function now returns (payload, lease).
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
        # Python 3: no reference to compare against (see docstring) --
        # validate the candidate's own structural well-formedness instead.
        cand_ok = (
            isinstance(cand.get("mapping_count"), int) and cand["mapping_count"] > 0
            and isinstance(cand.get("destination_count"), int) and cand["destination_count"] > 0
            and isinstance(cand.get("folded"), dict)
            and isinstance(cand.get("exact_literals"), set)
            and isinstance(cand.get("group_sibling_order"), dict)
            and isinstance(cand.get("group_metadata"), dict)
            and u"<ROOT>" in cand["group_sibling_order"]
        )
        print("[CASE %s] (Python 3, candidate-only) mapping_count=%d destination_count=%d "
              "folds_requested=%s provider_opens=%d peak=%d current=%d" % (
                  label, cand["mapping_count"], cand["destination_count"],
                  "ALL" if isinstance(wanted_folds, _AllFolds) else len(wanted_folds),
                  counters["total_provider_opens"], counters["peak_open_provider_count"],
                  counters["current_open_provider_count"],
              ))
        check("case.%s candidate output is structurally well-formed (Python 3, "
              "no reference available -- see docstring)" % label, cand_ok)
        check("case.%s current_open_provider_count == 0 after acquisition (Section 7 hard gate)" % label,
              counters["current_open_provider_count"] == 0, counters)
        return cand_ok, None, cand, counters, b

    ref_c = canon(ref)
    cand_c = canon(cand)
    per_component = {}
    ok = True
    for comp in COMPONENTS:
        h1 = sha_of(ref_c[comp])
        h2 = sha_of(cand_c[comp])
        per_component[comp] = (h1 == h2)
        ok = ok and (h1 == h2)
    combined_ok = sha_of(ref_c) == sha_of(cand_c)
    ok = ok and combined_ok

    print("[CASE %s] mapping_count=%d/%d destination_count=%d/%d folds_requested=%s "
          "provider_opens=%d peak=%d current=%d" % (
              label, ref["mapping_count"], cand["mapping_count"],
              ref["destination_count"], cand["destination_count"],
              "ALL" if isinstance(wanted_folds, _AllFolds) else len(wanted_folds),
              counters["total_provider_opens"], counters["peak_open_provider_count"],
              counters["current_open_provider_count"],
          ))
    check("case.%s combined structure hash matches exactly" % label, combined_ok,
          per_component if not combined_ok else None)
    check("case.%s current_open_provider_count == 0 after acquisition (Section 7 hard gate)" % label,
          counters["current_open_provider_count"] == 0, counters)
    return ok, ref, cand, counters, b


# ===========================================================================
# SECTION 6.A: full canonical Master, all 124,728 folds
# ===========================================================================
print("\n=== 6.A: Full canonical Master (all folds) ===")
sidecar_contract_mod = __import__("sfm_master_authority.sidecar_contract", fromlist=["x"])
sidecar_contract_mod.ensure_loaded()
_provider_for_enum = sidecar_contract_mod._provider_module.BoundedProvider.open_path(
    OFFICIAL_ROOT + r"\official.sfmsidecar", master_sha)
try:
    all_real_folds = set(ns_ref["ascii_fold"](occ["literal"]) for occ in _provider_for_enum.iter_occurrences())
finally:
    _provider_for_enum.close()
check("6A.0 discovered a plausible number of distinct folds", len(all_real_folds) > 100000, len(all_real_folds))

# A full-corpus request (~95MB estimated payload) legitimately exceeds
# the already-qualified 16 MiB retained-promotion gate -- this is
# CORRECT, intended B2B behavior (view_cache.admit), not a B2C-B defect.
# The exact full-corpus structural-hash equality itself was already
# established in B2C-A (verify_py27_equivalence.py, 15/15 PASS, combined
# hash 3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2)
# against the SAME, hash-unchanged adapter code (see identity table in
# the B2C-B report) -- what's newly proven HERE is that the MIGRATED
# call site correctly propagates that refusal rather than silently
# truncating or corrupting data.
ok_A, ref_A, cand_A, counters_A, broker_A = run_case(
    "6A_full_corpus", all_real_folds, expect_admission_refusal=True)

# ===========================================================================
# SECTION 6.B: small targeted literal/fold sets
# ===========================================================================
print("\n=== 6.B: Small targeted literal/fold sets ===")


def fold(lit):
    return ns_ref["ascii_fold"](lit)


REAL_LITERALS = ["left", "right", "Left PupilDown", "Right PupilDown", "Left PupilGrow"]
NONEXISTENT_LITERAL = "ThisControlDoesNotExistAnywhereInTheMaster_XYZ123"
PUNCTUATION_WHITESPACE_LITERAL = "     =Body="  # real literal found during B2C-A mismatch diagnosis

small_sets = {
    "6B_known_exact_literals": set(fold(l) for l in REAL_LITERALS),
    "6B_unknown_literal": set([fold(NONEXISTENT_LITERAL)]),
    "6B_punctuation_whitespace": set([fold(PUNCTUATION_WHITESPACE_LITERAL)]),
    "6B_left_right": set([fold("left"), fold("right")]),
    "6B_case_variants": set([fold("LEFT"), fold("Left"), fold("lEfT"), fold("left")]),  # collapses to one fold
    "6B_mixed_known_and_unknown": set(fold(l) for l in REAL_LITERALS) | set([fold(NONEXISTENT_LITERAL)]),
}
for label, folds in small_sets.items():
    run_case(label, folds)

# ===========================================================================
# SECTION 6.C / 6.D: real command scopes (W1/W2 captures) + real
# eye/facial controls (W1 IS a real single-target facial-control scope)
# ===========================================================================
print("\n=== 6.C/6.D: Real command-scope captures (W1/W2) ===")

w1_path = os.path.join(PUBLIC_DOCS, "SFM_R2_W1_FoxRealWorkload.json")
w2_path = os.path.join(PUBLIC_DOCS, "SFM_R2_W2_SixTargetRealWorkload.json")
w3_path = os.path.join(PUBLIC_DOCS, "SFM_R2_W3_AllShotsRealWorkload.json")

with open(w1_path) as f:
    w1 = json.load(f)
check("6C.0 W1 capture's own recorded Master SHA matches pinned value", w1["master"]["sha256"] == REAL_MASTER_PINNED_SHA256)
w1_folds = set(w1["workload"]["unique_folded_vocabulary"])
check("6C.1 W1 fold count matches its own recorded unique_fold_count", len(w1_folds) == w1["workload"]["unique_fold_count"])
run_case("6C_W1_single_shot_single_target_Fox", w1_folds)

with open(w2_path) as f:
    w2 = json.load(f)
check("6C.2 W2 capture's own recorded Master SHA matches pinned value", w2["master"]["sha256"] == REAL_MASTER_PINNED_SHA256)
w2_folds = set(w2["workload"]["union_folded_vocabulary"])
check("6C.3 W2 fold count matches its own recorded union_fold_count", len(w2_folds) == w2["workload"]["union_fold_count"])
run_case("6C_W2_six_target_union", w2_folds)

# per-target sub-scopes within W2 (several different target/model shapes)
for i, target in enumerate(w2.get("targets", [])[:6]):
    per_target_folds = set(target.get("ascii_folded_occurrence_stream", []))
    if per_target_folds:
        run_case("6C_W2_target%d" % i, per_target_folds)

with open(w3_path) as f:
    w3 = json.load(f)
w3_usable = w3.get("status") == "PASS" and "workload" in w3
check("6D.1 W3 (72-shot) capture is USABLE for read-only comparison",
      w3_usable, "W3's own stored capture recorded status=%r error=%r -- its own capture run failed "
                 "(wrong project: expected 72 shots, found 11), so it contains no real workload data "
                 "to compare against. NOT force-substituted with synthetic data (prompt Section 6.D: "
                 "'do not force mutation in B2C-B merely to reach historical hashes' -- likewise not "
                 "force-fabricating scope data the real capture never produced)." if not w3_usable else None)
if w3_usable:
    w3_folds = set(w3["workload"]["union_folded_vocabulary"])
    run_case("6D_W3_72shot", w3_folds)

# "scope with MasterUnknown results": explicit synthetic vocabulary guaranteed absent
masterunknown_folds = set(fold("XYZ_NEVER_A_REAL_CONTROL_%d" % i) for i in range(5))
run_case("6C_scope_with_masterunknown_only", masterunknown_folds)

print(
    "\n[NOTE 6C] 'skipped/non-eligible targets' scope-matrix item: NOT applicable at this "
    "authority-acquisition boundary. Per the completed B2C-A fork's finding, "
    "collect_scope_master_wanted_folds() and the master_index build both run BEFORE any "
    "GATE-phase eligibility classification -- wanted_folds is gathered from the raw selected "
    "scope regardless of eventual per-target eligibility, and the SAME already-built index is "
    "reused for eligible and skipped targets alike. There is no distinct 'skipped-target' "
    "wanted_folds shape to construct here; eligibility classification is a downstream concern "
    "unaffected by (and untestable at) this authority boundary."
)

RESULT_SO_FAR = "PASS" if all(c for _, c in RESULTS) else "FAIL"
print("\nRESULT (through scope matrix): %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS), RESULT_SO_FAR))
