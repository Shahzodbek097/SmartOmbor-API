from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class MeSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_active", "is_superuser", "role", "groups", "date_joined"]
        read_only_fields = fields

    def get_role(self, obj):
        g = obj.groups.first()
        return g.name if g else None

    def get_groups(self, obj):
        return [g.name for g in obj.groups.all()]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def validate_email(self, value):
        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu email allaqachon ishlatilgan.")
        return value


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_active", "is_superuser", "role", "date_joined"]
        read_only_fields = fields

    def get_role(self, obj):
        g = obj.groups.first()
        return g.name if g else None


class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    password = serializers.CharField(write_only=True, min_length=4)
    role = serializers.CharField()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Bu login allaqachon mavjud.")
        return value

    def validate_role(self, value):
        allowed = ["Omborchi", "Sotuvchi"] + (["Rahbar"] if self.context["request"].user.is_superuser else [])
        if value not in allowed:
            raise serializers.ValidationError(f"Role must be one of {allowed}")
        if not Group.objects.filter(name=value).exists():
            from django.core.management import call_command
            from io import StringIO
            call_command("migrate", run_syncdb=True, verbosity=0, stdout=StringIO())
            Group.objects.get_or_create(name=value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        role_name = validated_data.pop("role")
        user = User.objects.create_user(password=password, **validated_data)
        group = Group.objects.get(name=role_name)
        user.groups.set([group])
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    role = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active", "role"]

    def validate_role(self, value):
        allowed = ["Omborchi", "Sotuvchi"] + (["Rahbar"] if self.context["request"].user.is_superuser else [])
        if value not in allowed:
            raise serializers.ValidationError(f"Role must be one of {allowed}")
        Group.objects.get_or_create(name=value)
        return value

    def update(self, instance, validated_data):
        role_name = validated_data.pop("role", None)
        if instance.is_superuser and not self.context["request"].user.is_superuser:
            raise serializers.ValidationError("Superuser ma'lumotlarini tahrirlash mumkin emas.")
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if role_name:
            instance.groups.set([Group.objects.get(name=role_name)])
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Joriy parol noto'g'ri.")
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context["request"].user)
        return value
