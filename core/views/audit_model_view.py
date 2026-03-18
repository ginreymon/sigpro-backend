from .base_model_view import BaseModelViewSet


class AuditModelViewSet(BaseModelViewSet):

    def perform_create(self, serializer):
        extra = {}

        if hasattr(serializer.Meta.model, "created_by"):
            extra["created_by"] = self.request.user

        if hasattr(serializer.Meta.model, "updated_by"):
            extra["updated_by"] = self.request.user

        serializer.save(**extra)

    def perform_update(self, serializer):
        extra = {}

        if hasattr(serializer.Meta.model, "updated_by"):
            extra["updated_by"] = self.request.user

        serializer.save(**extra)
