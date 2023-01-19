from django.shortcuts import get_object_or_404, render
from rest_framework import filters, viewsets, status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, action, permission_classes
from django.contrib.auth import get_user_model, authenticate
from rest_framework.response import Response
from .serializers import CustomTokenSerializer


User = get_user_model()


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def get_token(request):
    serializer = CustomTokenSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
