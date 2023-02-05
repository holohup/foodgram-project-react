from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from api.views import custom404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

handler404 = custom404

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
