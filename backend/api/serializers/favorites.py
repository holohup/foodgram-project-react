from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.serializers.fields import Base64ImageField
from recipes.models import Favorite, Recipe
from users.models import User


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for the Favorite model."""

    name = serializers.CharField(source='recipe.name', read_only=True)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time', read_only=True
    )
    image = Base64ImageField(source='recipe.image', read_only=True)
    id = serializers.IntegerField(source='recipe.id', read_only=True)
    user = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=User.objects.all()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=Recipe.objects.all()
    )

    class Meta:
        model = Favorite
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
            'user',
            'recipe',
        )
        validators = (
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='You have already favorited this recipe.',
            ),
        )
