from rest_framework import serializers

from catalog.models.attribute import Attribute, AttributeValue
from catalog.utils import normalize_spec_value


class AttributeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ["name"]


class AttributeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ["id", "name"]


class AttributeValueWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        fields = ["attribute", "value"]

    def validate_value(self, value):
        return normalize_spec_value(value)


class AttributeValueDetailSerializer(serializers.ModelSerializer):
    attribute = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = AttributeValue
        fields = ["id", "attribute", "value"]
