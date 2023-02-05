import io

from django.contrib.auth import get_user_model
from django.db.models import BooleanField, Exists, OuterRef, Value
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.utils import draw_pdf, get_grocery_list, plain_data_to_cart_items
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscription

from .pagination import PageLimitPagination
from .permissions import IsAuthorPermission
from .search import UnquoteSearchFilter
from .serializers import (CustomUserSubscriptionsSerializer,
                          FavoriteSerializer, IngredientSerializer,
                          RecipeMiniSerializer, RecipeSerializer,
                          SubscriptionSerializer, TagSerializer)

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(TagViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all().order_by('id')
    filter_backends = (UnquoteSearchFilter, DjangoFilterBackend)
    search_fields = ('name',)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        search_term = request.query_params.get('name')
        if not search_term:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        data_startswith = self.get_serializer(
            queryset.filter(name__istartswith=search_term), many=True
        ).data
        data_notstartswith = self.get_serializer(
            queryset.exclude(name__istartswith=search_term), many=True
        ).data

        return Response(list(data_startswith) + list(data_notstartswith))


class FavoriteView(GenericAPIView, CreateModelMixin, DestroyModelMixin):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer

    def delete(self, request, pk, *args, **kwargs):
        return self.destroy(request, pk, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(
            Favorite,
            user=self.request.user,
            recipe=get_object_or_404(Recipe, id=self.kwargs['pk']),
        )

    def post(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, pk=kwargs['pk'])
        if hasattr(request.data, '_mutable'):
            request.data._mutable = True
        request.data.update(
            {'recipe': recipe.id, 'user': self.request.user.id}
        )
        return self.create(request)


class CustomUserViewSet(UserViewSet):
    serializer_class = CustomUserSubscriptionsSerializer

    @action(
        ['post', 'delete'], detail=True, permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id):
        if request.method == 'DELETE':
            subscription = get_object_or_404(
                Subscription,
                user=request.user,
                author=get_object_or_404(User, id=id),
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        context = {
            'user': request.user,
            'author': get_object_or_404(User, id=id),
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

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        paginator = PageLimitPagination()
        qs = Subscription.objects.filter(user=request.user).order_by('-id')
        page = paginator.paginate_queryset(qs, request=request)
        context = {'user': request.user, 'request': request}
        serializer = SubscriptionSerializer(page, many=True, context=context)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(self.get_serializer(request.user).data)

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.all().order_by('username')
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


class RecipesViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('author',)

    @action(
        ['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
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
        data = plain_data_to_cart_items(get_grocery_list(request.user))
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

    @action(['post', 'delete'], detail=True)
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
            queryset = queryset.filter(shop_cart__user=user)
        return queryset


def custom404(request, exception=None):
    return JsonResponse(
        {'error': 'The resource was not found'},
        status=status.HTTP_404_NOT_FOUND,
    )
