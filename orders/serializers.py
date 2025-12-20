from decimal import Decimal

from django.db import transaction

from rest_framework import serializers

from djmoney.money import Money

from orders.models import Order, OrderItem, OrderStatusHistory
from orders.utils import send_order_confirmation_email
from catalog.models.product_variant import ProductVariant


class OrderItemWriteSerializer(serializers.ModelSerializer):
    product_variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.select_related("product"),
        source="product_variant",
        write_only=True,
    )

    class Meta:
        model = OrderItem
        fields = [
            "product_variant_id",
            "quantity",
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0.")
        return value

class OrderItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "variant_sku",
            "variant_name",
            "quantity",
            "unit_price",
            "subtotal",
        ]

class OrderWriteSerializer(serializers.ModelSerializer):
    items = OrderItemWriteSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "customer_email",
            "customer_name",
            "customer_phone",
            "shipping_address_line1",
            "shipping_address_line2",
            "shipping_city",
            "shipping_state",
            "shipping_postal_code",
            "shipping_country",
            "items",
        ]
        
    @transaction.atomic
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("The order must have at least one item.")

        seen_variants = {}
        errors = {}

        for index, item in enumerate(value):
            variant = item["product_variant"]
            quantity = item["quantity"]

            if quantity <= 0:
                errors[index] = {"quantity": "La cantidad debe ser mayor a 0."}
                continue

            if variant.id in seen_variants:
                errors[index] = {
                    "product_variant": "La variante está duplicada en la orden."
                }
                continue

            seen_variants[variant.id] = quantity

        for variant_id, total_qty in seen_variants.items():
            variant = ProductVariant.objects.select_for_update().get(id=variant_id)

            if total_qty > variant.stock:
                errors.setdefault("stock", []).append(
                    f"Stock insuficiente para '{variant.sku}'. "
                    f"Disponible: {variant.stock}, solicitado: {total_qty}"
                )

        if errors:
            raise serializers.ValidationError(errors)

        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        request = self.context.get("request")

        order = Order.objects.create(
            account=request.user if request and request.user.is_authenticated else None,
            status=Order.Status.PENDING,
            **validated_data,
        )

        order.generate_guest_token(days=7)

        total_amount = Decimal("0.00")

        for item_data in items_data:
            print(item_data)
            variant = item_data["product_variant"]
            quantity = item_data["quantity"]

            # variant.stock -= quantity
            # variant.save(update_fields=["stock"])

            unit_price = variant.price.amount
            subtotal = unit_price * quantity

            OrderItem.objects.create(
                order=order,
                product_variant=variant,
                product_id=variant.product_id,
                product_name=variant.product.name,
                variant_name=variant.name,
                variant_sku=variant.sku,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
            )

            total_amount += subtotal

        order.total = Money(total_amount, "CLP")
        order.save(update_fields=["total"])

        order.reserve_stock()
        order.confirm()

        transaction.on_commit(lambda: send_order_confirmation_email(order))

        return order


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "account",
            "status",
            "customer_email",
            "customer_name",
            "customer_phone",
            "shipping_address_line1",
            "shipping_address_line2",
            "shipping_city",
            "shipping_state",
            "shipping_postal_code",
            "shipping_country",
            "total",
            "created_at",
            "updated_at",
            "items",
        ]


class OrderStatusHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderStatusHistory
        fields = [
            "id",
            "order",
            "from_status",
            "to_status",
            "notes",
            "changed_by",
            "created_at",
        ]
