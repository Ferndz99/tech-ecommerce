import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from accounts.models import Account
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
class TestLogout:
    def test_logout_success(self):
        user = Account.objects.create_user(
            email="test@example.com",
            password="123456",
            is_active=True
        )

        refresh = str(RefreshToken.for_user(user))

        client = APIClient()
        client.cookies["refresh_token"] = refresh

        response = client.post(reverse("account-logout"))

        assert response.status_code == 200


