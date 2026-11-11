from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView,
)


def root(request):
    return JsonResponse({
        "message": "SmartOmbor API",
        "docs": "/api/docs/",
        "schema": "/api/schema/",
        "frontend_note": "Frontend is separate — run ../frontend (see frontend/README.md)",
    })


def health(request):
    return JsonResponse({"status": "ok", "service": "SmartOmbor API"})


urlpatterns = [
    path("", root, name="root"),
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("health", health, name="health_noslash"),
    # --- REST API (frontend lives in ../frontend) ---
    path("api/", include("products.urls")),
    path("api/", include("sales.urls")),
    path("api/", include("inventory.urls")),
    path("api/", include("accounts.urls")),
    path("api/reports/", include("reports.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
