from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.pagination import RecipesLimitPagination
from api.serializers.recipe import RecipeMiniSerializer
from users.models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for the Subscription model."""

    email = serializers.EmailField(source='author.email', read_only=True)
    id = serializers.IntegerField(source='author.id', read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    recipes = serializers.SerializerMethodField()
    first_name = serializers.CharField(
        source='author.first_name', read_only=True
    )
    last_name = serializers.CharField(
        source='author.last_name', read_only=True
    )
    is_subscribed = serializers.BooleanField(read_only=True, default=False)

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

    def to_representation(self, instance):
        """Return correct unannotated fields upon subscription."""

        data = super().to_representation(instance)
        if self.context['request'].method == 'POST':
            data['is_subscribed'] = True
            data['recipes_count'] = self.instance.author.recipes.count()
        return data

    def validate_author(self, value):
        """Author field validation."""

        if self.context['request'].user == value:
            raise serializers.ValidationError('Say no to self-subscriptions.')
        return value

    def get_recipes(self, subscription):
        """Nested recipes serializer with recipes_limit arg."""

        paginator = RecipesLimitPagination()
        qs = subscription.author.recipes.order_by('-pub_date')
        page = paginator.paginate_queryset(qs, request=self.context['request'])
        serializer = RecipeMiniSerializer(
            many=True,
            instance=page,
            context=self.context,
        )
        return serializer.data
