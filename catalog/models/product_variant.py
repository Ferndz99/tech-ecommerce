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
        default_currency="CLP",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    stock = models.IntegerField(
        default=0, validators=[MinValueValidator(0)], db_index=True
    )
    attributes = models.ManyToManyField(
        "AttributeValue", related_name="variants", blank=True
    )
    tags = TaggableManager()

    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=300, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"



    # def generate_slug(self):
    #     base = slugify(self.product.name)

    #     # ordena atributos por el nombre del atributo
    #     attrs = self.attributes.order_by("attribute__name").values_list(
    #         "value", flat=True
    #     )

    #     parts = [base] + [slugify(a) for a in attrs]

    #     return "-".join(parts)

    # def save(self, *args, **kwargs):
    #     creating = self.pk is None

    #     super().save(*args, **kwargs)

    #     if creating:
    #         # ahora sí tiene ID
    #         self.slug = self.generate_slug()
    #         super().save(update_fields=["slug"])

    class Meta(LifeCycleMixin.Meta, TimeStampedMixin.Meta):
        indexes = [
            models.Index(fields=["product", "stock"]),
        ]
