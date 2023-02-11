from rest_framework import serializers

from recipes.models import Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for the Tag model."""

    class Meta:
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )
        model = Tag
        read_only_fields = fields
