from rest_framework import status

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiExample,
)

from accounts.serializers import ProblemDetailsSerializer
from catalog.common.docs.errors import error_401, error_403, error_404, error_500
from catalog.common.mixins import BaseAPIViewSet
from catalog.models.specification import ProductSpecification, Specification
from catalog.specifications.serializers import (
    ProductSpecificationDirectWriteSerializer,
    SpecificationDetailSerializer,
    SpecificationWriteSerializer,
    ProductSpecificationDetailSerializer,
    ProductSpecificationWriteSerializer,
)

TAG_SPECIFICATION = "Specification"
TAG_PRODUCT_SPECIFICATION = "Product Specification"


# TODO: FIX PUT/PATCH AND DOCS
@extend_schema_view(
    create=extend_schema(
        tags=[TAG_PRODUCT_SPECIFICATION],
        summary="Create a new product specification",
        description=(
            "Creates a new specification for a product.\n\n"
            "Examples of product specifications: `RAM`, `Screen Size`, `Storage`."
        ),
        request=ProductSpecificationDirectWriteSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Product specification created successfully",
                response=ProductSpecificationDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="ProductSpecificationCreated",
                        summary="Successful product specification creation",
                        value={
                            "id": 1,
                            "specification": "CPU",
                            "value": "intel core i 10",
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
                        summary="Missing required fields",
                        value={
                            "type": "https://httpstatuses.com/400",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "/api/v1/product-specifications/",
                            "detail": "The submitted data failed validation.",
                            "errors": [
                                {
                                    "field": "specification_id",
                                    "message": "This field is required.",
                                },
                                {
                                    "field": "value",
                                    "message": "This field is required.",
                                },
                            ],
                        },
                    )
                ],
            ),
            **error_401("/api/v1/product-specifications/"),
            **error_403("/api/v1/product-specifications/"),
            **error_500("/api/v1/product-specifications/"),
        },
    ),
    list=extend_schema(
        tags=[TAG_PRODUCT_SPECIFICATION],
        summary="List product specifications",
        description=(
            "Returns a list of specifications for products.\n\n"
            "- Public and admin users receive the same representation.\n"
            "- Useful for showing technical details of products."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="List of product specifications",
                response=ProductSpecificationDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="ProductSpecificationList",
                        summary="Product specifications list example",
                        value=[
                            {
                                "id": 1,
                                "specification": "Screen",
                                "value": "Pantalla OLED",
                            },
                            {
                                "id": 2,
                                "specification": "CPU",
                                "value": "intel core i10",
                            },
                        ],
                    )
                ],
            ),
            **error_500("/api/v1/product-specifications/"),
        },
    ),
    retrieve=extend_schema(
        tags=[TAG_PRODUCT_SPECIFICATION],
        summary="Retrieve a product specification",
        description=(
            "Returns the details of a specific product specification.\n\n"
            "Useful for showing the technical specification of a single product."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Product specification detail",
                response=ProductSpecificationDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="ProductSpecificationDetail",
                        summary="Product specification detail example",
                        value={
                            "id": 1,
                            "specification": "Screen",
                            "value": "Pantalla OLED",
                        },
                    )
                ],
            ),
            **error_404("/api/v1/product-specifications/{id}/"),
            **error_500("/api/v1/product-specifications/{id}/"),
        },
    ),
    partial_update=extend_schema(
        tags=[TAG_PRODUCT_SPECIFICATION],
        summary="Partially update a product specification",
        description=(
            "Allows partial updates to a product specification.\n\n"
            "Only the provided fields will be updated."
        ),
        request=ProductSpecificationWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Product specification partially updated",
                response=ProductSpecificationDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="ProductSpecificationPartiallyUpdated",
                        summary="Partial update example",
                        value={
                            "id": 1,
                            "specification": "Screen",
                            "value": "Pantalla OLED",
                        },
                    )
                ],
            ),
            **error_401("/api/v1/product-specifications/{id}/"),
            **error_403("/api/v1/product-specifications/{id}/"),
            **error_404("/api/v1/product-specifications/{id}/"),
            **error_500("/api/v1/product-specifications/{id}/"),
        },
    ),
    update=extend_schema(
        tags=[TAG_PRODUCT_SPECIFICATION],
        summary="Update a product specification",
        description="Fully updates a product specification using all writable fields.",
        request=ProductSpecificationWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Product specification updated",
                response=ProductSpecificationDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="ProductSpecificationUpdated",
                        summary="Full update example",
                        value={
                            "id": 1,
                            "specification": "Screen",
                            "value": "Pantalla OLED",
                        },
                    )
                ],
            ),
            **error_401("/api/v1/product-specifications/{id}/"),
            **error_403("/api/v1/product-specifications/{id}/"),
            **error_404("/api/v1/product-specifications/{id}/"),
            **error_500("/api/v1/product-specifications/{id}/"),
        },
    ),
    destroy=extend_schema(
        tags=[TAG_PRODUCT_SPECIFICATION],
        summary="Soft delete a product specification",
        description="Marks the product specification as deleted without permanently removing it.",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Product specification soft-deleted successfully"
            ),
            **error_401("/api/v1/product-specifications/{id}/"),
            **error_403("/api/v1/product-specifications/{id}/"),
            **error_404("/api/v1/product-specifications/{id}/"),
            **error_500("/api/v1/product-specifications/{id}/"),
        },
    ),
)
class ProductSpecificationViewSet(BaseAPIViewSet):
    queryset = ProductSpecification.objects.all()

    public_list_serializer_class = ProductSpecificationDetailSerializer
    admin_list_serializer_class = ProductSpecificationDetailSerializer
    write_serializer_class = ProductSpecificationDirectWriteSerializer
    admin_read_serializer_class = ProductSpecificationDetailSerializer
    public_read_serializer_class = ProductSpecificationDetailSerializer


