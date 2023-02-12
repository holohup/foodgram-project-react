from django.db.models import BooleanField, Count, Exists, OuterRef, Value
from rest_framework.decorators import action

from api.pagination import PageLimitPagination
from api.permissions import IsAuthorizedOrListCreateOnly
from api.serializers import CustomUserSerializer, SubscriptionSerializer
from api.views.viewsets import CustomModelViewsSet
from users.models import Subscription, User


class CustomUserViewSet(CustomModelViewsSet):
    """Viewset for users."""

    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthorizedOrListCreateOnly,)
    http_method_names = ('get', 'post', 'delete')

    @action(('post',), detail=True)
    def subscribe(self, request, pk):
        """Subscription creation."""

        return self.generic_create(SubscriptionSerializer, User, 'author')

    @subscribe.mapping.delete
    def delete_subscribe(self, request, pk):
        """Subscription deletion."""

        return self.generic_delete(Subscription, User, 'author')

    @action(detail=False)
    def subscriptions(self, request):
        """Subscriptions list."""

        paginator = PageLimitPagination()
        qs = (request.user.follower.annotate(is_subscribed=Value(
            True, output_field=BooleanField()
        )).prefetch_related(
            'author__recipes'
        ).annotate(recipes_count=Count(
            'author__recipes'
        )).order_by('-id')
        )
        page = paginator.paginate_queryset(qs, request=request)
        context = {'request': request}
        serializer = SubscriptionSerializer(page, many=True, context=context)
        return paginator.get_paginated_response(serializer.data)

    def get_queryset(self):
        """Annotated queryset for the serializer."""

        user = self.request.user
        queryset = User.objects.order_by('username')
        value = Exists(Subscription.objects.filter(
            user_id=user.id or None, author=OuterRef('id')
        ))
        return queryset.annotate(is_subscribed=value)
