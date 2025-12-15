from django.urls import path, include

from rest_framework.routers import DefaultRouter

from catalog.attributes.views import AttributeValueViewSet, AttributeViewSet

router = DefaultRouter()

router.register(r"attributes", AttributeViewSet, basename="attribute")
router.register(r"attribute-values", AttributeValueViewSet, basename="attribute-value")

urlpatterns = [
    path("", include(router.urls)),
]
