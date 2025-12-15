from rest_framework import serializers

from catalog.models.category import Category


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
    level = serializers.IntegerField(read_only=True)
    ancestors = serializers.SerializerMethodField()  # Breadcrumb
    descendants_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "level",
            "parent",
            "ancestors",
            "descendants_count",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
            "children",
        ]
        read_only_fields = fields

    def get_ancestors(self, obj):
        """Para breadcrumbs: Home > Electronics > Laptops"""
        return CategoryLightSerializer(obj.get_ancestors(), many=True).data

    def get_descendants_count(self, obj) -> int:
        """Total de subcategorías (incluyendo anidadas)"""
        return obj.get_descendant_count()


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
            raise serializers.ValidationError("Parent category must be active.")
        return value

    def validate(self, attrs):
        """Validación de ciclos circulares"""
        parent = attrs.get("parent")
        instance = self.instance  # Existe solo en update/patch

        if parent and instance:
            # Prevenir auto-referencia
            if parent == instance:
                raise serializers.ValidationError(
                    {"parent": "A category cannot be its own parent."}
                )

            # Prevenir ciclos (asignar descendiente como padre)
            if parent.is_descendant_of(instance, include_self=True):
                raise serializers.ValidationError(
                    {
                        "parent": "Cannot assign a descendant as parent (circular reference)."
                    }
                )

        return attrs


class CategoryPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class CategoryAdminListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "is_active", "is_deleted", "created_at"]
