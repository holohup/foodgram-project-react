from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet


class CustomReadOnlyModelViewSet(ReadOnlyModelViewSet):
    """ReadOnly model viewset with presets."""

    permission_classes = (AllowAny,)
    pagination_class = None
    http_method_names = ('get',)


class CustomModelViewsSet(ModelViewSet):
    """Common methods for foodgram views."""

    def generic_create(self, serializer, klass, outer_field):
        """Generic create an authenticated user."""

        data = {
            outer_field: get_object_or_404(klass, id=self.kwargs['pk']).id,
            'user': self.request.user.id,
        }
        serializer = serializer(data=data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def generic_delete(self, klass, outer_klass, outer_field):
        """Generic delete for an authenticated user."""

        g_o_404_args = {
            'user': self.request.user,
            outer_field: get_object_or_404(outer_klass, id=self.kwargs['pk'])
        }
        obj = get_object_or_404(klass, **g_o_404_args)

        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
