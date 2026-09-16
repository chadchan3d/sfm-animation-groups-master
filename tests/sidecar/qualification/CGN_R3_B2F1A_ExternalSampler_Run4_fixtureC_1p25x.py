# -*- coding: utf-8 -*-
# R3-B2F1A CORRECTED launcher -- Run4_fixtureC_1p25x.
#
# Correction from the original CGN_R3_B2F1_ExternalSampler_* launchers:
# SFM Main Menu manual execution does not set __name__ == "__main__" and
# does not define __file__, and the sibling mainmenu directory is not
# guaranteed to already be on sys.path. This launcher therefore:
#   - executes directly at module scope (no __main__ guard);
#   - derives the game root from sys.executable (inside real SFM,
#     sys.executable IS game\sfm.exe itself, confirmed in this project's
#     own prior H1 runtime audits), not from __file__;
#   - loads the shared campaign core (b2f1_campaign_core.py) by its own
#     absolute path via imp.load_source, never a bare sibling `import`.
#
# RESTART SFM FIRST. Run this as the ONLY script this SFM session
# executes for this run -- it targets ONE fixture (fixtureC_1p25x) from a
# fresh process so its measurements are not contaminated by any other
# run's already-warmed module state or already-open providers.
# DO NOT SAVE any prior experimental scene state -- restart to discard it.
import imp
import os
import sys

RUN_ID = "Run4_fixtureC_1p25x"
FIXTURE_NAME = "fixtureC_1p25x"

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
_core.run_single_fixture_campaign(FIXTURE_NAME, RUN_ID)
