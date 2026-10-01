# R15 Session 1 addendum - raw outputs

Source: the live files in `%PUBLIC%\Documents` after the addendum (copied 2026-09-30).
Each file here is an exact byte excerpt of the addendum span. Only two path prefixes are
redacted, for repository sanitation:
- the local SFM install path is replaced by `<SFM_GAME>`;
- the Windows user-profile path is replaced by `<USERPROFILE>`.

Every other byte is unchanged, including line endings.

Not retained:
- the SFM console transcript (the launcher's `outcome=` lines);
- a separate pre-step-9 log archive.

The CPM log and probe JSONL are cumulative, so the step-9 fresh-process entries are
included in them.

| File | Span | SHA-256 of the original live file | SHA-256 of the exact excerpt (pre-redaction) | SHA-256 of the committed file | Redactions (`<SFM_GAME>`, `<USERPROFILE>`) |
|---|---|---|---|---|---|
| `CPM_Session1_Probe.jsonl` | probe v3 records seq 21-38 (all probe-v3 lines) | `fffcb9a42f4727570ded42a3aaa446ef01517164f8962ab48163f1a2e8bc8324` | `e08d2e80839490b4ce1e03ad6feca1e04ebbdd682c88ff526457fbf9d59fbad9` | `834ad01de3b85d111677cc5ba350171a6b1d4a81577db69079221efa5efbf0ca` | 60, 0 |
| `SFM_CSP_G18AN_SaveNewCopy.log` | lines 1759-2304 (addendum process start 20:56:22 to EOF) | `683e5476f79dd8861b318e29413239b2e8d763238f881fbebdd481742e7e9332` | `1e1ab36f0cfbe4ec9dbdbdaa9bcd28895112c263aaea7e703ed2a730f6c9e149` | `e72c18a772bc278bbfbaadca99d394e85dd910c0d47af26adca5fa7e347063b0` | 6, 8 |
| `sfm_rebuild_control_groups.txt` | entire file (single addendum Normalizer run) | `1bf8854563e7ec622d1863ba7c8e0bbbfbcf592d225d05695167ffa175a3ee49` | `1bf8854563e7ec622d1863ba7c8e0bbbfbcf592d225d05695167ffa175a3ee49` | `f5fe10d099d82e161014dc5dda7e4cb4afd485f5ade559df7d6607f50e5dc50d` | 5, 0 |
