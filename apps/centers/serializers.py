"""
apps/centers/serializers.py
────────────────────────────
Serializers for HCC, FHC, and ClinicianProfile.
"""
from rest_framework import serializers
from .models import HealthCareCenter, FederalHealthCenter, ClinicianProfile


# ── Health Care Center ────────────────────────────────────────────────────────

class HealthCareCenterSerializer(serializers.ModelSerializer):
    clinician_count = serializers.SerializerMethodField()

    class Meta:
        model  = HealthCareCenter
        fields = [
            "id", "name", "code", "address", "state", "lga",
            "phone", "email", "website", "status",
            "notify_on_severe", "notify_on_very_severe",
            "clinician_count", "created_at",
        ]
        read_only_fields = ["id", "created_at", "clinician_count"]

    def get_clinician_count(self, obj):
        return obj.clinicians.filter(user__is_active=True).count()


class HealthCareCenterPublicSerializer(serializers.ModelSerializer):
    """Minimal read-only view — for dropdown in clinician registration."""
    class Meta:
        model  = HealthCareCenter
        fields = ["id", "name", "code", "state", "lga"]


# ── Federal Health Center ─────────────────────────────────────────────────────

class FederalHealthCenterSerializer(serializers.ModelSerializer):
    clinician_count = serializers.SerializerMethodField()

    class Meta:
        model  = FederalHealthCenter
        fields = [
            "id", "name", "code", "address", "state", "zone",
            "phone", "email", "status",
            "notify_on_very_severe",
            "clinician_count", "created_at",
        ]
        read_only_fields = ["id", "created_at", "clinician_count", "notify_on_very_severe"]

    @extend_schema_field(serializers.IntegerField())
    def get_clinician_count(self, obj):
        return obj.clinicians.filter(user__is_active=True).count()


class FederalHealthCenterPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FederalHealthCenter
        fields = ["id", "name", "code", "state", "zone"]


# ── Clinician Profile ─────────────────────────────────────────────────────────

class ClinicianProfileSerializer(serializers.ModelSerializer):
    center_name    = serializers.CharField(read_only=True)
    hcc_detail     = HealthCareCenterPublicSerializer(source="hcc", read_only=True)
    fhc_detail     = FederalHealthCenterPublicSerializer(source="fhc", read_only=True)
    user_email     = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)
    profile_photo_url = serializers.SerializerMethodField()

    class Meta:
        model  = ClinicianProfile
        fields = [
            "id", "user_email", "user_full_name",
            "specialization", "license_number", "years_of_experience", "bio",
            "center_type", "hcc", "fhc",
            "hcc_detail", "fhc_detail", "center_name",
            "is_verified", "verified_at",
            "profile_photo_url",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_verified", "verified_at", "created_at", "updated_at",
                            "user_email", "user_full_name", "center_name"]

    def get_profile_photo_url(self, obj):
        request = self.context.get("request")
        if obj.profile_photo and request:
            return request.build_absolute_uri(obj.profile_photo.url)
        return None

    def validate(self, attrs):
        center_type = attrs.get("center_type", getattr(self.instance, "center_type", None))
        hcc = attrs.get("hcc", getattr(self.instance, "hcc", None))
        fhc = attrs.get("fhc", getattr(self.instance, "fhc", None))

        if center_type == ClinicianProfile.CenterType.HCC and not hcc:
            raise serializers.ValidationError({"hcc": "Must select a Health Care Center."})
        if center_type == ClinicianProfile.CenterType.FHC and not fhc:
            raise serializers.ValidationError({"fhc": "Must select a Federal Health Center."})
        if hcc and fhc:
            raise serializers.ValidationError("Cannot be linked to both HCC and FHC.")
        return attrs


class CreateClinicianProfileSerializer(serializers.ModelSerializer):
    """Used during onboarding — clinician fills in their center affiliation."""
    class Meta:
        model  = ClinicianProfile
        fields = [
            "specialization", "license_number", "years_of_experience", "bio",
            "center_type", "hcc", "fhc", "profile_photo",
        ]

    def validate(self, attrs):
        center_type = attrs.get("center_type")
        hcc = attrs.get("hcc")
        fhc = attrs.get("fhc")

        if center_type == ClinicianProfile.CenterType.HCC and not hcc:
            raise serializers.ValidationError({"hcc": "Must select a Health Care Center."})
        if center_type == ClinicianProfile.CenterType.FHC and not fhc:
            raise serializers.ValidationError({"fhc": "Must select a Federal Health Center."})
        if hcc and fhc:
            raise serializers.ValidationError("Cannot be linked to both HCC and FHC.")
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        return ClinicianProfile.objects.create(user=user, **validated_data)
