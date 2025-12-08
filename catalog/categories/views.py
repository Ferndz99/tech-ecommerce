from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiExample
)

from catalog.models.category import Category
from catalog.categories.serializers import (
    CategoryDetailSerializer,
    CategoryLightSerializer,
    CategoryWriteSerializer,
    CategoryPublicSerializer,
    CategoryAdminListSerializer,
)
from catalog.common.mixins import BaseAPIViewSet, LifeCycleActionMixin
from catalog.common.serializers import ProblemDetailsSerializer

from catalog.categories.filters import CategoryFilterSet

TAG_CATEGORY = "Category"



@extend_schema_view(
    create=extend_schema(
        tags=[TAG_CATEGORY],
        summary="Create a new category",
        description="Endpoint to create a new category",
        request=CategoryWriteSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Category created successfully",
                response=CategoryDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="CategoryCreated",
                        summary="Successful category creation",
                        value={
                            "id": 20,
                            "name": "new category",
                            "slug": "new category",
                            "level": 0,
                            "parent": None,
                            "ancestors": [],
                            "descendants_count": 0,
                            "is_active": True,
                            "is_deleted": False,
                            "created_at": "2025-12-06 11:42:37",
                            "updated_at": "2025-12-06 11:42:37",
                            "children": [],
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
                            "instance": "/api/v1/categories/",
                            "detail": "The submitted data failed validation.",
                            "errors": [
                                {"field": "name", "message": "This field is required."}
                            ],
                        },
                    )
                ],
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided or are invalid.",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Missing Authorization header",
                        value={
                            "type": "https://httpstatuses.com/401",
                            "status": 401,
                            "title": "Unauthorized",
                            "instance": "/api/v1/categories/",
                            "detail": "Authentication credentials were not provided.",
                        },
                    )
                ],
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Invalid token",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Invalid token",
                        value={
                            "type": "https://httpstatuses.com/403",
                            "status": 403,
                            "title": "Forbidden",
                            "instance": "/api/v1/categories/",
                            "detail": "You do not have permission to perform this action.",
                        },
                    )
                ],
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Server error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "Server Error",
                        summary="Server Error Example",
                        description="Example response for server errors during creating category.",
                        value={
                            "type": "https://httpstatuses.com/500",
                            "status": 500,
                            "title": "Internal Server Error",
                            "instance": "/api/v1/categories/",
                            "detail": "An unexpected error occurred. Please try again later.",
                        },
                        status_codes=["500"],
                    )
                ],
            ),
        },
    ),
    list=extend_schema(
        tags=[TAG_CATEGORY],
        summary="List categories",
        description=(
            "Returns a list of categories.\n\n"
            "- **Public users** receive a simplified representation.\n"
            "- **Admin users** receive the full admin representation.\n"
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successful category list response",
                response=CategoryLightSerializer,  # por defecto documentamos el serializer público
                examples=[
                    OpenApiExample(
                        name="PublicCategoryList",
                        summary="Public response example",
                        value=[
                            {
                                "id": 1,
                                "name": "category 1",
                                "slug": "category-1",
                            },
                            {
                                "id": 2,
                                "name": "category 2",
                                "slug": "category-2",
                            },
                            {
                                "id": 3,
                                "name": "category 3",
                                "slug": "category-3",
                            },
                        ],
                    )
                ],
            ),
            "200 (admin)": OpenApiResponse(
                description="Admin category list response (only for staff users)",
                response=CategoryAdminListSerializer,
                examples=[
                    OpenApiExample(
                        name="AdminCategoryList",
                        summary="Admin response example",
                        value=[
                            {
                                "id": 1,
                                "name": "category 1",
                                "slug": "category-1",
                                "is_active": False,
                                "is_deleted": True,
                                "created_at": "2025-12-03 19:44:50",
                            },
                            {
                                "id": 2,
                                "name": "category 2",
                                "slug": "category-2",
                                "is_active": True,
                                "is_deleted": False,
                                "created_at": "2025-12-04 19:14:09",
                            },
                        ],
                    )
                ],
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Server error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "Server Error",
                        summary="Server Error Example",
                        description="Example response for server errors during list categories.",
                        value={
                            "type": "https://httpstatuses.com/500",
                            "status": 500,
                            "title": "Internal Server Error",
                            "instance": "/api/v1/categories/",
                            "detail": "An unexpected error occurred. Please try again later.",
                        },
                        status_codes=["500"],
                    )
                ],
            ),
        },
    ),
    retrieve=extend_schema(
        tags=[TAG_CATEGORY],
        summary="Retrieve a category",
        description=(
            "Returns the details of a specific category identified by its slug.\n\n"
            "- **Public users** receive a public-safe representation (`CategoryPublicSerializer`).\n"
            "- **Admin users** receive the full representation (`CategoryDetailSerializer`)."
        ),
        responses={
            # Documentación pública por defecto
            status.HTTP_200_OK: OpenApiResponse(
                description="Successful category retrieval (public)",
                response=CategoryPublicSerializer,
                examples=[
                    OpenApiExample(
                        name="PublicCategoryDetail",
                        summary="Public response example",
                        value={
                            "id": 15,
                            "name": "category 15",
                            "slug": "category-15",
                        },
                    )
                ],
            ),
            # Variante admin explícita
            "200 (admin)": OpenApiResponse(
                description="Successful category retrieval (admin)",
                response=CategoryDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="AdminCategoryDetail",
                        summary="Admin response example",
                        value={
                            "id": 15,
                            "name": "category 15",
                            "slug": "category-15",
                            "level": 0,
                            "parent": None,
                            "ancestors": [],
                            "descendants_count": 0,
                            "is_active": True,
                            "is_deleted": False,
                            "created_at": "2025-12-04 19:14:09",
                            "updated_at": "2025-12-04 19:14:09",
                            "children": [],
                        },
                    )
                ],
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Server error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "Server Error",
                        summary="Server Error Example",
                        description="Example response for server errors during retrive category.",
                        value={
                            "type": "https://httpstatuses.com/500",
                            "status": 500,
                            "title": "Internal Server Error",
                            "instance": "/api/v1/categories/{category_slug}",
                            "detail": "An unexpected error occurred. Please try again later.",
                        },
                        status_codes=["500"],
                    )
                ],
            ),
        },
    ),
    partial_update=extend_schema(
        tags=[TAG_CATEGORY],
        summary="Partially update a category",
        description=(
            "Partially updates an existing category using `CategoryWriteSerializer`. "
            "Only the fields provided in the request will be updated. The response returns "
            "the updated category using `CategoryDetailSerializer`.\n\n"
            "This endpoint supports partial modification of the resource."
        ),
        request=CategoryWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Category partially updated successfully",
                response=CategoryDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="CategoryPartiallyUpdated",
                        summary="Example of a successful partial update",
                        value={
                            "id": 3,
                            "name": "New Name Only",
                            "slug": "new-name-only",
                            "level": 0,
                            "parent": None,
                            "ancestors": [],
                            "descendants_count": 2,
                            "is_active": True,
                            "is_deleted": False,
                            "created_at": "2025-01-12 10:11:32",
                            "updated_at": "2025-12-06 13:29:14",
                            "children": [],
                        },
                    )
                ],
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Missing authentication",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="UnauthorizedPartial",
                        value={
                            "type": "https://httpstatuses.com/401",
                            "status": 401,
                            "title": "Unauthorized",
                            "instance": "/api/v1/categories/some-category/",
                            "detail": "Authentication credentials were not provided.",
                        },
                    )
                ],
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Forbidden operation",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="ForbiddenPartial",
                        value={
                            "type": "https://httpstatuses.com/403",
                            "status": 403,
                            "title": "Forbidden",
                            "instance": "/api/v1/categories/some-category/",
                            "detail": "You do not have permission to perform this action.",
                        },
                    )
                ],
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Server error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "ServerErrorPartial",
                        summary="Unexpected server error example",
                        description="Example response for server errors during partial update.",
                        value={
                            "type": "https://httpstatuses.com/500",
                            "status": 500,
                            "title": "Internal Server Error",
                            "instance": "/api/v1/categories/some-category/",
                            "detail": "An unexpected error occurred. Please try again later.",
                        },
                        status_codes=["500"],
                    )
                ],
            ),
        },
    ),
    update=extend_schema(
        tags=[TAG_CATEGORY],
        summary="Update a category",
        description=(
            "Updates an existing category. The request must use `CategoryWriteSerializer` "
            "to provide the editable fields. The response returns the updated category "
            "serialized with `CategoryDetailSerializer`.\n\n"
            "This endpoint supports full updates of the resource."
        ),
        request=CategoryWriteSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Category updated successfully",
                response=CategoryDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="CategoryUpdated",
                        summary="Successful category update",
                        value={
                            "id": 3,
                            "name": "Updated Category Name",
                            "slug": "updated-category-name",
                            "level": 0,
                            "parent": None,
                            "ancestors": [],
                            "descendants_count": 2,
                            "is_active": True,
                            "is_deleted": False,
                            "created_at": "2025-01-12 10:11:32",
                            "updated_at": "2025-12-06 13:21:04",
                            "children": [],
                        },
                    )
                ],
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Missing or invalid authentication",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={
                            "type": "https://httpstatuses.com/401",
                            "status": 401,
                            "title": "Unauthorized",
                            "instance": "/api/v1/categories/some-category/",
                            "detail": "Authentication credentials were not provided.",
                        },
                    )
                ],
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Forbidden – insufficient permissions",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Forbidden",
                        value={
                            "type": "https://httpstatuses.com/403",
                            "status": 403,
                            "title": "Forbidden",
                            "instance": "/api/v1/categories/some-category/",
                            "detail": "You do not have permission to perform this action.",
                        },
                    )
                ],
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Server error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "ServerError",
                        summary="Unexpected server error",
                        description="Example response for server errors during update.",
                        value={
                            "type": "https://httpstatuses.com/500",
                            "status": 500,
                            "title": "Internal Server Error",
                            "instance": "/api/v1/categories/some-category/",
                            "detail": "An unexpected error occurred. Please try again later.",
                        },
                        status_codes=["500"],
                    )
                ],
            ),
        },
    ),
    activate=extend_schema(
        tags=[TAG_CATEGORY],
        summary="Activate a category",
        description=(
            "Activates a category by setting its state to active. "
            "This action does not require a request body. "
            "Returns the updated category object."
        ),
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Category activated successfully",
                response=CategoryDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="CategoryActivated",
                        summary="Successful category activation",
                        value={
                            "id": 20,
                            "name": "new category",
                            "slug": "new-category",
                            "level": 0,
                            "parent": None,
                            "ancestors": [],
                            "descendants_count": 0,
                            "is_active": True,
                            "is_deleted": False,
                            "created_at": "2025-12-06 11:42:37",
                            "updated_at": "2025-12-06 11:50:02",
                            "children": [],
                        },
                    )
                ],
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Missing or invalid authentication",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={
                            "type": "https://httpstatuses.com/401",
                            "status": 401,
                            "title": "Unauthorized",
                            "instance": "/api/v1/categories/{category_slug}/activate/",
                            "detail": "Authentication credentials were not provided.",
                        },
                    )
                ],
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Forbidden – insufficient permissions",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Forbidden",
                        value={
                            "type": "https://httpstatuses.com/403",
                            "status": 403,
                            "title": "Forbidden",
                            "instance": "/api/v1/categories/{category_slug}/activate/",
                            "detail": "You do not have permission to perform this action.",
                        },
                    )
                ],
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Server error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "ServerError",
                        summary="Unexpected server error",
                        description="Example response for server errors during update.",
                        value={
                            "type": "https://httpstatuses.com/500",
                            "status": 500,
                            "title": "Internal Server Error",
                            "instance": "/api/v1/categories/{category_slug}/activate/",
                            "detail": "An unexpected error occurred. Please try again later.",
                        },
                        status_codes=["500"],
                    )
                ],
            ),
        },
    ),
    deactivate=extend_schema(
        tags=[TAG_CATEGORY],
        summary="Deactivate a category",
        description=(
            "Deactivates a category by setting its state to inactive. "
            "This action does not require a request body. "
            "Returns the updated category object."
        ),
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Category deactivated successfully",
                response=CategoryDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="CategoryDeactivated",
                        summary="Successful category deactivation",
                        value={
                            "id": 20,
                            "name": "new category",
                            "slug": "new-category",
                            "level": 0,
                            "parent": None,
                            "ancestors": [],
                            "descendants_count": 0,
                            "is_active": False,
                            "is_deleted": False,
                            "created_at": "2025-12-06 11:42:37",
                            "updated_at": "2025-12-06 12:05:44",
                            "children": [],
                        },
                    )
                ],
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Missing or invalid authentication",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={
                            "type": "https://httpstatuses.com/401",
                            "status": 401,
                            "title": "Unauthorized",
                            "instance": "/api/v1/categories/{category_slug}/deactivate/",
                            "detail": "Authentication credentials were not provided.",
                        },
                    )
                ],
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Forbidden – insufficient permissions",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Forbidden",
                        value={
                            "type": "https://httpstatuses.com/403",
                            "status": 403,
                            "title": "Forbidden",
                            "instance": "/api/v1/categories/{category_slug}/deactivate/",
                            "detail": "You do not have permission to perform this action.",
                        },
                    )
                ],
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Server error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "ServerError",
                        summary="Unexpected server error",
                        description="Example response for server errors during update.",
                        value={
                            "type": "https://httpstatuses.com/500",
                            "status": 500,
                            "title": "Internal Server Error",
                            "instance": "/api/v1/categories/{category_slug}/deactivate/",
                            "detail": "An unexpected error occurred. Please try again later.",
                        },
                        status_codes=["500"],
                    )
                ],
            ),
        },
    ),
    restore=extend_schema(
        tags=[TAG_CATEGORY],
        summary="Restore a soft-deleted category",
        description=(
            "Restores a previously soft-deleted category by marking it as active again. "
            "This action does not require a request body. "
            "Returns the updated category object."
        ),
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Category restored successfully",
                response=CategoryDetailSerializer,
                examples=[
                    OpenApiExample(
                        name="CategoryRestored",
                        summary="Successful category restore",
                        value={
                            "id": 20,
                            "name": "new category",
                            "slug": "new-category",
                            "level": 0,
                            "parent": None,
                            "ancestors": [],
                            "descendants_count": 0,
                            "is_active": True,
                            "is_deleted": False,
                            "created_at": "2025-12-06 11:42:37",
                            "updated_at": "2025-12-06 12:22:55",
                            "children": [],
                        },
                    )
                ],
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Missing or invalid authentication",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={
                            "type": "https://httpstatuses.com/401",
                            "status": 401,
                            "title": "Unauthorized",
                            "instance": "/api/v1/categories/{category_slug}/restore/",
                            "detail": "Authentication credentials were not provided.",
                        },
                    )
                ],
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Forbidden – insufficient permissions",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Forbidden",
                        value={
                            "type": "https://httpstatuses.com/403",
                            "status": 403,
                            "title": "Forbidden",
                            "instance": "/api/v1/categories/{category_slug}/restore/",
                            "detail": "You do not have permission to perform this action.",
                        },
                    )
                ],
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Server error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "ServerError",
                        summary="Unexpected server error",
                        description="Example response for server errors during restore.",
                        value={
                            "type": "https://httpstatuses.com/500",
                            "status": 500,
                            "title": "Internal Server Error",
                            "instance": "/api/v1/categories/{category_slug}/restore/",
                            "detail": "An unexpected error occurred. Please try again later.",
                        },
                        status_codes=["500"],
                    )
                ],
            ),
        },
    ),
    destroy=extend_schema(
        tags=[TAG_CATEGORY],
        summary="Soft delete a category",
        description=(
            "Marks the category as deleted without removing it from the database. "
            "This action is reversible and does not delete related products."
        ),
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Category soft-deleted successfully", response=None
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Missing or invalid authentication",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={
                            "type": "https://httpstatuses.com/401",
                            "status": 401,
                            "title": "Unauthorized",
                            "instance": "/api/v1/categories/{category_slug}/",
                            "detail": "Authentication credentials were not provided.",
                        },
                    )
                ],
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Forbidden – insufficient permissions",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Forbidden",
                        value={
                            "type": "https://httpstatuses.com/403",
                            "status": 403,
                            "title": "Forbidden",
                            "instance": "/api/v1/categories/{category_slug}/",
                            "detail": "You do not have permission to perform this action.",
                        },
                    )
                ],
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Server error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "ServerError",
                        summary="Unexpected server error",
                        description="Example response for server errors during restore.",
                        value={
                            "type": "https://httpstatuses.com/500",
                            "status": 500,
                            "title": "Internal Server Error",
                            "instance": "/api/v1/categories/{category_slug}/",
                            "detail": "An unexpected error occurred. Please try again later.",
                        },
                        status_codes=["500"],
                    )
                ],
            ),
        },
    ),
    hard_delete=extend_schema(
        tags=[TAG_CATEGORY],
        summary="Permanently delete a category",
        description=(
            "Permanently removes the category from the database. "
            "This action cannot be undone. Requires a confirmation body: {'confirm': true}."
        ),
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Category permanently deleted", response=None
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Missing or invalid authentication",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={
                            "type": "https://httpstatuses.com/401",
                            "status": 401,
                            "title": "Unauthorized",
                            "instance": "/api/v1/categories/{category_slug}/hard_delete/",
                            "detail": "Authentication credentials were not provided.",
                        },
                    )
                ],
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Forbidden – insufficient permissions",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Forbidden",
                        value={
                            "type": "https://httpstatuses.com/403",
                            "status": 403,
                            "title": "Forbidden",
                            "instance": "/api/v1/categories/{category_slug}/hard_delete/",
                            "detail": "You do not have permission to perform this action.",
                        },
                    )
                ],
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Server error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "ServerError",
                        summary="Unexpected server error",
                        description="Example response for server errors during restore.",
                        value={
                            "type": "https://httpstatuses.com/500",
                            "status": 500,
                            "title": "Internal Server Error",
                            "instance": "/api/v1/categories/{category_slug}/hard_delete/",
                            "detail": "An unexpected error occurred. Please try again later.",
                        },
                        status_codes=["500"],
                    )
                ],
            ),
        },
    ),
    deleted=extend_schema(
        tags=[TAG_CATEGORY],
        summary="List deleted categories",
        description=(
            "Returns a paginated list of categories that have been soft-deleted "
            "(i.e., categories where `is_deleted = true`).\n\n"
            "This endpoint is restricted to admin users. "
            "Regular authenticated users do not have access."
        ),
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="List of soft-deleted categories",
                response=CategoryAdminListSerializer,
                examples=[
                    OpenApiExample(
                        name="DeletedCategories",
                        summary="Example response showing deleted categories",
                        value={
                            "count": 1,
                            "next": None,
                            "previous": None,
                            "results": [
                                {
                                    "id": 5,
                                    "name": "category 1",
                                    "slug": "category 1",
                                    "is_active": False,
                                    "is_deleted": True,
                                    "created_at": "2025-12-03 19:44:50",
                                },
                            ],
                        },
                    )
                ],
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Missing or invalid authentication",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Unauthorized",
                        value={
                            "type": "https://httpstatuses.com/401",
                            "status": 401,
                            "title": "Unauthorized",
                            "instance": "/api/v1/categories/deleted/",
                            "detail": "Authentication credentials were not provided.",
                        },
                    )
                ],
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Forbidden – admin-only action",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        name="Forbidden",
                        value={
                            "type": "https://httpstatuses.com/403",
                            "status": 403,
                            "title": "Forbidden",
                            "instance": "/api/v1/categories/deleted/",
                            "detail": "You do not have permission to perform this action.",
                        },
                    )
                ],
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Server error",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "ServerError",
                        summary="Unexpected server error",
                        description="Example response for server errors when listing deleted categories.",
                        value={
                            "type": "https://httpstatuses.com/500",
                            "status": 500,
                            "title": "Internal Server Error",
                            "instance": "/api/v1/categories/deleted/",
                            "detail": "An unexpected error occurred. Please try again later.",
                        },
                        status_codes=["500"],
                    )
                ],
            ),
        },
    ),
)
class CategoryViewSet(LifeCycleActionMixin, BaseAPIViewSet):
    queryset = (
        Category.objects.all().select_related("parent").prefetch_related("children")
    )
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    public_list_serializer_class = CategoryLightSerializer
    admin_list_serializer_class = CategoryAdminListSerializer
    write_serializer_class = CategoryWriteSerializer
    admin_read_serializer_class = CategoryDetailSerializer
    public_read_serializer_class = CategoryPublicSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "slug", "created_at", "updated_at", "level"]
    filterset_class = CategoryFilterSet

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

    @action(detail=False, methods=["get"])
    def deleted(self, request):
        queryset = Category.objects.filter(is_deleted=True)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
