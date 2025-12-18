# orders/models/order.py
from datetime import timedelta, timezone
from django.db import models
from djmoney.models.fields import MoneyField
from djmoney.models.validators import MinMoneyValidator
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


Account = get_user_model()


class Order(models.Model):
    """
    Orden principal - soporta usuarios registrados e invitados
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        CONFIRMED = "confirmed", "Confirmada"
        PROCESSING = "processing", "En proceso"

    # Identificador único para tracking
    order_number = models.CharField(max_length=50, unique=True, editable=False)

    # Usuario (opcional para invitados)
    account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )

    # Información del cliente
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20, blank=True)

    # Dirección de envío
    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=2, default="CL")

    # Estado y pago
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    total = MoneyField(
        default_currency="CLP",
        max_digits=10,
        decimal_places=2,
        validators=[MinMoneyValidator(0)],
        editable=False,
        null=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["account", "-created_at"]),
            models.Index(fields=["customer_email"]),
            models.Index(fields=["order_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Order {self.order_number} - {self.customer_email}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def calculate_total(self):
        return sum(item.subtotal for item in self.items.all())

    @staticmethod
    def generate_order_number():
        """Genera un número de orden único"""
        from django.utils import timezone

        return f"ORD-{timezone.now():%Y%m%d}-{uuid.uuid4().hex[:8].upper()}"

    @property
    def is_guest_order(self):
        return self.account is None


class OrderItem(models.Model):
    """
    Items individuales de la orden
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    # Referencia a la variante del producto
    product_variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.PROTECT, related_name="order_items"
    )

    # Snapshot de información del producto al momento de la compra
    product_id = models.IntegerField()  # ID del producto base
    product_name = models.CharField(max_length=200)
    variant_name = models.CharField(max_length=200, blank=True)
    variant_sku = models.CharField(max_length=100, blank=True)

    # Precio y cantidad
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"


class OrderStatusHistory(models.Model):
    """
    Historial de cambios de estado de la orden
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="status_history"
    )

    from_status = models.CharField(max_length=20, choices=Order.Status.choices)
    to_status = models.CharField(max_length=20, choices=Order.Status.choices)

    changed_by = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Order status histories"

    def __str__(self):
        return (
            f"Order {self.order.order_number}: {self.from_status} -> {self.to_status}"
        )
