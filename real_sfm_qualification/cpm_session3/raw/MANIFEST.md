# CPM Session 3 - raw outputs

Copied 2026-10-06 from `%PUBLIC%\Documents` (the probe JSONL and the CPM log) and from
`%PUBLIC%\Documents\CPM_Session3\` (campaigns S3 and S3_ADD).

Each file is an exact byte excerpt of its source. Only three path prefixes are redacted, for
repository sanitation:
- the SFM install path becomes `<SFM_GAME>`;
- the user-profile path becomes `<USERPROFILE>`;
- the Public profile path becomes `<PUBLIC>`.

Every other byte, including line endings and the PowerShell `Out-File` BOM, is unchanged.

## Not copied (byte-identical to repository material; hash-verified at copy time)

| File | Bytes | SHA-256 | Identity |
|---|---|---|---|
| `S3/g1_source.txt` | 3972355 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | G1 (identical to repository sfm_defaultanimationgroups.txt) |
| `S3/g2_source.txt` | 3972356 | `54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7` | G2 (repository Master + one LF) |
| `S3_ADD/g1_source.txt` | 3972355 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | G1 (identical to repository sfm_defaultanimationgroups.txt) |
| `S3_ADD/g2_source.txt` | 3972356 | `54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7` | G2 (repository Master + one LF) |

## Not retained

- the PowerShell window transcripts (operator `S2 … OK` lines are corroborated by the tool records);
- the SFM console.

## Copied files

| File | Span | SHA-256 of the original source | SHA-256 of the exact excerpt | SHA-256 of the committed file | Redactions (`<SFM_GAME>`, `<USERPROFILE>`, `<PUBLIC>`) |
|---|---|---|---|---|---|
| `S3/baseline_inventory.json` | entire file | `661e623b1cc268d453aa79467588c1297b10d6d1a3a696e928570de5efd54cfb` | `661e623b1cc268d453aa79467588c1297b10d6d1a3a696e928570de5efd54cfb` | `176e0582d9f2b41b96e27ce1297f8ea3fda8cee805a4954cac5557cf6c68dad5` | 2, 0, 0 |
| `S3/deploy_after_removal.txt` | entire file | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | 0, 0, 0 |
| `S3/deploy_before_harness.txt` | entire file | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | 0, 0, 0 |
| `S3/finalization_record.json` | entire file | `5e5e44c0439cb9530088085a141fe44aba19e4d6f8411dfe196d14910f1212b8` | `5e5e44c0439cb9530088085a141fe44aba19e4d6f8411dfe196d14910f1212b8` | `17fa294b4eebdf7d79b9304d331487f98988d5bfdc6d58ecc1298d0f193064b2` | 8, 0, 0 |
| `S3/finalize_stdout.json` | entire file | `fcb5b8300d3a85a4216408280e59d96899f65a165ed25578016b536dcc60a2f7` | `fcb5b8300d3a85a4216408280e59d96899f65a165ed25578016b536dcc60a2f7` | `98b1b3270f5b34a53c46a27f6d3619149d373180facee8b240a87cca20b8f9e1` | 8, 0, 0 |
| `S3/g2_activation_record.json` | entire file | `fdf4be9196d4f6982fda6c5d8db3cb43104f4eb65ce100201d64b9799d29e72a` | `fdf4be9196d4f6982fda6c5d8db3cb43104f4eb65ce100201d64b9799d29e72a` | `331bf12bfa1045ace7a55f55ef658644be3960226c20c1d3db02497b3b4be6de` | 5, 0, 0 |
| `S3/g2_plan_record.json` | entire file | `a968957d0b8d2475746983d87d710797fe50c6748f28b403d986db330b823382` | `a968957d0b8d2475746983d87d710797fe50c6748f28b403d986db330b823382` | `4fb8f8e50cd4603f69905187dac2c70b718e82a2fb1750488050ce66f947ba42` | 2, 0, 2 |
| `S3/g2_publication_record.json` | entire file | `98ebc1e04aa9d91023166fae10bd06e126a1b1d5ea3bfae7eafdfe3cd018efda` | `98ebc1e04aa9d91023166fae10bd06e126a1b1d5ea3bfae7eafdfe3cd018efda` | `6eb087cd1909449d2c3c1e95c4feb901048625199e293cd04fbe716c6068df94` | 2, 0, 1 |
| `S3/harness_arm_record.json` | entire file | `2ad660fcaa00de58e4c72be8121859e1db63836f18a68cfef05260a9b84012e2` | `2ad660fcaa00de58e4c72be8121859e1db63836f18a68cfef05260a9b84012e2` | `2ad660fcaa00de58e4c72be8121859e1db63836f18a68cfef05260a9b84012e2` | 0, 0, 0 |
| `S3/harness_deploy_record.json` | entire file | `7074653ab7c3381a88080b2b9649bb1fa3a481f00b7f87871661cf4b93c12f6f` | `7074653ab7c3381a88080b2b9649bb1fa3a481f00b7f87871661cf4b93c12f6f` | `7074653ab7c3381a88080b2b9649bb1fa3a481f00b7f87871661cf4b93c12f6f` | 0, 0, 0 |
| `S3/harness_pause_record.json` | entire file | `3a58d8856b232b9832ad59d6a714101033f15bef9c0f352405af6f3eb79d3fb1` | `3a58d8856b232b9832ad59d6a714101033f15bef9c0f352405af6f3eb79d3fb1` | `3a58d8856b232b9832ad59d6a714101033f15bef9c0f352405af6f3eb79d3fb1` | 0, 0, 0 |
| `S3/harness_resume_record.json` | entire file | `1fae7d9a6fdc3ccadd13b2e2d23b9b6bd6a95511de34db74808e4dca83563f0d` | `1fae7d9a6fdc3ccadd13b2e2d23b9b6bd6a95511de34db74808e4dca83563f0d` | `1fae7d9a6fdc3ccadd13b2e2d23b9b6bd6a95511de34db74808e4dca83563f0d` | 0, 0, 0 |
| `S3/harness_undo_snapshot.json` | entire file | `0b2be975103270dc629431b75d7bddf28c43ce3fcb388a9bddc11a01f5d35165` | `0b2be975103270dc629431b75d7bddf28c43ce3fcb388a9bddc11a01f5d35165` | `0b2be975103270dc629431b75d7bddf28c43ce3fcb388a9bddc11a01f5d35165` | 0, 0, 0 |
| `S3/phase_a_stdout.json` | entire file | `ac4bdab370f4ad229651febe29ceb0f1066faf9cdf2af1ff9a2d572fb5baa9a2` | `ac4bdab370f4ad229651febe29ceb0f1066faf9cdf2af1ff9a2d572fb5baa9a2` | `9e410b6e11832bca566add1bc32e746db7a0710eb2f4361816a33b14f4226050` | 2, 0, 4 |
| `S3/phase_b_stdout.json` | entire file | `e0d07724eb902c90b71293c6de351a00a3c0b80356c4dc38936a1387c949a20f` | `e0d07724eb902c90b71293c6de351a00a3c0b80356c4dc38936a1387c949a20f` | `2c5a4dfc7a6e3125101772227fb65fd5f563c7a1f3d2498c0c8047a4da426481` | 5, 0, 0 |
| `S3/post_switch_inventory.json` | entire file | `b402d952ecf74411eecde62a4c1a8d059ffe7314672bb27b620e212f7e210449` | `b402d952ecf74411eecde62a4c1a8d059ffe7314672bb27b620e212f7e210449` | `6cb875189902dffafc0543e50b29c53cc3dc0a19da7c28cf1304bc3d9406ac00` | 2, 0, 0 |
| `S3/restore_compare.json` | entire file | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | 0, 0, 0 |
| `S3/restored_inventory.json` | entire file | `58520ff488fa26afc6745ec2c6e7e15263cf5a6aea8239c988b8f836da373cb8` | `58520ff488fa26afc6745ec2c6e7e15263cf5a6aea8239c988b8f836da373cb8` | `9bdb5e2f0069b80cd871743d8c7b63bce6d25eaac0e3c457956b9f149dfe2241` | 2, 0, 0 |
| `S3_ADD/baseline_inventory.json` | entire file | `1124382353222d9bc702b9b0c5e160de647674a33fe129328906c098a60f72bf` | `1124382353222d9bc702b9b0c5e160de647674a33fe129328906c098a60f72bf` | `a56d02fc14838bbc80266a475b50a87e19cbe72511b5de7bf697ce1f6f14c399` | 2, 0, 0 |
| `S3_ADD/finalization_record.json` | entire file | `040a457176c178cd0e3548b1fc2f02c71e91db07c28d7b98b6ea70ef3191f568` | `040a457176c178cd0e3548b1fc2f02c71e91db07c28d7b98b6ea70ef3191f568` | `7c2dfdb8332ce5851105a5136f5f37be7e563e4316f85c2e3d774cb5447a096a` | 8, 0, 0 |
| `S3_ADD/finalize_stdout.json` | entire file | `829ffc33d3c0538e3be471937c1870974c208d036d9b1db4b8e9b00de1896d71` | `829ffc33d3c0538e3be471937c1870974c208d036d9b1db4b8e9b00de1896d71` | `dc2751d9b717a9a7fc5dd125bf267bc9ec4b3dc57418e4366ae5a8f6760de717` | 8, 0, 0 |
| `S3_ADD/g2_activation_record.json` | entire file | `2d25d9eaa882903af9c3297e8bb0d7199d76b0c5253d5c72f71b2d413b8e07e3` | `2d25d9eaa882903af9c3297e8bb0d7199d76b0c5253d5c72f71b2d413b8e07e3` | `321f85805e0f335505a9302cf66adfdb70eecd38ac7c1b26cb286ac2ec5ad05e` | 5, 0, 0 |
| `S3_ADD/g2_plan_record.json` | entire file | `1630c8199ea02b71cb84fa359852bd8151e87e1d86eacef4c2a2b4eec13f7d7e` | `1630c8199ea02b71cb84fa359852bd8151e87e1d86eacef4c2a2b4eec13f7d7e` | `f8862862322a567e1a4fc34bd98b9977547f69d5f95471981108f7da0b6626fc` | 2, 0, 2 |
| `S3_ADD/g2_publication_record.json` | entire file | `903a21bfc2b0dc36546f5ea26e37626933332822ccf5cce927ff1883fde525d2` | `903a21bfc2b0dc36546f5ea26e37626933332822ccf5cce927ff1883fde525d2` | `2d6711d1be22477b1ec70b8513b37cd8ef8683118223f32a06d64e74654edc96` | 2, 0, 1 |
| `S3_ADD/phase_a_stdout.json` | entire file | `ab3653bb712b1eae2ce341eca83a5b37f026be6f385fb3ddcbfeea2b1902669f` | `ab3653bb712b1eae2ce341eca83a5b37f026be6f385fb3ddcbfeea2b1902669f` | `f7eac14b17fdc2f3339cc3f462d84c0f8b720d4da09a528e6383ee19b4ac55f7` | 2, 0, 4 |
| `S3_ADD/phase_b_stdout.json` | entire file | `c39a68cc7f4c7f8aa73935fc20cff9737f7f1f11adfa4b6eca50a4d56a04cc52` | `c39a68cc7f4c7f8aa73935fc20cff9737f7f1f11adfa4b6eca50a4d56a04cc52` | `f70b4afcd8e2b812dc3b8e026f888fc9b8f22eb2fa0df618e1358899bbace214` | 5, 0, 0 |
| `S3_ADD/post_switch_inventory.json` | entire file | `49276d0842d730dabc8077de71c006bc190b76dd50d848a65303d29a85e3135e` | `49276d0842d730dabc8077de71c006bc190b76dd50d848a65303d29a85e3135e` | `e29627f284d1a19adf21c33c718235bf7ad1c42533f91e2d723c36263cedf1ce` | 2, 0, 0 |
| `S3_ADD/restore_compare.json` | entire file | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | 0, 0, 0 |
| `S3_ADD/restored_inventory.json` | entire file | `a83ea3d53de0d3f996629c845429341955488c508eaa7b53bd41af96411899c9` | `a83ea3d53de0d3f996629c845429341955488c508eaa7b53bd41af96411899c9` | `468063f62b5924c838135ff30bfcc352f75288da9a57f87a444f2453c93da8dd` | 2, 0, 0 |
| `CPM_Session1_Probe.jsonl` | probe records seq 53-60 (Session 3 + S3_ADD) | `880e66b3e42c6c0bf50a97d2dec6cce41a4ccc9fad5c78649ba58502325eebaf` | `d5a46af1c3cb9f4db602223bfb95c51d18749392b46ecba3e679afe775566a0e` | `e8a11da1b499f32add29a575b3a551bc45fea904a17bed65e393a1203a3de673` | 30, 0, 6 |
| `SFM_CSP_G18AN_SaveNewCopy.log` | lines 3263-3651 (S3 process start 00:06:00 on 2026-10-06 to EOF) | `7e2ece78efa61d24690f9addba1baa93993e386d1f1cc7aeef1f0b00665a9f88` | `db2179517b53451ebd1d5c9bad110c05e3c969c0371873be20f1413cd1a89438` | `33f1dcc4a95248f1417f8a3b867dbb30b3578412d2c6e5c7805d65bffee06e4d` | 5, 0, 0 |
