"""Provider registry. To add a provider: implement EmailProvider and register it here."""
from .base import EmailProvider
from .microsoft_graph import MicrosoftGraphProvider

PROVIDERS = {
    'microsoft_graph': MicrosoftGraphProvider,
}


def get_provider(config) -> EmailProvider:
    try:
        provider_cls = PROVIDERS[config.provider]
    except KeyError:
        raise ValueError(f'Unknown EMAIL_PROVIDER: {config.provider!r}')
    return provider_cls(config)
