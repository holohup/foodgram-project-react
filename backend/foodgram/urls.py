from http import HTTPStatus

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

# from rest_framework.authtoken.models import TokenProxy

# admin.site.unregister(TokenProxy)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]


def custom_404(request, exception=None):
    return JsonResponse(
        {'error': '404: The resource was not found'},
        status=HTTPStatus.NOT_FOUND,
    )


handler404 = custom_404
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
