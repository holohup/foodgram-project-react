from api.serializers import TagSerializer
from api.views.viewsets import CustomReadOnlyModelViewSet
from recipes.models import Tag


class TagViewSet(CustomReadOnlyModelViewSet):
    """Viewset for tags."""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()
