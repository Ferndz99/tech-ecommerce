from django.urls import path, include

from rest_framework.routers import DefaultRouter

from catalog.products.views import ProductVariantViewSet, ProductViewSet


router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"product-variants", ProductVariantViewSet, basename="product-variant")

urlpatterns = [
    path("", include(router.urls)),
]
