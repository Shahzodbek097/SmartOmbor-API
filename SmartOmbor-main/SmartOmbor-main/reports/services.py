from django.db.models import Sum, Q, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate
from django.utils import timezone

from sales.models import Order, OrderItem
from products.models import Product
from inventory.models import OmborMovement


def get_daily_report():
    today = timezone.localdate()

    orders = Order.objects.filter(status=Order.Status.COMPLETED,created_at__date=today)
    order_items = OrderItem.objects.filter(order__in=orders)
    jami_pul = orders.aggregate(total=Sum("total_price"))["total"] or 0
    sot_mah_soni = order_items.aggregate(total=Sum("soni"))["total"] or 0
    yalpi_foyda = order_items.aggregate(total=Sum(
            ExpressionWrapper(
                (F("narxi") - F("product__xarid_narxi")) * F("soni"),
                output_field=DecimalField(
                    max_digits=14,
                    decimal_places=2
                )
            )
        )
    )["total"] or 0

    return {
        "date": today,
        "orders_count": orders.count(),
        "jami_pul": jami_pul,
        "sot_mah_soni": sot_mah_soni,
        "yalpi_foyda": yalpi_foyda,
    }


def get_monthly_report(year, month):

    orders = Order.objects.filter(
        status=Order.Status.COMPLETED,
        created_at__year=year,
        created_at__month=month
    )

    order_items = OrderItem.objects.filter(order__in=orders)
    jami_pul = orders.aggregate(total=Sum("total_price"))["total"] or 0
    sot_mah_soni = order_items.aggregate(total=Sum("soni"))["total"] or 0
    yalpi_foyda = order_items.aggregate(total=Sum(
            ExpressionWrapper(
                (F("narxi") - F("product__xarid_narxi"))
                * F("soni"),
                output_field=DecimalField(
                    max_digits=14,
                    decimal_places=2
                )
            )
        )
    )["total"] or 0

    return {
        "year": year,
        "month": month,
        "orders_count": orders.count(),
        "jami_pul": jami_pul,
        "sot_mah_soni": sot_mah_soni,
        "yalpi_foyda": yalpi_foyda,
    }


def get_low_stock_products():

    return Product.objects.filter(qoldiq__lte=F("min_qoldiq")).order_by("qoldiq")


def get_daily_sales_chart():

    today = timezone.localdate()

    orders = Order.objects.filter(
        status=Order.Status.COMPLETED,
        created_at__year=today.year,
        created_at__month=today.month
    )

    result = (
        orders
        .annotate(sana=TruncDate("created_at"))
        .values("sana")
        .annotate(tushum=Sum("total_price"))
        .order_by("sana")
    )

    return {
        "labels": [item["sana"].strftime("%d-%m") for item in result],
        "values": [float(item["tushum"]) for item in result]
    }


def get_top_products():

    return list(
        OrderItem.objects.filter(order__status=Order.Status.COMPLETED)
        .values("product__nomi")
        .annotate(
            jami_soni=Sum("soni"),
            jami_tushum=Sum(F("narxi") * F("soni"))
        ).order_by("-jami_soni")[:5]
    )


def get_sellers_report(sana_boshi=None, sana_oxiri=None):
    orders = Order.objects.all()

    if sana_boshi:
        orders = orders.filter(created_at__date__gte=sana_boshi)

    if sana_oxiri:
        orders = orders.filter(created_at__date__lte=sana_oxiri)

    sellers = list(
        orders.values(
            "customer__id",
            "customer__username"
        ).annotate(
            jami_buyurtmalar=Count("id"),
            yakunlangan_buyurtmalar=Count(
                "id",
                filter=Q(status="COMPLETED")
            ),
            bekor_qilingan_buyurtmalar=Count(
                "id",
                filter=Q(status="CANCELLED")
            ),
            savdo_summasi=Sum(
                "total_price",
                filter=Q(status="COMPLETED")
            )
        ).order_by("-savdo_summasi")
    )

    mahsulotlar = OrderItem.objects.filter(
        order__in=orders,
        order__status="COMPLETED"
    ).values(
        "order__customer_id"
    ).annotate(
        jami=Sum("soni")
    )

    mahsulotlar_dict = {
        item["order__customer_id"]: item["jami"]
        for item in mahsulotlar
    }

    for seller in sellers:
        seller["sotilgan_mahsulotlar"] = mahsulotlar_dict.get(
            seller["customer__id"], 0
        )
        seller["savdo_summasi"] = seller["savdo_summasi"] or 0

    return sellers

def get_period_report(sana_boshi=None, sana_oxiri=None):
    orders = Order.objects.filter(status="COMPLETED")

    if sana_boshi:
        orders = orders.filter(created_at__date__gte=sana_boshi)

    if sana_oxiri:
        orders = orders.filter(created_at__date__lte=sana_oxiri)

    buyurtmalar = orders.aggregate(
        soni=Count("id"),
        savdo=Sum("total_price")
    )

    items = OrderItem.objects.filter(order__in=orders)

    mahsulotlar = items.aggregate(
        jami=Sum("soni")
    )

    foyda = items.aggregate(
        jami=Sum(
            ExpressionWrapper(
                (F("narxi") - F("product__xarid_narxi")) * F("soni"),
                output_field=DecimalField(
                    max_digits=15,
                    decimal_places=2
                )
            )
        )
    )

    return {
        "buyurtmalar_soni": buyurtmalar["soni"] or 0,
        "savdo_summasi": buyurtmalar["savdo"] or 0,
        "sotilgan_mahsulotlar": mahsulotlar["jami"] or 0,
        "foyda": foyda["jami"] or 0,
    }


