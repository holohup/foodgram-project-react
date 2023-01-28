from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipesViewSet,
    TagViewSet,
)

router = DefaultRouter()

router.register('users', CustomUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')

djoser_urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
]

urlpatterns = [
    path('', include(router.urls)),
    path('', include(djoser_urlpatterns)),
]
