from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "sales"

router = DefaultRouter()
router.register(r"orders", views.OrderViewSet, basename="order")

manager_router = DefaultRouter()
manager_router.register(r"orders", views.ManagerOrderViewSet, basename="manager-order")

urlpatterns = [
    path("", include(router.urls)),
    path("manager/", include(manager_router.urls)),
]
