from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerificationToken, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ("email", "full_name", "role", "is_email_verified", "onboarding_completed", "date_joined")
    list_filter   = ("role", "is_email_verified", "onboarding_completed", "is_active")
    search_fields = ("email", "full_name")
    ordering      = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login")

    fieldsets = (
        (None,          {"fields": ("email", "password")}),
        ("Personal",    {"fields": ("full_name", "avatar")}),
        ("Role & Auth", {"fields": ("role", "is_email_verified", "onboarding_completed", "onboarding_step")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Timestamps",  {"fields": ("date_joined", "last_login")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "role", "password1", "password2"),
        }),
    )


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display  = ("user", "expires_at", "created_at")
    raw_id_fields = ("user",)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display  = ("user", "is_used", "expires_at", "created_at")
    list_filter   = ("is_used",)
    raw_id_fields = ("user",)
