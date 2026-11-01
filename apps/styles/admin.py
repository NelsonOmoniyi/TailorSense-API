"""Admin configuration for the style catalogue."""

from django.contrib import admin

from .models import Garment, Occasion, Style, StyleFabric, StyleImage, StyleMeasurementRequirement


class StyleImageInline(admin.TabularInline):
    model = StyleImage
    extra = 0


class StyleFabricInline(admin.TabularInline):
    model = StyleFabric
    extra = 0


class StyleMeasurementInline(admin.TabularInline):
    model = StyleMeasurementRequirement
    extra = 0
    fields = [
        'measurement_type', 'is_required', 'purpose', 'condition',
        'instructions', 'notes', 'display_order',
    ]


@admin.register(Style)
class StyleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'garment', 'gender', 'measurement_specification_status',
        'is_active', 'updated_at',
    ]
    list_filter = ['garment', 'gender', 'measurement_specification_status', 'is_active', 'occasions']
    search_fields = ['name', 'slug', 'description', 'garment__name']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['occasions']
    fieldsets = [
        (None, {
            'fields': [
                'name', 'slug', 'garment', 'gender', 'category', 'description',
                'silhouette', 'fit_type', 'complexity', 'is_active', 'occasions',
            ],
        }),
        ('Measurement specification review', {
            'fields': [
                'measurement_specification_status', 'measurement_specification_source',
                'measurement_specification_reviewed_by', 'measurement_specification_reviewed_at',
                'measurement_specification_validated_by', 'measurement_specification_validated_at',
            ],
        }),
    ]
    inlines = [StyleImageInline, StyleFabricInline, StyleMeasurementInline]


@admin.register(Garment)
class GarmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Occasion)
class OccasionAdmin(admin.ModelAdmin):
    search_fields = ['name']
