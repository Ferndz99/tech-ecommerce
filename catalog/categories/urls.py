from rest_framework.routers import DefaultRouter

from catalog.categories.views import CategoryViewSet

router = DefaultRouter()


router.register(r'categories', CategoryViewSet, basename="categories")

urlpatterns = router.urls