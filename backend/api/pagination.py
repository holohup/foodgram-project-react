from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """Pagination class with limit query param."""

    page_size_query_param = 'limit'
