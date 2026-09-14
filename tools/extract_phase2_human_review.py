#!/usr/bin/env python3
"""Mechanical, read-only extractor for the Phase 2 human review workbook.

Reads PHASE2_FULL_HUMAN_REVIEW.xlsx and writes PHASE2_HUMAN_DECISIONS.tsv,
containing exactly the rows where the reviewer entered something in FLAG,
Correct Category, or Note. Identity (fold_key, exact spellings, batch, the
original proposed destination) is read from the sheet's hidden machine
columns, not from visible-row position, so re-sorting or re-grouping the
Review sheet cannot silently corrupt the export.

This tool performs NO semantic inference and NO automatic correction. It
never writes to the ledger, the raw Phase 2 batch files, or the Master.
It is a deterministic extraction step only -- what happens to
PHASE2_HUMAN_DECISIONS.tsv afterward (a targeted QA pass, discussion,
disagreement, discard) is a separate, later decision.

Usage:
    python tools/extract_phase2_human_review.py
    python tools/extract_phase2_human_review.py path/to/workbook.xlsx -o out.tsv
"""

import argparse
import csv
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:
    print("This tool requires openpyxl (pip install openpyxl).", file=sys.stderr)
    sys.exit(2)

# Friendly-category -> canonical groupFile/... path lookup is rebuilt from
# the workbook's own Lists sheet, never hardcoded here, so the extractor
# stays correct even if the current Master's valid destination set changes.

REVIEW_HEADERS = ["Control Literal", "FLAG", "Correct Category", "Note"]
# Hidden column layout written by the current build script (Review sheet):
#   E production_position  F fold_key  G batch_id  H original_destination
#   I review_priority      J review_flags          K review_row_id
HIDDEN_COL = {"pp": 5, "fk": 6, "batch": 7, "dest": 8, "pri": 9, "flags": 10, "rid": 11}


def load_category_lookup(wb):
    """Friendly Category -> Canonical Path, from the Lists sheet. Sentinel
    rows (DO NOT IMPORT / UNSURE / NEEDS REVIEW) have no canonical path and
    map to an empty string, preserved as-is rather than guessed at."""
    lookup = {}
    if "Lists" not in wb.sheetnames:
        return lookup
    lst = wb["Lists"]
    for row in lst.iter_rows(min_row=2, values_only=True):
        friendly = row[0]
        canonical = row[1] if len(row) > 1 else None
        if friendly:
            lookup[friendly] = canonical or ""
    return lookup


def extract(xlsx_path, out_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    if "Review" not in wb.sheetnames:
        raise SystemExit(f"'Review' sheet not found in {xlsx_path}")
    ws = wb["Review"]
    cat_lookup = load_category_lookup(wb)

    header_row_values = {tuple(REVIEW_HEADERS)}
    rows_out = []
    scanned = 0
    exported = 0

    for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
        fk_cell = row[HIDDEN_COL["fk"] - 1].value if len(row) >= HIDDEN_COL["fk"] else None
        if fk_cell is None or fk_cell == "":
            continue  # section/tier/column-header rows and the top summary block carry no fold_key
        scanned += 1

        literal = row[0].value
        flag = row[1].value
        category = row[2].value
        note = row[3].value

        flag_str = str(flag).strip() if flag is not None else ""
        category_str = str(category).strip() if category is not None else ""
        note_str = str(note).strip() if note is not None else ""

        if not flag_str and not category_str and not note_str:
            continue  # blank row: no reviewer objection recorded, not exported

        pp = row[HIDDEN_COL["pp"] - 1].value
        batch = row[HIDDEN_COL["batch"] - 1].value
        original_dest = row[HIDDEN_COL["dest"] - 1].value or ""
        # Convert a recognized friendly category to its canonical groupFile/...
        # path. Sentinel entries (DO NOT IMPORT / UNSURE / NEEDS REVIEW) have no
        # canonical path in the Lists sheet and are preserved verbatim, as is
        # any free-typed text that doesn't match a known friendly label.
        if category_str:
            canonical = cat_lookup.get(category_str, "")
            human_dest = canonical if canonical else category_str
        else:
            human_dest = ""

        rows_out.append({
            "production_position": pp,
            "fold_key": fk_cell,
            "exact_spellings": "+".join((literal or "").split(" + ")),
            "original_batch_id": batch,
            "flag": "X" if flag_str.upper() == "X" else flag_str,
            "original_destination": original_dest,
            "human_destination": human_dest,
            "human_note": note_str,
        })
        exported += 1

    rows_out.sort(key=lambda r: (r["production_position"] is None, r["production_position"]))

    fieldnames = ["production_position", "fold_key", "exact_spellings", "original_batch_id",
                  "flag", "original_destination", "human_destination", "human_note"]
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        for r in rows_out:
            w.writerow(r)

    print(f"Scanned {scanned} family rows in '{ws.title}'.")
    print(f"Exported {exported} rows with reviewer input to {out_path}.")
    print("No ledger, raw batch file, or Master file was read for identity data other than "
          "what is embedded in this workbook's own hidden columns; nothing was written to any "
          "of them.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xlsx", nargs="?", default=None,
                         help="Path to PHASE2_FULL_HUMAN_REVIEW.xlsx (default: repository root copy)")
    parser.add_argument("-o", "--output", default=None,
                         help="Output TSV path (default: PHASE2_HUMAN_DECISIONS.tsv in the repository root)")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    xlsx_path = Path(args.xlsx) if args.xlsx else repo_root / "PHASE2_FULL_HUMAN_REVIEW.xlsx"
    out_path = Path(args.output) if args.output else repo_root / "PHASE2_HUMAN_DECISIONS.tsv"

    extract(xlsx_path, out_path)


if __name__ == "__main__":
    main()
