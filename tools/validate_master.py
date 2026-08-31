#!/usr/bin/env python3
"""Read-only structural and native-Rebuild casefold validator for an SFM
animation-group Master file.

This tool is strictly a diagnostic instrument. It parses the target file,
computes mechanical invariants, and reports PASS or FAIL with evidence. It
never writes to the target file (or anywhere else), never selects a
canonical taxonomy destination, and never attempts to repair a failure.

A validator failure is a failed validation, not authorization to repair.
Any corrective edit still requires the project's normal Phase 1 proposal
and explicit approval before Phase 2 (see CLAUDE.md).

Usage:
    python tools/validate_master.py
    python tools/validate_master.py path/to/candidate.txt

Exit codes:
    0 - validation passed (FAIL-level checks all clear; WARNs may exist)
    1 - the file was read and parsed sufficiently, but at least one
        FAIL-level invariant failed
    2 - validation could not be performed reliably (file not found,
        UTF-8 decode failure, or an unhandled internal error)
"""

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

TOKEN_RE = re.compile(r'"((?:[^"\\]|\\.)*)"|(\{)|(\})|(//[^\n]*)|([^\s"{}]+)')


def ascii_fold(literal):
    """Fold ONLY ASCII A-Z to a-z. Every other character, including all
    non-ASCII code points, punctuation, digits, and whitespace, passes
    through unchanged. This is deliberately not Unicode casefold/lower."""
    return "".join(
        chr(ord(ch) + 32) if "A" <= ch <= "Z" else ch for ch in literal
    )


def tokenize(lines):
    tokens = []
    for line_no, line in enumerate(lines, start=1):
        for m in TOKEN_RE.finditer(line):
            if m.group(1) is not None:
                tokens.append((line_no, "STR", m.group(1)))
            elif m.group(2):
                tokens.append((line_no, "OPEN", "{"))
            elif m.group(3):
                tokens.append((line_no, "CLOSE", "}"))
            elif m.group(4):
                break
            elif m.group(5):
                tokens.append((line_no, "WORD", m.group(5)))
    return tokens


class ParseResult:
    def __init__(self):
        self.groups = []  # list of dicts: name, full_path, name_line, open_line, close_line, depth
        self.controls = []  # list of (literal, full_path, line_no)
        self.unmatched_closes = []  # line numbers
        self.unmatched_opens = []  # (name, name_line)
        self.stack_depth_at_eof = 0


def parse_structure(lines):
    """Structurally parse group/control hierarchy by brace depth and full
    path, independent of line-based formatting assumptions. Comments and
    header prose are ignored via the tokenizer; unusual-but-valid historical
    formatting (e.g. a brace sharing a line with other content) parses
    identically to conventional formatting, because detection is
    token-order-based, not line-shape-based."""
    tokens = tokenize(lines)
    result = ParseResult()
    stack = []  # list of dicts: name, name_line, open_line
    idx = 0
    n = len(tokens)
    while idx < n:
        line_no, kind, val = tokens[idx]
        if kind in ("STR", "WORD"):
            if idx + 1 < n and tokens[idx + 1][1] == "OPEN":
                stack.append({"name": val, "name_line": line_no, "open_line": tokens[idx + 1][0]})
                idx += 2
                continue
            elif idx + 1 < n and tokens[idx + 1][1] == "STR":
                key = val
                value = tokens[idx + 1][2]
                if key == "control":
                    current_path = "/".join(frame["name"] for frame in stack)
                    result.controls.append((value, current_path, line_no))
                idx += 2
                continue
            else:
                idx += 1
                continue
        elif kind == "CLOSE":
            if not stack:
                result.unmatched_closes.append(line_no)
                idx += 1
                continue
            frame = stack.pop()
            full_path = "/".join([f["name"] for f in stack] + [frame["name"]])
            result.groups.append({
                "name": frame["name"],
                "full_path": full_path,
                "name_line": frame["name_line"],
                "open_line": frame["open_line"],
                "close_line": line_no,
                "depth": len(stack) + 1,
            })
            idx += 1
            continue
        elif kind == "OPEN":
            # An OPEN not immediately preceded by a STR/WORD name has no
            # attributable group name; nothing meaningful to push here.
            idx += 1
            continue
    result.unmatched_opens = [(f["name"], f["name_line"]) for f in stack]
    result.stack_depth_at_eof = len(stack)
    return result


