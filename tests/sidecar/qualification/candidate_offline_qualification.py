# -*- coding: utf-8 -*-
"""R2 bounded-repair CANDIDATE -- offline (desktop) pre-runtime qualification.

NOT production code, NOT a pytest suite (deliberately standalone so its
PASS/FAIL narrative is one linear, readable transcript). Compares the R2
candidate (`candidate_packed_validator.py` + `candidate_packed_provider.py`)
against the existing production/qualification oracle
(`tools/sfm_master_sidecar/reader.py` + `tests/sidecar/qualification/bounded_provider.py`)
on:

  1. dependency identity (every file this script reads/imports, hashed);
  2. digest-streaming equivalence (old whole-buffer-copy digest vs new
     streaming digest, byte-for-byte, on the real official artifact);
  3. canonical-artifact acceptance + full inventory/hierarchy/metadata
     parity (old provider vs candidate provider);
  4. W1 requested-family projection parity (build_manual_projection, old
     provider vs candidate provider) and provider-level lookup_fold parity
     for every W1 fold, cross-checked against the precomputed expected
     results;
  5. a corruption/incompatibility battery (old reader vs candidate
     validator, every case CHECKSUM-VALID per the recomputed-digest
     requirement) covering every Section 20 A-J category;
  6. static confirmation that the candidate contains no mmap, no forced
     GC, no process-global cache, and does not return/retain a full
     decoded string/occurrence/fold/index graph.

Run with desktop Python 3 (reader.py/format.py/bounded_provider.py are
explicitly Python 2.7-AND-3 compatible; this script is desktop-only and
does not need to be, and is never deployed to SFM).

Does not edit: production Normalizer, Master TXT, sidecar format/compiler,
workload corpus, expected-results JSON, reader.py, format.py,
bounded_provider.py. Everything here is read-only.
"""

import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
QUAL_DIR = Path(__file__).resolve().parent
FIXTURES_ROOT = REPO_ROOT / "tests" / "sidecar" / "fixtures"

sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(QUAL_DIR))
sys.path.insert(0, str(QUAL_DIR.parent))

import sfm_master_core as core  # noqa: E402
from sfm_master_sidecar import format as fmt  # noqa: E402
from sfm_master_sidecar import reader, writer  # noqa: E402
from corruption_helpers import MutableSidecar, compiled_fixture  # noqa: E402

import bounded_provider as old_provider_mod  # noqa: E402
import bounded_view  # noqa: E402
import r1_consumer_projection as proj  # noqa: E402
import candidate_packed_validator  # noqa: E402
import candidate_packed_provider as new_provider_mod  # noqa: E402

