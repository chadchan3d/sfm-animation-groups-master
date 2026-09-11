# -*- coding: utf-8 -*-
"""Runtime-safe package root for the experimental Master sidecar format.

Deliberately minimal: this file must be safely importable under the
embedded-SFM Python 2.7 runtime, so it imports NOTHING beyond the standard
library at package-init time -- not `writer` (Python-3-only, uses
`dataclasses`/`tools.sfm_master_core`), not `tools.sfm_master_core` itself,
and no test/CLI code. `format` and `reader` are the only two submodules
declared safe for the embedded runtime; a caller imports them explicitly
(`from tools.sfm_master_sidecar import reader`), never implicitly through
this file.

Phase B2B scope note: this package holds experimental, unfrozen format code
(`format_contract_version` is not `1`). See
SFM_MASTER_SIDECAR_PHASE_B1_2_FINAL_IMPLEMENTATION_SPEC.md for the normative
specification this implementation follows.
"""

__all__ = []
