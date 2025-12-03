from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator

from djmoney.models.fields import MoneyField

from taggit.managers import TaggableManager

from .base import LifeCycleMixin, TimeStampedMixin



class ProductVariant(LifeCycleMixin, TimeStampedMixin):
    """Product variants with different attributes"""

    sku = models.CharField(max_length=100, unique=True, db_index=True)
    product = models.ForeignKey(
        "Product", on_delete=models.CASCADE, related_name="variants"
    )
    price = MoneyField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    stock = models.IntegerField(
        default=0, validators=[MinValueValidator(0)], db_index=True
    )
    attributes = models.ManyToManyField(
        "AttributeValue", related_name="variants", blank=True
    )
    tags = TaggableManager()

    class Meta(LifeCycleMixin.Meta, TimeStampedMixin.Meta):
        indexes = [
            models.Index(fields=["product", "stock"]),
        ]