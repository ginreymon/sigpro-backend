# apps/email_service

Centralized, provider-agnostic email sending for SIGPRO. Current provider: **Microsoft Graph** (OAuth2 client credentials). No SMTP. No models, migrations, views or URLs.

## Architecture

```
apps/email_service/
  config.py                      # EmailConfig from Django settings (get_email_config)
  providers/
    base.py                      # EmailProvider ABC, EmailMessage, EmailAttachment, SendResult
    microsoft_graph.py           # token (cached) + POST /v1.0/users/{sender}/sendMail
    __init__.py                  # PROVIDERS registry + get_provider()
  services/
    email_sender.py              # send_email()  <- the only thing consumers import
    template_renderer.py         # render_template()
  templates/emails/              # base.html + one template per purpose
```

Consumers depend only on `send_email`. To add a provider (or another auth method), implement `EmailProvider`, add it to `PROVIDERS`, add its required settings to `config.REQUIRED_SETTINGS`, and set `EMAIL_PROVIDER`. No consumer changes.

`send_email` never raises: it returns `SendResult(success, error)`. If the service is disabled or unconfigured it logs and returns `success=False`; SIGPRO always starts.

## Configuration (`.env`)

| Variable | Default | Notes |
|---|---|---|
| `EMAIL_SERVICE_ENABLED` | `False` | Master switch |
| `EMAIL_PROVIDER` | `microsoft_graph` | Key in `PROVIDERS` |
| `MICROSOFT_TENANT_ID` | – | Directory (tenant) ID |
| `MICROSOFT_CLIENT_ID` | – | App registration client ID |
| `MICROSOFT_CLIENT_SECRET` | – | Secret **value** (never commit/log) |
| `MICROSOFT_SENDER_EMAIL` | – | Mailbox that sends (UPN/email) |
| `EMAIL_TIMEOUT` | `15` | Seconds per HTTP call |
| `EMAIL_TOKEN_CACHE_SECONDS` | `3300` | 55 min (tokens last ~60) |
| `EMAIL_SAVE_TO_SENT_ITEMS` | `True` | Save copy in sender's Sent Items |
| `EMAIL_MAX_RETRIES` | `3` | Retries for HTTP 429/503 (honors `Retry-After`, else exponential backoff, max 60 s) |

The token is cached with Django's cache (default local-memory: one token per worker process). Only HTTP **202** counts as accepted. A 401 triggers one token refresh. Tokens and secrets are never logged.

## Azure setup

1. Entra ID → App registrations → New registration (single tenant). Copy *Directory (tenant) ID* and *Application (client) ID*.
2. Certificates & secrets → New client secret → copy the **Value** immediately.
3. API permissions → Add → Microsoft Graph → **Application permissions** → `Mail.Send` → **Grant admin consent**.
4. Recommended: restrict the app to the sender mailbox only with an Exchange Online *Application Access Policy* (`New-ApplicationAccessPolicy -AccessRight RestrictAccess ...`), otherwise `Mail.Send` allows sending as any mailbox.
5. The sender mailbox must exist (licensed or shared mailbox). Set the variables above and `EMAIL_SERVICE_ENABLED=True`.

## Usage

```python
from apps.email_service.services.email_sender import send_email

result = send_email(
    to=['user@example.com', 'other@example.com'],   # str or list
    subject='Welcome',
    template='welcome',                              # templates/emails/welcome.html
    context={'user_name': 'Ana', 'username': 'ana', 'login_url': 'https://...'},
    cc=['boss@example.com'],
    bcc=None,
)
if not result.success:
    ...  # result.error; the caller decides (usually just continue)
```

Raw HTML instead of a template: `send_email(to, subject, html='<p>Hi</p>')`.

### Dynamic / per-user context
Everything in `context` is available in the template (`{{ user_name }}`, loops, `{% if %}`). Build the context per recipient and call `send_email` once per user for personalized messages. Django autoescapes values.

### Attachments
Tuples `(filename, bytes[, content_type])` or `EmailAttachment`:

```python
from apps.email_service.providers.base import EmailAttachment
send_email(to, 'Report', template='notification',
           context={'title': 'Report', 'message': 'Attached.'},
           attachments=[('report.pdf', pdf_bytes, 'application/pdf'),
                        EmailAttachment('data.xlsx', xlsx_bytes)])
```
Graph's `sendMail` accepts file attachments up to ~3 MB each inline (4 MB total request); larger files need upload sessions (not implemented).

## Creating a template

1. Create `templates/emails/<purpose>.html`.
2. Start with `{% extends "emails/base.html" %}` and override `title`, `header`, `content`, `footer` blocks.
3. Use **inline styles** and table layout only (email clients ignore `<style>`/flex/grid). Document the expected context in a `{% comment %}`.
4. Use it with `template='<purpose>'`. No registration needed: the app is in `INSTALLED_APPS` with `APP_DIRS=True`, so Django finds it by name.

Included examples: `notification.html` (generic notice with optional detail table and button), `welcome.html` (per-user greeting).
