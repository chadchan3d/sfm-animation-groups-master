# CPM Session 4 - raw outputs

Copied 2026-10-06 from `%PUBLIC%\Documents` (the probe JSONL and the CPM log) and from
`%PUBLIC%\Documents\CPM_Session4\` (campaigns S4A and S4F).

Each file is an exact byte excerpt of its source. Only three path prefixes are redacted, for
repository sanitation:
- the SFM install path becomes `<SFM_GAME>`;
- the user-profile path becomes `<USERPROFILE>`;
- the Public profile path becomes `<PUBLIC>`.

Every other byte, including line endings and the PowerShell `Out-File` BOM, is unchanged.

## Not copied (byte-identical to repository material; hash-verified at copy time)

| File | Bytes | SHA-256 | Identity |
|---|---|---|---|
| `S4A/g1_source.txt` | 3972355 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | G1 (identical to repository sfm_defaultanimationgroups.txt) |
| `S4F/g1_source.txt` | 3972355 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | G1 (identical to repository sfm_defaultanimationgroups.txt) |

## Not retained

- the PowerShell window transcripts (operator `S2 … OK` lines are corroborated by the tool records);
- the SFM console.

## Copied files

| File | Span | SHA-256 of the original source | SHA-256 of the exact excerpt | SHA-256 of the committed file | Redactions (`<SFM_GAME>`, `<USERPROFILE>`, `<PUBLIC>`) |
|---|---|---|---|---|---|
| `S4A/baseline_inventory.json` | entire file | `0f57cdf28facffc19cd822bc59bd530304e276d20665ad7e4b30aeec674c2ecf` | `0f57cdf28facffc19cd822bc59bd530304e276d20665ad7e4b30aeec674c2ecf` | `7445f84be1cc31b935eb7459c8d7692133ac663e44fa7955af6b53e958a230d1` | 2, 0, 0 |
| `S4A/deploy_after_removal.txt` | entire file | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | 0, 0, 0 |
| `S4A/deploy_before_harness.txt` | entire file | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | 0, 0, 0 |
| `S4A/harness_deploy_record.json` | entire file | `e60917359f444fcc7fda1ed6c4e3551aae1d326954b92eff9f4ba612f086065e` | `e60917359f444fcc7fda1ed6c4e3551aae1d326954b92eff9f4ba612f086065e` | `e60917359f444fcc7fda1ed6c4e3551aae1d326954b92eff9f4ba612f086065e` | 0, 0, 0 |
| `S4A/s1_arm.json` | entire file | `0dbc3aa40932b5a019dd532f1fc074ed57223c831998c21d15c5fd88377f5c00` | `0dbc3aa40932b5a019dd532f1fc074ed57223c831998c21d15c5fd88377f5c00` | `0dbc3aa40932b5a019dd532f1fc074ed57223c831998c21d15c5fd88377f5c00` | 0, 0, 0 |
| `S4A/s1_fire.json` | entire file | `efa15b54d81958a74c636bbf9ebfb66cd740670a5f607b95d7704f8e2a058b65` | `efa15b54d81958a74c636bbf9ebfb66cd740670a5f607b95d7704f8e2a058b65` | `efa15b54d81958a74c636bbf9ebfb66cd740670a5f607b95d7704f8e2a058b65` | 0, 0, 0 |
| `S4A/s1_state.json` | entire file | `2776935e8836fb8253df274dcb8d501e9c8d3975cce7afbb5ef40a130b78712e` | `2776935e8836fb8253df274dcb8d501e9c8d3975cce7afbb5ef40a130b78712e` | `2776935e8836fb8253df274dcb8d501e9c8d3975cce7afbb5ef40a130b78712e` | 0, 0, 0 |
| `S4A/s2_arm.json` | entire file | `239b8199d960305e98eadb65f2cf5f766654a8d348c21b58f1708d4e3e448c69` | `239b8199d960305e98eadb65f2cf5f766654a8d348c21b58f1708d4e3e448c69` | `239b8199d960305e98eadb65f2cf5f766654a8d348c21b58f1708d4e3e448c69` | 0, 0, 0 |
| `S4A/s2_fire.json` | entire file | `95a4e7717b05ced7fc7fae60f8fee0fae82738c4eb12df0e7ca141da48550b93` | `95a4e7717b05ced7fc7fae60f8fee0fae82738c4eb12df0e7ca141da48550b93` | `95a4e7717b05ced7fc7fae60f8fee0fae82738c4eb12df0e7ca141da48550b93` | 0, 0, 0 |
| `S4A/s2_state.json` | entire file | `4177126de29767201f29c21d89bea217550ba1332e98e3df6645a9afd9a58f4d` | `4177126de29767201f29c21d89bea217550ba1332e98e3df6645a9afd9a58f4d` | `4177126de29767201f29c21d89bea217550ba1332e98e3df6645a9afd9a58f4d` | 0, 0, 0 |
| `S4A/untouched_compare.json` | entire file | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | 0, 0, 0 |
| `S4A/untouched_inventory.json` | entire file | `04f917dbe72d1bcfc9e252c0b2c3673d425c3b0b733622e1794b979fff62263c` | `04f917dbe72d1bcfc9e252c0b2c3673d425c3b0b733622e1794b979fff62263c` | `1ee84a10c30a8900df8185fd1bca1f3c6e9a5ee88dd0b5241099ba18816ac460` | 2, 0, 0 |
| `S4F/baseline_inventory.json` | entire file | `393f5343013ee6542a4aad04ddbe5b4403e04e8fcb28c61e04fa552bd47be08d` | `393f5343013ee6542a4aad04ddbe5b4403e04e8fcb28c61e04fa552bd47be08d` | `84a3c5be9341e979d0b5b71d074da8c00f767eea34de81e6ea5d0701394ed9a3` | 2, 0, 0 |
| `S4F/deploy_after_removal.txt` | entire file | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | 0, 0, 0 |
| `S4F/deploy_before_harness.txt` | entire file | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` | 0, 0, 0 |
| `S4F/harness_deploy_record.json` | entire file | `a038a29c46be0bb2931df4c7411e808fab568e9990cfe2cb22d784fdd543316a` | `a038a29c46be0bb2931df4c7411e808fab568e9990cfe2cb22d784fdd543316a` | `a038a29c46be0bb2931df4c7411e808fab568e9990cfe2cb22d784fdd543316a` | 0, 0, 0 |
| `S4F/s1_arm.json` | entire file | `329230a56635a1a1e9f6ae8f8b98ce9c8f64c3e5952907d1474055d77eb1cdd5` | `329230a56635a1a1e9f6ae8f8b98ce9c8f64c3e5952907d1474055d77eb1cdd5` | `329230a56635a1a1e9f6ae8f8b98ce9c8f64c3e5952907d1474055d77eb1cdd5` | 0, 0, 0 |
| `S4F/s1_fire.json` | entire file | `49abce952f2a4724d81cf7311a4855cadc3337e58915049d4769f79cae76cda8` | `49abce952f2a4724d81cf7311a4855cadc3337e58915049d4769f79cae76cda8` | `49abce952f2a4724d81cf7311a4855cadc3337e58915049d4769f79cae76cda8` | 0, 0, 0 |
| `S4F/s1_state.json` | entire file | `c64ffeb071e855f47df49aef5ae79be1caa0b588ec5c7cf0c045619d03945f78` | `c64ffeb071e855f47df49aef5ae79be1caa0b588ec5c7cf0c045619d03945f78` | `c64ffeb071e855f47df49aef5ae79be1caa0b588ec5c7cf0c045619d03945f78` | 0, 0, 0 |
| `S4F/s2_arm.json` | entire file | `1bdce66f6041a1c09acff49f17af44f5e2796e99e143c2c533d46ff06c55e520` | `1bdce66f6041a1c09acff49f17af44f5e2796e99e143c2c533d46ff06c55e520` | `1bdce66f6041a1c09acff49f17af44f5e2796e99e143c2c533d46ff06c55e520` | 0, 0, 0 |
| `S4F/s2_fire.json` | entire file | `6209c1f4b0c49c9db208a673ecc319a849fd4d6184939a3600c38ed1c99b02e4` | `6209c1f4b0c49c9db208a673ecc319a849fd4d6184939a3600c38ed1c99b02e4` | `6209c1f4b0c49c9db208a673ecc319a849fd4d6184939a3600c38ed1c99b02e4` | 0, 0, 0 |
| `S4F/s2_state.json` | entire file | `b5ea8f0111fa97b98443af4fd9f329f9d150a161fb89dfc7f301874fca7d14c3` | `b5ea8f0111fa97b98443af4fd9f329f9d150a161fb89dfc7f301874fca7d14c3` | `b5ea8f0111fa97b98443af4fd9f329f9d150a161fb89dfc7f301874fca7d14c3` | 0, 0, 0 |
| `S4F/untouched_compare.json` | entire file | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | `4dec31d1ecad6914ef785c59006d395a8452c2001973c0b21628b4b4175704f0` | 0, 0, 0 |
| `S4F/untouched_inventory.json` | entire file | `5ed32c6cddd753b87d515294498cd6e61ea66653473653deacaec1062fe28961` | `5ed32c6cddd753b87d515294498cd6e61ea66653473653deacaec1062fe28961` | `66a7c1af07953ae223039a66b7830f9f6173f2a1a33668a549e33a4bbcc6354b` | 2, 0, 0 |
| `CPM_Session1_Probe.jsonl` | probe records seq 61-71 (S4A + S4F) | `ecf1595e8685ca70789732faeaf7fda16104996fd9745625650697b70f04d42b` | `274ae937492294d2e7b5d1893d7edacb0dd87411ce06994b2075884f31d648ca` | `a99837844b6d8bae4af9d23bdc328513252b5a33891279bda4c17d2d5e4ef8c0` | 45, 0, 9 |
| `SFM_CSP_G18AN_SaveNewCopy.log` | lines 3652-4079 (S4A process start 11:27:49 on 2026-10-06 to EOF) | `ae7bbaa037e0f17f1d50d785e73dce1beaa95292760827183176016700826fc2` | `b3ed4156297accec4b89385a59bc6f05b31c84d1026bf7f09db7dfa38d8bb97a` | `5b108d48d940c73cc2881019d04d38def160edc1bb03ca2b74c4bc958ee38591` | 14, 0, 0 |
