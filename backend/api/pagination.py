from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """Pagination class with limit query param."""

    page_size_query_param = 'limit'


class RecipesLimitPagination(PageNumberPagination):
    """Pagination class with limit query param."""

    page_size = settings.DEFAULT_RECIPES_LIMIT
    page_size_query_param = 'recipes_limit'
    page_query_param = None
