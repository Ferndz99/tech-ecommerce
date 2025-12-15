from rest_framework import status

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiExample,
)

from accounts.serializers import ProblemDetailsSerializer
from catalog.attributes.serializers import (
    AttributeDetailSerializer,
    AttributeValueDetailSerializer,
    AttributeValueWriteSerializer,
    AttributeWriteSerializer,
)
from catalog.common.docs.errors import error_401, error_403, error_404, error_500
from catalog.common.mixins import BaseAPIViewSet
from catalog.models.attribute import Attribute, AttributeValue


TAG_ATTRIBUTE = "Attribute"
TAG_ATTRIBUTE_VALUE = "Attribute value"


@extend_schema_view(
    create=extend_schema(
        tags=[TAG_ATTRIBUTE],
        summary="Create a new attribute",
        description="Endpoint to create a new product attribute.",
        request=AttributeWriteSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Attribute created successfully",
                response=AttributeDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="AttributeCreated",
                        summary="Successful attribute creation",
                        value={"id": 1, "name": "new attribute"},
                    )
                ],
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Validation error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="ValidationError",
                        summary="Missing required field",
                        value={
                            "type": "https://httpstatuses.com/400",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "/api/v1/attributes/",
                            "detail": "The submitted data failed validation.",
                            "errors": [
                                {"field": "name", "message": "This field is required."}
                            ],
                        },
                    )
                ],
            ),
            **error_401("/api/v1/attributes/"),
            **error_403("/api/v1/attributes/"),
            **error_500("/api/v1/attributes/"),
        },
    ),
    list=extend_schema(
        tags=[TAG_ATTRIBUTE],
        summary="List attributes",
        description=(
            "Returns a list of attributes.\n\n"
            "- **Public users** receive the standard attribute representation.\n"
            "- **Admin users** receive the same representation with management fields."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="List of attributes",
                response=AttributeDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="AttributeList",
                        summary="Attributes list example",
                        value=[
                            {
                                "id": 1,
                                "name": "Color",
                            },
                            {
                                "id": 2,
                                "name": "Storage",
                            },
                        ],
                    )
                ],
            ),
            **error_500("/api/v1/attributes/"),
        },
    ),
    retrieve=extend_schema(
        tags=[TAG_ATTRIBUTE],
        summary="Retrieve an attribute",
        description=(
            "Returns the details of a specific attribute.\n\n"
            "- **Public and admin users** receive the same detailed representation."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Attribute detail",
                response=AttributeDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="AttributeDetail",
                        summary="Attribute detail example",
                        value={
                            "id": 1,
                            "name": "Color",
                        },
                    )
                ],
            ),
            **error_404("/api/v1/attributes/{id}/"),
            **error_500("/api/v1/attributes/{id}/"),
        },
    ),
    partial_update=extend_schema(
        tags=[TAG_ATTRIBUTE],
        summary="Partially update an attribute",
        description=(
            "Allows partial updates of an attribute. "
            "Only the provided fields will be updated."
        ),
        request=AttributeWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Attribute partially updated",
                response=AttributeDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="AttributePartiallyUpdated",
                        summary="Partial update example",
                        value={
                            "id": 1,
                            "name": "Colour",
                        },
                    )
                ],
            ),
            **error_401("/api/v1/attributes/{id}/"),
            **error_403("/api/v1/attributes/{id}/"),
            **error_404("/api/v1/attributes/{id}/"),
            **error_500("/api/v1/attributes/{id}/"),
        },
    ),
    update=extend_schema(
        tags=[TAG_ATTRIBUTE],
        summary="Update an attribute",
        description="Fully updates an attribute using all writable fields.",
        request=AttributeWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Attribute updated",
                response=AttributeDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="AttributeUpdated",
                        summary="Full update example",
                        value={
                            "id": 1,
                            "name": "Size",
                        },
                    )
                ],
            ),
            **error_401("/api/v1/attributes/{id}/"),
            **error_403("/api/v1/attributes/{id}/"),
            **error_404("/api/v1/attributes/{id}/"),
            **error_500("/api/v1/attributes/{id}/"),
        },
    ),
    destroy=extend_schema(
        tags=[TAG_ATTRIBUTE],
        summary="Soft delete an attribute",
        description="Marks the attribute as deleted without removing it permanently.",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Attribute soft-deleted successfully"
            ),
            **error_401("/api/v1/attributes/{id}/"),
            **error_403("/api/v1/attributes/{id}/"),
            **error_404("/api/v1/attributes/{id}/"),
            **error_500("/api/v1/attributes/{id}/"),
        },
    ),
)
class AttributeViewSet(BaseAPIViewSet):
    queryset = Attribute.objects.all()

    public_list_serializer_class = AttributeDetailSerializer
    admin_list_serializer_class = AttributeDetailSerializer
    write_serializer_class = AttributeWriteSerializer
    admin_read_serializer_class = AttributeDetailSerializer
    public_read_serializer_class = AttributeDetailSerializer


