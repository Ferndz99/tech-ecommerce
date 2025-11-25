import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.models import Account



@pytest.mark.django_db
class TestLogin:
    def test_login_success(self):
        Account.objects.create_user(
            email="test@example.com", password="123456", is_active=True
        )

        client = APIClient()
        response = client.post(
            reverse("account-login"),
            {"email": "test@example.com", "password": "123456"},
            format="json",
        )

        assert response.status_code == 200
        assert "refresh" not in response.data
        assert "access" in response.data
        assert "refresh_token" in response.cookies

    def test_login_invalid_password(self):
        Account.objects.create_user(
            email="wrong@example.com", password="abcdef", is_active=True
        )

        client = APIClient()
        response = client.post(
            reverse("account-login"),
            {"email": "wrong@example.com", "password": "incorrect"},
            format="json",
        )

        assert response.status_code == 400

    def test_login_inactive_user(self):
        Account.objects.create_user(
            email="inactive@example.com", password="abcdef", is_active=False
        )

        client = APIClient()
        response = client.post(
            reverse("account-login"),
            {"email": "inactive@example.com", "password": "abcdef"},
            format="json",
        )

        assert response.status_code == 400
        assert (
            response.data["detail"].lower()
            == "account not found with the given credentials."
        )
