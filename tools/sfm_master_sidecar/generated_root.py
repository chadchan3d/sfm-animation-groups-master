# -*- coding: utf-8 -*-
"""Generated-root / install-slot derivation -- ASTRA_CORRECTED.md Section
14, R3-B2E Section 7.

Chooses ONE concrete Windows location for locally-generated immutable
sidecar artifacts + pointer/manifest, outside any Workshop-managed
content and outside anything Steam may replace as subscription payload.
"""
import hashlib
import os


def default_generated_root_base():
    """%LOCALAPPDATA%\\SFM_ControlGroupNormalizer\\generated -- a
    user-writable application-data location. Never inside
    `game/workshop`, never inside any Workshop item's own content
    directory, never a path Steam manages as subscription payload."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("%LOCALAPPDATA% is not set -- cannot derive a generated-root location")
    return os.path.join(local_app_data, "SFM_ControlGroupNormalizer", "generated")


def derive_install_slot_identity(install_root_path, master_path):
    """A short, stable identity distinguishing (SFM installation root,
    Master path) pairs, so multiple SFM installations -- or multiple
    Master files within one installation -- never silently share or
    merge generations.

    Migration behavior: if the installation MOVES (a different
    `install_root_path` string), this identity changes, and generations
    under the OLD slot become orphans -- never automatically migrated or
    merged into the new slot (matches the no-automatic-GC first-R3
    policy; a moved install simply starts a fresh slot, and the old
    slot's directory may be manually inspected/removed later as a
    separate maintenance action, out of scope here)."""
    canonical = (
        os.path.normcase(os.path.abspath(str(install_root_path)))
        + "|" + os.path.normcase(os.path.abspath(str(master_path)))
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def derive_generated_root(install_root_path, master_path, base=None):
    """`<base>/<install_slot_identity>/` -- one directory per (install,
    Master) pair, holding generation files + `manifest.json` (+
    `.bak`) + `publisher.lock` together, matching the already-tested
    `publisher.py` single-namespace-per-slot model. Permissions
    expectation: ordinary user-writable (LOCALAPPDATA is per-user by
    definition); no elevation required."""
    if base is None:
        base = default_generated_root_base()
    slot = derive_install_slot_identity(install_root_path, master_path)
    return os.path.join(base, slot)
