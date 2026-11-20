"""Public entry point: ``send_email(...)``. Usable from any module; never raises."""
import logging

from ..config import get_email_config
from ..providers import get_provider
from ..providers.base import EmailAttachment, EmailMessage, SendResult
from .template_renderer import render_template

logger = logging.getLogger('email_service')


def _as_list(value):
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def _as_attachment(item):
    """Accept EmailAttachment or a (filename, bytes[, content_type]) tuple."""
    if isinstance(item, EmailAttachment):
        return item
    return EmailAttachment(*item)


def send_email(to, subject, template=None, context=None, html=None,
               cc=None, bcc=None, attachments=None) -> SendResult:
    """Send an email through the configured provider.

    Provide either ``template`` (name under templates/emails/, rendered with
    ``context``) or raw ``html``. Returns SendResult; a disabled/unconfigured
    service or a provider failure yields ``success=False`` instead of raising,
    so callers' business flows are never broken by email problems.
    """
    config = get_email_config()
    if not config.enabled:
        logger.info('Email service disabled; message not sent')
        return SendResult(False, 'Email service disabled')
    missing = config.missing()
    if missing:
        logger.warning('Email service not configured; missing: %s', ', '.join(missing))
        return SendResult(False, 'Email service not configured')

    try:
        to_list = _as_list(to)
        if not to_list:
            raise ValueError('At least one recipient is required')
        if template:
            body = render_template(template, context)
        elif html is not None:
            body = html
        else:
            raise ValueError('Either template or html is required')
        message = EmailMessage(
            to=to_list,
            subject=subject,
            html=body,
            cc=_as_list(cc),
            bcc=_as_list(bcc),
            attachments=[_as_attachment(a) for a in (attachments or [])],
        )
        get_provider(config).send(message)
    except Exception as exc:  # noqa: BLE001 - email must not break the caller
        logger.error('Email not sent (%s): %s', type(exc).__name__, exc)
        return SendResult(False, str(exc))

    logger.info('Email accepted by %s for %s recipient(s)', config.provider, len(message.to))
    return SendResult(True)
