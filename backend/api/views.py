from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscription

from .pagination import PageLimitPagination
from .permissions import AuthorPermissions
from .search import UnquoteSearchFilter
from .serializers import (
    CustomUserSubscriptionsSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeMiniSerializer,
    RecipeSerializer,
    SubscriptionSerializer,
    TagSerializer,
)

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all().order_by('name')
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(TagViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all().order_by('name')
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


# class FavoriteView(views.APIView):
#     def post(self, request, **kwargs):
#         recipe = get_object_or_404(Recipe, pk=kwargs['recipe_id'])
#         serializer = FavoriteSerializer(
#             data={'recipe_id': recipe.id, 'user_id': self.request.user.id},
#             context={'request': request},
#         )
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, **kwargs):
#         favorite = get_object_or_404(
#             Favorite,
#             user=request.user,
#             recipe=Recipe.objects.get(id=self.kwargs.get('recipe_id')),
#         )
#         favorite.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserViewSet(UserViewSet):
    serializer_class = CustomUserSubscriptionsSerializer
    queryset = User.objects.all().order_by('username')
    permission_classes = [AllowAny]

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


class RecipesViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = (AuthorPermissions,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('author',)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk):
        if request.method == "DELETE":
            qs = ShoppingCart.objects.filter(user=request.user, recipe__id=pk)
            if not qs:
                return Response(
                    {'msg': 'The subscription does not exist'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            qs.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        recipe = get_object_or_404(Recipe, id=pk)
        _, created = ShoppingCart.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if created:
            context = {}
            context['request'] = request
            serializer = RecipeMiniSerializer(instance=recipe, context=context)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(
            {'msg': 'Already in the shopping cart.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        ['post', 'delete'],
        detail=True,
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'DELETE':
            favorite = get_object_or_404(
                Favorite,
                user=request.user,
                recipe=recipe,
            )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        data = {'user_id': request.user.id, 'recipe_id': pk}
        context = {'request': request}
        serializer = FavoriteSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Recipe.objects.all()
        if self.action != 'list':
            return queryset
        params = self.request.query_params
        tags = params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags)
        user = self.request.user
        if user.is_anonymous:
            return queryset
        if params.get('is_favorited') == '1':
            queryset = queryset.filter(favorite__user=user)
        if params.get('is_in_shopping_cart') == '1':
            queryset = queryset.filter(shop_cart__user=user)
        return queryset
