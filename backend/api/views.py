import io

from django.db.models import (BooleanField, Count, Exists, OuterRef, Prefetch,
                              Value)
from django.http import HttpResponse, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.pagination import PageLimitPagination
from api.permissions import (IsAuthorizedOrListCreateOnly,
                             IsAuthorOrObjectReadOnly)
from api.serializers import (CustomUserSerializer,
                             CustomUserSubscriptionsSerializer,
                             FavoriteSerializer, IngredientSerializer,
                             RecipeSerializer, ShoppingCartSerializer,
                             SubscriptionSerializer, TagSerializer)
from api.utils import draw_pdf, get_grocery_list
from api.viewsets import CustomModelViewsSet, CustomReadOnlyModelViewSet
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscription, User


class TagViewSet(CustomReadOnlyModelViewSet):
    """Viewset for tags."""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(CustomReadOnlyModelViewSet):
    """Viewset for ingredients."""

    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.order_by('id')
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('^name',)


class CustomUserViewSet(CustomModelViewsSet):
    """Viewset for users."""

    serializer_class = CustomUserSubscriptionsSerializer
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

    def get_serializer_class(self):
        """Return a serializer without the is_subscribed field upon reg."""

        if self.action == 'create':
            return CustomUserSerializer
        return super().get_serializer_class()


class RecipeViewSet(CustomModelViewsSet):
    """Viewset for recipes."""

    shopping_cart_filename = 'ShoppingCart.pdf'
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrObjectReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    @action(('post',), detail=True, permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        """Add a recipe to the shopping cart."""

        return self.generic_create(ShoppingCartSerializer, Recipe, 'recipe')

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """Delete a recipe from the shopping cart."""

        return self.generic_delete(ShoppingCart, Recipe, 'recipe')

    @action(detail=False)
    def download_shopping_cart(self, request):
        """Download shopping cart in a PDF format."""

        data = get_grocery_list(request.user)
        if not data:
            return Response(
                'The shopping list is empty', status=status.HTTP_204_NO_CONTENT
            )
        buffer = io.BytesIO(bytes(draw_pdf(data)))
        response = HttpResponse(buffer, content_type='application/pdf')
        response[
            'Content-Disposition'
        ] = f'attachment; filename={self.shopping_cart_filename}'
        return response

    @action(('post',), detail=True)
    def favorite(self, request, pk):
        """Add a recipe to favorites."""

        return self.generic_create(FavoriteSerializer, Recipe, 'recipe')

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """Delete from favorites."""

        return self.generic_delete(Favorite, Recipe, 'recipe')

    def perform_create(self, serializer):
        """Create a recipe."""

        return serializer.save(author=self.request.user)

    def get_queryset(self):
        """Recipes queryset for the serializer."""

        user = self.request.user
        favorited_value = Exists(Favorite.objects.filter(
            user_id=user.id or None, recipe=OuterRef('id'))
        )
        shop_cart_value = Exists(ShoppingCart.objects.filter(
            user_id=user.id or None, recipe=OuterRef('id'))
        )
        is_subscribed_value = Exists(Subscription.objects.filter(
            user_id=user.id or None, author=OuterRef('id'))
        )

        queryset = (Recipe.objects.all().order_by(
            '-pub_date'
        ).prefetch_related(
            'tags',
            'favorites',
            'recipeingredients__ingredient'
        ).prefetch_related(Prefetch(
            'author',
            User.objects.annotate(is_subscribed=is_subscribed_value),
        )))

        return queryset.annotate(
            is_favorited=favorited_value,
            is_in_shopping_cart=shop_cart_value,
        )


def custom404(request, exception=None):
    """Custom 404 response."""

    return JsonResponse(
        {'error': 'The resource was not found'},
        status=status.HTTP_404_NOT_FOUND,
    )
