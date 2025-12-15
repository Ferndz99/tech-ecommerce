from rest_framework.routers import DefaultRouter

from catalog.brands.views import BrandViewSet

router = DefaultRouter()

router.register(r"brands", BrandViewSet, basename="brands")

urlpatterns = router.urls
