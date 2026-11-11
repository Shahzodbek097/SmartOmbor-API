"""Inventory — REST API (replaces template views, same filters/rules)."""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsOmborchi
from .models import OmborMovement
from .serializers import OmborMovementSerializer


class OmborMovementViewSet(viewsets.ModelViewSet):
    """Only list + create (old code had no update/delete; model forbids edits)."""
    serializer_class = OmborMovementSerializer
    permission_classes = [IsAuthenticated, IsOmborchi]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = OmborMovement.objects.select_related("product", "user").order_by("-created_at")
        q = self.request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(product__nomi__icontains=q)
        movement_type = self.request.query_params.get("movement_type", "")
        if movement_type in ["IN", "OUT"]:
            qs = qs.filter(movement_type=movement_type)
        date_from = self.request.query_params.get("date_from", "")
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        date_to = self.request.query_params.get("date_to", "")
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        user_id = self.request.query_params.get("user", "")
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                instance = OmborMovement(**serializer.validated_data)
                instance.user = self.request.user
                instance.save()
                serializer.instance = instance
        except DjangoValidationError as e:
            raise DRFValidationError("; ".join(e.messages))
