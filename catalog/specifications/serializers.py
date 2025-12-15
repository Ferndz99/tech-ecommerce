from rest_framework import serializers

from catalog.models.product import Product
from catalog.models.specification import ProductSpecification, Specification


class SpecificationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = ["id", "name"]


class SpecificationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = ["name"]


class ProductSpecificationDetailSerializer(serializers.ModelSerializer):
    specification = serializers.StringRelatedField()

    class Meta:
        model = ProductSpecification
        fields = ["id", "specification", "value"]


class ProductSpecificationWriteSerializer(serializers.ModelSerializer):
    specification_id = serializers.PrimaryKeyRelatedField(
        queryset=Specification.objects.all(), source="specification"
    )

    class Meta:
        model = ProductSpecification
        fields = ["specification_id", "value"]



class ProductSpecificationDirectWriteSerializer(serializers.ModelSerializer):
    specification_id = serializers.PrimaryKeyRelatedField(
        queryset=Specification.objects.all(),
        source="specification",
    )

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = ProductSpecification
        fields = ["product", "specification_id", "value"]
