"""Style catalogue and links to the shared fabric and measurement catalogues."""

from django.core.exceptions import ValidationError
from django.db import models


class Garment(models.Model):
    """Broad clothing type, separate from individual designs."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Occasion(models.Model):
    """Reusable intended-use category; styles may have several occasions."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Style(models.Model):
    """A design in the style catalogue."""

    class MeasurementSpecificationStatus(models.TextChoices):
        NOT_CONFIGURED = 'not_configured', 'Not configured'
        DRAFT = 'draft', 'Draft'
        REVIEWED = 'reviewed', 'Reviewed'
        VALIDATED = 'validated', 'Validated in practice'

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255)
    garment = models.ForeignKey(Garment, on_delete=models.PROTECT, related_name='styles')
    gender = models.CharField(max_length=30, blank=True)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    silhouette = models.CharField(max_length=100, blank=True)
    fit_type = models.CharField(max_length=50, blank=True)
    occasions = models.ManyToManyField(Occasion, related_name='styles', blank=True)
    complexity = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    measurement_specification_status = models.CharField(
        max_length=20,
        choices=MeasurementSpecificationStatus.choices,
        default=MeasurementSpecificationStatus.NOT_CONFIGURED,
    )
    measurement_specification_source = models.TextField(blank=True)
    measurement_specification_reviewed_by = models.CharField(max_length=150, blank=True)
    measurement_specification_reviewed_at = models.DateTimeField(blank=True, null=True)
    measurement_specification_validated_by = models.CharField(max_length=150, blank=True)
    measurement_specification_validated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [models.UniqueConstraint(
            fields=['garment', 'slug'], name='unique_style_slug_per_garment'
        )]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        errors = {}
        reviewed_statuses = {
            self.MeasurementSpecificationStatus.REVIEWED,
            self.MeasurementSpecificationStatus.VALIDATED,
        }
        if self.measurement_specification_status in reviewed_statuses:
            if not self.measurement_specification_source.strip():
                errors['measurement_specification_source'] = (
                    'Add the source used to review this measurement specification.'
                )
            if not self.measurement_specification_reviewed_by.strip():
                errors['measurement_specification_reviewed_by'] = (
                    'Record who reviewed this measurement specification.'
                )
            if self.measurement_specification_reviewed_at is None:
                errors['measurement_specification_reviewed_at'] = (
                    'Record when this measurement specification was reviewed.'
                )
        if self.measurement_specification_status == self.MeasurementSpecificationStatus.VALIDATED:
            if not self.measurement_specification_validated_by.strip():
                errors['measurement_specification_validated_by'] = (
                    'Record who validated this measurement specification in practice.'
                )
            if self.measurement_specification_validated_at is None:
                errors['measurement_specification_validated_at'] = (
                    'Record when this measurement specification was validated in practice.'
                )
        if errors:
            raise ValidationError(errors)


class StyleImage(models.Model):
    """One catalogue image or externally stored image reference per view."""

    class ViewType(models.TextChoices):
        FRONT = 'front', 'Front'
        BACK = 'back', 'Back'
        SIDE = 'side', 'Side'
        DETAIL = 'detail', 'Detail'
        FULL = 'full', 'Full length'

    style = models.ForeignKey(Style, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='styles/', help_text='Upload the style image.')
    view_type = models.CharField(max_length=20, choices=ViewType.choices, default=ViewType.FRONT)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', 'id']

    def __str__(self):
        return f'{self.style.name} - {self.get_view_type_display()}'


class StyleFabric(models.Model):
    """Explicit many-to-many association with the existing Fabrics app."""

    class Suitability(models.TextChoices):
        EXCELLENT = 'excellent', 'Excellent'
        GOOD = 'good', 'Good'
        ACCEPTABLE = 'acceptable', 'Acceptable'
        UNSUITABLE = 'unsuitable', 'Unsuitable'

    style = models.ForeignKey(Style, on_delete=models.CASCADE, related_name='fabric_links')
    fabric = models.ForeignKey('fabrics.Fabric', on_delete=models.PROTECT, related_name='style_links')
    suitability = models.CharField(max_length=20, choices=Suitability.choices, default=Suitability.GOOD)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['style__name', 'fabric__fabric_name']
        constraints = [models.UniqueConstraint(fields=['style', 'fabric'], name='unique_style_fabric')]

    def __str__(self):
        return f'{self.style.name} + {self.fabric.fabric_name}'


class StyleMeasurementRequirement(models.Model):
    """Measurement types needed to construct a design; stores no body values."""

    class Purpose(models.TextChoices):
        RECOMMENDATION = 'recommendation', 'Recommendation completeness'
        DRAFTING = 'drafting', 'Pattern drafting'
        BOTH = 'both', 'Recommendation and drafting'

    style = models.ForeignKey(Style, on_delete=models.CASCADE, related_name='measurement_requirements')
    measurement_type = models.ForeignKey(
        'measurements.MeasurementType', on_delete=models.PROTECT, related_name='style_requirements'
    )
    is_required = models.BooleanField(default=True)
    purpose = models.CharField(max_length=20, choices=Purpose.choices, default=Purpose.BOTH)
    instructions = models.TextField(blank=True)
    condition = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'measurement_type__name']
        constraints = [models.UniqueConstraint(
            fields=['style', 'measurement_type'], name='unique_style_measurement_type'
        )]

    def __str__(self):
        return f'{self.style.name}: {self.measurement_type.name}'