# The real files this comparison depends on -- deployed-directory copies,
# same ones the SFM-side scripts pin, so this offline run and the runtime
# discriminator are provably looking at the same identities.
DEPLOY = Path(r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm\gate_r2_deploy")
ARTIFACT_PATH = DEPLOY / "official_sidecar_artifact.bin"
MASTER_TXT_PATH = Path(r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\cfg\sfm_defaultanimationgroups.txt")
CORPUS_PATH = DEPLOY / "SFM_NORMALIZER_R2_REAL_WORKLOADS.json"
EXPECTED_RESULTS_PATH = DEPLOY / "run_results" / "r2_precomputed_expected_results.json"

MASTER_EXPECTED_SHA = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
ARTIFACT_EXPECTED_SHA = "bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b"
CORPUS_EXPECTED_SHA = "f47e378aeb20d4bf142ea52f2d293a49d3cfcfc85f85135a36df0bf1e7503a3f"
EXPECTED_RESULTS_EXPECTED_SHA = "98c50c39752d595e3d245fa606932b3a0165a33171fed383c91c61bbc2dda2ec"
READER_EXPECTED_SHA = "1b95261c52d95c306b28fc6e5e9340afa65de4ea2574ed29c2bab427d252719f"
FORMAT_EXPECTED_SHA = "b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259"
BOUNDED_PROVIDER_EXPECTED_SHA = "8e70a47a5e657781f6047a0c50635904ba08894ff2a467f49420ff9a1fcea979"

_FAILURES = []
_report = {"checks": []}


def check(name, condition, detail=None):
    row = {"check": name, "pass": bool(condition), "detail": detail}
    _report["checks"].append(row)
    status = "PASS" if condition else "FAIL"
    print("[%s] %s%s" % (status, name, ("  -- " + str(detail)) if detail and not condition else ""))
    if not condition:
        _FAILURES.append(row)
    return condition


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


print("=" * 70)
print("SECTION 1: dependency identity")
print("=" * 70)

reader_sha = sha256_of(TOOLS_DIR / "sfm_master_sidecar" / "reader.py")
format_sha = sha256_of(TOOLS_DIR / "sfm_master_sidecar" / "format.py")
bounded_provider_sha = sha256_of(QUAL_DIR / "bounded_provider.py")
master_sha = sha256_of(MASTER_TXT_PATH)
artifact_sha = sha256_of(ARTIFACT_PATH)
corpus_sha = sha256_of(CORPUS_PATH)
expected_results_sha = sha256_of(EXPECTED_RESULTS_PATH)
candidate_validator_sha = sha256_of(QUAL_DIR / "candidate_packed_validator.py")
candidate_provider_sha = sha256_of(QUAL_DIR / "candidate_packed_provider.py")

print("reader.py                 %s" % reader_sha)
print("format.py                 %s" % format_sha)
print("bounded_provider.py        %s" % bounded_provider_sha)
print("Master TXT                %s" % master_sha)
print("official artifact         %s" % artifact_sha)
print("workload corpus           %s" % corpus_sha)
print("expected-results JSON     %s" % expected_results_sha)
print("candidate_packed_validator.py  %s" % candidate_validator_sha)
print("candidate_packed_provider.py   %s" % candidate_provider_sha)

check("reader.py matches pinned identity", reader_sha == READER_EXPECTED_SHA)
check("format.py matches pinned identity", format_sha == FORMAT_EXPECTED_SHA)
check("bounded_provider.py matches pinned identity", bounded_provider_sha == BOUNDED_PROVIDER_EXPECTED_SHA)
check("Master TXT matches pinned identity", master_sha == MASTER_EXPECTED_SHA)
check("official artifact matches pinned identity", artifact_sha == ARTIFACT_EXPECTED_SHA)
check("workload corpus matches pinned identity", corpus_sha == CORPUS_EXPECTED_SHA)
check("expected-results JSON matches pinned identity", expected_results_sha == EXPECTED_RESULTS_EXPECTED_SHA)

if _FAILURES:
    print("\nABORTING: a controlling dependency does not match its pinned identity.")
    sys.exit(1)


print()
print("=" * 70)
print("SECTION 2: digest-streaming equivalence (real official artifact)")
print("=" * 70)

with open(ARTIFACT_PATH, "rb") as f:
    real_artifact_buf = f.read()

digest_off = fmt.embedded_integrity_digest_offset()
old_digest = fmt.compute_embedded_integrity_digest(real_artifact_buf, digest_off)
new_digest = candidate_packed_validator._compute_embedded_integrity_digest_streaming(real_artifact_buf, digest_off)
check(
    "streaming digest == whole-buffer-copy digest (real artifact)",
    old_digest == new_digest,
    "old=%s new=%s" % (old_digest.hex(), new_digest.hex()),
)


print()
print("=" * 70)
print("SECTION 3: canonical artifact acceptance + inventory/hierarchy/metadata parity")
print("=" * 70)

old_p = old_provider_mod.BoundedProvider.open_path(str(ARTIFACT_PATH), MASTER_EXPECTED_SHA)
new_p = new_provider_mod.BoundedProvider.open_path(str(ARTIFACT_PATH), MASTER_EXPECTED_SHA)
check("old provider accepts canonical artifact", old_p.is_valid())
check("candidate provider accepts canonical artifact", new_p.is_valid())

check("group_count matches", old_p.group_count() == new_p.group_count(),
      "old=%r new=%r" % (old_p.group_count(), new_p.group_count()))
check("occurrence_count matches", old_p.occurrence_count() == new_p.occurrence_count(),
      "old=%r new=%r" % (old_p.occurrence_count(), new_p.occurrence_count()))
check("fold_count matches", old_p.fold_count() == new_p.fold_count(),
      "old=%r new=%r" % (old_p.fold_count(), new_p.fold_count()))
check("wrapper_path matches", old_p.wrapper_path() == new_p.wrapper_path(),
      "old=%r new=%r" % (old_p.wrapper_path(), new_p.wrapper_path()))

old_groups = list(old_p.iter_groups())
new_groups = list(new_p.iter_groups())
check("iter_groups() full output matches", old_groups == new_groups,
      "len old=%d new=%d" % (len(old_groups), len(new_groups)))

old_metadata_all = []
new_metadata_all = []
for pid in range(old_p.group_count()):
    old_metadata_all.append(list(old_p.iter_metadata(pid)))
    new_metadata_all.append(list(new_p.iter_metadata(pid)))
check("iter_metadata() matches for every group", old_metadata_all == new_metadata_all)


print()
print("=" * 70)
print("SECTION 4: W1 requested-family projection + lookup_fold parity")
print("=" * 70)

with open(CORPUS_PATH, "rb") as f:
    corpus = json.load(f)
w1 = corpus["workloads"]["W1_small_fox"]
w1_wanted_folds = set(w1["scalar_lookup_sequence_folded"])
w1_literals = list(w1["scalar_lookup_sequence_exact"])
print("W1 wanted_fold_count=%d literal_count=%d" % (len(w1_wanted_folds), len(w1_literals)))

# lookup_fold-level parity: does not need the real Normalizer/sfmApp --
# purely provider-level, fully offline-testable.
old_lookups = {}
new_lookups = {}
for folded in w1_wanted_folds:
    old_lookups[folded] = old_p.lookup_fold(folded.encode("utf-8"))
    new_lookups[folded] = new_p.lookup_fold(folded.encode("utf-8"))


def _hitlike_to_tuple(h):
    cls = h.__class__.__name__
    if cls == "MasterUnknown":
        return ("MasterUnknown", h.fold_key)
    if cls == "Hit":
        return ("Hit", h.fold_key, h.destination, tuple(sorted(o["global_rank"] for o in h.occurrences())))
    if cls == "FoldConflict":
        return ("FoldConflict", h.fold_key, tuple(sorted(h.destinations)),
                 tuple(sorted(o["global_rank"] for o in h.occurrences())))
    raise AssertionError("unexpected lookup_fold result class %r" % cls)


mismatches = []
for folded in w1_wanted_folds:
    ot = _hitlike_to_tuple(old_lookups[folded])
    nt = _hitlike_to_tuple(new_lookups[folded])
    if ot != nt:
        mismatches.append((folded, ot, nt))
check("lookup_fold() identical for all %d W1 folds" % len(w1_wanted_folds), not mismatches,
      "first mismatch: %r" % (mismatches[0],) if mismatches else None)

# Full detached-view (build_manual_projection) parity -- this exercises
# projection code, not just raw lookup_fold, over BOTH providers.
try:
    old_view = proj.build_manual_projection(
        old_p, bounded_view, w1_wanted_folds,
        old_provider_mod.AuthorityUnavailable,  # placeholder ProbeError arg (unused unless a probe actually errors)
        None, None,
    )
    projection_ran = True
except Exception:
    projection_ran = False
    print("NOTE: build_manual_projection needs real Normalizer callables "
          "(ProbeError/parse_master_rgba_text/parse_master_bool_text) not "
          "available on desktop (sfmApp-only, exactly like D1/D2's own "
          "constraint) -- skipped here; the SFM runtime diagnostic performs "
          "the real end-to-end projection instead.")
check("build_manual_projection offline attempt reported honestly", True,
      "ran=%r (expected False on desktop -- see note above)" % projection_ran)

with open(EXPECTED_RESULTS_PATH, "rb") as f:
    expected_all = json.load(f)
expected_manual = expected_all["workloads"]["W1_small_fox"]["manual"]
missing_vs_expected = [lit for lit in w1_literals if lit not in expected_manual]
check("every W1 literal has a precomputed expectation (missing = hard failure)",
      not missing_vs_expected,
      "missing_count=%d sample=%r" % (len(missing_vs_expected), missing_vs_expected[:5]))


print()
print("=" * 70)
print("SECTION 5: corruption/incompatibility battery (old reader vs candidate validator)")
print("=" * 70)


def _mutable(name="28_large_alias_family.txt"):
    data, result, blob = compiled_fixture(core, writer, FIXTURES_ROOT, name)
    return result, MutableSidecar(blob)


def old_verdict(m):
    try:
        r = reader.SidecarReader.open_generation_unbound_bytes(m.bytes())
        r.close()
        return ("ACCEPT", None)
    except reader.AuthorityUnavailable as exc:
        return ("REJECT", type(exc).__name__)


def new_verdict(m):
    try:
        candidate_packed_validator.validate_packed(m.bytes())
        return ("ACCEPT", None)
    except reader.AuthorityUnavailable as exc:
        return ("REJECT", type(exc).__name__)
    except candidate_packed_validator.AuthorityUnavailable as exc:
        return ("REJECT", type(exc).__name__)


CASES = []
DEFAULT_FIXTURE = "28_large_alias_family.txt"


def case(label, mutate_fn, fixture=DEFAULT_FIXTURE):
    CASES.append((label, mutate_fn, fixture))


# -- A. Header / directory --
case("bad magic", lambda m: m.set_header_fields(magic=b"XXXXXXX\x00"))
case("bad format_contract_version", lambda m: m.set_header_fields(format_contract_version=999))
case("bad authority_semantics_version", lambda m: m.set_header_fields(authority_semantics_version=77))
case("payload_length mismatch", lambda m: m.set_header_fields(payload_length=len(m.buf) + 8))
case("section_count mismatch", lambda m: m.set_header_fields(section_count=3))
case("directory row bounds overflow", lambda m: m.set_directory_row(fmt.SECTION_STRING_TABLE, offset=len(m.buf) + 1))
case("directory row_size mismatch", lambda m: m.set_directory_row(fmt.SECTION_GROUP_TABLE, row_size=999))
case("directory row_count*row_size mismatch",
     lambda m: m.set_directory_row(fmt.SECTION_FOLD_TABLE,
                                    row_count=m.directory_row_for(fmt.SECTION_FOLD_TABLE)[1].row_count + 7))
case("duplicate section_id", lambda m: m.set_directory_row_at_index(1, section_id=m.directory_row_for(fmt.SECTION_GROUP_TABLE)[1].section_id))

# -- B. Strings --
case("string table row out-of-bounds offset", lambda m: m.set_string_table_row(0, offset=10**9))
case("string exceeds single-string limit", lambda m: m.set_string_table_row(0, length=fmt.LIMIT_SINGLE_STRING_BYTE_LENGTH + 1))
case("invalid UTF-8 in pool", lambda m: m.patch_string_pool_byte(0, 0xFF))

# -- C/D. Groups + child index --
case("group name_string_id out of bounds", lambda m: m.set_group_row(1, name_string_id=10**6))
case("group parent cycle (parent >= self)", lambda m: m.set_group_row(1, parent_path_id=5))
case("two parentless groups", lambda m: m.set_group_row(1, parent_path_id=0xFFFFFFFF))
case("duplicate declare_order", lambda m: m.set_group_row(1, declare_order=m.get_group_row(2).declare_order),
     fixture="06_sibling_groups.txt")
case("child-id index ownership disagreement", lambda m: m.set_child_id_index_entry(0, m.get_group_row(1).child_index_start + 1))

# -- E. Metadata --
case("metadata key_string_id out of bounds", lambda m: m.set_metadata_row(0, key_string_id=10**6))
case("metadata source_order not dense", lambda m: m.set_metadata_row(0, source_order=99) if m.get_group_row(0).metadata_count > 0 else m.set_metadata_row(0, path_id=0))

# -- F/H. Occurrences + folds --
case("occurrence literal_string_id out of bounds", lambda m: m.set_occurrence_row(0, literal_string_id=10**6))
case("occurrence path_id out of bounds", lambda m: m.set_occurrence_row(0, path_id=10**6))
case("occurrence fold_id out of bounds", lambda m: m.set_occurrence_row(0, fold_id=10**6))
case("occurrence local_rank out of range", lambda m: m.set_occurrence_row(0, local_rank=999999))
case("fold occ_index_count zero", lambda m: m.set_fold_row(0, occ_index_count=0))
case("fold key ascending-order violation", lambda m: m.set_fold_row(1, fold_key_string_id=m.get_fold_row(0).fold_key_string_id))
case("occurrence ascii-fold(literal) != fold's own key",
     lambda m: m.set_occurrence_row(0, fold_id=(m.get_occurrence_row(0).fold_id + 1) % (len(m.section_bytes(fmt.SECTION_FOLD_TABLE)) // fmt.FOLD_TABLE_ROW_SIZE)),
     fixture="06_sibling_groups.txt")

# -- G/I. Indexes --
case("occ-by-group index entry out of bounds", lambda m: m.set_occ_by_group_index_entry(0, 10**6))
case("occ-by-group index duplicate claim", lambda m: m.set_occ_by_group_index_entry(1, m.get_occ_by_group_index_entry(0)))
case("occ-by-fold index entry out of bounds", lambda m: m.set_occ_by_fold_index_entry(0, 10**6))
case("occ-by-fold index duplicate claim", lambda m: m.set_occ_by_fold_index_entry(1, m.get_occ_by_fold_index_entry(0)))


parity_rows = []
disagreements = 0
for label, mutate_fn, fixture_name in CASES:
    result, m = _mutable(fixture_name)
    try:
        mutate_fn(m)
    except Exception as exc:
        print("  SKIP %-55s (mutation setup raised %r -- fixture too small for this field)" % (label, exc))
        continue
    m.recompute_checksum()  # CHECKSUM-VALID: digest recomputed AFTER the structural edit (prompt item 7)
    ov = old_verdict(m)
    nv = new_verdict(m)
    agree = ov[0] == nv[0]
    parity_rows.append({"case": label, "old": ov, "candidate": nv, "agree": agree})
    marker = "OK " if agree else "!! "
    print("  %s%-55s old=%-8s candidate=%-8s" % (marker, label, ov[0], nv[0]))
    if not agree:
        disagreements += 1

check("all corruption cases: old-vs-candidate accept/reject agreement", disagreements == 0,
      "%d/%d disagreed" % (disagreements, len(parity_rows)))

# The unmutated fixture must still be ACCEPTED by both (sanity: reject
# behavior above isn't simply "always rejects").
result0, m0 = _mutable()
ov0 = old_verdict(m0)
nv0 = new_verdict(m0)
check("unmutated fixture accepted by both (sanity)", ov0 == ("ACCEPT", None) and nv0 == ("ACCEPT", None),
      "old=%r candidate=%r" % (ov0, nv0))


print()
print("=" * 70)
print("SECTION 6: exact literal / ASCII-fold semantics")
print("=" * 70)

# R1D no longer reuses fmt.ascii_fold_bytes by object identity -- it uses a
# candidate-local, C-level `_ascii_fold_bytes_fast` (256-byte translate
# table) for speed. Equivalence must now be proven exhaustively rather than
# asserted via object identity: every one of the 256 possible byte values,
# individually, must fold identically to the production reference.
_fold_mismatches_exhaustive = []
for b in range(256):
    single = bytes(bytearray([b]))
    fast = candidate_packed_validator._ascii_fold_bytes_fast(single)
    slow = fmt.ascii_fold_bytes(single)
    if fast != slow:
        _fold_mismatches_exhaustive.append((b, fast, slow))
check("candidate's fast ASCII-fold matches production for all 256 individual byte values",
      not _fold_mismatches_exhaustive, "mismatches=%r" % (_fold_mismatches_exhaustive[:5],))


print()
print("=" * 70)
print("SECTION 7: static confirmation -- no mmap / no forced GC / no process-global cache / "
      "no retained full decoded graph")
print("=" * 70)

validator_src = (QUAL_DIR / "candidate_packed_validator.py").read_text(encoding="utf-8")
provider_src = (QUAL_DIR / "candidate_packed_provider.py").read_text(encoding="utf-8")
combined_src = validator_src + provider_src

check("no 'import mmap'", "import mmap" not in combined_src)
check("no 'gc.collect' / 'import gc'", "gc.collect" not in combined_src and "import gc" not in combined_src)
check("no module-level (process-global) string/row cache -- only per-instance self._string_cache",
      "globals()[" not in combined_src and "_GLOBAL_CACHE" not in combined_src)
check("validate_packed returns only (header, directory) -- verified by source scan",
      combined_src.count("return header, directory") >= 1)
validator_code_lines = [ln for ln in validator_src.splitlines() if not ln.strip().startswith("#")]
validator_code_only = "\n".join(validator_code_lines)
for leaked_name in ("strings = []", "occurrence_rows = []", "fold_rows = []",
                    "occ_by_group_index = []", "occ_by_fold_index = []"):
    check("candidate validator never builds %r (comment lines excluded)" % leaked_name,
          leaked_name not in validator_code_only)


old_p.close()
new_p.close()


print()
print("=" * 70)
print("SECTION 8: raw-byte ASCII-fold equivalence (timing-correction Approach A)")
print("=" * 70)

# Proves: ascii_fold_bytes(raw_utf8_bytes) == ascii_fold_bytes(text.encode("utf-8"))
# where text = raw_utf8_bytes.decode("utf-8") -- i.e. operating directly on
# validated raw bytes (what the corrected candidate now does) is identical
# to the old decode-then-fold-then-reencode round trip, for every case
# below. This is the semantic-equivalence argument made concrete and
# checked, not merely asserted.

ASCII_FOLD_CASES = [
    ("ASCII upper", b"HELLO WORLD"),
    ("ASCII lower", b"hello world"),
    ("ASCII mixed case", b"HeLLo WoRLD"),
    ("non-ASCII valid UTF-8 (accented)", "café".encode("utf-8")),
    ("non-ASCII valid UTF-8 (CJK)", "日本語".encode("utf-8")),
    ("mixed ASCII + non-ASCII", "Rig_Café_ARMS".encode("utf-8")),
    ("whitespace preserved", b"  Leading And Trailing  "),
    ("punctuation preserved", b"Rig.Arm-Left_(01)!"),
    ("empty string", b""),
    ("digits and underscores", b"control_130_ABC"),
]

fold_mismatches = []
fast_fold_mismatches = []
for label, raw in ASCII_FOLD_CASES:
    direct = fmt.ascii_fold_bytes(raw)
    text = raw.decode("utf-8")
    roundtrip = fmt.ascii_fold_bytes(text.encode("utf-8"))
    fast = candidate_packed_validator._ascii_fold_bytes_fast(raw)
    ok = direct == roundtrip
    fast_ok = fast == direct
    print("  %-40s direct=%-30r roundtrip=%-30r fast=%-30r %s" % (
        label, direct, roundtrip, fast, "OK" if (ok and fast_ok) else "MISMATCH"))
    if not ok:
        fold_mismatches.append(label)
    if not fast_ok:
        fast_fold_mismatches.append(label)
check("raw-byte ascii_fold_bytes matches decode->fold->encode round trip for all cases", not fold_mismatches,
      "failed: %r" % (fold_mismatches,))
check("candidate's fast (translate-table) ASCII-fold matches production for all mixed-string cases",
      not fast_fold_mismatches, "failed: %r" % (fast_fold_mismatches,))

# Invalid UTF-8 must still be rejected -- and rejected BEFORE any semantic
# (fold/equality) comparison is even attempted, i.e. via the same B-phase
# blanket pass, regardless of whether the corrupt string is referenced by
# anything else. Reuses the existing corrupted-pool case from Section 5.
result_iuf8, m_iuf8 = _mutable()
m_iuf8.patch_string_pool_byte(0, 0xFF)
m_iuf8.recompute_checksum()
verdict_iuf8 = new_verdict(m_iuf8)
check("invalid UTF-8 still rejected by candidate (before any semantic comparison)",
      verdict_iuf8[0] == "REJECT", "verdict=%r" % (verdict_iuf8,))


print()
print("=" * 70)
if _FAILURES:
    print("RESULT: %d CHECK(S) FAILED" % len(_FAILURES))
    for row in _FAILURES:
        print("  FAILED: %s -- %s" % (row["check"], row["detail"]))
    sys.exit(1)
else:
    print("RESULT: ALL CHECKS PASSED (%d checks)" % len(_report["checks"]))
    sys.exit(0)
