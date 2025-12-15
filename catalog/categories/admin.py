from django.db import transaction
from django.contrib import admin
from django.utils.safestring import mark_safe

from django_mptt_admin.admin import DjangoMpttAdmin

from catalog.models.category import Category


@admin.register(Category)
class CategoryAdmin(DjangoMpttAdmin):
    readonly_fields = ("slug", "created_at", "updated_at", "is_deleted")

    list_display = (
        "name",
        "slug",
        "status_display",
        "parent",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_active",
        "is_deleted",
        "created_at",
    )

    search_fields = (
        "name",
        "slug",
    )


    actions = [
        "soft_delete_selected",
        "restore_selected",
        "activate_selected",
        "deactivate_selected",
    ]

    @admin.display(description="Status")
    def status_display(self, obj):
        """Muestra un indicador visual para el estado."""
        if obj.is_deleted:
            color = "red"
            text = "DELETED"
        elif not obj.is_active:
            color = "orange"
            text = "INACTIVE"
        else:
            color = "green"
            text = "ACTIVE"

        return mark_safe(
            f'<span style="color: {color}; font-weight: bold;">{text}</span>'
        )

    @admin.action(description="Delete logically (Soft Delete)")
    @transaction.atomic
    def soft_delete_selected(self, request, queryset):
        for category in queryset:
            category.soft_delete()
        self.message_user(
            request, f"{queryset.count()} categories were logically removed."
        )

    @admin.action(description="Restore categories")
    @transaction.atomic
    def restore_selected(self, request, queryset):
        for category in queryset:
            category.restore()
        self.message_user(request, f"{queryset.count()} categories were restored")

    @admin.action(description="Activate categories")
    @transaction.atomic
    def activate_selected(self, request, queryset):
        for category in queryset:
            category.activate()
        self.message_user(request, f"{queryset.count()} categories were activated.")

    @admin.action(description="Deactivate categories")
    @transaction.atomic
    def deactivate_selected(self, request, queryset):
        for category in queryset:
            category.deactivate()
        self.message_user(request, f"{queryset.count()} categories were deactivated.")
