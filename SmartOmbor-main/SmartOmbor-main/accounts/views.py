"""Accounts — REST API (replaces template views, same rules)."""
from django.contrib.auth.models import User
from django.db import models
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsRahbar
from .serializers import (
    MeSerializer, ProfileUpdateSerializer, UserSerializer,
    UserCreateSerializer, UserUpdateSerializer, ChangePasswordSerializer,
)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)

    def patch(self, request):
        s = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(MeSerializer(request.user).data)

    def put(self, request):
        return self.patch(request)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = ChangePasswordSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        request.user.set_password(s.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response({"detail": "Parol yangilandi."})


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsRahbar]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        qs = User.objects.all().order_by("-date_joined")
        if not self.request.user.is_superuser:
            qs = qs.filter(is_superuser=False)
        q = self.request.query_params.get("q", "")
        if q:
            qs = qs.filter(
                models.Q(username__icontains=q)
                | models.Q(first_name__icontains=q)
                | models.Q(last_name__icontains=q)
                | models.Q(email__icontains=q)
            )
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        s = UserUpdateSerializer(instance, data=request.data, partial=partial, context={"request": request})
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response(UserSerializer(user).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="toggle-status")
    def toggle_status(self, request, pk=None):
        user = self.get_object()
        if user.is_superuser and not request.user.is_superuser:
            raise DRFValidationError("Superuser holatini o'zgartirish mumkin emas.")
        if user == request.user:
            raise DRFValidationError("O'zingizning hisobingizni o'chira olmaysiz.")
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        return Response(UserSerializer(user).data)
