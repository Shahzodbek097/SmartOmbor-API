from rest_framework import serializers
from .models import Product, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "nomi", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductSerializer(serializers.ModelSerializer):
    category_nomi = serializers.CharField(source="category.nomi", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "nomi", "category", "category_nomi",
            "xarid_narxi", "sotish_narxi", "qoldiq", "min_qoldiq", "created_at",
        ]
        read_only_fields = ["id", "qoldiq", "created_at", "category_nomi"]
