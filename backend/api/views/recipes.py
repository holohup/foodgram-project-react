import io

from django.db.models import Exists, OuterRef, Prefetch
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.permissions import IsAuthorOrObjectReadOnly
from api.serializers import (FavoriteSerializer, RecipeSerializer,
                             ShoppingCartSerializer)
from api.utils import draw_pdf, get_grocery_list
from api.views.viewsets import CustomModelViewsSet
from recipes.models import Favorite, Recipe, ShoppingCart
from users.models import Subscription, User


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
