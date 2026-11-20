"""Microsoft Graph provider: OAuth2 client credentials + POST /users/{sender}/sendMail."""
import base64
import logging
import time
from urllib.parse import quote

import requests
from django.core.cache import cache

from .base import EmailMessage, EmailProvider, EmailProviderError

logger = logging.getLogger('email_service')

LOGIN_URL = 'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token'
GRAPH_SEND_URL = 'https://graph.microsoft.com/v1.0/users/{sender}/sendMail'
SCOPE = 'https://graph.microsoft.com/.default'
RETRY_STATUSES = (429, 503)
MAX_BACKOFF_SECONDS = 60


def _error_code(response):
    """Short error code from a Graph/AAD error body; never the raw body (may echo data)."""
    try:
        body = response.json()
    except ValueError:
        return 'unknown'
    err = body.get('error') if isinstance(body, dict) else None
    if isinstance(err, dict):
        return str(err.get('code', 'unknown'))
    return str(err or 'unknown')


class MicrosoftGraphProvider(EmailProvider):
    def __init__(self, config):
        self.config = config
        self._cache_key = f'email_service:graph_token:{config.tenant_id}:{config.client_id}'

    # --- auth -------------------------------------------------------------
    def _get_token(self, force_refresh=False):
        if not force_refresh:
            token = cache.get(self._cache_key)
            if token:
                return token
        cfg = self.config
        try:
            resp = requests.post(
                LOGIN_URL.format(tenant=cfg.tenant_id),
                data={
                    'grant_type': 'client_credentials',
                    'client_id': cfg.client_id,
                    'client_secret': cfg.client_secret,
                    'scope': SCOPE,
                },
                timeout=cfg.timeout,
            )
        except requests.RequestException as exc:
            raise EmailProviderError(f'Token request failed: {type(exc).__name__}')
        if resp.status_code != 200:
            raise EmailProviderError(
                f'Token request rejected (HTTP {resp.status_code}, {_error_code(resp)})'
            )
        token = resp.json().get('access_token')
        if not token:
            raise EmailProviderError('Token response without access_token')
        cache.set(self._cache_key, token, cfg.token_cache_seconds)
        return token

    # --- payload ----------------------------------------------------------
    @staticmethod
    def _recipients(addresses):
        return [{'emailAddress': {'address': a}} for a in addresses]

    def _build_payload(self, message: EmailMessage):
        msg = {
            'subject': message.subject,
            'body': {'contentType': 'HTML', 'content': message.html},
            'toRecipients': self._recipients(message.to),
        }
        if message.cc:
            msg['ccRecipients'] = self._recipients(message.cc)
        if message.bcc:
            msg['bccRecipients'] = self._recipients(message.bcc)
        if message.attachments:
            msg['attachments'] = [
                {
                    '@odata.type': '#microsoft.graph.fileAttachment',
                    'name': a.filename,
                    'contentType': a.content_type,
                    'contentBytes': base64.b64encode(a.content).decode('ascii'),
                }
                for a in message.attachments
            ]
        return {'message': msg, 'saveToSentItems': self.config.save_to_sent_items}

    # --- send -------------------------------------------------------------
    def send(self, message: EmailMessage) -> None:
        cfg = self.config
        url = GRAPH_SEND_URL.format(sender=quote(cfg.sender))
        payload = self._build_payload(message)
        token = self._get_token()
        token_refreshed = False
        attempt = 0
        while True:
            try:
                resp = requests.post(
                    url,
                    json=payload,
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=cfg.timeout,
                )
            except requests.RequestException as exc:
                raise EmailProviderError(f'sendMail request failed: {type(exc).__name__}')

            if resp.status_code == 202:
                return
            if resp.status_code == 401 and not token_refreshed:
                # Cached token may have been revoked/expired early: refresh once.
                token = self._get_token(force_refresh=True)
                token_refreshed = True
                continue
            if resp.status_code in RETRY_STATUSES and attempt < cfg.max_retries:
                wait = self._retry_delay(resp, attempt)
                attempt += 1
                logger.warning(
                    'Graph sendMail HTTP %s, retry %s/%s in %.1fs',
                    resp.status_code, attempt, cfg.max_retries, wait,
                )
                time.sleep(wait)
                continue
            raise EmailProviderError(
                f'sendMail not accepted (HTTP {resp.status_code}, {_error_code(resp)})'
            )

    @staticmethod
    def _retry_delay(response, attempt):
        """Honor Retry-After (seconds) when present; otherwise exponential backoff."""
        header = response.headers.get('Retry-After')
        try:
            wait = float(header) if header is not None else 2 ** attempt
        except ValueError:
            wait = 2 ** attempt
        return max(0.0, min(wait, MAX_BACKOFF_SECONDS))
