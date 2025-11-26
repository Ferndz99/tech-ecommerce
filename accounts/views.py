from django.conf import settings

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


from djoser.views import UserViewSet

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiExample,
)

from .serializers import (
    AccountLoginSerializer,
    CustomTokenObtainPairSerializer,
    ProblemDetailsSerializer,
    AccountLoginResponseSerializer,
    DetailResponseSerializer,
)


class CustomAccountViewSet(UserViewSet):
    """UserViewSet with extended documentation for OpenAPI/Swagger."""

    def set_username(self, request, *args, **kwargs):
        raise NotImplementedError("This endpoint is disabled.")

    def reset_username(self, request, *args, **kwargs):
        raise NotImplementedError("This endpoint is disabled.")

    def reset_username_confirm(self, request, *args, **kwargs):
        raise NotImplementedError("This endpoint is disabled.")


class AccountLoginAPIView(APIView):
    """
    API endpoint for user login.
    Validates credentials and returns a JWT access token.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Authentication"],
        summary="User login",
        description="Validates credentials and returns a JWT access token. Sets refresh token in a secure cookie.",
        request=AccountLoginSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successful login, returns access token.",
                response=AccountLoginResponseSerializer,
                examples=[
                    OpenApiExample(
                        "Successful Login",
                        summary="Successful Login Example",
                        description="Example response for a successful login.",
                        value={"access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."},
                        status_codes=["200"],
                    )
                ],
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid credentials or validation error.",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "Invalid Credentials",
                        summary="Invalid Credentials Example",
                        description="Example response for invalid login credentials.",
                        value={
                            "type": "https://example.com/probs/authentication",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "api/v1/accounts/login/",
                            "detail": "Account not found with the given credentials.",
                        },
                        status_codes=["400"],
                    ),
                    OpenApiExample(
                        "Validation Error",
                        summary="Validation Error Example",
                        description="Example response for validation errors.",
                        value={
                            "type": "https://example.com/probs/validation",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "api/v1/accounts/login/",
                            "detail": "The submitted data failed validation.",
                            "errors": [
                                {"field": "email", "message": "Email is required."},
                                {
                                    "field": "password",
                                    "message": "Password is required.",
                                },
                            ],
                        },
                        status_codes=["400"],
                    ),
                    OpenApiExample(
                        "Invalid Email Format",
                        summary="Invalid Email Format Example",
                        description="Example response for invalid email format.",
                        value={
                            "type": "https://example.com/probs/validation",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "api/v1/accounts/login/",
                            "detail": "The submitted data failed validation.",
                            "errors": [
                                {
                                    "field": "email",
                                    "message": "Please enter a valid email address.",
                                }
                            ],
                        },
                    ),
                ],
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Server error during login.",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "Server Error",
                        summary="Server Error Example",
                        description="Example response for server errors during login.",
                        value={
                            "type": "https://example.com/probs/server-error",
                            "status": 500,
                            "title": "Internal Server Error",
                            "instance": "api/v1/accounts/login/",
                            "detail": "An unexpected error occurred. Please try again later.",
                        },
                        status_codes=["500"],
                    )
                ],
            ),
        },
    )
    def post(self, request):
        login_serializer = AccountLoginSerializer(
            data=request.data, context={"request": request}
        )

        login_serializer.is_valid(raise_exception=True)
        user = login_serializer.validated_data["user"]  # type: ignore

        refresh = CustomTokenObtainPairSerializer.get_token(user)

        response = Response(
            {"access": str(refresh.access_token)},  # type: ignore
            status=status.HTTP_200_OK,  # type: ignore
        )

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=not settings.DEBUG,  # True en producción
            samesite="Lax" if settings.DEBUG else "None",
            max_age=7 * 24 * 60 * 60,  # 7 días
            path="/",
        )

        return response


class TokenRefreshView(APIView):
    """
    View to refresh the access token using the refresh token from the cookie.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Authentication"],
        summary="Refresh access token",
        description="Obtains a new access token using the refresh token stored in an HTTP-only cookie.",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="New access token obtained successfully.",
                response=AccountLoginResponseSerializer,
                examples=[
                    OpenApiExample(
                        "Successful Token Refresh",
                        summary="Successful Token Refresh Example",
                        description="Example response for a successful token refresh.",
                        value={"access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."},
                        status_codes=["200"],
                    )
                ],
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid or missing refresh token.",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "Missing Refresh Token",
                        summary="Missing Refresh Token Example",
                        description="Example response when refresh token is missing.",
                        value={
                            "type": "https://example.com/probs/authentication",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "api/v1/accounts/refresh/",
                            "detail": "Refresh token not found in cookies.",
                        },
                        status_codes=["400"],
                    ),
                    OpenApiExample(
                        "Invalid Refresh Token",
                        summary="Invalid Refresh Token Example",
                        description="Example response for invalid refresh token.",
                        value={
                            "type": "https://example.com/probs/authentication",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "api/v1/accounts/refresh/",
                            "detail": "Invalid or expired refresh token.",
                        },
                        status_codes=["400"],
                    ),
                ],
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Server error during logout.",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "Server Error",
                        summary="Server Error Example",
                        description="Example response for server errors during logout.",
                        value={
                            "type": "https://example.com/probs/server-error",
                            "status": 500,
                            "title": "Internal Server Error",
                            "instance": "api/v1/accounts/refresh/",
                            "detail": "An unexpected error occurred. Please try again later.",
                        },
                        status_codes=["500"],
                    )
                ],
            ),
        },
    )
    def post(self, request):
        """
        Obtain a new access token using the cookie's refresh token.
        """

        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            raise ValidationError({"error": ["Refresh token not found in cookies."]})

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            return Response({"access": access_token}, status=status.HTTP_200_OK)

        except TokenError as e:
            raise ValidationError({"error": ["Invalid or expired refresh token."]})
        except Exception as exc:
            raise ValidationError({"error": [f"Unexpected refresh error: {str(exc)}"]})


