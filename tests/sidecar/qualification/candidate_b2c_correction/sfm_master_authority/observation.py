# -*- coding: utf-8 -*-
"""Exact-byte Master observation (H0/H1) -- ASTRA_CORRECTED.md Sections
7/8. No mtime/size substitution, ever. No whitespace/encoding
normalization -- raw bytes, streamed, hashed once, in full."""
import hashlib
import time

from . import descriptors
from . import errors


def observe_master(master_path):
    """Full-byte SHA-256 + exact byte length of `master_path`, taken
    fresh -- never cached, never reused across calls. Raises
    MasterUnreadable if the file cannot be opened/read."""
    try:
        h = hashlib.sha256()
        total = 0
        with open(master_path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
                total += len(chunk)
    except (IOError, OSError) as exc:
        raise errors.MasterUnreadable("cannot read Master at %r: %r" % (master_path, exc))
    return descriptors.ObservationToken(
        sha256=h.hexdigest(), byte_length=total, observed_at=time.time(), path=master_path,
    )
