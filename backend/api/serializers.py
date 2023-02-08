import base64
import datetime

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription, User


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

    def to_representation(self, value):
        return self.context['request'].build_absolute_uri(value.url)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )
        model = Tag
        read_only_fields = fields


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient
        read_only_fields = fields


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('name', 'measurement_unit', 'id')


class RecipeMiniSerializer(serializers.ModelSerializer):
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


class FavoriteSerializer(serializers.ModelSerializer):

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


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=150)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomUserSubscriptionsSerializer(CustomUserSerializer):
    is_subscribed = serializers.BooleanField(default=False, read_only=True)

    class Meta:
        model = User
        fields = CustomUserSerializer.Meta.fields + ('is_subscribed',)
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(source='author.email', read_only=True)
    id = serializers.IntegerField(source='author.id', read_only=True)
    recipes_count = serializers.SerializerMethodField()
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
        read_only_fields = ('recipes_count',)

        extra_kwargs = {
            'user': {'write_only': True},
            'author': {'write_only': True},
        }
        model = Subscription
        validators = (
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='You can only subscribe once.',
            ),
        )

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
    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField(allow_null=False)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipeingredients', read_only=True
    )
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False
    )
    author = CustomUserSubscriptionsSerializer(read_only=True)

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

    def validate_tags(self, data):
        if not isinstance(data, list):
            raise ValidationError(
                {'Tags must be an list integer id\'s.': data}
            )
        if not data:
            raise ValidationError({'Tags list cannot be empty.': data})

        for tag_id in data:
            if not isinstance(tag_id, int):
                raise ValidationError({'Tag must be an integer (id)': data})
            if not Tag.objects.filter(id=tag_id).exists():
                raise ValidationError({'Tag not found.': data})

        return data

    def validate_ingredients(self, data):
        if not data:
            raise ValidationError(
                {'Recipe ingredients cannot be empty.': data}
            )
        for ingredient in data:
            id_ = ingredient['id']
            if not Ingredient.objects.filter(id=id_).exists():
                raise ValidationError({'Ingredient not found': id})
            if int(ingredient['amount']) <= 0:
                raise ValidationError(
                    {'Amount of an Ingredient should be positive.': id_}
                )
        return data

    def to_internal_value(self, data):
        self._tags = self.validate_tags(data.get('tags'))
        self._ingredients = self.validate_ingredients(data.get('ingredients'))
        return super().to_internal_value(data)

    def _apply_data(self, recipe):
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
            RecipeIngredient.objects.filter(recipe=recipe).delete()
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def update(self, instance, validated_data):
        super().update(instance, validated_data)
        self._apply_data(instance)
        return instance

    def create(self, validated_data):
        recipe = Recipe.objects.create(**validated_data)
        self._apply_data(recipe)
        return recipe


class PasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=150, write_only=True)
    current_password = serializers.CharField(max_length=150, write_only=True)

    def create(self, validated_data):
        user = self.context['request'].user
        user.set_password(validated_data['new_password'])
        user.save()
        return user

    def validate_current_password(self, value):
        if self.context['request'].user.check_password(value):
            return value
        raise ValidationError('Invalid current password.')

    def validate_new_password(self, value):
        if not validate_password(value):
            return value
        raise ValidationError('Could not validate password')

    def validate(self, data):
        if data['new_password'] == data['current_password']:
            raise ValidationError('Cannot change password to the same value.')
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user')

    def validate(self, data):
        if not ShoppingCart.objects.filter(
            user=data['user'], recipe=data['recipe']
        ).exists():
            return data
        raise ValidationError('This recipe is already in the shopping cart.')

    def to_representation(self, instance):
        return RecipeMiniSerializer(
            instance=instance.recipe, context=self.context
        ).data
