#!/usr/bin/env python3
"""General-purpose, source-agnostic semantic core for SFM animation-group
Master files (the `groupFile { ... }` grammar used by
sfm_defaultanimationgroups.txt and any syntactically compatible custom
Master).

This module is the single production authority for:

  - ASCII-only case folding (the "native-Rebuild" identity)
  - tokenization of the supported grammar
  - structural parsing (group hierarchy, control occurrences)
  - group metadata presence/value representation
  - explicit source-order (occurrence rank) representation
  - ASCII-fold family construction

It has NO dependency on:
  - the official canonical Master's filename, path, or SHA-256
  - the current repository root
  - Git
  - Claude Code
  - today's control/group counts
  - any official-only taxonomy assumption

Every entry point that takes Master content takes it as bytes/a path, not as
"the" repository Master, so a future standalone compiler (official build or
an advanced user's custom Master) can call the exact same functions this
module exposes to `tools/validate_master.py`.

This module performs NO I/O side effects beyond reading the file it is asked
to parse, NO repair of malformed input, and NO semantic/taxonomy
classification decisions (see CLAUDE.md Section 22 -- destination decisions
are never made by parsing infrastructure).

Grammar summary (as actually observed in the canonical Master and encoded
here, not assumed):
    groupFile
    {
        "GroupName"
        {
            "metadataKey"       "value"
            "control"           "Exact Literal"
            "ChildGroup"
            { ... }
        }
    }
  - The outermost group name ("groupFile") is conventionally a bare,
    unquoted word; every other name observed in the canonical Master is a
    quoted string, but this module accepts either for any group, since the
    tokenizer does not distinguish grammatical role by quoting style.
  - `//` begins a line comment; the rest of the line is ignored.
  - A quoted string must open and close on the SAME line. This is not a new
    restriction invented here: the tokenizer has always operated line-by-
    line (see `_tokenize_line`), so a value spanning multiple lines was
    never actually supported -- this module simply makes that boundary an
    explicit, reported grammar error instead of silently discarding the
    unterminated fragment.
  - Any "key" "value" pair whose key is not exactly "control" is treated as
    group metadata, keyed by the literal key string. No metadata key is
    hardcoded into the grammar rules for parsing purposes (only descriptive
    notes below record what the *current* canonical Master actually uses).

Metadata actually observed in the canonical Master at the time this module
was written (informational only -- NOT a closed-world assumption enforced by
the parser):
    groupColor  (group-level, RGBA quoted string)
    selectable  ("0" or "1")
    visible     ("0" or "1")
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

# ---------------------------------------------------------------------------
# ASCII fold -- the single production authority.
# ---------------------------------------------------------------------------


def ascii_fold(literal: str) -> str:
    """Fold ONLY ASCII A-Z to a-z. Every other character, including all
    non-ASCII code points, punctuation, digits, and whitespace, passes
    through unchanged. This is deliberately not Unicode casefold/lower,
    not locale folding, and not punctuation/whitespace normalization."""
    return "".join(
        chr(ord(ch) + 32) if "A" <= ch <= "Z" else ch for ch in literal
    )


def sha256_of_bytes(data: bytes) -> str:
    """Whole-byte SHA-256 hex digest. Centralizes the hashing convention
    (raw bytes, not decoded/normalized text) so a compiler, a validator, and
    any future manifest agree by construction rather than by convention."""
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Tokenizer.
# ---------------------------------------------------------------------------

# Group 1: a quoted string (with backslash-escaping), required to close on
#          the same line it opens (see module docstring).
# Group 2/3: brace tokens.
# Group 4: a line comment -- consumes the rest of the line.
# Group 5: a bare, unquoted word (used for the root "groupFile" name and, in
#          principle, any other unquoted name/value the grammar might carry).
TOKEN_RE = re.compile(r'"((?:[^"\\]|\\.)*)"|(\{)|(\})|(//[^\n]*)|([^\s"{}]+)')


@dataclass(frozen=True)
class GrammarError:
    """A location-anchored report of content that does not fit the
    supported grammar. Parsing does not raise for these -- they are
    collected so a caller (validator or compiler) can see every problem in
    one pass, exactly as `tools/validate_master.py` has always reported
    multiple structural issues together. A `MasterParseResult` (or the
    legacy `ParseResult`) with ANY grammar error present must NOT be
    treated as a complete or trustworthy semantic graph by any consumer,
    including a future compiler, which must refuse to compile."""

    kind: str
    line: int
    col: Optional[int]
    message: str
    source_name: Optional[str] = None


class Token:
    """A single lexical token: (line, kind, value, col). `kind` is one of
    "STR", "OPEN", "CLOSE", or "WORD". `col` is the 1-based column of the
    token's first character."""

    __slots__ = ("line", "kind", "value", "col")

    def __init__(self, line, kind, value, col):
        self.line = line
        self.kind = kind
        self.value = value
        self.col = col

    def __repr__(self):
        return f"Token(line={self.line}, kind={self.kind!r}, value={self.value!r}, col={self.col})"


