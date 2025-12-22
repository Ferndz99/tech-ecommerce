import uuid
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from djmoney.models.fields import MoneyField
from djmoney.models.validators import MinMoneyValidator


Account = get_user_model()


class Order(models.Model):
    """
    Orden principal - soporta usuarios registrados e invitados
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente (reservada)"
        CONFIRMED = "confirmed", "Confirmada (pagada)"
        CANCELLED = "cancelled", "Cancelada"

    order_number = models.CharField(max_length=50, unique=True, editable=False)

    account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )

    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20, blank=True)

    shipping_address_line1 = models.CharField(max_length=255)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=2, default="CL")

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    total = MoneyField(
        default_currency="CLP",
        max_digits=10,
        decimal_places=2,
        validators=[MinMoneyValidator(0)],
        editable=False,
        null=True,
    ) # type: ignore

    access_token = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, db_index=True
    )

    access_token_expires_at = models.DateTimeField(null=True, blank=True)

    payment_reference = models.CharField(
    max_length=255, blank=True, null=True
)
    
    items: models.QuerySet["OrderItem"]

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

    def generate_guest_token(self, days=7):
        self.access_token = uuid.uuid4()
        self.access_token_expires_at = timezone.now() + timedelta(days=days)
        self.save(update_fields=["access_token", "access_token_expires_at"])

    def is_guest_token_valid(self):
        return (
            self.access_token_expires_at is None
            or self.access_token_expires_at > timezone.now()
        )

    def reserve_stock(self):
        for item in self.items.select_related("product_variant"):
            item.product_variant.reserve(item.quantity)

    def release_stock(self):
        for item in self.items.select_related("product_variant"):
            item.product_variant.release(item.quantity)

    def confirm(self):
        if self.status != self.Status.PENDING:
            raise ValidationError("La orden no puede confirmarse")

        for item in self.items.select_related("product_variant"):
            item.product_variant.consume(item.quantity)

        # self.status = self.Status.CONFIRMED
        # self.save(update_fields=["status"])
        self.change_status(self.Status.CONFIRMED)

    def cancel(self):
        if self.status != self.Status.PENDING:
            return
        self.release_stock()
        # self.status = self.Status.CANCELLED
        # self.save(update_fields=["status"])
        self.change_status(self.Status.CANCELLED)


    def change_status(self, to_status, *, by=None, notes=""):
        """
        Change the order status and record the history
        """
        from_status = self.status

        if from_status == to_status:
            return  # do nothing

        self.status = to_status
        self.save(update_fields=["status"])

        OrderStatusHistory.objects.create(
            order=self,
            from_status=from_status,
            to_status=to_status,
            changed_by=by,
            notes=notes,
        )


class OrderItem(models.Model):
    """
    Items individuales de la orden
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    product_variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.PROTECT, related_name="order_items"
    )

    product_id = models.IntegerField()  
    product_name = models.CharField(max_length=200)
    variant_name = models.CharField(max_length=200, blank=True)
    variant_sku = models.CharField(max_length=100, blank=True)

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
