from django_filters import FilterSet, filters
from django_filters.widgets import BooleanWidget


class RecipeFilter(FilterSet):
    """Required filters for RecipeViewSet."""

    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(widget=BooleanWidget)
    is_in_shopping_cart = filters.BooleanFilter(widget=BooleanWidget)
    author = filters.AllValuesFilter(field_name='author__id')
