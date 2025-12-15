from django.utils import timezone
from django.utils.text import slugify
import re


def generate_unique_slug(instance, value_to_slug, slug_field="slug"):
    """
    Generate a unique slug for instance based on a provided string (value_to_slug).
    """
    base = slugify(value_to_slug[:200])
    slug = base
    ModelClass = instance.__class__
    counter = 1

    while (
        ModelClass.objects.filter(**{slug_field: slug}).exclude(pk=instance.pk).exists()
    ):
        slug = f"{base}-{counter}"
        counter += 1

    return slug


def today_util():
    return timezone.localdate()



UNIT_MAP = {
    r"\bgb\b": "GB",
    r"\bmb\b": "MB",
    r"\btb\b": "TB",
    r"\bmhz\b": "MHz",
    r"\bghz\b": "GHz",
    r"\bmah\b": "mAh",
    r"\bv\b": "V",
    r"\bw\b": "W",
    r"\bkg\b": "kg",
    r"\bg\b": "g",
    r"\bcm\b": "cm",
    r"\bmm\b": "mm",
    r"\bpx\b": "px",
}


def normalize_spec_value(value: str) -> str:
    """Normaliza valores técnicos como '8gb', '5000mah', '1920x1080'."""
    if not value:
        return value

    value = value.strip()
    value = re.sub(r"\s+", " ", value)

    # Separar "8GB" → "8 GB"
    value = re.sub(r"(\d)([A-Za-z])", r"\1 \2", value)

    # Separar "GB8" → "GB 8"
    value = re.sub(r"([A-Za-z])(\d)", r"\1 \2", value)

    # Normalizar resoluciones
    value = re.sub(r"(\d+)[xX](\d+)", r"\1 x \2", value)

    # Reemplazar unidades por estándar
    for pattern, replacement in UNIT_MAP.items():
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)

    return value
