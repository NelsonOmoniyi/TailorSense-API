"""Recommendation-focused fabric model for TailorSense."""

from django.db import models


class Fabric(models.Model):
    """A fabric record used to evaluate garment suitability for a user's measurements."""

    class PropertyLevel(models.TextChoices):
        NONE = 'none', 'None'
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100, blank=True)
    composition = models.CharField(max_length=200, blank=True)
    construction = models.CharField(max_length=100, blank=True)
    weight_gsm = models.PositiveIntegerField(null=True, blank=True)
    stretch = models.CharField(
        max_length=20,
        choices=PropertyLevel.choices,
        default=PropertyLevel.NONE,
        blank=True,
    )
    drape = models.CharField(
        max_length=20,
        choices=PropertyLevel.choices,
        default=PropertyLevel.NONE,
        blank=True,
    )
    structure = models.CharField(
        max_length=20,
        choices=PropertyLevel.choices,
        default=PropertyLevel.NONE,
        blank=True,
    )
    breathability = models.CharField(
        max_length=20,
        choices=PropertyLevel.choices,
        default=PropertyLevel.NONE,
        blank=True,
    )
    opacity = models.CharField(
        max_length=20,
        choices=PropertyLevel.choices,
        default=PropertyLevel.NONE,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
