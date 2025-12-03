from django.db import models

from django.core.exceptions import ValidationError

from easy_thumbnails.fields import ThumbnailerImageField
from easy_thumbnails.files import get_thumbnailer

from .base import TimeStampedMixin


class ProductImage(TimeStampedMixin):
    """Product variant images with thumbnail generation"""

    product_variant = models.ForeignKey(
        "ProductVariant", on_delete=models.CASCADE, related_name="images"
    )
    image = ThumbnailerImageField(upload_to="products/images/")
    is_primary = models.BooleanField(default=False, db_index=True)

    class Meta(TimeStampedMixin.Meta):
        indexes = [
            models.Index(fields=["product_variant", "is_primary"]),
        ]

    def __str__(self):
        return f"Image for {self.product_variant.sku}"

    @property
    def thumbnail_url(self):
        """
        Return the URL of the thumbnail (e.g., 300x300) using the ThumbnailerImageField.
        """
        if not self.image:
            return None

        try:
            thumbnail_options = {"size": (300, 300), "crop": True, "quality": 85}

            thumbnailer = get_thumbnailer(self.image)
            return thumbnailer.get_thumbnail(thumbnail_options).url  # type: ignore
        except Exception:
            return None

    def clean(self):
        """Validate that only one primary image exists per variant"""
        super().clean()
        if self.is_primary:
            existing_primary = ProductImage.objects.filter(
                product_variant=self.product_variant, is_primary=True
            ).exclude(pk=self.pk)
            if existing_primary.exists():
                raise ValidationError(
                    "This variant already has a primary image. "
                    "Please unset the current primary image first."
                )