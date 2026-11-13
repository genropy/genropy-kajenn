# Copyright 2025-2026 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""Contract: the login plan of the benchmarks builds the frame page before logging in.

genropy serves a login call sent before the login only on a page that has
already been built by its ``main`` call. The plan extracted from the capture
must therefore replay that ``main`` call first, then the two login calls, in
the order a browser sends them. A capture without a login has no login plan.
"""

from pathlib import Path

from benchmarks.replay_a1 import build_plan, load_capture

CAPTURE = Path(__file__).resolve().parent.parent / "benchmarks" / "session_capture.jsonl"


def method_names(login_calls):
    return [call["method"].rsplit(";", 1)[-1] for call in login_calls]


def test_login_plan_builds_the_frame_page_before_logging_in():
    login_calls, _pages = build_plan(load_capture(CAPTURE))

    assert method_names(login_calls) == ["main", "login_checkAvatar", "login_doLogin"]


def test_login_plan_main_call_is_the_one_of_the_page_that_logs_in():
    rows = load_capture(CAPTURE)
    first_login = next(
        index for index, row in enumerate(rows)
        if "login" in (row.get("rpc_method") or "").lower()
    )
    page_main = next(
        row["form"] for row in reversed(rows[:first_login])
        if row.get("rpc_method") == "main" and row["path"] == "/"
    )

    login_calls, _pages = build_plan(rows)

    assert login_calls[0] == page_main


def test_capture_without_login_has_no_login_plan():
    rows = [
        row for row in load_capture(CAPTURE)
        if "login" not in (row.get("rpc_method") or "").lower()
    ]

    login_calls, _pages = build_plan(rows)

    assert login_calls == []
