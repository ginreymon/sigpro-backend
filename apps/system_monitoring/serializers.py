from rest_framework import serializers


class ClientErrorSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=500)
    url = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    stack = serializers.CharField(max_length=1500, required=False, allow_blank=True, default="")
