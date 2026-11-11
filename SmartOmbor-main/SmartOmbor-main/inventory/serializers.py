from rest_framework import serializers
from .models import OmborMovement


class OmborMovementSerializer(serializers.ModelSerializer):
    product_nomi = serializers.CharField(source="product.nomi", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True, default=None)

    class Meta:
        model = OmborMovement
        fields = [
            "id", "product", "product_nomi",
            "user", "user_username",
            "movement_type", "nechta", "sababi", "created_at",
        ]
        read_only_fields = ["id", "user", "user_username", "product_nomi", "created_at"]

    def create(self, validated_data):
        # user is injected by the view (request.user), stock logic stays in model.save()
        return OmborMovement.objects.create(**validated_data)
