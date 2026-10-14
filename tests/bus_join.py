# Copyright 2026 Softwell S.r.l.
# Licensed under the Apache License, Version 2.0

"""How a test lane joins a worker to its group's bus, without genropy.

``tests/lane.py`` imports genropy at module level and ``tests/test_delivery_desk.py``
must run without it: both join their worker through this module.
"""

from typing import Any

import kbus


async def join_bus(worker: Any, url: str) -> None:
    """Join a worker to its group's bus, as orchestra does: name, token and address from its URL."""
    scheme, _, rest = url.partition("://")
    credentials, _, location = rest.partition("@")
    name, _, token = credentials.partition(":")
    member = kbus.Member(name, secret=token, handler=worker.serve_call)
    worker.attach_member(member)
    await member.connect(f"{scheme}://{location}")
