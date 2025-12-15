from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiExample,
)

from catalog.models.brand import Brand
from catalog.common.mixins import BaseAPIViewSet, LifeCycleActionMixin
from catalog.common.serializers import ProblemDetailsSerializer
from catalog.brands.serializers import (
    BrandDetailSerializer,
    BrandLightSerializers,
    BrandWriteSerializer,
    BrandPublicSerializer,
    BrandAdminListSerializer,
)
from catalog.brands.filters import BrandFilterSet
from catalog.common.docs.errors import error_401, error_403, error_404, error_500

TAG_BRAND = "Brand"


@extend_schema_view(
    create=extend_schema(
        tags=[TAG_BRAND],
        summary="Create a new brand",
        description="Endpoint to create a new brand",
        request=BrandWriteSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Brand created successfully",
                response=BrandDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="BrandCreated",
                        summary="Successful brand creation",
                        value={
                            "id": 4,
                            "name": "logo",
                            "slug": "logo",
                            "logo": "http://localhost:8000/media/brands/logos/logo_placeholder_f5bx0vf.jpg",
                            "is_active": False,
                            "is_deleted": False,
                            "created_at": "2025-12-09 16:01:17",
                            "updated_at": "2025-12-09 16:01:17",
                        },
                    )
                ],
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Validation error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="ValidationErrorMissingFields",
                        summary="Example of missing required fields",
                        value={
                            "type": "https://httpstatuses.com/400",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "/api/v1/brands/",
                            "detail": "The submitted data failed validation.",
                            "errors": [
                                {"field": "name", "message": "This field is required."}
                            ],
                        },
                    )
                ],
            ),
            **error_401("/api/v1/brands/"),
            **error_403("/api/v1/brands/"),
            **error_500("/api/v1/brands/"),
        },
    ),
    list=extend_schema(
        tags=[TAG_BRAND],
        summary="List brands",
        description=(
            "Returns a list of brands.\n\n"
            "- **Public users** receive a simplified representation (`BrandLightSerializers`).\n"
            "- **Admin users** receive extended details (`BrandAdminListSerializer`)."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="List of brands (public)",
                response=BrandLightSerializers,
                examples=[
                    OpenApiExample(
                        name="PublicBrandList",
                        summary="Public list example",
                        value=[
                            {
                                "id": 3,
                                "name": "logo",
                                "slug": "logo",
                                "logo": "http://localhost:8000/media/brands/logos/logo_placeholder.jpg",
                            },
                            {
                                "id": 1,
                                "name": "Samsung",
                                "slug": "samsung",
                                "logo": "http://localhost:8000/media/default/product_placeholder.png",
                            },
                        ],
                    )
                ],
            ),
            "200 (admin)": OpenApiResponse(
                description="Admin list of brands",
                response=BrandAdminListSerializer,
                examples=[
                    OpenApiExample(
                        name="AdminBrandList",
                        summary="Admin response example",
                        value=[
                            {
                                "id": 3,
                                "name": "logo",
                                "slug": "logo",
                                "logo": "http://localhost:8000/media/brands/logos/logo_placeholder.jpg",
                                "is_active": True,
                                "is_deleted": False,
                                "created_at": "2025-12-09 15:27:20",
                            },
                            {
                                "id": 1,
                                "name": "Samsung",
                                "slug": "samsung",
                                "logo": "http://localhost:8000/media/default/product_placeholder.png",
                                "is_active": True,
                                "is_deleted": False,
                                "created_at": "2025-12-03 15:23:27",
                            },
                        ],
                    )
                ],
            ),
            **error_500("/api/v1/brands/"),
        },
    ),
    retrieve=extend_schema(
        tags=[TAG_BRAND],
        summary="Retrieve a brand",
        description=(
            "Returns the details of a brand identified by its slug.\n\n"
            "- **Public users** receive `BrandPublicSerializer`.\n"
            "- **Admin users** receive full details via `BrandDetailSerializer`."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Brand detail (public)",
                response=BrandPublicSerializer,
                examples=[
                    OpenApiExample(
                        name="PublicBrandDetail",
                        summary="Public example",
                        value={
                            "id": 1,
                            "name": "Samsung",
                            "slug": "samsung",
                            "logo": "http://localhost:8000/media/default/product_placeholder.png",
                        },
                    )
                ],
            ),
            "200 (admin)": OpenApiResponse(
                description="Brand detail (admin)",
                response=BrandDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="AdminBrandDetail",
                        summary="Admin example",
                        value={
                            "id": 1,
                            "name": "Samsung",
                            "slug": "samsung",
                            "logo": "http://localhost:8000/media/default/product_placeholder.png",
                            "is_active": True,
                            "is_deleted": False,
                            "created_at": "2025-12-03 15:23:27",
                            "updated_at": "2025-12-03 15:23:27",
                        },
                    )
                ],
            ),
            **error_404("/api/v1/brands/{slug}/"),
            **error_500("/api/v1/brands/{slug}/"),
        },
    ),
    partial_update=extend_schema(
        tags=[TAG_BRAND],
        summary="Partially update a brand",
        description=(
            "Allows partial updates to a brand using `BrandWriteSerializer`. "
            "Only the submitted fields will be updated.\n\n"
            "Response uses `BrandDetailSerializer`."
        ),
        request=BrandWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Brand partially updated",
                response=BrandDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="BrandPartiallyUpdated",
                        summary="Partial update example",
                        value={
                            "id": 1,
                            "name": "Sony New",
                            "slug": "sony-new",
                            "logo": "http://localhost:8000/media/brands/sony_new.jpg",
                            "is_active": True,
                            "is_deleted": False,
                            "created_at": "2025-12-03 11:14:09",
                            "updated_at": "2025-12-09 18:11:49",
                        },
                    )
                ],
            ),
            **error_401("/api/v1/brands/{slug}/"),
            **error_403("/api/v1/brands/{slug}/"),
            **error_404("/api/v1/brands/{slug}/"),
            **error_500("/api/v1/brands/{slug}/"),
        },
    ),
    update=extend_schema(
        tags=[TAG_BRAND],
        summary="Update a brand",
        description=(
            "Fully updates a brand using all editable fields defined in `BrandWriteSerializer`.\n"
            "The response returns the updated brand using `BrandDetailSerializer`."
        ),
        request=BrandWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Brand updated",
                response=BrandDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="BrandUpdated",
                        summary="Full update example",
                        value={
                            "id": 1,
                            "name": "Sony Updated",
                            "slug": "sony-updated",
                            "logo": "http://localhost:8000/media/brands/sony_updated.jpg",
                            "is_active": True,
                            "is_deleted": False,
                            "created_at": "2025-12-03 11:14:09",
                            "updated_at": "2025-12-09 18:21:32",
                        },
                    )
                ],
            ),
            **error_401("/api/v1/brands/{slug}/"),
            **error_403("/api/v1/brands/{slug}/"),
            **error_404("/api/v1/brands/{slug}/"),
            **error_500("/api/v1/brands/{slug}/"),
        },
    ),
    activate=extend_schema(
        tags=[TAG_BRAND],
        summary="Activate brand",
        description="Activates a previously inactive brand.",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Brand activated successfully",
                response=BrandDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="BrandActivated",
                        summary="Brand activated successfully",
                        value={
                            "id": 4,
                            "name": "Logitech",
                            "slug": "logitech",
                            "logo": "http://localhost:8000/media/brands/logitech.jpg",
                            "is_active": True,
                            "is_deleted": False,
                            "created_at": "2025-11-01 14:22:11",
                            "updated_at": "2025-12-01 09:10:45",
                        },
                    )
                ],
            ),
            **error_401("/api/v1/brands/{slug}/activate/"),
            **error_403("/api/v1/brands/{slug}/activate/"),
            **error_404("/api/v1/brands/{slug}/activate/"),
            **error_500("/api/v1/brands/{slug}/activate/"),
        },
    ),
    deactivate=extend_schema(
        tags=[TAG_BRAND],
        summary="Deactivate brand",
        description="Deactivates an active brand.",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Brand deactivated successfully",
                response=BrandDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="BrandDeactivated",
                        summary="Brand deactivated",
                        value={
                            "id": 4,
                            "name": "Logitech",
                            "slug": "logitech",
                            "logo": "http://localhost:8000/media/brands/logitech.jpg",
                            "is_active": False,
                            "is_deleted": False,
                            "created_at": "2025-11-01 14:22:11",
                            "updated_at": "2025-12-01 09:11:22",
                        },
                    )
                ],
            ),
            **error_401("/api/v1/brands/{slug}/deactivate/"),
            **error_403("/api/v1/brands/{slug}/deactivate/"),
            **error_404("/api/v1/brands/{slug}/deactivate/"),
            **error_500("/api/v1/brands/{slug}/deactivate/"),
        },
    ),
    restore=extend_schema(
        tags=[TAG_BRAND],
        summary="Restore a deleted brand",
        description="Restores a soft-deleted brand.",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Brand restored successfully",
                response=BrandDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="BrandRestored",
                        summary="Soft-deleted brand restored",
                        value={
                            "id": 4,
                            "name": "Logitech",
                            "slug": "logitech",
                            "logo": "http://localhost:8000/media/brands/logitech.jpg",
                            "is_active": True,
                            "is_deleted": False,
                            "created_at": "2025-11-01 14:22:11",
                            "updated_at": "2025-12-01 10:40:00",
                        },
                    )
                ],
            ),
            **error_401("/api/v1/brands/{slug}/restore/"),
            **error_403("/api/v1/brands/{slug}/restore/"),
            **error_404("/api/v1/brands/{slug}/restore/"),
            **error_500("/api/v1/brands/{slug}/restore/"),
        },
    ),
    destroy=extend_schema(
        tags=[TAG_BRAND],
        summary="Soft delete a brand",
        description="Marks the brand as deleted instead of removing it permanently.",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Brand soft-deleted successfully",
            ),
            **error_401("/api/v1/brands/{slug}/"),
            **error_403("/api/v1/brands/{slug}/"),
            **error_404("/api/v1/brands/{slug}/"),
            **error_500("/api/v1/brands/{slug}/"),
        },
    ),
    hard_delete=extend_schema(
        tags=[TAG_BRAND],
        summary="Permanently delete a brand",
        description=(
            "Permanently deletes a brand. "
            "This action requires a confirmation body: {'confirm': true}."
        ),
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Brand permanently deleted"
            ),
            **error_401("/api/v1/brands/{slug}/hard_delete/"),
            **error_403("/api/v1/brands/{slug}/hard_delete/"),
            **error_404("/api/v1/brands/{slug}/hard_delete/"),
            **error_500("/api/v1/brands/{slug}/hard_delete/"),
        },
    ),
    deleted=extend_schema(
        tags=[TAG_BRAND],
        summary="List deleted brands",
        description="Returns a list of all soft-deleted brands.",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="List of deleted brands",
                response=BrandAdminListSerializer,
                examples=[
                    OpenApiExample(
                        name="DeletedBrandsList",
                        summary="Example of deleted brands",
                        value={
                            "count": 1,
                            "next": None,
                            "previous": None,
                            "results": [
                                {
                                    "id": 5,
                                    "name": "Sony",
                                    "slug": "sony",
                                    "logo": "http://localhost:8000/media/brands/sony.jpg",
                                    "is_active": False,
                                    "is_deleted": True,
                                    "created_at": "2025-10-10",
                                }
                            ],
                        },
                    )
                ],
            ),
            **error_401("/api/v1/brands/deleted/"),
            **error_403("/api/v1/brands/deleted/"),
            **error_500("/api/v1/brands/deleted/"),
        },
    ),
)
class BrandViewSet(LifeCycleActionMixin, BaseAPIViewSet):
    queryset = Brand.objects.all()
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    public_list_serializer_class = BrandLightSerializers
    admin_list_serializer_class = BrandAdminListSerializer
    write_serializer_class = BrandWriteSerializer
    admin_read_serializer_class = BrandDetailSerializer
    public_read_serializer_class = BrandPublicSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "slug", "created_at", "updated_at"]
    filterset_class = BrandFilterSet

    def get_queryset(self):
        qs = Brand.objects.all()

        request = getattr(self, "request", None)

        if request and request.user.is_staff:
            return qs  # staff ve todo

        return qs.filter(is_active=True)

    def get_permissions(self):
        if self.action in [
            "activate",
            "deactivate",
            "restore",
            "hard_delete",
            "deleted",
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


