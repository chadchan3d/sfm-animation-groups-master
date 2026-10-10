# K raw outputs (attempts `K1A1`, `K1A2`)

Copied 2026-10-10 from the sealed live attempt folders `%PUBLIC%\Documents\CPM_K\<attempt>\` after each
attempt's `K-Disposition` (its `SHA256SUMS.txt`, also copied, lists every live file's SHA-256).

Each file is an exact byte copy of its source, or, for the cumulative CPM-log copies, an exact byte excerpt from
the attempt's `K-Preflight` CPM-log size. Only five path prefixes are redacted, in every spelling that occurs
(raw, JSON-escaped, forward-slash, lower-case): the SFM install path becomes `<SFM_GAME>`, the local SFM
sessions folder `<SFM_SESSIONS>`, the repository path `<REPOSITORY>`, the Public profile `<PUBLIC>` and the
user profile `<USERPROFILE>`. Every other byte is unchanged. The Normalizer log copies are whole files (the
Normalizer truncates its log at every run start).

## K1A1

CPM-log excerpt offset: 765057 bytes.

Not copied (byte-identical to repository material):

| File | Bytes | SHA-256 | Identity |
|---|---|---|---|
| `generation/g1_source.txt` | 3972355 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | G1 Master (identical to repository sfm_defaultanimationgroups.txt) |

| File | Span | SHA-256 of the original source | SHA-256 of the exact excerpt | SHA-256 of the committed file | Redactions |
|---|---|---|---|---|---|
| `SHA256SUMS.txt` | entire file | `67edd25ab26b6a1c548497aeb203651d0ae1adbb95b97e15753e17218d23f220` | `67edd25ab26b6a1c548497aeb203651d0ae1adbb95b97e15753e17218d23f220` | `67edd25ab26b6a1c548497aeb203651d0ae1adbb95b97e15753e17218d23f220` | none |
| `authority_pins.json` | entire file | `d335f3e4deb5a027f26ef9fc0a4e4011c8eb1e0a0901eaef2742b670a120323b` | `d335f3e4deb5a027f26ef9fc0a4e4011c8eb1e0a0901eaef2742b670a120323b` | `d335f3e4deb5a027f26ef9fc0a4e4011c8eb1e0a0901eaef2742b670a120323b` | none |
| `deployment_after.json` | entire file | `eb25f460f9bbbc7cd9eb74016f63548059d0b1e83571de0bb0c1c1ba80fbee81` | `eb25f460f9bbbc7cd9eb74016f63548059d0b1e83571de0bb0c1c1ba80fbee81` | `eb25f460f9bbbc7cd9eb74016f63548059d0b1e83571de0bb0c1c1ba80fbee81` | none |
| `deployment_before.json` | entire file | `57851d250713e6cf15e3002fad2c7af19de742eb5c549d2f015a16935af04f59` | `57851d250713e6cf15e3002fad2c7af19de742eb5c549d2f015a16935af04f59` | `57851d250713e6cf15e3002fad2c7af19de742eb5c549d2f015a16935af04f59` | none |
| `fixture_manifest.json` | entire file | `c3dfa4a952f66a811e638ffff3e3933ffa6360ee06f9d1302ded19daaf3fe87e` | `c3dfa4a952f66a811e638ffff3e3933ffa6360ee06f9d1302ded19daaf3fe87e` | `2d68359b43c3c81c75c08727abb07739ec5f62e2bd42b9d1acfd3dcb38bcd0f6` | <SFM_SESSIONS> 1 |
| `generation/baseline_inventory.json` | entire file | `dd782e7508cb6d100a3ce507da0deebaaddae38353dc8fb54235ce23ef98fd55` | `dd782e7508cb6d100a3ce507da0deebaaddae38353dc8fb54235ce23ef98fd55` | `4c183f96bc1cb3044e39e641d00f56afecfd2a4e52eb3d9528d27dae15833949` | <SFM_GAME> 2 |
| `generation/untouched_compare.json` | entire file | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | none |
| `generation/untouched_inventory.json` | entire file | `84ade45922b93ad9f62314312996df2a2f467c33ed3eaa29d43d8427be303509` | `84ade45922b93ad9f62314312996df2a2f467c33ed3eaa29d43d8427be303509` | `6297f98602d092f70dbc4ef5a1313b02d299d370503a84e61c2ba797216d0620` | <SFM_GAME> 2 |
| `library_inventories/library_00_preflight.txt` | entire file | `2b2779fcc16643688de0cf1b02b185ec315022dc7c9cfed12f545ea36ffb8fa0` | `2b2779fcc16643688de0cf1b02b185ec315022dc7c9cfed12f545ea36ffb8fa0` | `2b2779fcc16643688de0cf1b02b185ec315022dc7c9cfed12f545ea36ffb8fa0` | none |
| `logs/final.json` | entire file | `9561bd7517609046c8e2a584179a0d878afce7ba9a626843b3bc9b63d7b415be` | `9561bd7517609046c8e2a584179a0d878afce7ba9a626843b3bc9b63d7b415be` | `9561bd7517609046c8e2a584179a0d878afce7ba9a626843b3bc9b63d7b415be` | none |
| `logs/final__SFM_CSP_G18AN_SaveNewCopy.log` | bytes 765057-765057 (written after K-Preflight's recorded CPM-log size) | `05d406c02557a29ad9cbe6bbfacb841471a99215112b60d395185c12326f46ac` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | none |
| `logs/final__sfm_rebuild_control_groups.txt` | entire file | `4180ea506721c41dd02a166eba87d7793d3aa14fe6d63c63b90fbf4d0a482b8a` | `4180ea506721c41dd02a166eba87d7793d3aa14fe6d63c63b90fbf4d0a482b8a` | `96de2e5c468a0f1e687cb721acab04d05f2a4576368da7f5a514da0046e3eec8` | <SFM_GAME> 5 |
| `operator_steps.md` | entire file | `1268da704568810786218ffffa03ce831fb64b0c2d0dd6cc5fa997d12c191a86` | `1268da704568810786218ffffa03ce831fb64b0c2d0dd6cc5fa997d12c191a86` | `1268da704568810786218ffffa03ce831fb64b0c2d0dd6cc5fa997d12c191a86` | none |
| `probe.jsonl` | entire file | `61101415e8d5ce79265868a77a3019acbbbe42d7e2e4efd8795e86b39f68eb24` | `61101415e8d5ce79265868a77a3019acbbbe42d7e2e4efd8795e86b39f68eb24` | `61101415e8d5ce79265868a77a3019acbbbe42d7e2e4efd8795e86b39f68eb24` | none |
| `restoration/disposition.json` | entire file | `95e24538dacc14f205996e3b8d3cf037db1833e5b61e8e82b41b7f8f1e478d72` | `95e24538dacc14f205996e3b8d3cf037db1833e5b61e8e82b41b7f8f1e478d72` | `95e24538dacc14f205996e3b8d3cf037db1833e5b61e8e82b41b7f8f1e478d72` | none |
| `restoration/live_evidence_sha256.txt` | entire file | `f1ddc5458156e24381827b75ea323d7ce79f57c7d44ec1b30f681323af218fcb` | `f1ddc5458156e24381827b75ea323d7ce79f57c7d44ec1b30f681323af218fcb` | `f1ddc5458156e24381827b75ea323d7ce79f57c7d44ec1b30f681323af218fcb` | none |
| `restoration/qualification_removal.json` | entire file | `768958ea19da61981b3b200ce81caea3da35a62a26cc1a91ab621d20b26d38a6` | `768958ea19da61981b3b200ce81caea3da35a62a26cc1a91ab621d20b26d38a6` | `768958ea19da61981b3b200ce81caea3da35a62a26cc1a91ab621d20b26d38a6` | none |
| `restoration/scripts_inventory_after_deploy.txt` | entire file | `49f3aa2984ce4307aa031ac58b7d9e2c1614f55018ba618910c6d1f4889d65ba` | `49f3aa2984ce4307aa031ac58b7d9e2c1614f55018ba618910c6d1f4889d65ba` | `49f3aa2984ce4307aa031ac58b7d9e2c1614f55018ba618910c6d1f4889d65ba` | none |
| `restoration/scripts_inventory_after_probe_removal.txt` | entire file | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | none |
| `restoration/scripts_inventory_before_deploy.txt` | entire file | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | none |
| `restoration/scripts_inventory_final.txt` | entire file | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | none |
| `scene_snapshots/probe_0001.json` | entire file | `6cb6592075bd95c1b5d242d1949f9b25e6d1e70994f10b5f28ad3dae5bd3d0a9` | `6cb6592075bd95c1b5d242d1949f9b25e6d1e70994f10b5f28ad3dae5bd3d0a9` | `6cb6592075bd95c1b5d242d1949f9b25e6d1e70994f10b5f28ad3dae5bd3d0a9` | none |

## K1A2

CPM-log excerpt offset: 765057 bytes.

Not copied (byte-identical to repository material):

| File | Bytes | SHA-256 | Identity |
|---|---|---|---|
| `generation/g1_source.txt` | 3972355 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | G1 Master (identical to repository sfm_defaultanimationgroups.txt) |

| File | Span | SHA-256 of the original source | SHA-256 of the exact excerpt | SHA-256 of the committed file | Redactions |
|---|---|---|---|---|---|
| `SHA256SUMS.txt` | entire file | `18355ca58bc4ea7321309c73408114235115a179e4af9324ac76b88e1bd9e4c1` | `18355ca58bc4ea7321309c73408114235115a179e4af9324ac76b88e1bd9e4c1` | `18355ca58bc4ea7321309c73408114235115a179e4af9324ac76b88e1bd9e4c1` | none |
| `authority_pins.json` | entire file | `a7c537ba7575969b314698e05f927d77557f00c6f0867a568cd3479f48bd95ae` | `a7c537ba7575969b314698e05f927d77557f00c6f0867a568cd3479f48bd95ae` | `a7c537ba7575969b314698e05f927d77557f00c6f0867a568cd3479f48bd95ae` | none |
| `deployment_after.json` | entire file | `079010e34d2cf8a61bbbc089f31f6f9d0604d54650a86de12f7a6d8fd029142a` | `079010e34d2cf8a61bbbc089f31f6f9d0604d54650a86de12f7a6d8fd029142a` | `079010e34d2cf8a61bbbc089f31f6f9d0604d54650a86de12f7a6d8fd029142a` | none |
| `deployment_before.json` | entire file | `7bd05ff72c2e8a5e1d6db12b1740b16a0015eb2eb12eb17ce3cf4acdcb0e4547` | `7bd05ff72c2e8a5e1d6db12b1740b16a0015eb2eb12eb17ce3cf4acdcb0e4547` | `7bd05ff72c2e8a5e1d6db12b1740b16a0015eb2eb12eb17ce3cf4acdcb0e4547` | none |
| `fixture_manifest.json` | entire file | `0654dc16b12bb47680b58486cff9643f90336f5f6412f20b0be3f4553a3507e8` | `0654dc16b12bb47680b58486cff9643f90336f5f6412f20b0be3f4553a3507e8` | `137476d1ea61a8427e42ac8da3a442c086b864b938ffbcc0bbba4f5a87cb2d11` | <SFM_SESSIONS> 1 |
| `generation/baseline_inventory.json` | entire file | `f7a7df257f8560292a06f83dea48c1ea4d0904eedadb521b486abd94b3073b7c` | `f7a7df257f8560292a06f83dea48c1ea4d0904eedadb521b486abd94b3073b7c` | `636a2043a4d7f8ad55d700deb61c1a681b19d5c7df6e2bb9e09bd7dfcd7e6679` | <SFM_GAME> 2 |
| `generation/untouched_compare.json` | entire file | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | none |
| `generation/untouched_inventory.json` | entire file | `6efb83a2a564f09077925db181a1b4ffb8b87c332ed16043451131602f227f16` | `6efb83a2a564f09077925db181a1b4ffb8b87c332ed16043451131602f227f16` | `bbb18823cdd6f4e92e5cc8859f1191439203c7942dda4867570ac36f805ed711` | <SFM_GAME> 2 |
| `library_inventories/library_00_preflight.txt` | entire file | `2b2779fcc16643688de0cf1b02b185ec315022dc7c9cfed12f545ea36ffb8fa0` | `2b2779fcc16643688de0cf1b02b185ec315022dc7c9cfed12f545ea36ffb8fa0` | `2b2779fcc16643688de0cf1b02b185ec315022dc7c9cfed12f545ea36ffb8fa0` | none |
| `library_inventories/library_B4.txt` | entire file | `1852c0e9ed5a50a842c8bce71dba9a2bbb7c987ad13f8bcb20d4433250fc8367` | `1852c0e9ed5a50a842c8bce71dba9a2bbb7c987ad13f8bcb20d4433250fc8367` | `1852c0e9ed5a50a842c8bce71dba9a2bbb7c987ad13f8bcb20d4433250fc8367` | none |
| `library_inventories/library_D3.txt` | entire file | `9a8cc7a502dfa8ceb7747f5374ae188ca60c0278de44b5d7801789dd75da9676` | `9a8cc7a502dfa8ceb7747f5374ae188ca60c0278de44b5d7801789dd75da9676` | `9a8cc7a502dfa8ceb7747f5374ae188ca60c0278de44b5d7801789dd75da9676` | none |
| `library_inventories/library_E7.txt` | entire file | `8ab35f85028991a94d9e51ad283caa90b090494a29abcaf3e7245cc8fcd8eaa9` | `8ab35f85028991a94d9e51ad283caa90b090494a29abcaf3e7245cc8fcd8eaa9` | `8ab35f85028991a94d9e51ad283caa90b090494a29abcaf3e7245cc8fcd8eaa9` | none |
| `logs/N1.json` | entire file | `d667ab7815a125cea5bb1befde1c405c5510cee3fb7638254beda6fb3a96d82a` | `d667ab7815a125cea5bb1befde1c405c5510cee3fb7638254beda6fb3a96d82a` | `d667ab7815a125cea5bb1befde1c405c5510cee3fb7638254beda6fb3a96d82a` | none |
| `logs/N1__SFM_CSP_G18AN_SaveNewCopy.log` | bytes 765057-765057 (written after K-Preflight's recorded CPM-log size) | `05d406c02557a29ad9cbe6bbfacb841471a99215112b60d395185c12326f46ac` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | none |
| `logs/N1__sfm_rebuild_control_groups.txt` | entire file | `c93ecfbdc2b698070216a6bb3150b7e959565753c769ed5cfc3beae00514f2bc` | `c93ecfbdc2b698070216a6bb3150b7e959565753c769ed5cfc3beae00514f2bc` | `c13333ab85d96f03e0ae1e82b25404466527e60527decccbdb0c7339f9b3cafd` | <SFM_GAME> 5 |
| `logs/N2.json` | entire file | `5a5d43e60bd57e0bdaba219d3fbdbf8afe06fa8927adcafeb04c1f4b40471f10` | `5a5d43e60bd57e0bdaba219d3fbdbf8afe06fa8927adcafeb04c1f4b40471f10` | `5a5d43e60bd57e0bdaba219d3fbdbf8afe06fa8927adcafeb04c1f4b40471f10` | none |
| `logs/N2__SFM_CSP_G18AN_SaveNewCopy.log` | bytes 765057-780105 (written after K-Preflight's recorded CPM-log size) | `82d5340cb93488cba9776fbb005f8757a1d636ed476724b47c8eaa69722b9145` | `8154d3a63aa4aa0a1c55344896916d4df9c975f9ef59d39de4df0b6d2a58923a` | `cff61bedd92b145a6a8b466478443bd22f061644e825092ea6aa8e96986022cf` | <SFM_GAME> 1, <USERPROFILE> 4 |
| `logs/N2__sfm_rebuild_control_groups.txt` | entire file | `50ddb8b4cc347915c2eed08a8ac0f6ee56aec38dab2385186bf46ee9db1ac582` | `50ddb8b4cc347915c2eed08a8ac0f6ee56aec38dab2385186bf46ee9db1ac582` | `89ccc6e3a4306e481c7eb12b99807d213c0ad1e5f1f2474428c0debc860dbb4f` | <SFM_GAME> 5 |
| `logs/N3.json` | entire file | `e9be33b166047caaebff560f8202a469ecb512d2489ada049d01bd3a19400c22` | `e9be33b166047caaebff560f8202a469ecb512d2489ada049d01bd3a19400c22` | `e9be33b166047caaebff560f8202a469ecb512d2489ada049d01bd3a19400c22` | none |
| `logs/N3__SFM_CSP_G18AN_SaveNewCopy.log` | bytes 765057-791857 (written after K-Preflight's recorded CPM-log size) | `c3e2744178dc2535d7103cebb504df6a043b8af93922883057062ff7a9264b69` | `622898b5856494bbfd77ff1dc5b309a97382ce348ec5b287952562c0681acba7` | `4ede03efe5f98aa07e924c230301179cd8237ead2148bd6804ae89a2e7b496cc` | <SFM_GAME> 1, <USERPROFILE> 8 |
| `logs/N3__sfm_rebuild_control_groups.txt` | entire file | `1e1a21b38a3a8c89148654ede3338ada7cfced5f5955758dd6613145b0c70dde` | `1e1a21b38a3a8c89148654ede3338ada7cfced5f5955758dd6613145b0c70dde` | `ba69ada32ce667eff1e7a824bc7449a3f3e0b814725a27f35d7f0f8cde972f54` | <SFM_GAME> 5 |
| `logs/N4.json` | entire file | `2c5add3e95230793bff2e76a551169e4149d4500a3916d407956c6d866aa452f` | `2c5add3e95230793bff2e76a551169e4149d4500a3916d407956c6d866aa452f` | `2c5add3e95230793bff2e76a551169e4149d4500a3916d407956c6d866aa452f` | none |
| `logs/N4__SFM_CSP_G18AN_SaveNewCopy.log` | bytes 765057-794374 (written after K-Preflight's recorded CPM-log size) | `e1a04e9407b2b49f7e66132e5029b999f82524cb393186805df24020dde929b4` | `c2da49de62a0fee4e16092cb1d3ab490e58ff903e9512a9150753e5c7d834af4` | `9251347efe0f2bcdd9e08ca29a068c9a1fa15ff7734696d0b435bac8a1f581f3` | <SFM_GAME> 1, <USERPROFILE> 8 |
| `logs/N4__sfm_rebuild_control_groups.txt` | entire file | `8aa66e4bcb1d23af8e387dcd1fad22694b677b394d79d7c38e220562016283f4` | `8aa66e4bcb1d23af8e387dcd1fad22694b677b394d79d7c38e220562016283f4` | `63f2ad5b542f7b1689f9bdb514a4d34c4bcf8f34a1e012ba34fe053cff497b70` | <SFM_GAME> 5 |
| `logs/final.json` | entire file | `a26195200795d57efb85f5b146b4e7dc9e4d4aecea57549a873805bbd996abde` | `a26195200795d57efb85f5b146b4e7dc9e4d4aecea57549a873805bbd996abde` | `a26195200795d57efb85f5b146b4e7dc9e4d4aecea57549a873805bbd996abde` | none |
| `logs/final__SFM_CSP_G18AN_SaveNewCopy.log` | bytes 765057-811877 (written after K-Preflight's recorded CPM-log size) | `3ca7cb3b61d9b0de4e2b8f7388549905bbe41507f5c9876b245b2e1eb7bf5098` | `6a8c638625e2f53b5e318ae7c24c444895f266e821c994b926938d4646fa7b5d` | `957006a6e1553e133bdfab4a397ee681152ed163b19e9d514e21d65ac83e0484` | <SFM_GAME> 2, <USERPROFILE> 24 |
| `logs/final__sfm_rebuild_control_groups.txt` | entire file | `8aa66e4bcb1d23af8e387dcd1fad22694b677b394d79d7c38e220562016283f4` | `8aa66e4bcb1d23af8e387dcd1fad22694b677b394d79d7c38e220562016283f4` | `63f2ad5b542f7b1689f9bdb514a4d34c4bcf8f34a1e012ba34fe053cff497b70` | <SFM_GAME> 5 |
| `operator_steps.md` | entire file | `5bf3a012fb9a0b6c6939f1e2d6adf69bff1f72fae1ceaa5ea35354991d31041f` | `5bf3a012fb9a0b6c6939f1e2d6adf69bff1f72fae1ceaa5ea35354991d31041f` | `5bf3a012fb9a0b6c6939f1e2d6adf69bff1f72fae1ceaa5ea35354991d31041f` | none |
| `preset_readback/B3.json` | entire file | `24557725e4a9c0c6fb5db6518b5be6126f8c33c2247646fee6cc1298453c190e` | `24557725e4a9c0c6fb5db6518b5be6126f8c33c2247646fee6cc1298453c190e` | `24557725e4a9c0c6fb5db6518b5be6126f8c33c2247646fee6cc1298453c190e` | none |
| `preset_readback/B3.source.json` | entire file | `139aa0ad7f481ae090177b527e53272aa5c949fd175e2daae362fc46c060c735` | `139aa0ad7f481ae090177b527e53272aa5c949fd175e2daae362fc46c060c735` | `139aa0ad7f481ae090177b527e53272aa5c949fd175e2daae362fc46c060c735` | none |
| `preset_readback/D2.json` | entire file | `479318e3fd6ef04bb0abe69fba035a88f716d20ada955b39036593091d8d035a` | `479318e3fd6ef04bb0abe69fba035a88f716d20ada955b39036593091d8d035a` | `479318e3fd6ef04bb0abe69fba035a88f716d20ada955b39036593091d8d035a` | none |
| `preset_readback/D2.source.json` | entire file | `4e8f5b80ccfe7d87eb4b99a883016a6bd8b22ca8d123aa90220e6a354889ccd8` | `4e8f5b80ccfe7d87eb4b99a883016a6bd8b22ca8d123aa90220e6a354889ccd8` | `4e8f5b80ccfe7d87eb4b99a883016a6bd8b22ca8d123aa90220e6a354889ccd8` | none |
| `probe.jsonl` | entire file | `f40f805f32a9a48afccbca2412dc6bf146374468f40d4e4dfb3ed1afffa1d404` | `f40f805f32a9a48afccbca2412dc6bf146374468f40d4e4dfb3ed1afffa1d404` | `a76bf79c10b0db3391ee907a4c1ae87d2ab0b1808cc18478624fd75773c88dc6` | <PUBLIC> 10, <SFM_GAME> 54 |
| `restoration/adjudication.txt` | entire file | `2d32f6377b3f7639e2bd0ba1859dfa92e9d5ffe4255cd11089c624947f9eeb28` | `2d32f6377b3f7639e2bd0ba1859dfa92e9d5ffe4255cd11089c624947f9eeb28` | `2d32f6377b3f7639e2bd0ba1859dfa92e9d5ffe4255cd11089c624947f9eeb28` | none |
| `restoration/disposition.json` | entire file | `fe5b0a83a61f9ef9c2d02ec9d0a8f892d114d2efdf73514e0fce3a33c52698d6` | `fe5b0a83a61f9ef9c2d02ec9d0a8f892d114d2efdf73514e0fce3a33c52698d6` | `fe5b0a83a61f9ef9c2d02ec9d0a8f892d114d2efdf73514e0fce3a33c52698d6` | none |
| `restoration/live_evidence_sha256.txt` | entire file | `5e99fa4be654a8565d5e2522b97eb3a6e60ab00a0af7e2901c80a39794c9e99e` | `5e99fa4be654a8565d5e2522b97eb3a6e60ab00a0af7e2901c80a39794c9e99e` | `5e99fa4be654a8565d5e2522b97eb3a6e60ab00a0af7e2901c80a39794c9e99e` | none |
| `restoration/qualification_removal.json` | entire file | `5fcaca336e7f9b1d6dbf8e97d8e6948e9d01342789ab40f0317635c50f6ec137` | `5fcaca336e7f9b1d6dbf8e97d8e6948e9d01342789ab40f0317635c50f6ec137` | `5fcaca336e7f9b1d6dbf8e97d8e6948e9d01342789ab40f0317635c50f6ec137` | none |
| `restoration/scripts_inventory_after_deploy.txt` | entire file | `49f3aa2984ce4307aa031ac58b7d9e2c1614f55018ba618910c6d1f4889d65ba` | `49f3aa2984ce4307aa031ac58b7d9e2c1614f55018ba618910c6d1f4889d65ba` | `49f3aa2984ce4307aa031ac58b7d9e2c1614f55018ba618910c6d1f4889d65ba` | none |
| `restoration/scripts_inventory_after_probe_removal.txt` | entire file | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | none |
| `restoration/scripts_inventory_before_deploy.txt` | entire file | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | none |
| `restoration/scripts_inventory_final.txt` | entire file | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | `59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086` | none |
| `scene_snapshots/probe_0001.json` | entire file | `1c492de0728f3e1d21deacbb09300e508a851a28723b7e0d1154aec897219699` | `1c492de0728f3e1d21deacbb09300e508a851a28723b7e0d1154aec897219699` | `1c492de0728f3e1d21deacbb09300e508a851a28723b7e0d1154aec897219699` | none |
| `scene_snapshots/probe_0002.json` | entire file | `4b0b56cff9c49ef3b897c8b4404cc4d82862974b473a7e5c622e4e61a11c6711` | `4b0b56cff9c49ef3b897c8b4404cc4d82862974b473a7e5c622e4e61a11c6711` | `4b0b56cff9c49ef3b897c8b4404cc4d82862974b473a7e5c622e4e61a11c6711` | none |
| `scene_snapshots/probe_0003.json` | entire file | `83635287466b96afb45341ab389f72aa24154c7ec502208fbc47f0c76819f02b` | `83635287466b96afb45341ab389f72aa24154c7ec502208fbc47f0c76819f02b` | `83635287466b96afb45341ab389f72aa24154c7ec502208fbc47f0c76819f02b` | none |
| `scene_snapshots/probe_0004.json` | entire file | `b66a955bd366b3a81654b9673fd8460aa76b8f31d93d22fd4d057fa3e2277ab9` | `b66a955bd366b3a81654b9673fd8460aa76b8f31d93d22fd4d057fa3e2277ab9` | `b66a955bd366b3a81654b9673fd8460aa76b8f31d93d22fd4d057fa3e2277ab9` | none |
| `scene_snapshots/probe_0005.json` | entire file | `f2d8b499fc207f527cf5d95000ea00e5d1b410e20a5d67e484d2df8684341a87` | `f2d8b499fc207f527cf5d95000ea00e5d1b410e20a5d67e484d2df8684341a87` | `f2d8b499fc207f527cf5d95000ea00e5d1b410e20a5d67e484d2df8684341a87` | none |
| `scene_snapshots/probe_0006.json` | entire file | `f93289530f63657a16e0e8d14e549b9ae5dcfdb683def13f6676806e8cca4f3f` | `f93289530f63657a16e0e8d14e549b9ae5dcfdb683def13f6676806e8cca4f3f` | `f93289530f63657a16e0e8d14e549b9ae5dcfdb683def13f6676806e8cca4f3f` | none |
| `scene_snapshots/probe_0007.json` | entire file | `95ce1d4b64b8395c58228d836eb81bf5a81c913d779ba096154cea551481a059` | `95ce1d4b64b8395c58228d836eb81bf5a81c913d779ba096154cea551481a059` | `95ce1d4b64b8395c58228d836eb81bf5a81c913d779ba096154cea551481a059` | none |
| `scene_snapshots/probe_0008.json` | entire file | `e61cb3518e5ab07096029b4ab9e3786c32eea241ede7fc784381e0976c8011f3` | `e61cb3518e5ab07096029b4ab9e3786c32eea241ede7fc784381e0976c8011f3` | `e61cb3518e5ab07096029b4ab9e3786c32eea241ede7fc784381e0976c8011f3` | none |
| `scene_snapshots/probe_0009.json` | entire file | `2c9a554cb2d78366e9c88c53b1c94ef014c98be91b5a976949a3bda4b3f6d514` | `2c9a554cb2d78366e9c88c53b1c94ef014c98be91b5a976949a3bda4b3f6d514` | `2c9a554cb2d78366e9c88c53b1c94ef014c98be91b5a976949a3bda4b3f6d514` | none |
| `scene_snapshots/probe_0010.json` | entire file | `e51b378cf2edd306c1ae94259ae11ead379a16f6141de285390909100be31d64` | `e51b378cf2edd306c1ae94259ae11ead379a16f6141de285390909100be31d64` | `e51b378cf2edd306c1ae94259ae11ead379a16f6141de285390909100be31d64` | none |
| `scene_snapshots/probe_0011.json` | entire file | `fbcabdd5eddb98f621a3b48229e0f34b5a3f632ec6c25398c2121e218562cbc2` | `fbcabdd5eddb98f621a3b48229e0f34b5a3f632ec6c25398c2121e218562cbc2` | `fbcabdd5eddb98f621a3b48229e0f34b5a3f632ec6c25398c2121e218562cbc2` | none |
| `scene_snapshots/probe_0012.json` | entire file | `e42c4d6c32488ff6b87d1d644811bce7ed84afd430f23eba17a925956a8482d0` | `e42c4d6c32488ff6b87d1d644811bce7ed84afd430f23eba17a925956a8482d0` | `e42c4d6c32488ff6b87d1d644811bce7ed84afd430f23eba17a925956a8482d0` | none |
