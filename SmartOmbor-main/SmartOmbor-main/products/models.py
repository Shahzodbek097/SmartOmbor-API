from django.db import models


class Category(models.Model):
    nomi=models.CharField(max_length=100, unique=True)
    description=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nomi

class Product(models.Model):
    nomi=models.CharField(max_length=100)
    category=models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    xarid_narxi=models.DecimalField(max_digits=10, decimal_places=2)
    sotish_narxi=models.DecimalField(max_digits=10, decimal_places=2)
    qoldiq=models.PositiveIntegerField(default=0)
    min_qoldiq=models.PositiveIntegerField(default=10)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nomi












