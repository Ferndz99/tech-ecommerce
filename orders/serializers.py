from decimal import Decimal

from django.db import transaction

from rest_framework import serializers

from djmoney.money import Money

from orders.models import Order, OrderItem, OrderStatusHistory
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

    def create(self, validated_data):
        variant = validated_data["product_variant_id"]
        quantity = validated_data["quantity"]

        unit_price = variant.price.amount  # 👈 MUY IMPORTANTE
        subtotal = unit_price * quantity

        return OrderItem.objects.create(
            order=self.context["order"],
            product_variant=variant,
            product_id=variant.product_id,
            product_name=variant.product.name,
            variant_name=variant.name,
            variant_sku=variant.sku,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
        )


# orders/serializers/order_item.py


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


# orders/serializers/order.py


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

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("La orden debe tener al menos un item.")
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

        total_amount = Decimal("0.00")

        for item_data in items_data:
            variant = item_data["product_variant"]
            quantity = item_data["quantity"]

            unit_price = variant.price.amount
            subtotal = unit_price * quantity

            item = OrderItem.objects.create(
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

        return order


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemDetailSerializer(many=True, read_only=True)
    is_guest_order = serializers.BooleanField(read_only=True)

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
            "is_guest_order",
            "created_at",
            "updated_at",
            "items",
        ]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(source="changed_by.email", read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = [
            "from_status",
            "to_status",
            "changed_by_email",
            "notes",
            "created_at",
        ]
