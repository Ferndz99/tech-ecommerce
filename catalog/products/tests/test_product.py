import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Account
from catalog.models.category import Category
from catalog.models.product import Product
from catalog.models.brand import Brand


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
def active_brand(db):
    return Brand.objects.create(name="Active Brand", slug="active-brand")


@pytest.fixture
def parent_category(db):
    """Categoría padre."""
    return Category.objects.create(
        name="Parent Category", slug="parent-category", is_deleted=False
    )


@pytest.fixture
def child_category(db, parent_category):
    """Categoría hija."""
    return Category.objects.create(
        name="Child Category",
        slug="child-category",
        parent=parent_category,
        is_deleted=False,
    )


@pytest.fixture
def product(db, parent_category, active_brand):
    return Product.objects.create(
        name="Test Product",
        slug="test-product",
        category=parent_category,
        brand=active_brand,
    )


@pytest.mark.django_db
class TestProductViewSetList:
    def test_list_products_public(self, api_client, product):
        url = reverse("product-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", response.data)

        slugs = [item["slug"] for item in results]
        assert product.slug in slugs


@pytest.mark.django_db
class TestProductViewSetRetrieve:
    def test_retrieve_product_public(self, api_client, product):
        url = reverse("product-detail", kwargs={"slug": product.slug})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["slug"] == product.slug

    def test_retrieve_nonexistent_product(self, api_client):
        url = reverse("product-detail", kwargs={"slug": "missing"})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestProductViewSetCreate:
    def test_create_product_admin(
        self, api_client, admin_user, parent_category, active_brand
    ):
        api_client.force_authenticate(admin_user)

        url = reverse("product-list")
        data = {
            "name": "New Product",
            "slug": "new-product",
            "category": parent_category.pk,
            "brand": active_brand.pk,
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Product.objects.filter(slug="new-product").exists()

    def test_create_product_regular_user(self, api_client, regular_user):
        api_client.force_authenticate(regular_user)

        url = reverse("product-list")
        response = api_client.post(url, {"name": "X"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_product_unauthenticated(self, api_client):
        url = reverse("product-list")
        response = api_client.post(url, {"name": "X"}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProductViewSetCreateVariant:
    def test_create_variant_admin(self, api_client, admin_user, product):
        api_client.force_authenticate(admin_user)

        url = reverse(
            "product-create-variant",
            kwargs={"slug": product.slug},
        )

        data = {
            "sku": "SKU-001",
            "price": 999,
            "stock": 10,
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["sku"] == "SKU-001"

    def test_create_variant_regular_user(self, api_client, regular_user, product):
        api_client.force_authenticate(regular_user)

        url = reverse(
            "product-create-variant",
            kwargs={"slug": product.slug},
        )

        response = api_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_variant_unauthenticated(self, api_client, product):
        url = reverse(
            "product-create-variant",
            kwargs={"slug": product.slug},
        )

        response = api_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
