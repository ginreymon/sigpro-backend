from rest_framework import viewsets, status
from rest_framework.response import Response


class LocalBaseModelViewSet(viewsets.ModelViewSet):

    editable_fields = ["is_active"]

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(qs.model, "is_deleted") and hasattr(qs.model, "is_active"):
            qs = qs.filter(is_deleted=False, is_active=True)
        return qs

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if hasattr(instance, "soft_delete"):
            instance.soft_delete()
        else:
            instance.delete()
        return Response(
            {"message": f"{instance} marked as deleted"},
            status=status.HTTP_200_OK,
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = {
            field: request.data.get(field, getattr(instance, field))
            for field in self.editable_fields
        }
        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = {
            field: request.data.get(field, getattr(instance, field))
            for field in self.editable_fields
        }
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
