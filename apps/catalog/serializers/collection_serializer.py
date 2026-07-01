from rest_framework import serializers
from apps.catalog.models.collection import Collection


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ['id', 'rowid', 'name']
