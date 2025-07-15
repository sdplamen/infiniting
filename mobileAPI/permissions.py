from rest_framework.permissions import BasePermission

class IsAuthenticatedAndOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        return obj.user == request.user

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user and request.user.is_staff

class IsGroupMember(BasePermission):
    def has_permission(self, request, view):
        group_name = getattr(view, 'group_name', None)
        if not group_name:
            return False
        return request.user and request.user.groups.filter(name=group_name).exists()
