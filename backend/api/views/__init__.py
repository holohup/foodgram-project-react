from api.views.custom_responses import custom404
from api.views.ingredients import IngredientViewSet
from api.views.recipes import RecipeViewSet
from api.views.tags import TagViewSet
from api.views.users import CustomUserViewSet

__all__ = (
    'custom404',
    'IngredientViewSet',
    'RecipeViewSet',
    'TagViewSet',
    'CustomUserViewSet',
)
