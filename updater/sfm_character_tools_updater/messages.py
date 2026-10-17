# -*- coding: utf-8 -*-
"""Truthful outcome text (R2 C12, Amendment §2.1) and the backend's stop exception."""

MESSAGES = {
    "NOTHING": "Nothing was installed.",
    "INSTALLED": "Installation complete.",
    "RECOVERED": "Installation recovered.",
    "RESTORED": "Your previous files were restored.",
    "TXT_CHANGED": "Your TXT changed after the interruption. Choose which version to keep.",
    "MISSING": "Automatic recovery is unavailable; required files are missing.",
    "FOLDER_CHANGED": "The data folder changed. No files were overwritten.",
    "UNKNOWN_SCHEMA": "Use a compatible updater to recover this installation.",
    "NOOP": "Already installed; nothing changed.",
    # L-1 additions (Amendment §2.1 steps 4, 6 and 7; §2.3)
    "CLOSE_SFM": "Close SFM and try again. Nothing was changed.",
    "PREPARED": "Your data is prepared. Close SFM, then install.",
    "PREPARED_SFM_RUNNING": "Your data is prepared. SFM appears to be open: close SFM before installing.",
    "PREPARE_AGAIN": "The prepared data no longer matches this installation. Prepare it again. Nothing was changed.",
    "PATH_TOO_LONG": "This installation's folder path is too long for the SFM tools to read. Nothing was changed.",
    "UNVERIFIED": "The installation finished, but the installed files could not be verified. "
                  "Do not use the Character Tools until the data is rebuilt or recovered.",
    "RESTART_RUNNING": "SFM was started during installation. Close and reopen SFM before using the Character Tools.",
    "RESTART_UNKNOWN": "SFM's state could not be confirmed. If SFM is open, close and reopen it before using "
                       "the Character Tools.",
    "REOPEN": "You can now reopen SFM.",
    "NEEDS_REBUILD": "Your previous files were restored; the data still needs rebuilding.",
    "DEPENDENCY": "Updater components failed verification. Nothing was changed.",
    "STOPPED": "Stopped before completion; nothing reported as installed. Run recovery.",
    "RECOVERY_STOPPED": "Recovery stopped before completion; run recovery again.",
    "ERROR": "Unexpected error; state preserved, not reported as success.",
}


class Stop(Exception):
    def __init__(self, outcome, message_key, **details):
        Exception.__init__(self, outcome)
        self.outcome = outcome
        self.message_key = message_key
        self.details = details