def _tokenize_line(line: str, line_no: int, source_name, errors: List[GrammarError]) -> List[Token]:
    """Tokenize one line, reporting any content that the supported grammar
    cannot classify (most importantly: a quote that never closes on this
    line) as a GrammarError rather than silently dropping it."""
    tokens: List[Token] = []
    pos = 0
    length = len(line)
    for m in TOKEN_RE.finditer(line):
        gap = line[pos:m.start()]
        if gap.strip():
            errors.append(GrammarError(
                kind="unrecognized_content",
                line=line_no,
                col=pos + 1,
                message=f"Unrecognized content {gap!r} before column {m.start() + 1}.",
                source_name=source_name,
            ))
        if m.group(1) is not None:
            tokens.append(Token(line_no, "STR", m.group(1), m.start() + 1))
        elif m.group(2):
            tokens.append(Token(line_no, "OPEN", "{", m.start() + 1))
        elif m.group(3):
            tokens.append(Token(line_no, "CLOSE", "}", m.start() + 1))
        elif m.group(4):
            pos = length
            break
        elif m.group(5):
            tokens.append(Token(line_no, "WORD", m.group(5), m.start() + 1))
        pos = m.end()
    trailing = line[pos:length]
    if trailing.strip():
        errors.append(GrammarError(
            kind="unrecognized_content",
            line=line_no,
            col=pos + 1,
            message=f"Unrecognized trailing content {trailing!r}.",
            source_name=source_name,
        ))
    return tokens


def tokenize(lines: List[str], source_name: Optional[str] = None):
    """Tokenize the full line list. Returns `(tokens, errors)`.

    `tokens` is a flat list of `Token` in file order. `errors` is a list of
    `GrammarError` for any content the grammar could not classify (most
    notably an unterminated quoted string -- see module docstring for why
    this is a same-line, not a cross-line, requirement).

    This never raises for malformed *content*; it raises only for
    programming errors (e.g. non-string input), matching the existing
    validator's "report, do not crash" philosophy."""
    errors: List[GrammarError] = []
    tokens: List[Token] = []
    for line_no, line in enumerate(lines, start=1):
        tokens.extend(_tokenize_line(line, line_no, source_name, errors))
    return tokens, errors


# ---------------------------------------------------------------------------
# Structural parsing.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MetadataEntry:
    key: str
    value: str
    line: int


@dataclass
class GroupMetadata:
    """Presence-aware group metadata. Every "key" "value" pair encountered
    as a direct member of a group (any key other than exactly "control") is
    recorded here, in source order, INCLUDING duplicates of the same key --
    nothing is collapsed or overwritten. Absence of a key from `entries` is
    the ONLY representation of "this group never had that key"; it is never
    conflated with an explicit falsy/default value."""

    entries: List[MetadataEntry] = field(default_factory=list)

    def present(self, key: str) -> bool:
        return any(e.key == key for e in self.entries)

    def values(self, key: str) -> List[str]:
        return [e.value for e in self.entries if e.key == key]

    def value(self, key: str) -> Optional[str]:
        """The single value for `key`, or None if the key is absent OR
        appears more than once (an ambiguous/duplicate case the caller must
        handle explicitly via `values()`/`present()` -- this convenience
        method never silently picks a "winning" duplicate)."""
        vs = self.values(key)
        return vs[0] if len(vs) == 1 else None

    def keys(self) -> Set[str]:
        return {e.key for e in self.entries}


