# -*- coding: utf-8 -*-
"""DEVELOPMENT-SIDE release producer for official data packages (R2 D1-D3). Not shipped.

  make_official_package.py keygen --private KEY.pem --public KEY.pub [--passphrase-file F]
      New Ed25519 key pair. The private key is PKCS#8 PEM (encrypted when a passphrase file is
      given); the public file holds the raw public key as hex. Refuses to write inside the
      repository: production key custody stays outside it (R2 D3). Prints the key id only.

  make_official_package.py build --master TXT --private KEY.pem [--passphrase-file F] --out DIR
          --sequence N --data-version V --release-tag T --source-commit SHA40 --published-at UTC
          [--profile ID ...] [--minimum-updater-contract N]
      Compiles TXT with the canonical compiler under the official policy, writes the five package
      files into the NEW directory DIR (CREATE_NEW), signs the exact release.json bytes and
      verifies the result with the product's own descriptor and signature checks.

  make_official_package.py sign --descriptor FILE --private KEY.pem [--passphrase-file F] --out SIG
      Signs arbitrary descriptor bytes (qualification of malformed descriptors only).

The descriptor is serialized deterministically: UTF-8, sorted keys, no insignificant whitespace,
ASCII escapes, one trailing newline. Signing never reserializes: the signature covers the exact
bytes written.
"""
import argparse
import hashlib
import json
import os
import sys

UPDATER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(UPDATER)
sys.path.insert(0, UPDATER)

from sfm_character_tools_updater import candidate, official, w32  # noqa: E402

VALIDATE_MASTER_PIN = "62d5273e9575d6c1a245376640e024a020f9c9ee9f013eb5a929df8113e10e5c"


def _norm(p):
    return os.path.normcase(os.path.abspath(p)).rstrip("\\")


def _inside_repo(p):
    r = _norm(REPO)
    return _norm(p) == r or _norm(p).startswith(r + "\\")


def _load_private(path, passphrase_file):
    from cryptography.hazmat.primitives import serialization
    pw = open(passphrase_file, "rb").read().strip() if passphrase_file else None
    return serialization.load_pem_private_key(open(path, "rb").read(), password=pw)


def _public_raw(priv):
    from cryptography.hazmat.primitives import serialization
    return priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def _write_new(path, data):
    ok, err = w32.write_new_file(path, data)
    if not ok:
        raise SystemExit("write failed %s: %s" % (path, w32.ename(err)))


def keygen(a):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    for p in (a.private, a.public):
        if _inside_repo(p):
            raise SystemExit("refused: key material must be written outside the repository")
    k = Ed25519PrivateKey.generate()
    enc = (serialization.BestAvailableEncryption(open(a.passphrase_file, "rb").read().strip())
           if a.passphrase_file else serialization.NoEncryption())
    _write_new(a.private, k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, enc))
    raw = _public_raw(k)
    _write_new(a.public, raw.hex().encode("ascii") + b"\n")
    print(json.dumps({"key_id": official.key_id_for(raw), "public_key_hex": raw.hex()}))


def descriptor_bytes(d):
    return (json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def build(a):
    if hashlib.sha256(open(os.path.join(REPO, "tools", "validate_master.py"), "rb").read()).hexdigest() != VALIDATE_MASTER_PIN:
        raise SystemExit("refused: tools/validate_master.py does not match its pin")
    priv = _load_private(a.private, a.passphrase_file)
    raw = _public_raw(priv)
    kid = official.key_id_for(raw)
    txt = open(a.master, "rb").read()
    d = candidate.deps()
    snap = d["compiler"].SourceSnapshot("official", txt)
    outcome = d["compiler"].parse_and_compile(snap, official_policy=True)
    d["compiler"].self_validate_from_bytes(outcome)
    name = d["compiler"].generation_basename(outcome.ordinary_sha256)
    manifest = d["manifest"].serialize_manifest(d["manifest"].build_manifest_dict(outcome, name))
    desc = {"schema": 1, "object_type": official.OBJECT_TYPE, "repository": official.REPOSITORY,
            "channel": official.CHANNEL, "sequence": a.sequence, "data_version": a.data_version,
            "release_tag": a.release_tag, "source_commit": a.source_commit, "published_at": a.published_at,
            "minimum_updater_contract": a.minimum_updater_contract,
            "compatible_authority_profiles": a.profile or [official.AUTHORITY_PROFILE],
            "sidecar_contract": dict(official.SIDECAR_CONTRACT), "compiler_build": "sfm-master-sidecar-compiler-50dd1804",
            "signing_key_id": kid,
            "files": {"master": {"name": official.MASTER_NAME, "byte_length": len(txt), "sha256": official.sha(txt)},
                      "manifest": {"name": "manifest.json", "byte_length": len(manifest),
                                   "sha256": official.sha(manifest)},
                      "sidecar": {"name": name, "byte_length": len(outcome.blob), "sha256": official.sha(outcome.blob)}}}
    db = descriptor_bytes(desc)
    sig = priv.sign(db)
    official.parse_descriptor(db)
    official.verify_signature(db, sig, kid, keys={kid: raw.hex()})
    os.mkdir(a.out)
    for n, data in ((official.MASTER_NAME, txt), ("manifest.json", manifest), (name, outcome.blob),
                    (official.DESCRIPTOR, db), (official.SIGNATURE, sig)):
        _write_new(os.path.join(a.out, n), data)
    print(json.dumps({"package": a.out, "key_id": kid, "sequence": a.sequence, "descriptor_sha256": official.sha(db),
                      "sidecar": name}))


def sign(a):
    priv = _load_private(a.private, a.passphrase_file)
    _write_new(a.out, priv.sign(open(a.descriptor, "rb").read()))


def main(argv=None):
    p = argparse.ArgumentParser(prog="make_official_package.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("keygen")
    k.add_argument("--private", required=True)
    k.add_argument("--public", required=True)
    k.add_argument("--passphrase-file")
    b = sub.add_parser("build")
    b.add_argument("--master", required=True)
    b.add_argument("--private", required=True)
    b.add_argument("--passphrase-file")
    b.add_argument("--out", required=True)
    b.add_argument("--sequence", type=int, required=True)
    b.add_argument("--data-version", required=True)
    b.add_argument("--release-tag", required=True)
    b.add_argument("--source-commit", required=True)
    b.add_argument("--published-at", required=True)
    b.add_argument("--profile", action="append")
    b.add_argument("--minimum-updater-contract", type=int, default=1)
    s = sub.add_parser("sign")
    s.add_argument("--descriptor", required=True)
    s.add_argument("--private", required=True)
    s.add_argument("--passphrase-file")
    s.add_argument("--out", required=True)
    a = p.parse_args(argv)
    {"keygen": keygen, "build": build, "sign": sign}[a.cmd](a)


if __name__ == "__main__":
    main()
