# -*- coding: utf-8 -*-
"""Phase B2A: an independent, TEST-ONLY source inventory oracle for SFM
Master-shaped documents.

Purpose (see SFM_MASTER_SIDECAR_PHASE_B1_2_FINAL_IMPLEMENTATION_SPEC.md sec 37
and SFM_MASTER_SIDECAR_PHASE_B2A_ORACLE_FIXTURE_AUDIT.md): independently
reconstruct the same ordered structural facts tools/sfm_master_core.py claims
to produce, using a DIFFERENT implementation strategy, so that a shared parser
blind spot, omission, reassignment, or reordering bug cannot hide from every
qualification check simultaneously.

INDEPENDENCE BOUNDARY (do not weaken):
  - This module does NOT import tools/sfm_master_core, tools/validate_master,
    or any other production semantic module.
  - It does NOT call parse_master_bytes / parse_master_file / parse_structure
    / build_fold_families, directly or indirectly.
  - It uses only the Python 3 standard library.
  - It does NOT need, and does not attempt, Python 2.7 compatibility -- it is
    test/qualification infrastructure only, never shipped, never imported by
    any production or runtime-safe package.

WHAT THIS MODULE IS NOT:
  - Not a second production parser. It exists to independently COUNT and
    ORDER what a source document contains, not to become an alternate
    authority for taxonomy, ASCII-fold conflict policy, metadata meaning, or
    runtime lookup semantics. See SCOPE below.

IMPLEMENTATION STRATEGY (deliberately different from tools/sfm_master_core.py):
  - Tokenization here is a hand-written character-by-character scanner, not a
    single compiled regular expression matched per line.
  - Structure here is built by a recursive-descent parser (one Python
    function call per nested group), not an explicit brace-depth stack
    consumed by a flat while-loop over pre-tokenized input.
  - Groups are emitted in OPEN order (naturally pre-order, via direct
    recursion) rather than being collected via any subsequent reordering
    step -- this exercises the same declaration-order fact that
    tools/sfm_master_core.py's `declare_order` field is supposed to capture,
    but arrives at it via a structurally unrelated code path.

CONTRACT THIS MODULE ASSUMES (matches the qualified core's documented
behavior -- see SFM_MASTER_SIDECAR_PHASE_B0_1_COMPLETENESS_AUDIT.md sec 12,
corrected): a quoted string must open and close on the same source line; a
backslash followed by any character is treated as a two-character unit for
the purpose of finding the string's true closing quote, and BOTH characters
are retained literally in the captured value -- no unescaping occurs. This
is not an independent design choice; it mirrors the documented grammar
contract so that a well-formed fixture parses identically in spirit (though
via different code) in both places, and a genuine disagreement is
detectable rather than being an artifact of the oracle using a different
grammar than the one actually in force.
"""

from __future__ import annotations

import unicodedata  # stdlib only; NOT used for folding (see ascii_fold_for_test_fixtures below)
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


class OracleError(Exception):
    """Raised when the oracle cannot confidently produce a projection for a
    document -- e.g. malformed/ambiguous input. The oracle does not attempt
    to classify malformed input into the same error taxonomy as
    tools/sfm_master_core.py; it simply refuses to produce a result, which is
    sufficient for its role (see module docstring: SOURCE COMPLETENESS +
    STRUCTURAL PARITY for well-formed documents, not a competing malformed-
    input classifier)."""

    def __init__(self, message: str, line: Optional[int] = None, col: Optional[int] = None):
        self.line = line
        self.col = col
        loc = f" (line {line}" + (f", col {col}" if col is not None else "") + ")" if line is not None else ""
        super().__init__(message + loc)


# ---------------------------------------------------------------------------
# Tokenizer: hand-written character scanner.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _Tok:
    kind: str  # "STR", "WORD", "OPEN", "CLOSE"
    value: str
    line: int
    col: int