@dataclass(frozen=True)
class Occurrence:
    """One parsed `"control" "LITERAL"` occurrence."""

    literal: str
    full_path: str
    line: int
    global_rank: int  # 0-based, source order across the whole file
    local_rank: int  # 0-based, source order among occurrences sharing full_path


@dataclass
class Group:
    name: str
    full_path: str
    parent_path: Optional[str]  # None only for the implicit outermost wrapper group (see module docstring);
                                 # derived structurally from the parser's own stack state at close time,
                                 # never by re-splitting `full_path` as a string.
    name_line: int
    open_line: int
    close_line: int
    declare_order: int  # 0-based, global token-encounter order in which this group's name was declared.
                         # `open_line` is NOT a unique ordering key (the grammar permits multiple sibling
                         # groups declared on one source line); this field is the ordering authority.
    depth: int  # 1 == direct child of the implicit wrapper, matching prior convention
    sibling_rank: int  # 0-based, among children of the same parent, ordered by declare_order
    child_paths: List[str] = field(default_factory=list)  # ordered by declare_order
    metadata: GroupMetadata = field(default_factory=GroupMetadata)
    local_occurrence_global_ranks: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class FoldFamily:
    """All evidence for one ASCII-fold key: every exact spelling, every
    occurrence, and every destination it currently appears at. Deliberately
    NOT reduced to fold -> one destination; a fold with more than one
    destination is a conflict regardless of whether one exact spelling
    happens to match a hypothetical query (see module docstring / Phase A
    Part 4.8)."""

    fold_key: str
    exact_spellings: Set[str]
    occurrence_global_ranks: List[int]
    destinations: Set[str]

    @property
    def is_conflict(self) -> bool:
        return len(self.destinations) > 1


@dataclass
class MasterParseResult:
    source_name: Optional[str]
    source_sha256: str
    groups: List[Group]  # all groups, in declare_order (token-encounter order)
    groups_by_path: Dict[str, Group]
    wrapper_paths: List[str]  # the parentless "document" group(s) -- e.g. ["groupFile"] for the
                               # official Master; a real, ordinary Group like any other (see module
                               # docstring / Phase B0.1). Not hardcoded to any specific name.
    root_paths: List[str]  # the semantically-meaningful taxonomy-root groups -- children of the
                            # single wrapper when exactly one exists, else identical to wrapper_paths
                            # (see the long comment in parse_master_bytes for the full rationale)
    occurrences: List[Occurrence]  # global source order

    grammar_errors: List[GrammarError]
    unmatched_closes: List[int]
    unmatched_opens: List[tuple]  # (name, name_line)
    stack_depth_at_eof: int

    @property
    def ok(self) -> bool:
        """True only if the parse is structurally complete and every token
        was classifiable under the supported grammar. A caller (validator
        or future compiler) MUST check this before treating `groups` /
        `occurrences` as a complete, trustworthy semantic graph."""
        return (
            not self.grammar_errors
            and not self.unmatched_closes
            and not self.unmatched_opens
            and self.stack_depth_at_eof == 0
        )


