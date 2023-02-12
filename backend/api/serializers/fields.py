import base64
import datetime

from django.core.files.base import ContentFile
from rest_framework import serializers

from api.serializers.tags import TagSerializer


class Base64ImageField(serializers.ImageField):
    """Image field class to receive images in base64 and return urls."""

    def to_internal_value(self, data):
        """Decode base64 to file."""

        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=str(datetime.datetime.now().timestamp()) + '.' + ext,
            )
        return super().to_internal_value(data)

    def to_representation(self, value):
        """Return full url, based on request and image url."""

        return self.context['request'].build_absolute_uri(value.url)


class TagRelatedField(serializers.PrimaryKeyRelatedField):
    """Custom representation field for tags in recipes."""

    def to_representation(self, value):
        return TagSerializer(instance=value).data
