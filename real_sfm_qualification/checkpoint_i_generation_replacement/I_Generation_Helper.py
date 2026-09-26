# -*- coding: utf-8 -*-
"""
I_Generation_Helper -- narrow, fail-closed, SFM-DEPLOYABLE core primitives
for roadmap item I (Master generation replacement) qualification.

CORRECTION ROUND 1 (2026-09-25, independent review): this module now
contains ONLY the primitives the SFM-side checkpoint (Python 2.7.5)
needs. It has ZERO reference to tools/sfm_master_sidecar and performs NO
relative-path repo discovery -- it is safe to copy, standalone, to the
live MAINMENU directory alongside Checkpoint_I_Generation_Replacement.py
(BLOCKER 11). The Python-3-only publisher/finalizer operations
(check_only, publish, semantic-parity comparison, the G2 publication
record, and restoration finalization) now live in the separate,
repo-side-only I_Generation_Publisher.py, which imports THIS module for
its own shared primitives and requires an explicit, validated repo root
rather than guessing one from its own file location.

Dual Python 2.7.5 / Python 3 compatible throughout (no f-strings, no
pathlib, no os.replace -- not available in Python 2.7). Windows-only
(ctypes.windll) -- matches this project's own environment.

SAFETY CONTRACT (every live-mutation operation):
  - the CURRENT installed target must hash EXACTLY to the caller-
    supplied (or, for the two sanctioned high-level operations below,
    internally pinned) expected source hash before ANY byte is written;
  - any mismatch: STOP, raise GenerationHelperError, NO WRITE;
  - every mutation is a genuine OS-backed ATOMIC replacement
    (Windows MoveFileExW with MOVEFILE_REPLACE_EXISTING |
    MOVEFILE_WRITE_THROUGH) -- BLOCKER 1: there is no remove-then-rename
    sequence anywhere in this file, and therefore no interval during
    which the destination path does not exist. A replacement failure
    leaves the destination completely untouched; only the orphaned temp
    sibling is ever cleaned up on failure, never the destination;
  - every mutation returns a structured OPERATION RECORD (pre-hash,
    post-hash, source-bytes hash, timestamp, operation type,
    success/failure) -- never a bare boolean;
  - sidecar cleanup NEVER wildcards: remove_exact_sidecar() requires an
    exact SAFE BARE BASENAME (BLOCKER 2 hardening -- no path
    separators, no drive/colon, no "."/".." traversal) AND an exact
    expected SHA-256 of the file about to be removed, re-verified
    immediately before the delete.
  - BLOCKER 2: the live-mutation surface for real qualification use is
    narrowed to exactly two named operations,
    perform_g1_to_g2_replacement() and perform_g2_to_g1_restoration().
    Neither accepts arbitrary caller-supplied replacement bytes for the
    live Master: G1->G2 always constructs G2 internally as exactly
    "G1 bytes + one ASCII LF"; G2->G1 requires the proposed G1 backup
    bytes to hash to the exact pinned canonical G1 SHA-256 BEFORE
    touching the live Master. The old generic install_generation() /
    install_g2_over_g1() / restore_g1_over_g2() primitives are now
    PRIVATE (leading underscore) and exist only as tested internals;
    there is no public, generic "write arbitrary bytes to an arbitrary
    live path" surface. R3 BLOCKER 4 (2026-09-25, third independent
    review): the CLI at the bottom of this file now exposes ONLY
    read-only inventory/compare -- it no longer exposes either narrow
    mutation operation, or remove_exact_sidecar(), as a CLI subcommand
    at all. Those two Python functions remain (called directly,
    in-process, by I_Generation_Publisher.py's activate_g2_master()/
    finalize_restoration() and by the checkpoint's own path-bound I2
    wrapper) -- removing their CLI exposure closes an unbound,
    non-path-bound mutation escape hatch that bypassed the baseline-
    inventory path authority (R2 BLOCKER 5) the real orchestration
    relies on. activate_g2_master() (I_Generation_Publisher.py) is now
    literally the only external G1->G2 activation surface.

This module never touches:
  - the live production Normalizer source;
  - the authority package source;
  - the canonical Master, EXCEPT through the two explicit, hash-gated,
    narrow operations above.
Importing this module performs no I/O and no mutation by itself (no
top-level executable statement exists outside class/def bodies).

CORRECTION ROUND 2 (2026-09-25, independent review, R2 BLOCKER 5): adds
path_matches_baseline() / normalize_path_for_comparison() -- a
normalized, case-insensitive absolute-path comparator used by every
caller-facing live-mutation/finalization operation (in
I_Generation_Publisher.py and this checkpoint's own I2 wrapper) to bind
the supplied Master/authority paths to the exact paths the I1 baseline
inventory recorded, before any write is trusted. An arbitrary or wrong
path argument is never sufficient authorization by itself.
"""
import ctypes
import hashlib
import json
import os
import sys
import time


