from django.db import models

from .product import Product
from catalog.utils import normalize_spec_value


class Specification(models.Model):
    """Technical specification definitions"""

    name = models.CharField(max_length=100, unique=True, db_index=True)


    def __str__(self):
        return self.name


class ProductSpecification(models.Model):
    """Technical specifications for products with automatic normalization"""

    specification = models.ForeignKey(
        'Specification', on_delete=models.CASCADE, related_name="product_specifications"
    )
    product = models.ForeignKey(
        'Product', on_delete=models.CASCADE, related_name="specifications"
    )
    value = models.CharField(max_length=500)

    class Meta:
        unique_together = ["specification", "product"]
        indexes = [
            models.Index(fields=["product", "specification"]),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.specification.name}: {self.value}"

    def save(self, *args, **kwargs):
        """Normalización automática antes de guardar."""
        self.value = normalize_spec_value(self.value)
        return super().save(*args, **kwargs)