class AccountLogoutView(APIView):
    """
    View to logout by removing the refresh token cookie.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Authentication"],
        summary="User logout",
        description="Logs out the user by blacklisting the refresh token and deleting the cookie.",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successful logout.",
                response=DetailResponseSerializer,
                examples=[
                    OpenApiExample(
                        "Successful Logout",
                        summary="Successful Logout Example",
                        description="Example response for a successful logout.",
                        value={"detail": "Logged out successfully."},
                        status_codes=["200"],
                    )
                ],
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid or missing refresh token.",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "Missing Refresh Token",
                        summary="Missing Refresh Token Example",
                        description="Example response when refresh token is missing.",
                        value={
                            "type": "https://example.com/probs/authentication",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "api/v1/accounts/logout/",
                            "detail": "Refresh token not found in cookies.",
                        },
                        status_codes=["400"],
                    ),
                    OpenApiExample(
                        "Invalid Refresh Token",
                        summary="Invalid Refresh Token Example",
                        description="Example response for invalid refresh token.",
                        value={
                            "type": "https://example.com/probs/authentication",
                            "status": 400,
                            "title": "Validation Error",
                            "instance": "api/v1/accounts/logout/",
                            "detail": "Invalid or expired refresh token.",
                        },
                        status_codes=["400"],
                    ),
                ],
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Server error during logout.",
                response=ProblemDetailsSerializer,
                examples=[
                    OpenApiExample(
                        "Server Error",
                        summary="Server Error Example",
                        description="Example response for server errors during logout.",
                        value={
                            "type": "https://example.com/probs/server-error",
                            "status": 500,
                            "title": "Internal Server Error",
                            "instance": "api/v1/accounts/logout/",
                            "detail": "An unexpected error occurred. Please try again later.",
                        },
                        status_codes=["500"],
                    )
                ],
            ),
        },
    )
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            raise ValidationError({"error": ["Refresh token not found in cookies."]})

        try:
            refresh = RefreshToken(refresh_token)

            refresh.blacklist()

            response = Response(
                {"detail": "Logged out successfully."},
                status=status.HTTP_200_OK,
            )

            response.delete_cookie(
                key="refresh_token",
                samesite="Lax" if settings.DEBUG else "None",  # type: ignore
                path="/",  # type: ignore
            )

            return response

        except TokenError as e:
            raise ValidationError({"error": ["Invalid or expired refresh token."]})

        except Exception as exc:
            raise ValidationError({"error": [f"Unexpected logout error: {str(exc)}"]})
