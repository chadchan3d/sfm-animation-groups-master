# -*- coding: utf-8 -*-
"""Recognition and in-place holding of a verified legacy `publisher.lock` (R2 C5; owner
direction 2026-10-12: preserve and recognize in place). Ported from P1/C1 p1proto_c1.py."""
import hashlib

from . import w32

EMPTY_SHA = hashlib.sha256(b"").hexdigest()
LEGACY_HANDLE = [None]


def classify_legacy_lock(path):
    """Recognized only as an exact-name, regular, unlinked, empty file that no live
    legacy publisher holds. Returns (identity or None, refusal reason or None)."""
    a = w32.attrs(path)
    if a == w32.INVALID_FILE_ATTRIBUTES:
        return None, None
    if a & w32.FILE_ATTRIBUTE_REPARSE_POINT or a & w32.FILE_ATTRIBUTE_DIRECTORY:
        return None, "publisher.lock is not a regular file"
    h, err = w32.create_file(path, w32.GENERIC_READ, 0, w32.OPEN_EXISTING)
    if h is None:
        if err == 32:
            return None, "a legacy publisher may be active (publisher.lock in use)"
        return None, "publisher.lock unavailable: %s" % w32.ename(err)
    try:
        info = w32.std_info(h)
        s, _ = w32.sha_handle(h)
        ident = {"file_id": w32.file_id(h), "sha256": s, "links": info["links"]}
    finally:
        w32.close(h)
    if ident["links"] != 1:
        return None, "publisher.lock has hard links"
    if s != EMPTY_SHA:
        return None, "publisher.lock is not empty (unrecognized)"
    return ident, None


def hold_legacy_lock(path, ident):
    """Hold the recognized legacy lock (read-only, share 0) so no legacy publisher can
    open it while protection is held; verify it is the same file."""
    h, err = w32.create_file(path, w32.GENERIC_READ, 0, w32.OPEN_EXISTING)
    if h is None:
        return None, ("a legacy publisher may be active (publisher.lock in use)" if err == 32
                      else "publisher.lock unavailable: %s" % w32.ename(err))
    if w32.file_id(h) != ident["file_id"] or w32.sha_handle(h)[0] != ident["sha256"] \
            or w32.std_info(h)["links"] != 1:
        w32.close(h)
        return None, "publisher.lock identity changed"
    LEGACY_HANDLE[0] = h
    return h, None
