from io import BytesIO

from django.db import models

from django.core.files.base import ContentFile

import qrcode
from qrcode import constants
from qrcode.image.pil import PilImage


class ProductMeta(models.Model):
    """Additional metadata for product variants including QR code"""

    product_variant = models.OneToOneField(
        "ProductVariant",
        on_delete=models.CASCADE,
        related_name="meta",
        primary_key=True,
    )
    qr_code = models.ImageField(
        upload_to="products/qr_codes/", blank=True, editable=False
    )
    weight = models.CharField(
        max_length=50, blank=True, help_text="Weight with unit (e.g., 500g, 1.5kg)"
    )
    dimensions = models.CharField(
        max_length=100, blank=True, help_text="Dimensions (e.g., 10x20x5 cm)"
    )

    class Meta:
        verbose_name_plural = "Product Meta"

    def __str__(self):
        return f"Meta for {self.product_variant.sku}"

    def save(self, *args, **kwargs):
        """Generate QR code on save"""
        generating = self.pk is None
        super().save(*args, **kwargs)
        if generating:
            self._generate_qr_code()

    def _generate_qr_code(self):
        """Generate QR code with product information"""
        variant = self.product_variant
        product = variant.product

        # Prepare product information for QR code
        qr_data = (
            f"Product: {product.name}\n"
            f"Brand: {product.brand.name}\n"
            f"SKU: {variant.sku}\n"
        )

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
            image_factory=PilImage,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Save to model field
        filename = f"qr_{variant.sku}.png"
        self.qr_code.save(filename, ContentFile(buffer.read()), save=False)
