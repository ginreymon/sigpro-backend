"""Render Django email templates located in ``email_service/templates/emails/``."""
from django.template.loader import render_to_string

TEMPLATE_DIR = 'emails'


def render_template(name, context=None):
    """Render ``emails/<name>`` (".html" appended if missing) to an HTML string."""
    if not name.endswith('.html'):
        name += '.html'
    return render_to_string(f'{TEMPLATE_DIR}/{name}', context or {})
