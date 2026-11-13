# Copyright 2025-2026 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""Contract: the scaling probe reads the pool from the inspector census.

The probe needs two things after every login: the workers a user can be sent
to, each with its state and the number of users living on it, and how many
workers the pool tracks in all. A tracked worker that is not yet routable is a
spawn in flight, and the probe waits for it before the next login. The census
below has the shape ``/_server/inspector/census`` answers: one entry, under the
code of the SPA front.
"""

from benchmarks.scaling_probe import pool_from_census


def census(groups):
    return {"site": {"groups": groups}}


def group(living_workers, workers, user_worker_map):
    return {
        "living_workers": living_workers,
        "workers": {name: {"state": state} for name, state in workers.items()},
        "user_worker_map": user_worker_map,
    }


def test_the_routable_workers_are_the_living_ones_of_every_group():
    pool = census({
        "base": group(["base_0001"], {"base_0001": "running"}, {"alice": "base_0001"}),
        "experimental": group(
            ["experimental_0001"], {"experimental_0001": "running"}, {"bob": "experimental_0001"}
        ),
    })

    workers, tracked = pool_from_census(pool)

    assert workers == [("base_0001", "running", 1), ("experimental_0001", "running", 1)]
    assert tracked == 2


def test_a_worker_still_booting_is_tracked_and_not_routable():
    pool = census({
        "base": group(
            ["base_0001"],
            {"base_0001": "running", "base_0002": "starting"},
            {"alice": "base_0001"},
        ),
    })

    workers, tracked = pool_from_census(pool)

    assert [name for name, _state, _users in workers] == ["base_0001"]
    assert tracked == 2


def test_users_are_counted_on_the_worker_they_live_on():
    pool = census({
        "base": group(
            ["base_0001", "base_0002"],
            {"base_0001": "running", "base_0002": "running"},
            {"alice": "base_0001", "bob": "base_0001", "carol": "base_0002", "dave": None},
        ),
    })

    workers, _tracked = pool_from_census(pool)

    assert workers == [("base_0001", "running", 2), ("base_0002", "running", 1)]