class GenerationHelperError(Exception):
    pass


# ---------------------------------------------------------------------
# Governing identity this module is pinned against -- the ONLY value
# perform_g2_to_g1_restoration() will ever accept as a valid G1 backup.
# ---------------------------------------------------------------------
EXPECTED_CANONICAL_G1_MASTER_SHA256 = (
    "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
)


# ---------------------------------------------------------------------
# Pure hashing primitives (dual Python 2.7.5 / 3 safe).
# ---------------------------------------------------------------------
def sha256_file(path):
    if not os.path.isfile(path):
        raise GenerationHelperError("File not found for hashing: %r" % (path,))
    h = hashlib.sha256()
    fp = open(path, "rb")
    try:
        while True:
            chunk = fp.read(1048576)
            if not chunk:
                break
            h.update(chunk)
    finally:
        fp.close()
    return h.hexdigest()


def _now_wall():
    return time.strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------
# BLOCKER 1: genuine OS-backed atomic replacement (Windows
# MoveFileExW), never a remove-then-rename sequence.
# ---------------------------------------------------------------------
_MOVEFILE_REPLACE_EXISTING = 0x00000001
_MOVEFILE_WRITE_THROUGH = 0x00000008


def _to_win_unicode(path):
    if isinstance(path, bytes):
        return path.decode("mbcs")
    try:
        return unicode(path)  # noqa: F821 -- Python 2 only
    except NameError:
        return path  # Python 3: str is already the right type


def _atomic_replace_file(temp_path, dest_path):
    """Replaces `dest_path` with `temp_path` as ONE atomic filesystem
    operation via the real Windows MoveFileExW API
    (MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH). There is no
    interval during which `dest_path` does not exist -- the destination
    is never deleted first. On failure, `dest_path` is guaranteed
    untouched; only the orphaned `temp_path` may remain."""
    kernel32 = ctypes.windll.kernel32
    kernel32.MoveFileExW.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
    kernel32.MoveFileExW.restype = ctypes.c_int
    ok = kernel32.MoveFileExW(
        _to_win_unicode(temp_path), _to_win_unicode(dest_path),
        _MOVEFILE_REPLACE_EXISTING | _MOVEFILE_WRITE_THROUGH,
    )
    if not ok:
        err = ctypes.GetLastError()
        raise GenerationHelperError(
            "MoveFileExW failed replacing %r with %r (WinError %d) -- the "
            "original target is guaranteed untouched by this call; an "
            "orphaned temp file may remain at %r." % (dest_path, temp_path, err, temp_path)
        )


def _atomic_write_bytes(path, data):
    """Writes `data` to `path` via a fully-flushed-and-fsync'd temp
    sibling, then one atomic MoveFileExW replacement -- never a
    pre-delete of `path`. Cleanup on failure removes ONLY the orphaned
    temp file, never `path` itself."""
    tmp_path = path + ".tmp-igen"
    fp = open(tmp_path, "wb")
    try:
        fp.write(data)
        fp.flush()
        os.fsync(fp.fileno())
    finally:
        fp.close()
    try:
        _atomic_replace_file(tmp_path, path)
    except Exception:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        raise


