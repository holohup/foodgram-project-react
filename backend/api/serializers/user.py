from rest_framework import serializers

from users.models import User


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for the custom User model."""

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
        """Create a user and set thy password."""

        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomUserSubscriptionsSerializer(CustomUserSerializer):
    """Serializer for the custom User model with is_subscribed field."""

    is_subscribed = serializers.BooleanField(default=False, read_only=True)

    class Meta:
        model = User
        fields = CustomUserSerializer.Meta.fields + ('is_subscribed',)
        read_only_fields = fields
