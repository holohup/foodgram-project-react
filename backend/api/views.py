import io

from django.db.models import BooleanField, Exists, OuterRef, Value
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.pagination import PageLimitPagination
from api.permissions import IsAuthorOrObjectReadOnly
from api.serializers import (CustomUserSerializer,
                             CustomUserSubscriptionsSerializer,
                             FavoriteSerializer, IngredientSerializer,
                             PasswordSerializer, RecipeMiniSerializer,
                             RecipeSerializer, SubscriptionSerializer,
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
    # ordering = ('^name',)


class CustomUserViewSet(viewsets.ModelViewSet):
    serializer_class = CustomUserSubscriptionsSerializer
    permission_classes = (AllowAny,)

    @action(
        ('post', 'delete'), detail=True, permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk):
        if request.method == 'DELETE':
            subscription = get_object_or_404(
                Subscription,
                user=request.user,
                author=get_object_or_404(User, id=pk),
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
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

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        paginator = PageLimitPagination()
        qs = Subscription.objects.filter(user=request.user).order_by('-id')
        page = paginator.paginate_queryset(qs, request=request)
        context = {'user': request.user, 'request': request}
        serializer = SubscriptionSerializer(page, many=True, context=context)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request):
        return Response(self.get_serializer(request.user).data)

    @action(('post',), detail=False, permission_classes=(IsAuthenticated,))
    def set_password(self, request, *args, **kwargs):
        serializer = PasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.order_by('username')
        if self.request.method != 'GET':
            return queryset
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


class RecipesViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrObjectReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('author',)

    @action(
        ('post', 'delete'),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk):
        if request.method == "DELETE":
            qs = ShoppingCart.objects.filter(user=request.user, recipe__id=pk)
            if not qs:
                return Response(
                    ('This recipe does not exist in the shopping cart.'),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            qs.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        recipe = get_object_or_404(Recipe, id=pk)
        _, created = ShoppingCart.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if created:
            serializer = RecipeMiniSerializer(instance=recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(
            ('This recipe is already in the shopping cart.'),
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
        ] = 'attachment; filename="ShoppingCart.pdf"'
        return response

    @action(('post', 'delete'), detail=True)
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'DELETE':
            favorite = get_object_or_404(
                Favorite,
                user=request.user,
                recipe=recipe,
            )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        data = {'user': request.user.id, 'recipe': pk}
        serializer = FavoriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Recipe.objects.all()
            .order_by('-pub_date')
            .select_related('author')
            .prefetch_related('tags', 'ingredients', 'favorite')
        )

        if self.action != 'list':
            return queryset
        params = self.request.query_params
        tags = params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()
        if user.is_anonymous:
            return queryset
        if params.get('is_favorited') == '1':
            queryset = queryset.filter(favorite__user=user)
        if params.get('is_in_shopping_cart') == '1':
            queryset = queryset.filter(shop_carts__user=user)
        return queryset


def custom404(request, exception=None):
    return JsonResponse(
        {'error': 'The resource was not found'},
        status=status.HTTP_404_NOT_FOUND,
    )