# ---------------------------------------------------------------------
# G2 construction.
# ---------------------------------------------------------------------
def construct_g2_bytes(g1_bytes):
    """G2 changes generation IDENTITY (a different SHA-256) without
    materially changing Master semantics: exact G1 bytes plus exactly
    one trailing ASCII LF (0x0A) byte. Deterministic, reversible
    (dropping the final LF reconstructs G1 exactly), and trivially
    verifiable."""
    if not isinstance(g1_bytes, bytes):
        raise GenerationHelperError("construct_g2_bytes requires raw bytes")
    return g1_bytes + b"\n"


def g2_bytes_are_exact_g1_plus_one_lf(g1_bytes, g2_bytes):
    return (
        len(g2_bytes) == len(g1_bytes) + 1
        and g2_bytes[:-1] == g1_bytes
        and g2_bytes[-1:] == b"\n"
    )


# ---------------------------------------------------------------------
# PRIVATE generic hash-gated mutation primitive. Not part of the public
# surface for real qualification use (BLOCKER 2) -- exists only as a
# tested internal shared by the two narrow, named operations below.
# ---------------------------------------------------------------------
def _install_generation(master_path, expected_current_sha256, new_bytes, operation_type):
    record = {
        "operation_type": operation_type,
        "wall_time": _now_wall(),
        "epoch": time.time(),
        "master_path": master_path,
        "expected_current_sha256": expected_current_sha256,
        "success": False,
    }
    pre_sha256 = sha256_file(master_path)
    record["pre_operation_master_sha256"] = pre_sha256

    if pre_sha256.lower() != expected_current_sha256.lower():
        record["error"] = (
            "refusing to write: current Master sha256 %r does not match "
            "the expected source hash %r for operation %r -- STOP, no "
            "write performed." % (pre_sha256, expected_current_sha256, operation_type)
        )
        raise GenerationHelperError(record["error"])

    new_bytes_sha256 = hashlib.sha256(new_bytes).hexdigest()
    record["source_bytes_sha256"] = new_bytes_sha256

    _atomic_write_bytes(master_path, new_bytes)

    post_sha256 = sha256_file(master_path)
    record["post_operation_master_sha256"] = post_sha256
    record["success"] = (post_sha256.lower() == new_bytes_sha256.lower())
    if not record["success"]:
        record["error"] = (
            "post-write verification failed: wrote bytes hashing to %r but "
            "the file now reads back as %r." % (new_bytes_sha256, post_sha256)
        )
        raise GenerationHelperError(record["error"])
    return record


# ---------------------------------------------------------------------
# BLOCKER 2: the ONLY two sanctioned live-mutation operations for real
# qualification use. Neither accepts arbitrary caller-supplied
# replacement bytes for the live Master.
# ---------------------------------------------------------------------
def perform_g1_to_g2_replacement(master_path, expected_g1_sha256=EXPECTED_CANONICAL_G1_MASTER_SHA256):
    """The ONLY sanctioned way to advance the live canonical Master from
    G1 to G2. G2 is always constructed INTERNALLY as exactly the
    currently-observed G1 bytes plus one ASCII LF -- no caller-supplied
    replacement bytes ever reach the live Master."""
    current_bytes = _read_bytes(master_path)
    current_sha = hashlib.sha256(current_bytes).hexdigest()
    if current_sha.lower() != expected_g1_sha256.lower():
        raise GenerationHelperError(
            "perform_g1_to_g2_replacement: current bytes at %r hash to %r, "
            "not the expected G1 %r -- STOP, no write performed."
            % (master_path, current_sha, expected_g1_sha256)
        )
    g2_bytes = construct_g2_bytes(current_bytes)
    if not g2_bytes_are_exact_g1_plus_one_lf(current_bytes, g2_bytes):
        raise GenerationHelperError(
            "perform_g1_to_g2_replacement: internally constructed G2 bytes "
            "failed their own exact-G1-plus-one-LF self-check -- STOP, no "
            "write performed."
        )
    expected_g2_sha = hashlib.sha256(g2_bytes).hexdigest()
    record = _install_generation(master_path, expected_g1_sha256, g2_bytes, u"G1_TO_G2")
    if record["post_operation_master_sha256"].lower() != expected_g2_sha.lower():
        raise GenerationHelperError(
            "perform_g1_to_g2_replacement: post-write hash %r does not "
            "match the internally-computed expected G2 %r."
            % (record["post_operation_master_sha256"], expected_g2_sha)
        )
    record["computed_g2_sha256"] = expected_g2_sha
    return record


