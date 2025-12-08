from django_filters.rest_framework import FilterSet
import django_filters as filters

from catalog.models.category import Category


class CategoryFilterSet(FilterSet):
    # Filtrado exacto e insensible a mayúsculas/minúsculas por nombre.
    name = filters.CharFilter(
        lookup_expr="icontains", label="Filter by name (case-insensitive contains)"
    )

    # Filtrado exacto por slug.
    slug = filters.CharFilter(label="Filter by exact slug")

    # Filtros del LifeCycleMixin (ya documentados)
    is_active = filters.BooleanFilter(label="Filter by active status (True/False)")

    class Meta:
        # El modelo 'Category' debe estar importado y disponible
        model = Category
        fields = ["name", "slug", "is_active"]
