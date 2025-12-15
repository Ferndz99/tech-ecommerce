import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Account
from catalog.models.attribute import Attribute



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



@pytest.mark.django_db
class TestAttributeViewSetList:
    def test_queryset_works(self):
        """El queryset debe ejecutarse correctamente."""
        from catalog.attributes.views import AttributeViewSet

        view = AttributeViewSet()
        queryset = view.get_queryset()

        try:
            list(queryset)
        except Exception as e:
            pytest.fail(f"Queryset failed: {str(e)}")

    def test_list_attributes_public(self, api_client, attribute_color):
        """Cualquiera puede listar atributos."""
        url = reverse("attribute-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        names = [item["name"] for item in response.data.get("results", response.data)]

        assert attribute_color.name in names



@pytest.mark.django_db
class TestAttributeViewSetRetrieve:
    def test_retrieve_attribute(self, api_client, attribute_color):
        url = reverse(
            "attribute-detail",
            kwargs={"pk": attribute_color.pk},
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == attribute_color.name

    def test_retrieve_nonexistent_attribute(self, api_client):
        url = reverse("attribute-detail", kwargs={"pk": 9999})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAttributeViewSetCreate:
    def test_create_attribute_admin(self, api_client, admin_user):
        api_client.force_authenticate(admin_user)

        url = reverse("attribute-list")
        data = {"name": "Material"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Attribute.objects.filter(name="Material").exists()

    def test_create_attribute_regular_user(self, api_client, regular_user):
        api_client.force_authenticate(regular_user)

        url = reverse("attribute-list")
        response = api_client.post(url, {"name": "X"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_attribute_unauthenticated(self, api_client):
        url = reverse("attribute-list")
        response = api_client.post(url, {"name": "X"}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAttributeViewSetUpdate:
    def test_update_attribute_admin(self, api_client, admin_user, attribute_color):
        api_client.force_authenticate(admin_user)

        url = reverse(
            "attribute-detail",
            kwargs={"pk": attribute_color.pk},
        )
        response = api_client.patch(url, {"name": "Colour"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        attribute_color.refresh_from_db()
        assert attribute_color.name == "Colour"

    def test_update_attribute_regular_user(
        self, api_client, regular_user, attribute_color
    ):
        api_client.force_authenticate(regular_user)

        url = reverse(
            "attribute-detail",
            kwargs={"pk": attribute_color.pk},
        )
        response = api_client.patch(url, {"name": "X"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAttributeViewSetDelete:
    def test_delete_attribute_admin(self, api_client, admin_user, attribute_size):
        api_client.force_authenticate(admin_user)

        url = reverse(
            "attribute-detail",
            kwargs={"pk": attribute_size.pk},
        )
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Attribute.objects.filter(pk=attribute_size.pk).exists()

    def test_delete_attribute_regular_user(
        self, api_client, regular_user, attribute_size
    ):
        api_client.force_authenticate(regular_user)

        url = reverse(
            "attribute-detail",
            kwargs={"pk": attribute_size.pk},
        )
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
