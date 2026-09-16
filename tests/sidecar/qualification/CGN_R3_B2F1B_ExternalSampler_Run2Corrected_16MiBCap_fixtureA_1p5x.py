# -*- coding: utf-8 -*-
# R3-B2F1B CORRECTED Run 2 rerun -- fixtureA_1p5x, intended 16 MiB
# production runtime_cap_bytes (NOT the 64 MiB exploratory override the
# original Run 2 used). See R3_B2F1B_ReadCapPeak_Isolation_Report.md
# Section 1-4: the original Run 2's ~63.6 MiB transient peak was almost
# entirely explained by f.read(runtime_cap_bytes + 1) being sized off
# the 64 MiB exploratory cap, not by artifact content -- this rerun
# measures the SAME fixture, SAME stages, under the cap intended for
# the actual candidate production envelope.
#
# Executes directly at module scope (no __main__ guard, no __file__
# dependency, no sibling-directory import resolution) -- same corrected
# launcher pattern as CGN_R3_B2F1A_ExternalSampler_Run2_fixtureA_1p5x.py.
#
# RESTART SFM FIRST. Run this as the ONLY script this SFM session
# executes for this run. DO NOT SAVE any prior experimental scene state.
import imp
import os
import sys

RUN_ID = "Run2Corrected_16MiBCap_fixtureA_1p5x"
FIXTURE_NAME = "fixtureA_1p5x"
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
