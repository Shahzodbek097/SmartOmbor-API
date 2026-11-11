from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models import F
from products.models import Product
from django.conf import settings
from django.core.validators import MinValueValidator


class OmborMovement(models.Model):

    class MovementType(models.TextChoices):
        IN = "IN", "Kirim"
        OUT = "OUT", "Chiqim"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ombor_harakatlari",
        null=True,
        blank=True,
        verbose_name="Harakatni amalga oshirgan"
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="movements")
    movement_type = models.CharField(max_length=3,choices=MovementType.choices)
    nechta = models.PositiveIntegerField(validators=[MinValueValidator(1)],verbose_name="Miqdor")
    sababi = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Faqat yangi harakat yaratilganda qoldiqni o'zgartiramiz.
        if self.pk:
            raise ValidationError(
                "Saqlangan ombor harakatini o'zgartirish mumkin emas."
            )

        if self.nechta <= 0:
            raise ValidationError("Miqdor 0 dan katta bo'lishi kerak.")

        with transaction.atomic():
            # Mahsulot qatorini bloklaymiz.
            product = Product.objects.select_for_update().get(pk=self.product_id)

            if self.movement_type == self.MovementType.IN:
                Product.objects.filter(pk=product.pk).update(qoldiq=F("qoldiq") + self.nechta)

            elif self.movement_type == self.MovementType.OUT:
                updated = Product.objects.filter(
                    pk=product.pk,
                    qoldiq__gte=self.nechta
                ).update(qoldiq=F("qoldiq") - self.nechta)

                if updated == 0:
                    raise ValidationError("Omborda yetarli mahsulot mavjud emas!")

            else:
                raise ValidationError("Noto'g'ri harakat turi.")

            super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.product.nomi} - "
            f"{self.get_movement_type_display()} - "
            f"{self.nechta} dona"
        )
