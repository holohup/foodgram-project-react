from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (CustomUserViewSet, IngredientViewSet, RecipesViewSet,
                       TagViewSet)

router = DefaultRouter()

router.register('users', CustomUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')


urlpatterns = [
    # path(
    #     'recipes/<int:pk>/favorite/',
    #     FavoriteView.as_view(),
    #     name='recipes-favorite',
    # ),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
