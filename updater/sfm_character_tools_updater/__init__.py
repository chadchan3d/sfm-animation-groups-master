# -*- coding: utf-8 -*-
"""SFM Character Tools External Updater -- installed-publication backend (L-1).

Offline Updater v1 (updater_qualification/design/OFFLINE_UPDATER_V1_CONTRACT_AMENDMENT.md):
installation runs only while SFM is closed. This package is the one protected
activation/recovery backend of R2 C4-C12; every installed write goes through it.

L-1 scope: Rebuild My Data, headless. The replacement route used later by Use Another TXT
and Get Official Data (L-2) is present in the backend but not exposed by the worker.
"""

VERSION = "0.1.0-l1"
TX_SCHEMA = "sct-updater-tx-1"
PREP_SCHEMA = "sct-updater-prep-1"
