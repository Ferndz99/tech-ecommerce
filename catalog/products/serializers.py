from django.db import transaction
from django.utils.text import slugify

from rest_framework import serializers

from taggit.serializers import TagListSerializerField, TaggitSerializer


from catalog.attributes.serializers import AttributeValueDetailSerializer
from catalog.models.attribute import AttributeValue
from catalog.models.product import Product
from catalog.models.product_meta import ProductMeta
from catalog.models.product_image import ProductImage
from catalog.models.product_variant import ProductVariant
from catalog.models.specification import ProductSpecification
from catalog.specifications.serializers import (
    ProductSpecificationDetailSerializer,
    ProductSpecificationWriteSerializer,
)


# PRODUCT IMAGE
class ProductImageDetailSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = [
            "id",
            "image",
            "thumbnail_url",
            "is_primary",
            "created_at",
            "updated_at",
        ]

    def get_thumbnail_url(self, obj):
        relative_url = obj.thumbnail_url

        if not relative_url:
            return None

        request = self.context.get("request")

        if request is not None:
            return request.build_absolute_uri(relative_url)

        return relative_url


class ProductImagePublicSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = [
            "id",
            "image",
            "thumbnail_url",
            "is_primary",
        ]

    def get_thumbnail_url(self, obj):
        relative_url = obj.thumbnail_url

        if not relative_url:
            return None

        request = self.context.get("request")

        if request is not None:
            return request.build_absolute_uri(relative_url)

        return relative_url


class ProductImageWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["is_primary", "image"]


# PRODUCT META
class ProductMetaDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMeta
        fields = ["product_variant", "qr_code", "weight", "dimensions"]


class ProductMetaWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMeta
        fields = ["weight", "dimensions"]


# PRODUCT VARIANT
class ProductVariantListSerializer(serializers.ModelSerializer):
    brand = serializers.CharField(source="product.brand.name")
    category = serializers.CharField(source="product.category.name")
    description = serializers.CharField(source="product.description")
    specifications = ProductSpecificationDetailSerializer(
        source="product.specifications", many=True
    )
    meta = ProductMetaDetailSerializer(read_only=True)
    images = ProductImagePublicSerializer(read_only=True, many=True)
    tags = TagListSerializerField()
    attributes = AttributeValueDetailSerializer(read_only=True, many=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "price",
            "stock",
            "description",
            "brand",
            "category",
            "tags",
            "attributes",
            "specifications",
            "meta",
            "images",
            "specifications",
        ]


class ProductVariantAdminListSerializer(serializers.ModelSerializer):
    brand = serializers.CharField(source="product.brand.name")
    category = serializers.CharField(source="product.category.name")
    description = serializers.CharField(source="product.description")
    specifications = ProductSpecificationDetailSerializer(
        source="product.specifications", many=True
    )
    meta = ProductMetaDetailSerializer(read_only=True)
    images = ProductImageDetailSerializer(read_only=True, many=True)
    tags = TagListSerializerField()
    attributes = AttributeValueDetailSerializer(read_only=True, many=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "price",
            "stock",
            "description",
            "brand",
            "category",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
            "tags",
            "attributes",
            "meta",
            "images",
            "specifications",
        ]


class ProductVariantDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    meta = ProductMetaDetailSerializer(read_only=True)
    images = ProductImageDetailSerializer(read_only=True, many=True)
    tags = TagListSerializerField()
    attributes = AttributeValueDetailSerializer(read_only=True, many=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "slug",
            "name",
            "sku",
            "price",
            "stock",
            "attributes",
            "tags",
            "is_active",
            "is_deleted",
            "meta",
            "images",
            "created_at",
            "updated_at",
        ]


class ProductVariantPublicSerializer(TaggitSerializer, serializers.ModelSerializer):
    meta = ProductMetaDetailSerializer(read_only=True)
    images = ProductImagePublicSerializer(read_only=True, many=True)
    tags = TagListSerializerField()
    attributes = AttributeValueDetailSerializer(read_only=True, many=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "slug",
            "name",
            "sku",
            "price",
            "stock",
            "attributes",
            "tags",
            "meta",
            "images",
        ]


