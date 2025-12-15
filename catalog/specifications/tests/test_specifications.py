import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Account
from catalog.models.specification import Specification


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
def spec_weight(db):
    return Specification.objects.create(name="Weight")


@pytest.fixture
def spec_battery(db):
    return Specification.objects.create(name="Battery Capacity")


@pytest.mark.django_db
class TestSpecificationViewSetList:
    def test_queryset_works(self):
        """El queryset debe ejecutarse correctamente."""
        from catalog.specifications.views import SpecificationViewSet

        view = SpecificationViewSet()
        queryset = view.get_queryset()

        try:
            list(queryset)
        except Exception as e:
            pytest.fail(f"Queryset failed: {str(e)}")

    def test_list_specifications_public(self, api_client, spec_weight):
        """Cualquiera puede listar especificaciones."""
        url = reverse("specification-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        names = [item["name"] for item in response.data.get("results", response.data)]

        assert spec_weight.name in names


@pytest.mark.django_db
class TestSpecificationViewSetRetrieve:
    def test_retrieve_specification(self, api_client, spec_weight):
        url = reverse(
            "specification-detail",
            kwargs={"pk": spec_weight.pk},
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == spec_weight.name

    def test_retrieve_nonexistent_specification(self, api_client):
        url = reverse("specification-detail", kwargs={"pk": 9999})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestSpecificationViewSetCreate:
    def test_create_specification_admin(self, api_client, admin_user):
        api_client.force_authenticate(admin_user)

        url = reverse("specification-list")
        data = {"name": "Screen Size"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Specification.objects.filter(name="Screen Size").exists()

    def test_create_specification_regular_user(self, api_client, regular_user):
        api_client.force_authenticate(regular_user)

        url = reverse("specification-list")
        response = api_client.post(url, {"name": "X"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_specification_unauthenticated(self, api_client):
        url = reverse("specification-list")
        response = api_client.post(url, {"name": "X"}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestSpecificationViewSetUpdate:
    def test_update_specification_admin(
        self, api_client, admin_user, spec_weight
    ):
        api_client.force_authenticate(admin_user)

        url = reverse(
            "specification-detail",
            kwargs={"pk": spec_weight.pk},
        )
        response = api_client.patch(url, {"name": "Product Weight"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        spec_weight.refresh_from_db()
        assert spec_weight.name == "Product Weight"

    def test_update_specification_regular_user(
        self, api_client, regular_user, spec_weight
    ):
        api_client.force_authenticate(regular_user)

        url = reverse(
            "specification-detail",
            kwargs={"pk": spec_weight.pk},
        )
        response = api_client.patch(url, {"name": "X"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestSpecificationViewSetDelete:
    def test_delete_specification_admin(
        self, api_client, admin_user, spec_battery
    ):
        api_client.force_authenticate(admin_user)

        url = reverse(
            "specification-detail",
            kwargs={"pk": spec_battery.pk},
        )
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Specification.objects.filter(pk=spec_battery.pk).exists()

    def test_delete_specification_regular_user(
        self, api_client, regular_user, spec_battery
    ):
        api_client.force_authenticate(regular_user)

        url = reverse(
            "specification-detail",
            kwargs={"pk": spec_battery.pk},
        )
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