def _tokenize(text: str) -> List[_Tok]:
    tokens: List[_Tok] = []
    i = 0
    n = len(text)
    line = 1
    col = 1

    def advance(k: int = 1) -> None:
        nonlocal i, line, col
        for _ in range(k):
            if i >= n:
                return
            if text[i] == "\n":
                line += 1
                col = 1
            else:
                col += 1
            i += 1

    while i < n:
        ch = text[i]

        if ch in " \t\r\n":
            advance()
            continue

        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                advance()
            continue

        if ch == "{":
            tokens.append(_Tok("OPEN", "{", line, col))
            advance()
            continue

        if ch == "}":
            tokens.append(_Tok("CLOSE", "}", line, col))
            advance()
            continue

        if ch == '"':
            start_line, start_col = line, col
            advance()  # consume opening quote
            buf: List[str] = []
            closed = False
            while i < n:
                c = text[i]
                if c == "\n":
                    break  # unterminated on this line -- grammar requires same-line closure
                if c == "\\" and i + 1 < n and text[i + 1] != "\n":
                    buf.append(c)
                    buf.append(text[i + 1])
                    advance(2)
                    continue
                if c == '"':
                    advance()
                    closed = True
                    break
                buf.append(c)
                advance()
            if not closed:
                raise OracleError("unterminated quoted string", start_line, start_col)
            tokens.append(_Tok("STR", "".join(buf), start_line, start_col))
            continue

        # bare word: run of characters not whitespace/quote/brace
        start_line, start_col = line, col
        buf = []
        while i < n and text[i] not in ' \t\r\n"{}':
            buf.append(text[i])
            advance()
        if not buf:
            raise OracleError(f"unrecognized character {ch!r}", line, col)
        tokens.append(_Tok("WORD", "".join(buf), start_line, start_col))

    return tokens


# ---------------------------------------------------------------------------
# Result data model.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OracleGroup:
    declare_order: int
    name: str
    ancestry: Tuple[str, ...]  # ancestor names, root-to-parent, NOT including self
    full_path: str
    parent_path: Optional[str]
    sibling_index: int
    is_parentless: bool


@dataclass(frozen=True)
class OracleControl:
    global_order: int
    token: str
    owning_path: str
    local_rank: int


@dataclass(frozen=True)
class OracleMetadataEntry:
    owning_path: str
    local_order: int
    key: str
    value: str