def perform_g2_to_g1_restoration(master_path, g1_backup_bytes, expected_g2_sha256,
                                  expected_g1_sha256=EXPECTED_CANONICAL_G1_MASTER_SHA256):
    """The ONLY sanctioned way to restore the live canonical Master from
    G2 back to G1. Refuses BEFORE touching the live Master if the
    proposed G1 backup bytes do not hash to the EXACT pinned canonical
    G1 SHA-256 -- a tampered, truncated, or wrong backup can never reach
    the live Master."""
    backup_sha = hashlib.sha256(g1_backup_bytes).hexdigest()
    if backup_sha.lower() != expected_g1_sha256.lower():
        raise GenerationHelperError(
            "perform_g2_to_g1_restoration: proposed G1 backup bytes hash "
            "to %r, not the exact pinned canonical G1 %r -- STOP, no "
            "write performed." % (backup_sha, expected_g1_sha256)
        )
    return _install_generation(master_path, expected_g2_sha256, g1_backup_bytes, u"G2_TO_G1")


def _read_bytes(path):
    fp = open(path, "rb")
    try:
        return fp.read()
    finally:
        fp.close()


# ---------------------------------------------------------------------
# CORRECTION ROUND 2, R2 BLOCKER 5: every live-mutation/finalization
# operation must bind its supplied Master/authority paths to the exact
# paths the I1 baseline inventory recorded -- an arbitrary/wrong
# --master or --authority-dir argument must never be sufficient
# authorization by itself. Normalized absolute Windows path comparison
# (case-insensitive, separator-normalized -- NTFS/Win32 paths are
# case-insensitive) is dual Python 2.7.5/3 safe.
# ---------------------------------------------------------------------
def normalize_path_for_comparison(path):
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def path_matches_baseline(actual_path, baseline_path):
    if not actual_path or not baseline_path:
        return False
    return normalize_path_for_comparison(actual_path) == normalize_path_for_comparison(baseline_path)


# ---------------------------------------------------------------------
# Live-state inventory (baseline capture + restoration comparator).
# Pure read-only.
# ---------------------------------------------------------------------
MANIFEST_BASENAME = u"manifest.json"


def _list_sidecar_files(authority_dir):
    out = []
    if not os.path.isdir(authority_dir):
        return out
    for name in sorted(os.listdir(authority_dir)):
        if not name.lower().endswith(u".sfmsidecar"):
            continue
        full_path = os.path.join(authority_dir, name)
        if not os.path.isfile(full_path):
            continue
        out.append({
            "filename": name,
            "size_bytes": os.path.getsize(full_path),
            "sha256": sha256_file(full_path),
        })
    return out


def capture_live_state_inventory(master_path, authority_dir):
    """Immutable-in-spirit baseline capture: exact canonical Master
    bytes/hash/size, exact manifest.json bytes/hash, and every
    .sfmsidecar filename/size/SHA-256 in the shipped authority
    namespace. Pure read-only -- never writes anything."""
    master_sha256 = sha256_file(master_path)
    master_size = os.path.getsize(master_path)

    manifest_path = os.path.join(authority_dir, MANIFEST_BASENAME)
    manifest_exists = os.path.isfile(manifest_path)
    manifest_sha256 = sha256_file(manifest_path) if manifest_exists else None
    manifest_size = os.path.getsize(manifest_path) if manifest_exists else None

    return {
        "captured_at": _now_wall(),
        "captured_epoch": time.time(),
        "master_path": master_path,
        "master_sha256": master_sha256,
        "master_size_bytes": master_size,
        "authority_dir": authority_dir,
        "manifest_exists": manifest_exists,
        "manifest_sha256": manifest_sha256,
        "manifest_size_bytes": manifest_size,
        "sidecars": _list_sidecar_files(authority_dir),
    }


