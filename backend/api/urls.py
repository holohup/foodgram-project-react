from django.urls import include, path
from djoser.views import UserViewSet
from rest_framework.routers import DefaultRouter

from api.views import (CustomUserViewSet, IngredientViewSet, RecipeViewSet,
                       TagViewSet)

router = DefaultRouter()

router.register('users', CustomUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

djoser_urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'users/set_password/',
        UserViewSet.as_view({'post': 'set_password'}),
        name='users-set-password',
    ),
    path('users/me/', UserViewSet.as_view({'get': 'me'}), name='users-me'),
]

urlpatterns = [
    path('', include(djoser_urlpatterns)),
    path('', include(router.urls)),
]
