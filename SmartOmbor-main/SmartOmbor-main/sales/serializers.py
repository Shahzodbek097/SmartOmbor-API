from rest_framework import serializers
from decimal import Decimal

from .models import Order, OrderItem
from products.models import Product


class OrderItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    soni = serializers.IntegerField(min_value=1)


class OrderItemReadSerializer(serializers.ModelSerializer):
    product_nomi = serializers.CharField(source="product.nomi", read_only=True)
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_nomi", "soni", "narxi", "subtotal"]


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemWriteSerializer(many=True, write_only=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Buyurtma uchun kamida bitta mahsulot kerak.")
        return value

    def create(self, validated_data):
        from django.db import transaction
        items = validated_data["items"]
        with transaction.atomic():
            # customer set by view (request.user)
            order = Order.objects.create(customer=self.context["request"].user)
            for row in items:
                product = row["product"]
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    soni=row["soni"],
                    narxi=product.sotish_narxi,  # same as old order_create
                )
        return order


class OrderSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source="customer.username", read_only=True)
    items = OrderItemReadSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "customer", "customer_username", "status",
            "total_price", "created_at", "items", "items_count",
        ]
        read_only_fields = [
            "id", "customer", "customer_username", "status",
            "total_price", "created_at", "items", "items_count",
        ]
