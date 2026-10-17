# -*- coding: utf-8 -*-
"""Installation resolution and the fixed R2 C2 layout (ported from P1/C1 p1proto_c1.py).

Every path is derived from fixed rules and validated names; nothing is taken from a journal
or a prepared record.
"""
import os
import re

from . import w32
from .messages import Stop

MASTER_NAME = "sfm_defaultanimationgroups.txt"
LEGACY_LOCK = "publisher.lock"
SIDECAR_RE = re.compile(r"^sfm_master_0_[0-9a-f]{64}\.sfmsidecar$")
TXID_RE = re.compile(r"^[0-9a-f]{32}$")
FIXED_NAMES = {"manifest.json", "master.txt"}

# Amendment §2.3 / P1-F1: the SFM-embedded Python 2.7 consumers cannot open a Master or
# sidecar path of 260 characters or more. Refuse installations that would require one.
CONSUMER_PATH_LIMIT = 260


def resolve_installation(cfg):
    """C1: aliases may reach the same physical installation; operate on the resolved target."""
    h, err = w32.open_dir(os.path.abspath(cfg), share=7)
    if h is None:
        raise Stop("REFUSED", "NOTHING", reason="installation directory unavailable", error=w32.ename(err))
    try:
        fp = w32.final_path(h)
    finally:
        w32.close(h)
    if fp is None:
        raise Stop("REFUSED", "NOTHING", reason="installation directory path unavailable")
    if fp.startswith("\\\\?\\UNC\\"):
        raise Stop("REFUSED", "NOTHING", reason="network installation path is outside the support boundary")
    return fp[4:] if fp.startswith("\\\\?\\") else fp


class Layout(object):
    """Every path is derived from fixed rules; nothing is taken from a journal."""

    def __init__(self, cfg):
        self.cfg = os.path.abspath(cfg)
        self.master = os.path.join(self.cfg, MASTER_NAME)
        self.auth = os.path.join(self.cfg, "sfm_shared_authority")
        self.upd = os.path.join(self.cfg, "sfm_character_tools_updater")
        self.lock = os.path.join(self.upd, "installation.lock")
        self.txroot = os.path.join(self.upd, "transactions")
        self.staging = os.path.join(self.upd, "staging")

    def reparse_in_slots(self):
        """C1: no symlink/reparse point inside the managed Master/authority/transaction slots."""
        bad = []
        paths = [self.master, self.auth, self.upd, self.txroot, self.staging]
        for root in (self.auth, self.txroot, self.staging):
            if os.path.isdir(root):
                for dp, dn, fn in os.walk(root):
                    paths += [os.path.join(dp, n) for n in dn + fn]
        for p in paths:
            a = w32.attrs(p)
            if a != w32.INVALID_FILE_ATTRIBUTES and a & w32.FILE_ATTRIBUTE_REPARSE_POINT:
                bad.append(os.path.relpath(p, self.cfg))
        return bad

    def ensure_updater_dirs(self):
        """Create the updater's own directories if absent (never the authority directory)."""
        for d in (self.upd, self.txroot, self.staging):
            a = w32.attrs(d)
            if a == w32.INVALID_FILE_ATTRIBUTES:
                os.mkdir(d)
                a = w32.attrs(d)
            if not (a & w32.FILE_ATTRIBUTE_DIRECTORY) or a & w32.FILE_ATTRIBUTE_REPARSE_POINT:
                raise Stop("REFUSED", "FOLDER_CHANGED", reason="updater directory is not a plain directory",
                           path=os.path.relpath(d, self.cfg))

    def txdir(self, txid):
        if not TXID_RE.match(txid):
            raise Stop("CONFLICT", "FOLDER_CHANGED", reason="invalid transaction id", txid=txid)
        return os.path.join(self.txroot, txid)

    def prepdir(self, prepid):
        if not TXID_RE.match(prepid or ""):
            raise Stop("REFUSED", "PREPARE_AGAIN", reason="invalid preparation id", prepid=prepid)
        return os.path.join(self.staging, prepid)

    def slot(self, txid, kind, name):
        if kind == "master":
            return self.master
        if name not in FIXED_NAMES and not SIDECAR_RE.match(name):
            raise Stop("CONFLICT", "FOLDER_CHANGED", reason="invalid slot name", name=name)
        if kind == "auth":
            if name == "master.txt":
                raise Stop("CONFLICT", "FOLDER_CHANGED", reason="invalid auth slot", name=name)
            return os.path.join(self.auth, name)
        if kind in ("candidate", "snapshot", "retired"):
            return os.path.join(self.txdir(txid), kind, name)
        raise Stop("CONFLICT", "FOLDER_CHANGED", reason="invalid slot kind", kind=kind)

    def consumer_paths(self, sidecar_name):
        return {"master": self.master, "sidecar": os.path.join(self.auth, sidecar_name)}

    def path_budget(self, sidecar_name):
        """Returns None if every consumer read path is within the budget, else the details."""
        over = {k: len(p) for k, p in self.consumer_paths(sidecar_name).items() if len(p) >= CONSUMER_PATH_LIMIT}
        if not over:
            return None
        return {"limit": CONSUMER_PATH_LIMIT, "over": over}

    def require_path_budget(self, sidecar_name):
        over = self.path_budget(sidecar_name)
        if over:
            raise Stop("REFUSED", "PATH_TOO_LONG", reason="consumer read path exceeds the budget", **over)
