from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from orders.models import Order
from orders.payments.webpay import create_webpay_transaction, handle_webpay_return
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


class GuestOrderDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, token):
        try:
            order = Order.objects.prefetch_related("items").get(access_token=token)
        except Order.DoesNotExist:
            raise NotFound("Orden no encontrada")

        if not order.is_guest_token_valid():
            raise PermissionDenied("Token expirado")

        serializer = OrderDetailSerializer(order)
        return Response(serializer.data)


class WebpayCreateTransactionView(APIView):
    """
    Inicia el pago Webpay Plus
    """

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        response = create_webpay_transaction(order)

        return Response(
            {
                "token": response["token"],
                "url": response["url"],
            }
        )


class WebpayReturnView(APIView):
    """
    Endpoint llamado por Webpay luego del pago
    """

    authentication_classes = []
    permission_classes = []

    @transaction.atomic
    def post(self, request):
        token = request.data.get("token")

        if not token:
            raise ValidationError("Token Webpay no recibido")

        response, order = handle_webpay_return(token)

        return Response(
            {
                "order_id": order.pk,
                "order_number": order.order_number,
                "webpay_status": response["status"],
            }
        )
