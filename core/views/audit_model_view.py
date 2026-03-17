from .base_model_view import BaseModelViewSet


class AuditModelViewSet(BaseModelViewSet):

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
