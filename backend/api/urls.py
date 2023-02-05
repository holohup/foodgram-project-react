from django.urls import include, path

from .routers import CustomRouter
from .views import (CustomUserViewSet, IngredientViewSet, RecipesViewSet,
                    TagViewSet)

router = CustomRouter()

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
