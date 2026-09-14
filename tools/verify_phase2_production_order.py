#!/usr/bin/env python3
"""Read-only diagnostic: independently verify the Phase 2 canonical
production-order v1 sequence against PHASE2_PRODUCTION_ORDER.tsv.

This script performs no semantic classification, writes no project
artifact, and does not depend on Python's random module, hash(),
set/dict iteration order, locale collation, or filesystem order.
See audit/master-content/phase2/PHASE2_PRODUCTION_SEQUENCE_SPEC.txt for the
full specification.
"""
import csv
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHASE2_DIR = ROOT / "audit" / "master-content" / "phase2"
INVENTORY = PHASE2_DIR / "PHASE2_RESIDUAL_INVENTORY.tsv"
FINAL = PHASE2_DIR / "PHASE2_SEMANTIC_PILOT_500_FINAL.tsv"
ORDER = PHASE2_DIR / "PHASE2_PRODUCTION_ORDER.tsv"
SPEC_EXPECTED_FULL_SHA256 = "d43e0aa97e96608b165b993428af54084f3cfbe110379d22af8c416251618494"
SPEC_EXPECTED_PRODUCTION_SHA256 = "ad4c1e865c8edc18e039f233466731a56bf44170a9eacbd208e39c56f3dd4858"

DOMAIN_SEED = b"SFM_PHASE2_PRODUCTION_ORDER_V1_2026-09-01"


def strict_fold(s: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in s)


def sha_key(fold_key: str) -> bytes:
    return hashlib.sha256(DOMAIN_SEED + b"\x00" + fold_key.encode("utf-8")).digest()


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def main() -> None:
    checks = {}

    # 1-2. Reconstruct the strict-ASCII residual universe; assert 14,282 families.
    with open(INVENTORY, encoding="utf-8-sig", newline="") as f:
        inv_rows = list(csv.DictReader(f, delimiter="\t"))

    fam_literals = {}
    for r in inv_rows:
        lit = r["exact_literal"]
        fk = strict_fold(lit)
        if fk != r["fold_key"]:
            fail(f"fold mismatch: {lit!r} -> {fk!r} vs stored {r['fold_key']!r}")
        fam_literals.setdefault(fk, []).append(lit)

    universe = set(fam_literals.keys())
    checks["universe_size_14282"] = (len(universe) == 14282)
    if not checks["universe_size_14282"]:
        fail(f"universe size {len(universe)} != 14282")

    # 3-5. Load FINAL.tsv; assert 500 unique calibration families, all in universe.
    with open(FINAL, encoding="utf-8-sig", newline="") as f:
        final_rows = list(csv.DictReader(f, delimiter="\t"))

    calibration_fks = [r["fold_key"] for r in final_rows]
    checks["calibration_count_500"] = (len(calibration_fks) == 500)
    checks["calibration_unique_500"] = (len(set(calibration_fks)) == 500)
    checks["calibration_subset_of_universe"] = all(fk in universe for fk in calibration_fks)
    if not (checks["calibration_count_500"] and checks["calibration_unique_500"]
            and checks["calibration_subset_of_universe"]):
        fail("calibration set invariant violated")

    calibration_set = set(calibration_fks)

    # 6. Form the exact 13,782-family complement.
    production_set = universe - calibration_set
    checks["production_complement_13782"] = (len(production_set) == 13782)
    checks["zero_overlap"] = calibration_set.isdisjoint(production_set)
    checks["union_equals_universe"] = ((calibration_set | production_set) == universe)
    if not (checks["production_complement_13782"] and checks["zero_overlap"]
            and checks["union_equals_universe"]):
        fail("production complement invariant violated")

    # 7. Apply the documented SHA-256-key-sort v1 algorithm.
    generated_order = sorted(production_set, key=lambda fk: (sha_key(fk), fk.encode("utf-8")))

    # 8-9. Compare sequentially with PHASE2_PRODUCTION_ORDER.tsv; verify exact_spellings membership.
    with open(ORDER, encoding="utf-8-sig", newline="") as f:
        order_rows = list(csv.DictReader(f, delimiter="\t"))

    checks["order_file_row_count_13782"] = (len(order_rows) == 13782)
    if not checks["order_file_row_count_13782"]:
        fail(f"PHASE2_PRODUCTION_ORDER.tsv row count {len(order_rows)} != 13782")

    sequential_match = True
    spellings_match = True
    for i, (expected_fk, row) in enumerate(zip(generated_order, order_rows), start=501):
        if row["fold_key"] != expected_fk:
            sequential_match = False
            print(f"  mismatch at position {i}: expected {expected_fk!r}, file has {row['fold_key']!r}")
            break
        expected_spellings = "+".join(sorted(fam_literals[expected_fk]))
        if row["exact_spellings"] != expected_spellings:
            spellings_match = False
            print(f"  exact_spellings mismatch at position {i} ({expected_fk!r}): "
                  f"expected {expected_spellings!r}, file has {row['exact_spellings']!r}")
            break
    checks["sequential_match_all_13782"] = sequential_match
    checks["exact_spellings_match_all_13782"] = spellings_match

    # 10. Verify canonical positions 501-14282 exactly.
    positions_ok = [int(r["canonical_position"]) for r in order_rows] == list(range(501, 14283))
    checks["canonical_positions_501_to_14282"] = positions_ok

    # 11-12. Zero overlap with calibration; union equals full universe (already checked above,
    # re-asserted here against the file's own fold_key column for belt-and-suspenders).
    order_fks = set(r["fold_key"] for r in order_rows)
    checks["order_file_zero_overlap_with_calibration"] = calibration_set.isdisjoint(order_fks)
    checks["order_file_union_equals_universe"] = ((calibration_set | order_fks) == universe)

    # 13. Verify both stored SHA-256 fingerprints.
    full_sequence = calibration_fks + generated_order
    full_bytes = ("\n".join(full_sequence) + "\n").encode("utf-8")
    full_sha256 = hashlib.sha256(full_bytes).hexdigest()

    production_bytes = ("\n".join(generated_order) + "\n").encode("utf-8")
    production_sha256 = hashlib.sha256(production_bytes).hexdigest()

    checks["full_sequence_sha256_matches_spec"] = (full_sha256 == SPEC_EXPECTED_FULL_SHA256)
    checks["production_only_sha256_matches_spec"] = (production_sha256 == SPEC_EXPECTED_PRODUCTION_SHA256)

    print("VERIFICATION RESULTS:")
    for k, v in checks.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")

    all_pass = all(checks.values())
    print()
    print("canonical position 501 fold_key:", generated_order[0])
    print("full sequence SHA256:", full_sha256)
    print("production-only SHA256:", production_sha256)
    print()
    print("ALL CHECKS PASS:", all_pass)

    if not all_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
