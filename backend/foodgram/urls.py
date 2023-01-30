from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.models import TokenProxy

from api.exceptions import custom404

admin.site.unregister(TokenProxy)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

handler404 = custom404

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
