from rest_framework import serializers
from rest_framework.serializers import ValidationError

from api.serializers.recipe import RecipeMiniSerializer
from recipes.models import ShoppingCart


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Serializer for the ShoppingCart model."""

    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user')

    def validate(self, data):
        """Isn't this recipe already in a shopping cart?"""

        if not ShoppingCart.objects.filter(
            user=data['user'], recipe=data['recipe']
        ).exists():
            return data
        raise ValidationError('This recipe is already in the shopping cart.')

    def to_representation(self, instance):
        """Let's serialize the cart object as requested."""

        return RecipeMiniSerializer(
            instance=instance.recipe, context=self.context
        ).data
