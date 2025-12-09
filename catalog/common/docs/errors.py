from drf_spectacular.utils import OpenApiResponse, OpenApiExample
from rest_framework import status
from catalog.common.serializers import ProblemDetailsSerializer


def error_401(instance_path: str):
    return {
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            description="Authentication credentials were not provided or are invalid.",
            response=ProblemDetailsSerializer,
            examples=[
                OpenApiExample(
                    "Missing Authorization header",
                    value={
                        "type": "https://httpstatuses.com/401",
                        "status": 401,
                        "title": "Unauthorized",
                        "instance": instance_path,
                        "detail": "Authentication credentials were not provided.",
                    },
                )
            ],
        )
    }


def error_403(instance_path: str):
    return {
        status.HTTP_403_FORBIDDEN: OpenApiResponse(
            description="Forbidden",
            response=ProblemDetailsSerializer,
            examples=[
                OpenApiExample(
                    "Forbidden",
                    value={
                        "type": "https://httpstatuses.com/403",
                        "status": 403,
                        "title": "Forbidden",
                        "instance": instance_path,
                        "detail": "You do not have permission to perform this action.",
                    },
                )
            ],
        )
    }


def error_404(instance_path: str):
    return {
        status.HTTP_404_NOT_FOUND: OpenApiResponse(
            description="Resource not found",
            response=ProblemDetailsSerializer,
            examples=[
                OpenApiExample(
                    "Not Found",
                    value={
                        "type": "https://httpstatuses.com/404",
                        "status": 404,
                        "title": "Not Found",
                        "instance": instance_path,
                        "detail": "The requested resource was not found.",
                    },
                )
            ],
        )
    }


def error_500(instance_path: str):
    return {
        status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
            description="Server error",
            response=ProblemDetailsSerializer,
            examples=[
                OpenApiExample(
                    "Internal Server Error",
                    value={
                        "type": "https://httpstatuses.com/500",
                        "status": 500,
                        "title": "Internal Server Error",
                        "instance": instance_path,
                        "detail": "An unexpected error occurred. Please try again later.",
                    },
                )
            ],
        )
    }


# 🔥 Función para combinar errores comunes
def default_error_responses(instance_path: str):
    """
    Retorna: 401, 403, 404, 500 con una sola llamada.
    """
    combined = {}
    combined.update(error_401(instance_path))
    combined.update(error_403(instance_path))
    combined.update(error_404(instance_path))
    combined.update(error_500(instance_path))
    return combined
