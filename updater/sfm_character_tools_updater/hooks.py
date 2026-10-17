# -*- coding: utf-8 -*-
"""Test seams. Inert in the product: no module of this package assigns them.

Only the test-only entry point (updater/tests/support/test_worker.py) replaces them, to
stop at named barriers, to substitute the process query's output and to inject a write
fault. The shipped worker exposes no option that reaches them.
"""


class BarrierAbort(Exception):
    """Raised by a test barrier that did not receive its exact release token."""


def _no_barrier(name):
    return None


barrier = _no_barrier

# None: run the real tasklist query. Otherwise a callable returning (returncode, stdout)
# or raising, used in place of the subprocess call.
process_query = None

# None: no fault. Otherwise a Win32 error code reported for candidate writes.
candidate_write_error = None

# None: only official.TRUSTED_KEYS are trusted. Otherwise {key_id: public_key_hex} of TEST keys
# added for qualification; never set by the product.
extra_trusted_keys = None

# None: connect to the real endpoints over HTTPS. Otherwise a callable mapping each https URL to
# the URL actually connected (a local test server); only then is plain http accepted.
network_rewrite = None

# None: the product's network timeout. Otherwise seconds, to qualify the timeout path.
network_timeout = None
