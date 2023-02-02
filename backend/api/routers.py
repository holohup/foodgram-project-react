from django.urls import URLPattern, re_path
from rest_framework.routers import DefaultRouter

ALLOWED_ROUTE_NAMES = [
    'users-list',
    'users-me',
    'users-subscriptions',
    'users-detail',
    'users-subscribe',
    'users-set-password',
    'tags-list',
    'tags-detail',
    'ingredients-list',
    'ingredients-detail',
    'recipes-list',
    'recipes-detail',
    'recipes-shopping-cart',
    'api-root',
    'recipes-download-shopping-cart',
]


def route_name_filter(route: URLPattern) -> bool:
    return route.name in ALLOWED_ROUTE_NAMES


class CustomRouter(DefaultRouter):
    def get_urls(self):
        urls = list(filter(route_name_filter, super().get_urls()))
        if self.include_root_view:
            view = self.get_api_root_view(api_urls=urls)
            root_url = re_path(r'^$', view, name=self.root_view_name)
            urls.append(root_url)
        return urls
