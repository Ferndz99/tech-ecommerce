from rest_framework import serializers

from catalog.models import Category


class CategoryLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]
        read_only_fields = fields


class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "children"]

    def get_children(self, obj):
        qs = obj.get_children().filter(is_deleted=False)
        return CategoryTreeSerializer(qs, many=True).data


class CategoryDetailSerializer(serializers.ModelSerializer):
    parent = CategoryLightSerializer(read_only=True)
    children = CategoryLightSerializer(read_only=True, many=True, source="get_children")

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "parent",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
            "children",
        ]
        read_only_fields = fields


class CategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name", "parent", "is_active"]

        def validate_parent(self, value):
            if value and value.is_deleted:
                raise serializers.ValidationError(
                    "Cannot assign a deleted category as parent."
                )
            if value and not value.is_active:
                raise serializers.ValidationError(
                    "Parent category must be active."
                )
            return value
