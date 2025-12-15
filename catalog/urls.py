from django.urls import path, include

urlpatterns = [
    path("", include("catalog.categories.urls")),
    path("", include("catalog.brands.urls")),
    path("", include("catalog.products.urls")),
    path("", include("catalog.specifications.urls")),
    path("", include("catalog.attributes.urls")),
]
