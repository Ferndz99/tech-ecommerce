from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from accounts.serializers import ProblemDetailsSerializer
from catalog.common.docs.errors import error_401, error_403, error_404, error_500
from orders.models import Order, OrderStatusHistory
from orders.payments.webpay import create_webpay_transaction, handle_webpay_return
from orders.permissions import IsOwnerOrGuestCreateOnly
from orders.serializers import (
    OrderWriteSerializer,
    OrderDetailSerializer,
    OrderStatusHistorySerializer,
)

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiExample,
    OpenApiResponse,
    OpenApiParameter,
)

TAG_ORDER = "Orders"
TAG_PAYMENT = "Payments (Webpay)"


@extend_schema_view(
    create=extend_schema(
        tags=[TAG_ORDER],
        summary="Create a new order",
        description=(
            "Creates a new order.\n\n"
            "- **Authenticated users**: order is linked to the user.\n"
            "- **Guest users**: order is created with a temporary access token.\n\n"
            "Order items must reference existing product variants."
        ),
        request=OrderWriteSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Order created successfully",
                response=OrderDetailSerializer,
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Validation error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="ValidationError",
                        summary="Invalid order payload",
                        value={
                            "type": "https://httpstatuses.com/400",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "/api/v1/orders/",
                            "detail": "The submitted data failed validation.",
                            "errors": [
                                {
                                    "field": "customer_email",
                                    "message": "This field is required.",
                                },
                                {
                                    "field": "customer_name",
                                    "message": "This field is required.",
                                },
                                {
                                    "field": "shipping_address_line1",
                                    "message": "This field is required.",
                                },
                                {
                                    "field": "shipping_city",
                                    "message": "This field is required.",
                                },
                                {
                                    "field": "shipping_state",
                                    "message": "This field is required.",
                                },
                                {
                                    "field": "shipping_postal_code",
                                    "message": "This field is required.",
                                },
                                {
                                    "field": "items",
                                    "message": "This field is required.",
                                },
                            ],
                        },
                    )
                ],
            ),
            **error_401("/api/v1/orders/"),
            **error_403("/api/v1/orders/"),
            **error_500("/api/v1/orders/"),
        },
    ),
    list=extend_schema(
        tags=[TAG_ORDER],
        summary="List orders",
        description=(
            "Returns a list of all orders.\n\n"
            "- **Only admin users** can access this endpoint.\n"
            "- Includes order items and customer information."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Order list",
                response=OrderDetailSerializer,
            ),
            **error_401("/api/v1/orders/"),
            **error_403("/api/v1/orders/"),
            **error_500("/api/v1/orders/"),
        },
    ),
    retrieve=extend_schema(
        tags=[TAG_ORDER],
        summary="Retrieve an order",
        description=(
            "Returns the details of a specific order.\n\n"
            "- **Only admin users** can retrieve orders.\n"
            "- Includes items, prices and customer data."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Order detail",
                response=OrderDetailSerializer,
            ),
            **error_401("/api/v1/orders/{id}/"),
            **error_403("/api/v1/orders/{id}/"),
            **error_404("/api/v1/orders/{id}/"),
            **error_500("/api/v1/orders/{id}/"),
        },
    ),
)
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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        read_serializer = OrderDetailSerializer(instance)
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class GuestOrderDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=[TAG_ORDER],
        summary="Retrieve guest order by access token",
        description=(
            "Returns the details of an order created by a guest user.\n\n"
            "- This endpoint does **not require authentication**.\n"
            "- Access is granted using a temporary **guest access token**.\n"
            "- Token expires after a predefined time.\n\n"
            "**Possible outcomes:**\n"
            "- Valid token → order details returned\n"
            "- Invalid token → 404 Not Found\n"
            "- Expired token → 403 Forbidden"
        ),
        parameters=[
            OpenApiParameter(
                name="token",
                description="Guest access token associated with the order",
                required=True,
                location=OpenApiParameter.PATH,
                type=str,
            )
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Guest order detail",
                response=OrderDetailSerializer,
            ),
            **error_404("/api/v1/orders/guest/{token}/"),
            **error_500("/api/v1/orders/guest/{token}/"),
        },
    )
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

    @extend_schema(
        tags=[TAG_PAYMENT],
        summary="Create Webpay transaction",
        description=(
            "Initializes a **Webpay Plus** transaction for an order.\n\n"
            "This endpoint generates a **Webpay transaction token** and "
            "returns the URL where the customer must be redirected to "
            "complete the payment."
        ),
        parameters=[
            OpenApiParameter(
                name="order_id",
                description="ID of the order to be paid",
                required=True,
                type=int,
                location=OpenApiParameter.PATH,
            )
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Webpay transaction created successfully",
                examples=[
                    OpenApiExample(
                        name="WebpayTransactionCreated",
                        summary="Successful Webpay transaction creation",
                        value={
                            "token": "e6c3d8f7c4f34e5e8c3a...",
                            "url": "https://webpay3g.transbank.cl/webpayserver/initTransaction",
                        },
                    )
                ],
            ),
            **error_401("/api/v1/payments/webpay/create/{order_id}/"),
            **error_403("/api/v1/payments/webpay/create/{order_id}/"),
            **error_404("/api/v1/payments/webpay/create/{order_id}/"),
            **error_500("/api/v1/payments/webpay/create/{order_id}/"),
        },
    )
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

    @extend_schema(
        tags=[TAG_PAYMENT],
        summary="Handle Webpay payment return",
        description=(
            "Endpoint called by **Webpay Plus** after the payment process.\n\n"
            "This endpoint:\n"
            "- Validates the Webpay token\n"
            "- Confirms the transaction with Webpay\n"
            "- Updates the related order status\n\n"
            "⚠️ This endpoint is intended to be called **only by Webpay**."
        ),
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Webpay transaction token",
                        "example": "e6c3d8f7c4f34e5e8c3a...",
                    }
                },
                "required": ["token"],
            }
        },
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Webpay payment processed successfully",
                examples=[
                    OpenApiExample(
                        name="WebpayPaymentSuccess",
                        summary="Successful payment confirmation",
                        value={
                            "order_id": 12,
                            "order_number": "ORD-20251221-4FC2B98D",
                            "webpay_status": "AUTHORIZED",
                        },
                    )
                ],
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid or missing Webpay token",
                examples=[
                    OpenApiExample(
                        name="MissingToken",
                        summary="Token not provided",
                        value={"detail": "Token Webpay no recibido"},
                    )
                ],
            ),
            **error_500("/api/v1/payments/webpay/return/"),
        },
    )
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


