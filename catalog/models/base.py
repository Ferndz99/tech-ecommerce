from django.db import models


class LifeCycleMixin(models.Model):
    """
    Abstract model for implementing activation control and soft delete.

    Includes:

    - Two Boolean fields (is_active, is_deleted) for state management.

    - Methods for activating, deactivating, logically deleting, and restoring.

    - A custom manager (objects) that excludes records deleted by default.
    """

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indicates whether the record is available and in use. A deleted record is always inactive.",
    )

    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indicates if the record has been marked as deleted, but still exists in the database.",
    )

    class Meta:
        abstract = True

    def activate(self) -> None:
        """
        Activate registration, making it available for normal use.
        """
        if self.is_deleted:
            raise ValueError(
                "A record marked as deleted cannot be activated. Restore it first!"
            )

        self.is_active = True
        self.save(update_fields=["is_active"])

    def deactivate(self) -> None:
        """Disable logging, making it temporarily unavailable."""
        self.is_active = False
        self.save(update_fields=["is_active"])

    def soft_delete(self) -> None:
        """
        Marks the entry as deleted (soft/logical deletion).
        Automatically disables the entry to maintain consistency.
        """
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=["is_deleted", "is_active"])

    def restore(self) -> None:
        """
        Restores a previously deleted record. Marks it as not deleted, but does not automatically activate it.
        """
        self.is_deleted = False
        self.save(update_fields=["is_deleted"])

    def hard_delete(self) -> None:
        """Permanently deletes the record from the database."""
        super().delete()


class TimeStampedMixin(models.Model):
    """Abstract model mixin adding creation and last modification timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