@dataclass
class OracleResult:
    groups: List[OracleGroup]
    controls: List[OracleControl]
    metadata: List[OracleMetadataEntry]

    # ---- convenience projections (Part 3.D coverage) --------------------
    def parentless_groups(self) -> List[OracleGroup]:
        return [g for g in self.groups if g.is_parentless]

    def group_count(self) -> int:
        return len(self.groups)

    def control_count(self) -> int:
        return len(self.controls)

    def metadata_count(self) -> int:
        return len(self.metadata)

    def first_control(self) -> Optional[OracleControl]:
        return self.controls[0] if self.controls else None

    def last_control(self) -> Optional[OracleControl]:
        return self.controls[-1] if self.controls else None

    def first_group(self) -> Optional[OracleGroup]:
        return self.groups[0] if self.groups else None

    def last_group(self) -> Optional[OracleGroup]:
        return self.groups[-1] if self.groups else None

    def controls_by_path(self) -> Dict[str, List[OracleControl]]:
        out: Dict[str, List[OracleControl]] = {}
        for c in self.controls:
            out.setdefault(c.owning_path, []).append(c)
        return out

    def metadata_by_path(self) -> Dict[str, List[OracleMetadataEntry]]:
        out: Dict[str, List[OracleMetadataEntry]] = {}
        for m in self.metadata:
            out.setdefault(m.owning_path, []).append(m)
        return out

    def literal_multiplicity(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for c in self.controls:
            counts[c.token] = counts.get(c.token, 0) + 1
        return counts


# ---------------------------------------------------------------------------
# Recursive-descent structural parser.
# ---------------------------------------------------------------------------

def _parse_tokens(tokens: List[_Tok]) -> OracleResult:
    n = len(tokens)
    groups: List[OracleGroup] = []
    raw_controls: List[Tuple[str, str]] = []  # (token, owning_path), encounter order
    raw_metadata: List[Tuple[str, str, str]] = []  # (owning_path, key, value), encounter order
    declare_counter = [0]

    def parse_group(name: str, ancestry: Tuple[str, ...], parent_path: Optional[str],
                     sibling_index: int, idx: int) -> int:
        # idx points at the OPEN token for this group.
        assert tokens[idx].kind == "OPEN"
        idx += 1

        full_path = "/".join(list(ancestry) + [name])
        declare_order = declare_counter[0]
        declare_counter[0] += 1
        groups.append(OracleGroup(
            declare_order=declare_order,
            name=name,
            ancestry=ancestry,
            full_path=full_path,
            parent_path=parent_path,
            sibling_index=sibling_index,
            is_parentless=(parent_path is None),
        ))

        local_metadata_order = 0
        local_child_count = 0
        child_ancestry = tuple(list(ancestry) + [name])

        while True:
            if idx >= n:
                raise OracleError(f"truncated group {full_path!r} (missing closing brace)")
            tok = tokens[idx]

            if tok.kind == "CLOSE":
                return idx + 1

            if tok.kind in ("STR", "WORD"):
                nxt = tokens[idx + 1] if idx + 1 < n else None
                if nxt is not None and nxt.kind == "OPEN":
                    idx = parse_group(tok.value, child_ancestry, full_path, local_child_count, idx + 1)
                    local_child_count += 1
                    continue
                if tok.kind == "STR" and nxt is not None and nxt.kind == "STR":
                    key, value = tok.value, nxt.value
                    if key == "control":
                        raw_controls.append((value, full_path))
                    else:
                        raw_metadata.append((full_path, key, value))
                        local_metadata_order += 1
                    idx += 2
                    continue
                raise OracleError(
                    f"unrecognized token sequence inside {full_path!r}: {tok.kind} {tok.value!r}",
                    tok.line, tok.col,
                )

            raise OracleError(f"unexpected token {tok.kind} inside {full_path!r}", tok.line, tok.col)

    idx = 0
    top_sibling = 0
    while idx < n:
        tok = tokens[idx]
        if tok.kind in ("STR", "WORD"):
            nxt = tokens[idx + 1] if idx + 1 < n else None
            if nxt is not None and nxt.kind == "OPEN":
                idx = parse_group(tok.value, tuple(), None, top_sibling, idx + 1)
                top_sibling += 1
                continue
        raise OracleError(f"unexpected top-level token {tok.kind} {tok.value!r}", tok.line, tok.col)

    # Second pass: assign local_rank to controls, grouped by owning_path, in encounter order.
    local_seen: Dict[str, int] = {}
    controls: List[OracleControl] = []
    for i, (token, path) in enumerate(raw_controls):
        rank = local_seen.get(path, 0)
        local_seen[path] = rank + 1
        controls.append(OracleControl(global_order=i, token=token, owning_path=path, local_rank=rank))

    metadata: List[OracleMetadataEntry] = []
    local_meta_seen: Dict[str, int] = {}
    for path, key, value in raw_metadata:
        order = local_meta_seen.get(path, 0)
        local_meta_seen[path] = order + 1
        metadata.append(OracleMetadataEntry(owning_path=path, local_order=order, key=key, value=value))

    return OracleResult(groups=groups, controls=controls, metadata=metadata)


# ---------------------------------------------------------------------------
# Public entry points.
# ---------------------------------------------------------------------------

def scan_bytes(data: bytes) -> OracleResult:
    """Independently scan Master-shaped bytes into an OracleResult. Raises
    OracleError for anything it cannot confidently structure (malformed
    input is not this module's job to classify -- see module docstring)."""
    has_bom = data.startswith(b"\xef\xbb\xbf")
    text = data.decode("utf-8-sig" if has_bom else "utf-8")  # stdlib decode; raises UnicodeDecodeError on malformed UTF-8
    tokens = _tokenize(text)
    return _parse_tokens(tokens)


def scan_file(path) -> OracleResult:
    with open(path, "rb") as f:
        data = f.read()
    return scan_bytes(data)


# ---------------------------------------------------------------------------
# Test-only ASCII-fold helper (Part 4): NOT fold authority. Used only to
# construct hand-audited fixture expectations. Deliberately tiny and kept
# separate from anything resembling production fold-conflict policy.
# ---------------------------------------------------------------------------

def ascii_fold_for_test_fixtures(s: str) -> str:
    """TEST-ONLY. Folds ASCII A-Z to a-z, exactly like the production
    authority (tools/sfm_master_core.ascii_fold), for the sole purpose of
    letting fixture-authoring test code state its own expectations (e.g.
    'these two literals should land in the same fold family') without
    hand-computing folded keys. This function is never used by scan_bytes/
    scan_file above, is never treated as a completeness or conflict
    authority, and must not be imported by anything outside test code."""
    return "".join(chr(ord(ch) + 32) if "A" <= ch <= "Z" else ch for ch in s)
