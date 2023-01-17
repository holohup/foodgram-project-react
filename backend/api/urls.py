from django.urls import include, path
from rest_framework.routers import DefaultRouter

# from .views import CommentViewSet, GroupViewSet, PostViewSet, FollowViewSet

router = DefaultRouter()
# router.register(
#     r'posts/(?P<post_id>\d+)/comments', CommentViewSet, basename='comments'
# )
# router.register('follow', FollowViewSet, basename='follow')
# router.register('groups', GroupViewSet, basename='groups')
# router.register('posts', PostViewSet, basename='posts')

djoser_urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.jwt'))
]

urlpatterns = [
    path('', include(router.urls)),
    path('', include(djoser_urlpatterns))
]
