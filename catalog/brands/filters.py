from django_filters.rest_framework import FilterSet
from django.core.exceptions import PermissionDenied
import django_filters as filters

from catalog.models.brand import Brand


class BrandFilterSet(FilterSet):
    # Filtrado exacto e insensible a mayúsculas/minúsculas por nombre.
    name = filters.CharFilter(
        lookup_expr="icontains", label="Filter by name (case-insensitive contains)"
    )

    # Filtrado exacto por slug.
    slug = filters.CharFilter(label="Filter by exact slug")

    # Filtros del LifeCycleMixin (ya documentados)
    is_active = filters.BooleanFilter(label="Filter by active status (True/False)")


    # def filter_is_active(self, queryset, name, value):
    #     user = self.request.user

    #     if value is False and not user.is_staff:
    #         raise PermissionDenied("Only administrators can see inactive tags.")

    #     return queryset.filter(is_active=value)

    class Meta:
        # El modelo 'Category' debe estar importado y disponible
        model = Brand
        fields = ["name", "slug", "is_active"]