from rest_framework import serializers


class OPTypeDocumentsSerializer(serializers.Serializer):
    doc_type = serializers.CharField(source="Tipo_Doc")
