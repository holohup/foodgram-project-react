from django.urls import include, path
from rest_framework.routers import DefaultRouter
import djoser.urls
from .views import get_token

router = DefaultRouter()

djoser_urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls'))
]

urlpatterns = [
    path('auth/token/login/', get_token, name='get_token'),
    path('', include(router.urls)),
    path('', include(djoser_urlpatterns)),
]
