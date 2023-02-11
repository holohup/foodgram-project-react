from rest_framework import permissions


class IsAuthorOrObjectReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """Special permissions for object author."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.method in ('PATCH', 'DELETE')
            and obj.author == request.user
        )


class IsAuthorizedOrListCreateOnly(permissions.BasePermission):
    """Special permission for author-only actions."""

    def has_permission(self, request, view):
        return (
            view.action in ('list', 'create') or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated
