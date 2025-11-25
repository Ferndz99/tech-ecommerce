from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomAccountViewSet,
    AccountLoginAPIView,
    TokenRefreshView,
    AccountLogoutView,
)

router = DefaultRouter()
router.register(r"accounts", CustomAccountViewSet, basename="account")

urlpatterns = [
    path("accounts/login/", AccountLoginAPIView.as_view(), name="account-login"),
    path("accounts/logout/", AccountLogoutView.as_view(), name="account-logout"),
    path("accounts/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("", include(router.urls)),
]
