from datetime import timedelta
from core.views.base_model_view import BaseModelViewSet
from apps.production.models import WorkBreak
from apps.production.serializers import WorkBreakSerializer
from django.db import models  # type: ignore


class WorkBreakViewSet(BaseModelViewSet):
    queryset = WorkBreak.objects.all()
    serializer_class = WorkBreakSerializer

    def get_queryset(self):
        qs = WorkBreak.objects.all()
        search = self.request.GET.get("search")
        if search:
            try:
                h, m, s = map(int, search.split(":"))
                duration_td = timedelta(hours=h, minutes=m, seconds=s)
                qs = qs.filter(duration=duration_td)
            except ValueError:
                qs = qs.filter(
                    models.Q(name__icontains=search)
                    | models.Q(description__icontains=search)
                )
        return qs