def compare_inventories(baseline, current):
    """Mechanical restoration comparator. Requires EXACT Master hash
    equality, EXACT manifest hash equality (or both consistently
    absent), and the exact same (filename, sha256) sidecar set with no
    additions, removals, or same-name content changes."""
    master_matches = (
        baseline["master_sha256"].lower() == current["master_sha256"].lower()
    )
    manifest_matches = (
        baseline["manifest_exists"] == current["manifest_exists"]
        and (
            not baseline["manifest_exists"]
            or (baseline["manifest_sha256"] or u"").lower() == (current["manifest_sha256"] or u"").lower()
        )
    )

    baseline_by_name = dict((s["filename"], s["sha256"]) for s in baseline["sidecars"])
    current_by_name = dict((s["filename"], s["sha256"]) for s in current["sidecars"])

    added = sorted(set(current_by_name) - set(baseline_by_name))
    removed = sorted(set(baseline_by_name) - set(current_by_name))
    changed = sorted(
        name for name in (set(baseline_by_name) & set(current_by_name))
        if baseline_by_name[name].lower() != current_by_name[name].lower()
    )

    exact_match = (
        master_matches and manifest_matches
        and not added and not removed and not changed
    )

    return {
        "master_matches": master_matches,
        "manifest_matches": manifest_matches,
        "sidecars_added": added,
        "sidecars_removed": removed,
        "sidecars_changed": changed,
        "exact_match": exact_match,
    }


# ---------------------------------------------------------------------
# BLOCKER 2 hardening: exact-basename/exact-SHA gated sidecar removal,
# never a wildcard, and now rejects anything that is not a safe bare
# basename.
# ---------------------------------------------------------------------
def is_safe_bare_basename(basename):
    """Rejects anything that is not a single, literal, path-separator-
    free filename component: no "/" or "\\", no drive/colon, no "."/
    ".." traversal, and requires os.path.basename() to be a no-op on
    it (i.e. it already IS just a basename)."""
    if not basename:
        return False
    if u"/" in basename or u"\\" in basename:
        return False
    if u":" in basename:
        return False
    if basename in (u".", u".."):
        return False
    if os.path.basename(basename) != basename:
        return False
    return True


def remove_exact_sidecar(authority_dir, basename, expected_sha256):
    """Never wildcards. Requires `basename` to be a safe bare filename
    (no traversal/separators/drive), the exact basename to exist, AND
    its current on-disk SHA-256 to match `expected_sha256` immediately
    before deleting -- refuses (no delete) on any violation."""
    record = {
        "operation_type": u"REMOVE_EXACT_SIDECAR",
        "wall_time": _now_wall(),
        "epoch": time.time(),
        "authority_dir": authority_dir,
        "basename": basename,
        "expected_sha256": expected_sha256,
        "success": False,
    }
    if not is_safe_bare_basename(basename):
        record["error"] = (
            "refusing to remove: %r is not a safe bare basename (path "
            "separators, drive/colon, and '.'/'..' traversal are all "
            "rejected) -- STOP, no delete performed." % (basename,)
        )
        raise GenerationHelperError(record["error"])
    path = os.path.join(authority_dir, basename)
    if not os.path.isfile(path):
        record["error"] = "refusing to remove: %r does not exist." % (path,)
        raise GenerationHelperError(record["error"])
    actual_sha256 = sha256_file(path)
    record["actual_sha256_before_removal"] = actual_sha256
    if actual_sha256.lower() != expected_sha256.lower():
        record["error"] = (
            "refusing to remove %r: on-disk sha256 %r does not match the "
            "expected exact sha256 %r -- STOP, no delete performed."
            % (path, actual_sha256, expected_sha256)
        )
        raise GenerationHelperError(record["error"])
    os.remove(path)
    record["success"] = not os.path.exists(path)
    if not record["success"]:
        record["error"] = "os.remove() returned but %r still exists." % (path,)
        raise GenerationHelperError(record["error"])
    return record


