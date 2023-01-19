import base64
import datetime

from django.core.files.base import ContentFile

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from recipes.models import Recipe
from django.contrib.auth import get_user_model
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


class PostSerializer(serializers.ModelSerializer):
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


def get_tokens_for_user(user):
    return {'auth_token': str(RefreshToken.for_user(user).access_token)}
