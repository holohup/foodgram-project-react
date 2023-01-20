from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import get_token, CustomUserViewSet

router = DefaultRouter()

router.register('users', CustomUserViewSet, basename='users')

djoser_urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
]

urlpatterns = [
    path('auth/token/login/', get_token, name='get_token'),
    path('', include(router.urls)),
    path('', include(djoser_urlpatterns)),
]
