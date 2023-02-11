from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from api.serializers import IngredientSerializer
from api.views.viewsets import CustomReadOnlyModelViewSet
from recipes.models import Ingredient


class IngredientViewSet(CustomReadOnlyModelViewSet):
    """Viewset for ingredients."""

    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.order_by('id')
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('^name',)
