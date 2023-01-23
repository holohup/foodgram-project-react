import base64
import datetime

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
# from djoser.serializers import TokenCreateSerializer
from rest_framework.authtoken.models import Token
from rest_framework.serializers import ValidationError

from recipes.models import Favorite, Ingredient, Recipe, Tag
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


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
        read_only=True,
    )
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'text',
            'pub_date',
            'image',
            'group',
        )


# class CustomTokenCreateSerializer(TokenCreateSerializer):

#     password = serializers.CharField(
#         max_length=150, write_only=True, required=True
#     )

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.user = None
#         self.fields['email'] = serializers.EmailField(
#           write_only=True, required=True
#           )

#     def validate(self, data):
#         user = authenticate(
#             username=get_object_or_404(User, email=data['email']).username,
#             password=data['password'],
#         )
#         if user is not None:
#             return data
#         raise ValidationError(
#             f'Wrong password: {data["password"]}.'
#         )


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        max_length=150, write_only=True, required=True
    )
    old_password = serializers.CharField(
        max_length=150, write_only=True, required=True
    )

    def validate_old_password(self, value):
        if self.context['request'].user.check_password(value):
            return value
        raise ValidationError('Invalid old password.')

    def validate_new_password(self, value):
        if not validate_password(value):
            return value
        raise ValidationError('Could not validate password')

    def validate(self, data):
        if data['new_password'] == data['old_password']:
            raise ValidationError('Cannot change password to the same value.')
        return data


class CustomTokenSerializer(serializers.Serializer):

    email = serializers.EmailField(write_only=True, required=True)
    password = serializers.CharField(
        max_length=150, write_only=True, required=True
    )
    auth_token = serializers.CharField(required=False)

    def validate(self, data):
        user = authenticate(
            username=get_object_or_404(User, email=data['email']).username,
            password=data['password'],
        )
        if user is not None:
            return user
        raise ValidationError(f'Wrong password: {data["password"]}.')

    def save(self):
        return Token.objects.get_or_create(user=self.validated_data)


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


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Ingredient
