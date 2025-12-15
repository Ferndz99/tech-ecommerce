from django.contrib import admin

from catalog.models.attribute import Attribute, AttributeValue

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )




@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = (
        "attribute",
        "value",
    )

    list_filter = (
        "attribute",
    )

    search_fields = (
        "value",
        "attribute__name",
    )

    ordering = (
        "attribute__name",
        "value",
    )
