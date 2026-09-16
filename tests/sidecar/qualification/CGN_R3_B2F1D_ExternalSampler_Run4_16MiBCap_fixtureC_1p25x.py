# -*- coding: utf-8 -*-
# R3-B2F1D corrected Run 4 -- fixtureC_1p25x, intended 16 MiB production
# runtime_cap_bytes. This is the important retained-memory boundary
# case: offline recomputation (R3_B2F1D report) shows a current logical
# retained_detached_views charge of 16,733,007 bytes, only 44,209 bytes
# below the 16 MiB (16,777,216-byte) retained gate.
#
# Executes directly at module scope (no __main__ guard, no __file__
# dependency, no sibling-directory import resolution) -- same corrected
# launcher pattern as Runs 2 and 3.
#
# RESTART SFM FIRST. Run this as the ONLY script this SFM session
# executes for this run. DO NOT SAVE any prior experimental scene state.
import imp
import os
import sys

RUN_ID = "Run4_16MiBCap_fixtureC_1p25x"
FIXTURE_NAME = "fixtureC_1p25x"
RUNTIME_CAP_BYTES = 16 * 1024 * 1024

_KNOWN_GAME_ROOT_FALLBACK = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game"
)


def _derive_game_root():
    try:
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    except Exception:
        exe_dir = None
    if exe_dir and os.path.isdir(os.path.join(exe_dir, "usermod", "scripts", "sfm", "mainmenu")):
        return exe_dir
    return _KNOWN_GAME_ROOT_FALLBACK


_GAME_ROOT = _derive_game_root()
_MAINMENU_DIR = os.path.join(_GAME_ROOT, "usermod", "scripts", "sfm", "mainmenu")
_CORE_PATH = os.path.join(_MAINMENU_DIR, "b2f1_campaign_core.py")

_core = imp.load_source("b2f1_campaign_core_%s" % RUN_ID, _CORE_PATH)
_core.run_single_fixture_campaign(FIXTURE_NAME, RUN_ID, runtime_cap_bytes=RUNTIME_CAP_BYTES)