class ProductVariantWriteSerializer(TaggitSerializer, serializers.ModelSerializer):
    attribute_value_ids = serializers.ListField(
        child=serializers.IntegerField(), required=True
    )

    tags = TagListSerializerField(required=False)

    meta = ProductMetaWriteSerializer(required=True)

    images = ProductImageWriteSerializer(many=True, required=False)

    class Meta:
        model = ProductVariant
        fields = [
            "sku",
            "price",
            "stock",
            "attribute_value_ids",
            "tags",
            "meta",
            "images",
        ]
        extra_kwargs = {"stock": {"required": True}}

    @transaction.atomic
    def create(self, validated_data):
        attr_ids = validated_data.pop("attribute_value_ids", [])
        meta = validated_data.pop("meta", None)
        images = validated_data.pop("images", [])
        tags = validated_data.pop("tags", [])

        product = self.context["product"]

        variant = ProductVariant.objects.create(product=product, **validated_data)

        # if attr_ids:
        #     variant.attributes.set(AttributeValue.objects.filter(id__in=attr_ids))

        if attr_ids:
            attrs = AttributeValue.objects.filter(id__in=attr_ids)
            variant.attributes.set(attrs)

            variant.name = self._generate_variant_name(product, attrs)
            variant.slug = self._generate_variant_slug(product, attrs)
            variant.save(update_fields=["name", "slug"])

        if tags:
            variant.tags.set(tags)

        if meta:
            meta_instance = ProductMeta.objects.create(
                product_variant=variant,
                weight=meta.get("weight"),
                dimensions=meta.get("dimensions"),
            )

            if not meta_instance.qr_code:
                meta_instance._generate_qr_code()
                meta_instance.save(update_fields=["qr_code"])

        for img in images:
            ProductImage.objects.create(
                product_variant=variant,
                image=img["image"],
                is_primary=img.get("is_primary", False),
            )

        return variant

    def _generate_variant_slug(self, product, attrs):
        base = slugify(product.name)
        attr_parts = [slugify(a.value) for a in attrs]
        return "-".join([base] + attr_parts)

    def _generate_variant_name(self, product, attrs):
        attr_parts = [a.value for a in attrs.order_by("attribute__name")]
        return f"{product.name} – " + " – ".join(attr_parts)


# PRODUCT BASE
class ProductDetailSerializer(serializers.ModelSerializer):
    variants = ProductVariantDetailSerializer(read_only=True, many=True)
    brand = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    specifications = ProductSpecificationDetailSerializer(read_only=True, many=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "brand",
            "description",
            "specifications",
            "created_at",
            "updated_at",
            "variants",
        ]


class ProductPublicSerializer(serializers.ModelSerializer):
    variants = ProductVariantPublicSerializer(read_only=True, many=True)
    brand = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    specifications = ProductSpecificationWriteSerializer(read_only=True, many=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "brand",
            "specifications",
            "variants",
        ]


class ProductWriteSerializer(serializers.ModelSerializer):
    # brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all())
    # category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    variants = ProductVariantWriteSerializer(many=True, required=False, write_only=True)
    specifications = ProductSpecificationWriteSerializer(
        many=True, required=False, write_only=True
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "brand",
            "category",
            "variants",
            "specifications",
        ]

    def to_internal_value(self, data):
        # Eliminar variantes desde PUT/PATCH
        if self.instance is not None and "variants" in data:
            data = data.copy()
            data.pop("variants")

        if self.instance is not None and "specifications" in data:
            data = data.copy()
            data.pop("specifications")

        return super().to_internal_value(data)

    @transaction.atomic
    def create(self, validated_data):
        print(validated_data)
        variants_data = validated_data.pop("variants", [])
        specs_data = validated_data.pop("specifications", [])

        # product = Product.objects.create(**validated_data)
        product = super().create(validated_data)

        # Specifications
        for spec in specs_data:
            ProductSpecification.objects.create(product=product, **spec)

        # Variants (delegado correctamente al serializer)
        for variant_data in variants_data:
            serializer = ProductVariantWriteSerializer(
                data=variant_data, context={"product": product}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Actualiza únicamente los campos del producto base.
        Ignora completamente variantes y especificaciones.
        """

        partial = self.context.get("partial", False)

        validated_data.pop("variants", None)
        validated_data.pop("specifications", None)

        if "name" in validated_data:
            instance.name = validated_data.get("name", instance.name)
        if "description" in validated_data:
            instance.description = validated_data.get(
                "description", instance.description
            )
        if "brand" in validated_data:
            instance.brand = validated_data.get("brand", instance.brand)
        if "category" in validated_data:
            instance.category = validated_data.get("category", instance.category)

        instance.save()
        return instance
