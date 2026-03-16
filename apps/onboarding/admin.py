from django.contrib import admin
from .models import OnboardingProfile


@admin.register(OnboardingProfile)
class OnboardingProfileAdmin(admin.ModelAdmin):
    list_display   = ("user", "age", "ethnicity", "bmi", "rppg_baseline_captured", "updated_at")
    list_filter    = ("ethnicity", "cycle_regularity", "rppg_baseline_captured")
    search_fields  = ("user__email", "full_name")
    raw_id_fields  = ("user",)
    readonly_fields = ("bmi", "created_at", "updated_at")