def get_period_sales_chart(sana_boshi=None, sana_oxiri=None):
    orders = Order.objects.filter(status="COMPLETED")

    if sana_boshi:
        orders = orders.filter(created_at__date__gte=sana_boshi)

    if sana_oxiri:
        orders = orders.filter(created_at__date__lte=sana_oxiri)

    data = orders.annotate(
        sana=TruncDate("created_at")
    ).values("sana").annotate(
        jami=Sum("total_price")
    ).order_by("sana")

    return {
        "labels": [
            item["sana"].strftime("%d.%m.%Y")
            for item in data
        ],
        "values": [
            float(item["jami"] or 0)
            for item in data
        ]
    }


def get_period_top_products(sana_boshi=None, sana_oxiri=None):
    items = OrderItem.objects.filter(order__status="COMPLETED")

    if sana_boshi:
        items = items.filter(order__created_at__date__gte=sana_boshi)

    if sana_oxiri:
        items = items.filter(order__created_at__date__lte=sana_oxiri)

    return items.values(
        "product__nomi"
    ).annotate(
        jami_soni=Sum("soni"),
        jami_savdo=Sum(
            ExpressionWrapper(
                F("narxi") * F("soni"),
                output_field=DecimalField(
                    max_digits=15,
                    decimal_places=2
                )
            )
        )
    ).order_by("-jami_soni")[:5]


def get_inventory_report(sana_boshi=None, sana_oxiri=None):
    movements = OmborMovement.objects.select_related("product").all()

    if sana_boshi:
        movements = movements.filter(
            created_at__date__gte=sana_boshi
        )

    if sana_oxiri:
        movements = movements.filter(
            created_at__date__lte=sana_oxiri
        )

    kirim = movements.filter(
        movement_type="IN"
    ).aggregate(
        jami=Sum("nechta"),
        soni=Count("id")
    )

    chiqim = movements.filter(
        movement_type="OUT"
    ).aggregate(
        jami=Sum("nechta"),
        soni=Count("id")
    )

    # Har bir mahsulot bo'yicha kirim va chiqim
    sana_filter = Q()

    if sana_boshi:
        sana_filter &= Q(movements__created_at__date__gte=sana_boshi)

    if sana_oxiri:
        sana_filter &= Q(movements__created_at__date__lte=sana_oxiri)

    mahsulotlar = Product.objects.annotate(
        jami_kirim=Sum(
            "movements__nechta",
            filter=Q(movements__movement_type="IN") & sana_filter
        ),
        jami_chiqim=Sum(
            "movements__nechta",
            filter=Q(movements__movement_type="OUT") & sana_filter
        )
    ).order_by("nomi")

    return {
        "jami_kirim": kirim["jami"] or 0,
        "jami_chiqim": chiqim["jami"] or 0,
        "kirim_harakatlari": kirim["soni"] or 0,
        "chiqim_harakatlari": chiqim["soni"] or 0,
        "harakatlar": movements.order_by("-created_at"),
        "mahsulotlar": mahsulotlar,
    }

def get_inventory_chart(sana_boshi=None, sana_oxiri=None):
    movements = OmborMovement.objects.all()

    if sana_boshi:
        movements = movements.filter(
            created_at__date__gte=sana_boshi
        )

    if sana_oxiri:
        movements = movements.filter(
            created_at__date__lte=sana_oxiri
        )

    kirim = movements.filter(
        movement_type="IN"
    ).aggregate(
        jami=Sum("nechta")
    )["jami"] or 0

    chiqim = movements.filter(
        movement_type="OUT"
    ).aggregate(
        jami=Sum("nechta")
    )["jami"] or 0

    return {
        "labels": ["Kirim", "Chiqim"],
        "values": [kirim, chiqim],
    }

def get_product_inventory_chart(sana_boshi=None, sana_oxiri=None):
    sana_filter = Q()

    if sana_boshi:
        sana_filter &= Q(movements__created_at__date__gte=sana_boshi)

    if sana_oxiri:
        sana_filter &= Q(movements__created_at__date__lte=sana_oxiri)

    mahsulotlar = Product.objects.annotate(
        jami_kirim=Sum(
            "movements__nechta",
            filter=Q(movements__movement_type="IN") & sana_filter
        ),
        jami_chiqim=Sum(
            "movements__nechta",
            filter=Q(movements__movement_type="OUT") & sana_filter
        )
    ).order_by("nomi")

    return {
        "labels": [p.nomi for p in mahsulotlar],
        "kirim": [p.jami_kirim or 0 for p in mahsulotlar],
        "chiqim": [p.jami_chiqim or 0 for p in mahsulotlar],
    }