from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "products"

router = DefaultRouter()
router.register(r"categories", views.CategoryViewSet, basename="category")
router.register(r"products", views.ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
]

# Backwards-compatible names (used by frontend redirects/tests if any)
# Old template paths are gone; API is at /api/products/... and /api/categories/...
