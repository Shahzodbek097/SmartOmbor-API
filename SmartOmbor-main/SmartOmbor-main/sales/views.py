"""Sales — REST API (replaces template views, reuses sales/services.py)."""
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsSotuvchi, IsRahbar, IsSuperuserOrInGroups
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer
from .services import complete_order, cancel_order


class _OrderBase(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsSuperuserOrInGroups]
    groups = ("Sotuvchi", "Rahbar")
    # IsSuperuserOrInGroups already allows superuser always

    def get_queryset(self):
        qs = Order.objects.prefetch_related("items__product").select_related("customer").order_by("-created_at")
        # filters copied from old views
        q = self.request.query_params.get("q", "").strip()
        if q.isdigit():
            qs = qs.filter(id=int(q))
        holat = self.request.query_params.get("status", "")
        if holat in ["PENDING", "COMPLETED", "CANCELLED"]:
            qs = qs.filter(status=holat)
        date_from = self.request.query_params.get("date_from", "")
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        date_to = self.request.query_params.get("date_to", "")
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return qs

    def _check_owner(self, order):
        user = self.request.user
        is_rahbar = user.is_superuser or user.groups.filter(name="Rahbar").exists()
        if not is_rahbar and order.customer_id != user.id:
            raise PermissionDenied("Siz bu buyurtmani ko'rish huquqiga ega emassiz.")

    def get_object(self):
        obj = super().get_object()
        self._check_owner(obj)
        return obj


class OrderViewSet(_OrderBase):
    """Sotuvchi: own orders only (exactly like order_list)."""
    permission_classes = [IsAuthenticated, IsSotuvchi]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        # Sotuvchi sees only own; superuser/Rahbar with this endpoint also filtered to self
        # (manager view has its own endpoint below)
        return qs.filter(customer=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        out = OrderSerializer(order, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="finish")
    def finish(self, request, pk=None):
        order = self.get_object()
        try:
            complete_order(order.id, user=request.user)
        except DjangoValidationError as e:
            raise DRFValidationError("; ".join(e.messages))
        order.refresh_from_db()
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        order = self.get_object()
        try:
            cancel_order(order.id, user=request.user)
        except DjangoValidationError as e:
            raise DRFValidationError("; ".join(e.messages))
        order.refresh_from_db()
        return Response(OrderSerializer(order).data)

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status != "PENDING":
            raise DRFValidationError("Faqat kutilayotgan buyurtmalarni o'chirish mumkin.")
        oid = order.id
        order.delete()
        return Response({"deleted": oid}, status=status.HTTP_204_NO_CONTENT)


class ManagerOrderViewSet(_OrderBase):
    """Rahbar / superuser: all orders (manager_order_list)."""
    permission_classes = [IsAuthenticated, IsRahbar]
    http_method_names = ["get", "delete", "head", "options"]

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status != "PENDING":
            raise DRFValidationError("Faqat kutilayotgan buyurtmalarni o'chirish mumkin.")
        oid = order.id
        order.delete()
        return Response({"deleted": oid}, status=status.HTTP_204_NO_CONTENT)
