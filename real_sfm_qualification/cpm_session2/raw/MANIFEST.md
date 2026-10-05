# CPM Session 2 - raw outputs

Copied 2026-10-05 from `%PUBLIC%\Documents` (the probe JSONL and the CPM log) and from
`%PUBLIC%\Documents\CPM_Session2\` (all four campaign folders).

Each file is an exact byte excerpt of its source. Only three path prefixes are redacted, for
repository sanitation:
- the SFM install path becomes `<SFM_GAME>`;
- the user-profile path becomes `<USERPROFILE>`;
- the Public profile path becomes `<PUBLIC>`.

Every other byte, including line endings and the PowerShell `Out-File` BOM, is unchanged.

## Not copied (byte-identical to repository material; hash-verified at copy time)

| File | Bytes | SHA-256 | Identity |
|---|---|---|---|
| `S2A/g1_source.txt` | 3972355 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | G1 (identical to repository sfm_defaultanimationgroups.txt) |
| `S2A/g2_source.txt` | 3972356 | `54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7` | G2 (repository Master + one LF) |
| `S2A_R2/g1_source.txt` | 3972355 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | G1 (identical to repository sfm_defaultanimationgroups.txt) |
| `S2A_R2/g2_source.txt` | 3972356 | `54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7` | G2 (repository Master + one LF) |
| `S2B/g1_source.txt` | 3972355 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | G1 (identical to repository sfm_defaultanimationgroups.txt) |
| `S2B_R2/g1_source.txt` | 3972355 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | G1 (identical to repository sfm_defaultanimationgroups.txt) |
| `S2B_R2/g2_source.txt` | 3972356 | `54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7` | G2 (repository Master + one LF) |

## Not retained

- the PowerShell window transcripts (operator `S2 … OK` lines are corroborated by the tool records);
- the SFM console.

## Copied files

| File | Span | SHA-256 of the original source | SHA-256 of the exact excerpt | SHA-256 of the committed file | Redactions (`<SFM_GAME>`, `<USERPROFILE>`, `<PUBLIC>`) |
|---|---|---|---|---|---|
| `S2A/baseline_inventory.json` | entire file | `542c1766fe808dea66fdfb6fd2cbc51189a1a74c2045d242f4a598c712f8c539` | `542c1766fe808dea66fdfb6fd2cbc51189a1a74c2045d242f4a598c712f8c539` | `9d7dbeaee6cf438e46fa8d794119f0bf97782dcee23f2876102d893c7b874d08` | 2, 0, 0 |
| `S2A/finalization_record.json` | entire file | `024097abdd388f9471e27dbc259d4fe3b6b26c6cb6e93f58f840441b6f72bd8b` | `024097abdd388f9471e27dbc259d4fe3b6b26c6cb6e93f58f840441b6f72bd8b` | `d38192d5a148ec29a021991bc4b5796367f07a30b8c1ba0e05e0750d06df143d` | 8, 0, 0 |
| `S2A/finalize_stdout.json` | entire file | `c31bd99e5e7dacf313834594c818141a1491e9a747d605a42c7f8d4c7979ed14` | `c31bd99e5e7dacf313834594c818141a1491e9a747d605a42c7f8d4c7979ed14` | `25c8ecfc3eaca978eff501a5ae4c0d536c76f4f6213814b9fa2663c8f98ce195` | 8, 0, 0 |
| `S2A/g2_activation_record.json` | entire file | `d46e3c17ff0077bc9065a73969203b4fa07a9d5586fb953ac402501b10df33e1` | `d46e3c17ff0077bc9065a73969203b4fa07a9d5586fb953ac402501b10df33e1` | `c4de5c9c3029eca3383ff7295f6756a7c06649b536c4e5faad5b6f07d5d35b03` | 5, 0, 0 |
| `S2A/g2_plan_record.json` | entire file | `29a185004639251b0aa0d295cd066f1329d2cf9a6e9085eda2f5d45eb834c60a` | `29a185004639251b0aa0d295cd066f1329d2cf9a6e9085eda2f5d45eb834c60a` | `801dff150df975bb82aef18be4caa88f134f915a510610101843beddfcb68948` | 2, 0, 2 |
| `S2A/g2_publication_record.json` | entire file | `be28b105db4b4d2fa2c40ac6acd6f8252d63da53dceb7f0a47576dc4d89edef8` | `be28b105db4b4d2fa2c40ac6acd6f8252d63da53dceb7f0a47576dc4d89edef8` | `72dc78c0e8384c39000d4bc1c01fbff3aae6afbc4b4cf9cf97a288d69e1db503` | 2, 0, 1 |
| `S2A/phase_a_stdout.json` | entire file | `bfb0a33abdcee2b0e0db17ca890c84a35667a77cd53a021799b167cdaad5b577` | `bfb0a33abdcee2b0e0db17ca890c84a35667a77cd53a021799b167cdaad5b577` | `9e315514e1fce267d001a4c0ec63f189abcf60733cb46b2f0fd0278abeb8223b` | 2, 0, 4 |
| `S2A/phase_b_stdout.json` | entire file | `458569cb1a5b6062aaf1fe1c4ce3defc7f6c9c315b55ccf3162def34f0a3b9e6` | `458569cb1a5b6062aaf1fe1c4ce3defc7f6c9c315b55ccf3162def34f0a3b9e6` | `8647512f7df720880c7ea6fe0aa41f6eea6186163a62d8dbadae7841fc03fda1` | 5, 0, 0 |
| `S2A_R2/baseline_inventory.json` | entire file | `210a97a7b007a6f90c44624f62b1c3c17cc6336c5f9a748b01d9e03a8528b319` | `210a97a7b007a6f90c44624f62b1c3c17cc6336c5f9a748b01d9e03a8528b319` | `774ce808e3c6958af2f101a98b1ae6327607d9864ac30e8ffc7dfc175d179fcb` | 2, 0, 0 |
| `S2A_R2/finalization_record.json` | entire file | `a895334f39f65cfd7eaf69fe09dbc774273c4dd530540838f77e2f56f7453dcd` | `a895334f39f65cfd7eaf69fe09dbc774273c4dd530540838f77e2f56f7453dcd` | `ed7fcf4b576b13db7073c6d8655cfdd301052236c923334007f1b5c08913828c` | 8, 0, 0 |
| `S2A_R2/finalize_stdout.json` | entire file | `eebb347bee5b768f3474be43ee7025b8d3ae5d2122cfc35e41ba1924a6948e66` | `eebb347bee5b768f3474be43ee7025b8d3ae5d2122cfc35e41ba1924a6948e66` | `60ce378791f792646c0db2530818b51af91f64feb1ac9f2bc98018a686c7a356` | 8, 0, 0 |
| `S2A_R2/g2_activation_record.json` | entire file | `952c19cb2f51344e07b5d9921ce1698a4c413cdae64529f7b1fedbf74333efa0` | `952c19cb2f51344e07b5d9921ce1698a4c413cdae64529f7b1fedbf74333efa0` | `4879d55d8f6ac42ed0a62aa0071908334ec86074f64ce90e46fa2112fdbccca7` | 5, 0, 0 |
| `S2A_R2/g2_plan_record.json` | entire file | `a9542fa534dc67de1603674a749da28abef0ea26e3826b2b35fc5f4584313bf1` | `a9542fa534dc67de1603674a749da28abef0ea26e3826b2b35fc5f4584313bf1` | `985bdba8572f3a8801aecfe5d8bb908a4da0c74e3aa1428d16c603ba4e168e89` | 2, 0, 2 |
| `S2A_R2/g2_publication_record.json` | entire file | `8242b05a0e12b25bacfde6cfd7b2a29f9c554c8e0c500f458856aff39f81c35a` | `8242b05a0e12b25bacfde6cfd7b2a29f9c554c8e0c500f458856aff39f81c35a` | `2e3408168fa63c45f0034a5c83f0a53a533f014f4a965bde9f6a7abe85a1c3a9` | 2, 0, 1 |
| `S2A_R2/phase_a_stdout.json` | entire file | `ffc20eb93a70b54687bcc07d4e9280073e6c4939c1a6d770e0211c207436d41d` | `ffc20eb93a70b54687bcc07d4e9280073e6c4939c1a6d770e0211c207436d41d` | `f7757d6764aae4c5751741bbcd7964c91385715897c0a865237689478a118069` | 2, 0, 4 |
| `S2A_R2/phase_b_stdout.json` | entire file | `1f427aef56272e6fab461b673df1d63cee47c737fa767461ab9c2e3520aa6649` | `1f427aef56272e6fab461b673df1d63cee47c737fa767461ab9c2e3520aa6649` | `8f723d5dff69b79e766d0d4fe73fb819a03a4d31388c1c183e287fb1e38567cc` | 5, 0, 0 |
| `S2A_R2/post_switch_inventory.json` | entire file | `eab95c3d2305e3147d992f12a2c2b51b546701c213100931d2677ed0088e297d` | `eab95c3d2305e3147d992f12a2c2b51b546701c213100931d2677ed0088e297d` | `a9c9ef41fc6b28634c30325894c8288cbde6c75c1bc9bd7b470593a37077753d` | 2, 0, 0 |
| `S2A_R2/restore_compare.json` | entire file | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | 0, 0, 0 |
| `S2A_R2/restored_inventory.json` | entire file | `ac679c4f853c9c3bb244f4caebae0c78af23ff3ae3799e65e9f2c25e08c58089` | `ac679c4f853c9c3bb244f4caebae0c78af23ff3ae3799e65e9f2c25e08c58089` | `1918b9384e7607ef84988e6563383777dab629391474735c2dd89d1a41374384` | 2, 0, 0 |
| `S2B/baseline_inventory.json` | entire file | `79513f5539c3fd04e2a13d960fce63d15ba9c7ca5c5bd0ca1dc42fa38e521c92` | `79513f5539c3fd04e2a13d960fce63d15ba9c7ca5c5bd0ca1dc42fa38e521c92` | `941b47b47da219b37e00b891b57e97d29d2389ecbce7666faa89b94ad0640dd2` | 2, 0, 0 |
| `S2B/library_1_before_prompt.txt` | entire file | `e60d737deae21ed345b6085bc6d62766b4b3906104e92fe3c4d1e56a3b21d920` | `e60d737deae21ed345b6085bc6d62766b4b3906104e92fe3c4d1e56a3b21d920` | `e60d737deae21ed345b6085bc6d62766b4b3906104e92fe3c4d1e56a3b21d920` | 0, 0, 0 |
| `S2B_R2/baseline_inventory.json` | entire file | `0a6c8726bde215c6d2310c695b05fe7c39a4efff4280922b3055a73e244d34d6` | `0a6c8726bde215c6d2310c695b05fe7c39a4efff4280922b3055a73e244d34d6` | `07f1191e00b6923233b79d427f0e0e4d83e505e05542deb729bb6381f481b2e0` | 2, 0, 0 |
| `S2B_R2/finalization_record.json` | entire file | `fdfc55364ad890397c3169fe4bdb47bdb7103421111186ace7dd216746d3c31c` | `fdfc55364ad890397c3169fe4bdb47bdb7103421111186ace7dd216746d3c31c` | `89ec2e93d87e51b3bb6ce2bf518e934f9bb902db62f8020945f00218618d2e6d` | 8, 0, 0 |
| `S2B_R2/finalize_stdout.json` | entire file | `3a2c4d7a2dbf843805fdb43994dd128aca36e8ccc1808d2e468b83a5e847b93f` | `3a2c4d7a2dbf843805fdb43994dd128aca36e8ccc1808d2e468b83a5e847b93f` | `082d16ccd5d3a51f48af5464ada58eea4a2d10ec1825d1a86f3747485e69516c` | 8, 0, 0 |
| `S2B_R2/g2_activation_record.json` | entire file | `59bfbbfec185e9adf402bdab14dfd53c8eaee91fa70f23b6812ecfcf2f3d3f16` | `59bfbbfec185e9adf402bdab14dfd53c8eaee91fa70f23b6812ecfcf2f3d3f16` | `a264e7a8b3f0225333f80fa1d241351cefaa30ddb04b8eaac558a8d122d8218a` | 5, 0, 0 |
| `S2B_R2/g2_plan_record.json` | entire file | `0e0aab3666f83640fc2b859b392d6f42b24bdbbda081802a147d03444c24d000` | `0e0aab3666f83640fc2b859b392d6f42b24bdbbda081802a147d03444c24d000` | `21ba569428a1c05f2ef84f85e21b9f68b75add853b45d538f45ef5f9fef42985` | 2, 0, 2 |
| `S2B_R2/g2_publication_record.json` | entire file | `054ec9558c36a72188d643064080a257d48ed723feb83eea8099130787bdb450` | `054ec9558c36a72188d643064080a257d48ed723feb83eea8099130787bdb450` | `d67c83740bfdb788e60f2d56ab15469cb8f90a055276e216ba7913a80707e577` | 2, 0, 1 |
| `S2B_R2/library_1_before_prompt.txt` | entire file | `5605a2d9855cd59be7efde7ac5a1ffd6c443ea78d1bb015f478c9d03a5ab1ca5` | `5605a2d9855cd59be7efde7ac5a1ffd6c443ea78d1bb015f478c9d03a5ab1ca5` | `5605a2d9855cd59be7efde7ac5a1ffd6c443ea78d1bb015f478c9d03a5ab1ca5` | 0, 0, 0 |
| `S2B_R2/library_2_g2_active_prompt_open.txt` | entire file | `5605a2d9855cd59be7efde7ac5a1ffd6c443ea78d1bb015f478c9d03a5ab1ca5` | `5605a2d9855cd59be7efde7ac5a1ffd6c443ea78d1bb015f478c9d03a5ab1ca5` | `5605a2d9855cd59be7efde7ac5a1ffd6c443ea78d1bb015f478c9d03a5ab1ca5` | 0, 0, 0 |
| `S2B_R2/library_3_after_refusal.txt` | entire file | `5605a2d9855cd59be7efde7ac5a1ffd6c443ea78d1bb015f478c9d03a5ab1ca5` | `5605a2d9855cd59be7efde7ac5a1ffd6c443ea78d1bb015f478c9d03a5ab1ca5` | `5605a2d9855cd59be7efde7ac5a1ffd6c443ea78d1bb015f478c9d03a5ab1ca5` | 0, 0, 0 |
| `S2B_R2/library_4_after_g2_save.txt` | entire file | `ab7c3c146268c3820973bd4b60a2011e4e4e4691be474b49cecb1244dd97fee4` | `ab7c3c146268c3820973bd4b60a2011e4e4e4691be474b49cecb1244dd97fee4` | `ab7c3c146268c3820973bd4b60a2011e4e4e4691be474b49cecb1244dd97fee4` | 0, 0, 0 |
| `S2B_R2/phase_a_stdout.json` | entire file | `564bf239d587c73889916795debd5679996d41fda8a79f16a5e30d82a3de6260` | `564bf239d587c73889916795debd5679996d41fda8a79f16a5e30d82a3de6260` | `59aab0599337192c61c427d9edb9168d4b6abf625657b12cf0da89db0b788995` | 2, 0, 4 |
| `S2B_R2/phase_b_stdout.json` | entire file | `65e829a0a24444e01b1c4d7ddb8089268ce7737ea66973b59562e4e190cfdcf2` | `65e829a0a24444e01b1c4d7ddb8089268ce7737ea66973b59562e4e190cfdcf2` | `24dfe4dd0ccf2c9467a2685405ae393d47e927b1f788054037e0ca27f0fd316d` | 5, 0, 0 |
| `S2B_R2/post_switch_inventory.json` | entire file | `cf0f3de8d43525c7fee72cec5031284567f6f9d51d0f845abbe558a8b7631167` | `cf0f3de8d43525c7fee72cec5031284567f6f9d51d0f845abbe558a8b7631167` | `06d9dc7c40afc7fb036674a4eb6497904a7717ce271f232a673c5188632204e1` | 2, 0, 0 |
| `S2B_R2/restore_compare.json` | entire file | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | 0, 0, 0 |
| `S2B_R2/restored_inventory.json` | entire file | `93d70f021f0e1dc8b5579a19f46b80c65d1061c165a20e243f185c357b0a3507` | `93d70f021f0e1dc8b5579a19f46b80c65d1061c165a20e243f185c357b0a3507` | `6d59d0bfd314f75b2e0cb4db89efd2ca83937341dfcec1ee2ca11d16962faa79` | 2, 0, 0 |
| `CPM_Session1_Probe.jsonl` | probe records seq 39-52 (Session 2) | `dfe1672dd82a5e1b7bd7fb4597262767cfe4e48ee593019cb4be0d2bb72ab626` | `6ea99e85974b2934904a6b2c1b98d7e9283bfd314fb6dcdd14639597b7d184d6` | `565e438f582e7cbc5521ea7008dea34eb23620fae0c68c7c288b4d465ddb78db` | 50, 0, 10 |
| `SFM_CSP_G18AN_SaveNewCopy.log` | lines 2305-3262 (S2A process start 04:03:52 on 2026-10-01 to EOF) | `9409ebe19ed0dc70722b5b6ddfa4e735509b0d3b014d12e2a517741d21ef36ad` | `c53611231bcfd4503a5122526b4c4085474480ed603a33a60983d2cb44313129` | `b143fb123c91a01aa4cf3350b2b66b8bfc344de5b761dfd00ad1a3d26fa55d17` | 12, 8, 0 |
