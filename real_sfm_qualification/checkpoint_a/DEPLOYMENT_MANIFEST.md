# Deployment Manifest — `sfm_master_authority_productionized` + `sfm_master_sidecar`

## Why this deployment happened

Checkpoint A's first real-SFM run (row A-1 in `real_sfm_qualification/LEDGER.md`) failed at
installed package discovery: `sfm_master_authority_productionized\` and `sfm_master_sidecar\` were
both simply **missing** as sibling directories under `usermod\scripts\sfm\mainmenu\ChadChan3D\`.
Nothing had ever deployed them there — the source-level integration work (through commit
`68f1188e7dcb3fdd34d384396bf5d7a14acf7d25`) only ever placed the frozen Normalizer itself at that
location; the accepted package's real source has, until now, only ever lived in the qualification
tree (`tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/`)
and in `tools/sfm_master_sidecar/`.

This is a deployment correction only. The accepted package implementation
(`cf06ba4ec2080e17d5132ed15f641c143a4137b1`, unchanged through the accepted integration) and the
production Normalizer were not modified to make this work.

## Determining the exact required file set

Neither directory's entire contents are meant to ship. Both packages' own source explicitly
distinguish real runtime modules from qualification-only/dev-only ones:

- `sfm_master_authority_productionized/projections.py`'s own docstring: *"B2B projection-builder
  QUALIFICATION FIXTURES ONLY. NOT wired to any production consumer."* Confirmed via reverse-import
  grep: no other module in the package imports it (`cohort.py`'s unrelated `build_projections`
  *method* and two descriptive code comments are the only other matches). **Excluded.**
- `sfm_master_sidecar/__init__.py`'s own docstring: *"`format` and `reader` are the only two
  submodules declared safe for the embedded runtime... not `writer` (Python-3-only)... and no
  test/CLI code."* This directly excludes `writer.py`, `cli.py`, `compiler.py`, `manifest.py`,
  `publisher.py`, `mutex_publisher.py`, `generated_root.py`, `win_named_mutex.py` — all real,
  legitimate source, but explicitly Python-3-only compiler/publisher-side tooling, never meant for
  the embedded SFM Python 2.7 runtime. Confirmed `reader.py` imports only `format` (nothing else in
  the package), so the closure is exactly `{__init__.py, format.py, reader.py}`.
- `sfm_master_authority_productionized/native_discovery.py` is **real production source**, not a
  fixture (no "qualification"/"fixture" self-description anywhere in it) — `resolver.py`'s own
  docstring says its real discovery role is *"used only by the SFM runtime identity probe"*, a
  different real consumer than the Normalizer's own import chain. It is not reachable from
  `runtime.py`'s transitive imports, but it is genuine package source, not a test or a
  qualification-only fixture, so per the governing correction's own exclusion list ("qualification-
  only files; tests; repository metadata; caches") it does **not** qualify for exclusion. **Included**
  (deploying the full genuine package source is the conservative, correct choice — pruning further
  based on this session's own reachability analysis, beyond what the package's own source explicitly
  self-declares as fixture/dev-only, was avoided as exactly the kind of improvisation the governing
  correction warned against).

Excluded categorically, from both directories: every `.pyc` file, every `__pycache__/` directory —
these are this development machine's own bytecode caches, never source, and explicitly named for
exclusion.

## Pre-deployment manifest (source: `cf06ba4`, read directly from this repository)

### `sfm_master_authority_productionized/` — 23 files, 309,103 bytes total

Source: `tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/`

| File | Bytes | SHA-256 |
|---|---:|---|
| `__init__.py` | 1,088 | `8c4dc3af75a0eefb1d21e6afca3bbd60b248f1832c45f5fc967b6f5f00292af7` |
| `bootstrap.py` | 6,625 | `acad28b6ea383f5124024751347a80ba30eb293cdff87e4e0ea69d186bffe2d9` |
| `broker.py` | 32,148 | `b2113da7da5954e88f40f780cc36f012f5451ebcf6db4e5b8baf2d413cd9c514` |
| `candidate_packed_provider_r3a2b.py` | 25,083 | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` |
| `candidate_packed_validator_r3a2b.py` | 40,510 | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` |
| `cohort.py` | 8,779 | `4e368d6bedc048acf759685bac8fdc98b953ca96da09a6adbffe9ecc8c16111d` |
| `descriptors.py` | 5,140 | `db0fa70fff4154105804c5dece4033fa91b099cb9bfbe689ffbfb44f8b76652a` |
| `errors.py` | 3,309 | `82da08664006cc24fed85014ff8d79291dfc62c78f65dbea10be81b97698bee7` |
| `memory_accounting.py` | 4,389 | `b907cce9637a1690169d6f53a5516446a9bba4bd0a6bf967eea4fa06ecb0e53a` |
| `native_discovery.py` | 1,602 | `08a4393731b12380a32d216c834ea0f5bc94413d21828a8add3708b4812f7f38` |
| `normalizer_compat_adapter.py` | 19,741 | `acfdb4e925f0c46e128b4a6b7c2a84e8d073930afb3527b660abb082add7661b` |
| `observation.py` | 1,043 | `70bb3c1ce404f9974cd9d9ba6cfcdcfbd11c1779f64bf2f0d652f5fbc8f6c35b` |
| `packed_family_counts.py` | 4,574 | `c4f8b78c4e86b2f8d238e29f7c231036d12e8d97c73924f3bf9c31ede09a9d31` |
| `pointer.py` | 7,930 | `2cd5b5d2ee98c2cb500d8d3e8ae108571bfc40db87295c88362ab3f956136dea` |
| `resolver.py` | 5,062 | `dce6b0aed0765705276c8289fc926fc0c75f426566f095859b7e2bb73cbeaeb4` |
| `resource_estimator.py` | 44,529 | `1cc3649a44e1b3777afdd9f86c70386b2bc8d700508037e6a41d748a399771dd` |
| `resource_preflight.py` | 30,563 | `8ac3795453cddcd13ceb59a1d9989561e3c0919fc7a163bc569e0ca2e05afec5` |
| `runtime.py` | 14,851 | `961a31d1e54171110f1f0e2abcb0bc615fe7c4a77689abae3510cd5469c9915c` |
| `selection.py` | 14,894 | `ba5b49b7efadcac551674c3528aed0822c58cbad3b49c13371c833b435b43873` |
| `sidecar_contract.py` | 6,125 | `5fc74de146d9b1b58c81caee9d14fa125bdafad6ad67ed2ac9fbcc93051f9175` |
| `view_cache.py` | 17,361 | `26f1b34b39515350eaad8a2433fffd6fe916f040a36c5159b657e040abf6f3b2` |
| `views.py` | 8,129 | `cf803240ee39dd4741b7b34d9db4c8b6f81a156e96beb3260e8ee3a46c965092` |
| `win_file_identity.py` | 5,628 | `783086af37f93b3d836fabe69593b915a4ae6a947aecfced941ec592b7dfd701` |

### `sfm_master_sidecar/` — 3 files, 60,114 bytes total

Source: `tools/sfm_master_sidecar/`

| File | Bytes | SHA-256 |
|---|---:|---|
| `__init__.py` | 872 | `8cad865fd9954035aebb3e02d5c454228e80a095595bd9cd3746df0b357f904c` |
| `format.py` | 14,249 | `b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259` |
| `reader.py` | 44,993 | `1b95261c52d95c306b28fc6e5e9340afa65de4ea2574ed29c2bab427d252719f` |

## Post-deployment independent verification

Both target directories were listed and every deployed file re-hashed independently (a fresh read
from disk, not a reuse of the copy operation's own in-memory state) and compared against the tables
above:

- `sfm_master_authority_productionized`: **23/23 files present, 0 extra, 0 missing, all 23 SHA-256 +
  byte-size pairs matched exactly.**
- `sfm_master_sidecar`: **3/3 files present, 0 extra, 0 missing, all 3 SHA-256 + byte-size pairs
  matched exactly.**
- Zero `.pyc` files and zero `__pycache__/` directories present in either deployed directory
  (confirmed by directory listing).

## Confirmed unmodified by this deployment

| File | SHA-256 (before and after, identical) |
|---|---|
| Production Normalizer (`Rebuild_Control_Groups_Normalizer.py`) | `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867` |
| Canonical Master (`usermod\cfg\sfm_defaultanimationgroups.txt`) | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |
| Published authority generation `manifest.json` (`usermod\cfg\sfm_shared_authority\manifest.json`) | content re-read and confirmed byte-identical to what the prior deployment action published — `generation_basename` / `sidecar_sha256` / `source_sha256` all unchanged |

No file outside the two named package directories was created, modified, or deleted by this
correction.
