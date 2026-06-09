"""Email dispatch seam (C-03 §1).

`dispatch_email` is the seam. The default implementation is the in-memory
collector; a real SMTP/sendgrid adapter plugs in by calling `set_email_sender`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    body: str


class EmailSender(Protocol):
    async def send(self, message: EmailMessage) -> None: ...


class InMemoryEmailCollector:
    """Test sender. Captures every dispatch for assertion."""

    def __init__(self) -> None:
        self.messages: list[EmailMessage] = []

    async def send(self, message: EmailMessage) -> None:
        self.messages.append(message)

    def reset(self) -> None:
        self.messages = []


_sender: EmailSender = InMemoryEmailCollector()


def get_email_sender() -> EmailSender:
    return _sender


def set_email_sender(sender: EmailSender) -> None:
    global _sender
    _sender = sender


async def dispatch_email(to: str, subject: str, body: str) -> None:
    await _sender.send(EmailMessage(to=to, subject=subject, body=body))
