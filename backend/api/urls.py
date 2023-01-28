from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet,
    FavoriteView,
    IngredientViewSet,
    RecipesViewSet,
    TagViewSet,
)

# from djoser.serializers import SetPasswordSerializer
# from djoser.serializers import TokenCreateSerializer
# from djoser import urls

router = DefaultRouter()

# router.register('users', CustomUserViewSet, basename='users')
router.register('users', CustomUserViewSet, basename='user')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')

djoser_urlpatterns = [
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

urlpatterns = [
    path('', include(router.urls)),
    path(
        'recipes/<int:recipe_id>/favorite/',
        FavoriteView.as_view(),
        name='favorite',
    ),
    # path(
    #     'users/<int:id>/subscribe/',
    #     FavoriteView.as_view(),
    #     name='favorite',
    # ),
    path('', include(djoser_urlpatterns)),
    
]
