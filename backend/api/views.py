from django.shortcuts import get_object_or_404, render
from rest_framework import filters, viewsets, status, permissions
from rest_framework.decorators import api_view, action, permission_classes
from django.contrib.auth import get_user_model, authenticate
from rest_framework.response import Response
from .serializers import get_tokens_for_user

User = get_user_model()


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def get_token(request):
    data = request.data
    for arg in ('email', 'password'):
        if not data.get(arg):
            return Response(
                {arg: ['This field is required.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
    user = authenticate(
        username=get_object_or_404(User, email=data['email']).username,
        password=data['password']
        )
    if user is not None:
        return Response(get_tokens_for_user(user), status=status.HTTP_200_OK)
    return Response(
        f'Incorrect user credentials: {data}',
        status=status.HTTP_400_BAD_REQUEST,
    )
