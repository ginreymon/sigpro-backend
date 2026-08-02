from django.db.models import Max
from rest_framework.decorators import action
from rest_framework.response import Response


class RecentRecordsMixin:
    """Adds a `recent/` action returning the current user's last N records
    of this viewset's model, ordered by -updated_at.

    Subclasses must set `recent_records_user_filter` to the lookup path from
    the model to the user (e.g. 'work_session_activity__work_session__user').

    If `recent_records_dedup_field` is set (e.g. 'op_rowid'), records are
    deduplicated by that field first — the last N *distinct* values, each
    represented by its most recently updated record — instead of the last N
    raw rows (which could all belong to the same OP).
    """

    recent_records_limit = 3
    recent_records_user_filter: str | None = None
    recent_records_select_related: tuple = ()
    recent_records_dedup_field: str | None = None

    @action(detail=False, methods=['get'], url_path='recent')
    def recent(self, request):
        queryset = self.get_queryset().filter(**{
            self.recent_records_user_filter: request.user,
        })

        if self.recent_records_select_related:
            queryset = queryset.select_related(*self.recent_records_select_related)

        if self.recent_records_dedup_field:
            records = self._recent_distinct(queryset)
        else:
            records = list(queryset.order_by('-updated_at')[:self.recent_records_limit])

        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)

    def _recent_distinct(self, queryset):
        field = self.recent_records_dedup_field

        latest_per_key = (
            queryset
            .exclude(**{f'{field}__isnull': True})
            .values(field)
            .annotate(latest=Max('updated_at'))
            .order_by('-latest')[:self.recent_records_limit]
        )
        keys = [row[field] for row in latest_per_key]
        if not keys:
            return []

        rows = queryset.filter(**{f'{field}__in': keys}).order_by('-updated_at')

        seen = set()
        records = []
        for row in rows:
            key = getattr(row, field)
            if key in seen:
                continue
            seen.add(key)
            records.append(row)
            if len(records) >= self.recent_records_limit:
                break
        return records