def _parse_tokens(tokens: List[Token], source_name: Optional[str], token_errors: List[GrammarError]):
    """The single hierarchy-construction algorithm, shared by every public
    entry point in this module. Returns a dict of raw materials consumed by
    both the legacy-shape adapter (`parse_structure`) and the rich-shape
    adapter (`parse_master_bytes`).

    Phase B0.1 hardening (Astra findings):

    - Every non-comment, non-brace token must be consumed by one of exactly
      three recognized shapes -- name+OPEN, "key" "value" (BOTH quoted), or
      "control" "LITERAL" -- or it is reported as a `GrammarError` instead
      of being silently skipped. This includes a bare/unquoted key, a bare/
      unquoted value, a fully bare key+value pair, and a token with no
      recognizable partner at all.
    - A group name containing "/" is rejected: canonical full paths are
      "/"-joined, so a literal "/" inside a single name would make path
      identity ambiguous. This is a deliberate, documented compatibility
      constraint (see module docstring), not an escaping scheme.
    - Two sibling groups (same parent, same exact name) that would resolve
      to the same canonical full path are rejected as structurally
      ambiguous. Group full-path identity must be unique; this is distinct
      from, and does not affect, this module's separate support for
      duplicate CONTROL occurrences (see `Occurrence`), which remain fully
      representable.
    - Group declaration/sibling/child order is derived from an explicit
      token-encounter counter (`declare_order`), not from `open_line`.
      `open_line` alone is not a unique ordering key: the grammar permits
      multiple sibling groups declared on the same source line, and a
      close-order or line-order sort would silently tie-break such
      siblings by an accidental construction order instead of true
      left-to-right declaration order.
    - A group's parent is recorded directly from the parser's own stack
      state at the moment the group is closed (`parent_path` computed from
      the *remaining* stack, not by re-splitting the child's own full-path
      string after the fact). This guarantees every parent relationship
      comes from parsed structure, never from string inference, and is
      trivially free of self-parenting or orphaning by construction of the
      stack itself.
    """
    errors: List[GrammarError] = list(token_errors)

    # stack frames: name, name_line, open_line, declare_order,
    # metadata(GroupMetadata), children(list of full_path)
    stack = []
    raw_groups = []  # dicts, appended on CLOSE; parent_path/declare_order already final at append time
    raw_occurrences = []  # dicts: literal, full_path, line
    seen_group_paths: Dict[str, dict] = {}  # full_path -> first raw_group dict declared at that path
    declare_counter = [0]  # boxed so the nested helper can mutate it

    def next_declare_order():
        v = declare_counter[0]
        declare_counter[0] += 1
        return v

    idx = 0
    n = len(tokens)
    while idx < n:
        tok = tokens[idx]
        if tok.kind in ("STR", "WORD"):
            nxt = tokens[idx + 1] if idx + 1 < n else None

            if nxt is not None and nxt.kind == "OPEN":
                name = tok.value
                if "/" in name:
                    errors.append(GrammarError(
                        kind="slash_in_group_name",
                        line=tok.line,
                        col=tok.col,
                        message=(
                            f"Group name {name!r} contains \"/\", the canonical path separator; "
                            "this would make full-path identity ambiguous."
                        ),
                        source_name=source_name,
                    ))
                stack.append({
                    "name": name,
                    "name_line": tok.line,
                    "open_line": nxt.line,
                    "declare_order": next_declare_order(),
                    "metadata": GroupMetadata(),
                    "children": [],
                })
                idx += 2
                continue

            if tok.kind == "STR" and nxt is not None and nxt.kind == "STR":
                # The only recognized key/value shape: BOTH key and value quoted.
                key = tok.value
                value = nxt.value
                if key == "control":
                    if not stack:
                        errors.append(GrammarError(
                            kind="control_outside_any_group",
                            line=tok.line,
                            col=tok.col,
                            message="A \"control\" entry appears outside any group.",
                            source_name=source_name,
                        ))
                    else:
                        current_path = "/".join(frame["name"] for frame in stack)
                        raw_occurrences.append({"literal": value, "full_path": current_path, "line": tok.line})
                else:
                    if stack:
                        stack[-1]["metadata"].entries.append(MetadataEntry(key=key, value=value, line=tok.line))
                    else:
                        errors.append(GrammarError(
                            kind="metadata_outside_any_group",
                            line=tok.line,
                            col=tok.col,
                            message=f"Metadata key {key!r} appears outside any group.",
                            source_name=source_name,
                        ))
                idx += 2
                continue

            # Everything past this point is a token that looked like it
            # might be starting a key/value pair or a name, but does not
            # match a recognized shape. Reported, never silently skipped.
            if nxt is not None and nxt.kind == "STR" and tok.kind == "WORD":
                errors.append(GrammarError(
                    kind="unquoted_metadata_key",
                    line=tok.line,
                    col=tok.col,
                    message=f"Key {tok.value!r} is not quoted; only \"key\" \"value\" (both quoted) is supported.",
                    source_name=source_name,
                ))
                idx += 2
                continue
            if nxt is not None and nxt.kind == "WORD" and tok.kind == "STR":
                errors.append(GrammarError(
                    kind="unquoted_metadata_value",
                    line=tok.line,
                    col=tok.col,
                    message=f"Value for key {tok.value!r} is not quoted; only \"key\" \"value\" (both quoted) is supported.",
                    source_name=source_name,
                ))
                idx += 2
                continue
            if nxt is not None and nxt.kind == "WORD" and tok.kind == "WORD":
                errors.append(GrammarError(
                    kind="bare_property_value_pair",
                    line=tok.line,
                    col=tok.col,
                    message=f"Bare, unquoted {tok.value!r} {nxt.value!r} pair is not supported grammar.",
                    source_name=source_name,
                ))
                idx += 2
                continue

            # No recognizable partner at all (next token is CLOSE, or this
            # is the last token in the file).
            errors.append(GrammarError(
                kind="dangling_token",
                line=tok.line,
                col=tok.col,
                message=f"Token {tok.value!r} ({tok.kind}) does not form a supported group-name or key/value construct.",
                source_name=source_name,
            ))
            idx += 1
            continue
        elif tok.kind == "CLOSE":
            if not stack:
                errors.append(GrammarError(
                    kind="unmatched_closing_brace",
                    line=tok.line,
                    col=tok.col,
                    message="Unmatched closing brace.",
                    source_name=source_name,
                ))
                idx += 1
                continue
            frame = stack.pop()
            full_path = "/".join([f["name"] for f in stack] + [frame["name"]])
            parent_path = "/".join(f["name"] for f in stack) if stack else None
            if stack:
                stack[-1]["children"].append(full_path)
            raw_group = {
                "name": frame["name"],
                "full_path": full_path,
                "parent_path": parent_path,
                "name_line": frame["name_line"],
                "open_line": frame["open_line"],
                "close_line": tok.line,
                "declare_order": frame["declare_order"],
                "depth": len(stack) + 1,
                "metadata": frame["metadata"],
                "children": frame["children"],
            }
            if full_path in seen_group_paths:
                first = seen_group_paths[full_path]
                errors.append(GrammarError(
                    kind="duplicate_group_path",
                    line=frame["name_line"],
                    col=None,
                    message=(
                        f"Group path {full_path!r} declared more than once "
                        f"(first declared at line {first['name_line']}, "
                        f"again at line {frame['name_line']}). Group full-path identity must be unique; "
                        "this is a distinct rule from the module's separate, intentional support for "
                        "duplicate CONTROL occurrences."
                    ),
                    source_name=source_name,
                ))
            else:
                seen_group_paths[full_path] = raw_group
            raw_groups.append(raw_group)
            idx += 1
            continue
        elif tok.kind == "OPEN":
            # A "{" not immediately preceded by a name token is not
            # attributable to any group under the supported grammar. Unlike
            # the pre-B0 parser (which silently advanced past it), this is
            # now an explicit error: silently ignoring it would corrupt
            # hierarchy attribution for everything nested inside, because
            # the eventual matching "}" would incorrectly pop whatever
            # frame is actually on top of the stack.
            errors.append(GrammarError(
                kind="brace_without_name",
                line=tok.line,
                col=tok.col,
                message="Opening brace is not attributable to any preceding group name.",
                source_name=source_name,
            ))
            idx += 1
            continue

    unmatched_opens = [(f["name"], f["name_line"]) for f in stack]

    return {
        "raw_groups": raw_groups,
        "raw_occurrences": raw_occurrences,
        "errors": errors,
        "unmatched_closes": [e.line for e in errors if e.kind == "unmatched_closing_brace"],
        "unmatched_opens": unmatched_opens,
        "stack_depth_at_eof": len(stack),
    }


