from django.db import models
from django.conf import settings
from products.models import Product


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Kutilmoqda"
        COMPLETED = "COMPLETED", "Yakunlangan"
        CANCELLED = "CANCELLED", "Bekor qilingan"

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Buyurtma #{self.id}"



class OrderItem(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    soni = models.PositiveIntegerField()
    narxi = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.soni * self.narxi

    def __str__(self):
        return f"{self.product.nomi} - {self.soni} dona"

