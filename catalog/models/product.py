from django.db import models

from catalog.utils import generate_unique_slug

from .base import TimeStampedMixin


class Product(TimeStampedMixin):
    """Base product model"""

    name = models.CharField(max_length=300, db_index=True)
    slug = models.SlugField(max_length=320, editable=False, db_index=True, null=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        "Category", on_delete=models.PROTECT, related_name="products"
    )
    brand = models.ForeignKey(
        "Brand", on_delete=models.PROTECT, related_name="products"
    )

    class Meta(TimeStampedMixin.Meta):
        indexes = [
            models.Index(fields=["category", "brand"]),
        ]

    def save(self, *args, **kwargs):
        """Generate slug from name on save (never changes after creation)"""
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.brand.name})"