# ---------------------------------------------------------------------------
# Legacy-shape adapter -- preserves tools/validate_master.py's existing
# public contract (ParseResult with list-of-dict groups, list-of-tuple
# controls) exactly, so existing behavior and existing tests are unchanged.
# ---------------------------------------------------------------------------


class ParseResult:
    def __init__(self):
        self.groups = []  # list of dicts: name, full_path, name_line, open_line, close_line, depth
        self.controls = []  # list of (literal, full_path, line_no)
        self.unmatched_closes = []  # line numbers
        self.unmatched_opens = []  # (name, name_line)
        self.stack_depth_at_eof = 0
        # Additive fields (new in B0): safe for any pre-existing consumer
        # that only reads the fields above, since attribute access for
        # fields it never asks about cannot break it.
        self.grammar_errors = []


def parse_structure(lines: List[str]) -> ParseResult:
    """Structurally parse group/control hierarchy by brace depth and full
    path, independent of line-based formatting assumptions. Comments and
    header prose are ignored via the tokenizer; unusual-but-valid historical
    formatting (e.g. a brace sharing a line with other content) parses
    identically to conventional formatting, because detection is
    token-order-based, not line-shape-based.

    This is the exact function `tools/validate_master.py` has always
    called; its return shape (`.groups` as list-of-dict, `.controls` as
    list-of-tuple, `.unmatched_closes`/`.unmatched_opens`/
    `.stack_depth_at_eof`) is unchanged from before Phase B0. A new
    `.grammar_errors` field is additive only."""
    tokens, tok_errors = tokenize(lines)
    raw = _parse_tokens(tokens, source_name=None, token_errors=tok_errors)

    result = ParseResult()
    for g in raw["raw_groups"]:
        result.groups.append({
            "name": g["name"],
            "full_path": g["full_path"],
            "name_line": g["name_line"],
            "open_line": g["open_line"],
            "close_line": g["close_line"],
            "depth": g["depth"],
        })
    for occ in raw["raw_occurrences"]:
        result.controls.append((occ["literal"], occ["full_path"], occ["line"]))
    result.unmatched_closes = raw["unmatched_closes"]
    result.unmatched_opens = raw["unmatched_opens"]
    result.stack_depth_at_eof = raw["stack_depth_at_eof"]
    result.grammar_errors = raw["errors"]
    return result


