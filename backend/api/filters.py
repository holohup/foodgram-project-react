from django_filters import FilterSet, CharFilter, OrderingFilter

from recipes.models import Ingredient


class StartswithCaseInsensitiveFilter(OrderingFilter):
    name = CharFilter(name='name', lookup_type=("icontains"))

    # class Meta:
    #     model = Ingredient
    #     fields = {
    #         'name': ['istartswith', 'icontains']
    #     }
