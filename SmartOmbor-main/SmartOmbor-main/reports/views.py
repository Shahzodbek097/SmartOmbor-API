"""Reports — REST API (replaces template views, reuses reports/services.py)."""
from django.utils.dateparse import parse_date
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsRahbar, IsSuperuserOrInGroups, IsAnyRole
from .services import (
    get_period_report, get_period_sales_chart, get_period_top_products,
    get_low_stock_products, get_sellers_report,
    get_inventory_report, get_inventory_chart, get_product_inventory_chart,
)


def _dates(request):
    date_from = request.query_params.get("date_from", "")
    date_to = request.query_params.get("date_to", "")
    return (
        parse_date(date_from) if date_from else None,
        parse_date(date_to) if date_to else None,
        date_from, date_to,
    )


def _roles(user):
    return {
        "is_rahbar": user.is_superuser or user.groups.filter(name="Rahbar").exists(),
        "is_omborchi": user.groups.filter(name="Omborchi").exists(),
        "is_sotuvchi": user.groups.filter(name="Sotuvchi").exists(),
    }


class DashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAnyRole]

    def get(self, request):
        boshlanish, tugash, date_from, date_to = _dates(request)
        from products.serializers import ProductSerializer
        low = get_low_stock_products()
        top = list(get_period_top_products(boshlanish, tugash))
        # Decimal -> float for JSON (services return Decimal)
        def _to_jsonable(obj):
            import decimal
            if isinstance(obj, decimal.Decimal):
                return float(obj)
            if isinstance(obj, dict):
                return {k: _to_jsonable(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_to_jsonable(v) for v in obj]
            return obj
        return Response(_to_jsonable({
            "davr": get_period_report(boshlanish, tugash),
            "davr_grafigi": get_period_sales_chart(boshlanish, tugash),
            "davr_top_mahsulotlar": top,
            "kam_qolgan": ProductSerializer(low, many=True).data,
            "sana_boshi": date_from,
            "sana_oxiri": date_to,
            **_roles(request.user),
        }))


class SellersReportView(APIView):
    permission_classes = [IsAuthenticated, IsRahbar]

    def get(self, request):
        boshlanish, tugash, date_from, date_to = _dates(request)
        data = get_sellers_report(boshlanish, tugash)
        import decimal
        def _clean(o):
            if isinstance(o, decimal.Decimal):
                return float(o)
            return o
        data = [{k: _clean(v) for k, v in row.items()} for row in data]
        return Response({"sotuvchilar": data, "sana_boshi": date_from, "sana_oxiri": date_to})


class InventoryReportView(APIView):
    permission_classes = [IsAuthenticated, IsRahbar]

    def get(self, request):
        boshlanish, tugash, date_from, date_to = _dates(request)
        report = get_inventory_report(boshlanish, tugash)
        from products.serializers import ProductSerializer
        return Response({
            "jami_kirim": report["jami_kirim"],
            "jami_chiqim": report["jami_chiqim"],
            "kirim_harakatlari": report["kirim_harakatlari"],
            "chiqim_harakatlari": report["chiqim_harakatlari"],
            "mahsulotlar": [
                {
                    "id": p.id, "nomi": p.nomi, "qoldiq": p.qoldiq,
                    "jami_kirim": p.jami_kirim or 0, "jami_chiqim": p.jami_chiqim or 0,
                } for p in report["mahsulotlar"]
            ],
            "inventory_chart": get_inventory_chart(boshlanish, tugash),
            "product_inventory_chart": get_product_inventory_chart(boshlanish, tugash),
            "sana_boshi": date_from, "sana_oxiri": date_to,
        })


# --- File exports (kept, but lazy-imported so API still works without openpyxl/reportlab) ---
from django.http import HttpResponse
from rest_framework.views import APIView as _APIView


class _ExportBase(_APIView):
    permission_classes = [IsAuthenticated, IsRahbar]

    def _require(self, mod):
        try:
            __import__(mod)
        except ImportError:
            from rest_framework.exceptions import APIException
            raise APIException(f"Export needs '{mod}' — install it: pip install {mod}")

    def get(self, request, *args, **kwargs):
        raise NotImplementedError


class ExportDashboardExcelView(_ExportBase):
    def get(self, request):
        self._require("openpyxl")
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
        boshlanish, tugash, date_from, date_to = _dates(request)
        report = get_period_report(boshlanish, tugash)
        wb = Workbook()
        ws = wb.active
        ws.title = "Dashboard hisoboti"
        ws.append(["Ko‘rsatkich", "Natija"])
        ws.append(["Buyurtmalar soni", report["buyurtmalar_soni"]])
        ws.append(["Savdo summasi", float(report["savdo_summasi"])])
        ws.append(["Sotilgan mahsulotlar", report["sotilgan_mahsulotlar"]])
        ws.append(["Foyda", float(report["foyda"])])
        ws.append(["Boshlanish sanasi", date_from or "Barcha vaqt"])
        ws.append(["Tugash sanasi", date_to or "Barcha vaqt"])
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        resp = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        resp["Content-Disposition"] = 'attachment; filename="dashboard_hisoboti.xlsx"'
        wb.save(resp)
        return resp


class ExportSellersExcelView(_ExportBase):
    def get(self, request):
        self._require("openpyxl")
        from openpyxl import Workbook
        boshlanish, tugash, date_from, date_to = _dates(request)
        sellers = get_sellers_report(boshlanish, tugash)
        wb = Workbook()
        ws = wb.active
        ws.title = "Sotuvchilar hisoboti"
        ws.append(["Sotuvchi", "Jami buyurtmalar", "Yakunlangan", "Bekor qilingan", "Sotilgan mahsulotlar", "Savdo summasi"])
        for s in sellers:
            ws.append([s["customer__username"], s["jami_buyurtmalar"], s["yakunlangan_buyurtmalar"], s["bekor_qilingan_buyurtmalar"], s["sotilgan_mahsulotlar"], float(s["savdo_summasi"])])
        resp = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        resp["Content-Disposition"] = 'attachment; filename="sotuvchilar_hisoboti.xlsx"'
        wb.save(resp)
        return resp


class ExportDashboardPdfView(_ExportBase):
    def get(self, request):
        self._require("reportlab")
        from io import BytesIO
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        boshlanish, tugash, date_from, date_to = _dates(request)
        report = get_period_report(boshlanish, tugash)
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
        styles = getSampleStyleSheet()
        els = [Paragraph("SmartOmbor — Bosh menu hisoboti", styles["Title"]), Spacer(1, 15)]
        data = [["Ko‘rsatkich", "Natija"], ["Buyurtmalar soni", report["buyurtmalar_soni"]], ["Savdo summasi", f'{report["savdo_summasi"]} so‘m'], ["Sotilgan mahsulotlar", report["sotilgan_mahsulotlar"]], ["Foyda", f'{report["foyda"]} so‘m']]
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        els.append(t)
        doc.build(els)
        resp = HttpResponse(buf.getvalue(), content_type="application/pdf")
        resp["Content-Disposition"] = 'attachment; filename="bosh_menu_hisoboti.pdf"'
        return resp


class ExportSellersPdfView(_ExportBase):
    def get(self, request):
        self._require("reportlab")
        from io import BytesIO
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        boshlanish, tugash, date_from, date_to = _dates(request)
        sellers = get_sellers_report(boshlanish, tugash)
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
        styles = getSampleStyleSheet()
        els = [Paragraph("SmartOmbor — Sotuvchilar hisoboti", styles["Title"]), Spacer(1, 15)]
        data = [["Sotuvchi", "Jami buyurtma", "Yakunlangan", "Bekor qilingan", "Sotilgan mahsulot", "Savdo summasi"]]
        for s in sellers:
            data.append([s["customer__username"], s["jami_buyurtmalar"], s["yakunlangan_buyurtmalar"], s["bekor_qilingan_buyurtmalar"], s["sotilgan_mahsulotlar"], f'{s["savdo_summasi"]} so‘m'])
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        els.append(t)
        doc.build(els)
        resp = HttpResponse(buf.getvalue(), content_type="application/pdf")
        resp["Content-Disposition"] = 'attachment; filename="sotuvchilar_hisoboti.pdf"'
        return resp


class ExportInventoryExcelView(_ExportBase):
    def get(self, request):
        self._require("openpyxl")
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        boshlanish, tugash, date_from, date_to = _dates(request)
        report = get_inventory_report(boshlanish, tugash)
        wb = Workbook()
        ws = wb.active
        ws.title = "Ombor hisoboti"
        ws.append(["Mahsulot", "Kirim", "Chiqim", "Qoldiq"])
        for p in report["mahsulotlar"]:
            ws.append([p.nomi, p.jami_kirim or 0, p.jami_chiqim or 0, p.qoldiq])
        ws.append(["Jami kirim", report["jami_kirim"], "", ""])
        ws.append(["Jami chiqim", report["jami_chiqim"], "", ""])
        resp = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        resp["Content-Disposition"] = 'attachment; filename="ombor_hisoboti.xlsx"'
        wb.save(resp)
        return resp


class ExportInventoryPdfView(_ExportBase):
    def get(self, request):
        self._require("reportlab")
        from io import BytesIO
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        boshlanish, tugash, date_from, date_to = _dates(request)
        report = get_inventory_report(boshlanish, tugash)
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        els = [Paragraph("SMARTOMBOR - OMBOR HISOBOTI", styles["Title"]), Spacer(1, 15),
               Paragraph(f"Jami kirim: {report['jami_kirim']} dona, Jami chiqim: {report['jami_chiqim']} dona", styles["Normal"]), Spacer(1, 15)]
        data = [["№", "Mahsulot nomi", "Kirim", "Chiqim", "Joriy qoldiq"]]
        for i, p in enumerate(report["mahsulotlar"], 1):
            data.append([i, p.nomi, p.jami_kirim or 0, p.jami_chiqim or 0, p.qoldiq])
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#343A40")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        els.append(t)
        doc.build(els)
        resp = HttpResponse(buf.getvalue(), content_type="application/pdf")
        resp["Content-Disposition"] = 'attachment; filename="ombor_hisoboti.pdf"'
        return resp
