"""Strict TDD for app.integrations.email (C-03 §1, integration seam).

Spec contract:
- `dispatch_email(to, subject, body)` is the seam; it is async, but C-03 never
  uses a real SMTP server.
- `InMemoryEmailCollector` is the default in-test implementation; it captures
  every dispatch in a list and is observable from tests.
- `reset()` clears the collector.
"""

from __future__ import annotations

import pytest

from app.integrations import email as email_mod
from app.integrations.email import (
    InMemoryEmailCollector,
    dispatch_email,
    get_email_sender,
    set_email_sender,
)

pytestmark = pytest.mark.no_db


@pytest.fixture
def collector() -> InMemoryEmailCollector:
    coll = InMemoryEmailCollector()
    set_email_sender(coll)
    return coll


def test_default_sender_is_in_memory_collector() -> None:
    assert isinstance(get_email_sender(), InMemoryEmailCollector)


def test_dispatch_appends_message(collector: InMemoryEmailCollector) -> None:
    import asyncio

    asyncio.run(dispatch_email("a@b.com", "Welcome", "Hello"))
    assert len(collector.messages) == 1
    msg = collector.messages[0]
    assert msg.to == "a@b.com"
    assert msg.subject == "Welcome"
    assert msg.body == "Hello"


def test_collector_reset_clears_messages(collector: InMemoryEmailCollector) -> None:
    import asyncio

    asyncio.run(dispatch_email("a@b.com", "s", "b"))
    collector.reset()
    assert collector.messages == []


def test_set_email_sender_overrides_default() -> None:
    class _Sink:
        def __init__(self) -> None:
            self.messages: list[email_mod.EmailMessage] = []

        async def send(self, msg: email_mod.EmailMessage) -> None:
            self.messages.append(msg)

    sink = _Sink()
    set_email_sender(sink)  # type: ignore[arg-type]
    import asyncio

    asyncio.run(dispatch_email("x@y.com", "s2", "b2"))
    assert len(sink.messages) == 1
    set_email_sender(InMemoryEmailCollector())  # restore default