def read_manifest_source_sha256_plain(authority_dir):
    """Dual Python 2.7.5/3 safe, minimal read of manifest.json's own
    "source_sha256" field via plain json.loads() -- deliberately NOT
    the full hardened publisher-side manifest parser (which is Python 3
    only and lives in I_Generation_Publisher.py). Returns None if no
    manifest exists or the field is absent/unparsable -- never raises."""
    manifest_path = os.path.join(authority_dir, MANIFEST_BASENAME)
    if not os.path.isfile(manifest_path):
        return None
    try:
        with open(manifest_path, "rb") as f:
            raw = f.read()
        d = json.loads(raw.decode("utf-8"))
        return d.get("source_sha256")
    except Exception:
        return None


def read_manifest_field_plain(authority_dir, field_name):
    """Same technique as read_manifest_source_sha256_plain(), for any
    single manifest field. Returns None on any absence/parse failure."""
    manifest_path = os.path.join(authority_dir, MANIFEST_BASENAME)
    if not os.path.isfile(manifest_path):
        return None
    try:
        with open(manifest_path, "rb") as f:
            raw = f.read()
        d = json.loads(raw.decode("utf-8"))
        return d.get(field_name)
    except Exception:
        return None


def read_publication_record_plain(record_path):
    """Dual-compatible plain read of a G2 publication record written by
    I_Generation_Publisher.py's own publish_g2_with_record(). Returns
    None if the file does not exist or cannot be parsed -- never
    raises."""
    if not os.path.isfile(record_path):
        return None
    try:
        with open(record_path, "rb") as f:
            raw = f.read()
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def read_finalization_record_plain(record_path):
    """Dual-compatible plain read of a restoration/finalization record
    written by I_Generation_Publisher.py's own finalize_restoration().
    Returns None if the file does not exist or cannot be parsed --
    never raises."""
    if not os.path.isfile(record_path):
        return None
    try:
        with open(record_path, "rb") as f:
            raw = f.read()
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


# ---------------------------------------------------------------------
# CLI dispatcher -- R3 BLOCKER 4: READ-ONLY surface only. No live-Master
# or sidecar mutation command is exposed here at all -- not even the
# narrow, hash-gated ones. All real external live mutation goes through
# the repo-side, path-bound I_Generation_Publisher.py orchestration
# (activate_g2_master() is the ONLY external G1->G2 activation surface;
# finalize_restoration() is the only external G2->G1/cleanup surface),
# except the deliberately instrumented I2 in-process restore performed
# by the checkpoint itself after its own baseline-path gate. The
# underlying perform_g1_to_g2_replacement() / perform_g2_to_g1_
# restoration() / remove_exact_sidecar() Python functions remain (they
# are called directly, in-process, by I_Generation_Publisher.py and by
# Checkpoint_I_Generation_Replacement.py's own I2 wrapper) -- only their
# CLI exposure is removed, closing an unbound, non-path-bound mutation
# escape hatch that bypassed the baseline-inventory path authority the
# real orchestration relies on.
# ---------------------------------------------------------------------
def _cli_main(argv):
    import argparse

    parser = argparse.ArgumentParser(
        description="Read-only inventory/compare utilities for the SFM-deployable core of roadmap item I "
                    "(Master generation replacement). No live-Master or sidecar mutation command is exposed "
                    "here -- see I_Generation_Publisher.py for the path-bound activation/finalization CLI."
    )
    sub = parser.add_subparsers(dest="op")

    p_inv = sub.add_parser("inventory")
    p_inv.add_argument("--master", required=True)
    p_inv.add_argument("--authority-dir", required=True)
    p_inv.add_argument("--out", required=True)

    p_compare = sub.add_parser("compare")
    p_compare.add_argument("--baseline", required=True)
    p_compare.add_argument("--current", required=True)
    p_compare.add_argument("--out", required=True)

    args = parser.parse_args(argv)

    if args.op == "inventory":
        result = capture_live_state_inventory(args.master, args.authority_dir)
    elif args.op == "compare":
        with open(args.baseline, "rb") as f:
            baseline = json.loads(f.read().decode("utf-8"))
        with open(args.current, "rb") as f:
            current = json.loads(f.read().decode("utf-8"))
        result = compare_inventories(baseline, current)
    else:
        parser.print_help()
        return 2

    with open(args.out, "wb") as f:
        f.write(json.dumps(result, indent=2, sort_keys=True).encode("utf-8"))
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(_cli_main(sys.argv[1:]))
