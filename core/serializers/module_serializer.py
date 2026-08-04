from rest_framework import serializers
from ..models import Module
from .option_serializer import OptionSerializer


class ModuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Module
        fields = "__all__"


class ModuleWithOptionsSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = "__all__"
