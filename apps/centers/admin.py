from django.contrib import admin
from .models import HealthCareCenter, FederalHealthCenter, ClinicianProfile


@admin.register(HealthCareCenter)
class HealthCareCenterAdmin(admin.ModelAdmin):
    list_display   = ("name", "code", "state", "lga", "status", "notify_on_severe", "created_at")
    list_filter    = ("status", "state", "notify_on_severe", "notify_on_very_severe")
    search_fields  = ("name", "code", "email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(FederalHealthCenter)
class FederalHealthCenterAdmin(admin.ModelAdmin):
    list_display   = ("name", "code", "state", "zone", "status", "created_at")
    list_filter    = ("status", "state", "zone")
    search_fields  = ("name", "code", "email")
    readonly_fields = ("created_at", "updated_at", "notify_on_very_severe")


@admin.register(ClinicianProfile)
class ClinicianProfileAdmin(admin.ModelAdmin):
    list_display   = ("user", "specialization", "center_type", "center_name", "is_verified", "created_at")
    list_filter    = ("specialization", "center_type", "is_verified")
    search_fields  = ("user__email", "user__full_name", "license_number")
    raw_id_fields  = ("user", "hcc", "fhc")
    readonly_fields = ("created_at", "updated_at", "verified_at")

    actions = ["verify_clinicians"]

    @admin.action(description="Mark selected clinicians as verified")
    def verify_clinicians(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_verified=True, verified_at=timezone.now())
        self.message_user(request, f"{queryset.count()} clinician(s) verified.")
