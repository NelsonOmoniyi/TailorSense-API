"""Normalized data models for user measurements and garment requirements.

Each measurement is stored as one row linked to a reusable measurement type.
Garments declare their needed measurement types through an explicit join model,
so new garment definitions do not require schema changes.
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class ProfileUnit(models.TextChoices):
    CENTIMETERS = 'cm', 'Centimeters'
    INCHES = 'in', 'Inches'


class MeasurementUnit(models.TextChoices):
    CENTIMETERS = 'cm', 'Centimeters'
    INCHES = 'in', 'Inches'
    KILOGRAMS = 'kg', 'Kilograms'
    POUNDS = 'lb', 'Pounds'


class MeasurementProfile(models.Model):
    """A named set of measurements owned by one authenticated user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='measurement_profiles',
    )
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=30, blank=True)
    unit = models.CharField(
        max_length=2,
        choices=ProfileUnit.choices,
        default=ProfileUnit.CENTIMETERS,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name', 'id']

    def __str__(self):
        return f'{self.name} ({self.user})'


class MeasurementType(models.Model):
    """Reusable measurement definition referenced by profiles and garments."""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    unit = models.CharField(
        max_length=2,
        choices=MeasurementUnit.choices,
        default=MeasurementUnit.CENTIMETERS,
    )
    gender = models.CharField(max_length=30, blank=True)
    is_core = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class StandardMeasurementSet(models.Model):
    """A shared field template available to every account without a profile."""

    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'

    class Context(models.TextChoices):
        CASUAL = 'casual', 'Casual'
        CORPORATE = 'corporate', 'Corporate'

    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=Gender.choices)
    context = models.CharField(max_length=20, choices=Context.choices)
    description = models.TextField(blank=True)
    measurement_types = models.ManyToManyField(
        MeasurementType,
        through='StandardMeasurementRequirement',
        related_name='standard_sets',
    )

    class Meta:
        ordering = ['gender', 'context']
        constraints = [
            models.UniqueConstraint(
                fields=['gender', 'context'],
                name='uniq_standard_measurement_gender_context',
            ),
        ]

    def __str__(self):
        return self.name


class Garment(models.Model):
    """A garment catalog entry whose required measurements are data-driven."""

    name = models.CharField(max_length=120)
    category = models.CharField(max_length=80)
    gender = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)
    measurement_types = models.ManyToManyField(
        MeasurementType,
        through='GarmentMeasurementRequirement',
        related_name='garments',
        blank=True,
    )

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class Measurement(models.Model):
    """One numeric value for one type inside a user's measurement profile."""

    profile = models.ForeignKey(
        MeasurementProfile,
        on_delete=models.CASCADE,
        related_name='measurements',
    )
    measurement_type = models.ForeignKey(
        MeasurementType,
        on_delete=models.PROTECT,
        related_name='measurements',
    )
    value = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    unit = models.CharField(max_length=2, choices=MeasurementUnit.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['measurement_type__category', 'measurement_type__name']
        constraints = [
            models.UniqueConstraint(
                fields=['profile', 'measurement_type'],
                name='uniq_measurement_profile_type',
            ),
            models.CheckConstraint(
                condition=Q(value__gt=0),
                name='measurement_value_positive',
            ),
        ]

    def __str__(self):
        return f'{self.measurement_type.name}: {self.value} {self.get_unit_display()}'


class GarmentMeasurementRequirement(models.Model):
    """Join row defining whether a measurement type is needed for a garment."""

    garment = models.ForeignKey(
        Garment,
        on_delete=models.CASCADE,
        related_name='measurement_requirements',
    )
    measurement_type = models.ForeignKey(
        MeasurementType,
        on_delete=models.PROTECT,
        related_name='garment_requirements',
    )
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ['garment__name', 'measurement_type__name']
        constraints = [
            models.UniqueConstraint(
                fields=['garment', 'measurement_type'],
                name='uniq_garment_measurement_requirement',
            ),
        ]

    def __str__(self):
        requirement = 'required' if self.is_required else 'optional'
        return f'{self.garment.name}: {self.measurement_type.name} ({requirement})'


class StandardMeasurementRequirement(models.Model):
    """A shared standard's required/optional field, independent of user data."""

    standard_set = models.ForeignKey(
        StandardMeasurementSet,
        on_delete=models.CASCADE,
        related_name='requirements',
    )
    measurement_type = models.ForeignKey(
        MeasurementType,
        on_delete=models.PROTECT,
        related_name='standard_requirements',
    )
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ['standard_set__gender', 'standard_set__context', 'measurement_type__category', 'measurement_type__name']
        constraints = [
            models.UniqueConstraint(
                fields=['standard_set', 'measurement_type'],
                name='uniq_standard_set_measurement_type',
            ),
        ]

    def __str__(self):
        requirement = 'required' if self.is_required else 'optional'
        return f'{self.standard_set.name}: {self.measurement_type.name} ({requirement})'