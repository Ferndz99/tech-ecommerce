import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Account
from catalog.models.brand import Brand
from catalog.models.category import Category
from catalog.models.specification import Specification
from catalog.models.product import Product
from catalog.models.specification import ProductSpecification


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
def category(db):
    return Category.objects.create(name="Phones")


@pytest.fixture
def brand(db):
    return Brand.objects.create(name="Test Brand")


@pytest.fixture
def product(db, category, brand):
    return Product.objects.create(
        name="Test Product",
        category=category,
        brand=brand
    )


@pytest.fixture
def spec_weight(db):
    return Specification.objects.create(name="Weight")


@pytest.fixture
def spec_battery(db):
    return Specification.objects.create(name="Batteryy")


@pytest.fixture
def product_spec_weight(db, product, spec_weight):
    return ProductSpecification.objects.create(
        product=product,
        specification=spec_weight,
        value="200g",
    )


@pytest.mark.django_db
class TestProductSpecificationViewSetList:
    def test_queryset_works(self):
        """El queryset debe ejecutarse correctamente."""
        from catalog.specifications.views import ProductSpecificationViewSet

        view = ProductSpecificationViewSet()
        queryset = view.get_queryset()

        try:
            list(queryset)
        except Exception as e:
            pytest.fail(f"Queryset failed: {str(e)}")

    def test_list_product_specifications_public(
        self, api_client, product_spec_weight
    ):
        """Cualquiera puede listar especificaciones de productos."""
        url = reverse("product-specification-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        results = response.data.get("results", response.data)
        values = [item["value"] for item in results]

        assert product_spec_weight.value in values


@pytest.mark.django_db
class TestProductSpecificationViewSetRetrieve:
    def test_retrieve_product_specification(
        self, api_client, product_spec_weight
    ):
        url = reverse(
            "product-specification-detail",
            kwargs={"pk": product_spec_weight.pk},
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["value"] == product_spec_weight.value

    def test_retrieve_nonexistent_product_specification(self, api_client):
        url = reverse(
            "product-specification-detail",
            kwargs={"pk": 9999},
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestProductSpecificationViewSetCreate:
    def test_create_product_specification_admin(
        self, api_client, admin_user, product, spec_battery
    ):
        api_client.force_authenticate(admin_user)

        url = reverse("product-specification-list")
        data = {
            "product": product.id,
            "specification_id": spec_battery.pk,
            "value": "4000 mAh",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert ProductSpecification.objects.filter(
            product=product,
            specification=spec_battery,
        ).exists()

    def test_create_product_specification_regular_user(
        self, api_client, regular_user, product, spec_battery
    ):
        api_client.force_authenticate(regular_user)

        url = reverse("product-specification-list")
        response = api_client.post(
            url,
            {
                "product": product.pk,
                "specification": spec_battery.pk,
                "value": "X",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_product_specification_unauthenticated(
        self, api_client, product, spec_battery
    ):
        url = reverse("product-specification-list")
        response = api_client.post(
            url,
            {
                "product": product.pk,
                "specification": spec_battery.pk,
                "value": "X",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProductSpecificationViewSetUpdate:
    def test_update_product_specification_admin(
        self, api_client, admin_user, product_spec_weight
    ):
        api_client.force_authenticate(admin_user)

        url = reverse(
            "product-specification-detail",
            kwargs={"pk": product_spec_weight.pk},
        )
        response = api_client.patch(
            url,
            {"value": "250g"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        product_spec_weight.refresh_from_db()
        assert product_spec_weight.value == "250 g"

    def test_update_product_specification_regular_user(
        self, api_client, regular_user, product_spec_weight
    ):
        api_client.force_authenticate(regular_user)

        url = reverse(
            "product-specification-detail",
            kwargs={"pk": product_spec_weight.pk},
        )
        response = api_client.patch(
            url,
            {"value": "X"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestProductSpecificationViewSetDelete:
    def test_delete_product_specification_admin(
        self, api_client, admin_user, product_spec_weight
    ):
        api_client.force_authenticate(admin_user)

        url = reverse(
            "product-specification-detail",
            kwargs={"pk": product_spec_weight.pk},
        )
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ProductSpecification.objects.filter(
            pk=product_spec_weight.pk
        ).exists()

    def test_delete_product_specification_regular_user(
        self, api_client, regular_user, product_spec_weight
    ):
        api_client.force_authenticate(regular_user)

        url = reverse(
            "product-specification-detail",
            kwargs={"pk": product_spec_weight.pk},
        )
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
