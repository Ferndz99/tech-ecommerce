import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Account
from catalog.models.attribute import Attribute, AttributeValue
from catalog.utils import normalize_spec_value


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
def attribute_color(db):
    return Attribute.objects.create(name="Color")


@pytest.fixture
def attribute_size(db):
    return Attribute.objects.create(name="Size")


@pytest.fixture
def value_red(db, attribute_color):
    return AttributeValue.objects.create(
        attribute=attribute_color,
        value="Red",
    )


@pytest.fixture
def value_blue(db, attribute_color):
    return AttributeValue.objects.create(
        attribute=attribute_color,
        value="Blue",
    )


@pytest.mark.django_db
class TestAttributeValueViewSetList:
    def test_queryset_works(self):
        """El queryset debe ejecutarse correctamente."""
        from catalog.attributes.views import AttributeValueViewSet

        view = AttributeValueViewSet()
        queryset = view.get_queryset()

        try:
            list(queryset)
        except Exception as e:
            pytest.fail(f"Queryset failed: {str(e)}")

    def test_list_attribute_values_public(self, api_client, value_red, value_blue):
        """Cualquiera puede listar valores de atributos."""
        url = reverse("attribute-value-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        values = [item["value"] for item in response.data.get("results", response.data)]

        assert value_red.value in values
        assert value_blue.value in values

    def test_list_attribute_values_ordering(self, api_client, value_red, value_blue):
        """Debe respetar el ordering definido en el modelo."""
        url = reverse("attribute-value-list")
        response = api_client.get(url)

        values = [item["value"] for item in response.data.get("results", response.data)]
        assert values == sorted(values)


@pytest.mark.django_db
class TestAttributeValueViewSetRetrieve:
    def test_retrieve_attribute_value(self, api_client, value_red):
        url = reverse(
            "attribute-value-detail",
            kwargs={"pk": value_red.pk},
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["value"] == value_red.value

    def test_retrieve_nonexistent_attribute_value(self, api_client):
        url = reverse("attribute-value-detail", kwargs={"pk": 9999})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAttributeValueViewSetCreate:
    def test_create_attribute_value_admin(
        self, api_client, admin_user, attribute_color
    ):
        api_client.force_authenticate(admin_user)

        url = reverse("attribute-value-list")
        data = {
            "attribute": attribute_color.pk,
            "value": "Green",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        av = AttributeValue.objects.get(attribute=attribute_color)
        assert av.value == normalize_spec_value("Green")

    def test_create_attribute_value_duplicate(self, api_client, admin_user, value_red):
        """No se puede repetir (attribute, value)."""
        api_client.force_authenticate(admin_user)

        url = reverse("attribute-value-list")
        data = {
            "attribute": value_red.attribute.pk,
            "value": value_red.value,
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_attribute_value_regular_user(
        self, api_client, regular_user, attribute_color
    ):
        api_client.force_authenticate(regular_user)

        url = reverse("attribute-value-list")
        response = api_client.post(
            url,
            {"attribute": attribute_color.pk, "value": "X"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_attribute_value_unauthenticated(self, api_client, attribute_color):
        url = reverse("attribute-value-list")
        response = api_client.post(
            url,
            {"attribute": attribute_color.pk, "value": "X"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAttributeValueViewSetUpdate:
    def test_update_attribute_value_admin(self, api_client, admin_user, value_red):
        api_client.force_authenticate(admin_user)

        url = reverse(
            "attribute-value-detail",
            kwargs={"pk": value_red.pk},
        )
        response = api_client.patch(url, {"value": "Dark Red"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        value_red.refresh_from_db()
        assert value_red.value == normalize_spec_value("Dark Red")

    def test_update_attribute_value_regular_user(
        self, api_client, regular_user, value_red
    ):
        api_client.force_authenticate(regular_user)

        url = reverse(
            "attribute-value-detail",
            kwargs={"pk": value_red.pk},
        )
        response = api_client.patch(url, {"value": "X"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAttributeValueViewSetDelete:
    def test_delete_attribute_value_admin(self, api_client, admin_user, value_blue):
        api_client.force_authenticate(admin_user)

        url = reverse(
            "attribute-value-detail",
            kwargs={"pk": value_blue.pk},
        )
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not AttributeValue.objects.filter(pk=value_blue.pk).exists()

    def test_delete_attribute_value_regular_user(
        self, api_client, regular_user, value_blue
    ):
        api_client.force_authenticate(regular_user)

        url = reverse(
            "attribute-value-detail",
            kwargs={"pk": value_blue.pk},
        )
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