def validate(path):
    """Run all validations against the file at `path`. Returns a dict of
    evidence and exit code. Never writes to `path` or anywhere else."""
    report = {"path": str(path), "exit_code": 0, "warnings": [], "failures": []}

    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        report["exit_code"] = 2
        report["fatal"] = f"Could not read file: {exc}"
        return report

    report["file_size"] = len(raw)

    has_bom = raw.startswith(b"\xef\xbb\xbf")
    report["bom"] = has_bom
    if has_bom:
        report["warnings"].append("BOM present (established convention for this Master is no BOM).")

    try:
        text = raw.decode("utf-8-sig" if has_bom else "utf-8")
    except UnicodeDecodeError as exc:
        report["exit_code"] = 2
        report["fatal"] = f"UTF-8 decode failure: {exc}"
        return report

    crlf_count = raw.count(b"\r\n")
    lf_total = raw.count(b"\n")
    bare_lf = lf_total - crlf_count
    report["crlf_count"] = crlf_count
    report["bare_lf_count"] = bare_lf
    if crlf_count > 0:
        if bare_lf > 0:
            report["warnings"].append(
                f"Mixed newline style: {crlf_count} CRLF and {bare_lf} bare LF line endings "
                "(established convention for this Master is LF only)."
            )
        else:
            report["warnings"].append(
                f"CRLF newline style detected ({crlf_count} line endings); "
                "established convention for this Master is LF only."
            )

    lines = text.splitlines()
    report["line_count"] = len(lines)

    try:
        parsed = parse_structure(lines)
    except Exception as exc:  # unexpected internal failure, not a data-driven FAIL
        report["exit_code"] = 2
        report["fatal"] = f"Internal parser error: {exc}"
        return report

    report["group_count"] = len(parsed.groups)
    report["open_brace_count"] = text.count("{")
    report["close_brace_count"] = text.count("}")
    report["control_count"] = len(parsed.controls)

    structural_ok = (not parsed.unmatched_closes) and (parsed.stack_depth_at_eof == 0) and (not parsed.unmatched_opens)
    report["structural_parse_pass"] = structural_ok
    if not structural_ok:
        evidence = {
            "unmatched_closing_braces": list(parsed.unmatched_closes),
            "unmatched_opening_groups": [
                {"name": name, "name_line": name_line} for name, name_line in parsed.unmatched_opens
            ],
            "stack_depth_at_eof": parsed.stack_depth_at_eof,
        }
        report["failures"].append({"kind": "structural_parse", "evidence": evidence})

    # Exact duplicate control literals
    by_exact = defaultdict(list)
    for literal, full_path, line_no in parsed.controls:
        by_exact[literal].append((full_path, line_no))
    exact_dups = {lit: occ for lit, occ in by_exact.items() if len(occ) > 1}
    report["exact_duplicate_count"] = len(exact_dups)
    if exact_dups:
        evidence = [
            {"literal": lit, "occurrences": [{"path": p, "line": l} for p, l in occ]}
            for lit, occ in sorted(exact_dups.items())
        ]
        report["failures"].append({"kind": "exact_duplicate", "evidence": evidence})

    # Native-Rebuild ASCII-casefold invariant
    families = defaultdict(list)
    for literal, full_path, line_no in parsed.controls:
        families[ascii_fold(literal)].append((literal, full_path, line_no))

    unique_exact = len(by_exact)
    unique_fold_keys = len(families)
    multi_spelling = 0
    same_path_multi = 0
    cross_path = []
    for key, members in families.items():
        exact_spellings = set(m[0] for m in members)
        distinct_paths = set(m[1] for m in members)
        if len(exact_spellings) > 1:
            multi_spelling += 1
            if len(distinct_paths) == 1:
                same_path_multi += 1
            else:
                cross_path.append((key, members, distinct_paths))

    report["unique_exact_literals"] = unique_exact
    report["unique_ascii_fold_keys"] = unique_fold_keys
    report["multi_spelling_families"] = multi_spelling
    report["same_path_multi_spelling_families"] = same_path_multi
    report["cross_path_family_count"] = len(cross_path)

    if cross_path:
        evidence = []
        for key, members, distinct_paths in sorted(cross_path, key=lambda x: x[0]):
            evidence.append({
                "key": key,
                "members": [{"literal": lit, "path": p, "line": l} for lit, p, l in sorted(members, key=lambda m: m[2])],
                "distinct_path_count": len(distinct_paths),
            })
        report["failures"].append({"kind": "cross_path_casefold", "evidence": evidence})

    if report["failures"]:
        report["exit_code"] = 1

    return report


