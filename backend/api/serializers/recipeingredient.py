from rest_framework import serializers
from rest_framework.serializers import ValidationError

from recipes.models import Ingredient, RecipeIngredient


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Serializer for the RecipeIngredient model."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all().values_list('id', flat=True)
    )
    name = serializers.StringRelatedField(
        read_only=True, source='ingredient.name'
    )
    measurement_unit = serializers.StringRelatedField(
        read_only=True, source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError('Amount should be a positive number.')
        return value

    def to_representation(self, instance):
        instance.id = instance.ingredient.id
        return super().to_representation(instance)
