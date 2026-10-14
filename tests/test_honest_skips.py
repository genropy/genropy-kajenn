# Copyright 2026 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""A live test skips only for a recognised missing prerequisite.

The recognised prerequisites are: genropy not installed, a database driver not
installed, an opt-in environment variable not set (``BENCH_*``, ``GNR_BENCH_*``,
``GNR_WSX_TEST_URL``), and an installed genropy without ``websocketHandlerClass``.
Any other error while a site, a lane or a pool starts fails the test.
"""

from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_LIVE_TEST = "def test_live(lane):\n    assert lane.worker\n"


def run_suite(pytester, monkeypatch, conftest):
    """Run a one-test suite on the session's ``lane`` fixture in a child pytest."""
    monkeypatch.setenv("PYTHONPATH", str(_REPO))
    pytester.makeconftest(conftest)
    pytester.makepyfile(test_live=_LIVE_TEST)
    return pytester.runpytest_subprocess("-rs", "-p", "no:cacheprovider")


def test_a_lane_whose_site_cannot_be_built_fails_instead_of_skipping(pytester, monkeypatch):
    # wf:contract: a suite whose lane fixture starts a site name that does not
    # wf:contract: exist reports that test as failed (or errored), never skipped
    result = run_suite(pytester, monkeypatch, """
import tests.conftest as suite
from tests.conftest import lane, site_lane  # noqa: F401

suite.SITE = "no_such_site"
""")
    outcomes = result.parseoutcomes()
    assert outcomes.get("failed", 0) + outcomes.get("errors", 0) == 1
    assert "skipped" not in outcomes
    result.stdout.fnmatch_lines(["*site no_such_site not found*"])


def test_a_missing_genropy_still_skips(pytester, monkeypatch):
    # wf:contract: a suite run where genropy cannot be imported reports the live
    # wf:contract: tests as skipped with the reason "genropy not installed"
    result = run_suite(pytester, monkeypatch, """
import sys

sys.modules["gnr"] = None
from tests.conftest import lane, site_lane  # noqa: E402, F401
""")
    result.assert_outcomes(skipped=1)
    result.stdout.fnmatch_lines(["*genropy not installed*"])