# ---------------------------------------------------------------------------
# Rich-shape API -- the primary interface for a future compiler (official or
# advanced-user, official Master or arbitrary compatible custom Master).
# ---------------------------------------------------------------------------


def parse_master_bytes(data: bytes, source_name: Optional[str] = None) -> MasterParseResult:
    """Parse arbitrary Master-shaped bytes into the full rich semantic
    representation. Takes no dependency on any official filename, path,
    repository location, or Git state -- `data` may come from ANY
    syntactically compatible source, official or custom.

    Decoding follows the same convention this project has used throughout:
    UTF-8, with a UTF-8 BOM (if present) stripped via `utf-8-sig`. A decode
    failure raises `UnicodeDecodeError` (matching `validate_master.py`'s
    existing "fatal, not a data-driven FAIL" treatment of this case)."""
    has_bom = data.startswith(b"\xef\xbb\xbf")
    text = data.decode("utf-8-sig" if has_bom else "utf-8")
    lines = text.splitlines()

    tokens, tok_errors = tokenize(lines, source_name=source_name)
    raw = _parse_tokens(tokens, source_name=source_name, token_errors=tok_errors)

    # Occurrences: global + local rank, both 0-based (chosen and documented
    # here; see module docstring / Phase B0 audit for the rationale).
    occurrences: List[Occurrence] = []
    local_seen: Dict[str, int] = {}
    for i, occ in enumerate(raw["raw_occurrences"]):
        path = occ["full_path"]
        local_rank = local_seen.get(path, 0)
        local_seen[path] = local_rank + 1
        occurrences.append(Occurrence(
            literal=occ["literal"],
            full_path=path,
            line=occ["line"],
            global_rank=i,
            local_rank=local_rank,
        ))

    occ_index_by_global_rank = {o.global_rank: o for o in occurrences}
    occurrences_by_path: Dict[str, List[int]] = {}
    for o in occurrences:
        occurrences_by_path.setdefault(o.full_path, []).append(o.global_rank)

    # Groups: `parent_path` was already computed structurally, from the
    # parser's own stack state at close time (see `_parse_tokens`) -- never
    # by re-splitting `full_path` as a string, per Phase B0.1 (Astra: "do
    # not infer a missing parent by path-string splitting"). Sibling/child
    # order is derived from `declare_order` (token-encounter order), NOT
    # `open_line` -- `open_line` is not a unique ordering key, since the
    # grammar permits multiple sibling groups declared on one source line.
    by_full_path: Dict[str, dict] = {g["full_path"]: g for g in raw["raw_groups"]}

    children_by_parent: Dict[Optional[str], List[dict]] = {}
    for g in raw["raw_groups"]:
        children_by_parent.setdefault(g["parent_path"], []).append(g)
    for lst in children_by_parent.values():
        lst.sort(key=lambda g: g["declare_order"])

    sibling_rank_of: Dict[str, int] = {}
    for parent, kids in children_by_parent.items():
        for rank, g in enumerate(kids):
            sibling_rank_of[g["full_path"]] = rank

    groups: List[Group] = []
    groups_by_path: Dict[str, Group] = {}
    for g in raw["raw_groups"]:
        ordered_children = sorted(g["children"], key=lambda p: by_full_path[p]["declare_order"])
        grp = Group(
            name=g["name"],
            full_path=g["full_path"],
            parent_path=g["parent_path"],
            name_line=g["name_line"],
            open_line=g["open_line"],
            close_line=g["close_line"],
            declare_order=g["declare_order"],
            depth=g["depth"],
            sibling_rank=sibling_rank_of[g["full_path"]],
            child_paths=ordered_children,
            metadata=g["metadata"],
            local_occurrence_global_ranks=list(occurrences_by_path.get(g["full_path"], [])),
        )
        groups.append(grp)
        groups_by_path[g["full_path"]] = grp

    groups.sort(key=lambda g: g.declare_order)

    # `root_paths` means the semantically-meaningful root-level taxonomy
    # groups (e.g. "Face", "Correctives", "Helpers", "RigBody" in the
    # official Master) -- the children of the single implicit outermost
    # wrapper group (conventionally named "groupFile" in the official
    # Master, but not hardcoded as that name here -- see module docstring
    # and `MasterParseResult.wrapper_paths`), NOT the wrapper itself. This
    # matches the terminology this project has used throughout every prior
    # Master-editing task ("root order" has always meant this level). A
    # well-formed document has exactly one group with no parent; if a
    # compatible custom source ever had zero or more than one (which would
    # itself already be an unusual document shape), the parentless groups
    # themselves are used as both `wrapper_paths` and `root_paths` directly,
    # rather than guessing at an implicit wrapper that may not exist.
    outermost = children_by_parent.get(None, [])
    wrapper_paths = [g["full_path"] for g in sorted(outermost, key=lambda g: g["declare_order"])]
    if len(outermost) == 1:
        wrapper_path = outermost[0]["full_path"]
        root_paths = [g["full_path"] for g in children_by_parent.get(wrapper_path, [])]
    else:
        root_paths = list(wrapper_paths)

    return MasterParseResult(
        source_name=source_name,
        source_sha256=sha256_of_bytes(data),
        groups=groups,
        groups_by_path=groups_by_path,
        wrapper_paths=wrapper_paths,
        root_paths=root_paths,
        occurrences=occurrences,
        grammar_errors=raw["errors"],
        unmatched_closes=raw["unmatched_closes"],
        unmatched_opens=raw["unmatched_opens"],
        stack_depth_at_eof=raw["stack_depth_at_eof"],
    )


