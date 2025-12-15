# catalog/products/admin.py (o donde tengas los admins)
from django.contrib import admin

from catalog.models.specification import ProductSpecification, Specification


@admin.register(Specification)
class SpecificationAdmin(admin.ModelAdmin):
    list_display = ("name",)

    search_fields = ("name",)

    ordering = ("name",)


@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "specification",
        "short_value",
    )

    list_filter = (
        "specification",
        "product",
    )

    search_fields = (
        "product__name",
        "product__slug",
        "specification__name",
        "value",
    )


    ordering = (
        "product",
        "specification",
    )

    @admin.display(description="Value")
    def short_value(self, obj):
        """Evita valores largos en el listado."""
        return obj.value[:50]