@extend_schema_view(
    create=extend_schema(
        tags=[TAG_SPECIFICATION],
        summary="Create a new specification",
        description=(
            "Creates a new technical specification.\n\n"
            "Specifications are commonly used to describe technical "
            "details of a product such as RAM, storage, screen size, etc."
        ),
        request=SpecificationWriteSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Specification created successfully",
                response=SpecificationDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="SpecificationCreated",
                        summary="Successful specification creation",
                        value={"id": 1, "name": "USB"},
                    )
                ],
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Validation error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="ValidationError",
                        summary="Missing required fields",
                        value={
                            "type": "https://httpstatuses.com/400",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "/api/v1/specifications/",
                            "detail": "The submitted data failed validation.",
                            "errors": [
                                {"field": "name", "message": "This field is required."}
                            ],
                        },
                    )
                ],
            ),
            **error_401("/api/v1/specifications/"),
            **error_403("/api/v1/specifications/"),
            **error_500("/api/v1/specifications/"),
        },
    ),
    list=extend_schema(
        tags=[TAG_SPECIFICATION],
        summary="List specifications",
        description=(
            "Returns a list of specifications.\n\n"
            "- Public and admin users receive the same representation.\n"
            "- Typically used to display technical details."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="List of specifications",
                response=SpecificationDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="SpecificationList",
                        summary="Specification list example",
                        value=[
                            {
                                "id": 1,
                                "name": "Screen",
                            },
                            {
                                "id": 2,
                                "name": "Battery",
                            },
                        ],
                    )
                ],
            ),
            **error_500("/api/v1/specifications/"),
        },
    ),
    retrieve=extend_schema(
        tags=[TAG_SPECIFICATION],
        summary="Retrieve a specification",
        description=(
            "Returns the details of a specific specification.\n\n"
            "Useful for showing complete technical information."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Specification detail",
                response=SpecificationDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="SpecificationDetail",
                        summary="Specification detail example",
                        value={
                            "id": 1,
                            "name": "Screen",
                        },
                    )
                ],
            ),
            **error_404("/api/v1/specifications/{id}/"),
            **error_500("/api/v1/specifications/{id}/"),
        },
    ),
    partial_update=extend_schema(
        tags=[TAG_SPECIFICATION],
        summary="Partially update a specification",
        description=(
            "Allows partial updates to a specification.\n\n"
            "Only the provided fields will be updated."
        ),
        request=SpecificationWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Specification partially updated",
                response=SpecificationDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="SpecificationPartiallyUpdated",
                        summary="Partial update example",
                        value={
                            "id": 1,
                            "name": "Screen",
                        },
                    )
                ],
            ),
            **error_401("/api/v1/specifications/{id}/"),
            **error_403("/api/v1/specifications/{id}/"),
            **error_404("/api/v1/specifications/{id}/"),
            **error_500("/api/v1/specifications/{id}/"),
        },
    ),
    update=extend_schema(
        tags=[TAG_SPECIFICATION],
        summary="Update a specification",
        description="Fully updates a specification using all writable fields.",
        request=SpecificationWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Specification updated",
                response=SpecificationDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="SpecificationUpdated",
                        summary="Full update example",
                        value={
                            "id": 1,
                            "name": "Screen",
                        },
                    )
                ],
            ),
            **error_401("/api/v1/specifications/{id}/"),
            **error_403("/api/v1/specifications/{id}/"),
            **error_404("/api/v1/specifications/{id}/"),
            **error_500("/api/v1/specifications/{id}/"),
        },
    ),
    destroy=extend_schema(
        tags=[TAG_SPECIFICATION],
        summary="Soft delete a specification",
        description="Marks the specification as deleted instead of permanently removing it.",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Specification soft-deleted successfully"
            ),
            **error_401("/api/v1/specifications/{id}/"),
            **error_403("/api/v1/specifications/{id}/"),
            **error_404("/api/v1/specifications/{id}/"),
            **error_500("/api/v1/specifications/{id}/"),
        },
    ),
)
class SpecificationViewSet(BaseAPIViewSet):
    queryset = Specification.objects.all()

    public_list_serializer_class = SpecificationDetailSerializer
    admin_list_serializer_class = SpecificationDetailSerializer
    write_serializer_class = SpecificationWriteSerializer
    admin_read_serializer_class = SpecificationDetailSerializer
    public_read_serializer_class = SpecificationDetailSerializer
