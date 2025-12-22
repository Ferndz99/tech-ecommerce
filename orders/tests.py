import uuid
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Account
from catalog.models.brand import Brand
from catalog.models.category import Category
from catalog.models.product import Product
from catalog.models.product_variant import ProductVariant
from orders.models import Order


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return Account.objects.create_user(
        email="admin@test.com",
        password="admin123",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def regular_user(db):
    return Account.objects.create_user(
        email="user@test.com",
        password="user123",
    )


@pytest.fixture
def order_user(db, regular_user):
    return Order.objects.create(account=regular_user)


@pytest.fixture
def order_guest(db):
    return Order.objects.create(
        account=None,
        access_token=uuid.uuid4(),
    )


@pytest.fixture
def category(db):
    return Category.objects.create(name="Phones")


@pytest.fixture
def brand(db):
    return Brand.objects.create(name="Apple")


@pytest.fixture
def product(db, category, brand):
    return Product.objects.create(
        name="iPhone 15",
        category=category,
        brand=brand,
    )


@pytest.fixture
def product_variant(db, product):
    return ProductVariant.objects.create(
        product=product,
        sku="IP15-001",
        price=999,
        stock=10,
    )


@pytest.mark.django_db
class TestOrderViewSetList:
    def test_list_orders_admin(self, api_client, admin_user, order_user):
        api_client.force_authenticate(admin_user)

        url = reverse("orders-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_list_orders_regular_user_forbidden(self, api_client, regular_user):
        api_client.force_authenticate(regular_user)

        url = reverse("orders-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_orders_unauthenticated(self, api_client):
        url = reverse("orders-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestOrderViewSetRetrieve:
    def test_retrieve_order_admin(self, api_client, admin_user, order_user):
        api_client.force_authenticate(admin_user)

        url = reverse("orders-detail", kwargs={"pk": order_user.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == order_user.id

    def test_retrieve_order_regular_user_forbidden(
        self, api_client, regular_user, order_user
    ):
        api_client.force_authenticate(regular_user)

        url = reverse("orders-detail", kwargs={"pk": order_user.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_order_not_found(self, api_client, admin_user):
        api_client.force_authenticate(admin_user)

        url = reverse("orders-detail", kwargs={"pk": 9999})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestOrderViewSetCreate:
    def test_create_order_authenticated_user(
        self, api_client, regular_user, product_variant
    ):
        api_client.force_authenticate(regular_user)

        url = reverse("orders-list")
        data = {
            "customer_email": "test@test.com",
            "customer_name": "Test User",
            "shipping_address_line1": "Calle falsa 123",
            "shipping_city": "Santiago",
            "shipping_state": "RM",
            "shipping_postal_code": "123456",
            "items": [
                {
                    "product_variant_id": product_variant.id,
                    "quantity": 1,
                }
            ],
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_order_guest(self, api_client, product_variant):
        url = reverse("orders-list")
        data = {
            "customer_email": "test@test.com",
            "customer_name": "Test User",
            "shipping_address_line1": "Calle falsa 123",
            "shipping_city": "Santiago",
            "shipping_state": "RM",
            "shipping_postal_code": "123456",
            "items": [
                {
                    "product_variant_id": product_variant.id,
                    "quantity": 1,
                }
            ],
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.filter(account__isnull=True).exists()


@pytest.mark.django_db
class TestGuestOrderDetailView:
    def test_guest_order_detail_valid_token(self, api_client, order_guest):
        url = reverse(
            "guest-order-detail",
            kwargs={"token": order_guest.access_token},
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == order_guest.id

    def test_guest_order_detail_invalid_token(
        self, api_client, order_guest, monkeypatch
    ):
        monkeypatch.setattr(
            Order,
            "is_guest_token_valid",
            lambda self: False,
        )

        url = reverse(
            "guest-order-detail",
            kwargs={"token": order_guest.access_token},
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_guest_order_not_found(self, api_client):
        url = reverse(
            "guest-order-detail",
            kwargs={"token": uuid.uuid4()},
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
