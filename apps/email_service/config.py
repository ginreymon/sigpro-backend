"""Centralized email service configuration, read from Django settings (env-backed)."""
from dataclasses import dataclass

from django.conf import settings

DEFAULT_PROVIDER = 'microsoft_graph'

# Settings every provider needs, keyed by provider name. Extend when adding providers.
REQUIRED_SETTINGS = {
    'microsoft_graph': (
        'MICROSOFT_TENANT_ID',
        'MICROSOFT_CLIENT_ID',
        'MICROSOFT_CLIENT_SECRET',
        'MICROSOFT_SENDER_EMAIL',
    ),
}


@dataclass(frozen=True)
class EmailConfig:
    enabled: bool
    provider: str
    tenant_id: str
    client_id: str
    client_secret: str
    sender: str
    timeout: int
    token_cache_seconds: int
    save_to_sent_items: bool
    max_retries: int

    def missing(self):
        """Names of required settings that are empty for the selected provider."""
        names = REQUIRED_SETTINGS.get(self.provider, ())
        return [n for n in names if not getattr(settings, n, '')]

    def is_ready(self):
        return self.enabled and not self.missing()

    def __repr__(self):  # never leak the secret in logs/tracebacks
        return f'EmailConfig(enabled={self.enabled}, provider={self.provider!r}, sender={self.sender!r})'


def get_email_config():
    """Build the config on demand so settings overrides apply and startup never fails."""
    return EmailConfig(
        enabled=bool(getattr(settings, 'EMAIL_SERVICE_ENABLED', False)),
        provider=getattr(settings, 'EMAIL_PROVIDER', DEFAULT_PROVIDER) or DEFAULT_PROVIDER,
        tenant_id=getattr(settings, 'MICROSOFT_TENANT_ID', ''),
        client_id=getattr(settings, 'MICROSOFT_CLIENT_ID', ''),
        client_secret=getattr(settings, 'MICROSOFT_CLIENT_SECRET', ''),
        sender=getattr(settings, 'MICROSOFT_SENDER_EMAIL', ''),
        timeout=int(getattr(settings, 'EMAIL_TIMEOUT', 15)),
        token_cache_seconds=int(getattr(settings, 'EMAIL_TOKEN_CACHE_SECONDS', 3300)),
        save_to_sent_items=bool(getattr(settings, 'EMAIL_SAVE_TO_SENT_ITEMS', True)),
        max_retries=int(getattr(settings, 'EMAIL_MAX_RETRIES', 3)),
    )
