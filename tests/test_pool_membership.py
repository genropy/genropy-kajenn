# Copyright 2026 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""A worker is a pool member exactly when it has joined its group's bus.

kajenn-orchestra 0.5.0 joins a worker as a ``kbus.Member``: the live lane joins
it the way orchestra's own lanes do, and the register client's commit gate
reads ``pool_member`` to decide whether it may answer from its own cache.
"""

import importlib.util

import pytest

_HAS_GNR = importlib.util.find_spec("gnr") is not None

pytestmark = pytest.mark.skipif(not _HAS_GNR, reason="genropy not installed")


def test_a_worker_joined_to_the_pool_is_a_pool_member(site_lane):
    assert site_lane.worker.pool_member is True
