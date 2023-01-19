from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import get_token

router = DefaultRouter()
# router.register('auth/token/login', CustomTokenViewSet, basename='get_token')

djoser_urlpatterns = [
    # path('auth/token/login/', get_token, name='get_token'),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls'))
]
# print(djoser.urls)
urlpatterns = [
    path('auth/token/login/', get_token, name='get_token'),
    path('', include(router.urls)),
    path('', include(djoser_urlpatterns)),
]
