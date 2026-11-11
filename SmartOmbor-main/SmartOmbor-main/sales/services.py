from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Order
from inventory.models import OmborMovement


@transaction.atomic
def complete_order(order_id, user=None):

    # Buyurtmani bloklab olamiz
    order = Order.objects.select_for_update().get(
        pk=order_id
    )

    # Buyurtma egasini tekshirish
    rahbar = (
            user and user.groups.filter(name="Rahbar").exists()
    )

    if (
            user
            and not user.is_superuser
            and not rahbar
            and order.customer_id != user.id
    ):
        raise ValidationError(
            "Siz bu buyurtmani boshqarish huquqiga ega emassiz!"
        )

    # Buyurtma holatini tekshiramiz
    if order.status == Order.Status.COMPLETED:
        raise ValidationError("Bu buyurtma avval yakunlangan!")

    if order.status == Order.Status.CANCELLED:
        raise ValidationError("Bekor qilingan buyurtmani yakunlab bo'lmaydi!")

    # Buyurtma mahsulotlarini olamiz
    items = order.items.select_related("product").order_by("id")

    if not items.exists():
        raise ValidationError("Buyurtmada mahsulot mavjud emas!")

    total = Decimal("0.00")

    for item in items:

        if item.soni <= 0:
            raise ValidationError("Mahsulot miqdori 0 dan katta bo'lishi kerak!")

        if item.narxi <= 0:
            raise ValidationError("Mahsulot narxi noto'g'ri!")

        # Buyurtma umumiy summasini hisoblaymiz
        total += item.subtotal

        # Ombordan mahsulot chiqimini yaratamiz
        movement = OmborMovement(
            product=item.product,
            user=user,
            movement_type=OmborMovement.MovementType.OUT,
            nechta=item.soni,
            sababi=f"Buyurtma #{order.id}"
        )

        movement.save()

    # Buyurtmani yakunlaymiz
    order.total_price = total
    order.status = Order.Status.COMPLETED
    order.save(update_fields=["total_price", "status"])

    return order


@transaction.atomic
def cancel_order(order_id, user=None):

    order = Order.objects.select_for_update().get(
        pk=order_id
    )

    # Buyurtma egasini tekshirish
    rahbar = (
            user and user.groups.filter(name="Rahbar").exists()
    )

    if (
            user
            and not user.is_superuser
            and not rahbar
            and order.customer_id != user.id
    ):
        raise ValidationError(
            "Siz bu buyurtmani boshqarish huquqiga ega emassiz!"
        )

    if order.status == Order.Status.CANCELLED:
        raise ValidationError("Bu buyurtma avval bekor qilingan!")

    if order.status == Order.Status.COMPLETED:

        items = order.items.select_related(
            "product"
        ).order_by("product_id", "id")

        for item in items:

            movement = OmborMovement(
                product=item.product,
                user=user,
                movement_type=OmborMovement.MovementType.IN,
                nechta=item.soni,
                sababi=f"Buyurtma #{order.id} bekor qilindi"
            )

            movement.save()

    order.status = Order.Status.CANCELLED

    order.save(update_fields=["status"])

    return order

