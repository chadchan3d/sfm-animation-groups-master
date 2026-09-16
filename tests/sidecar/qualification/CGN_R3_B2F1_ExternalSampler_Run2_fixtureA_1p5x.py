# -*- coding: utf-8 -*-
# R3-B2F1 targeted external-sampler boundary campaign -- Run2_fixtureA_1p5x.
#
# IMPORTANT -- THIS SCRIPT DOES NOT AUTO-RUN. No QTimer/schedule() call
# at module scope. It runs ONLY when executed directly, exactly like
# CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01.py did.
#
# RESTART SFM FIRST. Run this as the ONLY script this SFM session
# executes for this run -- it targets ONE fixture (fixtureA_1p5x) from a
# fresh process so its measurements are not contaminated by any other
# run's already-warmed module state or already-open providers.
import b2f1_campaign_core as core

RUN_ID = "Run2_fixtureA_1p5x"
FIXTURE_NAME = "fixtureA_1p5x"


def _guarded_run():
    core.run_single_fixture_campaign(FIXTURE_NAME, RUN_ID)


if __name__ == "__main__":
    _guarded_run()
else:
    print(u"%s loaded (import only) -- run this file directly to execute "
          u"the %s campaign run. It does NOT auto-run." % (RUN_ID, FIXTURE_NAME))
