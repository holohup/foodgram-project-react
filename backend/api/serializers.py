import base64
import datetime

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from recipes.models import Recipe
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
        raise ValidationError(
            f'Wrong password: {data["password"]}.'
        )

    def save(self):
        return Token.objects.get_or_create(user=self.validated_data)


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

    def validate_username(self, value):
        if value in ('me', 'set_password') or value.isnumeric():
            raise ValidationError('This username is prohibited.')
        return value


class CustomUserSubscriptionsSerializer(CustomUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = CustomUserSerializer.Meta.fields + ('is_subscribed', )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        user = request.user
        return (
            user.is_authenticated
            and Subscription.objects.filter(author=obj, user=user).exists()
        )
