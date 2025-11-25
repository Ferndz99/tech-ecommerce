from django.conf import settings

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


from djoser.views import UserViewSet

from .serializers import AccountLoginSerializer, CustomTokenObtainPairSerializer


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

    def post(self, request):
        """
        Obtain a new access token using the cookie's refresh token.
        """

        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            raise ValidationError("Refresh token not found in cookies.")

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            return Response({"access": access_token}, status=status.HTTP_200_OK)

        except TokenError as e:
            raise ValidationError(
                {"refresh_token": ["Invalid or expired refresh token."]}
            )


class AccountLogoutView(APIView):
    """
    View to logout by removing the refresh token cookie.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            raise ValidationError("Refresh token not provided in cookies.")

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

        except TokenError:
            raise AuthenticationFailed("Invalid or expired refresh token")

        except Exception as exc:
            raise ValidationError(f"Unexpected logout error: {str(exc)}")
