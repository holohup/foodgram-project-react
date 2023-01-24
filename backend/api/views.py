# from django.shortcuts import get_object_or_404, render
# from rest_framework import filters
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, status, views, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .pagination import PageLimitPagination
from recipes.models import Favorite, Ingredient, Recipe, Tag
from users.models import Subscription

from .serializers import (
    CustomTokenSerializer,
    CustomUserSerializer,
    CustomUserSubscriptionsSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    SetPasswordSerializer,
    TagSerializer,
    SubscriptionSerializer,
    RecipeSerializer
)

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    serializer = CustomTokenSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all().order_by('name')
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(TagViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all().order_by('name')


class FavoriteView(views.APIView):
    def post(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, pk=kwargs['recipe_id'])
        serializer = FavoriteSerializer(
            data={'recipe_id': recipe.id, 'user_id': self.request.user.id},
            context={'request': request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        favorite = get_object_or_404(
            Favorite,
            user=self.request.user,
            recipe=Recipe.objects.get(id=self.kwargs.get('recipe_id')),
        )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserViewSet(viewsets.ModelViewSet):
    serializer_class = CustomUserSubscriptionsSerializer
    queryset = User.objects.all().order_by('username')
    permission_classes = [AllowAny]

    @action(
        methods=['get'], detail=False, permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        serializer = CustomUserSubscriptionsSerializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['post'],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            context={'request': request}, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(
            serializer.validated_data['new_password']
        )
        self.request.user.save()
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk):
        if request.method == 'DELETE':
            subscription = get_object_or_404(
                Subscription,
                user=request.user,
                author=get_object_or_404(User, pk=pk),
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        context = {
            'user': request.user,
            'author': get_object_or_404(User, id=pk),
            'request': request
        }
        data = {
            'user': context['user'].id,
            'author': context['author'].id,
        }
        serializer = SubscriptionSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        paginator = PageLimitPagination()
        qs = Subscription.objects.filter(user=request.user).order_by('-id')
        page = paginator.paginate_queryset(qs, request=request)
        context = {
            'user': request.user,
            'request': request
        }
        serializer = SubscriptionSerializer(page, many=True, context=context)
        return paginator.get_paginated_response(serializer.data)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomUserSerializer
        return super().get_serializer_class()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [AllowAny]