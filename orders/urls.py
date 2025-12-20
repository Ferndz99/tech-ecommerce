from django.urls import path, include
from rest_framework.routers import DefaultRouter

from orders.views import GuestOrderDetailView, OrderViewSet, WebpayCreateTransactionView, WebpayReturnView

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="orders")

urlpatterns = [
    path(
        "orders/<int:order_id>/pay/webpay/",
        WebpayCreateTransactionView.as_view(),
        name="webpay-create-transaction",
    ),
    path(
        "payments/webpay/return/",
        WebpayReturnView.as_view(),
        name="webpay-return",
    ),
    path(
        "orders/track/<uuid:token>/",
        GuestOrderDetailView.as_view(),
        name="guest-order-detail",
    ),
    path("", include(router.urls)),
]
