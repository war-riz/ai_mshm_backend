"""
apps/centers/views.py
──────────────────────
Endpoints for:
  - Public center listings (for registration dropdowns)
  - Clinician profile create/read/update
  - Admin: manage HCC and FHC records
"""
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from core.responses import success_response, created_response, error_response
from core.permissions import IsClinician
from .models import HealthCareCenter, FederalHealthCenter, ClinicianProfile
from .serializers import (
    HealthCareCenterSerializer,
    HealthCareCenterPublicSerializer,
    FederalHealthCenterSerializer,
    FederalHealthCenterPublicSerializer,
    ClinicianProfileSerializer,
    CreateClinicianProfileSerializer,
)


# ── Public: Center lists for dropdowns ───────────────────────────────────────

class HCCListPublicView(APIView):
    """
    GET /api/v1/centers/hcc/
    Public — used in clinician registration form to populate center dropdown.
    """
    permission_classes = [AllowAny]

    @extend_schema(tags=["Centers"], summary="List all active Health Care Centers (public)")
    def get(self, request):
        centers = HealthCareCenter.objects.filter(
            status=HealthCareCenter.CenterStatus.ACTIVE
        ).order_by("state", "name")
        return success_response(
            data=HealthCareCenterPublicSerializer(centers, many=True).data
        )


class FHCListPublicView(APIView):
    """
    GET /api/v1/centers/fhc/
    Public — used in clinician registration form.
    """
    permission_classes = [AllowAny]

    @extend_schema(tags=["Centers"], summary="List all active Federal Health Centers (public)")
    def get(self, request):
        centers = FederalHealthCenter.objects.filter(
            status=FederalHealthCenter.CenterStatus.ACTIVE
        ).order_by("state", "name")
        return success_response(
            data=FederalHealthCenterPublicSerializer(centers, many=True).data
        )


# ── Clinician Profile ─────────────────────────────────────────────────────────

class ClinicianProfileView(APIView):
    """
    GET   /api/v1/centers/clinician/profile/   → get own profile
    POST  /api/v1/centers/clinician/profile/   → create profile (first time)
    PATCH /api/v1/centers/clinician/profile/   → update profile
    """
    permission_classes = [IsAuthenticated, IsClinician]

    def _get_profile(self, user):
        try:
            return ClinicianProfile.objects.select_related("hcc", "fhc").get(user=user)
        except ClinicianProfile.DoesNotExist:
            return None

    @extend_schema(tags=["Centers"], summary="Get own clinician profile")
    def get(self, request):
        profile = self._get_profile(request.user)
        if not profile:
            return error_response(
                "Clinician profile not set up yet. Please complete your profile.",
                http_status=404,
            )
        return success_response(
            data=ClinicianProfileSerializer(profile, context={"request": request}).data
        )

    @extend_schema(
        tags=["Centers"],
        request=CreateClinicianProfileSerializer,
        summary="Create clinician profile and link to HCC or FHC",
    )
    def post(self, request):
        if self._get_profile(request.user):
            return error_response("Clinician profile already exists. Use PATCH to update.")

        serializer = CreateClinicianProfileSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return created_response(
            data=ClinicianProfileSerializer(profile, context={"request": request}).data,
            message="Clinician profile created.",
        )

    @extend_schema(
        tags=["Centers"],
        request=CreateClinicianProfileSerializer,
        summary="Update clinician profile",
    )
    def patch(self, request):
        profile = self._get_profile(request.user)
        if not profile:
            return error_response("Profile not found. Use POST to create it first.", http_status=404)

        serializer = ClinicianProfileSerializer(
            profile, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=ClinicianProfileSerializer(profile, context={"request": request}).data,
            message="Clinician profile updated.",
        )


# ── Admin: Full HCC Management ────────────────────────────────────────────────

