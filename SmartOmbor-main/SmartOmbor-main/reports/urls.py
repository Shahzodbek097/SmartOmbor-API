from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("sellers/", views.SellersReportView.as_view(), name="sellers_report"),
    path("inventory/", views.InventoryReportView.as_view(), name="inventory_report"),
    path("export/dashboard/excel/", views.ExportDashboardExcelView.as_view(), name="export_dashboard_excel"),
    path("export/sellers/excel/", views.ExportSellersExcelView.as_view(), name="export_sellers_excel"),
    path("export/dashboard/pdf/", views.ExportDashboardPdfView.as_view(), name="export_dashboard_pdf"),
    path("export/sellers/pdf/", views.ExportSellersPdfView.as_view(), name="export_sellers_pdf"),
    path("export/inventory/excel/", views.ExportInventoryExcelView.as_view(), name="export_inventory_excel"),
    path("export/inventory/pdf/", views.ExportInventoryPdfView.as_view(), name="export_inventory_pdf"),
]
