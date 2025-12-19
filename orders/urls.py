from django.urls import path, include
from rest_framework.routers import DefaultRouter

from orders.views import GuestOrderDetailView, OrderViewSet

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="orders")

urlpatterns = [
    path(
        "orders/track/<uuid:token>/",
        GuestOrderDetailView.as_view(),
        name="guest-order-detail",
    ),
    path("", include(router.urls)),
]
