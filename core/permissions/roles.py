"""
core/permissions/roles.py
──────────────────────────
Custom DRF permission classes used across apps.

Usage in a view:
    from core.permissions.roles import IsPatient, IsClinician, IsEmailVerified

    class SomeView(APIView):
        permission_classes = [IsAuthenticated, IsPatient, IsEmailVerified]
"""
from rest_framework.permissions import BasePermission


class IsEmailVerified(BasePermission):
    """
    Allow access only to users whose email address has been verified.
    Use in addition to IsAuthenticated — never standalone.
    """
    message = "Please verify your email address before accessing this resource."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_email_verified
        )


class IsPatient(BasePermission):
    """Allow access only to users with role == 'patient'."""
    message = "This endpoint is only available to patients."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "patient"
        )


class IsClinician(BasePermission):
    """Allow access only to users with role == 'clinician'."""
    message = "This endpoint is only available to clinicians."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "clinician"
        )


class IsPatientOrClinician(BasePermission):
    """Allow access to patients and clinicians (not admin-only routes)."""
    message = "This endpoint requires a patient or clinician account."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("patient", "clinician")
        )


class IsOnboardingComplete(BasePermission):
    """
    Restrict access until the user has finished onboarding.
    Use on dashboard / health data endpoints.
    """
    message = "Please complete your onboarding before accessing this feature."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.onboarding_completed
        )


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission: only the owner of an object can write to it.
    Assumes the model has a `user` FK field.
    """
    def has_object_permission(self, request, view, obj):
        from rest_framework.permissions import SAFE_METHODS
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user


class IsOwner(BasePermission):
    """
    Object-level permission: only the owner can read or write.
    Assumes the model has a `user` FK field.
    """
    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsHCCAdmin(BasePermission):
    """Allow access only to users with role == 'hcc_admin'."""
    message = "This endpoint is only available to Health Care Center administrators."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "hcc_admin"
        )


class IsFHCAdmin(BasePermission):
    """Allow access only to users with role == 'fhc_admin'."""
    message = "This endpoint is only available to Federal Health Center administrators."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "fhc_admin"
        )


class IsCenterAdmin(BasePermission):
    """Allow access to either HCC or FHC admins."""
    message = "This endpoint requires a center administrator account."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("hcc_admin", "fhc_admin")
        )


class IsClinicianVerified(BasePermission):
    """Allow access only to clinicians whose ClinicianProfile is verified."""
    message = "Your clinician profile has not been verified yet."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role != "clinician":
            return False
        try:
            return request.user.clinician_profile.is_verified
        except Exception:
            return False
