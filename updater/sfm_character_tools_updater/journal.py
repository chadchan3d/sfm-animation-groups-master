# -*- coding: utf-8 -*-
"""Transaction journal and transaction-record inspection (ported from P1/C1 p1proto_c1.py).

Each record is one line: canonical JSON {"seq", "rec"}, a tab, and the SHA-256 of that JSON.
A torn final line is preserved and acknowledged, never rewritten. Only the product schema
TX_SCHEMA is understood; any other schema (including the U0A/P1 experimental ones) is unknown.
"""
import hashlib
import json
import os

from . import TX_SCHEMA, w32
from .messages import Stop

SCHEMA = TX_SCHEMA
TERMINAL = {"COMPLETE", "ROLLED_BACK", "ABANDONED"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _line(seq, rec):
    body = json.dumps({"seq": seq, "rec": rec}, sort_keys=True, separators=(",", ":"))
    return ("%s\t%s\n" % (body, sha(body.encode("utf-8")))).encode("utf-8")


def parse_journal(data):
    """Returns (records, torn_tail_bytes or None). Raises Stop on malformed content."""
    recs = []
    lines = data.split(b"\n")
    tail = lines.pop()  # bytes after the final newline
    pending_torn = None
    for raw in lines:
        try:
            text = raw.decode("utf-8")
            body, digest = text.rsplit("\t", 1)
            if sha(body.encode("utf-8")) != digest:
                raise ValueError("checksum")
            obj = json.loads(body)
            seq, rec = obj["seq"], obj["rec"]
        except Exception:
            if pending_torn is None:
                pending_torn = sha(raw)
                continue
            raise Stop("CONFLICT", "UNKNOWN_SCHEMA", reason="malformed journal record")
        if pending_torn is not None:
            if rec.get("t") != "TORN_TAIL" or rec.get("sha") != pending_torn:
                raise Stop("CONFLICT", "UNKNOWN_SCHEMA", reason="malformed journal record")
            pending_torn = None
        if seq != len(recs):
            raise Stop("CONFLICT", "UNKNOWN_SCHEMA", reason="journal sequence gap")
        recs.append(rec)
    if pending_torn is not None:
        raise Stop("CONFLICT", "UNKNOWN_SCHEMA", reason="malformed journal record")
    if recs and (recs[0].get("t") != "INTENT" or recs[0].get("schema") != SCHEMA):
        raise Stop("CONFLICT", "UNKNOWN_SCHEMA", reason="unknown journal schema")
    return recs, (tail if tail else None)


class Journal(object):
    """Held open for the transaction's lifetime: write access, READ sharing only.
    A second process therefore cannot write it while the owner lives."""

    def __init__(self, path, create):
        disp = w32.CREATE_NEW if create else w32.OPEN_EXISTING
        self.h, err = w32.create_file(path, w32.GENERIC_READ | w32.GENERIC_WRITE,
                                      w32.FILE_SHARE_READ, disp)
        if self.h is None:
            raise Stop("REFUSED", "NOTHING", reason="journal unavailable", error=w32.ename(err),
                       journal_busy=(err == 32))
        data, _ = w32.read_all_handle(self.h)
        self.records, torn = parse_journal(data or b"")
        if torn is not None:
            # Preserve the torn bytes as their own line, then acknowledge them.
            w32.seek_end(self.h)
            self._write(b"\n")
            self.seq = len(self.records)
            self.append({"t": "TORN_TAIL", "sha": sha(torn)})
        self.seq = len(self.records)

    def _write(self, data):
        w32.seek_end(self.h)
        ok, err = w32.write_all(self.h, data)
        if ok:
            ok, err = w32.flush(self.h)
        if not ok:
            raise Stop("CONFLICT", "FOLDER_CHANGED", reason="journal write failed",
                       error=w32.ename(err))

    def append(self, rec):
        rec = json.loads(json.dumps(rec))
        if rec.get("t") == "CONFLICT" and self.records and self.records[-1] == rec:
            return  # the same unresolved conflict re-observed: keep recovery idempotent
        self._write(_line(self.seq, rec))
        self.records.append(rec)
        self.seq += 1

    def close(self):
        if self.h is not None:
            w32.close(self.h)
            self.h = None


def transaction_status(layout, txid, readonly=False):
    """Last journal record type, or a marker. The default open (write access, READ sharing)
    reports BUSY while a live owner holds the journal; `readonly` never requests write access."""
    p = os.path.join(layout.txdir(txid), "journal")
    if readonly:
        h, err = w32.create_file(p, w32.GENERIC_READ, w32.FILE_SHARE_READ | w32.FILE_SHARE_WRITE,
                                 w32.OPEN_EXISTING)
    else:
        h, err = w32.create_file(p, w32.GENERIC_READ | w32.GENERIC_WRITE, w32.FILE_SHARE_READ,
                                 w32.OPEN_EXISTING)
    if h is None:
        return "BUSY" if err == 32 else "UNREADABLE:%s" % w32.ename(err)
    try:
        data, _ = w32.read_all_handle(h)
    finally:
        w32.close(h)
    try:
        recs, torn = parse_journal(data or b"")
    except Stop:
        return "MALFORMED"
    if not recs:
        return "EMPTY"
    return recs[-1].get("t")


def intent_schema(layout, txid):
    """Schema named by a transaction's intent.json (path-based read), or a marker."""
    try:
        intent = json.loads(open(os.path.join(layout.txdir(txid), "intent.json"), "rb").read().decode("utf-8"))
    except Exception as e:
        return "UNREADABLE:%s" % type(e).__name__
    if not isinstance(intent, dict):
        return "UNREADABLE:not-an-object"
    if intent.get("txid") != txid:
        return "TXID_MISMATCH"
    return intent.get("schema")
