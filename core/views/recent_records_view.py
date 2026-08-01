from rest_framework.decorators import action
from rest_framework.response import Response


class RecentRecordsMixin:
    """Adds a `recent/` action returning the current user's last N records
    of this viewset's model, ordered by -updated_at.

    Subclasses must set `recent_records_user_filter` to the lookup path from
    the model to the user (e.g. 'work_session_activity__work_session__user').
    """

    recent_records_limit = 3
    recent_records_user_filter: str | None = None
    recent_records_select_related: tuple = ()

    @action(detail=False, methods=['get'], url_path='recent')
    def recent(self, request):
        queryset = self.get_queryset().filter(**{
            self.recent_records_user_filter: request.user,
        })

        if self.recent_records_select_related:
            queryset = queryset.select_related(*self.recent_records_select_related)

        records = queryset.order_by('-updated_at')[:self.recent_records_limit]
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)
