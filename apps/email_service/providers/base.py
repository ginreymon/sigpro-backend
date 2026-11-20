"""Provider-agnostic message model and abstract provider interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class EmailProviderError(Exception):
    """Raised by a provider when a message could not be accepted for delivery."""


@dataclass
class EmailAttachment:
    filename: str
    content: bytes
    content_type: str = 'application/octet-stream'


@dataclass
class EmailMessage:
    to: list
    subject: str
    html: str
    cc: list = field(default_factory=list)
    bcc: list = field(default_factory=list)
    attachments: list = field(default_factory=list)


@dataclass
class SendResult:
    success: bool
    error: str = ''


class EmailProvider(ABC):
    """Contract every provider implements; consumers never depend on a concrete one."""

    @abstractmethod
    def send(self, message: EmailMessage) -> None:
        """Send the message. Raise EmailProviderError if it was not accepted."""
