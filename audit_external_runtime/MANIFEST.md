# Audit-Only External Runtime Snapshot Manifest

This directory holds a **read-only, audit-only snapshot** of a file that lives outside this
git repository, in the real Source Filmmaker installation. It exists solely so an independent
auditor reviewing this repository's archive can inspect the actual bytes of the one functional
change the Production Normalizer Integration checkpoint made, without needing filesystem access
to the real SFM install.

**This snapshot is not a second production copy and not a new source of authority.** The single
real, live, authoritative copy of this file remains exactly where it has always been:

```
E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py
```

Nothing in this repository reads from, writes to, or depends on the copy in this directory. The
three integration test harnesses (`test_normalizer_integration_bootstrap.py`,
`test_normalizer_integration_acquisition.py`, `test_normalizer_integration_native_protect.py`)
continue to read the real, live, installed file directly from the absolute path above, exactly as
before -- this snapshot changes nothing about how those harnesses work.

## Snapshotted file

| Field | Value |
|---|---|
| Original installed path | `E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py` |
| Byte size | 355,316 bytes |
| Line count (newline-terminated lines) | 13,937 |
| SHA-256 | `88805dbbcebf8c813a97b5346194ff546ecd2a0ef7c6ab47192734b41e1fa2ef` |
| Newline style | pure LF (0 CRLF sequences found; matches the real installed file's own pre-existing convention, unchanged by this integration) |
| Encoding | pure ASCII (the file's own `# -*- coding: ascii -*-` declaration; independently confirmed by direct byte-level decode) |
| Reflects final post-correction production file? | **Yes.** This snapshot was taken AFTER the independent-audit-driven native-Master-protection fail-closed correction (2026-09-22) was applied to the real installed file. It is byte-for-byte identical to the file the real SFM installation currently runs. |

## Identity history (for audit continuity)

| Stage | SHA-256 |
|---|---|
| Pre-integration (frozen, before any of this arc's work) | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| Post-integration, commit `9202933` (before this correction) | `f69a57436d46252fb78d9ae2a2155d7206e07869c74ac5f4d28f6676f5ef2cf0` |
| **Post-correction (this snapshot)** | **`88805dbbcebf8c813a97b5346194ff546ecd2a0ef7c6ab47192734b41e1fa2ef`** |

## Verification

The exact command used to confirm this snapshot is byte-identical to the live installed file at
the time it was taken:

```python
import hashlib
src = r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py"
dst = r"audit_external_runtime\Rebuild_Control_Groups_Normalizer.py"
assert open(src, "rb").read() == open(dst, "rb").read()
```

An independent auditor can re-run the same comparison against a real SFM install, or simply trust
the SHA-256 above and compare it to the value reported for the live file at the time of any future
correction.