class HCCAdminListView(APIView):
    """
    GET  /api/v1/centers/admin/hcc/   → list all
    POST /api/v1/centers/admin/hcc/   → create
    Platform admin only.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(tags=["Centers – Admin"], summary="[Admin] List all Health Care Centers")
    def get(self, request):
        centers = HealthCareCenter.objects.all().order_by("state", "name")
        return success_response(data=HealthCareCenterSerializer(centers, many=True).data)

    @extend_schema(
        tags=["Centers – Admin"],
        request=HealthCareCenterSerializer,
        summary="[Admin] Create a new Health Care Center",
    )
    def post(self, request):
        serializer = HealthCareCenterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        center = serializer.save()
        return created_response(
            data=HealthCareCenterSerializer(center).data,
            message=f"Health Care Center '{center.name}' created.",
        )


class HCCAdminDetailView(APIView):
    """GET / PATCH / DELETE /api/v1/centers/admin/hcc/<id>/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get(self, pk):
        try:
            return HealthCareCenter.objects.get(pk=pk)
        except HealthCareCenter.DoesNotExist:
            return None

    @extend_schema(tags=["Centers – Admin"], summary="[Admin] Get HCC detail")
    def get(self, request, pk):
        center = self._get(pk)
        if not center:
            return error_response("Center not found.", http_status=404)
        return success_response(data=HealthCareCenterSerializer(center).data)

    @extend_schema(tags=["Centers – Admin"], request=HealthCareCenterSerializer,
                   summary="[Admin] Update HCC")
    def patch(self, request, pk):
        center = self._get(pk)
        if not center:
            return error_response("Center not found.", http_status=404)
        serializer = HealthCareCenterSerializer(center, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="Center updated.")

    @extend_schema(tags=["Centers – Admin"], summary="[Admin] Delete HCC")
    def delete(self, request, pk):
        center = self._get(pk)
        if not center:
            return error_response("Center not found.", http_status=404)
        name = center.name
        center.delete()
        return success_response(message=f"'{name}' deleted.")


class FHCAdminListView(APIView):
    """POST/GET /api/v1/centers/admin/fhc/ — Platform admin only."""
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(tags=["Centers – Admin"], summary="[Admin] List all Federal Health Centers")
    def get(self, request):
        centers = FederalHealthCenter.objects.all().order_by("state", "name")
        return success_response(data=FederalHealthCenterSerializer(centers, many=True).data)

    @extend_schema(tags=["Centers – Admin"], request=FederalHealthCenterSerializer,
                   summary="[Admin] Create a new Federal Health Center")
    def post(self, request):
        serializer = FederalHealthCenterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        center = serializer.save()
        return created_response(
            data=FederalHealthCenterSerializer(center).data,
            message=f"Federal Health Center '{center.name}' created.",
        )


class FHCAdminDetailView(APIView):
    """GET / PATCH / DELETE /api/v1/centers/admin/fhc/<id>/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get(self, pk):
        try:
            return FederalHealthCenter.objects.get(pk=pk)
        except FederalHealthCenter.DoesNotExist:
            return None

    @extend_schema(tags=["Centers – Admin"], summary="[Admin] Get FHC detail")
    def get(self, request, pk):
        center = self._get(pk)
        if not center:
            return error_response("Center not found.", http_status=404)
        return success_response(data=FederalHealthCenterSerializer(center).data)

    @extend_schema(tags=["Centers – Admin"], request=FederalHealthCenterSerializer,
                   summary="[Admin] Update FHC")
    def patch(self, request, pk):
        center = self._get(pk)
        if not center:
            return error_response("Center not found.", http_status=404)
        serializer = FederalHealthCenterSerializer(center, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="Center updated.")

    @extend_schema(tags=["Centers – Admin"], summary="[Admin] Delete FHC")
    def delete(self, request, pk):
        center = self._get(pk)
        if not center:
            return error_response("Center not found.", http_status=404)
        name = center.name
        center.delete()
        return success_response(message=f"'{name}' deleted.")
