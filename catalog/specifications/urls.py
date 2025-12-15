from django.urls import path, include

from rest_framework.routers import DefaultRouter

from catalog.specifications.views import (
    ProductSpecificationViewSet,
    SpecificationViewSet,
)

router = DefaultRouter()

router.register(r"specifications", SpecificationViewSet, basename="specification")
router.register(
    r"product-specifications",
    ProductSpecificationViewSet,
    basename="product-specification",
)


urlpatterns = [
    path("", include(router.urls)),
]