def format_report(report):
    lines = []
    failures = report.get("failures", [])
    fatal = report.get("fatal")

    if fatal:
        lines.append("FAIL: Master validation could not be completed")
        lines.append("")
        lines.append(f"Path: {report['path']}")
        lines.append(f"Error: {fatal}")
        lines.append("")
        lines.append("No files have been modified.")
        return "\n".join(lines)

    ok = not failures
    lines.append("PASS: Master validation succeeded" if ok else "FAIL: Master validation failed")
    lines.append("")
    lines.append(f"Path: {report['path']}")
    lines.append(f"File size (bytes): {report['file_size']}")
    lines.append(f"BOM present: {report['bom']}")
    lines.append(f"CRLF line endings: {report['crlf_count']}")
    lines.append(f"Bare LF line endings: {report['bare_lf_count']}")
    lines.append(f"Line count: {report['line_count']}")
    lines.append(f"Group count: {report['group_count']}")
    lines.append(f"Open brace count: {report['open_brace_count']}")
    lines.append(f"Close brace count: {report['close_brace_count']}")
    lines.append(f"Control lines: {report['control_count']}")
    lines.append(f"Unique exact literals: {report['unique_exact_literals']}")
    lines.append(f"Unique ASCII-fold keys: {report['unique_ascii_fold_keys']}")
    lines.append(f"Multi-spelling ASCII-fold families: {report['multi_spelling_families']}")
    lines.append(f"  same-path (valid): {report['same_path_multi_spelling_families']}")
    lines.append(f"  cross-path (invariant violation): {report['cross_path_family_count']}")
    lines.append(f"Exact duplicate literals: {report['exact_duplicate_count']}")
    lines.append(f"Structural parse: {'PASS' if report['structural_parse_pass'] else 'FAIL'}")
    lines.append("")

    if report.get("warnings"):
        lines.append("Warnings:")
        for w in report["warnings"]:
            lines.append(f"  WARN: {w}")
        lines.append("")

    for failure in failures:
        kind = failure["kind"]
        evidence = failure["evidence"]
        if kind == "structural_parse":
            lines.append("Structural parse failure evidence:")
            for ln in evidence["unmatched_closing_braces"]:
                lines.append(f"  Unmatched closing brace at line {ln}")
            for grp in evidence["unmatched_opening_groups"]:
                lines.append(f"  Unmatched opening brace for group {grp['name']!r} declared at line {grp['name_line']}")
            lines.append(f"  Stack depth at EOF: {evidence['stack_depth_at_eof']}")
            lines.append("")
        elif kind == "exact_duplicate":
            lines.append("Exact duplicate control literal evidence:")
            for item in evidence:
                lines.append(f"  literal: {item['literal']!r}")
                for occ in item["occurrences"]:
                    lines.append(f"    path: {occ['path']!r}  line: {occ['line']}")
            lines.append("")
        elif kind == "cross_path_casefold":
            lines.append("FAIL: native-Rebuild casefold family spans multiple paths")
            lines.append("")
            for fam in evidence:
                lines.append(f"  key: {fam['key']!r}")
                for m in fam["members"]:
                    lines.append(f"    literal: {m['literal']!r}")
                    lines.append(f"    path: {m['path']!r}")
                    lines.append(f"    line: {m['line']}")
                lines.append(f"  distinct paths: {fam['distinct_path_count']}")
                lines.append("")

    if not ok:
        lines.append("No suggested fix. No preferred path. No repair action.")
        lines.append("Any corrective edit requires the normal Phase 1 approval workflow (see CLAUDE.md).")
        lines.append("")

    lines.append("No files have been modified.")
    return "\n".join(lines)


def default_master_path():
    return Path(__file__).resolve().parent.parent / "sfm_defaultanimationgroups.txt"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Read-only structural and native-Rebuild ASCII-casefold validator "
            "for an SFM animation-group Master file. Reports PASS/FAIL with "
            "evidence. Never modifies the target file or any other file."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Path to the Master file to validate. Defaults to the repository's canonical sfm_defaultanimationgroups.txt.",
    )
    args = parser.parse_args(argv)

    target = Path(args.path) if args.path else default_master_path()
    report = validate(target)
    print(format_report(report))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
