from django.contrib import admin
from django.db import transaction
from django.utils.safestring import mark_safe

from catalog.models.product import Product
from catalog.models.product_image import ProductImage
from catalog.models.product_meta import ProductMeta
from catalog.models.product_variant import ProductVariant


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    readonly_fields = (
        "slug",
        "created_at",
        "updated_at",
    )

    list_display = (
        "name",
        "brand",
        "category",
        "created_at",
    )

    list_filter = (
        "brand",
        "category",
        "created_at",
    )

    search_fields = (
        "name",
        "slug",
        "brand__name",
        "category__name",
    )

    ordering = ("name",)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """
    NOTE:
    slug and name are generated at serializer level because
    they depend on the selected attributes at creation time.
    """

    readonly_fields = ("slug",)
    exclude = ("slug",)

    def has_add_permission(self, request):
        return False


@admin.register(ProductMeta)
class ProductMetaAdmin(admin.ModelAdmin):
    readonly_fields = ("qr_code",)

    list_display = (
        "product_variant",
        "weight",
        "dimensions",
    )

    search_fields = (
        "product_variant__sku",
        "product_variant__name",
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    readonly_fields = (
        "created_at",
        "updated_at",
        "thumbnail_preview",
    )

    list_display = (
        "product_variant",
        "is_primary",
        "thumbnail_preview",
    )

    list_filter = ("is_primary",)

    search_fields = (
        "product_variant__sku",
        "product_variant__name",
    )

    @admin.display(description="Preview")
    def thumbnail_preview(self, obj):
        if obj.thumbnail_url:
            return mark_safe(
                f'<img src="{obj.thumbnail_url}" style="width:80px; height:auto;" />'
            )
        return "—"
