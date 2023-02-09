from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet


class CustomReadOnlyModelViewSet(ReadOnlyModelViewSet):
    """ReadOnly model viewset with presets."""

    permission_classes = (AllowAny,)
    pagination_class = None
    http_method_names = ('get',)
