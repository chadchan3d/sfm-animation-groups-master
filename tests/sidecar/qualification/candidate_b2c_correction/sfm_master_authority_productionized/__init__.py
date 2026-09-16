# -*- coding: utf-8 -*-
"""sfm_master_authority -- the future canonical shared authority package
for the Control Group Normalizer and Character Preset Manager.

R3-B2A qualification package. NOT wired into either production consumer
yet. See `runtime.py` for the canonical module-ownership contract.

Import ONLY as:

    import sfm_master_authority.runtime

or:

    from sfm_master_authority import runtime

Never `execfile()` any module in this package. Never vendor/copy this
package under a different name or import path -- doing so creates a
second, non-canonical module object with independent state, defeating
the whole point of this package (see `runtime.py`'s own guard).
"""
