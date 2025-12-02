import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from accounts.models import Account
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
class TestRefresh:
    def test_refresh_success(self):
        user = Account.objects.create_user(
            email="test@example.com",
            password="123456",
            is_active=True
        )

        refresh = str(RefreshToken.for_user(user))

        client = APIClient()
        client.cookies["refresh_token"] = refresh

        response = client.post(reverse("token-refresh"))

        assert response.status_code == 200
        assert "access" in response.data

    def test_refresh_without_cookie(self):
        client = APIClient()
        response = client.post(reverse("token-refresh"))

        assert response.status_code == 400
        assert response.data["detail"] == "Refresh token not found in cookies."

    def test_refresh_invalid_token(self):
        client = APIClient()
        client.cookies["refresh_token"] = "invalid.token.value"

        response = client.post(reverse("token-refresh"))

        assert response.status_code == 400
        assert response.data["detail"] == "Invalid or expired refresh token."
