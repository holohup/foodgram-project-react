from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import get_token, CustomUserViewSet
# from djoser.serializers import SetPasswordSerializer
# from djoser.urls import authtoken
# from djoser.serializers import TokenCreateSerializer
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
