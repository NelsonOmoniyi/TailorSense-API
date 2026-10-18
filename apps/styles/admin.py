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


@admin.register(Style)
class StyleAdmin(admin.ModelAdmin):
    list_display = ['name', 'garment', 'gender', 'is_active', 'updated_at']
    list_filter = ['garment', 'gender', 'is_active', 'occasions']
    search_fields = ['name', 'slug', 'description', 'garment__name']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['occasions']
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

