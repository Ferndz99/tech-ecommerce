from django_filters.rest_framework import FilterSet
import django_filters as filters

from catalog.models.product_variant import ProductVariant



class ProductVariantFilter(FilterSet):
    price_min = filters.NumberFilter(
        field_name="price", lookup_expr="gte"
    )
    price_max = filters.NumberFilter(
        field_name="price", lookup_expr="lte"
    )
    stock_min = filters.NumberFilter(
        field_name="stock", lookup_expr="gte"
    )
    stock_max = filters.NumberFilter(
        field_name="stock", lookup_expr="lte"
    )

    is_active = filters.BooleanFilter()
    product = filters.CharFilter(
        field_name="product__slug"
    )

    class Meta:
        model = ProductVariant
        fields = [
            "slug",
            "name",
            "is_active",
            "product",
        ]