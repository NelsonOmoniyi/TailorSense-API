from django.contrib import admin

from .models import (
    Garment,
    GarmentMeasurementRequirement,
    Measurement,
    MeasurementProfile,
    MeasurementType,
)


class MeasurementInline(admin.TabularInline):
    model = Measurement
    extra = 0


class GarmentMeasurementRequirementInline(admin.TabularInline):
    model = GarmentMeasurementRequirement
    extra = 0


@admin.register(MeasurementProfile)
class MeasurementProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'gender', 'unit', 'updated_at')
    list_filter = ('gender', 'unit')
    search_fields = ('name', 'user__username', 'user__email')
    inlines = (MeasurementInline,)


@admin.register(MeasurementType)
class MeasurementTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'unit', 'gender', 'is_core')
    list_filter = ('category', 'unit', 'gender', 'is_core')
    search_fields = ('name', 'code', 'description')


@admin.register(Garment)
class GarmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'gender')
    list_filter = ('category', 'gender')
    search_fields = ('name', 'description')
    inlines = (GarmentMeasurementRequirementInline,)