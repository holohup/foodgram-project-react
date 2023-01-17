from django.contrib import admin
from django.http import JsonResponse
from http import HTTPStatus
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls'))
]


def custom_404(request, exception=None):
    return JsonResponse(
        {'error': '404: The resource was not found'},
        status=HTTPStatus.NOT_FOUND
    )


handler404 = custom_404
