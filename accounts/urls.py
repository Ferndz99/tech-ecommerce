from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomAccountViewSet

router = DefaultRouter()
router.register(r"accounts", CustomAccountViewSet, basename="account")

urlpatterns = [
    path("", include(router.urls)),
]