@extend_schema_view(
    create=extend_schema(
        tags=[TAG_ATTRIBUTE_VALUE],
        summary="Create a new attribute value",
        description=(
            "Creates a new value for a given attribute.\n\n"
            "Example: Attribute `Color` → Value `Red`."
        ),
        request=AttributeValueWriteSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Attribute value created successfully",
                response=AttributeValueDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="AttributeValueCreated",
                        summary="Successful attribute value creation",
                        value={"id": 1, "attribute": "Storage", "value": "128 GB"},
                    )
                ],
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Validation error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="ValidationError",
                        summary="Invalid or missing fields",
                        value={
                            "type": "https://httpstatuses.com/400",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "/api/v1/attribute-values/",
                            "detail": "The submitted data failed validation.",
                            "errors": [
                                {
                                    "field": "attribute",
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
            **error_401("/api/v1/attribute-values/"),
            **error_403("/api/v1/attribute-values/"),
            **error_500("/api/v1/attribute-values/"),
        },
    ),
    list=extend_schema(
        tags=[TAG_ATTRIBUTE_VALUE],
        summary="List attribute values",
        description=(
            "Returns a list of attribute values.\n\n"
            "- Each value is linked to its parent attribute.\n"
            "- Public and admin users receive the same representation."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="List of attribute values",
                response=AttributeValueDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="AttributeValueList",
                        summary="Attribute values list example",
                        value=[
                            {"id": 1, "attribute": "Storage", "value": "1 TB"},
                            {"id": 2, "attribute": "Storage", "value": "128 GB"},
                        ],
                    )
                ],
            ),
            **error_500("/api/v1/attribute-values/"),
        },
    ),
    retrieve=extend_schema(
        tags=[TAG_ATTRIBUTE_VALUE],
        summary="Retrieve an attribute value",
        description=(
            "Returns the details of a specific attribute value.\n\n"
            "The response includes the parent attribute information."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Attribute value detail",
                response=AttributeValueDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="AttributeValueDetail",
                        summary="Attribute value detail example",
                        value={"id": 1, "attribute": "Storage", "value": "128 GB"},
                    )
                ],
            ),
            **error_404("/api/v1/attribute-values/{id}/"),
            **error_500("/api/v1/attribute-values/{id}/"),
        },
    ),
    partial_update=extend_schema(
        tags=[TAG_ATTRIBUTE_VALUE],
        summary="Partially update an attribute value",
        description=(
            "Allows partial updates to an attribute value.\n\n"
            "Only the provided fields will be updated."
        ),
        request=AttributeValueWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Attribute value partially updated",
                response=AttributeValueDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="AttributeValuePartiallyUpdated",
                        summary="Partial update example",
                        value={"id": 1, "attribute": "Storage", "value": "128 GB"},
                    )
                ],
            ),
            **error_401("/api/v1/attribute-values/{id}/"),
            **error_403("/api/v1/attribute-values/{id}/"),
            **error_404("/api/v1/attribute-values/{id}/"),
            **error_500("/api/v1/attribute-values/{id}/"),
        },
    ),
    update=extend_schema(
        tags=[TAG_ATTRIBUTE_VALUE],
        summary="Update an attribute value",
        description="Fully updates an attribute value using all writable fields.",
        request=AttributeValueWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Attribute value updated",
                response=AttributeValueDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="AttributeValueUpdated",
                        summary="Full update example",
                        value={"id": 1, "attribute": "Storage", "value": "128 GB"},
                    )
                ],
            ),
            **error_401("/api/v1/attribute-values/{id}/"),
            **error_403("/api/v1/attribute-values/{id}/"),
            **error_404("/api/v1/attribute-values/{id}/"),
            **error_500("/api/v1/attribute-values/{id}/"),
        },
    ),
    destroy=extend_schema(
        tags=[TAG_ATTRIBUTE_VALUE],
        summary="Soft delete an attribute value",
        description="Marks the attribute value as deleted without permanently removing it.",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Attribute value soft-deleted successfully"
            ),
            **error_401("/api/v1/attribute-values/{id}/"),
            **error_403("/api/v1/attribute-values/{id}/"),
            **error_404("/api/v1/attribute-values/{id}/"),
            **error_500("/api/v1/attribute-values/{id}/"),
        },
    ),
)
class AttributeValueViewSet(BaseAPIViewSet):
    queryset = AttributeValue.objects.all()

    public_list_serializer_class = AttributeValueDetailSerializer
    admin_list_serializer_class = AttributeValueDetailSerializer
    write_serializer_class = AttributeValueWriteSerializer
    admin_read_serializer_class = AttributeValueDetailSerializer
    public_read_serializer_class = AttributeValueDetailSerializer