def parse_master_file(path) -> MasterParseResult:
    """Read and parse a Master file from an arbitrary path -- official or
    custom. No assumption is made about the path's location, filename, or
    relationship to any repository."""
    path = Path(path)
    data = path.read_bytes()
    return parse_master_bytes(data, source_name=str(path))


# ---------------------------------------------------------------------------
# Fold-family construction.
# ---------------------------------------------------------------------------


def build_fold_families(occurrences: List[Occurrence]) -> Dict[str, FoldFamily]:
    """Group occurrences by ASCII-fold key, retaining every exact spelling,
    every occurrence reference, and every destination -- never reduced
    prematurely to fold -> one destination. `family.is_conflict` is True
    whenever more than one destination exists for the fold, regardless of
    whether any single exact spelling happens to match a hypothetical
    query (see `FoldFamily` docstring)."""
    spellings: Dict[str, Set[str]] = {}
    ranks: Dict[str, List[int]] = {}
    destinations: Dict[str, Set[str]] = {}

    for occ in occurrences:
        key = ascii_fold(occ.literal)
        spellings.setdefault(key, set()).add(occ.literal)
        ranks.setdefault(key, []).append(occ.global_rank)
        destinations.setdefault(key, set()).add(occ.full_path)

    families: Dict[str, FoldFamily] = {}
    for key in spellings:
        families[key] = FoldFamily(
            fold_key=key,
            exact_spellings=spellings[key],
            occurrence_global_ranks=ranks[key],
            destinations=destinations[key],
        )
    return families
