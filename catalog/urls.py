from django.urls import path, include

urlpatterns = [
    path("", include("catalog.categories.urls")),
]