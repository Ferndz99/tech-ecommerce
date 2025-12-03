from django.db import models, transaction
from django.core.exceptions import ValidationError

from mptt.models import MPTTModel, TreeForeignKey

from .base import LifeCycleMixin, TimeStampedMixin
from catalog.utils import generate_unique_slug


class Category(MPTTModel, LifeCycleMixin, TimeStampedMixin):
    """
    Product categories with hierarchical structure using MPTT.

    Notes:
    - unique_together on (parent, name) allows same name under different parents.
    - Slug is generated once on creation and never changes.
    - Life cycle methods operate on subtrees using MPTT helpers.
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, editable=False)
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )

    class MPTTMeta:
        order_insertion_by = ["name"]

    class Meta(MPTTModel.Meta, LifeCycleMixin.Meta, TimeStampedMixin.Meta):
        verbose_name_plural = "Categories"
        unique_together = ("parent", "name")
        indexes = [
            models.Index(fields=["is_active", "name"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Generate slug from name on creation (never changes afterwards).
        """
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def clean(self):
        """
        Validates category relationships to prevent cycles and invalid parent assignments.
        """
        super().clean()

        if not self.parent:
            return

        if self.parent == self:
            raise ValidationError("A category cannot be its own parent.")

        if self.parent.is_deleted:
            raise ValidationError("Cannot assign a deleted category as parent.")

        if not self.parent.is_active:
            raise ValidationError("Parent category must be active.")

        if self.pk and self.parent.is_descendant_of(self, include_self=True):
            raise ValidationError(
                "Cannot assign a descendant as parent (circular reference)."
            )

    def soft_delete(self):
        """
        Marks the current category and all its descendants as deleted (soft delete).
        It does not physically delete the records. It also deactivates the marked nodes.

        NOTE: It does not deactivate ancestors to avoid unexpected impacts on other branches.
        """
        with transaction.atomic():
            descendants_qs = self.get_descendants(include_self=True).filter(
                is_deleted=False
            )
            if descendants_qs.exists():
                descendants_qs.update(is_deleted=True, is_active=False)

    def hard_delete(self):
        """
        Physically remove this category and all its descendants.
        Useful for thorough cleanups.
        """
        with transaction.atomic():
            self.get_descendants(include_self=True).delete()

    def activate(self):
        """
        Activates the current category and all its ancestors if they are not deleted.
        It will not restore categories that are marked as deleted.
        """
        if self.is_deleted:
            raise ValueError("Cannot activate a deleted category. Restore it first.")

        if self.get_ancestors().filter(is_deleted=True).exists():
            raise ValueError(
                "Cannot activate category because one or more ancestors are deleted."
            )

        with transaction.atomic():
            ancestors_qs = self.get_ancestors(include_self=True).filter(
                is_deleted=False
            )
            if ancestors_qs.exists():
                ancestors_qs.update(is_active=True)

    def deactivate(self):
        """
        Deactivates the current category and all its descendants.
        Does not mark as deleted (does not affect is_deleted).
        """
        with transaction.atomic():
            descendants_qs = self.get_descendants(include_self=True).filter(
                is_active=True
            )
            if descendants_qs.exists():
                descendants_qs.update(is_active=False)

    def restore(self):
        """
        Restores (soft) the category and all its descendants marked as deleted.
        Does not automatically activate restored categories; that must be done with `activate()`.
        Verifies that the parent is not deleted before restoring.
        """
        if self.parent and self.parent.is_deleted:
            raise ValueError("Cannot restore category because its parent is deleted.")

        with transaction.atomic():
            descendants_qs = self.get_descendants(include_self=True).filter(
                is_deleted=True
            )
            if descendants_qs.exists():
                descendants_qs.update(is_deleted=False)
