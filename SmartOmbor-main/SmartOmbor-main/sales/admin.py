from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import Order, OrderItem
from .services import complete_order, cancel_order


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer",
        "status",
        "total_price",
        "created_at",
    )

    list_filter = ("status", "created_at")

    inlines = [OrderItemInline]

    actions = ["finish_orders", "cancel_orders"]

    @admin.action(description="Tanlangan buyurtmalarni yakunlash")
    def finish_orders(self, request, queryset):

        success_count = 0
        error_count = 0

        for order in queryset:

            try:
                complete_order(order.id)
                success_count += 1

            except ValidationError as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Buyurtma #{order.id}: {e}",
                    level=messages.ERROR
                )

        if success_count:
            self.message_user(
                request,
                f"{success_count} ta buyurtma muvaffaqiyatli yakunlandi.",
                level=messages.SUCCESS
            )

        if error_count:
            self.message_user(
                request,
                f"{error_count} ta buyurtmani yakunlab bo'lmadi.",
                level=messages.WARNING
            )

    @admin.action(description="Tanlangan buyurtmalarni bekor qilish")
    def cancel_orders(self, request, queryset):

        success_count = 0
        error_count = 0

        for order in queryset:
            try:
                cancel_order(order.id)
                success_count += 1

            except ValidationError as e:
                error_count += 1

                self.message_user(
                    request,
                    f"Buyurtma #{order.id}: {e}",
                    level=messages.ERROR
                )

        if success_count:
            self.message_user(
                request,
                f"{success_count} ta buyurtma bekor qilindi.",
                level=messages.SUCCESS
            )

        if error_count:
            self.message_user(
                request,
                f"{error_count} ta buyurtmani bekor qilib bo'lmadi.",
                level=messages.WARNING
            )

admin.site.register(OrderItem)


