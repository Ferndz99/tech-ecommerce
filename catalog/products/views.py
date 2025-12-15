from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.filters import SearchFilter, OrderingFilter


from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiExample,
    OpenApiParameter,
    inline_serializer,
)

from catalog.common.docs.errors import error_401, error_403, error_404, error_500
from catalog.common.mixins import BaseAPIViewSet, LifeCycleActionMixin
from catalog.common.serializers import ProblemDetailsSerializer
from catalog.models.product import Product
from catalog.models.product_variant import ProductVariant
from catalog.products.filters import ProductVariantFilter
from catalog.products.serializers import (
    ProductVariantPublicSerializer,
    ProductWriteSerializer,
    ProductDetailSerializer,
    ProductPublicSerializer,
    ProductVariantWriteSerializer,
    ProductVariantDetailSerializer,
    ProductVariantListSerializer,
    ProductVariantAdminListSerializer,
)


TAG_PRODUCT = "Product"
TAG_PRODUCT_VARIANT = "Product Variant"


@extend_schema_view(
    create=extend_schema(
        tags=[TAG_PRODUCT],
        summary="Create a new product",
        description="Creates a new product with its base information.",
        request=ProductWriteSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Product created successfully",
                response=ProductDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="ProductCreated",
                        summary="Successful product creation",
                        value={
                            "id": 1,
                            "name": "prod test 1",
                            "slug": "prod-test-1-1",
                            "category": "Category",
                            "brand": "Brand",
                            "description": "Some value",
                            "specifications": [
                                {
                                    "id": 1,
                                    "specification": "Spec name",
                                    "value": "value",
                                }
                            ],
                            "created_at": "2025-12-14 17:48:53",
                            "updated_at": "2025-12-14 17:48:53",
                            "variants": [],
                        },
                    )
                ],
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Validation error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="ValidationError",
                        summary="Invalid product payload",
                        value={
                            "type": "https://httpstatuses.com/400",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "/api/v1/products/",
                            "detail": "The submitted data failed validation.",
                            "errors": [
                                {"field": "name", "message": "This field is required."},
                                {
                                    "field": "brand",
                                    "message": "This field is required.",
                                },
                                {
                                    "field": "category",
                                    "message": "This field is required.",
                                },
                            ],
                        },
                    )
                ],
            ),
            **error_401("/api/v1/products/"),
            **error_403("/api/v1/products/"),
            **error_500("/api/v1/products/"),
        },
    ),
    list=extend_schema(
        tags=[TAG_PRODUCT],
        summary="List products",
        description=(
            "Returns a list of products.\n\n"
            "- **Public users** receive a public representation.\n"
            "- **Admin users** receive full product details.\n\n"
            "Supports search and ordering."
        ),
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search by name, slug or variant slug",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description="Order results by fields such as name or created_at",
                required=False,
                type=str,
            ),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Product list (public)",
                response=ProductPublicSerializer,
                examples=[
                    OpenApiExample(
                        name="PublicProductList",
                        summary="Public list example",
                        value=[
                            {
                                "id": 36,
                                "name": "product test",
                                "slug": "prod-test",
                                "category": "Category",
                                "brand": "Brand",
                                "description": "lorem ipsum...",
                                "specifications": [
                                    {
                                        "id": 29,
                                        "specification": "Spec name",
                                        "value": "value",
                                    }
                                ],
                                "created_at": "2025-12-14 20:51:04",
                                "updated_at": "2025-12-14 20:53:24",
                                "variants": [],
                            },
                            {
                                "id": 36,
                                "name": "product test 1",
                                "slug": "prod-test-1",
                                "category": "Category",
                                "brand": "Brand",
                                "description": "lorem ipsum...",
                                "specifications": [
                                    {
                                        "id": 29,
                                        "specification": "Spec name",
                                        "value": "value",
                                    }
                                ],
                                "created_at": "2025-12-14 20:51:04",
                                "updated_at": "2025-12-14 20:53:24",
                                "variants": [],
                            },
                        ],
                    )
                ],
            ),
        },
    ),
    retrieve=extend_schema(
        tags=[TAG_PRODUCT],
        summary="Retrieve a product",
        description=(
            "Returns the details of a product identified by its slug.\n\n"
            "- **Public users** receive `ProductPublicSerializer`.\n"
            "- **Admin users** receive `ProductDetailSerializer`.\n\n"
            "Includes variants, attributes, images and specifications."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Product detail (public)",
                response=ProductPublicSerializer,
                examples=[
                    OpenApiExample(
                        name="PublicProductDetail",
                        summary="Public product detail",
                        value={
                            "id": 36,
                            "name": "product test",
                            "slug": "prod-test",
                            "category": "Category",
                            "brand": "Brand",
                            "description": "lorem ipsum...",
                            "specifications": [
                                {
                                    "id": 29,
                                    "specification": "Spec name",
                                    "value": "value",
                                }
                            ],
                            "created_at": "2025-12-14 20:51:04",
                            "updated_at": "2025-12-14 20:53:24",
                            "variants": [],
                        },
                    )
                ],
            ),
        },
    ),
    partial_update=extend_schema(
        tags=[TAG_PRODUCT],
        summary="Partially update a product",
        description="Allows partial updates to a product.",
        request=ProductWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Product partially updated",
                response=ProductDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="",
                        summary="",
                        value={
                            "id": 36,
                            "name": "prod test 2",
                            "slug": "prod-test-2",
                            "category": "Laptop",
                            "brand": "Asus",
                            "description": "mod 2",
                            "specifications": [
                                {
                                    "id": 29,
                                    "specification": "Spec name",
                                    "value": "value",
                                }
                            ],
                            "created_at": "2025-12-14 20:51:04",
                            "updated_at": "2025-12-14 20:53:24",
                            "variants": [],
                        },
                    )
                ],
            ),
            **error_401("/api/v1/products/{slug}/"),
            **error_403("/api/v1/products/{slug}/"),
            **error_404("/api/v1/products/{slug}/"),
            **error_500("/api/v1/products/{slug}/"),
        },
    ),
    update=extend_schema(
        tags=[TAG_PRODUCT],
        summary="Update a product",
        description="Fully updates a product.",
        request=ProductWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Product updated",
                response=ProductDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="",
                        summary="",
                        value={
                            "id": 36,
                            "name": "prod test 2",
                            "slug": "prod-test-2",
                            "category": "Laptop",
                            "brand": "Asus",
                            "description": "mod 2",
                            "specifications": [
                                {
                                    "id": 29,
                                    "specification": "Spec name",
                                    "value": "value",
                                }
                            ],
                            "created_at": "2025-12-14 20:51:04",
                            "updated_at": "2025-12-14 20:53:24",
                            "variants": [],
                        },
                    )
                ],
            ),
            **error_401("/api/v1/products/{slug}/"),
            **error_403("/api/v1/products/{slug}/"),
            **error_404("/api/v1/products/{slug}/"),
            **error_500("/api/v1/products/{slug}/"),
        },
    ),
    destroy=extend_schema(
        tags=[TAG_PRODUCT],
        summary="Soft delete a product",
        description="Marks the product as deleted instead of permanently removing it.",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Product soft-deleted successfully"
            ),
            **error_401("/api/v1/products/{slug}/"),
            **error_403("/api/v1/products/{slug}/"),
            **error_404("/api/v1/products/{slug}/"),
            **error_500("/api/v1/products/{slug}/"),
        },
    ),
    create_variant=extend_schema(
        tags=[TAG_PRODUCT],
        summary="Create a variant for a product",
        description=(
            "Creates a new variant for the specified product.\n\n"
            "- Only **admin users** can perform this action.\n"
            "- Variant is linked automatically to the product."
        ),
        request=ProductVariantWriteSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Product variant created",
                response=ProductVariantDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="VariantCreated",
                        summary="Product variant created",
                        value={
                            "id": 26,
                            "slug": "prod-test-128gb-black",
                            "name": "prod test - Black - 128GB",
                            "sku": "PROD-123",
                            "price": 12000.0,
                            "stock": 323,
                            "attributes": [
                                {"id": 2, "attribute": "Storage", "value": "128GB"},
                                {"id": 1, "attribute": "Colour", "value": "Black"},
                            ],
                            "tags": [],
                            "is_active": True,
                            "is_deleted": False,
                            "meta": {
                                "product_variant": 26,
                                "qr_code": "http://image.com/",
                                "weight": "120 gr",
                                "dimensions": "123x12x12",
                            },
                            "images": [],
                            "created_at": "2025-12-15 12:42:35",
                            "updated_at": "2025-12-15 12:42:35",
                        },
                    )
                ],
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Validation error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="ValidationError",
                        summary="Invalid product payload",
                        value={
                            "type": "https://httpstatuses.com/400",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "/api/v1/products/prod-test-2/create_variant/",
                            "detail": "The submitted data failed validation.",
                            "errors": [
                                {"field": "sku", "message": "This field is required."},
                                {
                                    "field": "price",
                                    "message": "This field is required.",
                                },
                                {
                                    "field": "stock",
                                    "message": "This field is required.",
                                },
                                {
                                    "field": "attribute_value_ids",
                                    "message": "This field is required.",
                                },
                                {"field": "meta", "message": "This field is required."},
                            ],
                        },
                    )
                ],
            ),
            **error_401("/api/v1/products/{slug}/create_variant/"),
            **error_403("/api/v1/products/{slug}/create_variant/"),
            **error_404("/api/v1/products/{slug}/create_variant/"),
            **error_500("/api/v1/products/{slug}/create_variant/"),
        },
    ),
)
class ProductViewSet(BaseAPIViewSet):
    queryset = Product.objects.prefetch_related(
        "variants__attributes__attribute",
        "variants__images",
        "variants__meta",
        "specifications__specification",
    )
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    public_list_serializer_class = ProductPublicSerializer
    admin_list_serializer_class = ProductDetailSerializer
    write_serializer_class = ProductWriteSerializer
    admin_read_serializer_class = ProductDetailSerializer
    public_read_serializer_class = ProductPublicSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "slug", "variants__slug"]

    def get_permissions(self):
        if self.action in ["create_variant"]:
            return [IsAdminUser()]
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def create_variant(self, request, slug=None):
        product = self.get_object()
        serializer = ProductVariantWriteSerializer(
            data=request.data,
            context={"product": product, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        variant = serializer.save()

        output_serializer = ProductVariantDetailSerializer(
            variant, context={"request": request}
        )

        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(
        tags=[TAG_PRODUCT_VARIANT],
        summary="List product variants",
        description=(
            "Returns a list of product variants.\n\n"
            "- **Public users** receive a simplified representation.\n"
            "- **Admin users** receive full variant data.\n\n"
            "Supports search and ordering."
        ),
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search by variant slug or name",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description="Order by price, stock or creation date",
                required=False,
                type=str,
                enum=[
                    "price",
                    "-price",
                    "stock",
                    "-stock",
                    "created_at",
                    "-created_at",
                ],
            ),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Variant list (public)",
                response=ProductVariantListSerializer,
            ),
            "200 (admin)": OpenApiResponse(
                description="Variant list (admin)",
                response=ProductVariantAdminListSerializer,
            ),
            **error_500("/api/v1/product-variants/"),
        },
    ),
    retrieve=extend_schema(
        tags=[TAG_PRODUCT_VARIANT],
        summary="Retrieve a product variant",
        description=(
            "Returns detailed information about a product variant identified by its slug.\n\n"
            "- **Public users** receive `ProductVariantPublicSerializer`.\n"
            "- **Admin users** receive `ProductVariantDetailSerializer`.\n\n"
            "Includes attributes, images and meta data."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Variant detail (public)",
                response=ProductVariantPublicSerializer,
            ),
            "200 (admin)": OpenApiResponse(
                description="Variant detail (admin)",
                response=ProductVariantDetailSerializer,
            ),
            **error_404("/api/v1/product-variants/{slug}/"),
            **error_500("/api/v1/product-variants/{slug}/"),
        },
    ),
    update=extend_schema(
        tags=[TAG_PRODUCT_VARIANT],
        summary="Update a product variant",
        description="Fully updates a product variant.",
        request=ProductVariantWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Variant updated successfully",
                response=ProductVariantDetailSerializer,
            ),
            **error_401("/api/v1/product-variants/{slug}/"),
            **error_403("/api/v1/product-variants/{slug}/"),
            **error_404("/api/v1/product-variants/{slug}/"),
            **error_500("/api/v1/product-variants/{slug}/"),
        },
    ),
    partial_update=extend_schema(
        tags=[TAG_PRODUCT_VARIANT],
        summary="Partially update a product variant",
        description="Allows partial updates to a product variant.",
        request=ProductVariantWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Variant partially updated",
                response=ProductVariantDetailSerializer,
            ),
            **error_401("/api/v1/product-variants/{slug}/"),
            **error_403("/api/v1/product-variants/{slug}/"),
            **error_404("/api/v1/product-variants/{slug}/"),
            **error_500("/api/v1/product-variants/{slug}/"),
        },
    ),
    destroy=extend_schema(
        tags=[TAG_PRODUCT_VARIANT],
        summary="Soft delete a product variant",
        description="Marks a product variant as deleted without permanently removing it.",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Variant soft-deleted successfully"
            ),
            **error_401("/api/v1/product-variants/{slug}/"),
            **error_403("/api/v1/product-variants/{slug}/"),
            **error_404("/api/v1/product-variants/{slug}/"),
            **error_500("/api/v1/product-variants/{slug}/"),
        },
    ),
    deleted=extend_schema(
        tags=[TAG_PRODUCT_VARIANT],
        summary="List deleted product variants",
        description=(
            "Returns a list of soft-deleted product variants.\n\n"
            "- **Admin only** endpoint."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Deleted variants list",
                response=ProductVariantAdminListSerializer,
            ),
            **error_401("/api/v1/product-variants/deleted/"),
            **error_403("/api/v1/product-variants/deleted/"),
            **error_500("/api/v1/product-variants/deleted/"),
        },
    ),
    activate=extend_schema(
        tags=[TAG_PRODUCT_VARIANT],
        summary="Activate a product variant",
        description="Marks a product variant as active.",
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Variant activated successfully",
                response=ProductVariantDetailSerializer,
            ),
            **error_401("/api/v1/product-variants/{slug}/activate/"),
            **error_403("/api/v1/product-variants/{slug}/activate/"),
            **error_404("/api/v1/product-variants/{slug}/activate/"),
            **error_500("/api/v1/product-variants/{slug}/activate/"),
        },
    ),
    deactivate=extend_schema(
        tags=[TAG_PRODUCT_VARIANT],
        summary="Deactivate a product variant",
        description="Marks a product variant as inactive.",
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Variant deactivated successfully",
                response=ProductVariantDetailSerializer,
            ),
            **error_401("/api/v1/product-variants/{slug}/deactivate/"),
            **error_403("/api/v1/product-variants/{slug}/deactivate/"),
            **error_404("/api/v1/product-variants/{slug}/deactivate/"),
            **error_500("/api/v1/product-variants/{slug}/deactivate/"),
        },
    ),
    restore=extend_schema(
        tags=[TAG_PRODUCT_VARIANT],
        summary="Restore a deleted product variant",
        description="Restores a soft-deleted product variant.",
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Variant restored successfully",
                response=ProductVariantDetailSerializer,
            ),
            **error_401("/api/v1/product-variants/{slug}/restore/"),
            **error_403("/api/v1/product-variants/{slug}/restore/"),
            **error_404("/api/v1/product-variants/{slug}/restore/"),
            **error_500("/api/v1/product-variants/{slug}/restore/"),
        },
    ),
    hard_delete=extend_schema(
        tags=[TAG_PRODUCT_VARIANT],
        summary="Permanently delete a product variant",
        request=inline_serializer(
            name="HardDeleteConfirmRequest",
            fields={"confirm": serializers.BooleanField()},
        ),
        description=(
            "Permanently removes a product variant from the database.\n\n"
            "- **Admin only**\n"
            "- **Irreversible action**"
        ),
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Variant permanently deleted"
            ),
            **error_401("/api/v1/product-variants/{slug}/hard_delete/"),
            **error_403("/api/v1/product-variants/{slug}/hard_delete/"),
            **error_404("/api/v1/product-variants/{slug}/hard_delete/"),
            **error_500("/api/v1/product-variants/{slug}/hard_delete/"),
        },
    ),
)
class ProductVariantViewSet(LifeCycleActionMixin, BaseAPIViewSet):
    queryset = ProductVariant.objects.select_related("product").prefetch_related(
        "attributes__attribute",
        "images",
        "meta",
    )
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    public_list_serializer_class = ProductVariantListSerializer
    admin_list_serializer_class = ProductVariantAdminListSerializer
    write_serializer_class = ProductVariantWriteSerializer
    admin_read_serializer_class = ProductVariantDetailSerializer
    public_read_serializer_class = ProductVariantPublicSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["slug", "name"]
    ordering_fields = [
        "price",
        "stock",
        "created_at",
    ]
    filterset_class = ProductVariantFilter

    def get_permissions(self):
        if self.action in [
            "activate",
            "deactivate",
            "restore",
            "hard_delete",
        ]:
            return [IsAdminUser()]

        return super().get_permissions()

    def get_serializer_class(self):  # type: ignore
        if self.action in [
            "activate",
            "deactivate",
            "restore",
        ]:
            if self.request.user.is_staff:
                return self.admin_read_serializer_class
            return self.public_read_serializer_class

        if self.action in ["deleted"]:
            return self.admin_list_serializer_class

        return super().get_serializer_class()

    @extend_schema(exclude=True)
    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            "POST", detail="Variants can only be created from product endpoint."
        )

    # @action(detail=False, methods=["get"])
    # def deleted(self, request):
    #     queryset = ProductVariant.objects.filter(is_deleted=True)
    #     page = self.paginate_queryset(queryset)

    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)

    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)
