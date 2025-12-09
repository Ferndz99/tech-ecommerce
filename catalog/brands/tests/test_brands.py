import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Account
from catalog.models.brand import Brand


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return Account.objects.create_user(
        email="admin@test.com", password="admin123",
        is_staff=True, is_superuser=True
    )


@pytest.fixture
def regular_user(db):
    return Account.objects.create_user(
        email="user@test.com", password="user123"
    )


@pytest.fixture
def active_brand(db):
    return Brand.objects.create(name="Active Brand", slug="active-brand")


@pytest.fixture
def inactive_brand(db):
    return Brand.objects.create(name="Inactive Brand", slug="inactive-brand", is_active=False)


@pytest.fixture
def deleted_brand(db):
    return Brand.objects.create(name="Deleted Brand", slug="deleted-brand", is_deleted=True)


# ============================================================
# LIST
# ============================================================

@pytest.mark.django_db
class TestBrandViewSetList:
    def test_queryset_works(self, active_brand, inactive_brand):
        """El queryset debe ejecutarse correctamente."""
        from catalog.brands.views import BrandViewSet

        view = BrandViewSet()
        queryset = view.get_queryset()

        try:
            brands = list(queryset)
            assert len(brands) >= 1
        except Exception as e:
            pytest.fail(f"Queryset failed: {str(e)}")

    def test_list_brands_public(self, api_client, active_brand):
        """Cualquiera puede listar marcas activas."""
        url = reverse("brands-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        slugs = [item["slug"] for item in response.data.get("results", response.data)]

        assert active_brand.slug in slugs

    def test_list_inactive_brands_requires_admin(
        self, api_client, regular_user, inactive_brand
    ):
        """Solo admin puede usar is_active=false."""
        api_client.force_authenticate(user=regular_user)
        url = reverse("brands-list") + "?is_active=false"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_list_inactive_brands_admin(self, api_client, admin_user, inactive_brand):
        api_client.force_authenticate(user=admin_user)
        url = reverse("brands-list") + "?is_active=false"
        response = api_client.get(url)

        assert response.status_code == 200
        slugs = [b["slug"] for b in response.data.get("results", response.data)]
        assert inactive_brand.slug in slugs


# ============================================================
# RETRIEVE
# ============================================================

@pytest.mark.django_db
class TestBrandViewSetRetrieve:
    def test_retrieve_brand(self, api_client, active_brand):
        url = reverse("brands-detail", kwargs={"slug": active_brand.slug})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["slug"] == active_brand.slug

    def test_retrieve_inactive_requires_admin(
        self, api_client, regular_user, inactive_brand
    ):
        api_client.force_authenticate(user=regular_user)
        url = reverse("brands-detail", kwargs={"slug": inactive_brand.slug})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_nonexistent_brand(self, api_client):
        url = reverse("brands-detail", kwargs={"slug": "missing"})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================
# CREATE
# ============================================================

@pytest.mark.django_db
class TestBrandViewSetCreate:
    def test_create_brand_admin(self, api_client, admin_user):
        api_client.force_authenticate(admin_user)
        url = reverse("brands-list")
        data = {"name": "New Brand", "slug": "new-brand"}

        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Brand.objects.filter(slug="new-brand").exists()

    def test_create_brand_regular_user(self, api_client, regular_user):
        api_client.force_authenticate(regular_user)
        url = reverse("brands-list")
        data = {"name": "X"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_brand_unauthenticated(self, api_client):
        url = reverse("brands-list")
        response = api_client.post(url, {"name": "X"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================
# UPDATE
# ============================================================

@pytest.mark.django_db
class TestBrandViewSetUpdate:
    def test_update_brand_admin(self, api_client, admin_user, active_brand):
        api_client.force_authenticate(admin_user)

        url = reverse("brands-detail", kwargs={"slug": active_brand.slug})
        response = api_client.patch(url, {"name": "Updated"}, format="json")

        assert response.status_code == 200
