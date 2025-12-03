from django.db import models

from catalog.utils import normalize_spec_value



class Attribute(models.Model):
    """Attribute definitions (e.g., Color, Size)"""

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name




class AttributeValue(models.Model):
    """Specific attribute values for product variants"""

    attribute = models.ForeignKey(
        'Attribute', on_delete=models.CASCADE, related_name="values"
    )
    value = models.CharField(max_length=200)

    class Meta:
        unique_together = ["attribute", "value"]
        indexes = [
            models.Index(fields=["attribute", "value"]),
        ]
        ordering = ["value"]

    def save(self, *args, **kwargs):
        """Normalización automática antes de guardar."""
        self.value = normalize_spec_value(self.value)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"
