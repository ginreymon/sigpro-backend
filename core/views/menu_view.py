from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch
from core.models import Module, Option

class MenuViewSet(viewsets.ViewSet):

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated], url_path="menu")
    def get_menu(self, request):

        user = request.user
        user_groups = user.groups.all()

        allowed_options = (
            Option.objects.filter(group_options__group__in=user_groups, state=True)
            .select_related("module")
            .distinct()
        )

        modules = (
            Module.objects.filter(options__in=allowed_options, state=True)
            .distinct()
            .prefetch_related(Prefetch("options", queryset=allowed_options))
        )

        menu = []

        for module in modules:
            module_data = {
                "id": module.id,
                "name": str.capitalize(module.name),
                "url": str.lower(module.url),
                "options": [],
            }

            for option in module.options.all():
                module_data["options"].append(
                    {
                        "id": option.id,
                        "name": str.capitalize(option.name),
                        "title": str.capitalize(option.title),
                        "url": str.lower(option.url),
                    }
                )

            menu.append(module_data)

        return Response(menu, status=status.HTTP_200_OK)
