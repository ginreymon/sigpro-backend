from rest_framework.permissions import SAFE_METHODS, BasePermission
from core.models.option import Option


def has_option_access(user, option_url: str) -> bool:
    """Same rule as AuthViewSet.has_access: an active option/module granted to one of the user's groups."""
    return Option.objects.filter(
        url=option_url,
        state=True,
        module__state=True,
        group_options__group__in=user.groups.all(),
    ).exists()


class OptionWritePermission(BasePermission):
    """Reads need only authentication; writes need the view's `option_url` menu option."""

    message = "No tiene permisos para realizar esta acción."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return has_option_access(request.user, view.option_url)
