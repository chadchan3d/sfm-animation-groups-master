# -*- coding: utf-8 -*-
"""SFM Character Tools External Updater -- installed-publication backend (L-1, L-2).

Offline Updater v1 (updater_qualification/design/OFFLINE_UPDATER_V1_CONTRACT_AMENDMENT.md):
installation runs only while SFM is closed. This package is the one protected
activation/recovery backend of R2 C4-C12; every installed write goes through it.

L-1: Rebuild My Data, headless. L-2: Use Another TXT and Get Official Data from a local signed
package, headless, through the same backend and replacement route.
"""

VERSION = "0.2.0-l2"
TX_SCHEMA = "sct-updater-tx-1"
PREP_SCHEMA = "sct-updater-prep-2"
