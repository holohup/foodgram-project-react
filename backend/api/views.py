# from django.shortcuts import get_object_or_404, render
# from rest_framework import filters
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import Tag
from .serializers import (CustomTokenSerializer, CustomUserSerializer,
                          CustomUserSubscriptionsSerializer,
                          SetPasswordSerializer, TagSerializer)

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    serializer = CustomTokenSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [AllowAny]
    pagination_class = None


class CustomUserViewSet(viewsets.ModelViewSet):
    serializer_class = CustomUserSubscriptionsSerializer
    queryset = User.objects.all().order_by('username')
    permission_classes = [AllowAny]

    @action(
        methods=['get'],
        detail=False,
        url_path='me',
        permission_classes=[IsAuthenticated],
    )
    def my_profile(self, request):
        serializer = CustomUserSubscriptionsSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['post'],
        detail=False,
        url_path='set_password',
        permission_classes=[IsAuthenticated],
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            context={'request': request}, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(
            serializer.validated_data['new_password']
        )
        self.request.user.save()
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomUserSerializer
        return super().get_serializer_class()
