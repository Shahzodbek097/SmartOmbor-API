"""Products — REST API (replaces old template views, same filters/rules)."""
from django.db import IntegrityError
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import ProductsAccess
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.order_by("nomi")
    serializer_class = CategorySerializer
    search_fields = ["nomi"]
    permission_classes = [IsAuthenticated, ProductsAccess]

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"nomi": "Bu kategoriya allaqachon mavjud."})

    def perform_update(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"nomi": "Bu nomdagi kategoriya allaqachon mavjud."})


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, ProductsAccess]

    def get_queryset(self):
        qs = Product.objects.select_related("category").order_by("-created_at")
        q = self.request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(nomi__icontains=q))
        category = self.request.query_params.get("category", "")
        if category:
            qs = qs.filter(category_id=category)
        return qs

    # search_fields would double-filter; we already filter manually, keep ordering param
    search_fields = None
