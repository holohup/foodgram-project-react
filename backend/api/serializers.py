import base64
import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=str(datetime.datetime.now().timestamp()) + '.' + ext,
            )
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'color', 'slug', 'id')
        model = Tag

    def to_internal_value(self, data):
        return Tag.objects.get(id=data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('measurement_unit', 'id', 'name')
        model = Ingredient


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', required=False)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', required=False
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeMiniSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = ('id', 'name', 'cooking_time')

    def get_image(self, favorite):
        request = self.context['request']
        return request.build_absolute_uri(favorite.image.url)


class FavoriteSerializer(serializers.ModelSerializer):

    name = serializers.CharField(source='recipe.name', read_only=True)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time', read_only=True
    )
    image = serializers.SerializerMethodField()
    user_id = serializers.CharField(write_only=True)
    recipe_id = serializers.CharField(write_only=True)

    def get_image(self, favorite):
        request = self.context['request']
        return request.build_absolute_uri(favorite.recipe.image.url)

    class Meta:
        model = Favorite
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
            'user_id',
            'recipe_id',
        )

    def validate(self, data):
        recipe = Recipe.objects.get(id=data['recipe_id'])
        user = User.objects.get(id=data['user_id'])
        if not Favorite.objects.filter(user=user, recipe=recipe):
            return data
        raise ValidationError('This favorite already exists.')


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
        )


class CustomUserSubscriptionsSerializer(CustomUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = CustomUserSerializer.Meta.fields + ('is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user
        return (
            user.is_authenticated
            and Subscription.objects.filter(author=obj, user=user).exists()
        )


class SubscriptionSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(source='author.email', read_only=True)
    id = serializers.IntegerField(source='author.id', read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    recipes = serializers.SerializerMethodField()
    first_name = serializers.CharField(
        source='author.first_name', read_only=True
    )
    last_name = serializers.CharField(
        source='author.last_name', read_only=True
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'user',
            'author',
        )

        extra_kwargs = {
            'user': {'write_only': True},
            'author': {'write_only': True},
        }
        model = Subscription
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author'],
                message='You can only subscribe once.',
            )
        ]

    def validate_author(self, value):
        if self.context['user'] == value:
            raise serializers.ValidationError('Say no to self-subscriptions.')
        return value

    def get_recipes_count(self, subscription):
        return Recipe.objects.filter(author=subscription.author).count()

    def get_recipes(self, subscription):
        recipes_limit = int(
            self.context['request'].query_params.get('recipes_limit')
            or settings.DEFAULT_RECIPES_LIMIT
        )
        serializer = RecipeMiniSerializer(
            many=True,
            instance=Recipe.objects.filter(
                author=subscription.author
            ).order_by('-pub_date')[:recipes_limit],
            context=self.context,
        )
        return serializer.data

    def get_is_subscribed(self, subscription):
        return Subscription.objects.filter(
            user=self.context['user'], author=subscription.author
        ).exists()


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    image = Base64ImageField(required=True, allow_null=False)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipeingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = CustomUserSubscriptionsSerializer(read_only=True, required=False)

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
        self._tags = None
        self._ingredients = None
        super().__init__(instance, **kwargs)

    def get_is_favorited(self, recipe):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and Favorite.objects.filter(user=user, recipe=recipe).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and ShoppingCart.objects.filter(user=user, recipe=recipe).exists()
        )

    def validate_ingredients(self, data):
        errors = []
        for ingredient in data:
            id = ingredient['ingredient']['id']
            if not Ingredient.objects.filter(id=id).exists():
                errors.append(
                    ValidationError(f'Ingredient {id} not found').detail
                )
            if ingredient['amount'] <= 0:
                errors.append(
                    ValidationError(
                        f'Amount of Ingredient {id} should be'
                        ' a positive number.'
                    ).detail
                )
        if errors:
            raise ValidationError(errors)
        return data

    def _stash_data(self, validated_data):
        self._tags = validated_data.pop('tags')
        self._ingredients = validated_data.pop('recipeingredients')

    def _apply_data(self, recipe):
        recipe.tags.set(self._tags)
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        for ingredient in self._ingredients:
            RecipeIngredient.objects.create(
                ingredient=Ingredient.objects.get(
                    id=ingredient['ingredient']['id']
                ),
                recipe=recipe,
                amount=ingredient['amount'],
            )

    def update(self, instance, validated_data):
        self._stash_data(validated_data)
        super().update(instance, validated_data)
        self._apply_data(instance)
        return instance

    def create(self, validated_data):
        self._stash_data(validated_data)
        recipe = Recipe.objects.create(**validated_data)
        self._apply_data(recipe)
        return recipe
