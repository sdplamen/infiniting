from rest_framework.permissions import BasePermission, SAFE_METHODS


def _resolve(obj, path):
    """Follow a dotted attribute path, e.g. 'author.user' -> obj.author.user."""
    for attr in path.split('.'):
        obj = getattr(obj, attr, None)
        if obj is None:
            return None
    return obj


class IsOwnerOrReadOnly(BasePermission):
    """
    Anyone may read; writing needs a logged-in user, and changing an existing
    object needs one of its owners. The view lists who counts as an owner with
    `owner_paths`, dotted paths from the object to a User (e.g. 'author.user'),
    and sets `staff_can_edit = True` where staff moderate, as on the website.
    """
    message = 'You can only change your own content.'

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if getattr(view, 'staff_can_edit', False) and request.user.is_staff:
            return True
        return any(_resolve(obj, path) == request.user for path in view.owner_paths)


class IsStaffOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
