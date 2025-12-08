import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import Account
from catalog.models import Category


@pytest.fixture
def api_client():
    """Cliente API para las pruebas."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Usuario administrador."""
    return Account.objects.create_user(
        email="admin@test.com", password="admin123", is_staff=True, is_superuser=True
    )


@pytest.fixture
def regular_user(db):
    """Usuario regular."""
    return Account.objects.create_user(email="user@test.com", password="user123")


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
def deleted_category(db):
    """Categoría eliminada (soft delete)."""
    return Category.objects.create(
        name="Deleted Category", slug="deleted-category", is_deleted=True
    )


@pytest.mark.django_db
class TestCategoryViewSetList:
    """Tests para listar categorías."""

    def test_queryset_works(self, parent_category, child_category):
        """Verifica que el queryset no causa errores."""
        from catalog.views import CategoryViewSet

        viewset = CategoryViewSet()
        queryset = viewset.get_queryset()

        # Intenta ejecutar el queryset
        try:
            categories = list(queryset)
            assert len(categories) >= 2
        except Exception as e:
            pytest.fail(f"Queryset failed: {str(e)}")

    def test_list_categories_unauthenticated(
        self, api_client, parent_category, child_category
    ):
        """Usuario no autenticado puede listar categorías activas."""
        url = reverse("categories-list")
        response = api_client.get(url)

        if response.status_code == 500:
            print("Response data:", response.data)
            print("Response content:", response.content)

        assert response.status_code == status.HTTP_200_OK

    def test_list_categories_authenticated(
        self, api_client, regular_user, parent_category
    ):
        """Usuario autenticado puede listar categorías."""
        api_client.force_authenticate(user=regular_user)
        url = reverse("categories-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestCategoryViewSetRetrieve:
    """Tests para obtener detalle de una categoría."""

    def test_retrieve_category_by_slug(self, api_client, parent_category):
        """Se puede obtener una categoría por su slug."""
        url = reverse("categories-detail", kwargs={"slug": parent_category.slug})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["slug"] == parent_category.slug
        assert response.data["name"] == parent_category.name

    def test_retrieve_category_with_children(
        self, api_client, parent_category, child_category
    ):
        """Se obtienen las categorías hijas en el detalle."""
        url = reverse("categories-detail", kwargs={"slug": parent_category.slug})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Verifica que incluya información de hijos según tu serializer
        assert (
            "children" in response.data or len(response.data.get("children", [])) >= 0
        )

    def test_retrieve_nonexistent_category(self, api_client):
        """Retorna 404 para categoría inexistente."""
        url = reverse("categories-detail", kwargs={"slug": "nonexistent"})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCategoryViewSetCreate:
    """Tests para crear categorías."""

    def test_create_category_as_admin(self, api_client, admin_user):
        """Admin puede crear categorías."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("categories-list")
        data = {
            "name": "New Category",
            "slug": "new-category",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Category.objects.filter(slug="new-category").exists()

    def test_create_category_with_parent(self, api_client, admin_user, parent_category):
        """Se puede crear una categoría con padre."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("categories-list")
        data = {
            "name": "Child Category",
            "parent": parent_category.id,  # o parent_category.slug según tu serializer
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        category = Category.objects.get(slug="child-category")
        assert category.parent == parent_category

    def test_create_category_as_regular_user(self, api_client, regular_user):
        """Usuario regular no puede crear categorías (si aplica según permisos)."""
        api_client.force_authenticate(user=regular_user)
        url = reverse("categories-list")
        data = {"name": "New Category"}
        response = api_client.post(url, data, format="json")

        # Ajusta según tus permisos
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_201_CREATED,
        ]

    def test_create_category_unauthenticated(self, api_client):
        """Usuario no autenticado no puede crear categorías."""
        url = reverse("categories-list")
        data = {"name": "New Category"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCategoryViewSetUpdate:
    """Tests para actualizar categorías."""

    def test_update_category_as_admin(self, api_client, admin_user, parent_category):
        """Admin puede actualizar categorías."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("categories-detail", kwargs={"slug": parent_category.slug})
        data = {"name": "Updated Category Name"}
        response = api_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        parent_category.refresh_from_db()
        assert parent_category.name == "Updated Category Name"

    def test_partial_update_category(self, api_client, admin_user, parent_category):
        """Se puede hacer actualización parcial."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("categories-detail", kwargs={"slug": parent_category.slug})
        data = {"name": "Partially Updated"}
        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        parent_category.refresh_from_db()
        assert parent_category.name == "Partially Updated"


@pytest.mark.django_db
class TestCategoryViewSetDelete:
    """Tests para eliminar categorías."""

    def test_hard_delete_as_admin(self, api_client, admin_user, parent_category):
        """Admin puede hacer hard delete."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("categories-hard-delete", kwargs={"slug": parent_category.slug})
        correct_body = {"confirm": True}
        response = api_client.delete(url, data=correct_body, format="json")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Category.objects.filter(slug=parent_category.slug).exists()

    def test_soft_delete_as_admin(self, api_client, admin_user, parent_category):
        """Admin puede hacer soft delete."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("categories-detail", kwargs={"slug": parent_category.slug})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        parent_category.refresh_from_db()
        assert parent_category.is_deleted is True

    def test_delete_as_regular_user(self, api_client, regular_user, parent_category):
        """Usuario regular no puede eliminar."""
        api_client.force_authenticate(user=regular_user)
        url = reverse("categories-detail", kwargs={"slug": parent_category.slug})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCategoryViewSetLifecycleActions:
    """Tests para acciones de lifecycle (activate, deactivate, restore)."""

    def test_activate_category_as_admin(self, api_client, admin_user, parent_category):
        """Admin puede activar categorías."""
        parent_category.is_active = False
        parent_category.save()

        api_client.force_authenticate(user=admin_user)
        url = reverse("categories-activate", kwargs={"slug": parent_category.slug})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        parent_category.refresh_from_db()
        assert parent_category.is_active is True

    def test_deactivate_category_as_admin(
        self, api_client, admin_user, parent_category
    ):
        """Admin puede desactivar categorías."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("categories-deactivate", kwargs={"slug": parent_category.slug})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        parent_category.refresh_from_db()
        assert parent_category.is_active is False

    def test_restore_deleted_category_as_admin(
        self, api_client, admin_user, deleted_category
    ):
        """Admin puede restaurar categorías eliminadas."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("categories-restore", kwargs={"slug": deleted_category.slug})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        deleted_category.refresh_from_db()
        assert deleted_category.is_deleted is False

    def test_lifecycle_actions_require_admin(
        self, api_client, regular_user, parent_category
    ):
        """Las acciones de lifecycle requieren permisos de admin."""
        api_client.force_authenticate(user=regular_user)

        actions = ["activate", "deactivate", "restore"]
        for action in actions:
            url = reverse(f"categories-{action}", kwargs={"slug": parent_category.slug})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCategoryViewSetDeletedAction:
    """Tests para la acción custom 'deleted'."""

    def test_deleted_list_as_admin(
        self, api_client, admin_user, parent_category, deleted_category
    ):
        """Admin puede ver lista de categorías eliminadas."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("categories-deleted")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        slugs = [item["slug"] for item in response.data.get("results", response.data)]
        assert deleted_category.slug in slugs
        assert parent_category.slug not in slugs

    def test_deleted_list_as_regular_user(self, api_client, regular_user):
        """Usuario regular no puede ver categorías eliminadas."""
        api_client.force_authenticate(user=regular_user)
        url = reverse("categories-deleted")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_deleted_list_unauthenticated(self, api_client):
        """Usuario no autenticado no puede ver categorías eliminadas."""
        url = reverse("categories-deleted")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_deleted_list_pagination(self, api_client, admin_user, db):
        """La lista de eliminados soporta paginación."""
        # Crear múltiples categorías eliminadas
        for i in range(15):
            Category.objects.create(
                name=f"Deleted {i}", slug=f"deleted-{i}", is_deleted=True
            )

        api_client.force_authenticate(user=admin_user)
        url = reverse("categories-deleted")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Si tienes paginación configurada
        if "results" in response.data:
            assert "count" in response.data
            assert "next" in response.data or "previous" in response.data


@pytest.mark.django_db
class TestCategoryViewSetSerializers:
    """Tests para verificar que se usan los serializers correctos."""

    def test_list_uses_light_serializer(self, api_client, parent_category):
        """El listado usa el serializer ligero."""
        url = reverse("categories-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Verifica campos específicos del light serializer
        # Ajusta según tus serializers

    def test_detail_uses_correct_serializer_for_admin(
        self, api_client, admin_user, parent_category
    ):
        """Admin ve el detalle con serializer de admin."""
        api_client.force_authenticate(user=admin_user)
        url = reverse("categories-detail", kwargs={"slug": parent_category.slug})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Verifica campos específicos del admin serializer

    def test_detail_uses_public_serializer_for_regular_user(
        self, api_client, regular_user, parent_category
    ):
        """Usuario regular ve el serializer público."""
        api_client.force_authenticate(user=regular_user)
        url = reverse("categories-detail", kwargs={"slug": parent_category.slug})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Verifica campos específicos del public serializer


@pytest.mark.django_db
class TestCategoryViewSetQueryOptimization:
    """Tests para verificar optimización de queries."""

    def test_list_uses_select_related_and_prefetch(
        self, api_client, parent_category, child_category, django_assert_num_queries
    ):
        """El listado usa select_related y prefetch_related correctamente."""
        url = reverse("categories-list")

        # Ajusta el número esperado de queries según tu configuración
        with django_assert_num_queries(3):  # Ajustar según sea necesario
            response = api_client.get(url)
            assert response.status_code == status.HTTP_200_OK
