from django_filters import FilterSet, filters
from django_filters.widgets import BooleanWidget


class RecipeFilter(FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(widget=BooleanWidget)
    is_in_shopping_cart = filters.BooleanFilter(widget=BooleanWidget)
