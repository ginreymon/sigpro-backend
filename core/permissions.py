from rest_framework.permissions import SAFE_METHODS, BasePermission
from core.models.option import Option


def user_option_keys(user, request=None) -> frozenset:
    """Active "<module url>/<option url>" keys granted to the user's roles (groups).

    Cached on the request so a call costs one query at most.
    """
    cached = getattr(request, "_option_keys", None) if request is not None else None
    if cached is not None:
        return cached
    rows = Option.objects.filter(
        state=True,
        module__state=True,
        group_options__group__in=user.groups.all(),
    ).values_list("module__url", "url")
    keys = frozenset(f"{m.lower()}/{o.lower()}" for m, o in rows)
    if request is not None:
        request._option_keys = keys
    return keys


def has_option_access(user, option_url: str) -> bool:
    """True if the user's roles grant the option. Accepts "module/option" or a bare option url."""
    keys = user_option_keys(user)
    if "/" in option_url:
        return option_url.lower() in keys
    return any(k.endswith(f"/{option_url.lower()}") for k in keys)


class RoleOptionPermission(BasePermission):
    """Default permission. Writes are denied unless the view declares `write_options`
    and the user's role holds at least one of them. Reads need only authentication,
    unless the view declares `read_options` (any one of them is then required).

    View attributes:
      write_options            tuple of option keys that enable every write action.
      write_options_by_action  optional {action_name: tuple} override per action.
      read_options             tuple of option keys required to read (default () = open).
      read_options_by_action   optional {action_name: tuple} override per action.
    """

    message = "No tiene permisos para realizar esta acción."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        action = getattr(view, "action", None)
        if request.method in SAFE_METHODS:
            required = getattr(view, "read_options_by_action", {}).get(
                action, getattr(view, "read_options", ())
            )
            if not required:
                return True  # reads are open by default
        else:
            required = getattr(view, "write_options_by_action", {}).get(
                action, getattr(view, "write_options", ())
            )
            if not required:
                return False  # writes are denied by default
        return not user_option_keys(request.user, request).isdisjoint(required)


# Kept as an alias for views that still use the previous name.
OptionWritePermission = RoleOptionPermission
