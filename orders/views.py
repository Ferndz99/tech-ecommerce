from rest_framework import viewsets, permissions
from orders.models import Order
from orders.serializers import (
    OrderWriteSerializer,
    OrderDetailSerializer,
    OrderItemDetailSerializer,
    OrderItemWriteSerializer,
    OrderStatusHistorySerializer,
)


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


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related("items")
    permission_classes = [IsOwnerOrGuestCreateOnly]

    http_method_names = ["get", "post"]

    def get_serializer_class(self):
        if self.action == "create":
            return OrderWriteSerializer
        return OrderDetailSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAdminUser()]

        return super().get_permissions()
