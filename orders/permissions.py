from rest_framework import permissions

class IsOwnerOrGuestCreateOnly(permissions.BasePermission):
    """
    - Permite crear órdenes a cualquiera
    - Solo el dueño puede ver sus órdenes
    """

    def has_permission(self, request, view):
        if view.action == "create":
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.account == request.user