@extend_schema_view(
    list=extend_schema(
        tags=[TAG_ORDER],
        summary="List order status history",
        description=(
            "Returns a list of order status history records.\n\n"
            "Each record represents a **state transition** of an order, "
            "including when the change occurred and the new status.\n\n"
            "- This endpoint is **read-only**.\n"
            "- Intended for **admin dashboards**, audit logs or order tracking."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Order status history list",
                response=OrderStatusHistorySerializer,
            ),
            **error_401("/api/v1/order-status/"),
            **error_403("/api/v1/order-status/"),
            **error_500("/api/v1/order-status/"),
        },
    ),
    retrieve=extend_schema(
        tags=[TAG_ORDER],
        summary="Retrieve an order status history record",
        description=(
            "Returns the details of a specific order status history entry.\n\n"
            "This endpoint allows inspecting a **single state transition** "
            "of an order for auditing or debugging purposes."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Order status history detail",
                response=OrderStatusHistorySerializer,
            ),
            **error_401("/api/v1/order-status/{id}/"),
            **error_403("/api/v1/order-status/{id}/"),
            **error_404("/api/v1/order-status/{id}/"),
            **error_500("/api/v1/order-status/{id}/"),
        },
    ),
)
class OrderStatusViewSet(viewsets.ModelViewSet):
    queryset = OrderStatusHistory.objects.all()
    http_method_names = ["get"]
    serializer_class = OrderStatusHistorySerializer

    permission_classes = [permissions.IsAdminUser]
