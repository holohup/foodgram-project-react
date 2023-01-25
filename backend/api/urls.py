from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CustomUserViewSet, FavoriteView, IngredientViewSet,
                    RecipesViewSet, TagViewSet, get_token)

# from djoser.serializers import SetPasswordSerializer
# from djoser.urls import authtoken
# from djoser.serializers import TokenCreateSerializer
router = DefaultRouter()

router.register('users', CustomUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')

djoser_urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
]

urlpatterns = [
    path('auth/token/login/', get_token, name='get_token'),
    path(
        'recipes/<int:recipe_id>/favorite/',
        FavoriteView.as_view(),
        name='favorite',
    ),
    path('', include(router.urls)),
    path('', include(djoser_urlpatterns)),
]
