from django.http import JsonResponse
from rest_framework import status


def custom404(request, exception=None):
    return JsonResponse(
        {'error': 'The resource was not found'},
        status=status.HTTP_404_NOT_FOUND,
    )
