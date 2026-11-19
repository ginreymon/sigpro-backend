from django.core.checks import Error, Tags, register
from django.urls import get_resolver
from rest_framework.permissions import SAFE_METHODS

from core.permissions import RoleOptionPermission


def _walk(patterns):
    for p in patterns:
        if hasattr(p, "url_patterns"):
            yield from _walk(p.url_patterns)
        elif hasattr(p, "callback"):
            yield p


@register(Tags.urls)
def check_write_endpoints_declare_options(app_configs, **kwargs):
    """Every endpoint that accepts writes under RoleOptionPermission must declare write_options."""
    errors, seen = [], set()
    for p in _walk(get_resolver().url_patterns):
        cb = p.callback
        cls, actions = getattr(cb, "cls", None), getattr(cb, "actions", None)
        if not cls or not actions:
            continue
        perms = getattr(cb, "initkwargs", {}).get("permission_classes", None)
        if perms is None:
            perms = cls.permission_classes
        if RoleOptionPermission not in perms:
            continue
        for method, action in actions.items():
            if method.upper() in SAFE_METHODS or method not in cls.http_method_names:
                continue
            declared = cls.write_options_by_action.get(action, cls.write_options) \
                if hasattr(cls, "write_options_by_action") else getattr(cls, "write_options", ())
            key = (cls, action)
            if not declared and key not in seen:
                seen.add(key)
                errors.append(Error(
                    f"{cls.__name__}.{action} accepts {method.upper()} but declares no write_options.",
                    hint="Set write_options (see core/option_keys.py); otherwise writes are denied.",
                    id="core.E001",
                ))
    return errors
