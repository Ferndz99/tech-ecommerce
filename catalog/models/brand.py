from django.db import models

from easy_thumbnails.fields import ThumbnailerImageField

from .base import LifeCycleMixin, TimeStampedMixin
from catalog.utils import generate_unique_slug


class Brand(LifeCycleMixin, TimeStampedMixin):
    """Product brands/manufacturers"""

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True, editable=False)
    logo = ThumbnailerImageField(
        upload_to="brands/logos/",
        blank=True,
        null=True,
        default="/default/product_placeholder.png",
    )

    class Meta(LifeCycleMixin.Meta, TimeStampedMixin.Meta):
        indexes = [
            models.Index(fields=["is_active", "name"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Generate slug from name on save (never changes after creation)"""
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)
