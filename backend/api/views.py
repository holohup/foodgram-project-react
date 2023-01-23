# from django.shortcuts import get_object_or_404, render
# from rest_framework import filters
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, status, views, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, Tag
from users.models import Subscription

from .serializers import (CustomTokenSerializer, CustomUserSerializer,
                          CustomUserSubscriptionsSerializer,
                          FavoriteSerializer, IngredientSerializer,
                          SetPasswordSerializer, TagSerializer)

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
        recipe = get_object_or_404(Recipe, pk=self.kwargs['recipe_id'])
        serializer = FavoriteSerializer(
            data={'recipe_id': recipe.id, 'user_id': self.request.user.id},
            context={'request': self.request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        favorite = get_object_or_404(
            Favorite,
            user=self.request.user,
            recipe=Recipe.objects.get(id=self.kwargs.get('recipe_id'))
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
            request.user,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['post'], detail=False, permission_classes=[IsAuthenticated],
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

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomUserSerializer
        return super().get_serializer_class()
