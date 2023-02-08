import io

from django.db.models import BooleanField, Exists, OuterRef, Prefetch, Value
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.pagination import PageLimitPagination
from api.permissions import (IsAuthorizedOrListCreateOnly,
                             IsAuthorOrObjectReadOnly)
from api.serializers import (CustomUserSerializer,
                             CustomUserSubscriptionsSerializer,
                             FavoriteSerializer, IngredientSerializer,
                             PasswordSerializer, RecipeSerializer,
                             ShoppingCartSerializer, SubscriptionSerializer,
                             TagSerializer)
from api.utils import draw_pdf, get_grocery_list
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscription, User


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.order_by('id')
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('^name',)


class CustomUserViewSet(viewsets.ModelViewSet):
    serializer_class = CustomUserSubscriptionsSerializer
    permission_classes = (IsAuthorizedOrListCreateOnly,)

    @action(('post',), detail=True)
    def subscribe(self, request, pk):
        context = {
            'user': request.user,
            'author': get_object_or_404(User, id=pk),
            'request': request,
        }
        data = {
            'user': context['user'].id,
            'author': context['author'].id,
        }
        serializer = SubscriptionSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, pk):
        subscription = get_object_or_404(
            Subscription,
            user=request.user,
            author=get_object_or_404(User, id=pk),
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False)
    def subscriptions(self, request):
        paginator = PageLimitPagination()
        qs = Subscription.objects.filter(user=request.user).order_by('-id')
        page = paginator.paginate_queryset(qs, request=request)
        context = {'user': request.user, 'request': request}
        serializer = SubscriptionSerializer(page, many=True, context=context)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False)
    def me(self, request):
        return Response(self.get_serializer(request.user).data)

    @action(('post',), detail=False)
    def set_password(self, request, *args, **kwargs):
        serializer = PasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.order_by('username')
        value = (
            Value(False, output_field=BooleanField())
            if user.is_anonymous
            else Exists(
                Subscription.objects.filter(user=user, author=OuterRef('id'))
            )
        )
        return queryset.annotate(is_subscribed=value)

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserSerializer
        return super().get_serializer_class()


class RecipeViewSet(viewsets.ModelViewSet):
    shopping_cart_filename = 'ShoppingCart.pdf'
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrObjectReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    @action(('post',), detail=True, permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        data = {
            'recipe': get_object_or_404(Recipe, id=pk).id,
            'user': request.user.id,
        }
        serializer = ShoppingCartSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        qs = ShoppingCart.objects.filter(user=request.user, recipe__id=pk)
        if qs.exists():
            qs.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            'This recipe does not exist in the shopping cart.',
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False)
    def download_shopping_cart(self, request):
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
        get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id, 'recipe': pk}
        serializer = FavoriteSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        get_object_or_404(
            Favorite,
            user=request.user,
            recipe=get_object_or_404(Recipe, id=pk),
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            favorited_value = Exists(
                Favorite.objects.filter(user=user, recipe=OuterRef('id'))
            )
            shop_cart_value = Exists(
                ShoppingCart.objects.filter(user=user, recipe=OuterRef('id'))
            )
            is_subscribed_value = Exists(
                Subscription.objects.filter(user=user, author=OuterRef('id'))
            )
        else:
            favorited_value = shop_cart_value = is_subscribed_value = Value(
                False, output_field=BooleanField()
            )

        queryset = (
            Recipe.objects.all()
            .order_by('-pub_date')
            .prefetch_related('tags', 'ingredients', 'favorites')
            .prefetch_related(
                Prefetch(
                    'author',
                    User.objects.annotate(is_subscribed=is_subscribed_value),
                ),
            )
        )

        return queryset.annotate(
            is_favorited=favorited_value,
            is_in_shopping_cart=shop_cart_value,
        )


def custom404(request, exception=None):
    return JsonResponse(
        {'error': 'The resource was not found'},
        status=status.HTTP_404_NOT_FOUND,
    )
