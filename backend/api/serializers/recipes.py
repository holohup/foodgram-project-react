from django.db import transaction
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from api.serializers.fields import Base64ImageField, TagRelatedField
from api.serializers.recipeingredients import RecipeIngredientSerializer
from api.serializers.users import CustomUserSerializer
from recipes.models import Recipe, RecipeIngredient, Tag


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for the Recipe model."""

    tags = TagRelatedField(many=True, queryset=Tag.objects.all())
    image = Base64ImageField(allow_null=False)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipeingredients'
    )
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False
    )
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'text',
            'image',
            'tags',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'cooking_time',
        )

    def __init__(self, instance=None, **kwargs):
        """Initialization with needed variables."""

        self._tags = None
        self._ingredients = None
        super().__init__(instance, **kwargs)

    def validate_tags(self, data):
        """Tags validation."""

        if not data:
            raise ValidationError('Tags list cannot be empty.')
        return data

    def validate_ingredients(self, data):
        """Tags validation."""

        if not data:
            raise ValidationError('Ingredients list cannot be empty.')
        return data

    def _stash_data(self, data):
        """Save data that needs manual deserializing."""

        self._tags = data.pop('tags')
        self._ingredients = data.pop('recipeingredients')

    def _apply_data(self, recipe):
        """Extra fields processing."""

        recipe.tags.set(self._tags)
        recipe_ingredients = [
            RecipeIngredient(
                ingredient_id=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount'],
            )
            for ingredient in self._ingredients
        ]
        with transaction.atomic():
            recipe.recipeingredients.all().delete()
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def update(self, instance, validated_data):
        """An upgraded update method."""

        self._stash_data(validated_data)
        super().update(instance, validated_data)
        self._apply_data(instance)
        return instance

    def create(self, validated_data):
        """An upgraded create method."""

        self._stash_data(validated_data)
        recipe = Recipe.objects.create(**validated_data)
        self._apply_data(recipe)
        return recipe


class RecipeMiniSerializer(serializers.ModelSerializer):
    """Mini-version of recipe serializer for some views."""

    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = ('id', 'name', 'image', 'cooking_time')
